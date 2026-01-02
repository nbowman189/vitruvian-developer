"""
API Blueprint Package
=====================

RESTful API layer for the multi-user health & fitness tracking application.

This package provides a complete REST API with endpoints for:
- Health metrics tracking
- Workout and exercise logging
- Coaching sessions and goals
- Nutrition tracking
- User profile management

All endpoints require authentication and enforce user data isolation.
Rate limiting is applied to prevent abuse.
"""

from flask import Blueprint, jsonify, request
from functools import wraps
from flask_login import current_user
import logging

# Create main API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Configure logger
logger = logging.getLogger(__name__)


# ====================
# Response Helpers
# ====================

def success_response(data=None, message=None, status_code=200):
    """
    Create a standardized success response.

    Args:
        data: Response data (dict, list, or None)
        message: Optional success message
        status_code: HTTP status code (default: 200)

    Returns:
        Flask JSON response with standard format
    """
    response = {
        'success': True,
        'data': data or {},
        'message': message or 'Success'
    }
    return jsonify(response), status_code


def error_response(message, errors=None, status_code=400):
    """
    Create a standardized error response.

    Args:
        message: Error message
        errors: Optional detailed errors (list or dict)
        status_code: HTTP status code (default: 400)

    Returns:
        Flask JSON response with standard format
    """
    response = {
        'success': False,
        'data': {},
        'message': message,
        'errors': errors or []
    }
    return jsonify(response), status_code


def paginated_response(items, page, per_page, total, message=None):
    """
    Create a standardized paginated response.

    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Optional message

    Returns:
        Flask JSON response with pagination metadata
    """
    import math

    response = {
        'success': True,
        'data': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': math.ceil(total / per_page) if per_page > 0 else 0
        },
        'message': message or 'Success'
    }
    return jsonify(response), 200


# ====================
# Validation Helpers
# ====================

def validate_request_data(required_fields=None, optional_fields=None):
    """
    Validate request JSON data.

    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names

    Returns:
        Tuple of (is_valid, data_or_errors)
    """
    if not request.is_json:
        return False, {'message': 'Request must be JSON', 'errors': ['Content-Type must be application/json']}

    data = request.get_json()

    if not data:
        return False, {'message': 'Request body is empty', 'errors': ['No data provided']}

    # Check required fields
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, {
                'message': 'Missing required fields',
                'errors': [f'Missing field: {field}' for field in missing_fields]
            }

    # Extract only known fields
    all_fields = (required_fields or []) + (optional_fields or [])
    if all_fields:
        filtered_data = {k: v for k, v in data.items() if k in all_fields}
    else:
        filtered_data = data

    return True, filtered_data


def validate_date_format(date_string):
    """
    Validate date string is in ISO format (YYYY-MM-DD).

    Args:
        date_string: Date string to validate

    Returns:
        Tuple of (is_valid, date_object_or_error_message)
    """
    from datetime import datetime

    try:
        date_obj = datetime.fromisoformat(date_string).date()
        return True, date_obj
    except (ValueError, AttributeError, TypeError):
        return False, f"Invalid date format: {date_string}. Expected ISO format (YYYY-MM-DD)"


def validate_pagination_params():
    """
    Validate and extract pagination parameters from request.

    Returns:
        Tuple of (page, per_page) with validated values
    """
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except (ValueError, TypeError):
        per_page = 20

    return page, per_page


def validate_date_range_params():
    """
    Validate and extract date range parameters from request.

    Returns:
        Tuple of (is_valid, start_date, end_date, error_message)
    """
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = None
    end_date = None

    if start_date_str:
        is_valid, result = validate_date_format(start_date_str)
        if not is_valid:
            return False, None, None, result
        start_date = result

    if end_date_str:
        is_valid, result = validate_date_format(end_date_str)
        if not is_valid:
            return False, None, None, result
        end_date = result

    # Validate start_date <= end_date
    if start_date and end_date and start_date > end_date:
        return False, None, None, "start_date must be before or equal to end_date"

    return True, start_date, end_date, None


# ====================
# Security Helpers
# ====================

def require_authentication(f):
    """
    Decorator to require user authentication.

    Returns 401 if user is not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return error_response('Authentication required', status_code=401)
        return f(*args, **kwargs)
    return decorated_function


def require_active_user(f):
    """
    Decorator to require active user account.

    Returns 403 if user account is not active.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return error_response('Authentication required', status_code=401)

        if not current_user.is_active:
            return error_response('Account is not active', status_code=403)

        return f(*args, **kwargs)
    return decorated_function


def require_role(role):
    """
    Decorator to require specific user role.

    Args:
        role: Required UserRole enum value

    Returns 403 if user doesn't have required role.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return error_response('Authentication required', status_code=401)

            if current_user.role != role:
                return error_response('Insufficient permissions', status_code=403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ====================
# Error Handlers
# ====================

@api_bp.errorhandler(400)
def handle_bad_request(error):
    """Handle 400 Bad Request errors"""
    logger.warning(f'Bad request: {error}')
    return error_response('Bad request', errors=[str(error)], status_code=400)


@api_bp.errorhandler(401)
def handle_unauthorized(error):
    """Handle 401 Unauthorized errors"""
    logger.warning(f'Unauthorized access attempt: {error}')
    return error_response('Authentication required', status_code=401)


@api_bp.errorhandler(403)
def handle_forbidden(error):
    """Handle 403 Forbidden errors"""
    logger.warning(f'Forbidden access attempt: {error}')
    return error_response('Access forbidden', status_code=403)


@api_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 Not Found errors"""
    logger.info(f'Resource not found: {error}')
    return error_response('Resource not found', status_code=404)


@api_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 Internal Server Error"""
    logger.error(f'Internal server error: {error}', exc_info=True)
    return error_response('Internal server error', status_code=500)


# Import API route modules (import at end to avoid circular imports)
from . import health
from . import workout
from . import coaching
from . import nutrition
from . import user
from . import ai_coach
from . import activity
from . import behavior

# Register sub-blueprints
api_bp.register_blueprint(health.health_api_bp)
api_bp.register_blueprint(workout.workout_api_bp)
api_bp.register_blueprint(coaching.coaching_api_bp)
api_bp.register_blueprint(nutrition.nutrition_api_bp)
api_bp.register_blueprint(user.user_api_bp)
api_bp.register_blueprint(ai_coach.ai_coach_api_bp)
api_bp.register_blueprint(activity.activity_api_bp)
api_bp.register_blueprint(behavior.behavior_api_bp)
