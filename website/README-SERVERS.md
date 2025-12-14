# Website Servers - Public Portfolio & Private Workspace

## Quick Start

### Run Both Servers
```bash
cd /Users/nathanbowman/primary-assistant/website
./start-servers.sh
```

Or manually start in separate terminals:
```bash
# Terminal 1
python3 app.py

# Terminal 2
python3 app-private.py
```

### Access
- **Public Portfolio**: http://localhost:8080
- **Private Workspace**: http://localhost:8081

---

## Server Comparison

| Aspect | Public (app.py) | Private (app-private.py) |
|--------|-----------------|--------------------------|
| **Port** | 8080 | 8081 |
| **Purpose** | Portfolio showcase | Personal workspace |
| **Access** | Public docs only | All project files |
| **Data Files** | ✗ Blocked | ✓ Full access |
| **Working Logs** | ✗ Blocked | ✓ Full access |
| **Notes/Coaching** | ✗ Blocked | ✓ Full access |
| **Auth Required** | No | No (local-only) |
| **Use Case** | Share portfolio with others | Personal file access |

---

## What Each Server Does

### Public Server (app.py)
**Purpose**: Present your portfolio to the world

- Serves project documentation from `/docs/` directories
- Shows blog posts and case studies
- Displays featured projects
- All content is curated and public-facing
- No access to working files or personal notes

**Routes**:
- `/` - Homepage with portfolio
- `/project-case-study/<project>` - Detailed project overview
- `/blog` - Blog listing
- `/blog/<slug>` - Individual blog articles
- `/api/projects` - Project metadata
- `/api/blog/posts` - All blog posts

### Private Server (app-private.py)
**Purpose**: Access all your working files and data

- Serves ALL markdown files from both `/docs/` and `/data/` directories
- Access to health/fitness tracking data
- Access to coaching notes and working documents
- Access to exercise logs and personal metrics
- Local-only access (not exposed to internet)

**Extra Routes** (beyond public server):
- Same routes as public server, PLUS
- Full access to `/data/` directory contents
- Access to `check-in-log.md` from working data
- Access to all project files regardless of directory

---

## File Access Examples

### Public Server Can Access:
```
Health_and_Fitness/
├── docs/
│   ├── fitness-roadmap.md         ✓
│   ├── Full-Meal-Plan.md          ✓
│   ├── Shopping-List-and-Estimate.md ✓
│   └── recipies.md                ✓
└── data/
    ├── check-in-log.md            ✗
    ├── exercise-log.md            ✗
    └── Coaching_sessions.md       ✗
```

### Private Server Can Access:
```
Health_and_Fitness/
├── docs/
│   ├── fitness-roadmap.md         ✓
│   ├── Full-Meal-Plan.md          ✓
│   ├── Shopping-List-and-Estimate.md ✓
│   └── recipies.md                ✓
└── data/
    ├── check-in-log.md            ✓
    ├── exercise-log.md            ✓
    └── Coaching_sessions.md       ✓
```

---

## Common Tasks

### Find a Working File
1. Go to http://localhost:8081 (private server)
2. Select project
3. Browse files from both docs/ and data/ directories

### Share Your Portfolio
1. Server is running at http://localhost:8080
2. Share the URL with others
3. They see curated portfolio content
4. They don't see any working files or personal data

### Update Nutrition Info
1. Edit `Health_and_Fitness/docs/recipies.md`
2. Both servers will reflect changes
3. Public sees it in portfolio
4. Private has full access to original

### Review Personal Metrics
1. Access http://localhost:8081/health-and-fitness/graphs
2. View detailed health data from private workspace
3. Public server doesn't expose these graphs or raw data

---

## File Modifications

Any changes you make to shared files (like `recipies.md` in docs/) will appear on both servers:
- Edit the file directly
- Both servers reload automatically (TEMPLATES_AUTO_RELOAD = True)
- No restart needed

---

## Future Upgrades

When ready to add security features, see `PRIVATE_SERVER_SETUP.md` for:
- **Option 2**: Add password protection
- **Option 3**: Add login page with sessions
- **Option 4**: Full OAuth/JWT authentication

All options are non-breaking and can be deployed alongside current setup.

---

## Troubleshooting

### "Address already in use" error
```bash
# Find what's using the port
lsof -i :8081

# Kill the process
kill -9 <PID>

# Or use different port
FLASK_PORT=8082 python3 app-private.py
```

### Can't access from another device
Both servers currently only listen on localhost (127.0.0.1). For external access:
```bash
FLASK_HOST=0.0.0.0 python3 app-private.py
```
⚠️ This exposes the server to the network. Only do this on trusted networks, and consider adding password protection (Option 2 in PRIVATE_SERVER_SETUP.md).

### Files not updating
1. Clear browser cache
2. Make sure you're editing the actual file on disk
3. Check that the file ends with `.md`
4. Ensure file is in an accessible directory (docs/ or data/ for private server)

---

## Security Notes

### Public Server (Port 8080)
- ✓ Safe to expose externally
- ✓ Only shows curated portfolio content
- ✓ No sensitive data access

### Private Server (Port 8081)
- ✓ Completely secure (localhost only, no auth needed)
- ✗ Not suitable for external access without authentication
- ✗ If exposed externally, add password protection (see PRIVATE_SERVER_SETUP.md)

---

## Related Files

- `app.py` - Public portfolio server
- `app-private.py` - Private workspace server
- `PRIVATE_SERVER_SETUP.md` - Authentication upgrade options
- `start-servers.sh` - Startup script for both servers
- `utils/file_utils.py` - File access utilities (updated for data access)
- `CLAUDE.md` - Main project documentation
