"""
Routes/Blueprints for the application
"""

from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')
api_bp = Blueprint('api', __name__, url_prefix='/api')
health_bp = Blueprint('health', __name__, url_prefix='/health')
insights_bp = Blueprint('insights', __name__)

__all__ = ['main_bp', 'blog_bp', 'api_bp', 'health_bp', 'insights_bp']
