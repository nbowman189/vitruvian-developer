# Production Deployment Plan

## Overview

This plan covers deploying the website to the remote server with a complete database rebuild and data migration from markdown files.

---

## Pre-Deployment Checklist

### Data Files to Import
| Source File | Database Table | Est. Records |
|-------------|----------------|--------------|
| `Health_and_Fitness/data/check-in-log.md` | `health_metrics` | ~121 |
| `Health_and_Fitness/data/meal-log.md` | `meal_logs` | ~90 |
| `Health_and_Fitness/data/exercise-log.md` | `workout_sessions` + `exercise_logs` | ~68 |
| `Health_and_Fitness/data/Coaching_sessions.md` | `coaching_sessions` | ~8 |
| `Health_and_Fitness/data/behavior-tracker.md` | `behavior_definitions` + `behavior_logs` | 12 defs, ~96 logs |
| `Health_and_Fitness/docs/nathan-recomposition-plan-phase-1.md` | `documents` | 1 |

### Existing Import Scripts (Verified)
- `scripts/import-health-data.py` - Health metrics
- `scripts/import-meal-log.py` - Meal logs
- `scripts/import-exercise-log.py` - Exercise/workout logs
- `scripts/import-coaching-sessions.py` - Coaching sessions
- `scripts/import_behavior_data.py` - Behavior tracking
- `scripts/import_recomp_document.py` - Recomposition plan document
- `scripts/import-all-health-data.py` - Master script (runs first 4)

---

## Deployment Steps

### Phase 1: Prepare Local Environment

1. **Commit pending changes**
   ```bash
   cd /Users/nathanbowman/primary-assistant
   git add -A
   git commit -m "Prepare for production deployment with data migration"
   git push origin main
   ```

### Phase 2: Deploy to Remote Server

2. **SSH to remote server and pull latest code**
   ```bash
   ssh nathan@vit-dev-website
   cd /home/nathan/vitruvian-developer
   git pull origin main
   ```

### Phase 3: Rebuild Database

3. **Run the database rebuild script**
   ```bash
   cd /home/nathan/vitruvian-developer
   ./scripts/rebuild_database.sh --remote
   ```

   This script will:
   - Stop containers and remove volumes (fresh database)
   - Rebuild containers from scratch (no cache)
   - Start containers
   - Wait for database health check
   - Run Flask-Migrate database migrations
   - Prompt to create admin user (answer: Y)
   - Skip sample data (answer: N - we'll import real data)

### Phase 4: Import Health & Fitness Data

4. **Copy data files to Docker container**
   ```bash
   # Copy the Health_and_Fitness data directory to the container
   docker cp Health_and_Fitness primary-assistant-web:/app/Health_and_Fitness
   ```

5. **Run the master import script for health data**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web \
       python /app/scripts/import-all-health-data.py
   ```

   This imports (in order):
   - Health metrics from check-in-log.md
   - Meal logs from meal-log.md
   - Exercise logs from exercise-log.md
   - Coaching sessions from Coaching_sessions.md

### Phase 5: Import Behavior Tracker Data

6. **Run the behavior data import script**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web \
       python /app/scripts/import_behavior_data.py /app/Health_and_Fitness/data/behavior-tracker.md
   ```

### Phase 6: Import Recomposition Document

7. **Run the document import script**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web \
       python /app/scripts/import_recomp_document.py
   ```

### Phase 7: Verification

8. **Verify data was imported correctly**
   ```bash
   # Check database record counts
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web \
       python -c "
   from website import create_app, db
   from website.models import HealthMetric, MealLog, WorkoutSession, ExerciseLog, CoachingSession, BehaviorDefinition, BehaviorLog, Document, User

   app = create_app()
   with app.app_context():
       print('=== Database Record Counts ===')
       print(f'Users: {User.query.count()}')
       print(f'Health Metrics: {HealthMetric.query.count()}')
       print(f'Meal Logs: {MealLog.query.count()}')
       print(f'Workout Sessions: {WorkoutSession.query.count()}')
       print(f'Exercise Logs: {ExerciseLog.query.count()}')
       print(f'Coaching Sessions: {CoachingSession.query.count()}')
       print(f'Behavior Definitions: {BehaviorDefinition.query.count()}')
       print(f'Behavior Logs: {BehaviorLog.query.count()}')
       print(f'Documents: {Document.query.count()}')
   "
   ```

9. **Test the application**
   - Visit: https://vitruvian.bowmanhomelabtech.net
   - Login with admin credentials
   - Verify dashboard shows imported data
   - Check health metrics graph
   - Check behavior tracker

10. **Purge Cloudflare cache (if JavaScript changed)**
    - Go to Cloudflare dashboard
    - Purge cache or enable Development Mode for 3 hours

---

## Rollback Plan

If something goes wrong:

```bash
# SSH to remote server
ssh nathan@vit-dev-website
cd /home/nathan/vitruvian-developer

# Stop all containers
docker-compose -f docker-compose.yml -f docker-compose.remote.yml down

# Start fresh with rebuild
./scripts/rebuild_database.sh --remote
```

---

## One-Line Deployment (After Approval)

For convenience, here's a combined deployment command:

```bash
# From local machine (requires sshpass installed)
./scripts/deploy-remote.sh && \
sshpass -p "PASSWORD" ssh nathan@vit-dev-website "cd /home/nathan/vitruvian-developer && \
  ./scripts/rebuild_database.sh --remote && \
  docker cp Health_and_Fitness primary-assistant-web:/app/Health_and_Fitness && \
  docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web python /app/scripts/import-all-health-data.py && \
  docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web python /app/scripts/import_behavior_data.py /app/Health_and_Fitness/data/behavior-tracker.md && \
  docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec -T web python /app/scripts/import_recomp_document.py"
```

---

## Estimated Timeline

| Step | Duration |
|------|----------|
| Git push | ~1 min |
| Git pull on remote | ~30 sec |
| Database rebuild | ~3-5 min |
| Data imports | ~2-3 min |
| Verification | ~2 min |
| **Total** | **~10-12 min** |

---

## Notes

- The `import-all-health-data.py` script auto-confirms with 'y' when run via subprocess
- All import scripts skip duplicates (safe to re-run)
- The `rebuild_database.sh --remote` uses the remote docker-compose override file
- Data is copied to container because scripts check `/app/Health_and_Fitness/data/` path first
