"""
Coaching API
============

RESTful API endpoints for coaching sessions, goals, and progress photos.

Endpoints:
- GET    /api/coaching/sessions          - List coaching sessions
- POST   /api/coaching/sessions          - Create coaching session
- GET    /api/coaching/sessions/<id>     - Get specific session
- PUT    /api/coaching/sessions/<id>     - Update session
- DELETE /api/coaching/sessions/<id>     - Delete session
- GET    /api/goals                      - List user goals
- POST   /api/goals                      - Create new goal
- PUT    /api/goals/<id>                 - Update goal
- PUT    /api/goals/<id>/complete        - Mark goal as completed
- GET    /api/progress/photos            - List progress photos
- POST   /api/progress/photos            - Upload progress photo
"""

from flask import Blueprint, request
from flask_login import current_user
from sqlalchemy import and_

from ..models import db
from ..models.coaching import CoachingSession, UserGoal, ProgressPhoto, GoalType, GoalStatus, PhotoType
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

# Create coaching API sub-blueprint
coaching_api_bp = Blueprint('coaching_api', __name__, url_prefix='/coaching')


# ====================
# Coaching Sessions
# ====================

@coaching_api_bp.route('/sessions', methods=['GET'])
@require_active_user
def get_coaching_sessions():
    """
    Get coaching sessions for authenticated user.

    Query Parameters:
        - page, per_page, start_date, end_date, sort

    Returns:
        200: Paginated list of coaching sessions
    """
    page, per_page = validate_pagination_params()

    is_valid, start_date, end_date, error_msg = validate_date_range_params()
    if not is_valid:
        return error_response(error_msg, status_code=400)

    sort_order = request.args.get('sort', 'desc').lower()

    # Build query
    query = CoachingSession.query.filter_by(user_id=current_user.id)

    if start_date:
        query = query.filter(CoachingSession.session_date >= start_date)
    if end_date:
        query = query.filter(CoachingSession.session_date <= end_date)

    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(CoachingSession.session_date.asc())
    else:
        query = query.order_by(CoachingSession.session_date.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    sessions = [session.to_dict() for session in pagination.items]

    return paginated_response(
        items=sessions,
        page=page,
        per_page=per_page,
        total=pagination.total
    )


@coaching_api_bp.route('/sessions', methods=['POST'])
@require_active_user
def create_coaching_session():
    """
    Create a new coaching session.

    Request Body:
        - session_date (str, required): Session date
        - coach_id (int, required): Coach user ID
        - duration_minutes (int, optional): Duration
        - topics (list, optional): Discussion topics
        - discussion_notes (str, optional): Notes
        - coach_feedback (str, optional): Coach feedback
        - action_items (list, optional): Action items
        - next_session_date (str, optional): Next session date

    Returns:
        201: Created coaching session
    """
    required_fields = ['session_date', 'coach_id']
    optional_fields = ['duration_minutes', 'topics', 'discussion_notes', 'coach_feedback',
                       'action_items', 'next_session_date']

    is_valid, result = validate_request_data(required_fields, optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate dates
    is_valid, date_obj = validate_date_format(data['session_date'])
    if not is_valid:
        return error_response(date_obj, status_code=400)
    data['session_date'] = date_obj

    if 'next_session_date' in data and data['next_session_date']:
        is_valid, next_date_obj = validate_date_format(data['next_session_date'])
        if not is_valid:
            return error_response(next_date_obj, status_code=400)
        data['next_session_date'] = next_date_obj

    # Verify coach exists
    from ..models.user import User
    coach = User.query.get(data['coach_id'])
    if not coach:
        return error_response('Coach not found', status_code=404)

    try:
        session = CoachingSession(
            user_id=current_user.id,
            **data
        )

        db.session.add(session)
        db.session.commit()

        logger.info(f'User {current_user.id} created coaching session {session.id}')

        return success_response(
            data=session.to_dict(),
            message='Coaching session created successfully',
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating coaching session: {e}', exc_info=True)
        return error_response('Failed to create coaching session', errors=[str(e)], status_code=500)


@coaching_api_bp.route('/sessions/<int:session_id>', methods=['GET'])
@require_active_user
def get_coaching_session(session_id):
    """Get a specific coaching session."""
    session = CoachingSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()

    if not session:
        return error_response('Coaching session not found', status_code=404)

    return success_response(
        data=session.to_dict(include_coach_info=True),
        message='Coaching session retrieved successfully'
    )


@coaching_api_bp.route('/sessions/<int:session_id>', methods=['PUT'])
@require_active_user
def update_coaching_session(session_id):
    """Update a coaching session."""
    session = CoachingSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()

    if not session:
        return error_response('Coaching session not found', status_code=404)

    optional_fields = ['session_date', 'duration_minutes', 'topics', 'discussion_notes',
                       'coach_feedback', 'action_items', 'next_session_date', 'completed',
                       'completion_notes', 'user_rating']

    is_valid, result = validate_request_data(required_fields=None, optional_fields=optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate dates if provided
    if 'session_date' in data:
        is_valid, date_obj = validate_date_format(data['session_date'])
        if not is_valid:
            return error_response(date_obj, status_code=400)
        data['session_date'] = date_obj

    if 'next_session_date' in data and data['next_session_date']:
        is_valid, next_date_obj = validate_date_format(data['next_session_date'])
        if not is_valid:
            return error_response(next_date_obj, status_code=400)
        data['next_session_date'] = next_date_obj

    try:
        for key, value in data.items():
            setattr(session, key, value)

        db.session.commit()

        logger.info(f'User {current_user.id} updated coaching session {session_id}')

        return success_response(
            data=session.to_dict(),
            message='Coaching session updated successfully'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating coaching session: {e}', exc_info=True)
        return error_response('Failed to update coaching session', errors=[str(e)], status_code=500)


@coaching_api_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@require_active_user
def delete_coaching_session(session_id):
    """Delete a coaching session."""
    session = CoachingSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()

    if not session:
        return error_response('Coaching session not found', status_code=404)

    try:
        db.session.delete(session)
        db.session.commit()

        logger.info(f'User {current_user.id} deleted coaching session {session_id}')

        return success_response(message='Coaching session deleted successfully')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting coaching session: {e}', exc_info=True)
        return error_response('Failed to delete coaching session', errors=[str(e)], status_code=500)


# ====================
# Goals
# ====================

@coaching_api_bp.route('/goals', methods=['GET'])
@require_active_user
def get_goals():
    """
    Get user goals.

    Query Parameters:
        - status (str): Filter by status (active, completed, paused, abandoned)
        - goal_type (str): Filter by type

    Returns:
        200: List of user goals
    """
    query = UserGoal.query.filter_by(user_id=current_user.id)

    # Filter by status
    status = request.args.get('status')
    if status:
        try:
            status_enum = GoalStatus(status)
            query = query.filter(UserGoal.status == status_enum)
        except ValueError:
            return error_response(f"Invalid status: {status}", status_code=400)

    # Filter by type
    goal_type = request.args.get('goal_type')
    if goal_type:
        try:
            type_enum = GoalType(goal_type)
            query = query.filter(UserGoal.goal_type == type_enum)
        except ValueError:
            return error_response(f"Invalid goal_type: {goal_type}", status_code=400)

    # Order by status (active first), then by target date
    query = query.order_by(
        UserGoal.status.asc(),
        UserGoal.target_date.asc()
    )

    goals = [goal.to_dict() for goal in query.all()]

    return success_response(
        data=goals,
        message=f'Retrieved {len(goals)} goals'
    )


@coaching_api_bp.route('/goals', methods=['POST'])
@require_active_user
def create_goal():
    """
    Create a new goal.

    Request Body:
        - goal_type (str, required): Goal type
        - title (str, required): Goal title
        - description (str, optional): Description
        - target_value (float, optional): Target value
        - target_unit (str, optional): Target unit
        - target_date (str, optional): Target date
        - notes (str, optional): Notes

    Returns:
        201: Created goal
    """
    required_fields = ['goal_type', 'title']
    optional_fields = ['description', 'target_value', 'target_unit', 'current_value',
                       'target_date', 'notes', 'milestones']

    is_valid, result = validate_request_data(required_fields, optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate goal type
    try:
        type_enum = GoalType(data['goal_type'])
    except ValueError:
        valid_types = [t.value for t in GoalType]
        return error_response(
            f"Invalid goal_type. Must be one of: {', '.join(valid_types)}",
            status_code=400
        )

    # Validate target date if provided
    if 'target_date' in data and data['target_date']:
        is_valid, date_obj = validate_date_format(data['target_date'])
        if not is_valid:
            return error_response(date_obj, status_code=400)
        data['target_date'] = date_obj

    try:
        goal = UserGoal(
            user_id=current_user.id,
            goal_type=type_enum,
            **{k: v for k, v in data.items() if k != 'goal_type'}
        )

        # Calculate initial progress if values provided
        if goal.current_value is not None and goal.target_value is not None:
            goal.progress_percentage = goal.calculate_progress()

        db.session.add(goal)
        db.session.commit()

        logger.info(f'User {current_user.id} created goal {goal.id}')

        return success_response(
            data=goal.to_dict(),
            message='Goal created successfully',
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating goal: {e}', exc_info=True)
        return error_response('Failed to create goal', errors=[str(e)], status_code=500)


@coaching_api_bp.route('/goals/<int:goal_id>', methods=['PUT'])
@require_active_user
def update_goal(goal_id):
    """Update a goal."""
    goal = UserGoal.query.filter_by(
        id=goal_id,
        user_id=current_user.id
    ).first()

    if not goal:
        return error_response('Goal not found', status_code=404)

    optional_fields = ['title', 'description', 'goal_type', 'target_value', 'target_unit',
                       'current_value', 'target_date', 'status', 'notes', 'milestones']

    is_valid, result = validate_request_data(required_fields=None, optional_fields=optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate enums if provided
    if 'goal_type' in data:
        try:
            data['goal_type'] = GoalType(data['goal_type'])
        except ValueError:
            return error_response("Invalid goal_type", status_code=400)

    if 'status' in data:
        try:
            data['status'] = GoalStatus(data['status'])
        except ValueError:
            return error_response("Invalid status", status_code=400)

    # Validate date if provided
    if 'target_date' in data and data['target_date']:
        is_valid, date_obj = validate_date_format(data['target_date'])
        if not is_valid:
            return error_response(date_obj, status_code=400)
        data['target_date'] = date_obj

    try:
        for key, value in data.items():
            setattr(goal, key, value)

        # Recalculate progress if current_value or target_value changed
        if 'current_value' in data or 'target_value' in data:
            goal.progress_percentage = goal.calculate_progress()

        db.session.commit()

        logger.info(f'User {current_user.id} updated goal {goal_id}')

        return success_response(
            data=goal.to_dict(),
            message='Goal updated successfully'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating goal: {e}', exc_info=True)
        return error_response('Failed to update goal', errors=[str(e)], status_code=500)


@coaching_api_bp.route('/goals/<int:goal_id>/complete', methods=['PUT'])
@require_active_user
def complete_goal(goal_id):
    """
    Mark a goal as completed.

    Returns:
        200: Goal marked as completed
        404: Goal not found
    """
    from datetime import date

    goal = UserGoal.query.filter_by(
        id=goal_id,
        user_id=current_user.id
    ).first()

    if not goal:
        return error_response('Goal not found', status_code=404)

    try:
        goal.status = GoalStatus.COMPLETED
        goal.completed_date = date.today()
        goal.progress_percentage = 100.0

        db.session.commit()

        logger.info(f'User {current_user.id} completed goal {goal_id}')

        return success_response(
            data=goal.to_dict(),
            message='Goal marked as completed'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error completing goal: {e}', exc_info=True)
        return error_response('Failed to complete goal', errors=[str(e)], status_code=500)


# ====================
# Progress Photos
# ====================

@coaching_api_bp.route('/progress/photos', methods=['GET'])
@require_active_user
def get_progress_photos():
    """
    Get progress photos.

    Query Parameters:
        - page, per_page, start_date, end_date, photo_type

    Returns:
        200: Paginated list of progress photos
    """
    page, per_page = validate_pagination_params()

    is_valid, start_date, end_date, error_msg = validate_date_range_params()
    if not is_valid:
        return error_response(error_msg, status_code=400)

    # Build query
    query = ProgressPhoto.query.filter_by(user_id=current_user.id)

    if start_date:
        query = query.filter(ProgressPhoto.photo_date >= start_date)
    if end_date:
        query = query.filter(ProgressPhoto.photo_date <= end_date)

    # Filter by photo type
    photo_type = request.args.get('photo_type')
    if photo_type:
        try:
            type_enum = PhotoType(photo_type)
            query = query.filter(ProgressPhoto.photo_type == type_enum)
        except ValueError:
            return error_response(f"Invalid photo_type: {photo_type}", status_code=400)

    # Order by date descending
    query = query.order_by(ProgressPhoto.photo_date.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    photos = [photo.to_dict() for photo in pagination.items]

    return paginated_response(
        items=photos,
        page=page,
        per_page=per_page,
        total=pagination.total
    )


@coaching_api_bp.route('/progress/photos', methods=['POST'])
@require_active_user
def upload_progress_photo():
    """
    Upload a progress photo.

    Request Body:
        - photo_date (str, required): Photo date
        - photo_url (str, required): Photo URL
        - photo_type (str, required): Photo type
        - weight_lbs (float, optional): Weight at time of photo
        - body_fat_percentage (float, optional): Body fat at time of photo
        - notes (str, optional): Notes
        - is_public (bool, optional): Make photo public

    Returns:
        201: Progress photo created
    """
    required_fields = ['photo_date', 'photo_url', 'photo_type']
    optional_fields = ['weight_lbs', 'body_fat_percentage', 'notes', 'is_public']

    is_valid, result = validate_request_data(required_fields, optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate date
    is_valid, date_obj = validate_date_format(data['photo_date'])
    if not is_valid:
        return error_response(date_obj, status_code=400)
    data['photo_date'] = date_obj

    # Validate photo type
    try:
        type_enum = PhotoType(data['photo_type'])
    except ValueError:
        valid_types = [t.value for t in PhotoType]
        return error_response(
            f"Invalid photo_type. Must be one of: {', '.join(valid_types)}",
            status_code=400
        )

    try:
        photo = ProgressPhoto(
            user_id=current_user.id,
            photo_type=type_enum,
            **{k: v for k, v in data.items() if k != 'photo_type'}
        )

        db.session.add(photo)
        db.session.commit()

        logger.info(f'User {current_user.id} uploaded progress photo {photo.id}')

        return success_response(
            data=photo.to_dict(),
            message='Progress photo uploaded successfully',
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error uploading progress photo: {e}', exc_info=True)
        return error_response('Failed to upload progress photo', errors=[str(e)], status_code=500)


# ====================
# Dashboard Endpoints
# ====================

@coaching_api_bp.route('/next-session', methods=['GET'])
@require_active_user
def get_next_session():
    """
    Get next scheduled coaching session and active goals count.

    Returns:
        200: Next session date and goals data
    """
    from datetime import datetime, timedelta

    today = datetime.now().date()

    # Get next scheduled session (future sessions only)
    next_session = CoachingSession.query.filter(
        and_(
            CoachingSession.user_id == current_user.id,
            CoachingSession.session_date >= today
        )
    ).order_by(CoachingSession.session_date.asc()).first()

    # Get active goals count
    active_goals = UserGoal.query.filter_by(
        user_id=current_user.id,
        status=GoalStatus.ACTIVE
    ).count()

    # Calculate countdown if there's a next session
    countdown = None
    session_date = None

    if next_session:
        session_date = next_session.session_date.isoformat()
        days_until = (next_session.session_date - today).days

        if days_until == 0:
            countdown = 'Today'
        elif days_until == 1:
            countdown = 'Tomorrow'
        elif days_until < 7:
            countdown = f'{days_until} days'
        elif days_until < 14:
            countdown = '1 week'
        else:
            weeks = days_until // 7
            countdown = f'{weeks} weeks'

    return success_response(
        data={
            'date': session_date,
            'countdown': countdown,
            'active_goals': active_goals
        },
        message='Next session data retrieved successfully'
    )
