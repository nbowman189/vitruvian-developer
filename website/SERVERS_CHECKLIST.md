# Dual-Server Checklist & Quick Reference

## Daily Operations

### Starting Both Servers
- [ ] Open terminal
- [ ] `cd /Users/nathanbowman/primary-assistant/website`
- [ ] `./start-servers.sh`
- [ ] Verify both servers start without errors
- [ ] Access http://localhost:8080 (public)
- [ ] Access http://localhost:8081 (private)

### Accessing Public Portfolio
- [ ] Go to http://localhost:8080
- [ ] View curated content from `/docs/` directories only
- [ ] Share URL with others (safe - no personal data)

### Accessing Private Workspace
- [ ] Go to http://localhost:8081
- [ ] View all files including `/data/` directories
- [ ] Access personal health metrics
- [ ] Access coaching notes and working documents

## File Updates

### When Updating Documentation
- Edit file in `/docs/` directory
- Both servers reflect changes automatically
- Public server shows it in portfolio
- Private server shows it in workspace

### When Adding Working Files
- Add file to `/data/` directory
- Only private server (8081) can access
- Public server doesn't see it
- Perfect for personal notes

### When Publishing Content
- Create file in `/docs/` directory
- Make it available on both servers
- Safe to share publicly from 8080

## Troubleshooting

### Port Already in Use
```bash
# Find what's using port 8081
lsof -i :8081

# Kill the process
kill -9 <PID>

# Or use different port
FLASK_PORT=8082 python3 app-private.py
```

### Can't Connect to Servers
- [ ] Check both servers started in startup script
- [ ] Verify port 8080 and 8081 are free
- [ ] Check firewall settings
- [ ] Try manual startup: `python3 app.py` and `python3 app-private.py`

### Files Not Showing Up
- [ ] Verify file ends with `.md`
- [ ] Check file is in correct directory (`/docs/` or `/data/`)
- [ ] For private server only: file must be in `/data/` or `/docs/`
- [ ] For public server only: file must be in `/docs/`
- [ ] Clear browser cache

### Startup Script Not Found
```bash
# Make it executable
chmod +x /Users/nathanbowman/primary-assistant/website/start-servers.sh

# Or run manually
python3 app.py &  # Public server
python3 app-private.py &  # Private server
```

## File Reference

### Public Server Access Only (`app.py` - Port 8080)
```
Health_and_Fitness/docs/
├── fitness-roadmap.md          ✓ Visible
├── Full-Meal-Plan.md           ✓ Visible
├── Shopping-List-and-Estimate.md ✓ Visible
└── recipies.md                 ✓ Visible

Health_and_Fitness/data/
├── check-in-log.md             ✗ NOT visible
├── exercise-log.md             ✗ NOT visible
└── Coaching_sessions.md        ✗ NOT visible
```

### Both Servers Access (`app-private.py` - Port 8081)
```
Health_and_Fitness/docs/
├── fitness-roadmap.md          ✓ Visible
├── Full-Meal-Plan.md           ✓ Visible
├── Shopping-List-and-Estimate.md ✓ Visible
└── recipies.md                 ✓ Visible

Health_and_Fitness/data/
├── check-in-log.md             ✓ Visible
├── exercise-log.md             ✓ Visible
└── Coaching_sessions.md        ✓ Visible
```

## Common Tasks

### View Health Metrics
1. Start servers: `./start-servers.sh`
2. Go to http://localhost:8081 (private)
3. Browse to Health & Fitness project
4. Access `data/check-in-log.md`

### Share Portfolio
1. Make sure `./start-servers.sh` is running
2. Give http://localhost:8080 to others
3. They see public portfolio only
4. No personal data exposed

### Add Coaching Notes
1. Edit `Health_and_Fitness/data/Coaching_sessions.md`
2. Save file
3. Refresh http://localhost:8081 (private)
4. Notes appear immediately
5. NOT visible on public server (8080)

### Update Meal Plan
1. Edit `Health_and_Fitness/docs/Full-Meal-Plan.md`
2. Save file
3. Changes visible on both servers
4. http://localhost:8080 shows it publicly
5. http://localhost:8081 shows it privately

## Future Authentication Upgrades

When ready to add security, see `PRIVATE_SERVER_SETUP.md` for:

### Option 2: Password Protection (Simple)
- Add HTTP Basic Auth
- No UI changes needed
- Good for network sharing
- Time: ~15 minutes

### Option 3: Login Page (Medium)
- Add session-based login
- Professional interface
- Better UX for multiple users
- Time: ~30 minutes

### Option 4: OAuth/JWT (Advanced)
- Production-grade security
- Mobile-friendly tokens
- Scalable to many devices
- Time: ~2-3 hours

## Environment Variables

```bash
# Optional - change default port
FLASK_PORT=8081

# Optional - change localhost binding
FLASK_HOST=127.0.0.1

# Optional - enable debug mode
FLASK_DEBUG=True

# Example: Run on different port
FLASK_PORT=8082 python3 app-private.py
```

## Quick Commands

```bash
# Start both servers
./start-servers.sh

# Start public only
python3 app.py

# Start private only
python3 app-private.py

# Check if ports are available
lsof -i :8080
lsof -i :8081

# Stop background process
kill -9 <PID>

# Run with custom port
FLASK_PORT=9000 python3 app-private.py
```

## Support Files

- **CLAUDE.md** - Main project documentation
- **ARCHITECTURE.md** - Technical architecture
- **README-SERVERS.md** - Detailed server guide
- **PRIVATE_SERVER_SETUP.md** - Auth upgrade documentation
- **IMPLEMENTATION_SUMMARY.md** - What was implemented

## Remember

- **Port 8080** = Public portfolio (safe to share)
- **Port 8081** = Private workspace (localhost only)
- Both use same templates and static files
- Both can run simultaneously
- `/docs/` = Public content (visible on both)
- `/data/` = Private content (only on private server)
- No passwords needed (localhost security)
- Clear upgrade path if you need passwords later
