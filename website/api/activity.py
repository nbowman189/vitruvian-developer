"""
Activity Feed API
==================

RESTful API endpoint for aggregated activity feed.

Endpoints:
- GET    /api/activity/recent     - Get recent activity feed
"""

from flask import Blueprint, request
from flask_login import current_user
from datetime import datetime, timedelta

from ..models import db
from ..models.health import HealthMetric
from ..models.workout import WorkoutSession
from ..models.coaching import CoachingSession
from ..models.nutrition import MealLog
from . import (
    success_response,
    error_response,
    require_active_user,
    logger
)

# Create activity API sub-blueprint
activity_api_bp = Blueprint('activity_api', __name__, url_prefix='/activity')


@activity_api_bp.route('/recent', methods=['GET'])
@require_active_user
def get_recent_activity():
    """
    Get recent activity feed from all sources.

    Query Parameters:
        - limit (int): Maximum number of items (default: 10, max: 50)
        - days (int): Number of days to look back (default: 30)

    Returns:
        200: List of recent activities sorted by date
    """
    try:
        limit = int(request.args.get('limit', 10))
        limit = max(1, min(50, limit))  # Limit to 1-50 items
    except (ValueError, TypeError):
        limit = 10

    try:
        days = int(request.args.get('days', 30))
        days = max(1, min(90, days))  # Limit to 1-90 days
    except (ValueError, TypeError):
        days = 30

    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    activities = []

    # Get recent health metrics
    health_metrics = HealthMetric.query.filter(
        HealthMetric.user_id == current_user.id,
        HealthMetric.recorded_date >= start_date
    ).order_by(HealthMetric.recorded_date.desc()).limit(limit).all()

    for metric in health_metrics:
        weight_text = f"{metric.weight_lbs} lbs" if metric.weight_lbs else ""
        bf_text = f"{metric.body_fat_percentage}% BF" if metric.body_fat_percentage else ""
        description_parts = [p for p in [weight_text, bf_text] if p]
        description = " • ".join(description_parts) if description_parts else "Health check-in"

        activities.append({
            'type': 'health',
            'title': 'Health Metrics Logged',
            'description': description,
            'date': metric.recorded_date.isoformat(),
            'timestamp': datetime.combine(metric.recorded_date, datetime.min.time())
        })

    # Get recent workouts
    workouts = WorkoutSession.query.filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.session_date >= start_date
    ).order_by(WorkoutSession.session_date.desc()).limit(limit).all()

    for workout in workouts:
        name = workout.notes or workout.session_type.value.replace('_', ' ').title()
        duration = f"{workout.duration_minutes} min" if workout.duration_minutes else ""
        exercises = f"{workout.total_exercises} exercises" if workout.total_exercises else ""
        description_parts = [p for p in [duration, exercises] if p]
        description = " • ".join(description_parts) if description_parts else name

        activities.append({
            'type': 'workout',
            'title': f'Workout: {name}',
            'description': description,
            'date': workout.session_date.isoformat(),
            'timestamp': datetime.combine(workout.session_date, datetime.min.time())
        })

    # Get recent coaching sessions
    coaching = CoachingSession.query.filter(
        CoachingSession.user_id == current_user.id,
        CoachingSession.session_date >= start_date
    ).order_by(CoachingSession.session_date.desc()).limit(limit).all()

    for session in coaching:
        description = session.coach_feedback or "Coaching session completed"
        if len(description) > 100:
            description = description[:97] + "..."

        activities.append({
            'type': 'coaching',
            'title': 'Coaching Session',
            'description': description,
            'date': session.session_date.isoformat(),
            'timestamp': datetime.combine(session.session_date, datetime.min.time())
        })

    # Get recent nutrition entries (group by date)
    meals = MealLog.query.filter(
        MealLog.user_id == current_user.id,
        MealLog.meal_date >= start_date
    ).all()

    # Group meals by date
    meals_by_date = {}
    for meal in meals:
        date_key = meal.meal_date
        if date_key not in meals_by_date:
            meals_by_date[date_key] = {
                'count': 0,
                'total_calories': 0,
                'total_protein': 0
            }
        meals_by_date[date_key]['count'] += 1
        meals_by_date[date_key]['total_calories'] += meal.calories or 0
        meals_by_date[date_key]['total_protein'] += meal.protein_g or 0

    # Create activity entries for each date with meals
    for date_key, data in meals_by_date.items():
        meal_text = f"{data['count']} meal" if data['count'] == 1 else f"{data['count']} meals"
        calories = f"{data['total_calories']} cal" if data['total_calories'] else ""
        protein = f"{int(data['total_protein'])}g protein" if data['total_protein'] else ""
        description_parts = [p for p in [meal_text, calories, protein] if p]
        description = " • ".join(description_parts)

        activities.append({
            'type': 'nutrition',
            'title': 'Nutrition Logged',
            'description': description,
            'date': date_key.isoformat(),
            'timestamp': datetime.combine(date_key, datetime.min.time())
        })

    # Sort all activities by timestamp (most recent first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)

    # Remove timestamp field before returning (was only for sorting)
    for activity in activities:
        del activity['timestamp']

    # Limit to requested number of items
    activities = activities[:limit]

    return success_response(
        data=activities,
        message=f'Retrieved {len(activities)} recent activities'
    )
