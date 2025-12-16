"""
AI Coach API
============

RESTful API endpoints for AI coaching interface.

Endpoints:
- POST /api/ai-coach/message - Send message to AI coach
- GET /api/ai-coach/conversations - List user's conversations
- GET /api/ai-coach/conversations/<id> - Get specific conversation
- POST /api/ai-coach/save-record - Save AI-suggested database record
"""

import logging
from datetime import datetime, timezone, date
from flask import Blueprint, request
from flask_login import current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .. import db
from ..models.conversation import ConversationLog
from ..models.health import HealthMetric
from ..models.nutrition import MealLog, MealType
from ..models.workout import WorkoutSession, ExerciseLog, SessionType
from ..models.coaching import CoachingSession
from ..services.gemini_service import GeminiService
from ..utils.ai_coach_tools import get_all_function_declarations
from . import (
    success_response,
    error_response,
    paginated_response,
    require_active_user,
    validate_request_data,
    validate_pagination_params,
    validate_date_format
)

# Create blueprint
ai_coach_api_bp = Blueprint('ai_coach_api', __name__, url_prefix='/ai-coach')

# Configure logger
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)


# ====================================================================================
# POST /api/ai-coach/message - Send message to AI coach
# ====================================================================================

@ai_coach_api_bp.route('/message', methods=['POST'])
@require_active_user
@limiter.limit("20 per minute")
def send_message():
    """
    Send a message to the AI coach and get response.

    Request Body:
        {
            "message": "I weighed myself today at 175 lbs",
            "conversation_id": 123  // Optional - creates new if not provided
        }

    Returns:
        {
            "success": true,
            "data": {
                "conversation_id": 123,
                "message": "user message",
                "response": "AI response",
                "function_call": {  // Optional - only if AI suggests a record
                    "name": "create_health_metric",
                    "args": {...}
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        # Validate request
        is_valid, data_or_errors = validate_request_data(
            required_fields=['message'],
            optional_fields=['conversation_id']
        )

        if not is_valid:
            return error_response(**data_or_errors)

        user_message = data_or_errors['message'].strip()
        conversation_id = data_or_errors.get('conversation_id')

        if not user_message:
            return error_response('Message cannot be empty')

        # Get or create conversation
        if conversation_id:
            conversation = ConversationLog.query.filter_by(
                id=conversation_id,
                user_id=current_user.id
            ).first()

            if not conversation:
                return error_response('Conversation not found', status_code=404)
        else:
            # Create new conversation
            conversation = ConversationLog(
                user_id=current_user.id,
                conversation_date=datetime.now(timezone.utc),
                messages=[],
                is_active=True
            )
            db.session.add(conversation)

        # Add user message to conversation
        conversation.add_message('user', user_message)

        # Initialize Gemini service
        try:
            gemini = GeminiService()
        except ValueError as e:
            logger.error(f"Gemini service initialization failed: {e}")
            return error_response(
                'AI coach is not configured. Please contact administrator.',
                status_code=503
            )

        # Get AI response with function calling support
        try:
            assistant_response, function_call = gemini.chat(
                user_message=user_message,
                conversation_history=conversation.messages,
                function_declarations=get_all_function_declarations(),
                max_context_messages=10
            )
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            return error_response(
                'Failed to get response from AI coach. Please try again.',
                status_code=500
            )

        # Add assistant response to conversation
        metadata = {'function_call': function_call} if function_call else None
        conversation.add_message('assistant', assistant_response, metadata=metadata)

        # Auto-generate title if this is the first user message
        if conversation.message_count == 2 and not conversation.title:
            conversation.title = conversation.generate_title()

        # Save conversation
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save conversation: {e}", exc_info=True)
            return error_response('Failed to save conversation', status_code=500)

        # Build response
        response_data = {
            'conversation_id': conversation.id,
            'message': user_message,
            'response': assistant_response,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if function_call:
            response_data['function_call'] = function_call

        return success_response(response_data, message='Message sent successfully')

    except Exception as e:
        logger.error(f"Unexpected error in send_message: {e}", exc_info=True)
        return error_response('An unexpected error occurred', status_code=500)


# ====================================================================================
# GET /api/ai-coach/conversations - List user's conversations
# ====================================================================================

@ai_coach_api_bp.route('/conversations', methods=['GET'])
@require_active_user
def list_conversations():
    """
    Get list of user's conversations.

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - active_only: Filter for active conversations only (default: true)

    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 123,
                    "title": "Weight tracking discussion",
                    "message_count": 10,
                    "records_created": 2,
                    "is_active": true,
                    "created_at": "2024-01-15T10:00:00Z",
                    "last_message_at": "2024-01-15T11:30:00Z"
                },
                ...
            ],
            "pagination": {...}
        }
    """
    try:
        # Get pagination params
        page, per_page = validate_pagination_params()

        # Get active_only filter
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        # Build query
        query = ConversationLog.query.filter_by(user_id=current_user.id)

        if active_only:
            query = query.filter_by(is_active=True)

        # Order by most recent first
        query = query.order_by(ConversationLog.last_message_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Convert to dict
        conversations = [conv.to_summary_dict() for conv in pagination.items]

        return paginated_response(
            items=conversations,
            page=page,
            per_page=per_page,
            total=pagination.total,
            message='Conversations retrieved successfully'
        )

    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        return error_response('Failed to retrieve conversations', status_code=500)


# ====================================================================================
# GET /api/ai-coach/conversations/<int:conversation_id> - Get specific conversation
# ====================================================================================

@ai_coach_api_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@require_active_user
def get_conversation(conversation_id):
    """
    Get full conversation with all messages.

    Returns:
        {
            "success": true,
            "data": {
                "id": 123,
                "title": "Weight tracking discussion",
                "message_count": 10,
                "records_created": 2,
                "is_active": true,
                "created_at": "2024-01-15T10:00:00Z",
                "last_message_at": "2024-01-15T11:30:00Z",
                "messages": [
                    {
                        "role": "user",
                        "content": "I weighed myself today",
                        "timestamp": "2024-01-15T10:00:00Z"
                    },
                    ...
                ]
            }
        }
    """
    try:
        conversation = ConversationLog.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()

        if not conversation:
            return error_response('Conversation not found', status_code=404)

        return success_response(
            conversation.to_dict(include_messages=True),
            message='Conversation retrieved successfully'
        )

    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}", exc_info=True)
        return error_response('Failed to retrieve conversation', status_code=500)


# ====================================================================================
# POST /api/ai-coach/save-record - Save AI-suggested database record
# ====================================================================================

@ai_coach_api_bp.route('/save-record', methods=['POST'])
@require_active_user
@limiter.limit("10 per minute")
def save_record():
    """
    Save an AI-suggested record to the database.

    Request Body:
        {
            "conversation_id": 123,
            "function_name": "create_health_metric",
            "record_data": {
                "recorded_date": "2024-01-15",
                "weight_lbs": 175.5,
                "notes": "Feeling good"
            }
        }

    Returns:
        {
            "success": true,
            "data": {
                "record_type": "health_metric",
                "record_id": 456,
                "record": {...}  // Full record data
            }
        }
    """
    try:
        # Validate request
        is_valid, data_or_errors = validate_request_data(
            required_fields=['conversation_id', 'function_name', 'record_data']
        )

        if not is_valid:
            return error_response(**data_or_errors)

        conversation_id = data_or_errors['conversation_id']
        function_name = data_or_errors['function_name']
        record_data = data_or_errors['record_data']

        # Verify conversation belongs to user
        conversation = ConversationLog.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()

        if not conversation:
            return error_response('Conversation not found', status_code=404)

        # Route to appropriate handler based on function name
        handler_map = {
            'create_health_metric': _save_health_metric,
            'create_meal_log': _save_meal_log,
            'create_workout': _save_workout,
            'create_coaching_session': _save_coaching_session
        }

        handler = handler_map.get(function_name)
        if not handler:
            return error_response(f'Unknown function: {function_name}', status_code=400)

        # Save the record
        try:
            record, record_type = handler(current_user.id, record_data)
        except ValueError as e:
            return error_response(str(e), status_code=400)
        except Exception as e:
            logger.error(f"Error saving record: {e}", exc_info=True)
            return error_response('Failed to save record', status_code=500)

        # Increment records_created counter
        conversation.increment_records_created()

        # Commit all changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit record: {e}", exc_info=True)
            return error_response('Failed to save record', status_code=500)

        return success_response(
            {
                'record_type': record_type,
                'record_id': record.id,
                'record': record.to_dict()
            },
            message=f'{record_type.replace("_", " ").title()} saved successfully',
            status_code=201
        )

    except Exception as e:
        logger.error(f"Unexpected error in save_record: {e}", exc_info=True)
        return error_response('An unexpected error occurred', status_code=500)


# ====================================================================================
# Helper Functions for Saving Records
# ====================================================================================

def _save_health_metric(user_id: int, data: dict) -> tuple:
    """Save health metric record."""
    # Validate and parse date
    recorded_date_str = data.get('recorded_date')
    if not recorded_date_str:
        raise ValueError('recorded_date is required')

    is_valid, result = validate_date_format(recorded_date_str)
    if not is_valid:
        raise ValueError(result)
    recorded_date = result

    # Create record
    metric = HealthMetric(
        user_id=user_id,
        recorded_date=recorded_date,
        weight_lbs=data.get('weight_lbs'),
        body_fat_percentage=data.get('body_fat_percentage'),
        waist_inches=data.get('waist_inches'),
        chest_inches=data.get('chest_inches'),
        energy_level=data.get('energy_level'),
        mood=data.get('mood'),
        sleep_quality=data.get('sleep_quality'),
        notes=data.get('notes')
    )

    db.session.add(metric)
    return metric, 'health_metric'


def _save_meal_log(user_id: int, data: dict) -> tuple:
    """Save meal log record."""
    # Validate and parse date
    meal_date_str = data.get('meal_date')
    if not meal_date_str:
        raise ValueError('meal_date is required')

    is_valid, result = validate_date_format(meal_date_str)
    if not is_valid:
        raise ValueError(result)
    meal_date = result

    # Validate meal_type
    meal_type_str = data.get('meal_type')
    if not meal_type_str:
        raise ValueError('meal_type is required')

    try:
        meal_type = MealType[meal_type_str]
    except KeyError:
        raise ValueError(f'Invalid meal_type: {meal_type_str}')

    # Create record
    meal = MealLog(
        user_id=user_id,
        meal_date=meal_date,
        meal_type=meal_type,
        calories=data.get('calories'),
        protein_g=data.get('protein_g'),
        carbs_g=data.get('carbs_g'),
        fat_g=data.get('fat_g'),
        fiber_g=data.get('fiber_g'),
        description=data.get('description')
    )

    db.session.add(meal)
    return meal, 'meal_log'


def _save_workout(user_id: int, data: dict) -> tuple:
    """Save workout session with exercises."""
    # Validate and parse date
    session_date_str = data.get('session_date')
    if not session_date_str:
        raise ValueError('session_date is required')

    is_valid, result = validate_date_format(session_date_str)
    if not is_valid:
        raise ValueError(result)
    session_date = result

    # Validate session_type
    session_type_str = data.get('session_type')
    if not session_type_str:
        raise ValueError('session_type is required')

    try:
        session_type = SessionType[session_type_str]
    except KeyError:
        raise ValueError(f'Invalid session_type: {session_type_str}')

    # Create workout session
    workout = WorkoutSession(
        user_id=user_id,
        session_date=session_date,
        session_type=session_type,
        duration_minutes=data.get('duration_minutes'),
        intensity_level=data.get('intensity_level'),
        notes=data.get('notes')
    )

    db.session.add(workout)
    db.session.flush()  # Get workout.id for exercises

    # Add exercises
    exercises_data = data.get('exercises', [])
    for ex_data in exercises_data:
        exercise = ExerciseLog(
            workout_session_id=workout.id,
            exercise_name=ex_data.get('exercise_name'),
            sets=ex_data.get('sets'),
            reps=ex_data.get('reps'),
            weight_lbs=ex_data.get('weight_lbs'),
            duration_seconds=ex_data.get('duration_seconds'),
            notes=ex_data.get('notes')
        )
        db.session.add(exercise)

    return workout, 'workout_session'


def _save_coaching_session(user_id: int, data: dict) -> tuple:
    """Save coaching session record."""
    # Validate and parse date
    session_date_str = data.get('session_date')
    if not session_date_str:
        raise ValueError('session_date is required')

    is_valid, result = validate_date_format(session_date_str)
    if not is_valid:
        raise ValueError(result)
    session_date = result

    # Create record
    # Note: coach_id is set to user_id since this is AI coaching (self-coaching)
    session = CoachingSession(
        user_id=user_id,
        coach_id=user_id,  # AI coach sessions are self-referential
        session_date=session_date,
        discussion_notes=data.get('discussion_notes'),
        coach_feedback=data.get('coach_feedback'),
        action_items=data.get('action_items', [])
    )

    db.session.add(session)
    return session, 'coaching_session'
