"""
Blog API endpoints
"""

from flask import jsonify, current_app, request
from . import api_bp
from ..utils.error_handler import handle_api_errors, log_request, NotFoundError
from ..utils.file_utils import BlogPostParser
from ..utils.cache import cached, get_cache
from ..utils.pagination import paginate_response, validate_pagination_params
from ..utils.performance import monitor_performance, RequestTimer
from datetime import datetime
import os


class BlogAPI:
    """Blog API service"""

    def __init__(self, blog_dir):
        self.blog_dir = blog_dir

    def get_all_posts(self):
        """Get all blog posts sorted by date (newest first)"""
        posts = []

        if not os.path.exists(self.blog_dir):
            return posts

        for filename in os.listdir(self.blog_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(self.blog_dir, filename)
                post = BlogPostParser.parse(filepath)
                if post:
                    posts.append({
                        'slug': post['metadata'].get('slug', filename[:-3]),
                        **post['metadata']
                    })

        # Sort by date (newest first) with safe parsing
        def safe_parse_date(date_str):
            """Safely parse date string with fallback"""
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except (ValueError, TypeError):
                return datetime.strptime('2000-01-01', '%Y-%m-%d')

        posts.sort(
            key=lambda x: safe_parse_date(x.get('date', '2000-01-01')),
            reverse=True
        )
        return posts

    def get_post_by_slug(self, slug):
        """Get a specific blog post by slug"""
        if not os.path.exists(self.blog_dir):
            raise NotFoundError("Blog not found")

        for filename in os.listdir(self.blog_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(self.blog_dir, filename)
                post_data = BlogPostParser.parse(filepath)
                if post_data and post_data['metadata'].get('slug') == slug:
                    return {
                        'slug': slug,
                        'metadata': post_data['metadata'],
                        'content': post_data['html']
                    }

        raise NotFoundError("Post not found")

    def get_related_projects(self, slug):
        """Get related projects for a blog post"""
        post = self.get_post_by_slug(slug)
        featured_projects = current_app.config.get('FEATURED_PROJECTS', [])

        post_disciplines = set(post['metadata'].get('disciplines', []))
        related_projects = [
            p for p in featured_projects
            if any(d in p['disciplines'] for d in post_disciplines)
        ]

        return related_projects[:5]  # Return up to 5 related projects


# Initialize the blog API
_blog_api = None


def get_blog_api():
    """Get or create blog API instance"""
    global _blog_api
    if _blog_api is None:
        blog_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog')
        _blog_api = BlogAPI(blog_dir)
    return _blog_api


# API Routes
@api_bp.route('/blog/posts', methods=['GET'])
@handle_api_errors
@log_request
@monitor_performance
def get_blog_posts():
    """Get all blog posts with pagination"""
    with RequestTimer('get_blog_posts'):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        page, per_page = validate_pagination_params(page, per_page)

        blog_api = get_blog_api()
        posts = blog_api.get_all_posts()

        return jsonify(paginate_response(posts, page, per_page))


@api_bp.route('/blog/posts/latest', methods=['GET'])
@handle_api_errors
@log_request
@monitor_performance
def get_latest_blog_posts():
    """Get latest N blog posts (cached)"""
    with RequestTimer('get_latest_blog_posts'):
        limit = request.args.get('limit', 5, type=int)
        limit = max(1, min(50, limit))  # Limit between 1-50

        # Check cache first
        cache = get_cache()
        cache_key = f"latest_posts_{limit}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return jsonify(cached_result)

        blog_api = get_blog_api()
        posts = blog_api.get_all_posts()[:limit]

        # Cache for 5 minutes
        cache.set(cache_key, posts, timeout=300)
        return jsonify(posts)


@api_bp.route('/blog/post/<slug>', methods=['GET'])
@handle_api_errors
@log_request
@monitor_performance
def get_blog_post(slug):
    """Get a specific blog post by slug (cached)"""
    with RequestTimer(f'get_blog_post_{slug}'):
        # Check cache first
        cache = get_cache()
        cache_key = f"post_{slug}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return jsonify(cached_result)

        blog_api = get_blog_api()
        post = blog_api.get_post_by_slug(slug)

        # Cache for 1 hour (post content doesn't change often)
        cache.set(cache_key, post, timeout=3600)
        return jsonify(post)


@api_bp.route('/blog/post/<slug>/related-projects', methods=['GET'])
@handle_api_errors
@log_request
@monitor_performance
def get_post_related_projects(slug):
    """Get related projects for a blog post (cached)"""
    with RequestTimer(f'get_post_related_projects_{slug}'):
        # Check cache first
        cache = get_cache()
        cache_key = f"related_projects_{slug}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return jsonify(cached_result)

        blog_api = get_blog_api()
        projects = blog_api.get_related_projects(slug)

        # Cache for 1 hour
        cache.set(cache_key, projects, timeout=3600)
        return jsonify(projects)
