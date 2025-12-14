"""
Coaching Session Migration
===========================

Migrates coaching data from Coaching_sessions.md to CoachingSession table.
Parses markdown sections and extracts session information.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict
import logging
import re
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migrations.validators import validate_date, sanitize_notes

logger = logging.getLogger(__name__)


class CoachingMigrator:
    """Migrates coaching sessions from markdown to database"""

    def __init__(self, db_session, user_id: int, coach_id: int):
        self.session = db_session
        self.user_id = user_id
        self.coach_id = coach_id
        self.source_file = PROJECT_ROOT / 'Health_and_Fitness' / 'data' / 'Coaching_sessions.md'

    def parse_coaching_sessions(self) -> List[Dict]:
        """
        Parse coaching sessions from Coaching_sessions.md.

        Expected format:
        ## 2025-12-10: Session Title
        **Trainer:** Name
        **Subject:** Description
        [Session content...]

        Returns:
            List of parsed coaching session dictionaries
        """
        if not self.source_file.exists():
            logger.error(f"Source file not found: {self.source_file}")
            return []

        sessions = []

        with open(self.source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by level 2 headers (session markers)
        session_blocks = re.split(r'\n## ', content)

        for block in session_blocks:
            if not block.strip():
                continue

            try:
                # Extract date from header like "2025-12-10: Title"
                first_line = block.split('\n')[0]
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', first_line)

                if not date_match:
                    continue

                session_date_str = date_match.group(1)
                title = first_line.split(':', 1)[1].strip() if ':' in first_line else 'Session'

                # Extract trainer/coach
                trainer_match = re.search(r'\*\*Trainer:\*\*\s*(.+)', block)
                trainer = trainer_match.group(1).strip() if trainer_match else 'Unknown'

                # Extract subject
                subject_match = re.search(r'\*\*Subject:\*\*\s*(.+)', block)
                subject = subject_match.group(1).strip() if subject_match else ''

                # Extract action items (lines starting with * in Orders or Adjustments sections)
                action_items = []
                orders_match = re.search(r'\*\*Orders:\*\*(.*?)(?=\n##|\n\*\*|$)', block, re.DOTALL)
                if orders_match:
                    orders_text = orders_match.group(1)
                    items = re.findall(r'\*\s+\*\*(.+?)\*\*', orders_text)
                    action_items.extend(items)

                # Full discussion notes (everything after subject)
                discussion_notes = block

                session = {
                    'date': session_date_str,
                    'title': title,
                    'trainer': trainer,
                    'subject': subject,
                    'discussion_notes': discussion_notes.strip(),
                    'action_items': action_items,
                }

                sessions.append(session)

            except Exception as e:
                logger.error(f"Failed to parse session block: {e}")
                continue

        logger.info(f"Parsed {len(sessions)} coaching sessions")
        return sessions

    def insert_sessions(self, sessions: List[Dict], dry_run: bool = False) -> Dict:
        """Insert coaching sessions into database."""
        from website.models import CoachingSession

        stats = {
            'inserted': 0,
            'failed': 0,
            'errors': []
        }

        for session in sessions:
            try:
                # Validate date
                date_result = validate_date(session['date'], 'session_date')
                if not date_result:
                    logger.warning(f"Skipping session with invalid date: {session['date']}")
                    stats['failed'] += 1
                    continue

                if dry_run:
                    logger.info(f"DRY RUN: Would insert session on {date_result.value}")
                    stats['inserted'] += 1
                    continue

                # Create CoachingSession entry
                coaching_session = CoachingSession(
                    user_id=self.user_id,
                    coach_id=self.coach_id,
                    session_date=date_result.value,
                    discussion_notes=sanitize_notes(session.get('discussion_notes')),
                    coach_feedback=sanitize_notes(session.get('subject')),
                    action_items=session.get('action_items') if session.get('action_items') else None,
                    topics=[session.get('title')] if session.get('title') else None
                )

                self.session.add(coaching_session)
                stats['inserted'] += 1

            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Failed to insert session on {session['date']}: {e}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)

        # Commit
        if not dry_run and stats['inserted'] > 0:
            try:
                self.session.commit()
                logger.info(f"Committed {stats['inserted']} coaching sessions")
            except Exception as e:
                self.session.rollback()
                error_msg = f"Commit failed, rolled back: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                stats['failed'] += stats['inserted']
                stats['inserted'] = 0

        return stats

    def migrate(self, dry_run: bool = False) -> Dict:
        """Execute coaching migration."""
        logger.info("="*60)
        logger.info("Starting Coaching Session Migration")
        logger.info("="*60)

        # Parse sessions
        logger.info("Step 1: Parsing Coaching_sessions.md...")
        sessions = self.parse_coaching_sessions()

        if not sessions:
            return {'status': 'error', 'message': 'No coaching sessions found'}

        # Insert sessions
        logger.info(f"Step 2: Inserting {len(sessions)} sessions (dry_run={dry_run})...")
        stats = self.insert_sessions(sessions, dry_run=dry_run)

        results = {
            'status': 'success' if stats['failed'] == 0 else 'partial',
            'dry_run': dry_run,
            'source_file': str(self.source_file),
            'statistics': {
                'total_parsed': len(sessions),
                'inserted': stats['inserted'],
                'failed': stats['failed']
            },
            'errors': stats['errors']
        }

        logger.info("="*60)
        logger.info(f"Coaching Migration Complete: {stats['inserted']} inserted")
        logger.info("="*60)

        return results


def migrate_coaching(session, user_id: int, coach_id: int, dry_run: bool = False) -> Dict:
    """Convenience function to run coaching migration."""
    migrator = CoachingMigrator(session, user_id, coach_id)
    return migrator.migrate(dry_run=dry_run)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("\n=== Coaching Migration Module ===")
    print("Run: python scripts/migrate_to_database.py --coaching --user-id 1 --coach-id 1")
