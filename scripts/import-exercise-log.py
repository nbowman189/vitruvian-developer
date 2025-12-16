#!/usr/bin/env python3
"""
Import exercise data from exercise-log.md to database.
Groups individual exercises into workout sessions by date.
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from website import create_app, db
from website.models.workout import WorkoutSession, ExerciseLog, SessionType
from website.models.user import User


def parse_exercise_log(file_path):
    """Parse exercise-log.md and group by date."""

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return []

    print(f"📖 Reading file: {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')

    # Dictionary to group exercises by date
    daily_workouts = defaultdict(lambda: {'exercises': [], 'phase': None})

    in_table = False

    for line in lines:
        line = line.strip()

        # Check if we're in the table
        if line.startswith('| Date'):
            in_table = True
            continue

        # Skip separator
        if line.startswith('| :---'):
            continue

        # Parse data rows
        if in_table and line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]

            # parts[1]=date, parts[2]=phase, parts[3]=workout, parts[4]=exercise, parts[5]=sets/reps, parts[6]=notes
            if len(parts) >= 6:
                try:
                    date_str = parts[1]
                    phase = parts[2]
                    workout_type = parts[3]
                    exercise_name = parts[4]
                    sets_reps = parts[5]
                    notes = parts[6] if len(parts) > 6 else ""

                    # Skip empty date rows
                    if not date_str or date_str == '':
                        continue

                    # Parse date
                    try:
                        workout_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue

                    # Store phase for this date
                    if phase and not daily_workouts[workout_date]['phase']:
                        daily_workouts[workout_date]['phase'] = phase

                    # Add exercise to this date
                    daily_workouts[workout_date]['exercises'].append({
                        'workout_type': workout_type,
                        'exercise_name': exercise_name,
                        'sets_reps': sets_reps,
                        'notes': notes
                    })

                except (ValueError, IndexError) as e:
                    continue

        # Stop if we're out of the table
        if in_table and not line.startswith('|') and line and not line.startswith('#'):
            in_table = False

    # Convert to list of workout sessions
    workout_sessions = []
    for workout_date, data in sorted(daily_workouts.items()):
        # Determine primary workout type (most common)
        workout_types = [ex['workout_type'] for ex in data['exercises'] if ex['workout_type']]
        primary_workout_type = max(set(workout_types), key=workout_types.count) if workout_types else "Mixed Workout"

        # Map to SessionType enum
        session_type = SessionType.MIXED  # Default
        if 'rings' in primary_workout_type.lower() or 'strength' in primary_workout_type.lower():
            session_type = SessionType.STRENGTH
        elif 'walk' in primary_workout_type.lower() or 'cardio' in primary_workout_type.lower():
            session_type = SessionType.CARDIO
        elif 'tai chi' in primary_workout_type.lower() or 'flexibility' in primary_workout_type.lower():
            session_type = SessionType.FLEXIBILITY
        elif 'martial' in primary_workout_type.lower() or 'serbatik' in primary_workout_type.lower():
            session_type = SessionType.MARTIAL_ARTS

        # Estimate duration (rough calculation based on exercise count)
        exercise_count = len(data['exercises'])
        estimated_duration = min(exercise_count * 10, 180)  # ~10 min per exercise, max 3 hours

        # Build exercise summary
        exercise_summary = "\n".join([
            f"- {ex['exercise_name']}: {ex['sets_reps']}" if ex['sets_reps'] and ex['sets_reps'] != 'N/A'
            else f"- {ex['exercise_name']}"
            for ex in data['exercises']
            if ex['exercise_name']
        ])

        workout_sessions.append({
            'session_date': workout_date,
            'session_type': session_type,
            'duration_minutes': estimated_duration,
            'notes': exercise_summary[:1000],  # Limit length
            'exercises': data['exercises'],
            'phase': data['phase']
        })

    return workout_sessions


def import_to_database(workout_sessions, skip_duplicates=True):
    """Import workout sessions to database."""

    print(f"\n📊 Found {len(workout_sessions)} workout sessions to import")

    app = create_app()

    with app.app_context():
        # Get admin user
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User.query.first()

        if not user:
            print("❌ No users found in database!")
            return False

        print(f"📌 Associating all workouts with user: {user.username} (ID: {user.id})")

        imported = 0
        skipped = 0
        errors = 0

        for session_data in workout_sessions:
            try:
                # Check if session exists for this date
                existing = WorkoutSession.query.filter_by(
                    user_id=user.id,
                    session_date=session_data['session_date']
                ).first()

                if existing:
                    if skip_duplicates:
                        print(f"⏭️  Skipping {session_data['session_date']} (already exists)")
                        skipped += 1
                        continue
                    else:
                        existing.session_type = session_data['session_type']
                        existing.duration_minutes = session_data['duration_minutes']
                        existing.notes = session_data['notes']
                        print(f"🔄 Updated {session_data['session_date']}")
                else:
                    # Create workout session
                    workout = WorkoutSession(
                        user_id=user.id,
                        session_date=session_data['session_date'],
                        session_type=session_data['session_type'],
                        duration_minutes=session_data['duration_minutes'],
                        notes=session_data['notes'],
                        program_phase=session_data['phase']
                    )
                    db.session.add(workout)
                    db.session.flush()  # Get the workout ID

                    # Create individual exercise records
                    for ex_data in session_data['exercises'][:20]:  # Limit to 20 exercises per session
                        if ex_data['exercise_name']:
                            exercise = ExerciseLog(
                                workout_session_id=workout.id,
                                exercise_name=ex_data['exercise_name'],
                                notes=f"{ex_data['sets_reps']} - {ex_data['notes']}" if ex_data['notes'] else ex_data['sets_reps']
                            )
                            db.session.add(exercise)

                    print(f"✅ Imported {session_data['session_date']} - {session_data['session_type'].value} ({len(session_data['exercises'])} exercises)")

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
        print(f"   Total: {len(workout_sessions)}")

        return True


def main():
    """Main function."""

    print("====================================")
    print("Exercise Log Import Tool")
    print("====================================")
    print()

    # Default path
    default_path = Path(__file__).parent.parent / "Health_and_Fitness" / "data" / "exercise-log.md"

    # Allow custom path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = str(default_path)

    print(f"📂 Looking for: {file_path}")

    # Parse the file
    workout_sessions = parse_exercise_log(file_path)

    if not workout_sessions:
        print("❌ No workout sessions found in file")
        return 1

    # Ask for confirmation
    print(f"\n⚠️  About to import {len(workout_sessions)} workout sessions to the database")
    print("   Exercises will be grouped by date into sessions.")
    print("   Duplicates will be skipped.")
    response = input("\n   Continue? (y/n): ")

    if response.lower() != 'y':
        print("❌ Import cancelled")
        return 0

    # Import to database
    success = import_to_database(workout_sessions)

    if success:
        print("\n✅ Import complete!")
        return 0
    else:
        print("\n❌ Import failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
