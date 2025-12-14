"""
Blog routes (rendering blog pages)
"""

from flask import render_template
from . import blog_bp
from ..utils.error_handler import log_request


@blog_bp.route('/')
@log_request
def blog_list():
    """Render blog listing page"""
    return render_template('blog_list.html')


@blog_bp.route('/saved')
@log_request
def saved_articles():
    """Render saved articles page"""
    return render_template('saved_articles.html')


@blog_bp.route('/<slug>')
@log_request
def blog_article(slug):
    """Render individual blog article"""
    return render_template('blog_article.html', slug=slug)
