#!/usr/bin/env python3
"""
Data Export Utility
===================

Export database data back to markdown format for backup or synchronization.

Usage:
    # Export all data
    python scripts/export_data.py --all --user-id 1

    # Export specific data types
    python scripts/export_data.py --health --user-id 1

    # Export to custom directory
    python scripts/export_data.py --all --user-id 1 --output exports/
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, date

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def setup_database():
    """Setup database connection."""
    from dotenv import load_dotenv
    load_dotenv()

    from website import create_app
    from website.models import db

    app = create_app()
    return app.app_context(), db.session


def export_health_metrics(session, user_id: int, output_dir: Path):
    """Export health metrics to markdown table format."""
    from website.models import HealthMetric

    logger.info("Exporting health metrics...")

    metrics = session.query(HealthMetric).filter_by(
        user_id=user_id
    ).order_by(HealthMetric.recorded_date).all()

    if not metrics:
        logger.warning("No health metrics found")
        return

    output_file = output_dir / 'check-in-log.md'

    with open(output_file, 'w') as f:
        # Write header
        f.write("| Date | Weight (lbs) | Body Fat % | Notes |\n")
        f.write("| :--------- | :----------- | :--------- | :---------------------------------- |\n")

        # Write data rows
        for metric in metrics:
            date_str = metric.recorded_date.strftime('%Y-%m-%d')
            weight = f"{metric.weight_lbs:.1f}" if metric.weight_lbs else "None"
            body_fat = f"{metric.body_fat_percentage:.1f}" if metric.body_fat_percentage else "None"
            notes = metric.notes if metric.notes else ""

            f.write(f"| {date_str} | {weight} | {body_fat} | {notes} |\n")

    logger.info(f"Exported {len(metrics)} health metrics to {output_file}")


def export_workouts(session, user_id: int, output_dir: Path):
    """Export workout sessions to markdown table format."""
    from website.models import WorkoutSession, ExerciseLog

    logger.info("Exporting workout sessions...")

    sessions = session.query(WorkoutSession).filter_by(
        user_id=user_id
    ).order_by(WorkoutSession.session_date).all()

    if not sessions:
        logger.warning("No workout sessions found")
        return

    output_file = output_dir / 'exercise-log.md'

    with open(output_file, 'w') as f:
        # Write header
        f.write("# Exercise Log\n\n")
        f.write("This log is used to track your workout performance.\n\n")
        f.write("| Date | Phase | Workout | Exercise | Sets x Reps | Notes |\n")
        f.write("| :--- | :---- | :------ | :------- | :---------- | :---------- |\n")

        # Write data rows
        exercise_count = 0
        for workout_session in sessions:
            for exercise in workout_session.exercise_logs:
                date_str = workout_session.session_date.strftime('%Y-%m-%d')
                phase = workout_session.program_phase or ""
                workout_type = workout_session.session_type.value
                exercise_name = exercise.exercise_name

                # Format sets and reps
                if exercise.sets and exercise.reps:
                    sets_reps = f"{exercise.sets} sets of {exercise.reps} reps"
                elif exercise.duration_seconds:
                    minutes = exercise.duration_seconds // 60
                    sets_reps = f"{minutes} minutes"
                else:
                    sets_reps = "N/A"

                notes = exercise.notes or ""

                f.write(f"| {date_str} | {phase} | {workout_type} | {exercise_name} | {sets_reps} | {notes} |\n")
                exercise_count += 1

    logger.info(f"Exported {len(sessions)} sessions with {exercise_count} exercises to {output_file}")


def export_meals(session, user_id: int, output_dir: Path):
    """Export meal logs to markdown table format."""
    from website.models import MealLog

    logger.info("Exporting meal logs...")

    meals = session.query(MealLog).filter_by(
        user_id=user_id
    ).order_by(MealLog.meal_date, MealLog.meal_time).all()

    if not meals:
        logger.warning("No meal logs found")
        return

    output_file = output_dir / 'meal-log.md'

    with open(output_file, 'w') as f:
        # Write header
        f.write("# Meal Log\n\n")
        f.write("| Date | Meal | Food/Drink | Calories (est.) | Notes |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")

        # Group by date for daily totals
        current_date = None
        daily_calories = 0

        for meal in meals:
            date_str = meal.meal_date.strftime('%Y-%m-%d')

            # Write daily total when date changes
            if current_date and current_date != meal.meal_date:
                f.write(f"| **{current_date.strftime('%Y-%m-%d')}** | | **DAILY TOTAL** | **~{daily_calories}** | |\n")
                daily_calories = 0

            current_date = meal.meal_date

            meal_type = meal.meal_type.value.replace('_', ' ').title()
            description = meal.description or ""
            calories = f"~{meal.calories}" if meal.calories else ""
            notes = meal.notes or ""

            f.write(f"| {date_str} | {meal_type} | {description} | {calories} | {notes} |\n")

            if meal.calories:
                daily_calories += meal.calories

        # Write final daily total
        if current_date:
            f.write(f"| **{current_date.strftime('%Y-%m-%d')}** | | **DAILY TOTAL** | **~{daily_calories}** | |\n")

    logger.info(f"Exported {len(meals)} meal logs to {output_file}")


def export_coaching(session, user_id: int, output_dir: Path):
    """Export coaching sessions to markdown format."""
    from website.models import CoachingSession

    logger.info("Exporting coaching sessions...")

    sessions = session.query(CoachingSession).filter_by(
        user_id=user_id
    ).order_by(CoachingSession.session_date.desc()).all()

    if not sessions:
        logger.warning("No coaching sessions found")
        return

    output_file = output_dir / 'Coaching_sessions.md'

    with open(output_file, 'w') as f:
        f.write("# Coaching Sessions Log\n\n")

        for coaching_session in sessions:
            date_str = coaching_session.session_date.strftime('%Y-%m-%d')
            title = coaching_session.topics[0] if coaching_session.topics else "Session"

            f.write(f"## {date_str}: {title}\n\n")

            # Write coach info if available
            if hasattr(coaching_session, 'coach') and coaching_session.coach:
                f.write(f"**Trainer:** {coaching_session.coach.username}\n\n")

            # Write subject/feedback
            if coaching_session.coach_feedback:
                f.write(f"**Subject:** {coaching_session.coach_feedback}\n\n")

            # Write discussion notes
            if coaching_session.discussion_notes:
                f.write(f"{coaching_session.discussion_notes}\n\n")

            # Write action items
            if coaching_session.action_items:
                f.write("**Action Items:**\n")
                for item in coaching_session.action_items:
                    f.write(f"- {item}\n")
                f.write("\n")

            f.write("---\n\n")

    logger.info(f"Exported {len(sessions)} coaching sessions to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Export database data to markdown format')

    # Export selection
    parser.add_argument('--all', action='store_true', help='Export all data types')
    parser.add_argument('--health', action='store_true', help='Export health metrics')
    parser.add_argument('--workouts', action='store_true', help='Export workouts')
    parser.add_argument('--meals', action='store_true', help='Export meals')
    parser.add_argument('--coaching', action='store_true', help='Export coaching sessions')

    # User and output
    parser.add_argument('--user-id', type=int, required=True, help='User ID to export data for')
    parser.add_argument('--output', type=str, help='Output directory (default: exports/TIMESTAMP)')

    args = parser.parse_args()

    if not any([args.all, args.health, args.workouts, args.meals, args.coaching]):
        parser.print_help()
        sys.exit(1)

    # Setup output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = PROJECT_ROOT / 'exports' / timestamp

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("DATA EXPORT UTILITY")
    logger.info("=" * 60)
    logger.info(f"User ID: {args.user_id}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 60)

    # Setup database
    app_context, db_session = setup_database()

    with app_context:
        try:
            # Run exports
            if args.all or args.health:
                export_health_metrics(db_session, args.user_id, output_dir)

            if args.all or args.workouts:
                export_workouts(db_session, args.user_id, output_dir)

            if args.all or args.meals:
                export_meals(db_session, args.user_id, output_dir)

            if args.all or args.coaching:
                export_coaching(db_session, args.user_id, output_dir)

            logger.info("=" * 60)
            logger.info(f"EXPORT COMPLETE: {output_dir}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    main()
