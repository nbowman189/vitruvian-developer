# Data Migration Guide

Complete guide for migrating markdown data to PostgreSQL database.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Migration Components](#migration-components)
5. [Step-by-Step Migration](#step-by-step-migration)
6. [Command Reference](#command-reference)
7. [Backup and Rollback](#backup-and-rollback)
8. [Data Format Specifications](#data-format-specifications)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Overview

This migration system safely moves health and fitness data from markdown files to a PostgreSQL database while preserving data integrity and providing rollback capabilities.

### What Gets Migrated

- **Health Metrics** (`check-in-log.md`) → `health_metrics` table
- **Workout Sessions** (`exercise-log.md`) → `workout_sessions` + `exercise_logs` tables
- **Meal Logs** (`meal-log.md`) → `meal_logs` table
- **Coaching Sessions** (`Coaching_sessions.md`) → `coaching_sessions` table

### Key Features

- **Safe Migration**: Dry-run mode to preview changes
- **Data Validation**: Comprehensive validation before insertion
- **Backup Creation**: Automatic backup of markdown files and database
- **Duplicate Detection**: Skips existing entries
- **Transaction Safety**: All-or-nothing insertions with rollback on errors
- **Migration Tracking**: Logs all migrations for audit and rollback
- **Data Export**: Export database back to markdown format

---

## Prerequisites

### 1. Database Setup

Ensure PostgreSQL is running with the correct database:

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# If not running, start it
cd /Users/nathanbowman/primary-assistant
docker-compose up -d
```

### 2. Environment Variables

Ensure `.env` file exists with database credentials:

```bash
# .env file
POSTGRES_USER=portfolio_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=portfolio_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
SECRET_KEY=your_secret_key
```

### 3. Python Dependencies

```bash
# Install required packages
pip install -r scripts/requirements.txt
```

Required packages:
- SQLAlchemy
- Flask-SQLAlchemy
- psycopg2-binary
- python-dotenv

### 4. User Account

You need a user account in the database. Create one if needed:

```python
# In Python shell
from website import create_app
from website.models import db, User

app = create_app()
with app.app_context():
    user = User(username='your_username', email='your@email.com')
    user.set_password('your_password')
    db.session.add(user)
    db.session.commit()
    print(f"Created user with ID: {user.id}")
```

---

## Quick Start

### Most Common Use Case: Full Migration with Backup

```bash
# 1. Dry run first (preview without changes)
python scripts/migrate_to_database.py --all --user-id 1 --dry-run

# 2. If preview looks good, run actual migration with backup
python scripts/migrate_to_database.py --all --user-id 1 --backup

# 3. Verify migration
python scripts/migrate_to_database.py --list-migrations
```

That's it! Your data is now in the database.

---

## Migration Components

### Directory Structure

```
scripts/
├── migrate_to_database.py          # Main orchestrator
├── export_data.py                  # Export database to markdown
└── migrations/
    ├── __init__.py
    ├── validators.py               # Data validation utilities
    ├── backup.py                   # Backup/restore functionality
    ├── rollback.py                 # Rollback management
    ├── migrate_health.py           # Health metrics migration
    ├── migrate_workouts.py         # Workout migration
    ├── migrate_meals.py            # Meal log migration
    ├── migrate_coaching.py         # Coaching migration
    └── MIGRATION_GUIDE.md          # This file

Generated directories:
backups/                            # Timestamped backups
logs/                               # Migration logs
  └── migrations/                   # Migration tracking logs
exports/                            # Data exports
```

### Component Descriptions

**validators.py**
- Validates dates (YYYY-MM-DD format)
- Validates numeric ranges (weight, body fat, calories)
- Validates text fields (max length, required fields)
- Parses sets/reps notation ("3 sets of 10 reps", "3x10")
- Sanitizes input (strips whitespace, normalizes text)

**backup.py**
- Creates timestamped backups of markdown files
- Exports database to SQL dump using pg_dump
- Verifies backup integrity
- Lists available backups

**rollback.py**
- Tracks all migrations in logs/migrations/
- Provides selective rollback by migration type
- Dry-run mode for rollback preview
- Migration history listing

**migrate_health.py**
- Parses check-in-log.md table format
- Validates weight and body fat percentage
- Detects duplicate entries (same user + date)
- Inserts into health_metrics table

**migrate_workouts.py**
- Parses exercise-log.md table format
- Groups exercises by date into workout sessions
- Creates workout_sessions and exercise_logs entries
- Links exercises to exercise definitions

**migrate_meals.py**
- Parses meal-log.md table format
- Extracts calories from various formats (~800, 800)
- Maps meal types to enum values
- Inserts into meal_logs table

**migrate_coaching.py**
- Parses Coaching_sessions.md markdown sections
- Extracts dates, titles, subjects, action items
- Creates coaching_sessions entries
- Links to user and coach

---

## Step-by-Step Migration

### Step 1: Review Source Data

Before migrating, review your markdown files:

```bash
# Check data files exist
ls -l Health_and_Fitness/data/

# Expected files:
# - check-in-log.md
# - exercise-log.md
# - meal-log.md
# - Coaching_sessions.md
```

### Step 2: Create a Backup

Always backup before migration:

```bash
# Create full backup (markdown + database)
python -c "
from scripts.migrations.backup import BackupManager
manager = BackupManager()
result = manager.create_full_backup()
print(f'Backup created: {result[\"backup_dir\"]}')"

# Backup location: backups/YYYY-MM-DD_HHMMSS/
```

### Step 3: Dry Run Migration

Preview migration without making changes:

```bash
# Preview all migrations
python scripts/migrate_to_database.py --all --user-id 1 --dry-run

# Preview specific migration
python scripts/migrate_to_database.py --health --user-id 1 --dry-run
```

Review the output:
- Total rows parsed
- Valid vs invalid rows
- Duplicate detection
- What would be inserted

### Step 4: Run Migration

If dry run looks good, run actual migration:

```bash
# Full migration with backup
python scripts/migrate_to_database.py --all --user-id 1 --backup

# Or run specific migrations
python scripts/migrate_to_database.py --health --workouts --user-id 1
```

### Step 5: Verify Migration

Check migration results:

```bash
# View migration history
python scripts/migrate_to_database.py --list-migrations --user-id 1

# Check migration log
tail -n 100 logs/migration_YYYYMMDD_HHMMSS.log

# Verify in database
python -c "
from website import create_app
from website.models import db, HealthMetric

app = create_app()
with app.app_context():
    count = db.session.query(HealthMetric).filter_by(user_id=1).count()
    print(f'Health metrics in database: {count}')
"
```

### Step 6: Test Application

Test that the application works with migrated data:

```bash
# Start Flask application
cd website
python app-private.py

# Visit http://localhost:8081 and verify data displays correctly
```

### Step 7: Export Data (Optional)

Export database back to markdown for verification:

```bash
# Export all data
python scripts/export_data.py --all --user-id 1 --output exports/verification/

# Compare with original
diff Health_and_Fitness/data/check-in-log.md exports/verification/check-in-log.md
```

---

## Command Reference

### Main Migration Script

```bash
python scripts/migrate_to_database.py [OPTIONS]
```

**Migration Selection:**
- `--all` - Run all migrations
- `--health` - Migrate health metrics only
- `--workouts` - Migrate workouts only
- `--meals` - Migrate meals only
- `--coaching` - Migrate coaching sessions only

**Required Arguments:**
- `--user-id USER_ID` - User ID to migrate data for

**Optional Arguments:**
- `--coach-id COACH_ID` - Coach ID for coaching sessions (defaults to user-id)
- `--dry-run` - Simulate without inserting data
- `--backup` - Create backup before migration
- `--skip-duplicates` - Skip existing entries (default: True)
- `--verbose, -v` - Verbose logging

**Rollback:**
- `--rollback` - Rollback migrations
- `--rollback-type {all,health,workouts,meals,coaching}` - Type to rollback

**Utilities:**
- `--list-migrations` - Show migration history

### Data Export Script

```bash
python scripts/export_data.py [OPTIONS]
```

**Export Selection:**
- `--all` - Export all data types
- `--health` - Export health metrics
- `--workouts` - Export workouts
- `--meals` - Export meals
- `--coaching` - Export coaching sessions

**Required Arguments:**
- `--user-id USER_ID` - User ID to export

**Optional Arguments:**
- `--output DIR` - Output directory (default: exports/TIMESTAMP)

### Examples

```bash
# Full migration with backup
python scripts/migrate_to_database.py --all --user-id 1 --backup

# Health and workouts only (no backup, dry run)
python scripts/migrate_to_database.py --health --workouts --user-id 1 --dry-run

# Actual health migration
python scripts/migrate_to_database.py --health --user-id 1

# Rollback all migrations (dry run)
python scripts/migrate_to_database.py --rollback --user-id 1 --dry-run

# Actual rollback of health data
python scripts/migrate_to_database.py --rollback --rollback-type health --user-id 1

# List migration history
python scripts/migrate_to_database.py --list-migrations --user-id 1

# Export all data
python scripts/export_data.py --all --user-id 1

# Export to specific directory
python scripts/export_data.py --all --user-id 1 --output backups/manual_export/
```

---

## Backup and Rollback

### Creating Backups

**Automatic Backup (Recommended):**
```bash
python scripts/migrate_to_database.py --all --user-id 1 --backup
```

**Manual Backup:**
```python
from scripts.migrations.backup import BackupManager

manager = BackupManager()

# Full backup
result = manager.create_full_backup()

# Markdown only
result = manager.backup_markdown_files()

# Database only
result = manager.backup_database()
```

### Backup Structure

```
backups/
└── 2025-12-14_153045/
    ├── BACKUP_SUMMARY.txt           # Summary of backup
    ├── markdown_files/              # All markdown files
    │   ├── check-in-log.md
    │   ├── exercise-log.md
    │   ├── meal-log.md
    │   ├── Coaching_sessions.md
    │   └── BACKUP_MANIFEST.txt
    └── database_backup.sql          # PostgreSQL dump
```

### Listing Backups

```python
from scripts.migrations.backup import BackupManager

manager = BackupManager()
backups = manager.list_backups()

for backup in backups:
    print(f"{backup['timestamp']}: {backup['markdown_file_count']} files, "
          f"{backup['database_size_bytes']:,} bytes")
```

### Restoring from Backup

**Restore Markdown Files:**
```python
from scripts.migrations.backup import BackupManager
from pathlib import Path

manager = BackupManager()
backup_dir = Path('backups/2025-12-14_153045')

result = manager.restore_markdown_files(backup_dir)
print(f"Restored {result['files_restored']} files")
```

**Restore Database:**
```bash
# Using psql
psql -h localhost -U portfolio_user -d portfolio_db < backups/2025-12-14_153045/database_backup.sql
```

### Rollback Migrations

**Dry Run (Preview):**
```bash
# Preview rollback of all data
python scripts/migrate_to_database.py --rollback --user-id 1 --dry-run

# Preview specific rollback
python scripts/migrate_to_database.py --rollback --rollback-type health --user-id 1 --dry-run
```

**Actual Rollback:**
```bash
# Rollback all migrations
python scripts/migrate_to_database.py --rollback --user-id 1

# Rollback specific migration type
python scripts/migrate_to_database.py --rollback --rollback-type health --user-id 1
```

**Programmatic Rollback:**
```python
from website import create_app
from website.models import db
from scripts.migrations.rollback import RollbackManager

app = create_app()
with app.app_context():
    manager = RollbackManager(db.session)

    # Rollback all (dry run)
    result = manager.rollback_all(user_id=1, dry_run=True)

    # Actual rollback
    result = manager.rollback_health_metrics(user_id=1, dry_run=False)
```

---

## Data Format Specifications

### Health Metrics (check-in-log.md)

**Format:**
```markdown
| Date | Weight (lbs) | Body Fat % | Notes |
| :--------- | :----------- | :--------- | :---------------------------------- |
| 2024-11-14 | 175.5 | 22.3 | Feeling strong |
| 2024-11-15 | 174.8 | None | |
```

**Rules:**
- Date: YYYY-MM-DD format (required)
- Weight: Float, 50-1000 lbs (optional)
- Body Fat: Float, 0-100% (optional)
- Notes: Text (optional)
- "None" or empty = NULL in database
- Duplicate detection: same user + date

### Workout Sessions (exercise-log.md)

**Format:**
```markdown
| Date | Phase | Workout | Exercise | Sets x Reps | Notes |
| 2024-11-17 | Phase 1 | Bodyweight Foundation | Push-ups | 3 sets of 15 reps | Completed |
| 2024-11-17 | Phase 1 | Daily Walk | Walking | 2 hours | |
```

**Sets x Reps Parsing:**
- "3 sets of 10 reps" → 3 sets, 10 reps
- "3x10" → 3 sets, 10 reps
- "3 sets: 15, 12, 10 reps" → 3 sets, 12 reps (average)
- "30 minutes" → duration_seconds
- "N/A" → NULL

**Session Grouping:**
- Exercises on same date + same workout type = one session
- Creates WorkoutSession + linked ExerciseLog entries

### Meal Logs (meal-log.md)

**Format:**
```markdown
| Date | Meal | Food/Drink | Calories (est.) | Notes |
| 2024-12-07 | Dinner | Mixed greens, chicken, dressing | ~1000 | Satiety: 8/10 |
| 2024-12-08 | Breakfast | 2x Breakfast Burritos | ~800 | |
```

**Calorie Parsing:**
- "~800" → 800
- "800" → 800
- Empty/None → NULL

**Meal Type Mapping:**
- "Breakfast" → BREAKFAST
- "Lunch" → LUNCH
- "Dinner" → DINNER
- "Morning Snack" → SNACK
- "Afternoon Snack" → SNACK
- "Evening Snack" → SNACK

### Coaching Sessions (Coaching_sessions.md)

**Format:**
```markdown
## 2025-12-10: Mid-Week Analysis

**Trainer:** The Transformative Trainer

**Subject:** Assessment of progress

[Session content...]

**Orders:**
* **Stay the Course:** The plan is working.
* **Prioritize Recovery:** Focus on hydration.
```

**Parsing:**
- Header: ## YYYY-MM-DD: Title
- Trainer: extracted from **Trainer:** line
- Subject: extracted from **Subject:** line
- Discussion notes: full content
- Action items: extracted from **Orders:** section

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error:** "Database connection failed"

**Solution:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Start if not running
docker-compose up -d

# Check environment variables
cat .env | grep POSTGRES

# Test connection manually
psql -h localhost -U portfolio_user -d portfolio_db
```

#### 2. No Data Found

**Error:** "No metrics found to migrate"

**Solution:**
```bash
# Check file exists
ls -l Health_and_Fitness/data/check-in-log.md

# Check file format (should have table header)
head -5 Health_and_Fitness/data/check-in-log.md

# Check file permissions
stat Health_and_Fitness/data/check-in-log.md
```

#### 3. Validation Errors

**Error:** "Line X: Validation failed"

**Solution:**
- Check date format (must be YYYY-MM-DD)
- Check numeric values are reasonable
- Check for special characters or formatting issues
- Review migration log for specific errors
- Run with `--verbose` flag for detailed output

#### 4. Duplicate Entries

**Error:** "UNIQUE constraint failed"

**Solution:**
- Use `--skip-duplicates` flag (default behavior)
- Or rollback and re-migrate
- Check for duplicate dates in source file

#### 5. Permission Denied

**Error:** "Permission denied"

**Solution:**
```bash
# Check file permissions
chmod 644 Health_and_Fitness/data/*.md

# Check directory permissions
chmod 755 Health_and_Fitness/data/

# Check script permissions
chmod +x scripts/migrate_to_database.py
```

### Debugging

**Enable Verbose Logging:**
```bash
python scripts/migrate_to_database.py --all --user-id 1 --verbose
```

**Check Migration Log:**
```bash
# Find latest log
ls -lt logs/migration_*.log | head -1

# View log
tail -100 logs/migration_YYYYMMDD_HHMMSS.log
```

**Test Individual Components:**
```python
# Test validators
python scripts/migrations/validators.py

# Test health migration parsing
from scripts.migrations.migrate_health import HealthMetricsMigrator
from website import create_app
from website.models import db

app = create_app()
with app.app_context():
    migrator = HealthMetricsMigrator(db.session, user_id=1)
    metrics = migrator.parse_markdown_table()
    print(f"Parsed {len(metrics)} metrics")

    valid, invalid = migrator.validate_metrics(metrics)
    print(f"Valid: {len(valid)}, Invalid: {len(invalid)}")

    for inv in invalid:
        print(f"Line {inv['line_number']}: {inv['errors']}")
```

### Getting Help

If issues persist:

1. Check the migration log: `logs/migration_*.log`
2. Run with `--verbose` flag
3. Test with `--dry-run` first
4. Create a backup before attempting fixes
5. Review this guide's FAQ section

---

## FAQ

### General Questions

**Q: Is migration safe?**

A: Yes. Use `--dry-run` to preview, `--backup` to create backups, and migrations use transactions (all-or-nothing). If something fails, rollback is available.

**Q: Can I migrate data multiple times?**

A: Yes. Duplicate detection skips existing entries by default (same user + date). Running migration again will only add new entries.

**Q: Will migration delete my markdown files?**

A: No. Migration is read-only for markdown files. They remain unchanged.

**Q: How long does migration take?**

A: Depends on data volume. Typical migration (~100 health metrics, 50 workouts, 100 meals) takes under 1 minute.

**Q: Can I migrate data for multiple users?**

A: Yes. Run migration separately for each user ID:
```bash
python scripts/migrate_to_database.py --all --user-id 1
python scripts/migrate_to_database.py --all --user-id 2
```

### Data-Specific Questions

**Q: What if some dates are invalid?**

A: Invalid rows are logged but skipped. Valid rows are still migrated. Check log for details:
```
Line 45: Validation failed: date has invalid format (expected YYYY-MM-DD): 11/14/2024
```

**Q: How are "None" values handled?**

A: "None", "N/A", "null", and empty values are converted to NULL in database.

**Q: What about partial data (weight but no body fat)?**

A: Perfectly fine. All metrics except date are optional.

**Q: Can I migrate custom data fields?**

A: Current migrators handle standard fields. For custom fields, extend the migrator classes or modify the source markdown to match expected format.

### Technical Questions

**Q: Where are migrations logged?**

A: Two locations:
- Migration execution log: `logs/migration_YYYYMMDD_HHMMSS.log`
- Migration tracking (for rollback): `logs/migrations/YYYYMMDD_HHMMSS_TYPE_userID.json`

**Q: How does duplicate detection work?**

A: Queries database for existing entry with same user_id + date. If found, skips insertion.

**Q: Can I customize validation rules?**

A: Yes. Edit `scripts/migrations/validators.py` and modify validation functions.

**Q: What happens if migration fails mid-way?**

A: Transactions ensure all-or-nothing. If any insertion fails, entire batch is rolled back. Nothing is partially committed.

**Q: Can I migrate to a different database?**

A: Yes. Change database connection settings in `.env` file before running migration.

### Rollback Questions

**Q: Can I rollback specific entries?**

A: Current rollback is all-or-nothing per data type. For selective rollback, use SQL directly or export→modify→re-import.

**Q: What happens to database IDs after rollback?**

A: IDs are not reused. After rollback→re-migration, entries will have new IDs.

**Q: Can I undo a rollback?**

A: If you created a backup before rollback, restore from backup. Otherwise, re-run migration from markdown files.

### Export Questions

**Q: Is exported markdown identical to original?**

A: Very close, but may have minor formatting differences. Data content is identical.

**Q: Can I use export for backups?**

A: Yes, but pg_dump (database backup) is recommended for complete backup including all fields and metadata.

**Q: Can I edit exported markdown and re-import?**

A: Yes. Edit exported files, rollback database, then re-migrate edited files.

---

## Best Practices

1. **Always dry-run first**: Preview changes with `--dry-run`
2. **Create backups**: Use `--backup` flag for safety
3. **Verify data**: Check migration logs and exported data
4. **Test incrementally**: Migrate one data type at a time first
5. **Keep markdown files**: Don't delete original files until verified
6. **Monitor logs**: Check `logs/` directory for errors
7. **Use version control**: Commit markdown files before migration
8. **Document custom changes**: If you modify migrators, document changes

---

## Support

For issues or questions:

1. Review this guide thoroughly
2. Check migration logs: `logs/migration_*.log`
3. Run with `--verbose` for detailed output
4. Test with `--dry-run` to diagnose issues
5. Review source code comments in `scripts/migrations/`

---

**Last Updated:** 2025-12-14

**Version:** 1.0.0
