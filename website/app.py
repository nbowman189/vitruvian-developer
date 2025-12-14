import os
import markdown
import re
from datetime import datetime
from flask import Flask, jsonify, render_template, send_from_directory

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Define the root directory of your project
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blog')

# List of directories to consider as "projects"
PROJECT_DIRS = ['AI_Development', 'Health_and_Fitness']

# Define the desired file order for Health_and_Fitness project
HEALTH_FITNESS_FILE_ORDER = [
    'fitness-roadmap.md',
    'Full-Meal-Plan.md',
    'Shopping-List-and-Estimate.md',
    'check-in-log.md',
    'progress-check-in-log.md'
]

# Project metadata
PROJECT_METADATA = {
    'Health_and_Fitness': {
        'display_name': 'Health & Fitness',
        'disciplines': ['fitness', 'meta'],
        'description': 'Complete health and fitness management system with meal plans, workout tracking, and progress monitoring.'
    },
    'AI_Development': {
        'display_name': 'AI Development',
        'disciplines': ['ai', 'code'],
        'description': 'Exploration and development of artificial intelligence concepts, applications, and research.'
    }
}

# Featured projects are now loaded dynamically from _project_summary.md files
# See get_featured_projects_data() function for implementation

# Contact information
CONTACT_INFO = {
    'email': 'nbowman189@gmail.com',
    'linkedin': 'https://www.linkedin.com/in/nathan-bowman-b27484103/',
    'github': 'https://github.com/nbowman189'
}

# Global Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found', 'status_code': 404}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error', 'status_code': 500}), 500

# Security headers middleware
@app.after_request
def set_security_headers(response):
    """Add HTTP security headers to all responses"""
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Enable browser XSS protections
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # HSTS header for HTTPS in production
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/project-case-study/<project_name>')
def project_case_study(project_name):
    """Render the professional case study page."""
    if project_name not in PROJECT_DIRS:
        return "Project not found", 404
    return render_template('case_study.html', project_title=project_name.replace('_', ' '))

@app.route('/the-vitruvian-developer')
def origin_story():
    """Render the complete origin story page."""
    return render_template('origin_story.html')

@app.route('/project/<project_name>')
@app.route('/project/<project_name>/')
@app.route('/project/<project_name>/<path:file_path>')
def project_page(project_name, file_path=None):
    """
    Render the project documentation page with sidebar navigation.
    Supports bookmarkable URLs like /project/Health_and_Fitness/fitness-roadmap.md
    """
    if project_name not in PROJECT_DIRS:
        return "Project not found", 404

    # Get project metadata
    metadata = PROJECT_METADATA.get(project_name, {})
    display_name = metadata.get('display_name', project_name.replace('_', ' '))

    return render_template('project.html',
                          project_name=project_name,
                          project_display_name=display_name,
                          initial_file=file_path)

@app.route('/api/project/<project_name>/categorized-files')
def get_categorized_files(project_name):
    """
    Get all markdown files for a project, categorized by content analysis.
    Returns files organized into categories like 'training', 'nutrition', etc.
    """
    if project_name not in PROJECT_DIRS:
        return jsonify({"error": "Project not found"}), 404

    try:
        from utils.file_utils import ProjectFileManager, FileCategorizer

        manager = ProjectFileManager(PROJECT_ROOT, PROJECT_DIRS)
        project_path = os.path.join(PROJECT_ROOT, project_name)
        docs_path = os.path.join(project_path, 'docs')

        # Determine scan path
        scan_path = docs_path if os.path.isdir(docs_path) else project_path

        files_with_content = []

        for root, _, files in os.walk(scan_path):
            for file in files:
                if file.endswith('.md') and not file.startswith('_'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, scan_path)

                    # Read first 2000 chars for categorization
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read(2000)
                        files_with_content.append((relative_path, content))
                    except Exception:
                        files_with_content.append((relative_path, ''))

        # Categorize files
        categorized = FileCategorizer.categorize_project_files(project_name, files_with_content)

        # Build response with display names
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
        app.logger.error(f"Error categorizing files: {str(e)}")
        return jsonify({"error": "Failed to categorize files"}), 500

def filename_to_title(filename):
    """Convert a filename to a readable title"""
    # Custom display names
    custom_titles = {
        'check-in-log.md': 'Metrics Log',
        'progress-check-in-log.md': 'Exercise Progress Log',
        'GEMINI.md': 'Overview',
        'README.md': 'Introduction'
    }

    if filename in custom_titles:
        return custom_titles[filename]

    # Remove path and extension
    name = os.path.basename(filename)
    name = os.path.splitext(name)[0]

    # Replace separators with spaces
    name = name.replace('-', ' ').replace('_', ' ')

    # Title case
    return name.title()

@app.route('/api/origin-story')
def get_origin_story():
    """Get the complete origin story as HTML-rendered markdown."""
    origin_story_path = os.path.join(PROJECT_ROOT, 'AI_Development', 'docs', 'vitruvian-origin-story-claude.md')

    if not os.path.exists(origin_story_path):
        return jsonify({"error": "Origin story not found"}), 404

    with open(origin_story_path, 'r') as f:
        content = f.read()

    # Render markdown to HTML
    html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])

    return jsonify({
        "title": "The Vitruvian Developer",
        "content": html_content
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.root_path + '/static', filename)

@app.route('/api/projects')
def get_projects():
    projects = []
    for project_dir in PROJECT_DIRS:
        if os.path.isdir(os.path.join(PROJECT_ROOT, project_dir)):
            projects.append(project_dir)
    return jsonify(projects)

@app.route('/api/projects-metadata')
def get_projects_metadata():
    """Get metadata for all projects including disciplines"""
    return jsonify(PROJECT_METADATA)

@app.route('/api/project/<project_name>')
def get_project_gemini_md(project_name):
    if project_name not in PROJECT_DIRS:
        return jsonify({"error": "Project not found"}), 404

    gemini_md_path = os.path.join(PROJECT_ROOT, project_name, 'GEMINI.md')
    if os.path.exists(gemini_md_path):
        with open(gemini_md_path, 'r') as f:
            content = f.read()
        return jsonify({"title": project_name, "content": content})
    return jsonify({"error": "GEMINI.md not found for this project"}), 404

@app.route('/api/project/<project_name>/files')
def get_project_markdown_files(project_name):
    if project_name not in PROJECT_DIRS:
        return jsonify({"error": "Project not found"}), 404

    project_path = os.path.join(PROJECT_ROOT, project_name)
    docs_path = os.path.join(project_path, 'docs')

    # If docs directory exists, scan it; otherwise scan project root
    scan_path = docs_path if os.path.isdir(docs_path) else project_path

    markdown_files = []
    for root, _, files in os.walk(scan_path):
        for file in files:
            if file.endswith('.md') and not file.startswith('_'):
                # Get path relative to the scan directory
                relative_path = os.path.relpath(os.path.join(root, file), scan_path)
                markdown_files.append(relative_path)

    # Apply custom ordering for Health_and_Fitness project
    if project_name == 'Health_and_Fitness':
        markdown_files.sort(key=lambda f: (
            HEALTH_FITNESS_FILE_ORDER.index(f) if f in HEALTH_FITNESS_FILE_ORDER else len(HEALTH_FITNESS_FILE_ORDER)
        ))

    return jsonify(markdown_files)

@app.route('/api/project/<project_name>/file/<path:file_path>')
def get_markdown_file_content(project_name, file_path):
    if project_name not in PROJECT_DIRS:
        return jsonify({"error": "Project not found"}), 404

    try:
        from utils.file_utils import ProjectFileManager
        manager = ProjectFileManager(PROJECT_ROOT, PROJECT_DIRS)
        content = manager.get_file_content(project_name, file_path)
        return jsonify({"title": file_path, "content": content})
    except ValueError as e:
        # Path traversal attempt
        app.logger.warning(f"Path traversal attempt detected: {project_name}/{file_path}")
        return jsonify({"error": "Access denied"}), 403
    except FileNotFoundError:
        return jsonify({"error": "File not found or not a markdown file"}), 404
    except Exception as e:
        app.logger.error(f"Error reading file: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health-and-fitness/graphs')
def graphs():
    return render_template('graphs.html')

@app.route('/api/health-and-fitness/health_data')
def get_health_data():
    health_data_path = os.path.join(PROJECT_ROOT, 'Health_and_Fitness', 'data', 'check-in-log.md')
    if not os.path.exists(health_data_path):
        return jsonify({"error": "Health data file not found"}), 404

    weight_data = []
    bodyfat_data = []

    with open(health_data_path, 'r') as f:
        lines = f.readlines()
        # Skip header and separator
        for line in lines[2:]:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                date = parts[0]
                weight = parts[1]
                bodyfat = parts[2]

                if weight != 'None':
                    try:
                        weight_data.append({'x': date, 'y': float(weight)})
                    except ValueError:
                        pass # Ignore lines where weight is not a valid float

                if bodyfat != 'None':
                    try:
                        bodyfat_data.append({'x': date, 'y': float(bodyfat)})
                    except ValueError:
                        pass # Ignore lines where bodyfat is not a valid float

    return jsonify({'weight': weight_data, 'bodyfat': bodyfat_data})

@app.route('/api/featured-projects')
def get_featured_projects():
    """Dynamically load featured projects from their _project_summary.md files."""
    return jsonify(get_featured_projects_data())

@app.route('/api/project/<project_name>/summary')
def get_project_summary(project_name):
    """Get the detailed project case study from _project_summary.md."""
    if project_name not in PROJECT_DIRS:
        return jsonify({"error": "Project not found"}), 404

    summary = parse_project_summary(project_name)
    if not summary:
        return jsonify({"error": "Project summary not found"}), 404

    return jsonify({
        'project_name': project_name,
        'metadata': summary['metadata'],
        'content': summary['content'],
        'html': summary['html']
    })

@app.route('/api/contact-info')
def get_contact_info():
    return jsonify(CONTACT_INFO)

# Blog helper functions
def parse_blog_post(filepath):
    """Parse a blog post markdown file with YAML front matter."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract YAML front matter
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return None

    metadata_str, body = match.groups()
    metadata = {}

    for line in metadata_str.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Parse lists
            if value.startswith('[') and value.endswith(']'):
                value = [item.strip().strip("'\"") for item in value[1:-1].split(',')]
            # Parse booleans and numbers
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)

            metadata[key] = value

    return {
        'metadata': metadata,
        'content': body.strip(),
        'html': markdown.markdown(body.strip(), extensions=['tables', 'codehilite'])
    }

def get_featured_projects_data():
    """Get featured projects dynamically from _project_summary.md files."""
    featured_projects = []

    for project_name in PROJECT_DIRS:
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

def parse_project_summary(project_name):
    """Parse a project summary markdown file with YAML front matter."""
    summary_path = os.path.join(PROJECT_ROOT, project_name, '_project_summary.md')

    if not os.path.exists(summary_path):
        return None

    with open(summary_path, 'r') as f:
        content = f.read()

    # Extract YAML front matter
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

            # Parse lists in YAML format (multiline with - prefix)
            if value == '' and i + 1 < len(lines) and lines[i + 1].startswith('  - '):
                list_items = []
                i += 1
                while i < len(lines) and lines[i].startswith('  - '):
                    item = lines[i].replace('  - ', '').strip()
                    list_items.append(item)
                    i += 1
                value = list_items
                i -= 1  # Adjust because we'll increment at the end of loop
            # Parse inline lists (format: [item1, item2, item3])
            elif value.startswith('[') and value.endswith(']'):
                value = [item.strip().strip("'\"") for item in value[1:-1].split(',')]
            # Parse multiline strings (format: |)
            elif value == '|':
                multiline_content = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    # Stop if we hit a new key (not indented)
                    if next_line and not next_line.startswith(' ') and ':' in next_line:
                        i -= 1
                        break
                    if next_line.startswith('  '):
                        multiline_content.append(next_line[2:])
                    i += 1
                value = '\n'.join(multiline_content) if multiline_content else ''
            # Parse booleans and numbers
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

def get_all_blog_posts():
    """Get all blog posts sorted by date (newest first)."""
    posts = []

    if not os.path.exists(BLOG_DIR):
        return posts

    for filename in os.listdir(BLOG_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(BLOG_DIR, filename)
            post = parse_blog_post(filepath)
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

    posts.sort(key=lambda x: safe_parse_date(x.get('date', '2000-01-01')), reverse=True)
    return posts

# Blog Routes
@app.route('/knowledge-graph')
def knowledge_graph():
    """Render knowledge graph visualization page."""
    return render_template('knowledge-graph.html')

@app.route('/blog')
def blog_list():
    """Render blog listing page."""
    return render_template('blog_list.html')

@app.route('/blog/saved')
def saved_articles():
    """Render saved articles page."""
    return render_template('saved_articles.html')

@app.route('/insights')
def insights():
    """Render reading insights dashboard."""
    return render_template('insights.html')

@app.route('/blog/<slug>')
def blog_article(slug):
    """Render individual blog article."""
    return render_template('blog_article.html', slug=slug)

@app.route('/api/blog/posts')
def get_blog_posts():
    """Get all blog posts."""
    posts = get_all_blog_posts()
    return jsonify(posts)

@app.route('/api/blog/posts/latest')
def get_latest_blog_posts():
    """Get latest N blog posts (default 5)."""
    from flask import request
    limit = request.args.get('limit', 5, type=int)
    posts = get_all_blog_posts()
    return jsonify(posts[:limit])

@app.route('/api/blog/post/<slug>')
def get_blog_post(slug):
    """Get a specific blog post by slug."""
    if not os.path.exists(BLOG_DIR):
        return jsonify({"error": "Blog not found"}), 404

    # Find the post file
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(BLOG_DIR, filename)
            post_data = parse_blog_post(filepath)
            if post_data and post_data['metadata'].get('slug') == slug:
                return jsonify({
                    'slug': slug,
                    'metadata': post_data['metadata'],
                    'content': post_data['html']
                })

    return jsonify({"error": "Post not found"}), 404

@app.route('/api/blog/post/<slug>/related-projects')
def get_related_projects(slug):
    """Get related projects for a blog post."""
    if not os.path.exists(BLOG_DIR):
        return jsonify({"error": "Blog not found"}), 404

    # Find the post file and get related projects
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(BLOG_DIR, filename)
            post_data = parse_blog_post(filepath)
            if post_data and post_data['metadata'].get('slug') == slug:
                related_project_ids = post_data['metadata'].get('related_projects', [])

                # Filter featured projects based on related_project_ids
                related_projects = [p for p in get_featured_projects_data() if p['id'] in related_project_ids]
                return jsonify(related_projects)

    return jsonify({"error": "Post not found"}), 404

# Content Graph and Knowledge Base APIs
@app.route('/api/content/graph')
def get_content_graph():
    """
    Get the complete content graph showing relationships between all content items.
    Returns nodes (blog posts, projects) and edges (connections between them).
    """
    # Get all blog posts
    all_posts = get_all_blog_posts()

    # Create nodes for blog posts
    post_nodes = [
        {
            'id': f'post-{post["slug"]}',
            'type': 'blog-post',
            'title': post.get('title', 'Untitled'),
            'slug': post['slug'],
            'disciplines': post.get('disciplines', []),
            'tags': post.get('tags', []),
            'date': post.get('date', ''),
            'reading_time': post.get('reading_time', 0)
        }
        for post in all_posts
    ]

    # Create nodes for projects
    project_nodes = [
        {
            'id': f'project-{project["id"]}',
            'type': 'project',
            'title': project.get('title', 'Untitled'),
            'project_id': project['id'],
            'disciplines': project.get('disciplines', []),
            'technologies': project.get('technologies', [])
        }
        for project in get_featured_projects_data()
    ]

    nodes = post_nodes + project_nodes

    # Create edges based on relationships
    edges = []

    # Direct project-to-post connections (from related_projects field)
    for post in all_posts:
        related_project_ids = post.get('related_projects', [])
        for project_id in related_project_ids:
            edges.append({
                'source': f'post-{post["slug"]}',
                'target': f'project-{project_id}',
                'type': 'related-project',
                'strength': 'strong'
            })

    # Discipline-based connections (posts sharing disciplines)
    for i, post1 in enumerate(all_posts):
        for post2 in all_posts[i+1:]:
            shared_disciplines = set(post1.get('disciplines', [])) & set(post2.get('disciplines', []))
            if shared_disciplines:
                edges.append({
                    'source': f'post-{post1["slug"]}',
                    'target': f'post-{post2["slug"]}',
                    'type': 'shared-discipline',
                    'disciplines': list(shared_disciplines),
                    'strength': 'medium' if len(shared_disciplines) == 1 else 'strong'
                })

    # Tag-based connections (posts sharing significant tags)
    significant_tags = {'Personal Development', 'Discipline', 'Fitness', 'Productivity', 'Python', 'AI'}
    for i, post1 in enumerate(all_posts):
        for post2 in all_posts[i+1:]:
            shared_tags = set(post1.get('tags', [])) & set(post2.get('tags', []))
            shared_tags = shared_tags & significant_tags  # Only count significant tags
            if shared_tags:
                edges.append({
                    'source': f'post-{post1["slug"]}',
                    'target': f'post-{post2["slug"]}',
                    'type': 'shared-tag',
                    'tags': list(shared_tags),
                    'strength': 'weak'
                })

    # Project-to-project discipline connections
    for i, proj1 in enumerate(get_featured_projects_data()):
        for proj2 in get_featured_projects_data()[i+1:]:
            shared_disciplines = set(proj1.get('disciplines', [])) & set(proj2.get('disciplines', []))
            if shared_disciplines:
                edges.append({
                    'source': f'project-{proj1["id"]}',
                    'target': f'project-{proj2["id"]}',
                    'type': 'shared-discipline',
                    'disciplines': list(shared_disciplines),
                    'strength': 'medium'
                })

    return jsonify({
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'posts': len(post_nodes),
            'projects': len(project_nodes)
        }
    })

@app.route('/api/content/related')
def get_related_content():
    """
    Get all related content for a given item (by slug or project ID).
    Query parameters: type (post|project), id (slug or project_id)
    """
    from flask import request
    content_type = request.args.get('type', 'post')
    content_id = request.args.get('id')

    if not content_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    related = {
        'primary': None,
        'related_posts': [],
        'related_projects': [],
        'shared_disciplines': [],
        'shared_tags': []
    }

    if content_type == 'post':
        # Find the blog post
        all_posts = get_all_blog_posts()
        primary_post = next((p for p in all_posts if p['slug'] == content_id), None)

        if not primary_post:
            return jsonify({"error": "Post not found"}), 404

        related['primary'] = {
            'type': 'post',
            'title': primary_post.get('title'),
            'slug': primary_post['slug'],
            'disciplines': primary_post.get('disciplines', []),
            'tags': primary_post.get('tags', [])
        }

        # Find related projects
        related_project_ids = primary_post.get('related_projects', [])
        related_projects = [p for p in get_featured_projects_data() if p['id'] in related_project_ids]
        related['related_projects'] = [
            {
                'id': p['id'],
                'title': p['title'],
                'disciplines': p.get('disciplines', [])
            }
            for p in related_projects
        ]

        # Find posts with shared disciplines
        for post in all_posts:
            if post['slug'] == content_id:
                continue
            shared_disciplines = set(primary_post.get('disciplines', [])) & set(post.get('disciplines', []))
            if shared_disciplines:
                related['related_posts'].append({
                    'slug': post['slug'],
                    'title': post.get('title'),
                    'shared_disciplines': list(shared_disciplines)
                })

        # Find posts with shared significant tags
        significant_tags = {'Personal Development', 'Discipline', 'Fitness', 'Productivity', 'Python', 'AI'}
        for post in all_posts:
            if post['slug'] == content_id:
                continue
            shared_tags = set(primary_post.get('tags', [])) & set(post.get('tags', [])) & significant_tags
            if shared_tags and post['slug'] not in [p['slug'] for p in related['related_posts']]:
                related['related_posts'].append({
                    'slug': post['slug'],
                    'title': post.get('title'),
                    'shared_tags': list(shared_tags)
                })

        related['shared_disciplines'] = primary_post.get('disciplines', [])
        related['shared_tags'] = primary_post.get('tags', [])

    elif content_type == 'project':
        # Find the project
        primary_project = next((p for p in get_featured_projects_data() if p['id'] == content_id), None)

        if not primary_project:
            return jsonify({"error": "Project not found"}), 404

        related['primary'] = {
            'type': 'project',
            'title': primary_project['title'],
            'project_id': primary_project['id'],
            'disciplines': primary_project.get('disciplines', [])
        }

        # Find related blog posts
        all_posts = get_all_blog_posts()
        for post in all_posts:
            if content_id in post.get('related_projects', []):
                related['related_posts'].append({
                    'slug': post['slug'],
                    'title': post.get('title'),
                    'connection': 'direct-reference'
                })
            else:
                # Check for shared disciplines
                shared_disciplines = set(primary_project.get('disciplines', [])) & set(post.get('disciplines', []))
                if shared_disciplines:
                    related['related_posts'].append({
                        'slug': post['slug'],
                        'title': post.get('title'),
                        'shared_disciplines': list(shared_disciplines)
                    })

        # Find related projects
        for project in get_featured_projects_data():
            if project['id'] == content_id:
                continue
            shared_disciplines = set(primary_project.get('disciplines', [])) & set(project.get('disciplines', []))
            if shared_disciplines:
                related['related_projects'].append({
                    'id': project['id'],
                    'title': project['title'],
                    'shared_disciplines': list(shared_disciplines)
                })

        related['shared_disciplines'] = primary_project.get('disciplines', [])

    else:
        return jsonify({"error": "Invalid content type. Use 'post' or 'project'"}), 400

    return jsonify(related)

@app.route('/api/content/disciplines')
def get_discipline_map():
    """
    Get all content organized by discipline, showing how different content
    items share disciplines and create synergies.
    """
    all_posts = get_all_blog_posts()
    disciplines_map = {
        'code': {'posts': [], 'projects': [], 'connections': 0},
        'ai': {'posts': [], 'projects': [], 'connections': 0},
        'fitness': {'posts': [], 'projects': [], 'connections': 0},
        'meta': {'posts': [], 'projects': [], 'connections': 0}
    }

    # Organize posts by discipline
    for post in all_posts:
        for discipline in post.get('disciplines', []):
            if discipline in disciplines_map:
                disciplines_map[discipline]['posts'].append({
                    'slug': post['slug'],
                    'title': post['title'],
                    'date': post.get('date')
                })

    # Organize projects by discipline
    for project in get_featured_projects_data():
        for discipline in project.get('disciplines', []):
            if discipline in disciplines_map:
                disciplines_map[discipline]['projects'].append({
                    'id': project['id'],
                    'title': project['title']
                })

    # Count connections (synergies) - posts with multiple disciplines
    for post in all_posts:
        post_disciplines = set(post.get('disciplines', []))
        if len(post_disciplines) > 1:
            for discipline in post_disciplines:
                if discipline in disciplines_map:
                    disciplines_map[discipline]['connections'] += len(post_disciplines) - 1

    return jsonify(disciplines_map)

@app.route('/api/content/search')
def search_content():
    """
    Search across blog posts and projects by title, tags, or disciplines.
    Query parameters: q (search query), type (post|project|all)
    """
    from flask import request
    query = request.args.get('q', '').lower()
    search_type = request.args.get('type', 'all')

    if not query or len(query) < 2:
        return jsonify({"error": "Query too short. Minimum 2 characters."}), 400

    results = {'posts': [], 'projects': []}

    # Search blog posts
    if search_type in ['all', 'post']:
        all_posts = get_all_blog_posts()
        for post in all_posts:
            # Check title, excerpt, tags, disciplines
            title_match = query in post.get('title', '').lower()
            excerpt_match = query in post.get('excerpt', '').lower()
            tags_match = any(query in tag.lower() for tag in post.get('tags', []))
            disciplines_match = any(query in d.lower() for d in post.get('disciplines', []))

            if title_match or excerpt_match or tags_match or disciplines_match:
                match_type = 'title' if title_match else 'excerpt' if excerpt_match else 'tag' if tags_match else 'discipline'
                results['posts'].append({
                    'slug': post['slug'],
                    'title': post['title'],
                    'excerpt': post.get('excerpt'),
                    'match_type': match_type,
                    'disciplines': post.get('disciplines', []),
                    'tags': post.get('tags', [])
                })

    # Search projects
    if search_type in ['all', 'project']:
        for project in get_featured_projects_data():
            # Check title, description, technologies, disciplines
            title_match = query in project.get('title', '').lower()
            description_match = query in project.get('description', '').lower()
            tech_match = any(query in tech.lower() for tech in project.get('technologies', []))
            disciplines_match = any(query in d.lower() for d in project.get('disciplines', []))

            if title_match or description_match or tech_match or disciplines_match:
                match_type = 'title' if title_match else 'description' if description_match else 'tech' if tech_match else 'discipline'
                results['projects'].append({
                    'id': project['id'],
                    'title': project['title'],
                    'description': project.get('description'),
                    'match_type': match_type,
                    'disciplines': project.get('disciplines', []),
                    'technologies': project.get('technologies', [])
                })

    return jsonify({
        'query': query,
        'results': results,
        'total': len(results['posts']) + len(results['projects'])
    })


if __name__ == '__main__':
    # Use environment variable for debug mode (default: False for safety)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    port = int(os.getenv('FLASK_PORT', '8080'))
    host = os.getenv('FLASK_HOST', '127.0.0.1')

    app.logger.info(f"Starting application on {host}:{port} (debug={debug_mode})")
    app.run(debug=debug_mode, port=port, host=host)
