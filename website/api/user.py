"""
User Profile API
================

RESTful API endpoints for user profile and dashboard.

Endpoints:
- GET    /api/user/profile       - Get current user profile
- PUT    /api/user/profile       - Update user profile
- GET    /api/user/dashboard     - Get dashboard data
- PUT    /api/user/settings      - Update user settings
"""

from flask import Blueprint, request
from flask_login import current_user
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta

from ..models import db
from ..models.user import User
from ..models.health import HealthMetric
from ..models.workout import WorkoutSession
from ..models.coaching import UserGoal, GoalStatus
from . import (
    success_response,
    error_response,
    require_active_user,
    validate_request_data,
    logger
)

# Create user API sub-blueprint
user_api_bp = Blueprint('user_api', __name__, url_prefix='/user')


@user_api_bp.route('/profile', methods=['GET'])
@require_active_user
def get_profile():
    """
    Get current user's profile.

    Returns:
        200: User profile data
    """
    return success_response(
        data=current_user.to_dict(include_sensitive=True),
        message='Profile retrieved successfully'
    )


@user_api_bp.route('/profile', methods=['PUT'])
@require_active_user
def update_profile():
    """
    Update current user's profile.

    Request Body:
        - full_name (str, optional): Full name
        - bio (str, optional): User bio
        - profile_photo_url (str, optional): Profile photo URL

    Returns:
        200: Updated user profile
        400: Validation error
    """
    optional_fields = ['full_name', 'bio', 'profile_photo_url']

    is_valid, result = validate_request_data(required_fields=None, optional_fields=optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    try:
        for key, value in data.items():
            setattr(current_user, key, value)

        db.session.commit()

        logger.info(f'User {current_user.id} updated profile')

        return success_response(
            data=current_user.to_dict(include_sensitive=True),
            message='Profile updated successfully'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating profile: {e}', exc_info=True)
        return error_response('Failed to update profile', errors=[str(e)], status_code=500)


@user_api_bp.route('/dashboard', methods=['GET'])
@require_active_user
def get_dashboard():
    """
    Get dashboard data for the current user.

    Includes:
    - Recent health metrics
    - Recent workouts
    - Active goals
    - Progress summary

    Query Parameters:
        - days (int): Number of days to include (default: 30)

    Returns:
        200: Dashboard data
    """
    try:
        days = int(request.args.get('days', 30))
        days = max(1, min(365, days))
    except (ValueError, TypeError):
        days = 30

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Get recent health metrics
    recent_metrics = HealthMetric.query.filter(
        and_(
            HealthMetric.user_id == current_user.id,
            HealthMetric.recorded_date >= start_date
        )
    ).order_by(HealthMetric.recorded_date.desc()).limit(10).all()

    latest_metric = recent_metrics[0] if recent_metrics else None

    # Get recent workouts
    recent_workouts = WorkoutSession.query.filter(
        and_(
            WorkoutSession.user_id == current_user.id,
            WorkoutSession.session_date >= start_date
        )
    ).order_by(WorkoutSession.session_date.desc()).limit(10).all()

    # Get active goals
    active_goals = UserGoal.query.filter_by(
        user_id=current_user.id,
        status=GoalStatus.ACTIVE
    ).order_by(UserGoal.target_date.asc()).all()

    # Calculate statistics
    total_workouts = len(recent_workouts)
    total_metrics = len(recent_metrics)

    # Weight trend (if available)
    weight_trend = None
    if len(recent_metrics) >= 2:
        first_metric = recent_metrics[-1]
        if latest_metric and latest_metric.weight_lbs and first_metric.weight_lbs:
            weight_change = latest_metric.weight_lbs - first_metric.weight_lbs
            weight_trend = {
                'current': latest_metric.weight_lbs,
                'previous': first_metric.weight_lbs,
                'change': round(weight_change, 2),
                'direction': 'up' if weight_change > 0 else 'down' if weight_change < 0 else 'stable'
            }

    # Workout frequency
    workout_frequency = None
    if total_workouts > 0:
        workouts_per_week = (total_workouts / days) * 7
        workout_frequency = {
            'total_workouts': total_workouts,
            'workouts_per_week': round(workouts_per_week, 1),
            'days_period': days
        }

    # Goals summary
    goals_summary = {
        'total_active': len(active_goals),
        'on_track': sum(1 for g in active_goals if not g.is_overdue),
        'overdue': sum(1 for g in active_goals if g.is_overdue),
        'completion_rate': 0  # Will calculate from all goals
    }

    # Calculate overall goal completion rate
    all_goals = UserGoal.query.filter_by(user_id=current_user.id).all()
    if all_goals:
        completed_goals = sum(1 for g in all_goals if g.status == GoalStatus.COMPLETED)
        goals_summary['completion_rate'] = round((completed_goals / len(all_goals)) * 100, 1)

    # Streaks (simplified version)
    streaks = {
        'current_workout_streak': 0,  # Placeholder for future implementation
        'current_logging_streak': 0   # Placeholder for future implementation
    }

    dashboard = {
        'user': current_user.to_dict(),
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days
        },
        'latest_metric': latest_metric.to_dict() if latest_metric else None,
        'recent_metrics': [m.to_dict() for m in recent_metrics[:5]],
        'recent_workouts': [w.to_dict() for w in recent_workouts[:5]],
        'active_goals': [g.to_dict() for g in active_goals[:5]],
        'statistics': {
            'weight_trend': weight_trend,
            'workout_frequency': workout_frequency,
            'goals_summary': goals_summary,
            'streaks': streaks,
        }
    }

    return success_response(
        data=dashboard,
        message=f'Dashboard data for {days} days'
    )


@user_api_bp.route('/settings', methods=['PUT'])
@require_active_user
def update_settings():
    """
    Update user settings.

    Request Body:
        - email (str, optional): Email address (must be unique)
        - username (str, optional): Username (must be unique)
        - current_password (str, required if changing password): Current password
        - new_password (str, optional): New password

    Returns:
        200: Updated settings
        400: Validation error
        401: Incorrect current password
        409: Email or username already exists
    """
    optional_fields = ['email', 'username', 'current_password', 'new_password']

    is_valid, result = validate_request_data(required_fields=None, optional_fields=optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # If changing password, verify current password
    if 'new_password' in data:
        if 'current_password' not in data:
            return error_response(
                'current_password is required when changing password',
                status_code=400
            )

        if not current_user.check_password(data['current_password']):
            return error_response('Current password is incorrect', status_code=401)

        # Set new password
        current_user.set_password(data['new_password'])
        logger.info(f'User {current_user.id} changed password')

    # Check email uniqueness
    if 'email' in data and data['email'] != current_user.email:
        existing = User.query.filter_by(email=data['email']).first()
        if existing:
            return error_response('Email already exists', status_code=409)
        current_user.email = data['email']
        logger.info(f'User {current_user.id} changed email')

    # Check username uniqueness
    if 'username' in data and data['username'] != current_user.username:
        existing = User.query.filter_by(username=data['username']).first()
        if existing:
            return error_response('Username already exists', status_code=409)
        current_user.username = data['username']
        logger.info(f'User {current_user.id} changed username')

    try:
        db.session.commit()

        return success_response(
            data=current_user.to_dict(include_sensitive=True),
            message='Settings updated successfully'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating settings: {e}', exc_info=True)
        return error_response('Failed to update settings', errors=[str(e)], status_code=500)
