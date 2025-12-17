# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CURRENT SESSION STATUS (December 17, 2024)

**STATUS:** Dashboard implementation complete locally, remote deployment needs debugging

**NEXT SESSION START HERE:** Remote server shows containers as healthy but host reports error state. Need to diagnose actual issue.

**COMPLETED THIS SESSION:**
- ✅ Implemented complete dashboard with 8 new API endpoints
- ✅ Created activity feed API module
- ✅ Fixed all frontend JavaScript for proper response parsing
- ✅ Added automated deployment script with health checks
- ✅ Tested successfully in local Docker environment (port 8001)
- ✅ Pushed all changes to GitHub

**BLOCKING ISSUE:** Remote deployment shows containers healthy but application in error state

**NEXT STEPS FOR DEBUGGING:**
1. Check nginx logs: `docker-compose logs nginx | tail -50`
2. Test direct web access: `curl http://localhost:8001/api/health`
3. Check actual browser error (502, timeout, etc.)
4. Verify nginx configuration is correct
5. Check if SSL certificates are causing issues

---

## Project Overview

This is a personal project management system with three main components:

1. **Website** (`/website`): A Flask-based web dashboard with authentication system
2. **Scripts** (`/scripts`): Data processing and visualization utilities
3. **Content Directories**: `Health_and_Fitness` and `AI_Development` folders containing markdown files and project data

Each content directory has a `GEMINI.md` file that provides context-specific information for that area.

### New in This Build:
- ✅ Complete authentication system (Flask-Login, bcrypt, CSRF protection)
- ✅ PostgreSQL database with 8+ models (User, Session, Health, Workout, Nutrition, Coaching)
- ✅ RESTful API layer with 30+ endpoints across 6 modules
- ✅ **Dashboard with real-time data visualization** (NEW - December 17, 2024)
  - 4 quick stat cards (weight, workout, coaching, nutrition)
  - 3 Chart.js interactive charts (trends and adherence)
  - Activity feed aggregating all user data
  - Quick action buttons
- ✅ Virtual database-driven pages (5 pages that generate content from database)
- ✅ Database migrations with Flask-Migrate/Alembic
- ✅ Admin user creation script
- ✅ Automated deployment script with health checks
- ✅ Docker containers building and running locally
- ⚠️ Remote deployment debugging needed

## Common Development Commands

### Running the Website

#### Both Public and Private Servers (Recommended)
```bash
cd /Users/nathanbowman/primary-assistant/website
./start-servers.sh
```
This runs both servers simultaneously:
- **Public Portfolio** (port 8080): `http://localhost:8080`
- **Private Workspace** (port 8081): `http://localhost:8081`

#### Public Portfolio Server Only
```bash
cd /Users/nathanbowman/primary-assistant/website
python3 app.py
```
Website runs on `http://localhost:8080`

#### Private Workspace Server Only
```bash
cd /Users/nathanbowman/primary-assistant/website
python3 app-private.py
```
Website runs on `http://localhost:8081` with full access to `/data/` directories.

**Note**: The website uses port 8080 for public and 8081 for private due to macOS's AirTunes service occupying port 5000.

### Docker Deployment (Local or Remote)

#### Local Development with Docker:
```bash
cd /Users/nathanbowman/primary-assistant
docker-compose up -d
```

#### Remote Server Deployment:
```bash
# Use remote override configuration for HTTP access
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

### Website Servers

The website consists of two separate Flask servers for different purposes:

#### Public Portfolio Server
**File**: `website/app.py` (Port 8080)

Serves curated public content from `/docs/` directories only. Safe to share with the world.

#### Private Workspace Server
**File**: `website/app-private.py` (Port 8081)

Serves ALL project files including `/data/` directories for personal workspace access. Local-only (localhost) for security - no authentication needed. Use this to access working documents, coaching notes, and personal metrics.

**Key Difference**: Private server includes `allow_data_access=True` parameter in `ProjectFileManager` utility, enabling full access to all markdown files.

### Public Portfolio Server (app.py)

The Flask app serves as a dashboard to browse all projects, markdown files, and blog posts:

**Main Routes:**
- **Route `/`**: Main index page with hero section, portfolio, blog section, and contact
- **Route `/health-and-fitness/graphs`**: Displays health data visualization with interactive charts

**Authentication Routes:**
- **Route `/auth/login`**: User login page with CSRF protection
- **Route `/auth/register`**: User registration page
- **Route `/auth/logout`**: Logout and end session
- **Route `/api/auth/status`**: Returns current authentication status (JSON)

**API Routes - Projects:**
- **Route `/api/projects`**: Returns list of available projects
- **Route `/api/project/<name>`**: Returns the GEMINI.md content for a project
- **Route `/api/project/<name>/files`**: Lists all markdown files in a project (with custom ordering for Health_and_Fitness)
  - **Authentication-aware**: Includes virtual database pages only when user is logged in
- **Route `/api/project/<name>/file/<path>`**: Returns content of a specific markdown file
  - **Protected**: Returns 401 for `/data/*` files if not authenticated
- **Route `/api/project/<name>/categorized-files`**: Returns files organized by category
  - **Authentication-aware**: Includes virtual pages when logged in

**API Routes - Health Data:**
- **Route `/api/health-and-fitness/health_data`**: Returns parsed weight/bodyfat data from check-in-log.md

**API Routes - Blog:**
- **Route `/blog`**: Blog listing page with filtering by tags
- **Route `/blog/<slug>`**: Individual blog article page with metadata and related articles
- **Route `/api/blog/posts`**: Returns all blog posts as JSON (sorted by date, newest first)
- **Route `/api/blog/posts/latest?limit=N`**: Returns latest N blog posts (default: 5)
- **Route `/api/blog/post/<slug>`**: Returns specific blog post with HTML-rendered content

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

#### Templates
- **`base.html`**: Base template with fixed navbar and common structure
- **`index.html`**: Main landing page with hero section, portfolio showcase, blog section, and contact area
- **`graphs.html`**: Health & Fitness graphs page with side-by-side chart display
- **`blog_list.html`**: Blog archive page with all posts, tag filtering, and search capability
- **`blog_article.html`**: Individual blog article page with metadata, related articles, and navigation

#### Static Files
- **`css/style.css`**: Modern, responsive design with:
  - CSS variables for consistent theming (primary colors, accent colors, typography)
  - Professional navbar with animated hover effects
  - Project navigation bar displaying file links as horizontal tabs
  - Hero section with background image, gradient overlay, compelling headline, and CTA
  - Featured portfolio section with project cards
  - Blog section styling (cards, grid, filtering, tags)
  - Blog article styling (typography, images with text wrapping)
  - Image float properties for desktop layout (.blog-image-left, .blog-image-right)
  - Responsive mobile breakpoints that convert floats to block display
  - Responsive flexbox layout
  - Markdown content styling (headings, code blocks, tables, blockquotes)
  - Print-friendly styles (hides navbar, project nav bar, sidebar, and print button)
  - Custom scrollbar styling

- **`js/utils.js`**: Shared utility functions
  - `filenameToTitle()`: Converts filename to title case (e.g., "check-in-log.md" → "Check In Log")
  - `projectToTitle()`: Converts project name to title case (e.g., "Health_and_Fitness" → "Health And Fitness")
  - Used by both script.js and graphs.js to ensure consistent formatting

- **`js/script.js`**: Main application logic
  - Project and file navigation
  - Custom title mappings for specific files (e.g., "check-in-log.md" displays as "Metrics Log")
  - Navigation bar population with file links in custom order
  - Active link highlighting
  - SessionStorage bridge for inter-page navigation
  - GEMINI.md loading and navigation
  - Print functionality
  - Duplicate prevention for GEMINI links
  - Blog post loading for homepage

- **`js/blog.js`**: Blog listing and homepage blog functionality
  - Fetches all blog posts from API
  - Creates blog cards with metadata, excerpt, tags
  - Implements tag-based filtering
  - Displays latest N posts on homepage
  - Formats dates and reading times
  - Active filter highlighting
  - Navigation to individual article pages

- **`js/blog-article.js`**: Individual blog article page logic
  - Loads article by slug from URL
  - Renders article metadata (date, author, reading time, tags)
  - Displays HTML-rendered content
  - Finds and displays related articles by tag matching
  - Creates previous/next article navigation
  - Smooth scrolling and page transitions

- **`js/graphs.js`**: Graph page specific logic
  - Navigation bar population with file links
  - Custom title mappings consistent with script.js
  - Chart.js visualization for weight and body fat trends
  - SessionStorage-based navigation to main page
  - Responsive chart rendering
  - GEMINI.md navigation from graphs page

### Navigation System

The website features a consistent navigation system across all pages:

1. **Top Navbar**: Fixed navbar with project selection links
2. **Project Navigation Bar**: Displays when a project is selected, includes:
   - Project name on the left
   - Horizontal list of file links in specified order
   - File links display in proper title case with custom display names
   - Active link is highlighted with color and underline
   - "Back to Project" link on the right
3. **Content Area**: Main display area for project overview or selected file

#### Health_and_Fitness Navigation Order
The Health_and_Fitness project has a custom file order (defined in `app.py`):
1. Fitness Roadmap
2. Full Meal Plan
3. Shopping List And Estimate
4. Metrics Log (displays as custom name, file: `check-in-log.md`)
5. Exercise Progress Log (displays as custom name, file: `progress-check-in-log.md`)
6. Graphs (special link to graphs page)
7. GEMINI (project overview)

#### Custom File Display Names
The following files have custom display names in the navigation bar:
- `check-in-log.md` → "Metrics Log"
- `progress-check-in-log.md` → "Exercise Progress Log"

These mappings are defined in both `script.js` and `graphs.js` using the `customTitles` object and `getFileDisplayTitle()` function.

#### SessionStorage Bridge for Graph Page Navigation
When navigating from the graphs page to files:
1. `graphs.js` stores the project and file names in `sessionStorage`
2. User is redirected to the main page (`/`)
3. `script.js` checks for stored values and automatically loads the project/file
4. SessionStorage values are cleared after loading

This ensures consistent behavior across all pages, including the health graphs page.

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

The application uses PostgreSQL with the following models (located in `website/models/`):

**Authentication Models:**
- `User` (`user.py`) - User accounts with bcrypt password hashing
- `Session` (`session.py`) - Login session tracking

**Health & Fitness Models:**
- `HealthMetric` (`health.py`) - Weight, body fat %, BMI tracking (field: `recorded_date`)
- `WorkoutSession` (`workout.py`) - Workout sessions (field: `session_date`)
- `WorkoutExercise` (`workout.py`) - Individual exercises within sessions
- `MealLog` (`nutrition.py`) - Daily nutrition tracking (field: `meal_date`, macros: `protein_g`, `carbs_g`, `fat_g`)
- `CoachingSession` (`coaching.py`) - Coaching notes and feedback (field: `session_date`)
- `CoachingGoal` (`coaching.py`) - Goal tracking
- `ProgressPhoto` (`coaching.py`) - Progress photos with metadata (field: `photo_date`)

**Important:** All models use specific date field names (not just `date`). This was a common bug that has been fixed in `file_utils.py`.

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
├── app.py                          # PUBLIC server - curated portfolio (port 8080)
├── app-private.py                  # PRIVATE server - all files including /data (port 8081)
├── start-servers.sh                # Startup script to run both servers
├── PRIVATE_SERVER_SETUP.md         # Documentation for authentication upgrades
├── README-SERVERS.md               # Quick reference guide for both servers
├── blog/                           # Blog posts directory
│   ├── the-vitruvian-project-week-1.md
│   ├── getting-started-with-ai.md
│   ├── discipline-in-code-and-fitness.md
│   └── building-scalable-systems.md
├── templates/
│   ├── base.html                   # Base template with navbar
│   ├── index.html                  # Homepage with hero, portfolio, blog, contact
│   ├── blog_list.html              # Blog archive page
│   ├── blog_article.html           # Individual article page
│   └── graphs.html                 # Health & Fitness graphs page
├── static/
│   ├── css/
│   │   └── style.css               # Complete styling including blog
│   ├── js/
│   │   ├── utils.js                # Shared utility functions
│   │   ├── script.js               # Main app logic
│   │   ├── blog.js                 # Blog listing and homepage
│   │   ├── blog-article.js         # Individual article page
│   │   └── graphs.js               # Graphs page logic
│   └── images/
│       ├── hero-section.jpg                  # Background image for hero section
│       ├── profile/
│       │   └── me.jpg
│       ├── blog/
│       │   ├── vitruvian-journey.jpg
│       │   ├── vitruvian-gears.jpg
│       │   ├── vitruvian-martial-arts.jpg
│       │   └── vitruvian-coding.jpg
│       └── projects/
│           └── (project screenshots)
├── utils/
│   ├── file_utils.py               # File management utilities (updated with allow_data_access flag)
│   └── (other utilities)
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

### Navigation & Cross-Page Behavior
- SessionStorage is used to bridge navigation between the graphs page and main page
- When clicking navigation links from the graphs page, data is stored in sessionStorage before redirect
- The main page automatically detects and loads this data on page load
- This approach avoids URL query parameters and ensures clean, consistent navigation
- All markdown file names are automatically converted to proper title case (e.g., "fitness-roadmap.md" → "Fitness Roadmap")

### File Structure
- The sidebar has been removed; all navigation now happens through the horizontal project navigation bar
- File links appear as tabs in the project navigation bar, sorted by custom order from the API
- The "Graphs" link only appears for the Health_and_Fitness project
- Duplicate utility functions extracted to `js/utils.js` for DRY principle

### Recent Updates (Current Session - November 17, 2024)

#### Portfolio & Blog System Implementation
- Revamped homepage with hero section, portfolio showcase, and blog integration
- Implemented complete blog system with Flask backend and frontend
- Created 4 blog post markdown files with YAML front matter metadata
- Added blog-specific CSS styling including responsive image float properties
- Created blog listing page with tag-based filtering functionality
- Created individual blog article pages with metadata display and related articles

#### Blog Routes Added to Flask (app.py)
- `/blog` - Blog listing page
- `/blog/<slug>` - Individual article pages
- `/api/blog/posts` - Returns all blog posts (sorted newest first)
- `/api/blog/posts/latest?limit=N` - Returns latest N posts
- `/api/blog/post/<slug>` - Returns specific post with HTML content
- Added `parse_blog_post()` helper function for YAML front matter parsing
- Added `get_all_blog_posts()` function for retrieving and sorting blog posts

#### New Template Files
- `blog_list.html` - Full blog archive with filtering
- `blog_article.html` - Individual article view with related articles and navigation

#### New JavaScript Files
- `blog.js` - Blog listing and homepage blog functionality
- `blog-article.js` - Individual article page logic

#### Featured Projects Data Structure
- Added `FEATURED_PROJECTS` list with 3 featured projects
- Added `CONTACT_INFO` dictionary with email, LinkedIn, and GitHub links
- Projects include links to demo and GitHub

#### Image Infrastructure
- Created `/static/images/` directory structure with subdirectories:
  - `profile/` - Profile photos
  - `blog/` - Blog post images
  - `projects/` - Project screenshots
- Moved profile image to `static/images/profile/me.jpg`
- Added 4 Vitruvian Project images to `static/images/blog/`:
  - `vitruvian-journey.jpg` (2.1M)
  - `vitruvian-gears.jpg` (612K)
  - `vitruvian-martial-arts.jpg` (1.6M)
  - `vitruvian-coding.jpg` (1.2M)

#### Blog Post: The Vitruvian Project - Week 1
- Successfully integrated existing markdown blog post from blog_post_1 folder
- Added all 4 images with proper alignment and text wrapping
- Implemented magazine-style layout with alternating left/right image placement
- Images use CSS float properties on desktop, convert to block display on mobile
- HTML img tags with inline styles for width and margins
- Proper alt text for accessibility

#### CSS Enhancements
- Added hero section styling with background image and gradient overlay
- Added portfolio grid with featured project cards
- Added blog card styling with gradient headers and hover effects
- Added blog article typography and image styling
- Added `.blog-image` base class with rounded corners and shadows
- Added `.blog-image-left` and `.blog-image-right` float classes
- Added responsive mobile breakpoints for images
- Added hover effects (1.02x scale, enhanced shadow)
- Added float clearing for h2 and blockquote elements

#### Hero Section Background Image
- Located and moved `hero section photo.jpg` from website root to `/static/images/hero-section.jpg`
- Updated `.hero` CSS class with background image implementation
- Added semi-transparent gradient overlay (0.75 opacity) for text readability
- Used `center/cover` sizing for responsive, full-width background
- Gradient overlay uses primary (rgba(26, 35, 126, 0.75)) and secondary (rgba(66, 44, 77, 0.75)) colors
- Maintains visual hierarchy while showcasing the background photo
- Image size: 3.4M, served at `/static/images/hero-section.jpg`

#### Port Configuration Update
- Changed Flask port from 5000 to 8080
- Reason: macOS AirTunes service occupies port 5000
- Updated in `app.py` line 283

#### Phase 1: Design Foundation - The Vitruvian Developer
**Visual Identity System:**
- Redesigned color palette with discipline-specific colors:
  - Code (Deep Navy Blue #1a237e)
  - AI (Purple #7c3aed)
  - Fitness (Warm Orange #ff8a3d)
  - Meta/Philosophy (Cyan #06b6d4)
- Created synergy gradient combining all three main disciplines
- Established consistent shadow system (sm, md, lg, xl)

**Typography System:**
- Enhanced heading hierarchy (H1-H4 with improved font sizing and spacing)
- Refined link styling with smooth transitions
- Improved body text readability and hierarchy

**Component Library:**
- Created discipline tag system (`tag-code`, `tag-ai`, `tag-fitness`, `tag-meta`)
- Added card accent classes for discipline-based borders
- Implemented highlight classes for inline discipline references
- Created synergy badge component showing multi-discipline work
- Added section divider with synergy gradient

**JavaScript Design System:**
- Created `design-system.js` with DesignSystem object
- Implemented utility methods for creating discipline tags and styling
- Added synergy gradient generation
- Content categorization by discipline functionality
- Color mapping system for programmatic styling

**Design Documentation:**
- Created comprehensive `DESIGN_SYSTEM.md` documenting:
  - Complete color palette and usage guidelines
  - Component specifications and usage patterns
  - Brand voice and design principles
  - CSS variable reference
  - Implementation checklist

#### Phase 2: Hero & Homepage Redesign
**Enhanced Hero Section:**
- Updated gradient overlay to use synergy colors (Navy → Purple → Orange)
- Added parallax background-attachment for depth
- Implemented flexbox centering for better layout
- Increased min-height to 85vh for immersive experience
- Added ::before pseudo-element with radial gradients for accent lighting
- Created hero-badge component with glassmorphic styling

**Hero Content Improvements:**
- Added "The Vitruvian Developer" badge
- Updated headline to 4rem with improved letter-spacing
- Changed subtitle to "Code • AI • Discipline"
- Rewrote description to emphasize synergy theme
- Updated CTA buttons to link to synergy section and blog
- Added text-shadow for better readability over background

**Button System Enhancements:**
- Primary button uses gradient-accent with hover states
- Secondary button uses gradient-primary with hover states
- Added transform: translateY(-2px) for lift effect on hover
- Enhanced box-shadow with discipline-specific colors
- Improved visual hierarchy and CTAs

**Synergy Section (NEW):**
- Created full synergy section after hero, before about
- Three-card grid showcasing Code, AI, and Fitness disciplines
- Each card has discipline-colored top border
- Hover effects with lift animation
- Icons (💻 🧠 💪) for visual recognition
- Synergy conclusion section with highlight classes
- Background gradient subtle to main content

**Section Styling Updates:**
- Increased padding to 5rem for better breathing room
- Added h2::after underline with accent color
- Synergy section has special background and gradient text for h2
- Improved section-subtitle styling and line-height
- Better visual separation between sections

**Mobile Responsive Design:**
- Hero section adjusts padding and min-height on mobile
- Hero badge sizing optimized for small screens
- Heading sizes scale appropriately (4rem → 2.2rem)
- Synergy grid converts to single column
- Button layout adjusts to vertical stacking on mobile
- Section padding reduced for mobile (2.5rem)

**Homepage Structure Update:**
- Hero → Synergy → About → Portfolio → Blog → Contact
- Synergy section elevated to featured content position
- Emphasizes "The Vitruvian Developer" theme from start
- Better narrative flow connecting disciplines

#### Phase 3: Navigation & UI/UX Overhaul (Current Session)
**Navigation Architecture Refactoring:**
- Removed the fixed top navbar ("My Journey" branding and project links)
- Eliminated persistent navigation bar at page top
- Simplified page layout for cleaner appearance

**All Projects Section Enhancement:**
- Updated "All Projects" section on homepage to display clickable project cards
- Created `loadAllProjects()` function in `script.js` to dynamically load and display projects
- Implemented responsive project grid with `projects-grid` class (auto-fill columns, 250px minimum width)
- Added `project-card` styling with hover effects and animations
- Cards display project title and "Explore Project" button linking to project content
- Grid uses flexbox with 2rem gap for spacing

**Project Page Controls:**
- Added "Home" button to project view header
- Home button returns to homepage and hides all project-related UI elements
- Button group uses flexbox layout with gap spacing
- Both Home and Print buttons styled with compact sizing and white-space: nowrap
- Implemented proper state management for button visibility
- Fixed bug where project navigation bar persisted after clicking Home

**Button & Control Styling:**
- Created `.button-group` class with flexbox layout
- Styled buttons with constrained padding and proper sizing
- Added hover effects with transform and shadow transitions
- Print button positioned in header alongside Home button

**Color Scheme Exploration:**
- Tested multiple color palette variations while maintaining original theme
- Experimented with: Teal, Deep Forest Green, and other complementary colors
- Ultimately reverted to original color scheme:
  - Primary: Deep Navy Blue (#1a237e)
  - Secondary: Slate Blue (#6a5acd)
  - Accent: Amber (#ffb347)
- Researched color complement options including burgundy, forest green, plum, copper, and olive
- Confirmed original palette provides best aesthetic and brand consistency

**Technical Improvements:**
- Enhanced state management for show/hide of major UI elements (homepage, project-view, nav-bar, buttons)
- Improved CSS organization with modular component classes
- Better event handler management with proper cleanup
- Fixed intermittent UI state issues through proper element selection and condition checks

#### Phase 4: Private Workspace Server Implementation (Current Session - November 21, 2024)

**New Server Architecture:**
- Created separate `app-private.py` running on port 8081 for local-only private workspace access
- Maintains `app.py` (port 8080) for public portfolio showcase
- Both servers can run simultaneously without conflicts
- Private server includes full access to `/data/` directories with working files

**File Access Separation:**
- **Public Server (app.py)**: Only serves `/docs/` directories (curated portfolio content)
- **Private Server (app-private.py)**: Serves both `/docs/` AND `/data/` directories (all project files)
- Implements secure file access control without requiring authentication on localhost

**Updated File Utilities:**
- Modified `utils/file_utils.py` to add `allow_data_access` parameter to `ProjectFileManager` class
- Public server instantiates with `allow_data_access=False` (default)
- Private server instantiates with `allow_data_access=True` to enable data directory scanning
- Maintains security through path validation and stays within project boundaries

**Startup & Documentation:**
- Created `start-servers.sh` shell script for convenient dual-server startup
- Created `README-SERVERS.md` quick reference guide for using both servers
- Created `PRIVATE_SERVER_SETUP.md` comprehensive documentation with upgrade paths:
  - Option 1: Simple local-only (current implementation)
  - Option 2: Basic authentication with password protection
  - Option 3: Session-based login interface
  - Option 4: Production-ready OAuth/JWT
- All upgrade options are non-breaking and documented for future implementation

**Use Cases:**
- **Public Server**: Share portfolio with others, impress employers, present curated work
- **Private Server**: Access personal health metrics, coaching notes, exercise logs, all working documents
- Both servers use same templates/static files for consistent experience
- Can develop/test on private server before publishing to public portfolio

#### Previous Session Work
- Created `js/utils.js` with shared utility functions (`filenameToTitle`, `projectToTitle`)
- Fixed print functionality to hide the project navigation bar in print media query
- Implemented custom file ordering for Health_and_Fitness project in `app.py`
- Added custom display names for specific files (Metrics Log, Exercise Progress Log)
- Added GEMINI link to project navigation with duplicate prevention
- Created `loadGemini()` function in script.js to handle GEMINI.md navigation
