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
