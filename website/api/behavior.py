"""
Behavior Tracking API
=====================

RESTful API endpoints for behavior definition and logging.

Endpoints:
- Behavior Definition CRUD
- Behavior Log CRUD
- Analytics and Statistics
- Compliance Analysis
"""

import logging
from datetime import datetime, timezone, date, timedelta
from flask import Blueprint, request
from flask_login import current_user
from sqlalchemy import func, and_

from .. import db, csrf
from ..models.behavior import BehaviorDefinition, BehaviorLog, BehaviorCategory
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
behavior_api_bp = Blueprint('behavior_api', __name__, url_prefix='/behavior')

# Configure logger
logger = logging.getLogger(__name__)


# ====================================================================================
# Behavior Definition Endpoints
# ====================================================================================

@behavior_api_bp.route('/definitions', methods=['GET'])
@require_active_user
def get_behavior_definitions():
    """
    Get list of user's behavior definitions.

    Query Parameters:
        - include_inactive (bool): Include inactive (archived) behaviors (default: false)
        - include_stats (bool): Include recent completion statistics (default: false)

    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "name": "Morning Weigh-In",
                    "category": "health",
                    "icon": "bi-scale",
                    "color": "#1a237e",
                    "target_frequency": 7,
                    ...
                }
            ]
        }
    """
    try:
        # Get query parameters
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'

        # Build query
        query = BehaviorDefinition.query.filter_by(user_id=current_user.id)

        if not include_inactive:
            query = query.filter_by(is_active=True)

        # Order by display_order, then name
        behaviors = query.order_by(
            BehaviorDefinition.display_order,
            BehaviorDefinition.name
        ).all()

        # Serialize to dict
        data = [b.to_dict(include_stats=include_stats) for b in behaviors]

        return success_response(data)

    except Exception as e:
        logger.error(f"Error fetching behavior definitions: {e}", exc_info=True)
        return error_response('Failed to fetch behavior definitions', status_code=500)


@behavior_api_bp.route('/definitions', methods=['POST'])
@csrf.exempt
@require_active_user
def create_behavior_definition():
    """
    Create a new behavior definition.

    Request Body:
        {
            "name": "Morning Meditation",
            "description": "10 minutes of mindfulness meditation",
            "category": "wellness",
            "target_frequency": 7,
            "icon": "bi-peace",
            "color": "#6a5acd"
        }

    Returns:
        {
            "success": true,
            "data": {behavior_definition_dict}
        }
    """
    try:
        # Validate request
        is_valid, data_or_errors = validate_request_data(
            required_fields=['name', 'category'],
            optional_fields=['description', 'target_frequency', 'icon', 'color', 'display_order']
        )

        if not is_valid:
            return error_response(**data_or_errors)

        data = data_or_errors

        # Validate category
        try:
            category = BehaviorCategory[data['category'].upper()]
        except KeyError:
            return error_response(f"Invalid category: {data['category']}. Must be one of: {', '.join([c.value for c in BehaviorCategory])}")

        # Check for duplicate name
        existing = BehaviorDefinition.query.filter_by(
            user_id=current_user.id,
            name=data['name']
        ).first()

        if existing:
            return error_response(f"Behavior '{data['name']}' already exists", status_code=409)

        # Validate target_frequency
        target_frequency = data.get('target_frequency')
        if target_frequency is not None:
            if not isinstance(target_frequency, int) or target_frequency < 1 or target_frequency > 7:
                return error_response('target_frequency must be between 1 and 7')

        # Create behavior definition
        behavior = BehaviorDefinition(
            user_id=current_user.id,
            name=data['name'],
            description=data.get('description'),
            category=category,
            target_frequency=target_frequency,
            icon=data.get('icon', 'bi-check-circle'),
            color=data.get('color', '#1a237e'),
            display_order=data.get('display_order', 0),
            is_active=True
        )

        db.session.add(behavior)
        db.session.commit()

        logger.info(f"Created behavior definition: {behavior.name} (ID: {behavior.id})")
        return success_response(behavior.to_dict(), status_code=201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating behavior definition: {e}", exc_info=True)
        return error_response('Failed to create behavior definition', status_code=500)


@behavior_api_bp.route('/definitions/<int:behavior_id>', methods=['GET'])
@require_active_user
def get_behavior_definition(behavior_id):
    """Get specific behavior definition."""
    try:
        behavior = BehaviorDefinition.query.filter_by(
            id=behavior_id,
            user_id=current_user.id
        ).first()

        if not behavior:
            return error_response('Behavior not found', status_code=404)

        return success_response(behavior.to_dict(include_stats=True))

    except Exception as e:
        logger.error(f"Error fetching behavior definition: {e}", exc_info=True)
        return error_response('Failed to fetch behavior definition', status_code=500)


@behavior_api_bp.route('/definitions/<int:behavior_id>', methods=['PUT'])
@csrf.exempt
@require_active_user
def update_behavior_definition(behavior_id):
    """Update behavior definition."""
    try:
        behavior = BehaviorDefinition.query.filter_by(
            id=behavior_id,
            user_id=current_user.id
        ).first()

        if not behavior:
            return error_response('Behavior not found', status_code=404)

        # Validate request
        is_valid, data_or_errors = validate_request_data(
            required_fields=[],
            optional_fields=['name', 'description', 'category', 'target_frequency', 'icon', 'color', 'display_order', 'is_active']
        )

        if not is_valid:
            return error_response(**data_or_errors)

        data = data_or_errors

        # Update fields
        if 'name' in data:
            # Check for duplicate name (excluding self)
            existing = BehaviorDefinition.query.filter(
                BehaviorDefinition.user_id == current_user.id,
                BehaviorDefinition.name == data['name'],
                BehaviorDefinition.id != behavior_id
            ).first()

            if existing:
                return error_response(f"Behavior '{data['name']}' already exists", status_code=409)

            behavior.name = data['name']

        if 'description' in data:
            behavior.description = data['description']

        if 'category' in data:
            try:
                behavior.category = BehaviorCategory[data['category'].upper()]
            except KeyError:
                return error_response(f"Invalid category: {data['category']}")

        if 'target_frequency' in data:
            if not isinstance(data['target_frequency'], int) or data['target_frequency'] < 1 or data['target_frequency'] > 7:
                return error_response('target_frequency must be between 1 and 7')
            behavior.target_frequency = data['target_frequency']

        if 'icon' in data:
            behavior.icon = data['icon']

        if 'color' in data:
            behavior.color = data['color']

        if 'display_order' in data:
            behavior.display_order = data['display_order']

        if 'is_active' in data:
            behavior.is_active = data['is_active']

        db.session.commit()

        logger.info(f"Updated behavior definition: {behavior.name} (ID: {behavior.id})")
        return success_response(behavior.to_dict())

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating behavior definition: {e}", exc_info=True)
        return error_response('Failed to update behavior definition', status_code=500)


@behavior_api_bp.route('/definitions/<int:behavior_id>', methods=['DELETE'])
@csrf.exempt
@require_active_user
def delete_behavior_definition(behavior_id):
    """Soft delete behavior definition (set is_active=false)."""
    try:
        behavior = BehaviorDefinition.query.filter_by(
            id=behavior_id,
            user_id=current_user.id
        ).first()

        if not behavior:
            return error_response('Behavior not found', status_code=404)

        # Soft delete
        behavior.is_active = False
        db.session.commit()

        logger.info(f"Deleted behavior definition: {behavior.name} (ID: {behavior.id})")
        return success_response({'message': 'Behavior archived successfully'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting behavior definition: {e}", exc_info=True)
        return error_response('Failed to delete behavior definition', status_code=500)


@behavior_api_bp.route('/definitions/reorder', methods=['PUT'])
@csrf.exempt
@require_active_user
def reorder_behavior_definitions():
    """
    Bulk update display_order for behavior definitions.

    Request Body:
        {
            "order": [
                {"id": 1, "display_order": 0},
                {"id": 3, "display_order": 1},
                {"id": 2, "display_order": 2}
            ]
        }
    """
    try:
        # Validate request
        is_valid, data_or_errors = validate_request_data(
            required_fields=['order'],
            optional_fields=[]
        )

        if not is_valid:
            return error_response(**data_or_errors)

        order_list = data_or_errors['order']

        if not isinstance(order_list, list):
            return error_response('order must be an array')

        # Update each behavior
        for item in order_list:
            if 'id' not in item or 'display_order' not in item:
                return error_response('Each order item must have id and display_order')

            behavior = BehaviorDefinition.query.filter_by(
                id=item['id'],
                user_id=current_user.id
            ).first()

            if behavior:
                behavior.display_order = item['display_order']

        db.session.commit()

        logger.info(f"Reordered {len(order_list)} behavior definitions")
        return success_response({'message': 'Behaviors reordered successfully'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reordering behaviors: {e}", exc_info=True)
        return error_response('Failed to reorder behaviors', status_code=500)


# ====================================================================================
# Behavior Log Endpoints
# ====================================================================================

@behavior_api_bp.route('/logs', methods=['GET'])
@require_active_user
def get_behavior_logs():
    """
    Get behavior logs with filters.

    Query Parameters:
        - start_date (YYYY-MM-DD): Filter by start date
        - end_date (YYYY-MM-DD): Filter by end date
        - behavior_id (int): Filter by specific behavior
        - page (int): Page number (default: 1)
        - per_page (int): Items per page (default: 50, max: 200)
    """
    try:
        from sqlalchemy.orm import joinedload

        # Log request details for debugging
        logger.info(f"Behavior logs request - user_id: {current_user.id}, start_date: {request.args.get('start_date')}, end_date: {request.args.get('end_date')}")

        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        behavior_id = request.args.get('behavior_id', type=int)

        # Validate pagination
        page, per_page = validate_pagination_params(default_per_page=50, max_per_page=1000)
        logger.info(f"Pagination params - page: {page}, per_page: {per_page}")

        # Build query with eager loading of behavior_definition
        query = BehaviorLog.query.options(joinedload(BehaviorLog.behavior_definition)).filter_by(user_id=current_user.id)

        # Date filters
        if start_date_str:
            is_valid, result = validate_date_format(start_date_str)
            if not is_valid:
                logger.error(f"Invalid start_date: {start_date_str}")
                return error_response(f'Invalid start_date: {result}')
            query = query.filter(BehaviorLog.tracked_date >= result)
            logger.info(f"Applied start_date filter: {result}")

        if end_date_str:
            is_valid, result = validate_date_format(end_date_str)
            if not is_valid:
                logger.error(f"Invalid end_date: {end_date_str}")
                return error_response(f'Invalid end_date: {result}')
            query = query.filter(BehaviorLog.tracked_date <= result)
            logger.info(f"Applied end_date filter: {result}")

        # Behavior filter
        if behavior_id:
            query = query.filter_by(behavior_definition_id=behavior_id)

        # Order by date descending
        query = query.order_by(BehaviorLog.tracked_date.desc())

        # Paginate
        logger.info("Executing query with pagination...")
        logs = query.paginate(page=page, per_page=per_page, error_out=False)
        logger.info(f"Query completed - found {logs.total} total logs, returning page {logs.page} with {len(logs.items)} items")

        # Serialize logs
        logger.info("Serializing logs...")
        serialized_logs = []
        for i, log in enumerate(logs.items):
            try:
                serialized_logs.append(log.to_dict())
            except Exception as serialize_error:
                logger.error(f"Error serializing log {log.id}: {serialize_error}", exc_info=True)
                raise

        logger.info(f"Successfully serialized {len(serialized_logs)} logs")

        # Return in same format as other endpoints to ensure compatibility
        return success_response({
            'items': serialized_logs,
            'pagination': {
                'page': logs.page,
                'per_page': logs.per_page,
                'total': logs.total,
                'pages': (logs.total // logs.per_page) + (1 if logs.total % logs.per_page > 0 else 0)
            }
        })

    except Exception as e:
        logger.error(f"Error fetching behavior logs: {e}", exc_info=True)
        return error_response('Failed to fetch behavior logs', status_code=500)


@behavior_api_bp.route('/logs', methods=['POST'])
@csrf.exempt
@require_active_user
def create_or_update_behavior_log():
    """
    Create or update behavior log for a specific date.

    Request Body:
        {
            "behavior_definition_id": 1,
            "tracked_date": "2024-01-15",
            "completed": true,
            "notes": "Felt great today"
        }
    """
    try:
        # Validate request
        is_valid, data_or_errors = validate_request_data(
            required_fields=['behavior_definition_id', 'tracked_date', 'completed'],
            optional_fields=['notes']
        )

        if not is_valid:
            return error_response(**data_or_errors)

        data = data_or_errors

        # Validate date
        is_valid, tracked_date = validate_date_format(data['tracked_date'])
        if not is_valid:
            return error_response(tracked_date)

        # Verify behavior exists and belongs to user
        behavior = BehaviorDefinition.query.filter_by(
            id=data['behavior_definition_id'],
            user_id=current_user.id
        ).first()

        if not behavior:
            return error_response('Behavior not found', status_code=404)

        # Get or create log
        log = BehaviorLog.query.filter_by(
            user_id=current_user.id,
            behavior_definition_id=data['behavior_definition_id'],
            tracked_date=tracked_date
        ).first()

        if log:
            # Update existing
            log.completed = data['completed']
            if 'notes' in data:
                log.notes = data['notes']
            action = 'updated'
        else:
            # Create new
            log = BehaviorLog(
                user_id=current_user.id,
                behavior_definition_id=data['behavior_definition_id'],
                tracked_date=tracked_date,
                completed=data['completed'],
                notes=data.get('notes')
            )
            db.session.add(log)
            action = 'created'

        db.session.commit()

        logger.info(f"{action.capitalize()} behavior log: {behavior.name} on {tracked_date}")
        return success_response(log.to_dict(), status_code=201 if action == 'created' else 200)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating/updating behavior log: {e}", exc_info=True)
        return error_response('Failed to save behavior log', status_code=500)


@behavior_api_bp.route('/logs/today', methods=['GET'])
@require_active_user
def get_today_behavior_checklist():
    """
    Get today's behavior checklist (all active behaviors with completion status).

    Returns:
        {
            "success": true,
            "data": [
                {
                    "behavior_id": 1,
                    "name": "Morning Weigh-In",
                    "icon": "bi-scale",
                    "color": "#1a237e",
                    "target_frequency": 7,
                    "completed": true,
                    "log_id": 123,
                    "notes": "..."
                },
                ...
            ]
        }
    """
    try:
        today = date.today()

        # Get all active behaviors
        behaviors = BehaviorDefinition.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(BehaviorDefinition.display_order, BehaviorDefinition.name).all()

        # Get today's logs
        logs = BehaviorLog.query.filter_by(
            user_id=current_user.id,
            tracked_date=today
        ).all()

        # Create log lookup dict
        logs_by_behavior = {log.behavior_definition_id: log for log in logs}

        # Build checklist
        checklist = []
        for behavior in behaviors:
            log = logs_by_behavior.get(behavior.id)
            checklist.append({
                'behavior_id': behavior.id,
                'name': behavior.name,
                'description': behavior.description,
                'category': behavior.category.value,
                'icon': behavior.icon,
                'color': behavior.color,
                'target_frequency': behavior.target_frequency,
                'completed': log.completed if log else False,
                'log_id': log.id if log else None,
                'notes': log.notes if log else None
            })

        return success_response(checklist)

    except Exception as e:
        logger.error(f"Error fetching today's checklist: {e}", exc_info=True)
        return error_response('Failed to fetch today\'s checklist', status_code=500)


@behavior_api_bp.route('/logs/bulk', methods=['POST'])
@csrf.exempt
@require_active_user
def bulk_update_behavior_logs():
    """
    Bulk update multiple behavior logs for a specific date.

    Request Body:
        {
            "tracked_date": "2024-01-15",
            "logs": [
                {"behavior_definition_id": 1, "completed": true, "notes": "..."},
                {"behavior_definition_id": 2, "completed": false}
            ]
        }
    """
    try:
        # Validate request
        is_valid, data_or_errors = validate_request_data(
            required_fields=['tracked_date', 'logs'],
            optional_fields=[]
        )

        if not is_valid:
            return error_response(**data_or_errors)

        data = data_or_errors

        # Validate date
        is_valid, tracked_date = validate_date_format(data['tracked_date'])
        if not is_valid:
            return error_response(tracked_date)

        logs_data = data['logs']
        if not isinstance(logs_data, list):
            return error_response('logs must be an array')

        # Get existing logs for this date
        existing_logs = BehaviorLog.query.filter_by(
            user_id=current_user.id,
            tracked_date=tracked_date
        ).all()

        existing_logs_by_behavior = {log.behavior_definition_id: log for log in existing_logs}

        # Update or create logs
        updated_count = 0
        created_count = 0

        for log_data in logs_data:
            if 'behavior_definition_id' not in log_data or 'completed' not in log_data:
                continue

            behavior_id = log_data['behavior_definition_id']

            # Verify behavior exists and belongs to user
            behavior = BehaviorDefinition.query.filter_by(
                id=behavior_id,
                user_id=current_user.id
            ).first()

            if not behavior:
                continue

            log = existing_logs_by_behavior.get(behavior_id)

            if log:
                # Update existing
                log.completed = log_data['completed']
                if 'notes' in log_data:
                    log.notes = log_data['notes']
                updated_count += 1
            else:
                # Create new
                log = BehaviorLog(
                    user_id=current_user.id,
                    behavior_definition_id=behavior_id,
                    tracked_date=tracked_date,
                    completed=log_data['completed'],
                    notes=log_data.get('notes')
                )
                db.session.add(log)
                created_count += 1

        db.session.commit()

        logger.info(f"Bulk update: {created_count} created, {updated_count} updated for {tracked_date}")
        return success_response({
            'message': 'Bulk update successful',
            'created': created_count,
            'updated': updated_count
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error bulk updating behavior logs: {e}", exc_info=True)
        return error_response('Failed to bulk update behavior logs', status_code=500)


# ====================================================================================
# Analytics Endpoints
# ====================================================================================

@behavior_api_bp.route('/stats', methods=['GET'])
@require_active_user
def get_behavior_stats():
    """
    Get summary statistics for behavior tracking.

    Query Parameters:
        - days (int): Number of days to analyze (default: 30, max: 365)

    Returns:
        {
            "success": true,
            "data": {
                "period_days": 30,
                "overall_completion_rate": 75.5,
                "week_completion_rate": 82.1,
                "current_streak": 5,
                "best_streak": 14,
                "active_behaviors": 5,
                "behaviors": [
                    {
                        "name": "Morning Weigh-In",
                        "completion_rate": 92.3,
                        "completed_count": 28,
                        "total_count": 30
                    },
                    ...
                ]
            }
        }
    """
    try:
        # Get query parameters
        days = min(request.args.get('days', 30, type=int), 365)

        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        week_start = end_date - timedelta(days=7)

        # Get active behaviors
        behaviors = BehaviorDefinition.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()

        if not behaviors:
            return success_response({
                'period_days': days,
                'overall_completion_rate': 0,
                'week_completion_rate': 0,
                'current_streak': 0,
                'best_streak': 0,
                'active_behaviors': 0,
                'behaviors': []
            })

        # Get logs for period
        logs = BehaviorLog.query.filter(
            BehaviorLog.user_id == current_user.id,
            BehaviorLog.tracked_date >= start_date,
            BehaviorLog.tracked_date <= end_date
        ).all()

        # Calculate overall stats
        total_possible = len(behaviors) * days
        total_completed = sum(1 for log in logs if log.completed)
        overall_completion_rate = (total_completed / total_possible * 100) if total_possible > 0 else 0

        # Calculate week stats
        week_logs = [log for log in logs if log.tracked_date >= week_start]
        week_possible = len(behaviors) * 7
        week_completed = sum(1 for log in week_logs if log.completed)
        week_completion_rate = (week_completed / week_possible * 100) if week_possible > 0 else 0

        # Calculate current streak (consecutive days with all behaviors completed)
        current_streak = _calculate_current_streak(current_user.id, behaviors)
        best_streak = _calculate_best_streak(current_user.id, behaviors, days=days)

        # Per-behavior stats
        behavior_stats = []
        logs_by_behavior = {}
        for log in logs:
            if log.behavior_definition_id not in logs_by_behavior:
                logs_by_behavior[log.behavior_definition_id] = []
            logs_by_behavior[log.behavior_definition_id].append(log)

        for behavior in behaviors:
            behavior_logs = logs_by_behavior.get(behavior.id, [])
            completed_count = sum(1 for log in behavior_logs if log.completed)
            completion_rate = (completed_count / days * 100) if days > 0 else 0

            behavior_stats.append({
                'id': behavior.id,
                'name': behavior.name,
                'category': behavior.category.value,
                'target_frequency': behavior.target_frequency,
                'completion_rate': round(completion_rate, 1),
                'completed_count': completed_count,
                'total_count': days
            })

        # Sort by completion rate descending
        behavior_stats.sort(key=lambda x: x['completion_rate'], reverse=True)

        return success_response({
            'period_days': days,
            'overall_completion_rate': round(overall_completion_rate, 1),
            'week_completion_rate': round(week_completion_rate, 1),
            'current_streak': current_streak,
            'best_streak': best_streak,
            'active_behaviors': len(behaviors),
            'behaviors': behavior_stats
        })

    except Exception as e:
        logger.error(f"Error calculating behavior stats: {e}", exc_info=True)
        return error_response('Failed to calculate statistics', status_code=500)


@behavior_api_bp.route('/trends', methods=['GET'])
@require_active_user
def get_behavior_trends():
    """
    Get trend data for Chart.js visualization.

    Query Parameters:
        - days (int): Number of days (default: 30, max: 365)
        - behavior_ids (comma-separated): Filter specific behaviors

    Returns:
        {
            "success": true,
            "data": {
                "dates": ["2024-01-01", "2024-01-02", ...],
                "behaviors": [
                    {
                        "id": 1,
                        "name": "Morning Weigh-In",
                        "color": "#1a237e",
                        "values": [100, 100, 0, 100, ...]
                    },
                    ...
                ]
            }
        }
    """
    try:
        # Get query parameters
        days = min(request.args.get('days', 30, type=int), 365)
        behavior_ids_str = request.args.get('behavior_ids')

        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Build behavior query
        query = BehaviorDefinition.query.filter_by(
            user_id=current_user.id,
            is_active=True
        )

        if behavior_ids_str:
            behavior_ids = [int(bid) for bid in behavior_ids_str.split(',')]
            query = query.filter(BehaviorDefinition.id.in_(behavior_ids))

        behaviors = query.order_by(BehaviorDefinition.display_order).all()

        if not behaviors:
            return success_response({'dates': [], 'behaviors': []})

        # Get logs for period
        logs = BehaviorLog.query.filter(
            BehaviorLog.user_id == current_user.id,
            BehaviorLog.tracked_date >= start_date,
            BehaviorLog.tracked_date <= end_date
        ).all()

        # Build date range
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.isoformat())
            current_date += timedelta(days=1)

        # Build logs lookup dict
        logs_dict = {}
        for log in logs:
            key = (log.behavior_definition_id, log.tracked_date)
            logs_dict[key] = log

        # Build trend data
        trend_data = []
        for behavior in behaviors:
            values = []
            for date_str in dates:
                log_date = date.fromisoformat(date_str)
                log = logs_dict.get((behavior.id, log_date))
                # Convert to percentage (100 for completed, 0 for not completed)
                values.append(100 if (log and log.completed) else 0)

            trend_data.append({
                'id': behavior.id,
                'name': behavior.name,
                'color': behavior.color or '#1a237e',
                'values': values
            })

        return success_response({
            'dates': dates,
            'behaviors': trend_data
        })

    except Exception as e:
        logger.error(f"Error calculating behavior trends: {e}", exc_info=True)
        return error_response('Failed to calculate trends', status_code=500)


@behavior_api_bp.route('/compliance', methods=['GET'])
@require_active_user
def get_behavior_compliance():
    """
    Get plan compliance analysis (actual vs. target frequency).

    Query Parameters:
        - period (str): 'week' or 'month' (default: 'week')

    Returns:
        {
            "success": true,
            "data": {
                "period": "week",
                "start_date": "2024-01-08",
                "end_date": "2024-01-14",
                "behaviors": [
                    {
                        "name": "Morning Weigh-In",
                        "target_frequency": 7,
                        "actual_frequency": 6,
                        "compliance_rate": 85.7,
                        "status": "on_track",
                        "missed_dates": ["2024-01-12"]
                    },
                    ...
                ]
            }
        }
    """
    try:
        # Get query parameters
        period = request.args.get('period', 'week')

        # Calculate date range
        end_date = date.today()
        if period == 'week':
            start_date = end_date - timedelta(days=6)  # Last 7 days including today
            period_days = 7
        else:  # month
            start_date = end_date - timedelta(days=29)  # Last 30 days including today
            period_days = 30

        # Get active behaviors with target frequency
        behaviors = BehaviorDefinition.query.filter(
            BehaviorDefinition.user_id == current_user.id,
            BehaviorDefinition.is_active == True,
            BehaviorDefinition.target_frequency.isnot(None)
        ).all()

        # Get logs for period
        logs = BehaviorLog.query.filter(
            BehaviorLog.user_id == current_user.id,
            BehaviorLog.tracked_date >= start_date,
            BehaviorLog.tracked_date <= end_date
        ).all()

        # Build logs lookup
        logs_by_behavior = {}
        for log in logs:
            if log.behavior_definition_id not in logs_by_behavior:
                logs_by_behavior[log.behavior_definition_id] = []
            logs_by_behavior[log.behavior_definition_id].append(log)

        # Calculate compliance for each behavior
        compliance_data = []
        for behavior in behaviors:
            behavior_logs = logs_by_behavior.get(behavior.id, [])
            actual_frequency = sum(1 for log in behavior_logs if log.completed)

            # Scale target frequency to period
            if period == 'month':
                target = int(behavior.target_frequency * 4.3)  # Approximate month = 4.3 weeks
            else:
                target = behavior.target_frequency

            compliance_rate = (actual_frequency / target * 100) if target > 0 else 0

            # Determine status
            if compliance_rate >= 90:
                status = 'excellent'
            elif compliance_rate >= 70:
                status = 'on_track'
            elif compliance_rate >= 50:
                status = 'needs_improvement'
            else:
                status = 'off_track'

            # Find missed dates (dates where behavior was not completed)
            completed_dates = set(log.tracked_date for log in behavior_logs if log.completed)
            all_dates = set(start_date + timedelta(days=i) for i in range(period_days))
            missed_dates = sorted([d.isoformat() for d in (all_dates - completed_dates)])

            compliance_data.append({
                'id': behavior.id,
                'name': behavior.name,
                'category': behavior.category.value,
                'target_frequency': target,
                'actual_frequency': actual_frequency,
                'compliance_rate': round(compliance_rate, 1),
                'status': status,
                'missed_dates': missed_dates[:5]  # Limit to 5 most recent
            })

        # Sort by compliance rate descending
        compliance_data.sort(key=lambda x: x['compliance_rate'], reverse=True)

        return success_response({
            'period': period,
            'period_days': period_days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'behaviors': compliance_data
        })

    except Exception as e:
        logger.error(f"Error calculating compliance: {e}", exc_info=True)
        return error_response('Failed to calculate compliance', status_code=500)


# ====================================================================================
# Helper Functions
# ====================================================================================

def _calculate_current_streak(user_id: int, behaviors: list) -> int:
    """
    Calculate current streak (consecutive days with all behaviors completed).

    Args:
        user_id: User ID
        behaviors: List of active behavior definitions

    Returns:
        Current streak in days
    """
    if not behaviors:
        return 0

    streak = 0
    current_date = date.today()

    while True:
        # Get logs for current_date
        logs = BehaviorLog.query.filter_by(
            user_id=user_id,
            tracked_date=current_date
        ).all()

        # Check if all behaviors were completed
        completed_behavior_ids = set(log.behavior_definition_id for log in logs if log.completed)
        all_behavior_ids = set(b.id for b in behaviors)

        if completed_behavior_ids == all_behavior_ids:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

        # Safety limit
        if streak >= 365:
            break

    return streak


def _calculate_best_streak(user_id: int, behaviors: list, days: int = 365) -> int:
    """
    Calculate best streak in the given period.

    Args:
        user_id: User ID
        behaviors: List of active behavior definitions
        days: Number of days to look back

    Returns:
        Best streak in days
    """
    if not behaviors:
        return 0

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get all logs for period
    logs = BehaviorLog.query.filter(
        BehaviorLog.user_id == user_id,
        BehaviorLog.tracked_date >= start_date,
        BehaviorLog.tracked_date <= end_date
    ).all()

    # Build dict of completed behaviors per date
    completed_by_date = {}
    for log in logs:
        if log.completed:
            if log.tracked_date not in completed_by_date:
                completed_by_date[log.tracked_date] = set()
            completed_by_date[log.tracked_date].add(log.behavior_definition_id)

    # Scan through dates to find best streak
    all_behavior_ids = set(b.id for b in behaviors)
    current_streak = 0
    best_streak = 0
    current_date = start_date

    while current_date <= end_date:
        completed_ids = completed_by_date.get(current_date, set())

        if completed_ids == all_behavior_ids:
            current_streak += 1
            best_streak = max(best_streak, current_streak)
        else:
            current_streak = 0

        current_date += timedelta(days=1)

    return best_streak
