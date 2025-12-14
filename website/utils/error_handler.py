"""
Error handling and logging utilities
"""

import logging
import traceback
from functools import wraps
from flask import jsonify, request
from datetime import datetime
import os


class AppLogger:
    """Centralized logging configuration"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.logger = logging.getLogger('app')
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(
            os.path.join(logs_dir, 'app.log')
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """Get the logger instance"""
        return self.logger


class APIError(Exception):
    """Base API error"""

    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert error to dictionary"""
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class NotFoundError(APIError):
    """404 Not Found error"""

    def __init__(self, message, payload=None):
        super().__init__(message, 404, payload)


class ValidationError(APIError):
    """400 Validation error"""

    def __init__(self, message, payload=None):
        super().__init__(message, 400, payload)


class ServerError(APIError):
    """500 Server error"""

    def __init__(self, message, payload=None):
        super().__init__(message, 500, payload)


def handle_api_errors(f):
    """Decorator for handling API errors"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger = AppLogger().get_logger()
            logger.warning(f"API Error: {e.message}")
            return jsonify(e.to_dict()), e.status_code
        except FileNotFoundError as e:
            logger = AppLogger().get_logger()
            logger.warning(f"File not found: {str(e)}")
            error = NotFoundError(str(e))
            return jsonify(error.to_dict()), error.status_code
        except ValueError as e:
            logger = AppLogger().get_logger()
            logger.warning(f"Validation error: {str(e)}")
            error = ValidationError(str(e))
            return jsonify(error.to_dict()), error.status_code
        except Exception as e:
            logger = AppLogger().get_logger()
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            error = ServerError("An unexpected error occurred")
            return jsonify(error.to_dict()), 500

    return decorated_function


def log_request(f):
    """Decorator for logging requests"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger = AppLogger().get_logger()
        logger.info(
            f"{request.method} {request.path} - "
            f"IP: {request.remote_addr} - "
            f"User-Agent: {request.user_agent}"
        )
        return f(*args, **kwargs)

    return decorated_function
