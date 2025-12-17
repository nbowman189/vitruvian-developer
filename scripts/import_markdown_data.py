#!/usr/bin/env python3
"""
Import data from markdown files into the database.

This script parses the Health_and_Fitness data markdown files and populates
the database with health metrics, meal logs, workout sessions, and coaching sessions.
"""

import sys
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import from website package
sys.path.insert(0, str(Path(__file__).parent.parent))

from website.app import create_app
from website.models import db
from website.models.health import HealthMetric
from website.models.nutrition import MealLog, MealType
from website.models.workout import WorkoutSession, SessionType, ExerciseLog
from website.models.coaching import CoachingSession


def parse_check_in_log(file_path, user_id):
    """Parse check-in-log.md and create health metrics."""
    print(f"\n📊 Importing health metrics from {file_path}...")

    with open(file_path, 'r') as f:
        lines = f.readlines()

    count = 0
    skipped = 0
    for line in lines[1:]:  # Skip just the first header line
        line = line.strip()
        if not line or line.count('|') < 3:
            continue

        # Skip the separator line (| :--- | :--- |)
        if ':---' in line:
            continue

        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 5:
            continue

        try:
            date_str = parts[1]
            weight_str = parts[2]
            bodyfat_str = parts[3]
            notes = parts[4] if len(parts) > 4 else ''

            # Skip if not a valid date
            if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                skipped += 1
                continue

            # Parse values
            recorded_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            weight_lbs = float(weight_str) if weight_str and weight_str.lower() not in ['none', 'n/a', ''] else None
            body_fat = float(bodyfat_str) if bodyfat_str and bodyfat_str.lower() not in ['none', 'n/a', ''] else None

            # Skip if no weight data
            if not weight_lbs:
                skipped += 1
                continue

            # Check if already exists
            existing = HealthMetric.query.filter_by(
                user_id=user_id,
                recorded_date=recorded_date
            ).first()

            if existing:
                continue

            # Create new health metric
            metric = HealthMetric(
                user_id=user_id,
                recorded_date=recorded_date,
                weight_lbs=weight_lbs,
                body_fat_percentage=body_fat,
                notes=notes if notes else None
            )
            db.session.add(metric)
            count += 1

        except (ValueError, IndexError) as e:
            print(f"  ⚠️  Skipping line: {line[:50]}... ({e})")
            skipped += 1
            continue

    db.session.commit()
    print(f"  ✅ Imported {count} health metrics (skipped {skipped} invalid/duplicate entries)")
    return count


def parse_meal_log(file_path, user_id):
    """Parse meal-log.md and create meal logs."""
    print(f"\n🍽️  Importing meals from {file_path}...")

    with open(file_path, 'r') as f:
        lines = f.readlines()

    count = 0
    for line in lines[3:]:  # Skip header rows
        line = line.strip()
        if not line or '**DAILY TOTAL**' in line:
            continue

        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 6:
            continue

        try:
            date_str = parts[1]
            meal_type_str = parts[2]
            food_desc = parts[3]
            calories_str = parts[4]
            notes = parts[5] if len(parts) > 5 else ''

            # Skip if not a valid date
            if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                continue

            # Parse values
            meal_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Map meal type
            meal_type_lower = meal_type_str.lower()
            if 'breakfast' in meal_type_lower:
                meal_type = MealType.BREAKFAST
            elif 'lunch' in meal_type_lower:
                meal_type = MealType.LUNCH
            elif 'dinner' in meal_type_lower:
                meal_type = MealType.DINNER
            elif 'snack' in meal_type_lower:
                meal_type = MealType.SNACK
            else:
                meal_type = MealType.OTHER

            # Extract calories
            calories_match = re.search(r'~?(\d+)', calories_str)
            calories = int(calories_match.group(1)) if calories_match else None

            # Create new meal log
            meal = MealLog(
                user_id=user_id,
                meal_date=meal_date,
                meal_type=meal_type
            )

            # Set nutrition data
            meal.nutrition = {
                'calories': calories,
                'protein_g': None,
                'carbs_g': None,
                'fat_g': None
            }

            # Set meal details
            meal.meal_details = {
                'description': food_desc,
                'foods': None,
                'recipe_name': None
            }

            meal.notes = notes if notes else None

            db.session.add(meal)
            count += 1

        except (ValueError, IndexError) as e:
            print(f"  ⚠️  Skipping line: {line[:50]}... ({e})")
            continue

    db.session.commit()
    print(f"  ✅ Imported {count} meals")
    return count


def parse_exercise_log(file_path, user_id):
    """Parse exercise-log.md and create workout sessions."""
    print(f"\n💪 Importing workouts from {file_path}...")

    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Group exercises by date and workout
    workout_sessions = {}

    for line in lines[6:]:  # Skip header rows
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:
            continue

        try:
            date_str = parts[1]
            phase = parts[2]
            workout_name = parts[3]
            exercise_name = parts[4]
            sets_reps = parts[5]
            notes = parts[6] if len(parts) > 6 else ''

            # Skip if not a valid date
            if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                continue

            session_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Create session key
            session_key = (session_date, workout_name)

            if session_key not in workout_sessions:
                # Determine session type
                workout_lower = workout_name.lower()
                if 'walk' in workout_lower or 'cardio' in workout_lower:
                    session_type = SessionType.CARDIO
                elif 'tai chi' in workout_lower or 'mobility' in workout_lower:
                    session_type = SessionType.FLEXIBILITY
                elif 'martial' in workout_lower or 'serbatik' in workout_lower:
                    session_type = SessionType.MARTIAL_ARTS
                else:
                    session_type = SessionType.STRENGTH

                workout_sessions[session_key] = {
                    'session_date': session_date,
                    'session_type': session_type,
                    'workout_name': workout_name,
                    'notes': notes,
                    'exercises': []
                }

            # Add exercise if it has a name
            if exercise_name and exercise_name.strip():
                workout_sessions[session_key]['exercises'].append({
                    'name': exercise_name,
                    'sets_reps': sets_reps,
                    'notes': notes
                })

        except (ValueError, IndexError) as e:
            print(f"  ⚠️  Skipping line: {line[:50]}... ({e})")
            continue

    # Create workout sessions in database
    count = 0
    for session_data in workout_sessions.values():
        # Check if already exists (by date and type)
        existing = WorkoutSession.query.filter_by(
            user_id=user_id,
            session_date=session_data['session_date'],
            session_type=session_data['session_type']
        ).first()

        if existing:
            continue

        # Combine workout name and notes
        combined_notes = f"{session_data['workout_name']}"
        if session_data['notes']:
            combined_notes += f" - {session_data['notes']}"

        workout = WorkoutSession(
            user_id=user_id,
            session_date=session_data['session_date'],
            session_type=session_data['session_type'],
            notes=combined_notes
        )
        db.session.add(workout)
        db.session.flush()  # Get workout ID

        # Add exercises
        for ex_data in session_data['exercises']:
            exercise = ExerciseLog(
                workout_id=workout.id,
                exercise_name=ex_data['name'],
                notes=ex_data['notes']
            )
            db.session.add(exercise)

        count += 1

    db.session.commit()
    print(f"  ✅ Imported {count} workout sessions")
    return count


def parse_coaching_sessions(file_path, user_id):
    """Parse Coaching_sessions.md and create coaching sessions."""
    print(f"\n🎯 Importing coaching sessions from {file_path}...")

    with open(file_path, 'r') as f:
        content = f.read()

    # Split by session headers (## date: title)
    sessions = re.split(r'##\s+(\d{4}-\d{2}-\d{2}):\s+([^\n]+)', content)

    count = 0
    # Process in groups of 3 (text before, date, title, content)
    for i in range(1, len(sessions), 3):
        if i + 2 > len(sessions):
            break

        try:
            date_str = sessions[i]
            title = sessions[i + 1]
            session_content = sessions[i + 2]

            session_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Check if already exists
            existing = CoachingSession.query.filter_by(
                user_id=user_id,
                session_date=session_date
            ).first()

            if existing:
                continue

            # Create coaching session
            session = CoachingSession(
                user_id=user_id,
                coach_id=user_id,  # Self-coaching via AI
                session_date=session_date,
                discussion_notes=session_content.strip(),
                coach_feedback=title.strip()
            )
            db.session.add(session)
            count += 1

        except (ValueError, IndexError) as e:
            print(f"  ⚠️  Skipping session: {e}")
            continue

    db.session.commit()
    print(f"  ✅ Imported {count} coaching sessions")
    return count


def main():
    """Main import function."""
    app = create_app()

    with app.app_context():
        # Get or create admin user
        from website.models.user import User
        user = User.query.filter_by(username='admin').first()

        if not user:
            print("❌ Admin user not found. Please create an admin user first.")
            return

        print(f"📥 Importing data for user: {user.username}")

        # Define file paths
        # Check if running in Docker (files at root) or locally (files in parent dir)
        docker_base_path = Path('/Health_and_Fitness/data')
        local_base_path = Path(__file__).parent.parent / 'Health_and_Fitness' / 'data'

        base_path = docker_base_path if docker_base_path.exists() else local_base_path

        check_in_log = base_path / 'check-in-log.md'
        meal_log = base_path / 'meal-log.md'
        exercise_log = base_path / 'exercise-log.md'
        coaching_sessions = base_path / 'Coaching_sessions.md'

        print(f"📂 Looking for data files in: {base_path}")

        # Import data
        total_health = parse_check_in_log(check_in_log, user.id) if check_in_log.exists() else 0
        total_meals = parse_meal_log(meal_log, user.id) if meal_log.exists() else 0
        total_workouts = parse_exercise_log(exercise_log, user.id) if exercise_log.exists() else 0
        total_coaching = parse_coaching_sessions(coaching_sessions, user.id) if coaching_sessions.exists() else 0

        print(f"\n" + "="*60)
        print(f"✅ Import Complete!")
        print(f"="*60)
        print(f"  📊 Health Metrics:     {total_health}")
        print(f"  🍽️  Meal Logs:          {total_meals}")
        print(f"  💪 Workout Sessions:   {total_workouts}")
        print(f"  🎯 Coaching Sessions:  {total_coaching}")
        print(f"="*60)


if __name__ == '__main__':
    main()
