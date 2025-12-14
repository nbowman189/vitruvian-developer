"""
Flask application factory and configuration
Main entry point for the application
"""

import os
from flask import Flask
from config import config
from utils.error_handler import AppLogger


def create_app(config_name=None):
    """
    Application factory function

    Args:
        config_name: Configuration environment ('development', 'production', 'testing')

    Returns:
        Flask application instance
    """
    # Determine configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    app_config = config.get(config_name, config['default'])
    app.config.from_object(app_config)

    # Initialize logger
    logger = AppLogger()
    app.logger = logger.get_logger()

    # Register blueprints
    register_blueprints(app)

    # Add performance middleware
    add_performance_middleware(app)

    # Add security headers
    add_security_headers(app)

    # Register error handlers
    register_error_handlers(app)

    # Log application startup
    app.logger.info(f"Application created with config: {config_name}")

    return app


def register_blueprints(app):
    """Register all application blueprints"""
    from routes.main import main_bp
    from routes.blog import blog_bp
    from routes.health import health_bp
    from routes import api_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)

    app.logger.info("Blueprints registered successfully")


def add_performance_middleware(app):
    """Add performance monitoring middleware"""
    import time
    from utils.performance import get_performance_monitor

    @app.before_request
    def before_request():
        from flask import request, g
        g.start_time = time.time()
        g.request_path = request.path

    @app.after_request
    def after_request(response):
        from flask import g
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            monitor = get_performance_monitor()
            endpoint = g.request_path
            monitor.record_request(endpoint, duration)

        return response


def add_security_headers(app):
    """Add HTTP security headers to all responses"""
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Enable browser XSS protections
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # HSTS header for HTTPS in production
        if os.getenv('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


def register_error_handlers(app):
    """Register application error handlers"""
    from flask import jsonify
    from utils.error_handler import APIError

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({'error': 'Not found', 'status_code': 404}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error', 'status_code': 500}), 500

    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle API errors"""
        return jsonify(error.to_dict()), error.status_code

    app.logger.info("Error handlers registered successfully")


# Create application instance
app = create_app()

if __name__ == '__main__':
    # Get configuration
    debug = app.config.get('DEBUG', False)
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))

    app.logger.info(f"Starting server at {host}:{port}")
    app.run(host=host, port=port, debug=debug)
