# Deployment Instructions for Remote Server

## Quick Deploy - Health Data Import

All code has been tested locally and is ready for deployment.

### Step 1: Update Remote Server

```bash
# SSH to your server
ssh nathan@<your-server-ip>
cd /home/nathan/vitruvian-developer

# Pull latest code (includes all fixes)
git pull origin main

# Should show latest commits:
# - bd337cc: Fix Workout Log and Meal Log virtual page generators
# - 4f42cc0: Add master import script and volume mount
# - f71f8f6: Fix import script paths for Docker
```

### Step 2: Rebuild Containers

```bash
# Stop and remove all containers/volumes
docker-compose down -v

# Remove old images to force fresh build
docker rmi $(docker images | grep vitruvian-developer | awk '{print $3}') 2>/dev/null || true

# Clean Docker cache
docker system prune -f
docker builder prune -f

# Rebuild from scratch
docker-compose -f docker-compose.yml -f docker-compose.remote.yml build --no-cache

# Start containers
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d

# Wait for containers to start
sleep 15

# Check status
docker-compose ps
```

### Step 3: Verify Containers Are Healthy

```bash
# All containers should show "Up" and "healthy"
docker-compose ps

# Check web container logs
docker-compose logs web | tail -30

# Should see:
# ✅ Migrations completed successfully!
# 🎉 Application initialization complete!
# 🌐 Starting web server...
```

### Step 4: Import All Health Data

```bash
# Run the master import script (imports all 4 data files)
docker-compose exec -T web python scripts/import-all-health-data.py <<EOF
y
EOF
```

**Expected Results:**
- Health Metrics: 118 records
- Meal Log: 9 records
- Exercise Log: 13 workout sessions
- Coaching Sessions: 5 sessions
- Overall: 4/4 imports successful

### Step 5: Verify Virtual Pages Load

1. Open browser: `http://your-server-ip:8080`
2. Login with admin credentials
3. Navigate to Health_and_Fitness project
4. Click each virtual page:
   - ✅ Health Metrics Log - should show weight/bodyfat table
   - ✅ Workout Log - should show exercise sessions
   - ✅ Meal Log - should show daily nutrition
   - ✅ Progress Photos - should show empty state (no photos uploaded yet)
   - ✅ Coaching Sessions - should show coaching notes

All pages should load without "ERROR Failed to load the file" messages.

---

## What Was Fixed

### Issue 1: Data Files Not Accessible in Container
**Solution:** Added volume mount in docker-compose.yml
```yaml
volumes:
  - ./Health_and_Fitness/data:/Health_and_Fitness/data:ro
```

### Issue 2: Import Scripts Looking in Wrong Path
**Solution:** Updated all import scripts to detect Docker vs local environment
```python
docker_path = Path("/Health_and_Fitness/data/file.md")
local_path = Path(__file__).parent.parent / "Health_and_Fitness" / "data" / "file.md"
default_path = docker_path if docker_path.exists() else local_path
```

### Issue 3: Virtual Pages Using Wrong Field Names
**Solution:** Fixed field names in file_utils.py
- `workout.workout_type` → `workout.session_type.value`
- `workout.exercises` → `workout.exercise_logs`
- `exercise.weight` → `exercise.weight_lbs`

### Issue 4: Python Bytecode Cache Issues
**Solution:** Complete rebuild process with `--no-cache` and cache cleanup

---

## Troubleshooting

### If Meal Log Import Still Fails

The remote server may have stale Python bytecode. Try this:

```bash
# Stop containers
docker-compose down

# Clear local Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Rebuild completely from scratch
docker-compose -f docker-compose.yml -f docker-compose.remote.yml build --no-cache

# Start fresh
docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d

# Clear cache inside container
docker-compose exec web find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
docker-compose exec web find /app -type f -name "*.pyc" -delete 2>/dev/null || true

# Restart web container
docker-compose restart web
sleep 5

# Try import again
docker-compose exec -T web python scripts/import-all-health-data.py <<EOF
y
EOF
```

### If Virtual Pages Still Show Errors

1. Check container has latest code:
```bash
docker-compose exec -T web grep "session_type.value" website/utils/file_utils.py
```

Should show line with `workout.session_type.value` (not `workout.workout_type`)

2. Check database has data:
```bash
docker-compose exec -T web python3 -c "
from website import create_app, db
from website.models.workout import WorkoutSession
from website.models.nutrition import MealLog

app = create_app()
with app.app_context():
    workouts = WorkoutSession.query.count()
    meals = MealLog.query.count()
    print(f'Workouts: {workouts}')
    print(f'Meals: {meals}')
"
```

---

## Success Checklist

- [ ] Git pull shows latest commits
- [ ] Containers rebuild successfully
- [ ] All containers show "Up" and "healthy" status
- [ ] Master import script runs successfully (4/4 imports)
- [ ] Health Metrics Log page loads with data
- [ ] Workout Log page loads with workout sessions
- [ ] Meal Log page loads with nutrition data
- [ ] Coaching Sessions page loads with session notes
- [ ] No "ERROR Failed to load the file" messages

---

## Next Steps After Successful Deployment

1. Set up HTTPS with Let's Encrypt (see `scripts/setup-ssl.sh`)
2. Configure automated daily database backups (see `scripts/backup-database.sh`)
3. Monitor application logs for any issues
4. Add new data files as they're created

---

**All fixes have been tested locally and work correctly. The deployment should be straightforward.**
