"""
Debug API Endpoint
==================

Temporary debugging endpoint to diagnose GeminiService issues.
"""

import logging
import os
import traceback
from flask import Blueprint, current_app
from .. import csrf

# Create blueprint
debug_api_bp = Blueprint('debug_api', __name__, url_prefix='/debug')

# Configure logger
logger = logging.getLogger(__name__)


@debug_api_bp.route('/gemini-config', methods=['GET'])
@csrf.exempt
def check_gemini_config():
    """Debug endpoint to check Gemini configuration."""
    debug_info = {}

    try:
        # Check environment variable
        api_key = os.environ.get('GEMINI_API_KEY')
        debug_info['env_api_key_present'] = bool(api_key)
        debug_info['env_api_key_length'] = len(api_key) if api_key else 0

        # Check Flask config
        debug_info['config_api_key_present'] = bool(current_app.config.get('GEMINI_API_KEY'))

        # Check model fallback chain
        model_chain = current_app.config.get('GEMINI_MODEL_FALLBACK_CHAIN')
        debug_info['model_chain_type'] = str(type(model_chain))
        debug_info['model_chain_value'] = str(model_chain)

        # Check generation config
        gen_config = current_app.config.get('GEMINI_GENERATION_CONFIG')
        debug_info['gen_config_type'] = str(type(gen_config))
        debug_info['gen_config_value'] = str(gen_config)

        # Try to import quota_manager
        try:
            from ..services.quota_manager import quota_manager
            debug_info['quota_manager_imported'] = True
            debug_info['quota_manager_type'] = str(type(quota_manager))
        except Exception as e:
            debug_info['quota_manager_imported'] = False
            debug_info['quota_manager_error'] = str(e)

        # Try to instantiate GeminiService
        try:
            from ..services.gemini_service import GeminiService
            debug_info['gemini_service_imported'] = True

            # Try instantiation
            try:
                service = GeminiService()
                debug_info['gemini_service_instantiated'] = True
                debug_info['gemini_service_model_count'] = len(service.model_names)
                debug_info['gemini_service_models'] = service.model_names
                debug_info['gemini_service_has_quota_manager'] = service.quota_manager is not None
            except Exception as e:
                debug_info['gemini_service_instantiated'] = False
                debug_info['gemini_service_init_error'] = str(e)
                debug_info['gemini_service_init_traceback'] = traceback.format_exc()

        except Exception as e:
            debug_info['gemini_service_imported'] = False
            debug_info['gemini_service_import_error'] = str(e)
            debug_info['gemini_service_import_traceback'] = traceback.format_exc()

        return {
            'success': True,
            'debug_info': debug_info
        }, 200

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, 500


@debug_api_bp.route('/gemini-chat-test', methods=['GET'])
@csrf.exempt
def test_gemini_chat():
    """Debug endpoint to test actual chat() call."""
    debug_info = {}

    try:
        from ..services.gemini_service import GeminiService

        # Try to instantiate
        try:
            service = GeminiService()
            debug_info['instantiation_success'] = True
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to instantiate GeminiService',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, 500

        # Try to call chat() with a simple message
        try:
            response, function_call = service.chat(
                user_message="Hello, this is a test message.",
                conversation_history=[],
                function_declarations=None,
                max_context_messages=10
            )

            debug_info['chat_success'] = True
            debug_info['response_length'] = len(response) if response else 0
            debug_info['response_preview'] = response[:100] if response else None
            debug_info['function_call'] = function_call

        except Exception as e:
            debug_info['chat_success'] = False
            debug_info['chat_error_type'] = type(e).__name__
            debug_info['chat_error_message'] = str(e)
            debug_info['chat_traceback'] = traceback.format_exc()

        return {
            'success': True,
            'debug_info': debug_info
        }, 200

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, 500


@debug_api_bp.route('/gemini-chat-with-functions', methods=['GET'])
@csrf.exempt
def test_gemini_chat_with_functions():
    """Debug endpoint to test chat() with function declarations."""
    debug_info = {}

    try:
        from ..services.gemini_service import GeminiService
        from ..utils.ai_coach_tools import get_all_function_declarations

        # Try to instantiate
        try:
            service = GeminiService()
            debug_info['instantiation_success'] = True
        except Exception as e:
            return {
                'success': False,
                'error': 'Failed to instantiate GeminiService',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, 500

        # Get function declarations
        try:
            function_decls = get_all_function_declarations()
            debug_info['function_declarations_count'] = len(function_decls) if function_decls else 0
            debug_info['function_declarations_loaded'] = True
        except Exception as e:
            debug_info['function_declarations_loaded'] = False
            debug_info['function_declarations_error'] = str(e)
            debug_info['function_declarations_traceback'] = traceback.format_exc()
            function_decls = None

        # Try to call chat() with function declarations
        try:
            response, function_call = service.chat(
                user_message="I want to log my weight today at 175 lbs",
                conversation_history=[],
                function_declarations=function_decls,
                max_context_messages=10
            )

            debug_info['chat_success'] = True
            debug_info['response_length'] = len(response) if response else 0
            debug_info['response_preview'] = response[:100] if response else None
            debug_info['function_call'] = function_call

        except Exception as e:
            debug_info['chat_success'] = False
            debug_info['chat_error_type'] = type(e).__name__
            debug_info['chat_error_message'] = str(e)
            debug_info['chat_traceback'] = traceback.format_exc()

        return {
            'success': True,
            'debug_info': debug_info
        }, 200

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, 500


@debug_api_bp.route('/check-health-records', methods=['GET'])
@csrf.exempt
def check_health_records():
    """Debug endpoint to check recent health metric records."""
    from flask_login import current_user
    from ..models.health import HealthMetric
    from datetime import datetime, timedelta

    debug_info = {
        'user_authenticated': current_user.is_authenticated
    }

    if not current_user.is_authenticated:
        return {
            'success': False,
            'debug_info': debug_info,
            'error': 'User not authenticated'
        }, 401

    try:
        debug_info['user_id'] = current_user.id
        debug_info['username'] = current_user.username

        # Get all health metrics for user
        all_metrics = HealthMetric.query.filter_by(user_id=current_user.id).all()
        debug_info['total_health_metrics'] = len(all_metrics)

        # Get recent metrics (last 30 days)
        thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
        recent_metrics = HealthMetric.query.filter(
            HealthMetric.user_id == current_user.id,
            HealthMetric.recorded_date >= thirty_days_ago
        ).order_by(HealthMetric.recorded_date.desc()).all()

        debug_info['recent_health_metrics_count'] = len(recent_metrics)
        debug_info['recent_metrics'] = [
            {
                'id': m.id,
                'recorded_date': m.recorded_date.isoformat(),
                'weight_lbs': m.weight_lbs,
                'body_fat_percentage': m.body_fat_percentage,
                'notes': m.notes
            }
            for m in recent_metrics[:10]  # Show last 10
        ]

        # Get latest metric
        latest = HealthMetric.query.filter_by(user_id=current_user.id).order_by(
            HealthMetric.recorded_date.desc()
        ).first()

        if latest:
            debug_info['latest_metric'] = {
                'id': latest.id,
                'recorded_date': latest.recorded_date.isoformat(),
                'weight_lbs': latest.weight_lbs,
                'body_fat_percentage': latest.body_fat_percentage,
                'created_at': latest.created_at.isoformat() if latest.created_at else None
            }
        else:
            debug_info['latest_metric'] = None

        return {
            'success': True,
            'debug_info': debug_info
        }, 200

    except Exception as e:
        return {
            'success': False,
            'debug_info': debug_info,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, 500


@debug_api_bp.route('/test-query-functions', methods=['GET'])
@csrf.exempt
def test_query_functions():
    """Debug endpoint to test all query handler functions."""
    from flask_login import current_user

    debug_info = {
        'user_authenticated': current_user.is_authenticated
    }

    if not current_user.is_authenticated:
        return {
            'success': False,
            'debug_info': debug_info,
            'error': 'User not authenticated'
        }, 401

    debug_info['user_id'] = current_user.id

    # Import query handlers
    from ..api.ai_coach import (
        _query_health_metrics,
        _query_workout_history,
        _query_nutrition_summary,
        _query_user_goals,
        _query_coaching_history,
        _query_progress_summary,
        _query_behavior_tracking,
        _query_behavior_compliance
    )

    # Test each query function
    test_results = {}

    # Test health metrics
    try:
        data, summary = _query_health_metrics(current_user.id, {'days': 7})
        test_results['health_metrics'] = {
            'success': True,
            'summary': summary,
            'data_keys': list(data.keys()) if data else []
        }
    except Exception as e:
        test_results['health_metrics'] = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

    # Test workout history
    try:
        data, summary = _query_workout_history(current_user.id, {'days': 7})
        test_results['workout_history'] = {
            'success': True,
            'summary': summary,
            'data_keys': list(data.keys()) if data else []
        }
    except Exception as e:
        test_results['workout_history'] = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

    # Test nutrition summary
    try:
        data, summary = _query_nutrition_summary(current_user.id, {'days': 7})
        test_results['nutrition_summary'] = {
            'success': True,
            'summary': summary,
            'data_keys': list(data.keys()) if data else []
        }
    except Exception as e:
        test_results['nutrition_summary'] = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

    # Test user goals
    try:
        data, summary = _query_user_goals(current_user.id, {'status': 'active'})
        test_results['user_goals'] = {
            'success': True,
            'summary': summary,
            'data_keys': list(data.keys()) if data else []
        }
    except Exception as e:
        test_results['user_goals'] = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

    # Test coaching history
    try:
        data, summary = _query_coaching_history(current_user.id, {'limit': 5})
        test_results['coaching_history'] = {
            'success': True,
            'summary': summary,
            'data_keys': list(data.keys()) if data else []
        }
    except Exception as e:
        test_results['coaching_history'] = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

    # Test behavior tracking
    try:
        data, summary = _query_behavior_tracking(current_user.id, {'days': 7})
        test_results['behavior_tracking'] = {
            'success': True,
            'summary': summary,
            'data_keys': list(data.keys()) if data else []
        }
    except Exception as e:
        test_results['behavior_tracking'] = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

    # Test behavior compliance
    try:
        data, summary = _query_behavior_compliance(current_user.id, {'period': 'week'})
        test_results['behavior_compliance'] = {
            'success': True,
            'summary': summary,
            'data_keys': list(data.keys()) if data else []
        }
    except Exception as e:
        test_results['behavior_compliance'] = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

    # Test progress summary (calls all others)
    try:
        data, summary = _query_progress_summary(current_user.id, {'period_days': 30})
        test_results['progress_summary'] = {
            'success': True,
            'summary': summary,
            'data_keys': list(data.keys()) if data else []
        }
    except Exception as e:
        test_results['progress_summary'] = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

    debug_info['test_results'] = test_results

    return {
        'success': True,
        'debug_info': debug_info
    }, 200
