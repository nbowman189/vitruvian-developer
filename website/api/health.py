"""
Health Metrics API
==================

RESTful API endpoints for health metrics tracking.

Endpoints:
- GET    /api/health/metrics          - List all metrics for authenticated user
- POST   /api/health/metrics          - Create new health metric entry
- GET    /api/health/metrics/<id>     - Get specific metric
- PUT    /api/health/metrics/<id>     - Update metric
- DELETE /api/health/metrics/<id>     - Delete metric
- GET    /api/health/metrics/latest   - Get most recent metric
- GET    /api/health/metrics/summary  - Get summary statistics
"""

from flask import Blueprint, request
from flask_login import current_user
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from ..models import db
from ..models.health import HealthMetric
from . import (
    success_response,
    error_response,
    paginated_response,
    require_active_user,
    validate_request_data,
    validate_pagination_params,
    validate_date_range_params,
    validate_date_format,
    logger
)

# Create health API sub-blueprint
health_api_bp = Blueprint('health_api', __name__, url_prefix='/health')


@health_api_bp.route('/metrics', methods=['GET'])
@require_active_user
def get_metrics():
    """
    Get health metrics for authenticated user with pagination and filtering.

    Query Parameters:
        - page (int): Page number (default: 1)
        - per_page (int): Items per page (default: 20, max: 100)
        - start_date (str): Filter by start date (ISO format: YYYY-MM-DD)
        - end_date (str): Filter by end date (ISO format: YYYY-MM-DD)
        - sort (str): Sort order ('asc' or 'desc', default: 'desc')

    Returns:
        200: Paginated list of health metrics
        400: Invalid parameters
    """
    # Validate pagination
    page, per_page = validate_pagination_params()

    # Validate date range
    is_valid, start_date, end_date, error_msg = validate_date_range_params()
    if not is_valid:
        return error_response(error_msg, status_code=400)

    # Get sort order
    sort_order = request.args.get('sort', 'desc').lower()
    if sort_order not in ['asc', 'desc']:
        return error_response("Invalid sort order. Must be 'asc' or 'desc'", status_code=400)

    # Build query
    query = HealthMetric.query.filter_by(user_id=current_user.id)

    # Apply date filters
    if start_date:
        query = query.filter(HealthMetric.recorded_date >= start_date)
    if end_date:
        query = query.filter(HealthMetric.recorded_date <= end_date)

    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(HealthMetric.recorded_date.asc())
    else:
        query = query.order_by(HealthMetric.recorded_date.desc())

    # Execute paginated query
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Serialize results
    metrics = [metric.to_dict() for metric in pagination.items]

    return paginated_response(
        items=metrics,
        page=page,
        per_page=per_page,
        total=pagination.total,
        message=f'Retrieved {len(metrics)} health metrics'
    )


@health_api_bp.route('/metrics', methods=['POST'])
@require_active_user
def create_metric():
    """
    Create a new health metric entry.

    Request Body (JSON):
        - recorded_date (str, required): Date of recording (ISO format)
        - weight_lbs (float, optional): Weight in pounds
        - body_fat_percentage (float, optional): Body fat percentage (0-100)
        - muscle_mass_lbs (float, optional): Muscle mass in pounds
        - bmi (float, optional): Body mass index
        - waist_inches (float, optional): Waist measurement
        - chest_inches (float, optional): Chest measurement
        - left_arm_inches (float, optional): Left arm measurement
        - right_arm_inches (float, optional): Right arm measurement
        - left_thigh_inches (float, optional): Left thigh measurement
        - right_thigh_inches (float, optional): Right thigh measurement
        - hips_inches (float, optional): Hips measurement
        - neck_inches (float, optional): Neck measurement
        - resting_heart_rate (int, optional): Resting heart rate (20-300)
        - blood_pressure_systolic (int, optional): Systolic BP (50-300)
        - blood_pressure_diastolic (int, optional): Diastolic BP (30-200)
        - energy_level (int, optional): Energy level (1-10)
        - mood (int, optional): Mood level (1-10)
        - sleep_quality (int, optional): Sleep quality (1-10)
        - stress_level (int, optional): Stress level (1-10)
        - notes (str, optional): Additional notes

    Returns:
        201: Created health metric
        400: Validation error
        409: Metric already exists for this date
    """
    # Define fields
    required_fields = ['recorded_date']
    optional_fields = [
        'weight_lbs', 'body_fat_percentage', 'muscle_mass_lbs', 'bmi',
        'waist_inches', 'chest_inches', 'left_arm_inches', 'right_arm_inches',
        'left_thigh_inches', 'right_thigh_inches', 'hips_inches', 'neck_inches',
        'resting_heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic',
        'energy_level', 'mood', 'sleep_quality', 'stress_level', 'notes'
    ]

    # Validate request data
    is_valid, result = validate_request_data(required_fields, optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate date format
    is_valid, date_obj = validate_date_format(data['recorded_date'])
    if not is_valid:
        return error_response(date_obj, status_code=400)

    # Check for duplicate entry
    existing = HealthMetric.query.filter_by(
        user_id=current_user.id,
        recorded_date=date_obj
    ).first()

    if existing:
        return error_response(
            f'Health metric already exists for {date_obj}',
            errors=['Use PUT to update existing metric'],
            status_code=409
        )

    # Create new metric
    try:
        metric = HealthMetric(
            user_id=current_user.id,
            recorded_date=date_obj,
            **{k: v for k, v in data.items() if k != 'recorded_date'}
        )

        db.session.add(metric)
        db.session.commit()

        logger.info(f'User {current_user.id} created health metric for {date_obj}')

        return success_response(
            data=metric.to_dict(),
            message='Health metric created successfully',
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating health metric: {e}', exc_info=True)
        return error_response('Failed to create health metric', errors=[str(e)], status_code=500)


@health_api_bp.route('/metrics/<int:metric_id>', methods=['GET'])
@require_active_user
def get_metric(metric_id):
    """
    Get a specific health metric by ID.

    Args:
        metric_id (int): Health metric ID

    Returns:
        200: Health metric data
        404: Metric not found
    """
    metric = HealthMetric.query.filter_by(
        id=metric_id,
        user_id=current_user.id
    ).first()

    if not metric:
        return error_response('Health metric not found', status_code=404)

    return success_response(
        data=metric.to_dict(),
        message='Health metric retrieved successfully'
    )


@health_api_bp.route('/metrics/<int:metric_id>', methods=['PUT'])
@require_active_user
def update_metric(metric_id):
    """
    Update an existing health metric.

    Args:
        metric_id (int): Health metric ID

    Request Body (JSON):
        Same fields as create_metric, all optional

    Returns:
        200: Updated health metric
        404: Metric not found
        400: Validation error
    """
    metric = HealthMetric.query.filter_by(
        id=metric_id,
        user_id=current_user.id
    ).first()

    if not metric:
        return error_response('Health metric not found', status_code=404)

    # Define optional fields
    optional_fields = [
        'recorded_date', 'weight_lbs', 'body_fat_percentage', 'muscle_mass_lbs', 'bmi',
        'waist_inches', 'chest_inches', 'left_arm_inches', 'right_arm_inches',
        'left_thigh_inches', 'right_thigh_inches', 'hips_inches', 'neck_inches',
        'resting_heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic',
        'energy_level', 'mood', 'sleep_quality', 'stress_level', 'notes'
    ]

    # Validate request data
    is_valid, result = validate_request_data(required_fields=None, optional_fields=optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate date if provided
    if 'recorded_date' in data:
        is_valid, date_obj = validate_date_format(data['recorded_date'])
        if not is_valid:
            return error_response(date_obj, status_code=400)

        # Check for duplicate (if date is changing)
        if date_obj != metric.recorded_date:
            existing = HealthMetric.query.filter_by(
                user_id=current_user.id,
                recorded_date=date_obj
            ).first()

            if existing:
                return error_response(
                    f'Health metric already exists for {date_obj}',
                    status_code=409
                )

        data['recorded_date'] = date_obj

    # Update metric
    try:
        for key, value in data.items():
            setattr(metric, key, value)

        db.session.commit()

        logger.info(f'User {current_user.id} updated health metric {metric_id}')

        return success_response(
            data=metric.to_dict(),
            message='Health metric updated successfully'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating health metric: {e}', exc_info=True)
        return error_response('Failed to update health metric', errors=[str(e)], status_code=500)


@health_api_bp.route('/metrics/<int:metric_id>', methods=['DELETE'])
@require_active_user
def delete_metric(metric_id):
    """
    Delete a health metric.

    Args:
        metric_id (int): Health metric ID

    Returns:
        200: Metric deleted successfully
        404: Metric not found
    """
    metric = HealthMetric.query.filter_by(
        id=metric_id,
        user_id=current_user.id
    ).first()

    if not metric:
        return error_response('Health metric not found', status_code=404)

    try:
        db.session.delete(metric)
        db.session.commit()

        logger.info(f'User {current_user.id} deleted health metric {metric_id}')

        return success_response(
            message='Health metric deleted successfully'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting health metric: {e}', exc_info=True)
        return error_response('Failed to delete health metric', errors=[str(e)], status_code=500)


@health_api_bp.route('/metrics/latest', methods=['GET'])
@require_active_user
def get_latest_metric():
    """
    Get the most recent health metric for the authenticated user.

    Returns:
        200: Latest health metric
        404: No metrics found
    """
    metric = HealthMetric.query.filter_by(
        user_id=current_user.id
    ).order_by(HealthMetric.recorded_date.desc()).first()

    if not metric:
        return error_response('No health metrics found', status_code=404)

    return success_response(
        data=metric.to_dict(),
        message='Latest health metric retrieved successfully'
    )


@health_api_bp.route('/metrics/summary', methods=['GET'])
@require_active_user
def get_metrics_summary():
    """
    Get summary statistics for health metrics.

    Query Parameters:
        - days (int): Number of days to include (default: 30)

    Returns:
        200: Summary statistics including averages, trends, and latest values
    """
    try:
        days = int(request.args.get('days', 30))
        days = max(1, min(365, days))  # Limit to 1-365 days
    except (ValueError, TypeError):
        days = 30

    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Get metrics in date range
    metrics = HealthMetric.query.filter(
        and_(
            HealthMetric.user_id == current_user.id,
            HealthMetric.recorded_date >= start_date,
            HealthMetric.recorded_date <= end_date
        )
    ).order_by(HealthMetric.recorded_date.asc()).all()

    if not metrics:
        return success_response(
            data={
                'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
                'total_entries': 0,
                'message': 'No metrics found for this period'
            }
        )

    # Calculate summary statistics
    latest = metrics[-1]
    first = metrics[0]

    # Weight statistics
    weight_values = [m.weight_lbs for m in metrics if m.weight_lbs is not None]
    avg_weight = sum(weight_values) / len(weight_values) if weight_values else None
    weight_change = (latest.weight_lbs - first.weight_lbs) if (latest.weight_lbs and first.weight_lbs) else None

    # Body fat statistics
    bf_values = [m.body_fat_percentage for m in metrics if m.body_fat_percentage is not None]
    avg_bf = sum(bf_values) / len(bf_values) if bf_values else None
    bf_change = (latest.body_fat_percentage - first.body_fat_percentage) if (latest.body_fat_percentage and first.body_fat_percentage) else None

    # Wellness averages
    energy_values = [m.energy_level for m in metrics if m.energy_level is not None]
    avg_energy = sum(energy_values) / len(energy_values) if energy_values else None

    mood_values = [m.mood for m in metrics if m.mood is not None]
    avg_mood = sum(mood_values) / len(mood_values) if mood_values else None

    sleep_values = [m.sleep_quality for m in metrics if m.sleep_quality is not None]
    avg_sleep = sum(sleep_values) / len(sleep_values) if sleep_values else None

    stress_values = [m.stress_level for m in metrics if m.stress_level is not None]
    avg_stress = sum(stress_values) / len(stress_values) if stress_values else None

    summary = {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days
        },
        'total_entries': len(metrics),
        'latest': latest.to_dict(include_calculated=True),
        'averages': {
            'weight_lbs': round(avg_weight, 2) if avg_weight else None,
            'body_fat_percentage': round(avg_bf, 2) if avg_bf else None,
            'energy_level': round(avg_energy, 2) if avg_energy else None,
            'mood': round(avg_mood, 2) if avg_mood else None,
            'sleep_quality': round(avg_sleep, 2) if avg_sleep else None,
            'stress_level': round(avg_stress, 2) if avg_stress else None,
        },
        'changes': {
            'weight_lbs': round(weight_change, 2) if weight_change else None,
            'body_fat_percentage': round(bf_change, 2) if bf_change else None,
        }
    }

    return success_response(
        data=summary,
        message=f'Summary statistics for {days} days'
    )


@health_api_bp.route('/metrics/trend', methods=['GET'])
@require_active_user
def get_metrics_trend():
    """
    Get health metrics trend data for charting.

    Query Parameters:
        - days (int): Number of days to include (default: 7)

    Returns:
        200: Arrays of dates and weights for charting
    """
    try:
        days = int(request.args.get('days', 7))
        days = max(1, min(90, days))  # Limit to 1-90 days
    except (ValueError, TypeError):
        days = 7

    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Get metrics in date range
    metrics = HealthMetric.query.filter(
        and_(
            HealthMetric.user_id == current_user.id,
            HealthMetric.recorded_date >= start_date,
            HealthMetric.recorded_date <= end_date
        )
    ).order_by(HealthMetric.recorded_date.asc()).all()

    # Prepare data for charting
    dates = []
    weights = []

    for metric in metrics:
        if metric.weight_lbs is not None:
            dates.append(metric.recorded_date.isoformat())
            weights.append(metric.weight_lbs)

    return success_response(
        data={
            'dates': dates,
            'weights': weights
        },
        message=f'Weight trend data for {days} days'
    )
