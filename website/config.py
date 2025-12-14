"""
Application Configuration
Centralized configuration for the Flask application with security, database, and multi-environment support
"""

import os
from datetime import timedelta

# Base configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)


class BaseConfig:
    """Base configuration - shared settings across all environments"""

    # ==================== Flask Core Settings ====================
    TEMPLATES_AUTO_RELOAD = True
    JSON_SORT_KEYS = False

    # ==================== Security Settings ====================
    # SECRET_KEY must be set via environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set. Generate with: python scripts/generate_secret_key.py")

    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Session expires after 24 hours
    SESSION_COOKIE_NAME = 'primary_assistant_session'

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens don't expire (use session expiry instead)

    # ==================== Database Settings ====================
    # PostgreSQL database configuration
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'portfolio_user')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'portfolio_db')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')

    if not POSTGRES_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD environment variable must be set")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable modification tracking for performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Enable connection health checks
        'pool_recycle': 300,  # Recycle connections after 5 minutes
    }

    # ==================== Authentication Settings ====================
    # Bcrypt complexity (higher = more secure but slower)
    BCRYPT_LOG_ROUNDS = 12  # Good balance of security and performance

    # Login management
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # ==================== File Upload Settings ====================
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 16)) * 1024 * 1024  # Default 16MB
    ALLOWED_UPLOAD_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'md', 'txt'}

    # ==================== Rate Limiting ====================
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day, 50 per hour')
    RATELIMIT_HEADERS_ENABLED = True

    # ==================== Application Settings ====================
    APP_NAME = os.environ.get('APP_NAME', 'Primary Assistant Portfolio')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'nbowman189@gmail.com')

    # File paths
    BLOG_DIR = os.path.join(BASE_DIR, 'blog')
    PROJECT_DIRS = ['AI_Development', 'Health_and_Fitness']

    # Health & Fitness file ordering
    HEALTH_FITNESS_FILE_ORDER = [
        'fitness-roadmap.md',
        'Full-Meal-Plan.md',
        'Shopping-List-and-Estimate.md',
        'check-in-log.md',
        'progress-check-in-log.md'
    ]

    # Featured projects configuration
    FEATURED_PROJECTS = [
        {
            'id': 'fitness-tracker',
            'title': 'Comprehensive Fitness Tracker',
            'description': 'A complete health and fitness management system combining meal planning, workout tracking, and progress visualization. Includes automated HealthKit data integration, detailed metrics logging, and interactive progress graphs.',
            'disciplines': ['fitness', 'code', 'meta'],
            'technologies': ['Python', 'Flask', 'Markdown', 'Chart.js', 'Apple HealthKit'],
            'project': 'Health_and_Fitness',
            'links': {
                'demo': '/#/project/Health_and_Fitness',
                'github': 'https://github.com/nbowman189'
            }
        },
        {
            'id': 'meal-planning',
            'title': 'Strategic Meal Planning System',
            'description': 'Develop personalized nutrition strategies with detailed meal plans and shopping lists. Helps maintain consistency in achieving fitness goals through organized meal planning.',
            'disciplines': ['fitness', 'meta'],
            'technologies': ['Markdown', 'Python', 'Data Management'],
            'project': 'Health_and_Fitness',
            'links': {
                'demo': '/#/project/Health_and_Fitness/file/Full-Meal-Plan.md',
                'github': 'https://github.com/nbowman189'
            }
        },
        {
            'id': 'ai-development',
            'title': 'AI Development Projects',
            'description': 'Exploration and development of artificial intelligence concepts, applications, and research. Building knowledge in machine learning, neural networks, and AI systems.',
            'disciplines': ['ai', 'code'],
            'technologies': ['Python', 'Machine Learning', 'AI Research'],
            'project': 'AI_Development',
            'links': {
                'demo': '/#/project/AI_Development',
                'github': 'https://github.com/nbowman189'
            }
        }
    ]

    # Contact information
    CONTACT_INFO = {
        'email': 'nbowman189@gmail.com',
        'linkedin': 'https://www.linkedin.com/in/nathan-bowman-b27484103/',
        'github': 'https://github.com/nbowman189'
    }

    # ==================== Caching ====================
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # ==================== Logging ====================
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', os.path.join(BASE_DIR, 'logs', 'app.log'))
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

    # ==================== Email Configuration (Future) ====================
    # Commented out for future implementation
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', ADMIN_EMAIL)


class DevelopmentConfig(BaseConfig):
    """Development configuration - local development settings"""
    DEBUG = True
    TESTING = False

    # Development-specific security (less strict for local dev)
    SESSION_COOKIE_SECURE = False  # Allow HTTP for local development
    REMEMBER_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True  # Keep CSRF protection even in dev

    # Enhanced logging for development
    LOG_LEVEL = 'DEBUG'

    # Disable rate limiting in development for easier testing
    RATELIMIT_ENABLED = False

    # Development database can use environment variable or fallback to default
    # This allows developers to use PostgreSQL or SQLite for local testing
    if os.environ.get('USE_SQLITE_DEV', 'false').lower() == 'true':
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'dev.db')}"


class ProductionConfig(BaseConfig):
    """Production configuration - secure production settings"""
    DEBUG = False
    TESTING = False

    # Production security settings
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'

    # Stricter session configuration
    SESSION_COOKIE_SAMESITE = 'Strict'
    REMEMBER_COOKIE_SAMESITE = 'Strict'

    # Production caching (consider Redis for multi-server setups)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache')
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL')  # Optional Redis caching

    if CACHE_TYPE == 'RedisCache' and CACHE_REDIS_URL:
        CACHE_KEY_PREFIX = 'portfolio_'

    # Enhanced bcrypt rounds for production
    BCRYPT_LOG_ROUNDS = 13

    # Production rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = '100 per day, 30 per hour'

    # Production logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')


class TestingConfig(BaseConfig):
    """Testing configuration - for unit tests and integration tests"""
    TESTING = True
    DEBUG = True

    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False

    # Fast bcrypt for tests (lower security but faster test execution)
    BCRYPT_LOG_ROUNDS = 4

    # No caching in tests
    CACHE_TYPE = 'NullCache'

    # Override SECRET_KEY requirement for testing
    SECRET_KEY = 'test-secret-key-not-for-production'
    POSTGRES_PASSWORD = 'test-password'


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration object based on environment

    Args:
        config_name: Configuration name ('development', 'production', 'testing')
                    If None, uses FLASK_ENV environment variable

    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    return config.get(config_name, config['default'])
