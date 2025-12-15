"""
Flask Application Factory

This module provides the application factory pattern for creating and configuring
the Flask application with all necessary extensions, blueprints, and configurations.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_caching import Cache

# Initialize Flask extensions (but don't bind to app yet)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
cache = Cache()


def create_app(config_name=None):
    """
    Application Factory Pattern

    Creates and configures the Flask application with all extensions and blueprints.

    Args:
        config_name: Configuration name ('development', 'production', 'testing')
                    If None, uses FLASK_ENV environment variable

    Returns:
        Configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    from .config import get_config
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Initialize extensions with app
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Configure logging
    configure_logging(app)

    # Register error handlers
    register_error_handlers(app)

    # Add security headers
    add_security_headers(app)

    # Create necessary directories
    ensure_directories_exist(app)

    return app


def initialize_extensions(app):
    """
    Initialize Flask extensions with the application

    Args:
        app: Flask application instance
    """
    # Database
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models for Flask-Migrate to detect them
    with app.app_context():
        from . import models

    # Authentication
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login"""
        from .models.user import User  # Import here to avoid circular imports
        return User.query.get(int(user_id))

    # CSRF Protection
    csrf.init_app(app)

    # Rate Limiting
    if app.config.get('RATELIMIT_ENABLED', True):
        limiter.init_app(app)

    # Caching
    cache.init_app(app)

    # CORS (if needed for API access)
    # Uncomment if you need cross-origin requests
    # CORS(app, resources={r"/api/*": {"origins": "*"}})


def register_blueprints(app):
    """
    Register Flask blueprints with the application

    Args:
        app: Flask application instance
    """
    # Import blueprints from routes/__init__.py
    from .routes import main_bp, blog_bp, api_bp, health_bp, insights_bp

    # Import route modules to register their decorated routes with blueprints
    from .routes import main, blog, health
    from .routes import api_projects, api_blog, api_misc, api_monitoring

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(insights_bp)

    # Authentication blueprint
    from .auth import auth_bp
    app.register_blueprint(auth_bp)


def configure_logging(app):
    """
    Configure application logging

    Args:
        app: Flask application instance
    """
    # Don't configure logging in testing mode
    if app.config.get('TESTING'):
        return

    # Set log level
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    app.logger.setLevel(log_level)

    # Create logs directory if it doesn't exist
    log_file = app.config.get('LOG_FILE')
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=app.config.get('LOG_MAX_BYTES', 10485760),  # 10MB
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
        )
        file_handler.setLevel(log_level)

        # Log format
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)

        app.logger.addHandler(file_handler)

    # Console handler for development
    if app.config.get('DEBUG'):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        app.logger.addHandler(console_handler)

    app.logger.info(f'Application started in {app.config.get("FLASK_ENV", "unknown")} mode')


def register_error_handlers(app):
    """
    Register error handlers for common HTTP errors

    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        return jsonify({
            'error': 'Bad Request',
            'message': str(error)
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for this resource'
        }), 405

    @app.errorhandler(429)
    def ratelimit_handler(error):
        """Handle 429 Too Many Requests errors"""
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded. Please try again later.'
        }), 429

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error"""
        app.logger.error(f'Internal Server Error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all other exceptions"""
        app.logger.exception(f'Unhandled exception: {error}')

        # Return JSON response for API requests
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


def add_security_headers(app):
    """
    Add security headers to all responses

    Args:
        app: Flask application instance
    """

    @app.after_request
    def set_security_headers(response):
        """Set security headers on all responses"""

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS protection (legacy browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # HTTPS enforcement (production only)
        if not app.config.get('DEBUG'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy (adjust as needed)
        # Uncomment and customize based on your needs
        # response.headers['Content-Security-Policy'] = "default-src 'self'"

        return response


def ensure_directories_exist(app):
    """
    Create necessary directories if they don't exist

    Args:
        app: Flask application instance
    """
    directories = [
        app.config.get('BLOG_DIR'),
        os.path.join(app.instance_path, 'uploads'),
        os.path.dirname(app.config.get('LOG_FILE', '')),
    ]

    for directory in directories:
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
                app.logger.info(f'Created directory: {directory}')
            except OSError as e:
                app.logger.warning(f'Could not create directory {directory}: {e}')
