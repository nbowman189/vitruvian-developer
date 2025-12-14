"""
Health and fitness related routes
"""

from flask import render_template
from . import health_bp
from ..utils.error_handler import log_request


@health_bp.route('/graphs')
@log_request
def graphs():
    """Render health and fitness graphs page"""
    return render_template('graphs.html')
