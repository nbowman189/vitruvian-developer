"""
Create sample data for dashboard testing
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app first to initialize everything
from website import create_app, db
from website.models.user import User
from website.models.health import HealthMetric
from website.models.workout import WorkoutSession, ExerciseLog, SessionType
from website.models.nutrition import MealLog, MealType
from website.models.coaching import CoachingSession, UserGoal, GoalStatus

def create_sample_data():
    """Create sample data for all models"""
    app = create_app()

    with app.app_context():
        # Get admin user
        user = User.query.filter_by(username='admin').first()

        if not user:
            print("❌ Admin user not found. Please create admin user first.")
            return

        print(f"✅ Found user: {user.username}")

        # Create health metrics for the past 7 days
        print("\n📊 Creating health metrics...")
        today = datetime.now().date()

        for i in range(7):
            date = today - timedelta(days=i)

            # Check if metric already exists
            existing = HealthMetric.query.filter_by(
                user_id=user.id,
                recorded_date=date
            ).first()

            if not existing:
                metric = HealthMetric(
                    user_id=user.id,
                    recorded_date=date,
                    weight_lbs=180 - (i * 0.5),  # Gradual weight loss
                    body_fat_percentage=20 - (i * 0.2),
                    energy_level=7 + (i % 2),
                    mood=8,
                    sleep_quality=7 + (i % 3)
                )
                db.session.add(metric)
                print(f"  ✓ Added health metric for {date}")

        # Create workout sessions for the past week
        print("\n💪 Creating workout sessions...")
        workout_dates = [today - timedelta(days=i) for i in [0, 2, 4, 6]]

        for idx, date in enumerate(workout_dates):
            existing = WorkoutSession.query.filter_by(
                user_id=user.id,
                session_date=date
            ).first()

            if not existing:
                workout = WorkoutSession(
                    user_id=user.id,
                    session_date=date,
                    session_type=SessionType.STRENGTH if idx % 2 == 0 else SessionType.CARDIO,
                    name=f"{'Upper Body' if idx % 2 == 0 else 'Running'} Workout",
                    duration_minutes=60 if idx % 2 == 0 else 30,
                    intensity=8
                )
                db.session.add(workout)
                db.session.flush()

                # Add exercises to strength workouts
                if idx % 2 == 0:
                    for ex_idx in range(3):
                        exercise = ExerciseLog(
                            workout_id=workout.id,
                            exercise_name=["Bench Press", "Squats", "Deadlifts"][ex_idx],
                            sets=3,
                            reps=10,
                            weight_lbs=135 + (ex_idx * 50),
                            order_index=ex_idx
                        )
                        db.session.add(exercise)

                print(f"  ✓ Added workout for {date}")

        # Create nutrition logs for the past 7 days
        print("\n🍽️  Creating nutrition logs...")

        for i in range(7):
            date = today - timedelta(days=i)

            # Create 3 meals per day
            for meal_idx, meal_type in enumerate([MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]):
                existing = MealLog.query.filter(
                    MealLog.user_id == user.id,
                    MealLog.meal_date == date,
                    MealLog.meal_type == meal_type
                ).first()

                if not existing:
                    meal = MealLog(
                        user_id=user.id,
                        meal_date=date,
                        meal_type=meal_type,
                        meal_name=f"{meal_type.value.title()} meal",
                        calories=500 + (meal_idx * 100),
                        protein_g=30 + (meal_idx * 10),
                        carbs_g=50 + (meal_idx * 10),
                        fat_g=15 + (meal_idx * 5),
                        planned_meal=True
                    )
                    db.session.add(meal)

            print(f"  ✓ Added meals for {date}")

        # Create coaching sessions
        print("\n🎯 Creating coaching sessions...")

        # Past session
        past_date = today - timedelta(days=5)
        existing = CoachingSession.query.filter_by(
            user_id=user.id,
            session_date=past_date
        ).first()

        if not existing:
            session = CoachingSession(
                user_id=user.id,
                session_date=past_date,
                coach_name="Coach Alex",
                focus_areas="Progressive overload and nutrition consistency",
                notes="Great progress this week! Keep pushing.",
                action_items="Continue current program, add 5lbs to major lifts"
            )
            db.session.add(session)
            print(f"  ✓ Added coaching session for {past_date}")

        # Future session
        future_date = today + timedelta(days=3)
        existing = CoachingSession.query.filter_by(
            user_id=user.id,
            session_date=future_date
        ).first()

        if not existing:
            session = CoachingSession(
                user_id=user.id,
                session_date=future_date,
                coach_name="Coach Alex",
                focus_areas="Check-in and program adjustment"
            )
            db.session.add(session)
            print(f"  ✓ Added future coaching session for {future_date}")

        # Create goals
        print("\n🎯 Creating goals...")

        goal_titles = [
            ("Reach 175 lbs", "Weight loss goal"),
            ("Bench Press 225 lbs", "Strength goal"),
            ("Run 5K under 25 minutes", "Cardio goal")
        ]

        for title, description in goal_titles:
            existing = UserGoal.query.filter_by(
                user_id=user.id,
                title=title
            ).first()

            if not existing:
                goal = UserGoal(
                    user_id=user.id,
                    title=title,
                    description=description,
                    target_date=today + timedelta(days=30),
                    status=GoalStatus.ACTIVE,
                    progress_percentage=25
                )
                db.session.add(goal)
                print(f"  ✓ Added goal: {title}")

        # Commit all changes
        db.session.commit()
        print("\n✅ Sample data created successfully!")
        print(f"\n📝 Summary:")
        print(f"  - Health metrics: 7 days")
        print(f"  - Workouts: 4 sessions")
        print(f"  - Nutrition: 21 meals (3/day × 7 days)")
        print(f"  - Coaching: 2 sessions (1 past, 1 future)")
        print(f"  - Goals: 3 active goals")

if __name__ == '__main__':
    create_sample_data()
