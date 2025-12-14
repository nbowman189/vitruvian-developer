# Authentication System Integration Plan

**Status**: IN PROGRESS
**Date**: December 14, 2024

## Overview

Integrate the existing authentication system (Flask-Login, user models, auth blueprints) into the running Docker application, replacing the standalone app.py with the factory pattern.

## Current State

### What Exists
- ✅ Complete auth system in `website/__init__.py` + `website/auth/` + `website/models/`
- ✅ User model with password hashing
- ✅ Login/logout/registration routes
- ✅ Flask-Login integration
- ✅ Database models
- ✅ Configuration in `config.py`
- ✅ Some blueprints already created (minimal)

### What's Running
- ❌ Standalone `app.py` with no auth, no database
- ❌ No database migrations initialized
- ❌ No login templates
- ❌ Private data accessible without authentication

## Migration Steps

### Phase 1: Application Structure ✅
- [x] Backup original app.py to app_standalone_backup.py
- [x] Create new minimal app.py that calls create_app()

### Phase 2: Route Migration (IN PROGRESS)
Need to add missing routes from app_standalone_backup.py to blueprints:

**Routes Already in Blueprints:**
- `/` - main_bp
- `/knowledge-graph` - main_bp
- `/insights` - main_bp
- `/api/projects` - api_projects_bp
- `/api/project/<name>` - api_projects_bp
- `/api/project/<name>/files` - api_projects_bp
- `/api/project/<name>/file/<path>` - api_projects_bp

**Routes Need to be Added:**
1. **main_bp** (`routes/main.py`):
   - `/project-case-study/<project_name>`
   - `/the-vitruvian-developer`
   - `/project/<project_name>` (with optional file_path)

2. **api_projects_bp** (`routes/api_projects.py`):
   - `/api/projects-metadata`
   - `/api/project/<name>/categorized-files`
   - `/api/project/<name>/summary`
   - `/api/featured-projects`
   - `/api/origin-story`

3. **health_bp** (`routes/health.py`):
   - `/health-and-fitness/graphs`
   - `/api/health-and-fitness/health_data`

4. **api_misc_bp** (`routes/api_misc.py`):
   - `/api/contact-info`
   - `/api/content/graph`
   - `/api/content/related`
   - `/api/content/disciplines`
   - `/api/content/search`

5. **api_monitoring_bp** (`routes/api_monitoring.py`):
   - `/api/health` (Docker health check)

6. **blog_bp** (`routes/blog.py`):
   - Already has routes but may need additions from app_standalone_backup.py

7. **api_blog_bp** (`routes/api_blog.py`):
   - Already has routes but may need additions from app_standalone_backup.py

### Phase 3: Configuration
- [ ] Add PROJECT_METADATA to config.py
- [ ] Add CONTACT_INFO to config.py
- [ ] Verify all environment variables are set

### Phase 4: Database Setup
- [ ] Initialize Flask-Migrate in Docker container
- [ ] Create initial migration for user tables
- [ ] Run migration to create tables
- [ ] Create initial admin user

### Phase 5: Templates
- [ ] Create login.html template
- [ ] Create register.html template
- [ ] Add login/logout links to base.html navigation
- [ ] Create user profile page template

### Phase 6: Access Control
- [ ] Identify routes that should require authentication
- [ ] Add `@login_required` decorator to private data routes
- [ ] Update `file_utils.py` to respect authentication
- [ ] Routes to protect:
  - `/api/project/<name>/file/<path>` (if file in /data/ directory)
  - `/api/health-and-fitness/health_data` (private metrics)
  - Any coaching or personal data endpoints

### Phase 7: Docker Updates
- [ ] Update Dockerfile to run database migrations on startup
- [ ] Update docker-compose.yml to ensure database is ready
- [ ] Add script to create initial admin user
- [ ] Update Gunicorn command to use `website:create_app()`

### Phase 8: Testing
- [ ] Test public routes work without authentication
- [ ] Test private routes redirect to login
- [ ] Test login/logout flow
- [ ] Test user registration
- [ ] Test protected API endpoints return 401 when not authenticated
- [ ] Test database persistence across container restarts

## Environment Variables Required

```bash
# Already in .env
SECRET_KEY=<generated>
POSTGRES_PASSWORD=<set>
POSTGRES_USER=postgres
POSTGRES_DB=primary_assistant
POSTGRES_HOST=db
POSTGRES_PORT=5432

# May need to add
FLASK_ENV=production
FLASK_DEBUG=False
```

## Files to Modify

1. ✅ `website/app.py` - Replace with factory pattern
2. `website/routes/main.py` - Add missing page routes
3. `website/routes/api_projects.py` - Add missing API routes
4. `website/routes/api_misc.py` - Add content graph APIs
5. `website/routes/api_monitoring.py` - Add health check
6. `website/routes/health.py` - Add graphs and health data API
7. `website/config.py` - Add PROJECT_METADATA and CONTACT_INFO
8. `website/templates/login.html` - CREATE
9. `website/templates/register.html` - CREATE
10. `website/templates/base.html` - Add auth navigation
11. `docker/Dockerfile` - Add migration commands
12. `docker-compose.yml` - Update command for Gunicorn

## Rollback Plan

If integration fails:
1. Stop containers: `docker compose down`
2. Restore backup: `mv website/app_standalone_backup.py website/app.py`
3. Rebuild: `docker compose up -d --build`

## Success Criteria

- [ ] Application starts with database connection
- [ ] Public routes accessible without login
- [ ] Private routes require authentication
- [ ] Login/logout works
- [ ] User can register new account
- [ ] Database persists across restarts
- [ ] No functionality lost from original app.py
