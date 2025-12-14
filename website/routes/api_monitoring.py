"""
Application monitoring and health check endpoints
"""

from flask import jsonify
from . import api_bp
from ..utils.error_handler import handle_api_errors, log_request
from ..utils.performance import get_performance_monitor
from ..utils.cache import get_cache, get_cache_stats
import psutil
import os


@api_bp.route('/health', methods=['GET'])
@handle_api_errors
@log_request
def health_check():
    """Health check endpoint"""
    try:
        from flask import current_app
        memory = psutil.Process(os.getpid()).memory_info()
        return jsonify({
            'status': 'healthy',
            'memory_mb': memory.rss / 1024 / 1024,
            'cpu_percent': psutil.cpu_percent(interval=0.1)
        })
    except (OSError, psutil.Error) as e:
        from flask import current_app
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Unable to retrieve system metrics'
        }), 503


@api_bp.route('/metrics', methods=['GET'])
@handle_api_errors
@log_request
def get_metrics():
    """Get application metrics"""
    monitor = get_performance_monitor()
    cache = get_cache()
    cache_stats = get_cache_stats()

    return jsonify({
        'performance': monitor.get_system_metrics(),
        'cache': {
            'stats': cache.get_stats(),
            'cache_stats': cache_stats.get_stats()
        },
        'system': {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent
        }
    })


@api_bp.route('/metrics/endpoints', methods=['GET'])
@handle_api_errors
@log_request
def get_endpoint_metrics():
    """Get metrics for all endpoints"""
    monitor = get_performance_monitor()

    return jsonify({
        'slowest': monitor.get_slowest_endpoints(),
        'most_called': monitor.get_most_called_endpoints(),
        'summary': monitor.get_system_metrics()
    })


@api_bp.route('/metrics/cache', methods=['GET'])
@handle_api_errors
@log_request
def get_cache_metrics():
    """Get cache metrics"""
    cache = get_cache()
    cache_stats = get_cache_stats()

    return jsonify({
        'cache': cache.get_stats(),
        'stats': cache_stats.get_stats()
    })


@api_bp.route('/metrics/full', methods=['GET'])
@handle_api_errors
@log_request
def get_full_metrics():
    """Get complete application metrics"""
    monitor = get_performance_monitor()
    cache = get_cache()
    cache_stats = get_cache_stats()

    return jsonify({
        'performance': monitor.get_full_report(),
        'cache': {
            'data': cache.get_stats(),
            'stats': cache_stats.get_stats()
        },
        'system': {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'virtual_memory': dict(psutil.virtual_memory()._asdict()),
            'disk_usage': dict(psutil.disk_usage('/')._asdict())
        }
    })
