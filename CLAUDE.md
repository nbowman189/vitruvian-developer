# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CURRENT SESSION STATUS

**For latest session notes and status, see:** `SESSION_NOTES.md` in project root

**Current Session (December 18, 2024 - Evening):**
- ✅ Fixed blog functionality: JavaScript now handles paginated API responses
- ✅ Updated blog.js, blog-article.js, saved-articles.js to extract `data.items`
- ✅ Added blog.js script to homepage for blog posts display
- ✅ Cleaned up CLAUDE.md documentation (829→591 lines, removed obsolete content)
- ✅ Committed and ready to push: commit hash `79f80d0`

**Deployment Process:**
1. **Local Changes:**
   - Make code changes
   - Test locally if possible
   - Commit: `git add -A && git commit -m "description"`
   - Push: `git push origin main`

2. **Remote Deployment (CRITICAL - Code is baked into Docker image):**
   ```bash
   # Use the deployment script:
   ./scripts/deploy-remote.sh

   # OR manual process:
   cd /home/nathan/vitruvian-developer
   git pull origin main
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml stop web
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml rm -f web
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d --build web
   ```

3. **NEVER use `docker-compose restart`** - it doesn't load new code!

4. **After JavaScript changes:** Purge Cloudflare cache or enable Development Mode

**Known Issues:**
1. **Code Not Mounted as Volume:** Website code is baked into Docker image, so containers MUST be rebuilt (not just restarted) for code changes to take effect
2. **Cloudflare Cache:** Must purge or enable Development Mode after JavaScript/CSS updates

---

## Project Overview

This is a personal project management system with three main components:

1. **Website** (`/website`): A Flask-based web dashboard with authentication system
2. **Scripts** (`/scripts`): Data processing and visualization utilities
3. **Content Directories**: `Health_and_Fitness` and `AI_Development` folders containing markdown files and project data

Each content directory has a `GEMINI.md` file that provides context-specific information for that area.

### New in This Build:
- ✅ Complete authentication system (Flask-Login, bcrypt, CSRF protection)
- ✅ PostgreSQL database with 14 models (User, Session, Health, Workout, Nutrition, Coaching, Behavior)
- ✅ RESTful API layer with 43+ endpoints across 7 modules
- ✅ **Dashboard with real-time data visualization** (December 17, 2024)
  - 4 quick stat cards (weight, workout, coaching, nutrition)
  - 3 Chart.js interactive charts (trends and adherence)
  - Activity feed aggregating all user data
  - Quick action buttons
- ✅ **Dynamic Behavior Tracker System** (NEW - January 2, 2026)
  - Database-backed habit tracking with flexible behavior definitions
  - Daily completion checklist with binary Yes/No marking
  - Streak calculation and compliance analysis
  - Chart.js visualization showing 30-day completion trends
  - Full AI integration for creating behaviors and logging completion
- ✅ **AI Coach Historical Data Access** (NEW - January 2, 2026)
  - AI can READ 6 types of historical data (health, workout, nutrition, goals, coaching, progress)
  - Data-driven coaching based on actual user metrics and trends
  - Automatic query execution with context injection
- ✅ Virtual database-driven pages (5 pages that generate content from database)
- ✅ Database migrations with Flask-Migrate/Alembic
- ✅ Admin user creation script
- ✅ Automated deployment script with health checks
- ✅ Docker containers building and running locally
- ⚠️ Remote deployment debugging needed

## Common Development Commands

### Running the Website

#### Local Development (Non-Docker)
```bash
cd /Users/nathanbowman/primary-assistant/website
python3 app.py
```
Runs the Flask development server on `http://localhost:8080`

**Note**: Port 8080 is used instead of default 5000 due to macOS AirTunes service conflict.

### Docker Deployment (Local or Remote)

#### Local Development with Docker:
```bash
cd /Users/nathanbowman/primary-assistant
docker-compose up -d
```
Services will be available at:
- **Web Application**: `http://localhost:8001` (Docker port mapping: 8001→8000)
- **PostgreSQL**: localhost:5432
- **Nginx**: localhost:80

#### Remote Server Deployment:
```bash
# Use remote override configuration for HTTP-only nginx (Cloudflare handles SSL)
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d
```

#### Database Setup:
```bash
# Run migrations
docker-compose exec web flask db upgrade

# Create admin user (username: admin, password: admin123)
docker-compose exec web python website/scripts/create_admin_user.py
```

#### Useful Docker Commands:
```bash
# View logs
docker-compose logs -f web

# Restart services
docker-compose restart web

# Rebuild after code changes
docker-compose down
docker-compose up -d --build

# Clean restart (removes volumes/database)
docker-compose down -v
docker-compose up -d --build
```

#### Deploying Static File Updates to Remote Server:

Due to Docker build caching issues with static files, use this workflow:

```bash
# 1. Pull latest code
git pull origin main

# 2. Copy updated files directly to running container
docker cp website/static/js/blog.js primary-assistant-web:/app/website/static/js/blog.js
docker cp website/templates/index.html primary-assistant-web:/app/website/templates/index.html

# 3. Fix file permissions
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T -u root web \
  sh -c "chown -R appuser:appuser /app/website/static/ /app/website/templates/ && \
         chmod -R 644 /app/website/static/js/*.js && \
         chmod 644 /app/website/templates/*.html"

# 4. Restart web container
docker-compose -f docker-compose.yml -f docker-compose.remote.yml restart web

# 5. CRITICAL: Purge Cloudflare cache or enable Development Mode for 3 hours
```

### SSL/TLS Configuration

**IMPORTANT: This project does NOT use SSL certificates on nginx.**

- **Cloudflare handles all SSL termination** - nginx only listens on HTTP port 80
- nginx sets `X-Forwarded-Proto: https` to tell Flask the original request was HTTPS
- No Let's Encrypt, no SSL certificates, no SSL configuration needed
- See `docs/deployment/SSL_CONFIGURATION.md` for complete details

### Authentication System

The application now has a complete authentication system:

**Login:** `http://localhost:8080/auth/login`
- Default admin credentials: `admin` / `admin123`

**Features:**
- Session-based authentication with Flask-Login
- Password hashing with bcrypt
- CSRF protection on all forms
- Protected routes for private data
- Virtual database pages (visible only when logged in)

**Virtual Database Pages (require authentication):**
1. Health Metrics Log - `/api/project/Health_and_Fitness/file/data/health-metrics-log.md`
2. Workout Log - `/api/project/Health_and_Fitness/file/data/workout-log.md`
3. Meal Log - `/api/project/Health_and_Fitness/file/data/meal-log.md`
4. Progress Photos - `/api/project/Health_and_Fitness/file/data/progress-photos.md`
5. Coaching Sessions - `/api/project/Health_and_Fitness/file/data/coaching-sessions.md`

These pages are dynamically generated from the PostgreSQL database and only appear in navigation when logged in.

### Health Data Processing
Update the check-in-log.md from HealthKit export:
```bash
python scripts/parse_health_data.py
```

### Generating Progress Graphs
Create PNG charts from health data:
```bash
python scripts/generate_progress_graphs.py
```

### Starting Graph Server
Legacy graph visualization server (port 8000):
```bash
python scripts/graph_server.py
```

## Architecture

### Website Application

**File**: `website/app.py`

The Flask application uses the **app factory pattern** with `create_app()` for modular, testable architecture.

**Structure:**
- `/website/__init__.py` - App factory with configuration
- `/website/routes/` - Blueprint modules for web pages (main, blog, health)
- `/website/api/` - Modular API endpoints (health, nutrition, workout, coaching, activity, ai_coach)
- `/website/auth/` - Complete authentication system (routes, forms, decorators)
- `/website/services/` - External services (Gemini AI integration)
- `/website/models/` - SQLAlchemy database models
- `/website/utils/` - Utility functions and helpers

### Main Application Routes (app.py)

The Flask app serves as a dashboard to browse all projects, markdown files, and blog posts:

**Web Routes (Blueprints in `/website/routes/`):**
- `main.py` - Homepage, dashboard, project pages
- `blog.py` - Blog listing and individual articles
- `health.py` - Health & fitness specific pages, graphs visualization

**Authentication Routes (`/website/auth/routes.py`):**
- `/auth/login` - User login with CSRF protection
- `/auth/register` - New user registration
- `/auth/logout` - Session logout
- `/api/auth/status` - Current authentication status (JSON)

**API Endpoints (Modular structure in `/website/api/`):**
- `health.py` - Health metrics CRUD operations
- `nutrition.py` - Meal log and nutrition tracking
- `workout.py` - Workout sessions and exercise logging
- `coaching.py` - Coaching sessions and goal management
- `behavior.py` - Behavior tracking CRUD, analytics, and compliance (13 endpoints)
- `activity.py` - Activity feed aggregation across all data types
- `ai_coach.py` - AI coaching conversation endpoints with function calling (Gemini integration)

**API Routes - Projects:**
- `/api/projects` - List of available projects
- `/api/project/<name>` - Project GEMINI.md content
- `/api/project/<name>/files` - Project markdown files (authentication-aware)
- `/api/project/<name>/file/<path>` - Specific file content (protected)

**API Routes - Blog:**
- `/api/blog/posts` - All blog posts (sorted newest first)
- `/api/blog/posts/latest?limit=N` - Latest N posts
- `/api/blog/post/<slug>` - Specific blog post with HTML content

#### Custom File Ordering
The `HEALTH_FITNESS_FILE_ORDER` list at the top of `app.py` defines the desired file order for the Health_and_Fitness project:
- `fitness-roadmap.md`
- `Full-Meal-Plan.md`
- `Shopping-List-and-Estimate.md`
- `check-in-log.md`
- `progress-check-in-log.md`

The `/api/project/<name>/files` endpoint applies this custom sorting when returning files for the Health_and_Fitness project.

The app auto-reloads templates and parses the check-in-log.md table format (pipe-separated with date, weight, bodyfat columns).

### Website Frontend

#### Templates (28 total in `/website/templates/`)
**Core Pages:**
- `base.html` - Base template with navbar and common structure
- `index.html` - Main landing page with hero, portfolio, blog, contact
- `dashboard.html` - Main dashboard with stats, charts, activity feed
- `project.html` - Project display page

**Feature Pages:**
- `health_metrics.html` - Health tracking page
- `nutrition_meals.html` - Nutrition and meal logging
- `workout_workouts.html` - Workout session tracking
- `coaching_sessions.html` - Coaching session management
- `graphs.html` - Health & Fitness graphs (Chart.js visualizations)

**Blog:**
- `blog_list.html` - Blog archive with filtering
- `blog_article.html` - Individual blog post view

**Admin & Auth:**
- `/auth/` subdirectory - Login, register, profile templates
- `/admin/` subdirectories - Management interfaces for all data types

#### JavaScript Files (21 total in `/website/static/js/`)
**Core:**
- `utils.js` - Shared utility functions (title formatting, date utils)
- `common.js` - Common functionality across pages
- `script.js` - Main application logic, navigation, project display

**Page-Specific:**
- `dashboard.js` - Dashboard with Chart.js visualizations, stats cards
- `health.js` - Health metrics page functionality
- `nutrition.js` - Nutrition tracking interface
- `workout.js` - Workout logging interface
- `coaching.js` - Coaching session management
- `graphs.js` - Health graphs page (Chart.js)
- `project.js` - Project page functionality

**Blog:**
- `blog.js` - Blog listing and homepage integration
- `blog-article.js` - Individual article page

**Advanced Features:**
- `ai-coach.js` - AI coaching conversation interface (Gemini)
- `insights.js` - Data insights and analytics
- `recommendation-engine.js` - Personalized recommendations
- `recommendation-widget.js` - Recommendation UI components
- `analytics-service.js` - Analytics tracking
- `knowledge-graph.js` - Knowledge graph visualization
- `saved-articles.js` - Saved content management
- `design-system.js` - Design system utilities

#### CSS (in `/website/static/css/`)
- `style.css` - Complete responsive design system with CSS variables, component styling, mobile breakpoints

### Navigation System

The website features a modern navigation system:

**Main Navigation:**
- Fixed navbar with authentication status
- Dashboard link for logged-in users
- Project and blog navigation

**Dashboard (authenticated users):**
- Quick stat cards (health, workout, nutrition, coaching)
- Interactive Chart.js visualizations (weight trend, workout volume, nutrition adherence, behavior completion)
- Daily behavior tracker checklist with streak tracking and compliance stats
- Activity feed aggregating all user data
- Quick action buttons for data entry

**Project Pages:**
- Dynamic project display with markdown rendering
- Custom file ordering for Health & Fitness project
- Responsive layout with mobile support

### Scripts

**`parse_health_data.py`**: Parses Apple HealthKit XML export files
- Extracts weight (HKQuantityTypeIdentifierBodyMass) and body fat % (HKQuantityTypeIdentifierBodyFatPercentage)
- Merges new data with existing entries in check-in-log.md
- Sorts entries chronologically
- Input: `Health_and_Fitness/export.xml`
- Output: Updates `Health_and_Fitness/check-in-log.md`

**`generate_progress_graphs.py`**: Creates matplotlib visualizations
- Parses the check-in-log.md markdown table
- Generates weight and body fat percentage charts as PNG files
- Uses pandas for data manipulation
- Output: `Health_and_Fitness/generated_html/weight_chart.png` and `bodyfat_chart.png`

**`graph_server.py`**: Simple HTTP server for legacy graph visualization
- Serves health data as JSON at `/data` endpoint
- Renders markdown files as HTML from `Health_and_Fitness/` directory
- Port 8000

**`generate_htmls.py`** and **`generate_pdfs.py`**: Convert markdown to HTML/PDF
- Style markdown with embedded CSS
- Useful for exporting plans and documentation

### Database Models

The application uses PostgreSQL with 14 models across 8 files (located in `website/models/`):

**Authentication Models:**
- `User` (`user.py`) - User accounts with bcrypt password hashing
- `UserSession` (`session.py`) - Login session tracking with expiry

**Health & Fitness Models:**
- `HealthMetric` (`health.py`) - Weight, body fat %, BMI tracking (field: `recorded_date`)
- `WorkoutSession` (`workout.py`) - Workout sessions (field: `session_date`)
- `ExerciseLog` (`workout.py`) - Individual exercises within workout sessions
- `ExerciseDefinition` (`workout.py`) - Exercise reference data and metadata
- `MealLog` (`nutrition.py`) - Daily nutrition tracking (field: `meal_date`, macros: `protein_g`, `carbs_g`, `fat_g`)
- `CoachingSession` (`coaching.py`) - Coaching notes and feedback (field: `session_date`)
- `UserGoal` (`coaching.py`) - Goal tracking and progress
- `ProgressPhoto` (`coaching.py`) - Progress photos with metadata (field: `photo_date`)

**Behavior Tracking Models:**
- `BehaviorDefinition` (`behavior.py`) - User-defined behavior categories for tracking (field: `name`, `category`, `target_frequency`)
- `BehaviorLog` (`behavior.py`) - Daily behavior completion tracking (field: `tracked_date`, `completed`)

**AI Integration Models:**
- `ConversationLog` (`conversation.py`) - AI coaching conversation history (Gemini integration)

**Important:** All models use specific date field names (`recorded_date`, `session_date`, `meal_date`, `photo_date`, `tracked_date`) not generic `date` field.

**Database Migrations:**
- Location: `website/migrations/versions/`
- Initial migration: `b72667ea0290_initial_migration_user_session_health_.py`
- Run migrations: `docker-compose exec web flask db upgrade`

### Data Format

**Check-in-log.md table format**:
```
| Date | Weight (lbs) | Body Fat % | Notes |
| :--------- | :----------- | :--------- | :---------------------------------- |
| 2024-11-14 | 175.5 | 22.3 | |
```

The parsing expects dates in YYYY-MM-DD format, numeric values for weight and body fat, and uses "None" or "N/A" for missing values.

### Project Directory Structure

Projects follow a consistent, organized structure to separate public documentation from working files:

**Health_and_Fitness Project:**
```
Health_and_Fitness/
├── _project_summary.md              # Case study narrative (auto-discovered as featured project)
├── GEMINI.md                        # Context file for Claude
├── .gitignore                       # Ignore data/ and generated/ directories
├── docs/                            # [PUBLIC] Curated documentation
│   ├── README.md                    # Overview of public docs
│   ├── fitness-roadmap.md           # Phased progression plan
│   ├── Full-Meal-Plan.md            # Nutrition strategy
│   └── Shopping-List-and-Estimate.md # Grocery list
├── data/                            # [PRIVATE] Working logs and data
│   ├── check-in-log.md              # Weight/body fat tracking
│   ├── exercise-log.md              # Workout performance log
│   ├── Coaching_sessions.md         # Coaching feedback and plans
│   └── exports/
│       └── export.xml               # HealthKit export (1.2GB)
└── generated/                       # [OUTPUT] Generated artifacts
    ├── progress-graphs/
    ├── weight_chart.png
    └── bodyfat_chart.png
```

**AI_Development Project:**
```
AI_Development/
├── _project_summary.md              # Case study narrative (auto-discovered as featured project)
├── GEMINI.md                        # Context file for Claude
├── .gitignore                       # Ignore OS files
├── docs/                            # [PUBLIC] Curated educational content
│   ├── README.md                    # Overview of public docs
│   └── curriculum.md                # Four-stage AI learning curriculum
└── reference/                       # [REFERENCE] Supporting materials
    ├── personas-reference.md        # Index to My-personas.md
    ├── curriculum_tasks.md          # Task-oriented curriculum tracking
    └── brand-project-review-gemini.md
```

**Project Root:**
```
primary-assistant/
├── My-personas.md                   # [UNIVERSAL] Detailed personas for AI interactions
├── CLAUDE.md                        # This file
├── Health_and_Fitness/              # See structure above
├── AI_Development/                  # See structure above
└── website/                         # Flask application
```

**Key Points:**
- **docs/** directories contain public, curated content for portfolio display
- **data/** directories (Health_and_Fitness only) contain working files and logs excluded from portfolio
- **_project_summary.md** files automatically become featured projects (no hardcoded list needed)
- **.gitignore** files prevent large files and working data from being committed
- **My-personas.md** lives at project root for easy reference during Claude Code sessions
- All markdown file discovery scans **docs/** directories when available, falling back to project root for backwards compatibility

### Documentation Organization

The project uses a centralized documentation structure to reduce root directory clutter:

```
primary-assistant/
├── CLAUDE.md                        # This file - project guide for Claude Code
├── GEMINI.md                        # AI context file
├── My-personas.md                   # AI interaction personas
├── README.md                        # Main project readme
├── CONTRIBUTING.md                  # Contributing guide
├── DOCKER_README.md                 # Complete Docker implementation guide
├──
├── docs/                            # [NEW] Organized documentation
│   ├── database/                    # Database architecture docs
│   │   ├── INDEX.md                 # Navigation guide
│   │   ├── README.md                # Complete database guide (650+ lines)
│   │   ├── SCHEMA.md                # Visual ER diagrams and relationships
│   │   └── IMPLEMENTATION.md        # Implementation summary
│   │
│   ├── website/                     # Website design and UX docs
│   │   ├── README.md                # Website docs index
│   │   ├── UX_ANALYSIS.md           # Project pages UX analysis (16K)
│   │   └── PROJECT_LAYOUT.md        # Project structure updates
│   │
│   ├── planning/                    # Strategic planning documents
│   │   ├── README.md                # Planning docs index
│   │   ├── PROJECT_IMPLEMENTATION_PLAN.md  # 7-phase refactoring plan (28K)
│   │   ├── WEBSITE_REBUILD_PLAN.md  # Website modernization strategy
│   │   └── NARRATIVE_QA.md          # Brand narrative Q&A
│   │
│   └── personal/                    # Personal professional documents
│       ├── README.md                # Personal docs index
│       ├── resume.md                # Professional resume
│       └── brand-review.md          # Brand portfolio review
│
└── archive/                         # [NEW] Historical documentation
    ├── README.md                    # Archive index
    ├── IMPLEMENTATION_COMPLETE.md   # Completed implementation records
    ├── IMPLEMENTATION_SUMMARY.md    # Implementation summaries
    ├── VITRUVIAN_BRANDING_IMPLEMENTATION.md
    ├── SESSION_WRAP_UP.md           # Session notes
    ├── QUICK_REFERENCE.md           # Historical quick reference
    ├── WEBSITE_STATUS_SUMMARY.md    # Website status snapshots
    └── PHASE_3_DELIVERABLES_CHECKLIST.md
```

**Documentation Quick Links:**
- **Database**: See `docs/database/INDEX.md` for complete database documentation
- **Website UX**: See `docs/website/README.md` for design and UX analysis
- **Planning**: See `docs/planning/README.md` for strategic plans
- **Docker**: See `DOCKER_README.md` in root for complete containerization guide
- **Historical**: See `archive/README.md` for past implementation records

### Documentation Quick Links (Updated December 2024)

- **Session Notes**: See `SESSION_NOTES.md` in root for current status and next session pickup point
- **Remote Deployment**: See `docs/deployment/REMOTE_DEPLOYMENT.md` for deployment troubleshooting
- **Verification Guide**: See `docs/website/VERIFICATION_GUIDE.md` for testing authentication
- **Database**: See `docs/database/INDEX.md` for complete database documentation
- **Website UX**: See `docs/website/README.md` for design and UX analysis
- **Planning**: See `docs/planning/README.md` for strategic plans (including `AUTH_INTEGRATION_PLAN.md`)
- **Docker**: See `DOCKER_README.md` in root for complete containerization guide
- **Historical**: See `archive/README.md` for past implementation records

### Website File Structure

```
website/
├── __init__.py                     # App factory with create_app()
├── app.py                          # Main application entry point
├── config.py                       # Configuration management
├── routes/                         # Blueprint modules for web pages
│   ├── main.py                     # Homepage, dashboard, projects
│   ├── blog.py                     # Blog pages
│   └── health.py                   # Health & fitness pages
├── api/                            # Modular API endpoints
│   ├── health.py                   # Health metrics API
│   ├── nutrition.py                # Nutrition tracking API
│   ├── workout.py                  # Workout logging API
│   ├── coaching.py                 # Coaching sessions API
│   ├── activity.py                 # Activity feed API
│   └── ai_coach.py                 # AI coaching API (Gemini)
├── auth/                           # Authentication system
│   ├── routes.py                   # Auth routes (login, register, logout)
│   ├── forms.py                    # WTForms with CSRF protection
│   └── decorators.py               # Custom auth decorators
├── models/                         # SQLAlchemy models (12 models)
│   ├── user.py                     # User authentication
│   ├── session.py                  # User sessions
│   ├── health.py                   # HealthMetric
│   ├── workout.py                  # WorkoutSession, ExerciseLog, ExerciseDefinition
│   ├── nutrition.py                # MealLog
│   ├── coaching.py                 # CoachingSession, UserGoal, ProgressPhoto
│   └── conversation.py             # ConversationLog (AI chat)
├── services/                       # External service integrations
│   └── gemini_service.py           # Google Gemini AI integration
├── utils/                          # Utility functions
│   ├── file_utils.py               # File management utilities
│   └── (other helpers)
├── templates/                      # Jinja2 templates (28 files)
│   ├── base.html                   # Base template
│   ├── index.html                  # Landing page
│   ├── dashboard.html              # Main dashboard
│   ├── auth/                       # Authentication templates
│   ├── admin/                      # Admin management interfaces
│   └── (feature-specific templates)
├── static/                         # Static assets
│   ├── css/
│   │   └── style.css               # Main stylesheet
│   ├── js/                         # JavaScript (21 files)
│   │   ├── dashboard.js            # Dashboard functionality
│   │   ├── ai-coach.js             # AI coaching interface
│   │   └── (other page scripts)
│   └── images/
│       ├── hero-section.jpg
│       ├── profile/
│       ├── blog/
│       └── projects/
├── blog/                           # Blog post markdown files
│   └── (blog posts with YAML frontmatter)
├── migrations/                     # Flask-Migrate database migrations
└── requirements.txt                # Python dependencies
```

## Key Dependencies

- Flask (web framework)
- markdown / markdown2 (markdown rendering)
- pandas (data manipulation)
- matplotlib (graph generation)
- weasyprint (PDF generation)
- ElementTree (XML parsing, standard library)

Install with:
```bash
pip install -r scripts/requirements.txt
```

## Important Notes

### Website Design & UI
- Modern, professional design using CSS variables for consistent theming
- Responsive layout that adapts to mobile, tablet, and desktop screens
- Fixed top navbar for constant project navigation
- Project navigation bar displays file links as horizontal tabs with title case formatting
- Active page/file is visually highlighted with color and underline
- Smooth hover effects and transitions throughout the interface

### Development
- The website config has `TEMPLATES_AUTO_RELOAD = True` for development convenience
- Flask app runs in debug mode by default (app.py line 107)
- All markdown files are discovered dynamically from `AI_Development` and `Health_and_Fitness` directories
- The health data routes expect a table-format markdown file with pipe separators

## Development Notes

### Authentication & Security
- Session-based authentication with Flask-Login
- bcrypt password hashing (12 rounds)
- CSRF protection enabled on all forms
- 24-hour session expiry for security
- Database-backed session management

### Data Import & Management
- Data import scripts in `/scripts/` for markdown data migration
- Database rebuild script: `scripts/rebuild_database.sh`
- Backup script: `scripts/backup-database.sh`
- Use `docker cp` to update scripts in running containers

### Deployment Considerations
- **Local Development**: Use `python3 app.py` on port 8080
- **Docker Deployment**: Use `docker-compose up -d` with nginx on port 80/443
- **Remote Deployment**: Include `-f docker-compose.remote.yml` for Cloudflare SSL termination
- **Cache Management**: Purge Cloudflare cache after JavaScript updates

## Feature Documentation

### Behavior Tracker System

The behavior tracker provides database-backed habit tracking with full dashboard and AI integration.

**Database Models** (`website/models/behavior.py`):
- `BehaviorDefinition` - User-defined behavior categories
  - Fields: `name`, `description`, `category` (enum), `icon` (Bootstrap class), `color` (hex), `display_order`, `target_frequency` (1-7 days/week), `is_active`
  - Soft delete pattern preserves historical data
  - Unique constraint on (user_id, name)
- `BehaviorLog` - Daily completion tracking
  - Fields: `tracked_date`, `completed` (boolean), `notes`
  - Unique constraint on (user_id, behavior_definition_id, tracked_date)

**API Endpoints** (`website/api/behavior.py` - 13 endpoints):

*Behavior Definition Management:*
- `GET /api/behavior/definitions` - List user's behavior definitions
- `POST /api/behavior/definitions` - Create new behavior definition
- `GET /api/behavior/definitions/<id>` - Get specific definition
- `PUT /api/behavior/definitions/<id>` - Update definition
- `DELETE /api/behavior/definitions/<id>` - Soft delete (set is_active=false)
- `PUT /api/behavior/definitions/reorder` - Bulk update display_order

*Behavior Logging:*
- `GET /api/behavior/logs` - Query logs with filters (start_date, end_date, behavior_id)
- `POST /api/behavior/logs` - Create/update behavior log for a date
- `GET /api/behavior/logs/today` - Get today's behavior checklist
- `POST /api/behavior/logs/bulk` - Bulk update multiple behaviors for a date

*Analytics:*
- `GET /api/behavior/stats` - Summary statistics (completion rates, streaks, trends)
- `GET /api/behavior/trends` - Trend data for Chart.js (time series per behavior)
- `GET /api/behavior/compliance` - Plan compliance analysis (actual vs. target frequency)

**Dashboard Integration**:
- Daily behavior checklist with checkboxes (dashboard.html:161-210)
- 3 stat cards showing weekly completion rate, best streak, and current streak
- Chart.js multi-line chart showing 30-day completion trends per behavior
- Real-time updates when behaviors are marked complete/incomplete
- Manage behaviors button for future CRUD interface

**JavaScript** (`website/static/js/dashboard.js`):
- `initializeBehaviorTracker()` - Main initialization
- `loadTodaysBehaviors()` - Fetch and render today's checklist
- `toggleBehavior()` - Mark behavior complete/incomplete with API call
- `loadBehaviorStats()` - Fetch and display summary statistics
- `createBehaviorTrendChart()` - Chart.js visualization of completion trends

**CSS** (`website/static/css/style.css`):
- `.dashboard-behaviors` - Section layout
- `.behavior-checklist` - Card container with loading/empty/error states
- `.behavior-item` - Individual checkbox rows with hover effects
- `.behavior-checkbox` - Styled checkboxes with strikethrough on completion
- `.behavior-stat-card` - Grid layout for stat cards (responsive)

### AI Coach Function Calling

The AI coach uses Gemini's function calling to both READ and WRITE data.

**Function Schemas** (`website/utils/ai_coach_tools.py`):

*WRITE Functions (suggest records to create):*
1. `create_health_metric` - Log weight, body fat, measurements, wellness
2. `create_meal_log` - Track nutrition and macros
3. `create_workout` - Record workout sessions with exercises
4. `create_coaching_session` - Save coaching discussion and action items
5. `create_behavior_definition` - Create new trackable behavior
6. `log_behavior` - Mark behavior as completed for a date

*READ Functions (query historical data):*
1. `get_recent_health_metrics` - Query weight, body fat, trends (7-90 days)
2. `get_workout_history` - Review recent workout sessions (7-30 days)
3. `get_nutrition_summary` - Query meals, macros, adherence (7-30 days)
4. `get_user_goals` - View active/completed goals and progress
5. `get_coaching_history` - Review previous coaching sessions (up to 20)
6. `get_progress_summary` - Comprehensive overview across all data types (30-90 days)
7. `get_behavior_tracking` - Query behavior completion history and streaks (7-30 days)
8. `get_behavior_plan_compliance` - Analyze adherence to target frequencies (week/month)

**AI Handlers** (`website/api/ai_coach.py`):

*WRITE Handlers (save AI-suggested records):*
- `_save_health_metric()` - Validates date, creates HealthMetric
- `_save_meal_log()` - Validates date and meal_type enum, creates MealLog
- `_save_workout()` - Validates date and session_type, creates WorkoutSession with ExerciseLogs
- `_save_coaching_session()` - Creates CoachingSession with self-referential coach_id
- `_save_behavior_definition()` - Validates category, checks duplicates, creates BehaviorDefinition
- `_save_behavior_log()` - Finds behavior by name, creates/updates BehaviorLog

*READ Handlers (execute data queries):*
- `_query_health_metrics()` - Queries HealthMetric, calculates trends, returns AI summary
- `_query_workout_history()` - Queries WorkoutSession, aggregates types and duration
- `_query_nutrition_summary()` - Queries MealLog, calculates daily averages
- `_query_user_goals()` - Queries UserGoal, groups by type
- `_query_coaching_history()` - Queries CoachingSession, returns recent sessions
- `_query_progress_summary()` - Aggregates all data types using other handlers
- `_query_behavior_tracking()` - Queries BehaviorLog, calculates streaks and completion rates
- `_query_behavior_compliance()` - Analyzes actual vs. target frequency, provides status and recommendations

**Automatic READ Execution**:
When AI calls a READ function (name starts with 'get_'), the `/message` endpoint:
1. Detects the READ function call
2. Executes the corresponding query handler immediately
3. Injects results as system message into conversation context
4. Gets AI's final data-informed response
5. Returns response to user with embedded context

This enables the AI to provide data-driven coaching based on actual user metrics instead of operating on conversation memory alone.

## Historical Documentation

For detailed implementation history, design decisions, and phase-by-phase development notes, see:
- `/archive/` - Historical implementation records and session notes
- `/docs/planning/` - Strategic planning documents and architectural decisions

**Previous Major Milestones:**
- November 2024: Portfolio & blog system implementation with Vitruvian Developer branding
- December 2024: Authentication system, database models, dashboard with Chart.js visualizations, AI coaching integration
- January 2026: Dynamic behavior tracker system with database models, 13 REST endpoints, dashboard integration, and full AI function calling support (6 WRITE + 8 READ functions)
