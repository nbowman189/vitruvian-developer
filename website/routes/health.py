"""
Health and fitness related routes
"""

from flask import render_template
from flask_login import login_required
from . import health_bp
from ..utils.error_handler import log_request


@health_bp.route('/graphs')
@log_request
def graphs():
    """Render health and fitness graphs page"""
    return render_template('graphs.html')


@health_bp.route('/ai-coach')
@login_required
@log_request
def ai_coach():
    """Render AI coaching interface page"""
    return render_template('health/ai_coach.html')
