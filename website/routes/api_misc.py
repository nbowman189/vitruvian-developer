"""
Miscellaneous API endpoints (health data, featured projects, contact info)
"""

from flask import jsonify, current_app
from . import api_bp
from ..utils.error_handler import handle_api_errors, log_request, NotFoundError
from ..utils.file_utils import HealthDataParser
import os


class MiscAPI:
    """Miscellaneous API service"""

    def get_health_data(self, project_root):
        """Get health data from check-in-log.md"""
        health_data_path = os.path.join(project_root, 'Health_and_Fitness', 'check-in-log.md')
        return HealthDataParser.parse_health_data(health_data_path)

    def get_featured_projects(self):
        """Get featured projects"""
        return current_app.config.get('FEATURED_PROJECTS', [])

    def get_contact_info(self):
        """Get contact information"""
        return current_app.config.get('CONTACT_INFO', {})

    def get_graph_data(self):
        """Get knowledge graph data"""
        # This endpoint integrates with the knowledge graph data
        featured_projects = self.get_featured_projects()
        # The actual graph structure would be built based on blog posts and projects
        # For now, we return a basic structure
        return {
            'nodes': [
                {
                    'id': p['id'],
                    'title': p['title'],
                    'type': 'project',
                    'disciplines': p['disciplines'],
                    'slug': p['id']
                }
                for p in featured_projects
            ],
            'edges': [],
            'stats': {
                'total_nodes': len(featured_projects),
                'total_edges': 0,
                'posts': 0,
                'projects': len(featured_projects)
            }
        }

    def get_disciplines(self):
        """Get discipline information"""
        return {
            'code': {
                'posts': [],
                'projects': [p for p in self.get_featured_projects() if 'code' in p.get('disciplines', [])],
                'connections': 0
            },
            'ai': {
                'posts': [],
                'projects': [p for p in self.get_featured_projects() if 'ai' in p.get('disciplines', [])],
                'connections': 0
            },
            'fitness': {
                'posts': [],
                'projects': [p for p in self.get_featured_projects() if 'fitness' in p.get('disciplines', [])],
                'connections': 0
            },
            'meta': {
                'posts': [],
                'projects': [p for p in self.get_featured_projects() if 'meta' in p.get('disciplines', [])],
                'connections': 0
            }
        }


# Initialize the misc API
_misc_api = None


def get_misc_api():
    """Get or create misc API instance"""
    global _misc_api
    if _misc_api is None:
        _misc_api = MiscAPI()
    return _misc_api


# API Routes
@api_bp.route('/health-and-fitness/health_data', methods=['GET'])
@handle_api_errors
@log_request
def get_health_data():
    """Get health and fitness data (requires authentication)"""
    from flask_login import login_required, current_user

    # Require authentication for private health data
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401

    import os
    # In Docker, project directories are at root level /
    # In local dev, they're in the parent of the website directory
    project_root = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    misc_api = get_misc_api()
    data = misc_api.get_health_data(project_root)
    return jsonify(data)


@api_bp.route('/featured-projects', methods=['GET'])
@handle_api_errors
@log_request
def get_featured_projects():
    """Get featured projects"""
    misc_api = get_misc_api()
    projects = misc_api.get_featured_projects()
    return jsonify(projects)


@api_bp.route('/contact-info', methods=['GET'])
@handle_api_errors
@log_request
def get_contact_info():
    """Get contact information"""
    misc_api = get_misc_api()
    info = misc_api.get_contact_info()
    return jsonify(info)


@api_bp.route('/content/graph', methods=['GET'])
@handle_api_errors
@log_request
def get_graph_data():
    """Get knowledge graph data"""
    misc_api = get_misc_api()
    data = misc_api.get_graph_data()
    return jsonify(data)


@api_bp.route('/content/disciplines', methods=['GET'])
@handle_api_errors
@log_request
def get_disciplines():
    """Get discipline information"""
    misc_api = get_misc_api()
    data = misc_api.get_disciplines()
    return jsonify(data)


@api_bp.route('/content/related', methods=['GET'])
@handle_api_errors
@log_request
def get_related_content():
    """Get related content for a specific item"""
    from flask import request
    from ..utils.error_handler import ValidationError

    content_type = request.args.get('type', '').strip()
    content_id = request.args.get('id', '').strip()

    # Validate input parameters
    if not content_type or content_type not in ['post', 'project']:
        raise ValidationError("Invalid content type. Must be 'post' or 'project'")

    if not content_id or len(content_id) > 255:
        raise ValidationError("Invalid content ID. Must be non-empty and <= 255 characters")

    # This endpoint would be extended to provide actual related content
    # For now, return empty structure
    return jsonify({
        'primary': content_id,
        'type': content_type,
        'shared_disciplines': [],
        'related_posts': []
    })


@api_bp.route('/content/search', methods=['GET'])
@handle_api_errors
@log_request
def search_content():
    """Search across blog posts and projects by title, tags, or disciplines"""
    from flask import request
    from ..utils.error_handler import ValidationError

    query = request.args.get('q', '').lower().strip()
    search_type = request.args.get('type', 'all')

    if not query or len(query) < 2:
        raise ValidationError("Query too short. Minimum 2 characters.")

    results = {'posts': [], 'projects': []}

    # Search would be implemented here
    # For now, return empty results
    return jsonify(results)
