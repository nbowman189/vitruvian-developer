# Application Architecture - Phase 7 Refactoring & Phase 4 Dual-Server Implementation

## Overview

This document outlines the Flask application architecture including the Phase 7 modernization and Phase 4 implementation of a dual-server system for public portfolio and private workspace access. The website now consists of two separate Flask servers optimized for different purposes while sharing templates and static assets.

### Current Architecture (Phase 4 Update)
- **Public Server** (`app.py`, port 8080): Portfolio showcase with curated content from `/docs/` directories
- **Private Server** (`app-private.py`, port 8081): Personal workspace with full access to `/docs/` and `/data/` directories
- Shared assets: templates, static files, blog posts
- Simultaneous execution: Both servers can run at the same time without conflicts

## Directory Structure

```
website/
├── app.py                          # PUBLIC server (port 8080) - Portfolio showcase
├── app-private.py                  # PRIVATE server (port 8081) - Full workspace access
├── start-servers.sh                # Dual-server startup script
├── config.py                       # Centralized configuration
├── requirements.txt                # Python dependencies
│
├── PRIVATE_SERVER_SETUP.md        # Documentation for authentication upgrades (Options 2-4)
├── README-SERVERS.md              # Quick reference for both servers
├── ARCHITECTURE.md                # This file
│
├── routes/                         # Blueprint routes (modular endpoints, Phase 7)
│   ├── __init__.py                # Blueprint definitions
│   ├── main.py                    # Main page routes (/, /knowledge-graph, /insights)
│   ├── blog.py                    # Blog page routes (/blog/*, /blog/saved)
│   ├── health.py                  # Health routes (/health-and-fitness/graphs)
│   ├── api_blog.py                # Blog API endpoints (/api/blog/*)
│   ├── api_projects.py            # Projects API endpoints (/api/project/*)
│   └── api_misc.py                # Miscellaneous APIs (/api/health-and-fitness/*, /api/featured-projects, etc.)
│
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── file_utils.py              # File handling and parsing
│   │   ├── BlogPostParser              # Parse markdown with YAML front matter
│   │   ├── ProjectFileManager          # Handle project files (now supports allow_data_access flag)
│   │   └── HealthDataParser            # Parse health data from markdown tables
│   ├── error_handler.py           # Error handling and logging
│   │   ├── AppLogger                   # Centralized logging
│   │   ├── APIError                    # Base API error class
│   │   ├── NotFoundError               # 404 errors
│   │   ├── ValidationError             # 400 errors
│   │   ├── ServerError                 # 500 errors
│   │   ├── handle_api_errors()         # Decorator for error handling
│   │   └── log_request()               # Decorator for request logging
│   └── (other utilities)
│
├── templates/                      # Jinja2 templates (shared by both servers)
├── static/                         # Static assets (CSS, JS, shared by both servers)
├── blog/                           # Blog posts (markdown files, shared by both servers)
└── logs/                           # Application logs (created at runtime)
```

## Key Improvements

### 1. **Modular Architecture**
- **Blueprints**: Application logic separated into logical blueprints
  - `main_bp`: Core pages and static files
  - `blog_bp`: Blog-related page rendering
  - `health_bp`: Health tracking pages
  - `api_bp`: All REST API endpoints

- **Service Classes**: Business logic abstraction
  - `BlogAPI`: Blog data retrieval and operations
  - `ProjectsAPI`: Project file management
  - `MiscAPI`: Featured projects, health data, contact info

### 2. **Configuration Management**
- Centralized configuration in `config.py`
- Environment-specific configs (development, production, testing)
- Easy override via environment variables

### 3. **Error Handling**
- Custom error classes for different error types
- Decorators for automatic error handling on routes
- Centralized error response format
- Comprehensive logging to file and console

### 4. **Logging**
- Singleton `AppLogger` instance
- Logs stored in `logs/app.log`
- Request logging with IP, method, and user agent
- Error tracking with full stack traces

### 5. **Code Organization**
- Separation of concerns (routes, services, utilities)
- DRY principle with shared utility functions
- Reusable service classes
- Easy to test and maintain

## API Endpoints

### Page Routes (Traditional Rendering)
```
GET  /                           # Home page
GET  /knowledge-graph            # Knowledge graph visualization
GET  /insights                   # Reading insights dashboard
GET  /blog                       # Blog listing
GET  /blog/saved                 # Saved articles
GET  /blog/<slug>                # Individual blog article
GET  /health-and-fitness/graphs  # Health graphs page
GET  /static/<path>              # Static files
```

### API Endpoints (JSON Response)
```
# Blog API
GET  /api/blog/posts              # Get all blog posts
GET  /api/blog/posts/latest       # Get latest N posts
GET  /api/blog/post/<slug>        # Get specific post
GET  /api/blog/post/<slug>/related-projects

# Projects API
GET  /api/projects                # Get all projects
GET  /api/project/<name>          # Get GEMINI.md
GET  /api/project/<name>/files    # Get project files
GET  /api/project/<name>/file/<path>

# Health & Fitness API
GET  /api/health-and-fitness/health_data

# Content API
GET  /api/featured-projects       # Get featured projects
GET  /api/contact-info            # Get contact information
GET  /api/content/graph           # Get knowledge graph data
GET  /api/content/disciplines     # Get discipline info
GET  /api/content/related         # Get related content
```

## Configuration

### Environment Variables
```bash
FLASK_ENV=development|production|testing
FLASK_HOST=127.0.0.1              # Default: 127.0.0.1
FLASK_PORT=5000                   # Default: 5000
```

### Configuration Classes
- `Config`: Base configuration
- `DevelopmentConfig`: Debug enabled, auto-reload
- `ProductionConfig`: Debug disabled
- `TestingConfig`: Testing mode

## Error Handling Pattern

All API routes should use the `@handle_api_errors` decorator:

```python
@api_bp.route('/api/example', methods=['GET'])
@handle_api_errors
@log_request
def example_endpoint():
    # Your code here
    # Errors are automatically caught and formatted
    pass
```

Errors are automatically converted to JSON responses:
```json
{
    "error": "Error message",
    "status_code": 400
}
```

## Logging

Logs are written to `logs/app.log` with format:
```
2024-01-15 10:30:45,123 - app - INFO - GET /api/blog/posts - IP: 127.0.0.1
```

## Migration from Monolithic to Modular

The new architecture is backward compatible with the existing API. To switch to the new `app_refactored.py`:

1. Backup current `app.py`
2. Rename `app_refactored.py` to `app.py`
3. Update imports in any entry points
4. Test all endpoints

## Dual-Server Architecture (Phase 4 Implementation)

### Overview
The website now uses two separate Flask servers optimized for different purposes:

#### Public Portfolio Server (app.py - Port 8080)
- **Purpose**: Showcase curated portfolio content
- **Access Level**: Public-facing (safe to share)
- **File Visibility**: Only `/docs/` directories
- **Authentication**: None required
- **Use Cases**: Share with employers, clients, or public internet

#### Private Workspace Server (app-private.py - Port 8081)
- **Purpose**: Personal workspace with full file access
- **Access Level**: Local-only (localhost)
- **File Visibility**: Both `/docs/` and `/data/` directories
- **Authentication**: None required (localhost security)
- **Use Cases**: Personal health metrics, coaching notes, working documents

### Shared Components
Both servers share:
- Same `/templates/` directory for consistent UI
- Same `/static/` directory for CSS and JavaScript
- Same `/blog/` directory for blog posts
- Same utility functions in `utils/`

### File Access Control
Implemented via `ProjectFileManager` in `utils/file_utils.py`:

```python
# Public server (app.py)
manager = ProjectFileManager(PROJECT_ROOT, PROJECT_DIRS, allow_data_access=False)
# Only finds files in /docs/ directories

# Private server (app-private.py)
manager = ProjectFileManager(PROJECT_ROOT, PROJECT_DIRS, allow_data_access=True)
# Finds files in both /docs/ and /data/ directories
```

### Running Both Servers

#### Recommended: Use startup script
```bash
cd website/
./start-servers.sh
# Starts both servers automatically
```

#### Manual: Separate terminals
```bash
# Terminal 1 - Public portfolio
python3 app.py

# Terminal 2 - Private workspace
python3 app-private.py
```

#### Single server only
```bash
# Public only
python3 app.py                    # Port 8080

# Private only
python3 app-private.py            # Port 8081
```

### Environment Variables
Both servers respect the same environment variables:

```bash
FLASK_HOST=127.0.0.1      # Default: 127.0.0.1 (localhost only for private)
FLASK_PORT=8080           # Default: 8080 (public), 8081 (private)
FLASK_DEBUG=False         # Default: False
```

## Running the Application

```bash
# Both servers (Recommended)
cd website/
./start-servers.sh

# Public portfolio only
python3 app.py

# Private workspace only
python3 app-private.py

# Production deployment
FLASK_ENV=production python3 app.py

# Custom host/port
FLASK_HOST=0.0.0.0 FLASK_PORT=8000 python3 app.py
```

### Future Authentication Options
See `PRIVATE_SERVER_SETUP.md` for documented upgrade paths:
- **Option 2**: Basic HTTP authentication with password
- **Option 3**: Session-based login interface
- **Option 4**: Production-grade OAuth/JWT implementation

## Future Enhancements

### Phase 7.4: Caching & Performance
- Redis caching for frequently accessed data
- Query result caching
- Static asset caching headers
- Pagination for large datasets

### Phase 8: Launch
- Deployment configuration
- Docker containerization
- CI/CD pipeline
- Performance optimization
- Security hardening

## Benefits

1. **Maintainability**: Code is organized by feature
2. **Testability**: Each module can be tested independently
3. **Scalability**: Easy to add new features and endpoints
4. **Reliability**: Comprehensive error handling and logging
5. **Flexibility**: Configuration-driven behavior
6. **Debugging**: Detailed logging for troubleshooting

## Code Quality

- Type hints recommended for better IDE support
- Docstrings for all functions and classes
- Error handling at all levels
- Input validation before processing
- Security checks (path traversal prevention)
