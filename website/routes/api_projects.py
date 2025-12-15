"""
Projects API endpoints
"""

from flask import jsonify, current_app
from . import api_bp
from ..utils.error_handler import handle_api_errors, log_request, NotFoundError
from ..utils.file_utils import ProjectFileManager, FileCategorizer
import os
import re
import markdown


class ProjectsAPI:
    """Projects API service"""

    def __init__(self, project_root, project_dirs, file_orders):
        self.project_root = project_root
        self.project_dirs = project_dirs
        self.file_orders = file_orders
        # File manager is created dynamically based on authentication status

    def _get_file_manager(self):
        """Get file manager with appropriate data access based on authentication"""
        from flask_login import current_user
        allow_data_access = current_user.is_authenticated
        return ProjectFileManager(self.project_root, self.project_dirs, allow_data_access=allow_data_access)

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
            file_manager = self._get_file_manager()
            content = file_manager.get_gemini_file(project_name)
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
            file_manager = self._get_file_manager()
            file_order = self.file_orders.get(project_name)
            files = file_manager.get_project_files(project_name, file_order)
            return files
        except ValueError as e:
            raise NotFoundError(str(e))

    def get_project_file_content(self, project_name, file_path):
        """Get content of a specific file in a project"""
        try:
            file_manager = self._get_file_manager()
            content = file_manager.get_file_content(project_name, file_path)
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
        # In Docker, project directories are at root level /
        # In local dev, they're in the parent of the website directory
        project_root = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        file_orders = {
            'Health_and_Fitness': current_app.config.get('HEALTH_FITNESS_FILE_ORDER', [])
        }
        project_dirs = current_app.config.get('PROJECT_DIRS', [])
        _projects_api = ProjectsAPI(project_root, project_dirs, file_orders)
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
    from flask_login import current_user

    # Check if this is a private data file (in /data/ directory)
    if file_path.startswith('data/') or '/data/' in file_path:
        # Require authentication for private data files
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required for private data"}), 401

    projects_api = get_projects_api()
    data = projects_api.get_project_file_content(project_name, file_path)
    return jsonify(data)


# Helper functions for project summaries and featured projects
def filename_to_title(filename):
    """Convert a filename to a readable title"""
    custom_titles = {
        'check-in-log.md': 'Metrics Log',
        'progress-check-in-log.md': 'Exercise Progress Log',
        'GEMINI.md': 'Overview',
        'README.md': 'Introduction'
    }

    if filename in custom_titles:
        return custom_titles[filename]

    name = os.path.basename(filename)
    name = os.path.splitext(name)[0]
    name = name.replace('-', ' ').replace('_', ' ')
    return name.title()


def parse_project_summary(project_name):
    """Parse a project summary markdown file with YAML front matter"""
    # In Docker, project directories are at root level /
    # In local dev, they're in the parent of the website directory
    project_root = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    summary_path = os.path.join(project_root, project_name, '_project_summary.md')

    if not os.path.exists(summary_path):
        return None

    with open(summary_path, 'r') as f:
        content = f.read()

    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return None

    metadata_str, body = match.groups()
    metadata = {}
    lines = metadata_str.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        if ':' in line and not line.startswith(' '):
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if value == '' and i + 1 < len(lines) and lines[i + 1].startswith('  - '):
                list_items = []
                i += 1
                while i < len(lines) and lines[i].startswith('  - '):
                    item = lines[i].replace('  - ', '').strip()
                    list_items.append(item)
                    i += 1
                value = list_items
                i -= 1
            elif value.startswith('[') and value.endswith(']'):
                value = [item.strip().strip("'\"") for item in value[1:-1].split(',')]
            elif value == '|':
                multiline_content = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line and not next_line.startswith(' ') and ':' in next_line:
                        i -= 1
                        break
                    if next_line.startswith('  '):
                        multiline_content.append(next_line[2:])
                    i += 1
                value = '\n'.join(multiline_content) if multiline_content else ''
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)

            metadata[key] = value

        i += 1

    return {
        'metadata': metadata,
        'content': body.strip(),
        'html': markdown.markdown(body.strip(), extensions=['tables', 'codehilite', 'fenced_code']),
        'project_name': project_name
    }


def get_featured_projects_data():
    """Get featured projects dynamically from _project_summary.md files"""
    featured_projects = []
    project_dirs = current_app.config.get('PROJECT_DIRS', [])

    for project_name in project_dirs:
        summary = parse_project_summary(project_name)
        if summary:
            metadata = summary['metadata']
            featured_projects.append({
                'id': project_name.lower().replace('_', '-'),
                'title': metadata.get('title', project_name),
                'description': metadata.get('description', ''),
                'disciplines': metadata.get('disciplines', []),
                'technologies': metadata.get('technologies', []),
                'project': project_name,
                'links': {
                    'demo': f'/#/project/{project_name}',
                    'github': 'https://github.com/nbowman189'
                }
            })

    return featured_projects


# Additional API Routes
@api_bp.route('/projects-metadata', methods=['GET'])
@handle_api_errors
@log_request
def get_projects_metadata():
    """Get metadata for all projects including disciplines"""
    project_metadata = current_app.config.get('PROJECT_METADATA', {})
    return jsonify(project_metadata)


@api_bp.route('/project/<project_name>/categorized-files', methods=['GET'])
@handle_api_errors
@log_request
def get_categorized_files(project_name):
    """Get all markdown files for a project, categorized by content analysis"""
    from flask_login import current_user

    project_dirs = current_app.config.get('PROJECT_DIRS', [])
    if project_name not in project_dirs:
        raise NotFoundError("Project not found")

    try:
        # In Docker, project directories are at root level /
        # In local dev, they're in the parent of the website directory
        project_root = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        project_path = os.path.join(project_root, project_name)
        docs_path = os.path.join(project_path, 'docs')

        scan_path = docs_path if os.path.isdir(docs_path) else project_path

        files_with_content = []

        for root, _, files in os.walk(scan_path):
            for file in files:
                if file.endswith('.md') and not file.startswith('_'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, scan_path)

                    try:
                        with open(file_path, 'r') as f:
                            content = f.read(2000)
                        files_with_content.append((relative_path, content))
                    except Exception:
                        files_with_content.append((relative_path, ''))

        # Add virtual database-driven pages if user is authenticated
        if current_user.is_authenticated and project_name in ProjectFileManager.VIRTUAL_PAGES:
            for virtual_page in ProjectFileManager.VIRTUAL_PAGES[project_name]:
                # Add virtual page with empty content (will be generated on demand)
                files_with_content.append((virtual_page, ''))

        categorized = FileCategorizer.categorize_project_files(project_name, files_with_content)

        result = {
            'project': project_name,
            'categories': []
        }

        for category, files in categorized.items():
            result['categories'].append({
                'id': category,
                'name': FileCategorizer.get_category_display_name(category),
                'files': [{'path': f, 'name': filename_to_title(f)} for f in files]
            })

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error categorizing files: {str(e)}")
        return jsonify({"error": "Failed to categorize files"}), 500


@api_bp.route('/project/<project_name>/summary', methods=['GET'])
@handle_api_errors
@log_request
def get_project_summary(project_name):
    """Get the detailed project case study from _project_summary.md"""
    project_dirs = current_app.config.get('PROJECT_DIRS', [])
    if project_name not in project_dirs:
        raise NotFoundError("Project not found")

    summary = parse_project_summary(project_name)
    if not summary:
        raise NotFoundError("Project summary not found")

    return jsonify({
        'project_name': project_name,
        'metadata': summary['metadata'],
        'content': summary['content'],
        'html': summary['html']
    })


@api_bp.route('/origin-story', methods=['GET'])
@handle_api_errors
@log_request
def get_origin_story():
    """Get the complete origin story as HTML-rendered markdown"""
    # In Docker, project directories are at root level /
    # In local dev, they're in the parent of the website directory
    project_root = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    origin_story_path = os.path.join(project_root, 'AI_Development', 'docs', 'vitruvian-origin-story-claude.md')

    if not os.path.exists(origin_story_path):
        raise NotFoundError("Origin story not found")

    with open(origin_story_path, 'r') as f:
        content = f.read()

    html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])

    return jsonify({
        "title": "The Vitruvian Developer",
        "content": html_content
    })
