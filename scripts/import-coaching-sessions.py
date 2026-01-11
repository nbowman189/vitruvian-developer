#!/usr/bin/env python3
"""
Import coaching sessions from Coaching_sessions.md to database.
Parses markdown headers to extract session dates and content.
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from website import create_app, db
from website.models.coaching import CoachingSession
from website.models.user import User


def parse_coaching_sessions(file_path):
    """Parse Coaching_sessions.md and extract sessions."""

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return []

    print(f"📖 Reading file: {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    sessions = []

    # Split by ## headers (session markers)
    sections = re.split(r'\n## ', content)

    for section in sections[1:]:  # Skip first section (file header)
        lines = section.split('\n')

        # First line should be the session header with date
        header = lines[0].strip()

        # Try to extract date from header (format: "YYYY-MM-DD: Title")
        date_match = re.match(r'(\d{4}-\d{2}-\d{2}):\s*(.+)', header)

        if not date_match:
            print(f"⚠️  Skipping section without date: {header[:50]}...")
            continue

        date_str = date_match.group(1)
        session_title = date_match.group(2).strip()

        try:
            session_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"⚠️  Invalid date format: {date_str}")
            continue

        # Extract trainer name and subject
        trainer = None
        subject = None
        content_lines = []
        in_content = False

        for line in lines[1:]:
            line = line.strip()

            if line.startswith('**Trainer:**'):
                trainer = line.replace('**Trainer:**', '').strip()
            elif line.startswith('**Subject:**'):
                subject = line.replace('**Subject:**', '').strip()
            elif line.startswith('###'):
                in_content = True
                content_lines.append(line)
            elif in_content or (trainer and subject):
                in_content = True
                content_lines.append(line)

        # Join content
        session_content = '\n'.join(content_lines).strip()

        # Determine session type from title
        session_type = "General Check-in"
        if "Check-in" in session_title or "Check-in" in subject:
            session_type = "Weekly Check-in"
        elif "Plan" in session_title or "Strategy" in subject:
            session_type = "Planning Session"
        elif "Analysis" in session_title:
            session_type = "Progress Analysis"
        elif "Motivational" in session_title:
            session_type = "Motivational Session"

        # Note: Field mapping for template compatibility:
        # - coach_feedback: displayed as card title (short summary)
        # - discussion_notes: rendered as markdown content (full notes)
        sessions.append({
            'session_date': session_date,
            'session_type': session_type,
            'coach_feedback': f"{session_title}\n\n{subject}" if subject else session_title,
            'discussion_notes': session_content[:2000],  # Full markdown content
            'trainer': trainer or "The Transformative Trainer"
        })

    return sessions


def import_to_database(sessions, skip_duplicates=True):
    """Import coaching sessions to database."""

    print(f"\n📊 Found {len(sessions)} coaching sessions to import")

    app = create_app()

    with app.app_context():
        # Get admin user
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User.query.first()

        if not user:
            print("❌ No users found in database!")
            return False

        # Use admin user as both client and coach (self-coaching)
        coach_user = user

        print(f"📌 Associating all coaching sessions with user: {user.username} (ID: {user.id})")
        print(f"📌 Using coach: {coach_user.username} (ID: {coach_user.id})")

        imported = 0
        skipped = 0
        errors = 0

        for session_data in sessions:
            try:
                # Check if session exists for this date
                existing = CoachingSession.query.filter_by(
                    user_id=user.id,
                    session_date=session_data['session_date']
                ).first()

                if existing:
                    if skip_duplicates:
                        print(f"⏭️  Skipping {session_data['session_date']} (already exists)")
                        skipped += 1
                        continue
                    else:
                        existing.coach_feedback = session_data['coach_feedback']
                        existing.discussion_notes = session_data['discussion_notes']
                        print(f"🔄 Updated {session_data['session_date']}")
                else:
                    # Create coaching session
                    coaching = CoachingSession(
                        user_id=user.id,
                        coach_id=coach_user.id,
                        session_date=session_data['session_date'],
                        coach_feedback=session_data['coach_feedback'],
                        discussion_notes=session_data['discussion_notes']
                    )
                    db.session.add(coaching)
                    print(f"✅ Imported {session_data['session_date']} - {session_data['session_type']}")

                imported += 1

            except Exception as e:
                print(f"❌ Error importing {session_data.get('session_date', 'unknown')}: {e}")
                errors += 1

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Database commit successful!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Database commit failed: {e}")
            return False

        print(f"\n📈 Import Summary:")
        print(f"   Imported: {imported}")
        print(f"   Skipped: {skipped}")
        print(f"   Errors: {errors}")
        print(f"   Total: {len(sessions)}")

        return True


def main():
    """Main function."""

    print("====================================")
    print("Coaching Sessions Import Tool")
    print("====================================")
    print()

    # Default path - check if in Docker container (data at root) or local dev (relative path)
    docker_path = Path("/Health_and_Fitness/data/Coaching_sessions.md")
    local_path = Path(__file__).parent.parent / "Health_and_Fitness" / "data" / "Coaching_sessions.md"

    # Use Docker path if it exists, otherwise local path
    default_path = docker_path if docker_path.exists() else local_path

    # Allow custom path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = str(default_path)

    print(f"📂 Looking for: {file_path}")

    # Parse the file
    sessions = parse_coaching_sessions(file_path)

    if not sessions:
        print("❌ No coaching sessions found in file")
        return 1

    # Ask for confirmation
    print(f"\n⚠️  About to import {len(sessions)} coaching sessions to the database")
    print("   Session content will be extracted from markdown headers.")
    print("   Duplicates will be skipped.")
    response = input("\n   Continue? (y/n): ")

    if response.lower() != 'y':
        print("❌ Import cancelled")
        return 0

    # Import to database
    success = import_to_database(sessions)

    if success:
        print("\n✅ Import complete!")
        return 0
    else:
        print("\n❌ Import failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
