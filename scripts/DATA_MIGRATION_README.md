# Health & Fitness Data Migration Guide

This guide explains how to migrate all health and fitness data from markdown files to the remote database.

## Overview

The migration scripts import all your historical health and fitness data from markdown files into the PostgreSQL database on the remote server. All data is automatically associated with the **admin user** (first user in database).

## Data Sources

The following markdown files are imported:

| Data File | Description | Database Table(s) |
|-----------|-------------|-------------------|
| `check-in-log.md` | Weight, body fat %, BMI | `health_metrics` |
| `exercise-log.md` | Workout sessions and exercises | `workout_sessions`, `exercise_logs`, `exercise_definitions` |
| `meal-log.md` | Meal logs and nutrition | `meal_logs` |
| `Coaching_sessions.md` | Coaching session notes | `coaching_sessions` |
| `behavior-tracker.md` | Habit tracking data | `behavior_definitions`, `behavior_logs` |

## Prerequisites

### Windows (.bat)
- **PuTTY** installed (plink and pscp must be in PATH)
- Download from: https://www.putty.org/

### Mac/Linux (.sh)
- **sshpass** installed
  - Mac: `brew install sshpass`
  - Linux: `apt-get install sshpass` or `yum install sshpass`

## Migration Scripts

### Complete Migration (All Data)

**Recommended:** Use these scripts to import all data at once.

#### Windows
```batch
cd scripts
migrate_and_import_all_data.bat
```

#### Mac/Linux
```bash
cd scripts
./migrate_and_import_all_data.sh
```

**What it does:**
1. Pulls latest code from git
2. Copies all import scripts to remote server
3. Copies all data files to remote server
4. Applies database migrations
5. Imports data in order:
   - Health metrics (weight, body fat)
   - Workout sessions and exercises
   - Meal logs and nutrition
   - Coaching sessions
   - Behavior tracker data
6. Cleans up temporary files
7. All data associated with admin user

### Individual Data Migration

If you want to import only specific data types, use the individual import scripts:

#### Behavior Tracker Only
```batch
# Windows
migrate_and_import_behaviors.bat

# Mac/Linux
./migrate_and_import_behaviors.sh
```

## Verification Steps

After running the migration:

1. **Visit Dashboard**
   - URL: https://vitruvian.bowmanhomelabtech.net/dashboard
   - Log in with admin credentials

2. **Check Health Metrics**
   - Navigate to Health Metrics page
   - Verify weight and body fat data appears
   - Check dates match your check-in-log.md

3. **Check Workouts**
   - Navigate to Workouts page
   - Verify workout sessions appear
   - Check exercise details

4. **Check Meals**
   - Navigate to Nutrition page
   - Verify meal logs appear
   - Check daily totals

5. **Check Coaching Sessions**
   - Navigate to Coaching page
   - Verify all sessions appear with correct dates

6. **Check Behaviors**
   - View Dashboard Daily Behaviors section
   - Verify behavior definitions created
   - Check historical completion data

## How Import Works

### Data Association
All imported data is automatically associated with the **admin user** (or first user if admin doesn't exist):

```python
# Each import script follows this pattern:
user = User.query.filter_by(username='admin').first()
if not user:
    user = User.query.first()  # Fallback to first user

# All records get this user_id
record.user_id = user.id
```

### Duplicate Handling
By default, duplicate records are **skipped**:

```python
existing = Model.query.filter_by(
    user_id=user.id,
    date_field=record.date
).first()

if existing:
    print("Skipping duplicate")
    continue
else:
    db.session.add(record)
```

### Error Handling
- Invalid data rows are skipped with warnings
- Errors don't stop the import process
- Summary shows: imported, skipped, errors

## Import Scripts Details

### Health Metrics (`import-health-data.py`)
- **Input:** `check-in-log.md`
- **Format:** Markdown table with columns: Date, Weight (lbs), Body Fat %, Notes
- **Calculates:** BMI (assumes 70" height by default)
- **Creates:** One `HealthMetric` record per row

### Workout Data (`import-exercise-log.py`)
- **Input:** `exercise-log.md`
- **Format:** Markdown table with columns: Date, Phase, Exercise, Sets, Reps, Weight
- **Groups:** Exercises by date into `WorkoutSession`
- **Creates:**
  - `ExerciseDefinition` for each unique exercise
  - `WorkoutSession` for each date
  - `ExerciseLog` for each exercise performed

### Meal Logs (`import-meal-log.py`)
- **Input:** `meal-log.md`
- **Format:** Markdown table with columns: Date, Time, Meal Type, Food, Calories
- **Aggregates:** Meals by date
- **Creates:** One `MealLog` per date with daily totals

### Coaching Sessions (`import-coaching-sessions.py`)
- **Input:** `Coaching_sessions.md`
- **Format:** Markdown sections with `## YYYY-MM-DD: Title` headers
- **Extracts:** Date, title, and full content
- **Creates:** One `CoachingSession` per section

### Behavior Tracker (`import_behavior_data.py`)
- **Input:** `behavior-tracker.md`
- **Format:** Markdown with behavior definitions and completion table
- **Creates:**
  - `BehaviorDefinition` for each unique behavior
  - `BehaviorLog` for each day's completion status

## Troubleshooting

### "File not found" errors
- **Cause:** Data file doesn't exist in `Health_and_Fitness/data/`
- **Solution:** Create the file or remove it from import (warnings are OK)

### "No users found" error
- **Cause:** Database has no users yet
- **Solution:** Run `scripts/create_admin_user.py` first

### Connection errors
- **Cause:** Can't connect to remote server
- **Solution:**
  - Check remote server is running: `ssh nathan@vit-dev-website`
  - Verify password is correct
  - Check network connection

### Import shows 0 records
- **Cause:** All records already exist (duplicates skipped)
- **Solution:** This is normal if you've already imported the data

### Permission errors on remote
- **Cause:** Docker container file permissions
- **Solution:** Scripts handle this automatically with `docker cp`

## Manual Import Process

If automated scripts fail, you can import manually:

1. **SSH to server:**
   ```bash
   ssh nathan@vit-dev-website
   cd /home/nathan/vitruvian-developer
   ```

2. **Copy import script:**
   ```bash
   docker cp /path/to/import-health-data.py primary-assistant-web:/tmp/
   docker cp /path/to/check-in-log.md primary-assistant-web:/tmp/
   ```

3. **Run import:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec web \
     python /tmp/import-health-data.py /tmp/check-in-log.md
   ```

4. **Cleanup:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec web \
     rm /tmp/import-health-data.py /tmp/check-in-log.md
   ```

## Database Schema Notes

All data is stored in PostgreSQL with proper relationships:

- **user_id**: Foreign key to `users` table
- **Date fields**:
  - `health_metrics.recorded_date`
  - `workout_sessions.session_date`
  - `meal_logs.meal_date`
  - `coaching_sessions.session_date`
  - `behavior_logs.tracked_date`

Each user's data is isolated by `user_id`. The admin user owns all imported data.

## Next Steps After Import

1. **Verify Data Integrity**
   - Spot check a few records manually
   - Verify date ranges match source files
   - Check totals/counts

2. **Test API Endpoints**
   - Dashboard should populate automatically
   - Check charts render correctly
   - Verify filtering and pagination work

3. **Backup Database**
   ```bash
   ./scripts/backup-database.sh
   ```

4. **Document Import Date**
   - Record when you ran the import
   - Note any issues or manual fixes needed

## Support

For issues or questions:
- Check import script output for specific error messages
- Review Flask logs: `docker-compose logs web`
- Check database directly: `docker-compose exec db psql -U vitruvian_dev`
