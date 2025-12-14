"""
Main application routes
"""

from flask import render_template, send_from_directory
from . import main_bp
from ..utils.error_handler import log_request
import os


@main_bp.route('/')
@log_request
def index():
    """Render home page"""
    return render_template('index.html')


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


@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'), filename)
