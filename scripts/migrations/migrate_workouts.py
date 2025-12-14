"""
Workout Migration
==================

Migrates workout data from exercise-log.md to WorkoutSession and ExerciseLog tables.
Parses markdown table format and creates workout sessions with linked exercises.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import date
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migrations.validators import (
    validate_date, validate_text, validate_int,
    parse_sets_reps_notation, sanitize_notes
)

logger = logging.getLogger(__name__)


class WorkoutMigrator:
    """Migrates workout sessions and exercise logs from markdown to database"""

    def __init__(self, db_session, user_id: int):
        """
        Initialize workout migrator.

        Args:
            db_session: SQLAlchemy database session
            user_id: User ID to associate workouts with
        """
        self.session = db_session
        self.user_id = user_id
        self.source_file = PROJECT_ROOT / 'Health_and_Fitness' / 'data' / 'exercise-log.md'

    def parse_markdown_table(self) -> List[Dict]:
        """
        Parse workout logs from exercise-log.md table format.

        Expected format:
        | Date | Phase | Workout | Exercise | Sets x Reps | Notes |

        Returns:
            List of dictionaries with parsed workout logs
        """
        if not self.source_file.exists():
            logger.error(f"Source file not found: {self.source_file}")
            return []

        exercises = []
        with open(self.source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse table rows
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line.startswith('|'):
                continue
            if '| :' in line or 'Date' in line:  # Skip header/separator
                continue

            try:
                parts = [p.strip() for p in line.split('|')]
                parts = [p for p in parts if p]  # Remove empty

                if len(parts) < 4:
                    continue

                date_str = parts[0] if len(parts) > 0 else ''
                phase = parts[1] if len(parts) > 1 else ''
                workout_type = parts[2] if len(parts) > 2 else ''
                exercise_name = parts[3] if len(parts) > 3 else ''
                sets_reps = parts[4] if len(parts) > 4 else ''
                notes = parts[5] if len(parts) > 5 else ''

                # Parse sets and reps from notation
                sets, reps = parse_sets_reps_notation(sets_reps)

                exercise = {
                    'date': date_str,
                    'phase': phase,
                    'workout_type': workout_type,
                    'exercise_name': exercise_name,
                    'sets': sets,
                    'reps': reps,
                    'sets_reps_raw': sets_reps,
                    'notes': notes,
                    'line_number': line_num
                }

                exercises.append(exercise)

            except Exception as e:
                logger.error(f"Line {line_num}: Parse error: {e}")
                continue

        logger.info(f"Parsed {len(exercises)} exercise log entries")
        return exercises

    def group_by_session(self, exercises: List[Dict]) -> Dict:
        """
        Group exercises by date and workout type to create sessions.

        Args:
            exercises: List of parsed exercise dictionaries

        Returns:
            Dictionary mapping (date, workout_type) to list of exercises
        """
        sessions = defaultdict(list)

        for exercise in exercises:
            date_result = validate_date(exercise['date'], 'date')
            if not date_result:
                logger.warning(f"Skipping exercise with invalid date: {exercise['date']}")
                continue

            session_key = (date_result.value, exercise['workout_type'])
            sessions[session_key].append(exercise)

        logger.info(f"Grouped into {len(sessions)} workout sessions")
        return dict(sessions)

    def create_sessions(self, grouped_exercises: Dict, dry_run: bool = False) -> Dict:
        """
        Create workout sessions and exercise logs in database.

        Args:
            grouped_exercises: Dictionary of exercises grouped by session
            dry_run: If True, simulate without inserting

        Returns:
            Dictionary with migration statistics
        """
        from website.models import WorkoutSession, ExerciseLog, SessionType

        stats = {
            'sessions_created': 0,
            'exercises_created': 0,
            'sessions_failed': 0,
            'errors': []
        }

        # Map workout type strings to SessionType enum
        type_mapping = {
            'full body rings': SessionType.STRENGTH,
            'ring progression plan': SessionType.STRENGTH,
            'bodyweight foundation': SessionType.STRENGTH,
            'daily walk progression': SessionType.CARDIO,
            'general mobility': SessionType.FLEXIBILITY,
            'tai chi': SessionType.MARTIAL_ARTS,
        }

        for (session_date, workout_type), exercises in grouped_exercises.items():
            try:
                if dry_run:
                    logger.info(f"DRY RUN: Would create session on {session_date} with {len(exercises)} exercises")
                    stats['sessions_created'] += 1
                    stats['exercises_created'] += len(exercises)
                    continue

                # Determine session type
                workout_type_lower = workout_type.lower()
                session_type = SessionType.MIXED  # default
                for key, stype in type_mapping.items():
                    if key in workout_type_lower:
                        session_type = stype
                        break

                # Extract phase info from first exercise
                first_ex = exercises[0]
                phase = first_ex.get('phase', '')

                # Create workout session
                session = WorkoutSession(
                    user_id=self.user_id,
                    session_date=session_date,
                    session_type=session_type,
                    program_phase=phase if phase else None,
                    notes=f"Imported from exercise-log.md ({workout_type})"
                )

                self.session.add(session)
                self.session.flush()  # Get session ID

                # Create exercise logs for this session
                for idx, exercise in enumerate(exercises):
                    exercise_log = ExerciseLog(
                        workout_session_id=session.id,
                        exercise_name=exercise['exercise_name'],
                        sets=exercise.get('sets'),
                        reps=exercise.get('reps'),
                        notes=sanitize_notes(exercise.get('notes')),
                        order_index=idx
                    )

                    self.session.add(exercise_log)
                    stats['exercises_created'] += 1

                stats['sessions_created'] += 1
                logger.debug(f"Created session on {session_date} with {len(exercises)} exercises")

            except Exception as e:
                stats['sessions_failed'] += 1
                error_msg = f"Failed to create session {session_date}: {e}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)

        # Commit all changes
        if not dry_run and stats['sessions_created'] > 0:
            try:
                self.session.commit()
                logger.info(f"Committed {stats['sessions_created']} sessions with {stats['exercises_created']} exercises")
            except Exception as e:
                self.session.rollback()
                error_msg = f"Commit failed, rolled back: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                stats['sessions_failed'] = stats['sessions_created']
                stats['sessions_created'] = 0
                stats['exercises_created'] = 0

        return stats

    def migrate(self, dry_run: bool = False) -> Dict:
        """
        Execute complete workout migration.

        Args:
            dry_run: If True, simulate without inserting

        Returns:
            Migration results dictionary
        """
        logger.info("="*60)
        logger.info("Starting Workout Migration")
        logger.info("="*60)

        # Step 1: Parse markdown
        logger.info("Step 1: Parsing exercise-log.md...")
        exercises = self.parse_markdown_table()

        if not exercises:
            return {'status': 'error', 'message': 'No exercises found'}

        # Step 2: Group by session
        logger.info("Step 2: Grouping exercises into sessions...")
        sessions = self.group_by_session(exercises)

        # Step 3: Create sessions and exercises
        logger.info(f"Step 3: Creating {len(sessions)} sessions (dry_run={dry_run})...")
        stats = self.create_sessions(sessions, dry_run=dry_run)

        results = {
            'status': 'success' if stats['sessions_failed'] == 0 else 'partial',
            'dry_run': dry_run,
            'source_file': str(self.source_file),
            'statistics': {
                'total_exercises_parsed': len(exercises),
                'sessions_created': stats['sessions_created'],
                'exercises_created': stats['exercises_created'],
                'sessions_failed': stats['sessions_failed']
            },
            'errors': stats['errors']
        }

        logger.info("="*60)
        logger.info("Workout Migration Complete")
        logger.info(f"Sessions created: {results['statistics']['sessions_created']}")
        logger.info(f"Exercises created: {results['statistics']['exercises_created']}")
        logger.info("="*60)

        return results


def migrate_workouts(session, user_id: int, dry_run: bool = False) -> Dict:
    """Convenience function to run workout migration."""
    migrator = WorkoutMigrator(session, user_id)
    return migrator.migrate(dry_run=dry_run)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("\n=== Workout Migration Module ===")
    print("Run: python scripts/migrate_to_database.py --workouts --user-id 1")
