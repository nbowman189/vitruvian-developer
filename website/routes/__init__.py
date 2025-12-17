"""
Routes/Blueprints for the application
"""

from flask import Blueprint

# Import API blueprint from api package (has sub-blueprints for health, workout, etc.)
from ..api import api_bp

# Create blueprints
main_bp = Blueprint('main', __name__)
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')
health_bp = Blueprint('health', __name__, url_prefix='/health-and-fitness')
insights_bp = Blueprint('insights', __name__)

__all__ = ['main_bp', 'blog_bp', 'api_bp', 'health_bp', 'insights_bp']
