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

from .. import db, csrf
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


# ====================================================================================
# POST /api/ai-coach/message - Send message to AI coach
# ====================================================================================

@ai_coach_api_bp.route('/message', methods=['POST'])
@csrf.exempt
@require_active_user
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

        # Handle READ function calls (query data)
        # Execute immediately and provide results to AI for informed response
        if function_call and function_call['name'].startswith('get_'):
            logger.info(f"READ function detected: {function_call['name']}")

            # Define READ function handler map
            QUERY_HANDLERS = {
                'get_recent_health_metrics': _query_health_metrics,
                'get_workout_history': _query_workout_history,
                'get_nutrition_summary': _query_nutrition_summary,
                'get_user_goals': _query_user_goals,
                'get_coaching_history': _query_coaching_history,
                'get_progress_summary': _query_progress_summary,
                'get_behavior_tracking': _query_behavior_tracking,
                'get_behavior_plan_compliance': _query_behavior_compliance
            }

            if function_call['name'] in QUERY_HANDLERS:
                try:
                    # Execute query
                    handler = QUERY_HANDLERS[function_call['name']]
                    query_data, summary = handler(current_user.id, function_call['args'])

                    # Add query result to conversation context
                    query_result_message = f"[Data Query Result]\n{summary}\n\nFull data available for reference."
                    conversation.add_message('system', query_result_message)

                    # Get AI's final response with data context
                    try:
                        assistant_response, _ = gemini.chat(
                            user_message="Based on the data provided above, please give your coaching response.",
                            conversation_history=conversation.messages,
                            function_declarations=None,  # No more function calling in this turn
                            max_context_messages=15  # Include more context for data-informed response
                        )
                        function_call = None  # Clear function call since we executed it
                    except Exception as e:
                        logger.error(f"Gemini API error on data-informed response: {e}", exc_info=True)
                        assistant_response = f"I've reviewed your data: {summary}. Let me know if you have questions!"

                except Exception as e:
                    logger.error(f"Error executing query function: {e}", exc_info=True)
                    assistant_response = "I tried to access your data but encountered an error. Let's continue our conversation."
                    function_call = None

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
@csrf.exempt
@require_active_user
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
            'create_coaching_session': _save_coaching_session,
            'create_behavior_definition': _save_behavior_definition,
            'log_behavior': _save_behavior_log
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


def _save_behavior_definition(user_id: int, data: dict) -> tuple:
    """Save behavior definition record."""
    from ..models.behavior import BehaviorDefinition, BehaviorCategory

    # Validate required fields
    name = data.get('name')
    if not name:
        raise ValueError('name is required')

    # Check for duplicate behavior name for this user
    existing = BehaviorDefinition.query.filter_by(
        user_id=user_id,
        name=name,
        is_active=True
    ).first()

    if existing:
        raise ValueError(f'Behavior "{name}" already exists')

    # Validate category
    category_str = data.get('category', 'CUSTOM')
    try:
        category = BehaviorCategory[category_str]
    except KeyError:
        raise ValueError(f'Invalid category: {category_str}')

    # Validate target_frequency (1-7)
    target_frequency = data.get('target_frequency', 7)
    if not isinstance(target_frequency, int) or target_frequency < 1 or target_frequency > 7:
        raise ValueError('target_frequency must be between 1 and 7')

    # Get highest display_order for this user
    max_order = db.session.query(db.func.max(BehaviorDefinition.display_order)).filter_by(
        user_id=user_id
    ).scalar() or 0

    # Create behavior definition
    behavior = BehaviorDefinition(
        user_id=user_id,
        name=name,
        description=data.get('description'),
        category=category,
        icon=data.get('icon', 'bi-check-circle'),
        color=data.get('color', '#4A90E2'),
        display_order=max_order + 1,
        target_frequency=target_frequency,
        is_active=True
    )

    db.session.add(behavior)
    return behavior, 'behavior_definition'


def _save_behavior_log(user_id: int, data: dict) -> tuple:
    """Save behavior log record."""
    from ..models.behavior import BehaviorDefinition, BehaviorLog

    # Validate required fields
    behavior_name = data.get('behavior_name')
    if not behavior_name:
        raise ValueError('behavior_name is required')

    # Validate and parse date
    tracked_date_str = data.get('tracked_date')
    if not tracked_date_str:
        raise ValueError('tracked_date is required')

    is_valid, result = validate_date_format(tracked_date_str)
    if not is_valid:
        raise ValueError(result)
    tracked_date = result

    # Find behavior definition by name
    behavior_def = BehaviorDefinition.query.filter_by(
        user_id=user_id,
        name=behavior_name,
        is_active=True
    ).first()

    if not behavior_def:
        raise ValueError(f'Behavior "{behavior_name}" not found. Create it first with create_behavior_definition.')

    # Check if log already exists for this date
    existing_log = BehaviorLog.query.filter_by(
        user_id=user_id,
        behavior_definition_id=behavior_def.id,
        tracked_date=tracked_date
    ).first()

    completed = data.get('completed', True)

    if existing_log:
        # Update existing log
        existing_log.completed = completed
        existing_log.notes = data.get('notes')
        existing_log.updated_at = datetime.now(timezone.utc)
        return existing_log, 'behavior_log'
    else:
        # Create new log
        log = BehaviorLog(
            user_id=user_id,
            behavior_definition_id=behavior_def.id,
            tracked_date=tracked_date,
            completed=completed,
            notes=data.get('notes')
        )
        db.session.add(log)
        return log, 'behavior_log'


# ====================================================================================
# POST /api/ai-coach/query-data - Execute data query for AI coach
# ====================================================================================

@ai_coach_api_bp.route('/query-data', methods=['POST'])
@csrf.exempt
@require_active_user
def query_user_data():
    """
    Execute AI coach data query function.

    Allows AI to READ historical user data for informed coaching.

    Request Body:
        {
            "function_name": "get_recent_health_metrics",
            "parameters": {"days": 7, "include_trends": true}
        }

    Returns:
        {
            "success": true,
            "data": {...},  // Query results
            "summary": "..."  // Human-readable summary for AI context
        }
    """
    try:
        # Validate request
        is_valid, data_or_errors = validate_request_data(
            required_fields=['function_name'],
            optional_fields=['parameters']
        )

        if not is_valid:
            return error_response(**data_or_errors)

        function_name = data_or_errors['function_name']
        parameters = data_or_errors.get('parameters', {})

        # Handler map for query functions
        QUERY_HANDLERS = {
            'get_recent_health_metrics': _query_health_metrics,
            'get_workout_history': _query_workout_history,
            'get_nutrition_summary': _query_nutrition_summary,
            'get_user_goals': _query_user_goals,
            'get_coaching_history': _query_coaching_history,
            'get_progress_summary': _query_progress_summary,
            'get_behavior_tracking': _query_behavior_tracking,
            'get_behavior_plan_compliance': _query_behavior_compliance
        }

        if function_name not in QUERY_HANDLERS:
            return error_response(f'Unknown query function: {function_name}', status_code=400)

        # Execute query handler
        handler = QUERY_HANDLERS[function_name]
        query_data, summary = handler(current_user.id, parameters)

        return success_response({
            'data': query_data,
            'summary': summary
        })

    except Exception as e:
        logger.error(f'Error executing query function: {e}', exc_info=True)
        return error_response(f'Query failed: {str(e)}', status_code=500)


# ====================================================================================
# Query Handler Functions
# ====================================================================================

def _query_health_metrics(user_id: int, params: dict) -> tuple:
    """Query recent health metrics."""
    from ..models.health import HealthMetric
    from datetime import timedelta

    # Get parameters
    days = min(params.get('days', 7), 90)  # Max 90 days
    include_trends = params.get('include_trends', True)

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Query health metrics
    metrics = HealthMetric.query.filter(
        HealthMetric.user_id == user_id,
        HealthMetric.recorded_date >= start_date,
        HealthMetric.recorded_date <= end_date
    ).order_by(HealthMetric.recorded_date.desc()).all()

    if not metrics:
        return {}, "No health metrics recorded in the specified period."

    # Build data response
    data = {
        'count': len(metrics),
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'latest': metrics[0].to_dict() if metrics else None,
        'metrics': [m.to_dict() for m in metrics]
    }

    # Calculate trends if requested
    if include_trends and len(metrics) > 1:
        weights = [m.weight_lbs for m in reversed(metrics) if m.weight_lbs]
        body_fats = [m.body_fat_percentage for m in reversed(metrics) if m.body_fat_percentage]

        trends = {}
        if weights:
            trends['weight'] = {
                'start': weights[0],
                'end': weights[-1],
                'change': round(weights[-1] - weights[0], 1),
                'average': round(sum(weights) / len(weights), 1)
            }
        if body_fats:
            trends['body_fat'] = {
                'start': body_fats[0],
                'end': body_fats[-1],
                'change': round(body_fats[-1] - body_fats[0], 1),
                'average': round(sum(body_fats) / len(body_fats), 1)
            }
        data['trends'] = trends

    # Generate AI summary
    latest = metrics[0]
    summary_parts = []

    if latest.weight_lbs:
        summary_parts.append(f"Latest weight: {latest.weight_lbs} lbs")
    if latest.body_fat_percentage:
        summary_parts.append(f"body fat {latest.body_fat_percentage}%")

    if include_trends and 'trends' in data and 'weight' in data['trends']:
        weight_change = data['trends']['weight']['change']
        direction = "DOWN" if weight_change < 0 else "UP" if weight_change > 0 else "STABLE"
        summary_parts.append(f"(trending {direction} by {abs(weight_change)} lbs over {days} days)")

    summary = f"Last {days} days: {len(metrics)} check-ins. " + ", ".join(summary_parts)

    return data, summary


def _query_workout_history(user_id: int, params: dict) -> tuple:
    """Query recent workout sessions."""
    from ..models.workout import WorkoutSession, SessionType
    from datetime import timedelta

    # Get parameters
    days = min(params.get('days', 7), 30)  # Max 30 days
    session_type_str = params.get('session_type')
    include_exercises = params.get('include_exercises', False)

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Build query
    query = WorkoutSession.query.filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.session_date >= start_date,
        WorkoutSession.session_date <= end_date
    )

    # Filter by session type if provided
    if session_type_str:
        try:
            session_type = SessionType[session_type_str]
            query = query.filter(WorkoutSession.session_type == session_type)
        except KeyError:
            pass  # Invalid session type, ignore filter

    sessions = query.order_by(WorkoutSession.session_date.desc()).all()

    if not sessions:
        return {}, f"No workouts recorded in the last {days} days."

    # Build data response
    data = {
        'count': len(sessions),
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'sessions': []
    }

    for session in sessions:
        session_dict = session.to_dict()
        if not include_exercises:
            session_dict.pop('exercise_logs', None)  # Exclude exercises if not requested
        data['sessions'].append(session_dict)

    # Generate AI summary
    total_duration = sum(s.duration_minutes or 0 for s in sessions)
    session_types = {}
    for s in sessions:
        session_types[s.session_type.value] = session_types.get(s.session_type.value, 0) + 1

    type_summary = ", ".join([f"{count} {stype}" for stype, count in session_types.items()])
    summary = f"Last {days} days: {len(sessions)} workouts ({type_summary}), {total_duration} total minutes"

    return data, summary


def _query_nutrition_summary(user_id: int, params: dict) -> tuple:
    """Query nutrition data and adherence."""
    from ..models.nutrition import MealLog
    from datetime import timedelta

    # Get parameters
    days = min(params.get('days', 7), 30)  # Max 30 days
    summary_type = params.get('summary_type', 'weekly')

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Query meal logs
    meals = MealLog.query.filter(
        MealLog.user_id == user_id,
        MealLog.meal_date >= start_date,
        MealLog.meal_date <= end_date
    ).order_by(MealLog.meal_date.desc()).all()

    if not meals:
        return {}, f"No meals logged in the last {days} days."

    # Build data response
    data = {
        'count': len(meals),
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    }

    # Calculate totals
    total_calories = sum(m.calories or 0 for m in meals)
    total_protein = sum(m.protein_g or 0 for m in meals)
    total_carbs = sum(m.carbs_g or 0 for m in meals)
    total_fat = sum(m.fat_g or 0 for m in meals)

    data['totals'] = {
        'calories': total_calories,
        'protein_g': round(total_protein, 1),
        'carbs_g': round(total_carbs, 1),
        'fat_g': round(total_fat, 1)
    }

    # Calculate averages
    days_with_logs = len(set(m.meal_date for m in meals))
    if days_with_logs > 0:
        data['daily_averages'] = {
            'calories': round(total_calories / days_with_logs),
            'protein_g': round(total_protein / days_with_logs, 1),
            'carbs_g': round(total_carbs / days_with_logs, 1),
            'fat_g': round(total_fat / days_with_logs, 1)
        }

    # Generate AI summary
    avg_cals = data.get('daily_averages', {}).get('calories', 0)
    avg_protein = data.get('daily_averages', {}).get('protein_g', 0)
    summary = f"Last {days} days: {len(meals)} meals logged across {days_with_logs} days. " \
              f"Daily avg: {avg_cals} calories, {avg_protein}g protein"

    return data, summary


def _query_user_goals(user_id: int, params: dict) -> tuple:
    """Query user goals and progress."""
    from ..models.coaching import UserGoal

    # Get parameters
    status_filter = params.get('status', 'active')

    # Build query
    query = UserGoal.query.filter(UserGoal.user_id == user_id)

    if status_filter == 'active':
        query = query.filter(UserGoal.completed == False)
    elif status_filter == 'completed':
        query = query.filter(UserGoal.completed == True)
    # 'all' - no filter

    goals = query.order_by(UserGoal.target_date.asc()).all()

    if not goals:
        return {}, f"No {status_filter} goals found."

    # Build data response
    data = {
        'count': len(goals),
        'goals': [g.to_dict() for g in goals]
    }

    # Generate AI summary
    if status_filter == 'active':
        goal_types = {}
        for g in goals:
            goal_types[g.goal_type.value] = goal_types.get(g.goal_type.value, 0) + 1
        type_summary = ", ".join([f"{count} {gtype}" for gtype, count in goal_types.items()])
        summary = f"{len(goals)} active goals: {type_summary}"
    else:
        summary = f"{len(goals)} {status_filter} goals found"

    return data, summary


def _query_coaching_history(user_id: int, params: dict) -> tuple:
    """Query previous coaching sessions."""
    from ..models.coaching import CoachingSession

    # Get parameters
    limit = min(params.get('limit', 5), 20)  # Max 20 sessions

    # Query coaching sessions
    sessions = CoachingSession.query.filter(
        CoachingSession.user_id == user_id
    ).order_by(CoachingSession.session_date.desc()).limit(limit).all()

    if not sessions:
        return {}, "No previous coaching sessions found."

    # Build data response
    data = {
        'count': len(sessions),
        'sessions': [s.to_dict() for s in sessions]
    }

    # Generate AI summary
    latest = sessions[0]
    summary = f"Retrieved {len(sessions)} recent coaching sessions. " \
              f"Most recent: {latest.session_date.isoformat()}"

    return data, summary


def _query_progress_summary(user_id: int, params: dict) -> tuple:
    """Get comprehensive progress overview."""
    from datetime import timedelta

    # Get parameters
    period_days = min(params.get('period_days', 30), 90)  # Max 90 days

    # Query all data types using existing handlers
    health_data, health_summary = _query_health_metrics(user_id, {'days': period_days, 'include_trends': True})
    workout_data, workout_summary = _query_workout_history(user_id, {'days': period_days})
    nutrition_data, nutrition_summary = _query_nutrition_summary(user_id, {'days': period_days})
    goals_data, goals_summary = _query_user_goals(user_id, {'status': 'active'})

    # Build comprehensive data response
    data = {
        'period_days': period_days,
        'health': health_data,
        'workouts': workout_data,
        'nutrition': nutrition_data,
        'goals': goals_data
    }

    # Generate comprehensive AI summary
    summary = f"Progress overview for last {period_days} days:\n" \
              f"- Health: {health_summary}\n" \
              f"- Workouts: {workout_summary}\n" \
              f"- Nutrition: {nutrition_summary}\n" \
              f"- Goals: {goals_summary}"

    return data, summary


def _query_behavior_tracking(user_id: int, params: dict) -> tuple:
    """Query behavior tracking data including completion history and streaks."""
    from ..models.behavior import BehaviorDefinition, BehaviorLog
    from datetime import timedelta

    # Get parameters
    days = min(params.get('days', 7), 30)  # Max 30 days
    behavior_name = params.get('behavior_name')

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get behaviors
    behavior_query = BehaviorDefinition.query.filter_by(
        user_id=user_id,
        is_active=True
    )

    if behavior_name:
        behavior_query = behavior_query.filter_by(name=behavior_name)

    behaviors = behavior_query.order_by(BehaviorDefinition.display_order).all()

    if not behaviors:
        suffix = f' matching "{behavior_name}"' if behavior_name else ''
        return {}, f"No behaviors found{suffix}."

    # Query logs
    behavior_ids = [b.id for b in behaviors]
    logs = BehaviorLog.query.filter(
        BehaviorLog.user_id == user_id,
        BehaviorLog.behavior_definition_id.in_(behavior_ids),
        BehaviorLog.tracked_date >= start_date,
        BehaviorLog.tracked_date <= end_date
    ).all()

    # Organize logs by behavior
    logs_by_behavior = {}
    for log in logs:
        if log.behavior_definition_id not in logs_by_behavior:
            logs_by_behavior[log.behavior_definition_id] = []
        logs_by_behavior[log.behavior_definition_id].append(log)

    # Build data response
    data = {
        'count': len(behaviors),
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'behaviors': []
    }

    # Calculate streaks and completion rates
    for behavior in behaviors:
        behavior_logs = logs_by_behavior.get(behavior.id, [])
        completed_count = sum(1 for log in behavior_logs if log.completed)
        completion_rate = round((completed_count / days) * 100, 1) if days > 0 else 0

        # Calculate current streak (consecutive days up to today)
        current_streak = 0
        check_date = end_date
        logs_by_date = {log.tracked_date: log for log in behavior_logs}

        while check_date >= start_date:
            log = logs_by_date.get(check_date)
            if log and log.completed:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        behavior_data = {
            'id': behavior.id,
            'name': behavior.name,
            'category': behavior.category.value,
            'target_frequency': behavior.target_frequency,
            'completed_count': completed_count,
            'total_days': days,
            'completion_rate': completion_rate,
            'current_streak': current_streak
        }

        data['behaviors'].append(behavior_data)

    # Generate AI summary
    if behavior_name and len(behaviors) == 1:
        b = data['behaviors'][0]
        summary = f"{b['name']}: {b['completed_count']}/{days} days completed ({b['completion_rate']}%), " \
                  f"current streak: {b['current_streak']} days"
    else:
        avg_completion = round(sum(b['completion_rate'] for b in data['behaviors']) / len(data['behaviors']), 1) if data['behaviors'] else 0
        total_completed = sum(b['completed_count'] for b in data['behaviors'])
        summary = f"Tracking {len(behaviors)} behaviors over last {days} days. " \
                  f"Total completions: {total_completed}, avg completion rate: {avg_completion}%"

    return data, summary


def _query_behavior_compliance(user_id: int, params: dict) -> tuple:
    """Analyze behavior plan compliance by comparing actual vs. target frequency."""
    from ..models.behavior import BehaviorDefinition, BehaviorLog
    from datetime import timedelta

    # Get parameters
    period = params.get('period', 'week')
    include_recommendations = params.get('include_recommendations', True)

    # Calculate date range based on period
    end_date = date.today()
    if period == 'week':
        start_date = end_date - timedelta(days=7)
        days = 7
    else:  # month
        start_date = end_date - timedelta(days=30)
        days = 30

    # Get all active behaviors
    behaviors = BehaviorDefinition.query.filter_by(
        user_id=user_id,
        is_active=True
    ).order_by(BehaviorDefinition.display_order).all()

    if not behaviors:
        return {}, "No behaviors to track. Create some behaviors first!"

    # Query logs
    behavior_ids = [b.id for b in behaviors]
    logs = BehaviorLog.query.filter(
        BehaviorLog.user_id == user_id,
        BehaviorLog.behavior_definition_id.in_(behavior_ids),
        BehaviorLog.tracked_date >= start_date,
        BehaviorLog.tracked_date <= end_date
    ).all()

    # Organize logs by behavior
    logs_by_behavior = {}
    for log in logs:
        if log.behavior_definition_id not in logs_by_behavior:
            logs_by_behavior[log.behavior_definition_id] = []
        logs_by_behavior[log.behavior_definition_id].append(log)

    # Build compliance data
    data = {
        'period': period,
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'behaviors': []
    }

    # Analyze each behavior
    for behavior in behaviors:
        behavior_logs = logs_by_behavior.get(behavior.id, [])
        completed_count = sum(1 for log in behavior_logs if log.completed)

        # Calculate target for the period
        if period == 'week':
            target = behavior.target_frequency
        else:  # month - scale weekly target to monthly (target * 4.3)
            target = round(behavior.target_frequency * 4.3)

        # Calculate compliance rate
        compliance_rate = round((completed_count / target) * 100, 1) if target > 0 else 0

        # Determine status
        if compliance_rate >= 90:
            status = 'excellent'
        elif compliance_rate >= 70:
            status = 'on_track'
        elif compliance_rate >= 50:
            status = 'needs_improvement'
        else:
            status = 'off_track'

        # Find missed dates
        logs_by_date = {log.tracked_date: log for log in behavior_logs}
        missed_dates = []
        check_date = start_date
        while check_date <= end_date:
            log = logs_by_date.get(check_date)
            if not log or not log.completed:
                missed_dates.append(check_date.isoformat())
            check_date += timedelta(days=1)

        behavior_compliance = {
            'name': behavior.name,
            'target': target,
            'actual': completed_count,
            'compliance_rate': compliance_rate,
            'status': status,
            'missed_dates': missed_dates[:5]  # Limit to first 5
        }

        # Add recommendations if requested
        if include_recommendations:
            if status == 'off_track':
                behavior_compliance['recommendation'] = f"You're significantly behind on {behavior.name}. " \
                    f"Try to complete it at least {target - completed_count} more times this {period}."
            elif status == 'needs_improvement':
                behavior_compliance['recommendation'] = f"You're making progress on {behavior.name}, but could improve. " \
                    f"Aim for {target - completed_count} more completions this {period}."
            elif status == 'on_track':
                behavior_compliance['recommendation'] = f"Great consistency with {behavior.name}! Keep it up."
            else:  # excellent
                behavior_compliance['recommendation'] = f"Outstanding work on {behavior.name}! You're crushing it."

        data['behaviors'].append(behavior_compliance)

    # Calculate overall compliance
    total_target = sum(b['target'] for b in data['behaviors'])
    total_actual = sum(b['actual'] for b in data['behaviors'])
    overall_compliance = round((total_actual / total_target) * 100, 1) if total_target > 0 else 0

    data['overall_compliance'] = overall_compliance

    # Generate AI summary
    on_track_count = sum(1 for b in data['behaviors'] if b['status'] in ['excellent', 'on_track'])
    summary = f"Behavior compliance for last {period}: {overall_compliance}% overall. " \
              f"{on_track_count}/{len(behaviors)} behaviors on track or better."

    return data, summary
