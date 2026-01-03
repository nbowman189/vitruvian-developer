# Session Notes

## Latest Session - January 3, 2026: Behavior Tracker Deployment & Docker Volume Fix - COMPLETE ✅

### Issues Resolved:

**Problem 1:** Behavior History page returning 500 error on `/api/behavior/logs` endpoint
**Problem 2:** Docker deployments not loading updated Python code despite rebuilding
**Problem 3:** Manage Behaviors page - JavaScript and CSS files missing or outdated after rebuild
**Problem 4:** Static files volume mount overwriting freshly built files
**Problem 5:** Coaching Sessions page displaying fields in reversed order

### Root Causes:

**Issue 1 - Function Signature Mismatch:**
- `validate_pagination_params()` in `website/api/__init__.py` had uncommitted changes
- Local code: `def validate_pagination_params(default_per_page=20, max_per_page=100):`
- Remote code: `def validate_pagination_params():` (no parameters)
- `behavior.py` called it with parameters: `validate_pagination_params(default_per_page=50, max_per_page=1000)`
- Result: `TypeError: validate_pagination_params() got an unexpected keyword argument 'default_per_page'`

**Issue 2 - Docker Layer Caching:**
- Even `docker-compose up -d --build` uses cached layers
- Python code changes weren't being copied into Docker image
- Container was running old code even after "rebuild"

**Issue 3 - Static Files Missing/Outdated:**
- `behavior-manage.js` (16,410 bytes) completely missing from container despite being in git
- `style.css` outdated in container (5,834 lines vs 6,116 lines)
- Files existed on remote server and in git, but not in running container
- Even `--no-cache` rebuild didn't fix the problem

**Issue 4 - Root Cause: Volume Mount Overwriting Built Files:**
- Docker image build correctly copies ALL files including `behavior-manage.js` and updated `style.css`
- `docker-compose.yml` line 63: `static_files:/app/website/static` mounts persistent volume
- When container starts, Docker mounts old `static_files` volume OVER the freshly built directory
- Result: Newly built static files immediately replaced by old volume contents
- `docker cp` workaround worked because it copied INTO the mounted volume (which persists)
- `--no-cache` flag was irrelevant because the build was fine - volume mount was the issue

**Issue 5 - Coaching Sessions Field Mapping:**
- Template displayed `coach_feedback` in card header and `discussion_notes` in card body
- User confirmed correct mapping should be reversed:
  - Card header (collapsed): `discussion_notes` (topic/summary)
  - Card body (expanded): `coach_feedback` (detailed feedback)

### Solutions Applied:

**Fix #1 - Commit Missing Changes:**
```bash
git add website/api/__init__.py
git commit -m "Add parameters to validate_pagination_params for flexible pagination limits"
git push origin main
```

**Fix #2 - Force No-Cache Rebuild:**
```bash
# WRONG (uses cache):
docker-compose up -d --build web

# CORRECT (forces fresh build):
docker-compose stop web
docker-compose rm -f web
docker-compose build --no-cache web
docker-compose up -d web
```

**Fix #3 - Update Deployment Script:**
- Updated `scripts/deploy-remote.sh` to use `build --no-cache` instead of `up -d --build`
- Ensures all future deployments use correct process

**Fix #4 - Remove Static Files Volume Mount (PERMANENT SOLUTION):**
```bash
# Removed from docker-compose.yml:
# web service: - static_files:/app/website/static
# nginx service: - static_files:/app/website/static:ro
# volumes section: static_files definition

# Updated nginx configurations:
# - Changed from serving files directly (alias /app/website/static/)
# - Changed to proxying /static/ requests to Flask app
# - Flask serves static files from built-in directory in Docker image
```

**Why This Works:**
- Static files (JS, CSS, images) are application code, not user data
- They should be baked into the Docker image during build, not stored in volumes
- Volumes are for persistent user-generated data (uploads, logs, database)
- Nginx now proxies static file requests to Flask, which serves from the image
- Every deployment gets fresh static files automatically

**Fix #5 - Coaching Sessions Field Mapping:**
```javascript
// CORRECT mapping in coaching_sessions.html:
const title = session.discussion_notes || 'Coaching Session';  // Header
const hasContent = session.coach_feedback && session.coach_feedback.length > 0;  // Body

// Render markdown for expanded content:
if (markdownDiv && session.coach_feedback) {
    markdownDiv.innerHTML = marked.parse(session.coach_feedback);
}
```

### Key Lessons Learned:

1. **Docker volume mounts override image contents** - Volume mounts replace directories even after fresh builds
2. **Static files should NOT use volumes** - They're application code, not user data
3. **Docker's layer caching is aggressive** - Even `--build` flag can skip copying updated files (separate issue)
4. **Always use `build --no-cache` for remote deployments** - Only way to guarantee fresh code
5. **Commit all changes before deploying** - Uncommitted local changes won't be on remote server
6. **Use detailed error debugging** - Modified error handler to return full Python traceback for diagnosis
7. **Separate concerns: Code vs Data** - Code → Docker image, User data → Docker volumes

### Files Modified:
- `website/api/__init__.py` - Committed parameter changes to `validate_pagination_params()`
- `scripts/deploy-remote.sh` - Changed to use `build --no-cache`
- `CLAUDE.md` - Updated deployment documentation with --no-cache warnings
- `docker-compose.yml` - Removed `static_files` volume mount from web and nginx services
- `docker/nginx/nginx.conf` - Changed to proxy /static/ requests to Flask
- `docker/nginx/nginx-remote.conf` - Changed to proxy /static/ requests to Flask
- `website/templates/coaching_sessions.html` - Fixed field mapping (discussion_notes → header, coach_feedback → body)
- `SESSION_NOTES.md` - Documented root cause investigation and permanent fix

### Git Commits:
- `342b673` - "Force no-cache rebuild in deployment script to ensure code updates"
- `ea6bd2f` - "Add parameters to validate_pagination_params for flexible pagination limits"
- `0110c74` - "Update deployment docs: emphasize --no-cache requirement for Docker builds"
- `950942b` - "Fix Docker volume mount overwriting static files"
- `a86a36c` - "Fix coaching sessions: swap coach_feedback and discussion_notes display" (incorrect)
- `35b59e5` - "Fix coaching sessions field mapping (correct version)"

### Deployment Command Reference:
```bash
# ALWAYS use this for remote Python code deployments:
./scripts/deploy-remote.sh

# OR manually:
cd /home/nathan/vitruvian-developer
git pull origin main
docker-compose -f docker-compose.yml -f docker-compose.remote.yml stop web
docker-compose -f docker-compose.yml -f docker-compose.remote.yml rm -f web
docker-compose -f docker-compose.yml -f docker-compose.remote.yml build --no-cache web
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d web
```

### Current Deployment Status - STABLE ✅

**Remote Server:** vit-dev-website (vitruvian.bowmanhomelabtech.net)

**Container Status:**
- ✅ primary-assistant-db: Up (healthy)
- ✅ primary-assistant-web: Up (healthy)
- ✅ primary-assistant-nginx: Up (healthy)

**Deployed Commit:** `35b59e5` - "Fix coaching sessions field mapping (correct version)"

**Working Features:**
- ✅ Behavior History page - Pagination working correctly
- ✅ Manage Behaviors page - Full CRUD interface with drag-and-drop reordering
- ✅ Coaching Sessions page - Correct field mapping (discussion_notes in header, coach_feedback in body)
- ✅ Static files served from Docker image (no more volume mount issues)
- ✅ All JavaScript and CSS files loading correctly

**Post-Deployment Steps Required:**
1. **Purge Cloudflare cache** - Necessary for JavaScript/CSS changes to take effect
   - Option 1: Purge Everything in Cloudflare dashboard
   - Option 2: Enable Development Mode for 3 hours
2. Test all pages after cache purge

**Known Issues:** None

**Next Session Priorities:**
- Continue with AI Fitness Coach expansion (if plan mode work is needed)
- Any new feature requests or bug fixes

---

## Previous Session - December 17, 2024: AI Coach CSRF Fix - COMPLETE ✅

### Issue Resolved:
**Problem:** AI Coach API endpoints were blocked by CSRF protection
- Frontend showed: "Error: Failed to send message. Please try again."
- Backend returned: `{"errors":["400 Bad Request: The CSRF token is missing."]}`

### Root Cause:
- Flask-WTF's CSRFProtect was enforcing CSRF tokens on all POST requests
- API endpoints (JSON) don't use CSRF tokens - they rely on authentication
- Blueprint-level exemption (`csrf.exempt(api_bp)`) wasn't working for nested blueprints

### Solutions Applied:

**Fix #1 - CSRF Protection Exemption:**
1. Added `@csrf.exempt` decorator directly to POST routes in `website/api/ai_coach.py`
2. Imported `csrf` from `website` package
3. Applied decorator to:
   - `/api/ai-coach/message` (line 49)
   - `/api/ai-coach/save-record` (line 297)
4. Removed ineffective blueprint-level exemption from `website/__init__.py`

**Fix #2 - Authentication Credentials:**
1. Added `credentials: 'include'` to all 4 fetch calls in `website/static/js/ai-coach.js`
2. Fixed GET requests:
   - `/api/ai-coach/conversations` (line 64-66)
   - `/api/ai-coach/conversations/<id>` (line 124-126)
3. Fixed POST requests:
   - `/api/ai-coach/message` (line 220-227)
   - `/api/ai-coach/save-record` (line 662-673)
4. Without credentials: 'include', authentication cookies weren't being sent

### Verification:
```bash
# CSRF error resolved - now returns proper authentication check
$ curl -X POST http://localhost:8000/api/ai-coach/message
{"message":"Authentication required","success":false}
```

### Files Modified:
- `website/api/ai_coach.py` - Added CSRF exemption decorators (Fix #1)
- `website/__init__.py` - Removed ineffective blueprint exemption (Fix #1)
- `website/static/js/ai-coach.js` - Added credentials to all fetch calls (Fix #2)

### Git Commits:
**Commit 1:** `261c030` - "Fix CSRF protection blocking AI Coach API endpoints"
**Commit 2:** `4e4463b` - "Update session notes: CSRF fix for AI Coach API complete"
**Commit 3:** `1755362` - "Fix authentication: Add credentials to AI Coach fetch calls"
**Status:** All commits pushed to remote repository

### Deployment Status:
- ✅ Local testing: CSRF error resolved
- ✅ All 5 routes registered successfully
- ✅ GEMINI_API_KEY configured (39 characters)
- ⏳ Ready for remote deployment testing

### Next Steps:
1. User should pull latest changes on remote server
2. Run deployment script: `./deploy-ai-coach.sh`
3. Purge Cloudflare cache
4. Test AI Coach functionality end-to-end

---

## Previous Session - December 14, 2024: Database Connection Issue - RESOLVED

## Current Status: Database Connection Issue on Remote Server

### ✅ Completed Across Sessions:

1. **Authentication System - FULLY WORKING (Local)**
   - Flask-Login integration with session-based auth
   - User registration and login with bcrypt password hashing
   - CSRF protection on all forms
   - PostgreSQL database models (User, Session, Health, Workout, Nutrition, Coaching)
   - Database migrations with Flask-Migrate/Alembic
   - Admin user creation script
   - All working perfectly on local development (localhost:8080)

2. **Virtual Database Pages - FULLY FIXED (Local)**
   - Fixed all 5 virtual database page generators:
     - Health Metrics Log (`recorded_date`)
     - Workout Log (`session_date`)
     - Meal Log (`meal_date`, `protein_g`, `carbs_g`, `fat_g`)
     - Progress Photos (`photo_date`, import from `coaching.py`)
     - Coaching Sessions (`session_date`)
   - All pages load correctly when authenticated
   - Display empty state when no data exists

3. **Frontend Fixes - COMPLETE**
   - Navbar z-index fix (login bar now visible)
   - Added `credentials: 'include'` to all 8 fetch calls
   - JavaScript properly sends authentication cookies

4. **Configuration - COMPLETE**
   - `SESSION_COOKIE_SECURE=false` for local HTTP
   - Environment variable overrides in ProductionConfig
   - Created `docker-compose.remote.yml` for remote deployments

5. **Remote Server Setup - PROGRESS MADE (Today's Session)**
   - ✅ Docker ContainerConfig error RESOLVED (was version mismatch, but 1.29.2 works)
   - ✅ Containers building successfully on remote server
   - ✅ PostgreSQL container running and healthy
   - ✅ Web container builds without errors
   - ❌ NEW ISSUE: Database connection string parsing error

---

## ❌ CURRENT BLOCKING ISSUE - Database Connection String:

**Problem:** Web container cannot connect to database due to special characters in password

**Error Message:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not translate host name "rcher@db" to address: Name or service not known
```

**Root Cause:**
- Database password contains `@` symbol: `Gn05!s12!@rcher`
- In PostgreSQL connection string format `postgresql://user:password@host:port/database`, the `@` is a delimiter
- The parser interprets `@rcher` as part of the hostname instead of the password
- This breaks the connection string parsing

**Fix Required:**
URL-encode the `@` symbol in the password as `%40` in `docker-compose.yml`:

```yaml
# Current (BROKEN):
DATABASE_URL: postgresql://postgres:Gn05!s12!@rcher@db:5432/primary_assistant

# Fixed (URL-encoded @ as %40):
DATABASE_URL: postgresql://postgres:Gn05!s12!%40rcher@db:5432/primary_assistant
```

**Status:** User stopped for the day before applying this fix

---

## 🚨 NEXT SESSION - START HERE:

### Priority 1: Fix Database Connection String

On remote server at `/home/nathan/vitruvian-developer/docker-compose.yml`:

1. **Edit docker-compose.yml to URL-encode the @ symbol:**
   ```bash
   cd /home/nathan/vitruvian-developer

   # Option 1: Manual edit
   nano docker-compose.yml
   # Find: postgresql://postgres:Gn05!s12!@rcher@db:5432/primary_assistant
   # Replace with: postgresql://postgres:Gn05!s12!%40rcher@db:5432/primary_assistant

   # Option 2: Automated sed (use single quotes to prevent bash expansion)
   sed -i 's|Gn05!s12!@rcher@db|Gn05!s12!%40rcher@db|g' docker-compose.yml
   ```

2. **Verify the change:**
   ```bash
   grep "DATABASE_URL" docker-compose.yml
   # Should show: postgresql://postgres:Gn05!s12!%40rcher@db:5432/primary_assistant
   ```

3. **Restart containers:**
   ```bash
   docker-compose down
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d
   ```

4. **Check container status:**
   ```bash
   docker-compose ps
   # All containers should be "Up" and healthy
   ```

5. **Verify web container logs:**
   ```bash
   docker-compose logs web | tail -50
   # Should show successful migration and "Starting Primary Assistant Application"
   ```

6. **Create admin user:**
   ```bash
   docker-compose exec web python website/scripts/create_admin_user.py
   ```

7. **Test access:**
   - Navigate to `http://your-server-ip:8080`
   - Login with admin credentials
   - Verify all virtual pages appear and load correctly

---

## Remote Server Environment:

### System Information:
- **OS:** Ubuntu 24.04.3 LTS
- **Kernel:** 6.8.0-88-generic
- **Architecture:** x86_64
- **CPUs:** 4
- **Memory:** 15.53 GiB

### Docker Environment:
- **Docker Version:** 28.2.2
- **Docker Compose Version:** 1.29.2 (legacy standalone)
- **Storage Driver:** overlay2
- **Cgroup Version:** 2
- **Hostname:** vit-dev-website

### Docker Status:
- ✅ Docker daemon running
- ✅ Containers can be created
- ✅ PostgreSQL container healthy
- ✅ Images building successfully
- ❌ Web container fails on database connection

### Project Path:
- `/home/nathan/vitruvian-developer`

---

## Working Features (Local):

### Authentication:
- ✅ User registration
- ✅ User login/logout
- ✅ Session management
- ✅ Password hashing (bcrypt)
- ✅ CSRF protection
- ✅ Protected routes

### Virtual Database Pages (when authenticated):
- ✅ Health Metrics Log - shows table of weight/bodyfat/BMI
- ✅ Workout Log - shows exercise sessions
- ✅ Meal Log - shows daily nutrition
- ✅ Progress Photos - shows photo gallery
- ✅ Coaching Sessions - shows coaching notes

### UI/UX:
- ✅ Navbar visible (z-index fixed)
- ✅ Login bar works correctly
- ✅ Virtual pages appear in navigation after login
- ✅ All pages load without errors

---

## Known Issues:

1. **CRITICAL (Remote):** Database connection string has special character (@) that needs URL encoding
2. **Resolved:** Docker ContainerConfig error (was false alarm, docker-compose 1.29.2 works fine)
3. **Note:** Session cookies configured for HTTP (SESSION_COOKIE_SECURE=false in docker-compose.remote.yml)

---

## Database Schema:

All models created and migrated:
- `users` - User authentication
- `sessions` - Login sessions
- `health_metrics` - Weight, bodyfat, BMI tracking
- `workout_sessions` - Exercise logging
- `workout_exercises` - Exercise details
- `meal_logs` - Nutrition tracking
- `coaching_sessions` - Coaching notes
- `coaching_goals` - Goal tracking
- `progress_photos` - Progress images

Migration file: `website/migrations/versions/b72667ea0290_initial_migration_user_session_health_.py`

---

## Git Status:

**Last Commit:** `1bc5422` - "Add remote deployment support and fix Bad Request error"

**Branch:** main

**Repository:** https://github.com/nbowman189/vitruvian-developer.git

All changes committed and pushed.

---

## Commands Reference:

### Local Development:
```bash
cd /Users/nathanbowman/primary-assistant/website
./start-servers.sh
# Public: http://localhost:8080
# Private: http://localhost:8081
```

### Remote Deployment (once database connection fixed):
```bash
cd /home/nathan/vitruvian-developer
git pull origin main
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d --build
```

### Create Admin User (remote):
```bash
docker-compose exec web python website/scripts/create_admin_user.py
```

### Database Migrations (remote):
```bash
# Create migration
docker-compose exec web flask db migrate -m "description"

# Apply migration
docker-compose exec web flask db upgrade
```

### View Container Logs (remote):
```bash
# All containers
docker-compose logs

# Specific container
docker-compose logs web
docker-compose logs db
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f web
```

### Container Management (remote):
```bash
# Check status
docker-compose ps

# Restart specific service
docker-compose restart web

# Rebuild and restart
docker-compose up -d --build web

# Stop all containers
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## Next Session Checklist:

- [ ] Fix DATABASE_URL in docker-compose.yml (encode @ as %40)
- [ ] Restart remote containers
- [ ] Verify all containers healthy
- [ ] Create admin user on remote server
- [ ] Test authentication flow remotely
- [ ] Verify all 5 virtual pages work on remote
- [ ] Document successful deployment process
- [ ] Consider HTTPS setup for production (future)

---

## Troubleshooting Reference:

### Docker Compose V2 Installation Attempt:
- Attempted to upgrade to Docker Compose V2 plugin
- Ubuntu package repository did not have `docker-compose-plugin`
- Direct binary download had curl syntax errors
- **Conclusion:** docker-compose 1.29.2 (legacy) works fine, no upgrade needed

### Database Connection Issues:
- **Symptom:** `could not translate host name "rcher@db" to address`
- **Cause:** Special characters in password not URL-encoded
- **Solution:** URL-encode special characters in connection string
- **Special characters that need encoding:**
  - `@` → `%40`
  - `!` → `%21` (if causes issues)
  - `#` → `%23`
  - `$` → `%24`
  - `%` → `%25`

---

## Contact Info:

**User:** Nathan Bowman
**GitHub:** nbowman189
**Project:** The Vitruvian Developer
**Session Dates:**
- Previous Session: December 14, 2024
- Today's Session: December 14, 2024 (continued)
**Status:** Incomplete - Database connection string needs URL encoding on remote server
