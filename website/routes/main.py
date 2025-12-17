"""
Main application routes
"""

from flask import render_template, send_from_directory, current_app
from . import main_bp
from ..utils.error_handler import log_request
import os


@main_bp.route('/')
@log_request
def index():
    """Render home page"""
    return render_template('index.html')


@main_bp.route('/project-case-study/<project_name>')
@log_request
def project_case_study(project_name):
    """Render the professional case study page"""
    PROJECT_DIRS = current_app.config.get('PROJECT_DIRS', [])
    if project_name not in PROJECT_DIRS:
        return "Project not found", 404
    return render_template('case_study.html', project_title=project_name.replace('_', ' '))


@main_bp.route('/the-vitruvian-developer')
@log_request
def origin_story():
    """Render the complete origin story page"""
    return render_template('origin_story.html')


@main_bp.route('/project/<project_name>')
@main_bp.route('/project/<project_name>/')
@main_bp.route('/project/<project_name>/<path:file_path>')
@log_request
def project_page(project_name, file_path=None):
    """
    Render the project documentation page with sidebar navigation.
    Supports bookmarkable URLs like /project/Health_and_Fitness/fitness-roadmap.md
    """
    PROJECT_DIRS = current_app.config.get('PROJECT_DIRS', [])
    PROJECT_METADATA = current_app.config.get('PROJECT_METADATA', {})

    if project_name not in PROJECT_DIRS:
        return "Project not found", 404

    # Get project metadata
    metadata = PROJECT_METADATA.get(project_name, {})
    display_name = metadata.get('display_name', project_name.replace('_', ' '))

    return render_template('project.html',
                          project_name=project_name,
                          project_display_name=display_name,
                          initial_file=file_path)


@main_bp.route('/knowledge-graph')
@log_request
def knowledge_graph():
    """Render knowledge graph visualization page"""
    return render_template('knowledge-graph.html')


@main_bp.route('/insights')
@log_request
def insights():
    """Render reading insights dashboard"""
    return render_template('insights.html')


@main_bp.route('/dashboard')
@log_request
def dashboard():
    """Render user dashboard page"""
    from flask_login import login_required
    from flask import abort
    from flask_login import current_user

    # Require authentication
    if not current_user.is_authenticated:
        abort(401)

    return render_template('dashboard.html')


@main_bp.route('/health/metrics')
@log_request
def health_metrics():
    """Render health metrics page"""
    from flask import abort
    from flask_login import current_user

    if not current_user.is_authenticated:
        abort(401)

    return render_template('health_metrics.html')


@main_bp.route('/workout/workouts')
@log_request
def workout_workouts():
    """Render workouts page"""
    from flask import abort
    from flask_login import current_user

    if not current_user.is_authenticated:
        abort(401)

    return render_template('workout_workouts.html')


@main_bp.route('/coaching/sessions')
@log_request
def coaching_sessions():
    """Render coaching sessions page"""
    from flask import abort
    from flask_login import current_user

    if not current_user.is_authenticated:
        abort(401)

    return render_template('coaching_sessions.html')


@main_bp.route('/nutrition/meals')
@log_request
def nutrition_meals():
    """Render nutrition meals page"""
    from flask import abort
    from flask_login import current_user

    if not current_user.is_authenticated:
        abort(401)

    return render_template('nutrition_meals.html')


@main_bp.route('/ai-coach')
@log_request
def ai_coach():
    """Render AI coach page"""
    from flask import abort
    from flask_login import current_user

    if not current_user.is_authenticated:
        abort(401)

    return render_template('health/ai_coach.html')


@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'), filename)
