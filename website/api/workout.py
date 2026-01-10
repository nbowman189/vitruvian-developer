"""
Workout API
===========

RESTful API endpoints for workout and exercise tracking.

Endpoints:
- GET    /api/workouts                      - List workout sessions
- POST   /api/workouts                      - Create workout session
- GET    /api/workouts/<id>                 - Get specific workout
- PUT    /api/workouts/<id>                 - Update workout
- DELETE /api/workouts/<id>                 - Delete workout
- POST   /api/workouts/<id>/exercises       - Add exercise to workout
- GET    /api/workouts/stats                - Get workout statistics
- GET    /api/exercises/definitions         - List exercise definitions
- POST   /api/exercises/definitions         - Create exercise definition
"""

from flask import Blueprint, request
from flask_login import current_user
from sqlalchemy import func, and_, desc

from ..models import db
from ..models.workout import WorkoutSession, ExerciseLog, ExerciseDefinition, SessionType
from .. import csrf
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

# Create workout API sub-blueprint
workout_api_bp = Blueprint('workout_api', __name__, url_prefix='/workouts')


@workout_api_bp.route('', methods=['GET'])
@require_active_user
def get_workouts():
    """
    Get workout sessions for authenticated user.

    Query Parameters:
        - page (int): Page number (default: 1)
        - per_page (int): Items per page (default: 20, max: 100)
        - start_date (str): Filter by start date (YYYY-MM-DD)
        - end_date (str): Filter by end date (YYYY-MM-DD)
        - session_type (str): Filter by session type
        - sort (str): Sort order ('asc' or 'desc', default: 'desc')

    Returns:
        200: Paginated list of workout sessions
    """
    page, per_page = validate_pagination_params()

    # Validate date range
    is_valid, start_date, end_date, error_msg = validate_date_range_params()
    if not is_valid:
        return error_response(error_msg, status_code=400)

    # Get sort order
    sort_order = request.args.get('sort', 'desc').lower()
    if sort_order not in ['asc', 'desc']:
        return error_response("Invalid sort order", status_code=400)

    # Build query
    query = WorkoutSession.query.filter_by(user_id=current_user.id)

    # Apply filters
    if start_date:
        query = query.filter(WorkoutSession.session_date >= start_date)
    if end_date:
        query = query.filter(WorkoutSession.session_date <= end_date)

    session_type = request.args.get('session_type')
    if session_type:
        try:
            session_type_enum = SessionType(session_type)
            query = query.filter(WorkoutSession.session_type == session_type_enum)
        except ValueError:
            return error_response(f"Invalid session_type: {session_type}", status_code=400)

    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(WorkoutSession.session_date.asc())
    else:
        query = query.order_by(WorkoutSession.session_date.desc())

    # Execute paginated query
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Serialize results
    workouts = [workout.to_dict() for workout in pagination.items]

    return paginated_response(
        items=workouts,
        page=page,
        per_page=per_page,
        total=pagination.total
    )


@workout_api_bp.route('', methods=['POST'])
@csrf.exempt
@require_active_user
def create_workout():
    """
    Create a new workout session.

    Request Body:
        - session_date (str, required): Session date (YYYY-MM-DD)
        - session_type (str, required): Session type (strength, cardio, etc.)
        - duration_minutes (int, optional): Duration in minutes
        - program_phase (str, optional): Program phase name
        - week_number (int, optional): Week number
        - day_number (int, optional): Day number
        - intensity (int, optional): Intensity level (1-10)
        - fatigue (int, optional): Fatigue level (1-10)
        - soreness (int, optional): Soreness level (1-10)
        - notes (str, optional): Session notes

    Returns:
        201: Created workout session
        400: Validation error
    """
    required_fields = ['session_date', 'session_type']
    optional_fields = ['duration_minutes', 'program_phase', 'week_number', 'day_number',
                       'intensity', 'fatigue', 'soreness', 'notes', 'coach_notes']

    is_valid, result = validate_request_data(required_fields, optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate date
    is_valid, date_obj = validate_date_format(data['session_date'])
    if not is_valid:
        return error_response(date_obj, status_code=400)

    # Validate session type
    try:
        session_type_enum = SessionType(data['session_type'])
    except ValueError:
        valid_types = [t.value for t in SessionType]
        return error_response(
            f"Invalid session_type. Must be one of: {', '.join(valid_types)}",
            status_code=400
        )

    try:
        workout = WorkoutSession(
            user_id=current_user.id,
            session_date=date_obj,
            session_type=session_type_enum,
            **{k: v for k, v in data.items() if k not in ['session_date', 'session_type']}
        )

        db.session.add(workout)
        db.session.commit()

        logger.info(f'User {current_user.id} created workout session {workout.id}')

        return success_response(
            data=workout.to_dict(),
            message='Workout session created successfully',
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating workout: {e}', exc_info=True)
        return error_response('Failed to create workout', errors=[str(e)], status_code=500)


@workout_api_bp.route('/<int:workout_id>', methods=['GET'])
@require_active_user
def get_workout(workout_id):
    """
    Get a specific workout session with exercises.

    Returns:
        200: Workout session with exercises
        404: Workout not found
    """
    workout = WorkoutSession.query.filter_by(
        id=workout_id,
        user_id=current_user.id
    ).first()

    if not workout:
        return error_response('Workout session not found', status_code=404)

    return success_response(
        data=workout.to_dict(include_exercises=True),
        message='Workout session retrieved successfully'
    )


@workout_api_bp.route('/<int:workout_id>', methods=['PUT'])
@csrf.exempt
@require_active_user
def update_workout(workout_id):
    """
    Update a workout session.

    Returns:
        200: Updated workout session
        404: Workout not found
    """
    workout = WorkoutSession.query.filter_by(
        id=workout_id,
        user_id=current_user.id
    ).first()

    if not workout:
        return error_response('Workout session not found', status_code=404)

    optional_fields = ['session_date', 'session_type', 'duration_minutes', 'program_phase',
                       'week_number', 'day_number', 'intensity', 'fatigue', 'soreness',
                       'notes', 'coach_notes']

    is_valid, result = validate_request_data(required_fields=None, optional_fields=optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate date if provided
    if 'session_date' in data:
        is_valid, date_obj = validate_date_format(data['session_date'])
        if not is_valid:
            return error_response(date_obj, status_code=400)
        data['session_date'] = date_obj

    # Validate session type if provided
    if 'session_type' in data:
        try:
            data['session_type'] = SessionType(data['session_type'])
        except ValueError:
            valid_types = [t.value for t in SessionType]
            return error_response(
                f"Invalid session_type. Must be one of: {', '.join(valid_types)}",
                status_code=400
            )

    try:
        for key, value in data.items():
            setattr(workout, key, value)

        db.session.commit()

        logger.info(f'User {current_user.id} updated workout {workout_id}')

        return success_response(
            data=workout.to_dict(include_exercises=True),
            message='Workout session updated successfully'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating workout: {e}', exc_info=True)
        return error_response('Failed to update workout', errors=[str(e)], status_code=500)


@workout_api_bp.route('/<int:workout_id>', methods=['DELETE'])
@csrf.exempt
@require_active_user
def delete_workout(workout_id):
    """
    Delete a workout session and all associated exercises.

    Returns:
        200: Workout deleted successfully
        404: Workout not found
    """
    workout = WorkoutSession.query.filter_by(
        id=workout_id,
        user_id=current_user.id
    ).first()

    if not workout:
        return error_response('Workout session not found', status_code=404)

    try:
        db.session.delete(workout)
        db.session.commit()

        logger.info(f'User {current_user.id} deleted workout {workout_id}')

        return success_response(message='Workout session deleted successfully')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting workout: {e}', exc_info=True)
        return error_response('Failed to delete workout', errors=[str(e)], status_code=500)


@workout_api_bp.route('/<int:workout_id>/exercises', methods=['POST'])
@csrf.exempt
@require_active_user
def add_exercise_to_workout(workout_id):
    """
    Add an exercise log to a workout session.

    Request Body:
        - exercise_name (str, required): Exercise name
        - exercise_definition_id (int, optional): Link to exercise definition
        - sets (int, optional): Number of sets
        - reps (int, optional): Number of reps
        - weight_lbs (float, optional): Weight in pounds
        - rest_seconds (int, optional): Rest period
        - duration_seconds (int, optional): Duration for time-based exercises
        - distance_miles (float, optional): Distance for cardio
        - form_quality (int, optional): Form quality (1-10)
        - rpe (int, optional): RPE (1-10)
        - notes (str, optional): Exercise notes

    Returns:
        201: Exercise added successfully
        404: Workout not found
    """
    workout = WorkoutSession.query.filter_by(
        id=workout_id,
        user_id=current_user.id
    ).first()

    if not workout:
        return error_response('Workout session not found', status_code=404)

    required_fields = ['exercise_name']
    optional_fields = ['exercise_definition_id', 'sets', 'reps', 'weight_lbs', 'rest_seconds',
                       'duration_seconds', 'distance_miles', 'form_quality', 'rpe', 'notes']

    is_valid, result = validate_request_data(required_fields, optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Calculate order_index (append to end)
    max_order = db.session.query(func.max(ExerciseLog.order_index)).filter_by(
        workout_session_id=workout_id
    ).scalar()
    order_index = (max_order or -1) + 1

    try:
        exercise = ExerciseLog(
            workout_session_id=workout_id,
            order_index=order_index,
            **data
        )

        db.session.add(exercise)
        db.session.commit()

        logger.info(f'User {current_user.id} added exercise to workout {workout_id}')

        return success_response(
            data=exercise.to_dict(),
            message='Exercise added successfully',
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error adding exercise: {e}', exc_info=True)
        return error_response('Failed to add exercise', errors=[str(e)], status_code=500)


@workout_api_bp.route('/stats', methods=['GET'])
@require_active_user
def get_workout_stats():
    """
    Get workout statistics and progress.

    Query Parameters:
        - days (int): Number of days to include (default: 30)

    Returns:
        200: Workout statistics
    """
    from datetime import datetime, timedelta

    try:
        days = int(request.args.get('days', 30))
        days = max(1, min(365, days))
    except (ValueError, TypeError):
        days = 30

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Get workouts in date range
    workouts = WorkoutSession.query.filter(
        and_(
            WorkoutSession.user_id == current_user.id,
            WorkoutSession.session_date >= start_date,
            WorkoutSession.session_date <= end_date
        )
    ).all()

    if not workouts:
        return success_response(data={
            'total_workouts': 0,
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
        })

    # Calculate statistics
    total_workouts = len(workouts)
    total_duration = sum(w.duration_minutes for w in workouts if w.duration_minutes)
    avg_duration = total_duration / total_workouts if total_workouts > 0 else 0

    # Workout type distribution
    type_counts = {}
    for workout in workouts:
        type_name = workout.session_type.value
        type_counts[type_name] = type_counts.get(type_name, 0) + 1

    # Average metrics
    intensity_values = [w.intensity for w in workouts if w.intensity]
    avg_intensity = sum(intensity_values) / len(intensity_values) if intensity_values else None

    # Total exercises and sets
    total_exercises = sum(w.total_exercises for w in workouts)
    total_sets = sum(w.total_sets for w in workouts)

    stats = {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days
        },
        'totals': {
            'workouts': total_workouts,
            'duration_minutes': total_duration,
            'exercises': total_exercises,
            'sets': total_sets,
        },
        'averages': {
            'duration_minutes': round(avg_duration, 1),
            'intensity': round(avg_intensity, 2) if avg_intensity else None,
            'workouts_per_week': round((total_workouts / days) * 7, 1),
        },
        'by_type': type_counts
    }

    return success_response(data=stats, message=f'Statistics for {days} days')


# ====================
# Exercise Definitions
# ====================

@workout_api_bp.route('/exercises/definitions', methods=['GET'])
@require_active_user
def get_exercise_definitions():
    """
    Get all exercise definitions.

    Query Parameters:
        - category (str): Filter by category
        - search (str): Search by name

    Returns:
        200: List of exercise definitions
    """
    query = ExerciseDefinition.query.filter_by(is_active=True)

    # Filter by category
    category = request.args.get('category')
    if category:
        from ..models.workout import ExerciseCategory
        try:
            category_enum = ExerciseCategory(category)
            query = query.filter(ExerciseDefinition.category == category_enum)
        except ValueError:
            pass

    # Search by name
    search = request.args.get('search')
    if search:
        query = query.filter(ExerciseDefinition.name.ilike(f'%{search}%'))

    # Order by name
    query = query.order_by(ExerciseDefinition.name.asc())

    definitions = [d.to_dict() for d in query.all()]

    return success_response(
        data=definitions,
        message=f'Retrieved {len(definitions)} exercise definitions'
    )


@workout_api_bp.route('/exercises/definitions', methods=['POST'])
@csrf.exempt
@require_active_user
def create_exercise_definition():
    """
    Create a new exercise definition.

    Request Body:
        - name (str, required): Exercise name
        - category (str, required): Exercise category
        - muscle_groups (list, required): Target muscle groups
        - difficulty_level (str, required): Difficulty level
        - equipment_needed (list, optional): Required equipment
        - description (str, optional): Exercise description
        - instructions (str, optional): How to perform
        - tips (str, optional): Form tips
        - video_url (str, optional): Video URL
        - image_url (str, optional): Image URL

    Returns:
        201: Created exercise definition
        409: Exercise already exists
    """
    from ..models.workout import ExerciseCategory, DifficultyLevel

    required_fields = ['name', 'category', 'muscle_groups', 'difficulty_level']
    optional_fields = ['equipment_needed', 'description', 'instructions', 'tips',
                       'video_url', 'image_url']

    is_valid, result = validate_request_data(required_fields, optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Check if exercise already exists
    existing = ExerciseDefinition.query.filter_by(name=data['name']).first()
    if existing:
        return error_response('Exercise definition already exists', status_code=409)

    # Validate category
    try:
        category_enum = ExerciseCategory(data['category'])
    except ValueError:
        valid_categories = [c.value for c in ExerciseCategory]
        return error_response(
            f"Invalid category. Must be one of: {', '.join(valid_categories)}",
            status_code=400
        )

    # Validate difficulty
    try:
        difficulty_enum = DifficultyLevel(data['difficulty_level'])
    except ValueError:
        valid_levels = [d.value for d in DifficultyLevel]
        return error_response(
            f"Invalid difficulty_level. Must be one of: {', '.join(valid_levels)}",
            status_code=400
        )

    try:
        definition = ExerciseDefinition(
            name=data['name'],
            category=category_enum,
            difficulty_level=difficulty_enum,
            created_by=current_user.username,
            **{k: v for k, v in data.items() if k not in ['name', 'category', 'difficulty_level']}
        )

        db.session.add(definition)
        db.session.commit()

        logger.info(f'User {current_user.id} created exercise definition: {definition.name}')

        return success_response(
            data=definition.to_dict(),
            message='Exercise definition created successfully',
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating exercise definition: {e}', exc_info=True)
        return error_response('Failed to create exercise definition', errors=[str(e)], status_code=500)


# ====================
# Dashboard Endpoints
# ====================

@workout_api_bp.route('/recent', methods=['GET'])
@require_active_user
def get_recent_workout():
    """
    Get the most recent workout session for the authenticated user.

    Returns:
        200: Most recent workout data
        404: No workouts found
    """
    workout = WorkoutSession.query.filter_by(
        user_id=current_user.id
    ).order_by(WorkoutSession.session_date.desc()).first()

    if not workout:
        return success_response(
            data={
                'name': 'No recent workout',
                'duration': None,
                'date': None
            },
            message='No workouts found'
        )

    return success_response(
        data={
            'name': workout.notes or workout.session_type.value.replace('_', ' ').title(),
            'duration': workout.duration_minutes,
            'date': workout.session_date.isoformat() if workout.session_date else None
        },
        message='Recent workout retrieved successfully'
    )


@workout_api_bp.route('/volume-trend', methods=['GET'])
@require_active_user
def get_volume_trend():
    """
    Get workout volume trend data for charting.

    Query Parameters:
        - days (int): Number of days to include (default: 7)

    Returns:
        200: Arrays of dates and volumes for charting
    """
    from datetime import datetime, timedelta

    try:
        days = int(request.args.get('days', 7))
        days = max(1, min(90, days))  # Limit to 1-90 days
    except (ValueError, TypeError):
        days = 7

    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # Get all dates in range
    dates_list = []
    current_date = start_date
    while current_date <= end_date:
        dates_list.append(current_date)
        current_date += timedelta(days=1)

    # Get workouts in date range
    workouts = WorkoutSession.query.filter(
        and_(
            WorkoutSession.user_id == current_user.id,
            WorkoutSession.session_date >= start_date,
            WorkoutSession.session_date <= end_date
        )
    ).all()

    # Create a dictionary of date -> total volume
    volume_by_date = {}
    for workout in workouts:
        date_key = workout.session_date

        # Calculate total volume for this workout
        total_volume = 0
        for exercise in workout.exercise_logs:
            if exercise.weight_lbs and exercise.reps and exercise.sets:
                total_volume += exercise.weight_lbs * exercise.reps * exercise.sets

        if date_key in volume_by_date:
            volume_by_date[date_key] += total_volume
        else:
            volume_by_date[date_key] = total_volume

    # Prepare data for charting (include all dates, 0 for days without workouts)
    dates = []
    volumes = []

    for date in dates_list:
        dates.append(date.isoformat())
        volumes.append(volume_by_date.get(date, 0))

    return success_response(
        data={
            'dates': dates,
            'volumes': volumes
        },
        message=f'Workout volume trend data for {days} days'
    )
