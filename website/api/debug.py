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
