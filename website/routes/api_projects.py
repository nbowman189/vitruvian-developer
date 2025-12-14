"""
Projects API endpoints
"""

from flask import jsonify, current_app
from . import api_bp
from ..utils.error_handler import handle_api_errors, log_request, NotFoundError
from ..utils.file_utils import ProjectFileManager
import os


class ProjectsAPI:
    """Projects API service"""

    def __init__(self, project_root, project_dirs, file_orders):
        self.project_root = project_root
        self.project_dirs = project_dirs
        self.file_orders = file_orders
        self.file_manager = ProjectFileManager(project_root, project_dirs)

    def get_projects(self):
        """Get all available projects"""
        projects = []
        for project_dir in self.project_dirs:
            if os.path.isdir(os.path.join(self.project_root, project_dir)):
                projects.append(project_dir)
        return projects

    def get_project_gemini(self, project_name):
        """Get GEMINI.md content for a project"""
        try:
            content = self.file_manager.get_gemini_file(project_name)
            return {
                "title": project_name,
                "content": content
            }
        except FileNotFoundError:
            raise NotFoundError(f"GEMINI.md not found for project '{project_name}'")
        except ValueError as e:
            raise NotFoundError(str(e))

    def get_project_files(self, project_name):
        """Get all markdown files for a project"""
        try:
            file_order = self.file_orders.get(project_name)
            files = self.file_manager.get_project_files(project_name, file_order)
            return files
        except ValueError as e:
            raise NotFoundError(str(e))

    def get_project_file_content(self, project_name, file_path):
        """Get content of a specific file in a project"""
        try:
            content = self.file_manager.get_file_content(project_name, file_path)
            return {
                "title": file_path,
                "content": content
            }
        except (FileNotFoundError, ValueError) as e:
            raise NotFoundError(str(e))


# Initialize the projects API
_projects_api = None


def get_projects_api():
    """Get or create projects API instance"""
    global _projects_api
    if _projects_api is None:
        from config import Config
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        file_orders = {
            'Health_and_Fitness': Config.HEALTH_FITNESS_FILE_ORDER
        }
        _projects_api = ProjectsAPI(project_root, Config.PROJECT_DIRS, file_orders)
    return _projects_api


# API Routes
@api_bp.route('/projects', methods=['GET'])
@handle_api_errors
@log_request
def get_projects():
    """Get all available projects"""
    projects_api = get_projects_api()
    projects = projects_api.get_projects()
    return jsonify(projects)


@api_bp.route('/project/<project_name>', methods=['GET'])
@handle_api_errors
@log_request
def get_project(project_name):
    """Get GEMINI.md content for a project"""
    projects_api = get_projects_api()
    data = projects_api.get_project_gemini(project_name)
    return jsonify(data)


@api_bp.route('/project/<project_name>/files', methods=['GET'])
@handle_api_errors
@log_request
def get_project_files(project_name):
    """Get all markdown files for a project"""
    projects_api = get_projects_api()
    files = projects_api.get_project_files(project_name)
    return jsonify(files)


@api_bp.route('/project/<project_name>/file/<path:file_path>', methods=['GET'])
@handle_api_errors
@log_request
def get_project_file(project_name, file_path):
    """Get content of a specific file in a project"""
    projects_api = get_projects_api()
    data = projects_api.get_project_file_content(project_name, file_path)
    return jsonify(data)
