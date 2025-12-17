#!/usr/bin/env python3
"""
Import Health Data from Markdown Files
=======================================

This script imports all health-related data from markdown log files into the database:
- check-in-log.md → HealthMetric
- meal-log.md → MealLog
- exercise-log.md → WorkoutSession + ExerciseLog
- Coaching_sessions.md → CoachingSession

Usage:
    python scripts/import_health_data.py [--truncate] [--user-id=1]

Options:
    --truncate    Clear existing data before importing
    --user-id=N   User ID to associate data with (default: 1)
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from website import create_app, db
from website.models.health import HealthMetric
from website.models.nutrition import MealLog, MealType
from website.models.workout import WorkoutSession, ExerciseLog, SessionType
from website.models.coaching import CoachingSession


class HealthDataImporter:
    def __init__(self, user_id=1, truncate=False):
        self.user_id = user_id
        self.truncate = truncate
        # Use absolute path for Docker container
        if os.path.exists('/Health_and_Fitness/data'):
            self.data_dir = Path('/Health_and_Fitness/data')
        else:
            self.data_dir = Path(__file__).parent.parent / 'Health_and_Fitness' / 'data'

        self.stats = {
            'health_metrics': 0,
            'meal_logs': 0,
            'workout_sessions': 0,
            'exercise_logs': 0,
            'coaching_sessions': 0
        }

    def run(self):
        """Main import process"""
        print("=" * 60)
        print("Health Data Import")
        print("=" * 60)
        print(f"User ID: {self.user_id}")
        print(f"Data Directory: {self.data_dir}")
        print(f"Truncate existing: {self.truncate}")
        print()

        if self.truncate:
            self.truncate_tables()

        # Import each data type
        self.import_health_metrics()
        self.import_meal_logs()
        self.import_exercise_logs()
        self.import_coaching_sessions()

        # Commit all changes
        db.session.commit()

        self.print_summary()

    def truncate_tables(self):
        """Clear existing data"""
        print("Truncating existing data...")

        ExerciseLog.query.delete()
        WorkoutSession.query.delete()
        MealLog.query.delete()
        HealthMetric.query.delete()
        CoachingSession.query.delete()

        db.session.commit()
        print("✓ All tables truncated\n")

    def import_health_metrics(self):
        """Import from check-in-log.md"""
        print("Importing health metrics...")
        file_path = self.data_dir / 'check-in-log.md'

        if not file_path.exists():
            print(f"  Warning: {file_path} not found, skipping")
            return

        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Skip header lines (first 2)
        for line in lines[2:]:
            line = line.strip()
            if not line or not line.startswith('|'):
                continue

            # Parse table row: | Date | Weight | Body Fat | Notes |
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) < 3:
                continue

            date_str, weight_str, bodyfat_str = parts[0], parts[1], parts[2]

            # Skip if no date
            if not date_str or date_str == 'Date':
                continue

            try:
                recorded_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Parse weight
                weight_lbs = None
                if weight_str and weight_str not in ('None', 'N/A', ''):
                    weight_lbs = float(weight_str)

                # Parse body fat
                body_fat = None
                if bodyfat_str and bodyfat_str not in ('None', 'N/A', ''):
                    body_fat = float(bodyfat_str)

                # Create metric
                metric = HealthMetric(
                    user_id=self.user_id,
                    recorded_date=recorded_date,
                    weight_lbs=weight_lbs,
                    body_fat_percentage=body_fat
                )
                db.session.add(metric)
                self.stats['health_metrics'] += 1

            except (ValueError, IndexError) as e:
                print(f"  Warning: Skipping invalid row: {line[:50]}...")
                continue

        print(f"✓ Imported {self.stats['health_metrics']} health metrics\n")

    def import_meal_logs(self):
        """Import from meal-log.md"""
        print("Importing meal logs...")
        file_path = self.data_dir / 'meal-log.md'

        if not file_path.exists():
            print(f"  Warning: {file_path} not found, skipping")
            return

        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Skip header lines (first 3)
        for line in lines[3:]:
            line = line.strip()
            if not line or not line.startswith('|'):
                continue

            # Skip DAILY TOTAL rows
            if 'DAILY TOTAL' in line:
                continue

            # Parse table row: | Date | Meal | Food/Drink | Calories | Notes |
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) < 4:
                continue

            date_str, meal_str, food_str, calories_str = parts[0], parts[1], parts[2], parts[3]
            notes = parts[4] if len(parts) > 4 else ''

            # Skip if no date or no food
            if not date_str or not food_str or date_str == 'Date':
                continue

            # Skip lines with only dashes or asterisks
            if date_str.startswith('**') or date_str.startswith('---'):
                continue

            try:
                meal_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Parse calories
                calories = None
                if calories_str and calories_str not in ('N/A', ''):
                    # Remove non-numeric characters except decimal point
                    calories_clean = re.sub(r'[^\d.]', '', calories_str)
                    if calories_clean:
                        calories = int(float(calories_clean))

                # Map meal type
                meal_type_map = {
                    'breakfast': MealType.BREAKFAST,
                    'morning snack': MealType.SNACK,
                    'lunch': MealType.LUNCH,
                    'afternoon snack': MealType.SNACK,
                    'dinner': MealType.DINNER,
                    'evening snack': MealType.SNACK,
                    'snack': MealType.SNACK
                }
                meal_type = meal_type_map.get(meal_str.lower(), MealType.OTHER)

                # Create meal log
                meal = MealLog(
                    user_id=self.user_id,
                    meal_date=meal_date,
                    meal_type=meal_type,
                    calories=calories,
                    description=food_str[:500] if food_str else None  # Limit length
                )
                db.session.add(meal)
                self.stats['meal_logs'] += 1

            except (ValueError, IndexError) as e:
                print(f"  Warning: Skipping invalid meal row: {line[:50]}...")
                continue

        print(f"✓ Imported {self.stats['meal_logs']} meal logs\n")

    def import_exercise_logs(self):
        """Import from exercise-log.md"""
        print("Importing exercise logs...")
        file_path = self.data_dir / 'exercise-log.md'

        if not file_path.exists():
            print(f"  Warning: {file_path} not found, skipping")
            return

        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Group exercises by date to create workout sessions
        sessions = {}  # date -> list of exercises

        # Skip header lines (first 6)
        for line in lines[6:]:
            line = line.strip()
            if not line or not line.startswith('|'):
                continue

            # Parse table row: | Date | Phase | Workout | Exercise | Sets x Reps | Notes |
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) < 5:
                continue

            date_str, phase, workout, exercise, sets_reps = parts[0], parts[1], parts[2], parts[3], parts[4]
            notes = parts[5] if len(parts) > 5 else ''

            # Skip if no date or no exercise
            if not date_str or not exercise or date_str == 'Date':
                continue

            try:
                session_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Group by date and workout type
                key = (session_date, workout)
                if key not in sessions:
                    sessions[key] = []

                sessions[key].append({
                    'exercise': exercise,
                    'sets_reps': sets_reps,
                    'notes': notes
                })

            except (ValueError, IndexError) as e:
                print(f"  Warning: Skipping invalid exercise row: {line[:50]}...")
                continue

        # Create workout sessions and exercise logs
        for (session_date, workout_name), exercises in sessions.items():
            # Determine session type
            workout_lower = workout_name.lower()
            if 'strength' in workout_lower or 'ring' in workout_lower or 'bodyweight' in workout_lower:
                session_type = SessionType.STRENGTH
            elif 'cardio' in workout_lower or 'walk' in workout_lower:
                session_type = SessionType.CARDIO
            elif 'tai chi' in workout_lower or 'martial' in workout_lower:
                session_type = SessionType.MARTIAL_ARTS
            elif 'mobility' in workout_lower:
                session_type = SessionType.FLEXIBILITY
            else:
                session_type = SessionType.MIXED

            # Create workout session
            session = WorkoutSession(
                user_id=self.user_id,
                session_date=session_date,
                session_type=session_type,
                notes=workout_name
            )
            db.session.add(session)
            db.session.flush()  # Get session.id

            self.stats['workout_sessions'] += 1

            # Add exercises
            for ex in exercises:
                exercise_log = ExerciseLog(
                    workout_session_id=session.id,
                    exercise_name=ex['exercise'],
                    notes=f"{ex['sets_reps']} - {ex['notes']}" if ex['notes'] else ex['sets_reps']
                )
                db.session.add(exercise_log)
                self.stats['exercise_logs'] += 1

        print(f"✓ Imported {self.stats['workout_sessions']} workout sessions")
        print(f"✓ Imported {self.stats['exercise_logs']} exercise logs\n")

    def import_coaching_sessions(self):
        """Import from Coaching_sessions.md"""
        print("Importing coaching sessions...")
        file_path = self.data_dir / 'Coaching_sessions.md'

        if not file_path.exists():
            print(f"  Warning: {file_path} not found, skipping")
            return

        with open(file_path, 'r') as f:
            content = f.read()

        # Split by H2 headers (##) which contain dates
        sections = re.split(r'\n## ', content)

        for section in sections[1:]:  # Skip first (title)
            # Extract date from header: "2025-12-10: Title"
            match = re.match(r'(\d{4}-\d{2}-\d{2}):\s*(.+)', section)
            if not match:
                continue

            date_str, title = match.groups()

            try:
                session_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Get the rest of the content
                content_lines = section.split('\n', 1)
                discussion = content_lines[1] if len(content_lines) > 1 else ''

                # Create coaching session
                coaching = CoachingSession(
                    user_id=self.user_id,
                    coach_id=self.user_id,  # Self-coaching
                    session_date=session_date,
                    discussion_notes=discussion[:2000],  # Limit length
                    coach_feedback=title[:500]  # Store title as feedback
                )
                db.session.add(coaching)
                self.stats['coaching_sessions'] += 1

            except (ValueError, IndexError) as e:
                print(f"  Warning: Skipping invalid coaching session: {date_str}")
                continue

        print(f"✓ Imported {self.stats['coaching_sessions']} coaching sessions\n")

    def print_summary(self):
        """Print import summary"""
        print("=" * 60)
        print("Import Complete!")
        print("=" * 60)
        print(f"Health Metrics:     {self.stats['health_metrics']:>5} records")
        print(f"Meal Logs:          {self.stats['meal_logs']:>5} records")
        print(f"Workout Sessions:   {self.stats['workout_sessions']:>5} records")
        print(f"Exercise Logs:      {self.stats['exercise_logs']:>5} records")
        print(f"Coaching Sessions:  {self.stats['coaching_sessions']:>5} records")
        print("=" * 60)


def main():
    """Main entry point"""
    # Parse command line arguments
    truncate = '--truncate' in sys.argv

    user_id = 1
    for arg in sys.argv:
        if arg.startswith('--user-id='):
            user_id = int(arg.split('=')[1])

    # Create app and import data
    app = create_app()
    with app.app_context():
        importer = HealthDataImporter(user_id=user_id, truncate=truncate)
        importer.run()


if __name__ == '__main__':
    main()
