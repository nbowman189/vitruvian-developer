# Data Migration Tools

Comprehensive toolkit for migrating markdown health data to PostgreSQL database.

## Quick Start

```bash
# 1. Dry run to preview
python scripts/migrate_to_database.py --all --user-id 1 --dry-run

# 2. Run migration with backup
python scripts/migrate_to_database.py --all --user-id 1 --backup

# 3. Verify
python scripts/migrate_to_database.py --list-migrations
```

## Components

### Main Scripts

- **`migrate_to_database.py`** - Main migration orchestrator
- **`export_data.py`** - Export database back to markdown

### Migration Modules

- **`validators.py`** - Data validation and parsing utilities
- **`backup.py`** - Backup and restore functionality
- **`rollback.py`** - Rollback management with migration tracking
- **`migrate_health.py`** - Health metrics migration (check-in-log.md)
- **`migrate_workouts.py`** - Workout session migration (exercise-log.md)
- **`migrate_meals.py`** - Meal log migration (meal-log.md)
- **`migrate_coaching.py`** - Coaching session migration (Coaching_sessions.md)

## Common Commands

### Migration

```bash
# Full migration
python scripts/migrate_to_database.py --all --user-id 1 --backup

# Specific migrations
python scripts/migrate_to_database.py --health --user-id 1
python scripts/migrate_to_database.py --workouts --meals --user-id 1

# Dry run (preview)
python scripts/migrate_to_database.py --all --user-id 1 --dry-run

# Verbose output
python scripts/migrate_to_database.py --all --user-id 1 --verbose
```

### Rollback

```bash
# Dry run rollback
python scripts/migrate_to_database.py --rollback --user-id 1 --dry-run

# Rollback all
python scripts/migrate_to_database.py --rollback --user-id 1

# Rollback specific type
python scripts/migrate_to_database.py --rollback --rollback-type health --user-id 1
```

### Export

```bash
# Export all data
python scripts/export_data.py --all --user-id 1

# Export to specific directory
python scripts/export_data.py --all --user-id 1 --output backups/export/

# Export specific types
python scripts/export_data.py --health --workouts --user-id 1
```

### Utilities

```bash
# List migration history
python scripts/migrate_to_database.py --list-migrations

# List for specific user
python scripts/migrate_to_database.py --list-migrations --user-id 1
```

## Data Flow

```
Markdown Files                  PostgreSQL Database
─────────────────              ───────────────────────

check-in-log.md       ──────>  health_metrics
exercise-log.md       ──────>  workout_sessions + exercise_logs
meal-log.md           ──────>  meal_logs
Coaching_sessions.md  ──────>  coaching_sessions
```

## Migration Features

✅ **Safe Migration**
- Dry-run mode for preview
- Transactions (all-or-nothing)
- Duplicate detection

✅ **Data Validation**
- Date format validation
- Numeric range checking
- Text sanitization
- Required field verification

✅ **Backup & Recovery**
- Automatic backups
- Markdown file backup
- Database SQL dumps
- Rollback capabilities

✅ **Migration Tracking**
- JSON logs for each migration
- Migration history
- Rollback metadata

## Directory Structure

```
scripts/
├── migrate_to_database.py      # Main orchestrator
├── export_data.py              # Export utility
└── migrations/
    ├── validators.py           # Data validation
    ├── backup.py               # Backup/restore
    ├── rollback.py             # Rollback management
    ├── migrate_health.py       # Health migration
    ├── migrate_workouts.py     # Workout migration
    ├── migrate_meals.py        # Meal migration
    ├── migrate_coaching.py     # Coaching migration
    ├── MIGRATION_GUIDE.md      # Complete guide
    └── README.md               # This file

Generated:
backups/                        # Timestamped backups
logs/                           # Migration logs
  └── migrations/               # Migration tracking
exports/                        # Data exports
```

## Prerequisites

1. **PostgreSQL Running**
   ```bash
   docker-compose up -d
   ```

2. **Environment Variables** (`.env` file)
   ```
   POSTGRES_USER=portfolio_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=portfolio_db
   SECRET_KEY=your_secret_key
   ```

3. **User Account Created**
   ```python
   from website import create_app
   from website.models import db, User

   app = create_app()
   with app.app_context():
       user = User(username='your_username', email='your@email.com')
       user.set_password('password')
       db.session.add(user)
       db.session.commit()
       print(f"User ID: {user.id}")
   ```

## Validation Rules

### Health Metrics
- **Date**: YYYY-MM-DD (required)
- **Weight**: 50-1000 lbs (optional)
- **Body Fat**: 0-100% (optional)
- **Notes**: Text (optional)

### Workouts
- **Date**: YYYY-MM-DD (required)
- **Exercise Name**: Max 200 chars (required)
- **Sets**: 1-500 (optional)
- **Reps**: 1-500 (optional)
- **Notes**: Text (optional)

### Meals
- **Date**: YYYY-MM-DD (required)
- **Meal Type**: breakfast/lunch/dinner/snack (required)
- **Calories**: 0-10000 (optional)
- **Description**: Text (optional)

### Coaching
- **Date**: YYYY-MM-DD (required)
- **Title**: Text (optional)
- **Discussion Notes**: Text (optional)
- **Action Items**: List (optional)

## Error Handling

### Validation Errors
- Invalid rows logged but skipped
- Valid rows still migrated
- Check logs for details

### Database Errors
- Transactions rolled back on failure
- Nothing partially committed
- Safe to retry

### Duplicate Detection
- Checks user_id + date combination
- Skips existing entries
- Logs duplicates

## Logging

**Migration Logs**
- Location: `logs/migration_YYYYMMDD_HHMMSS.log`
- Contains: Detailed execution log with timestamps
- Format: Timestamped, leveled (INFO/WARNING/ERROR/DEBUG)

**Migration Tracking**
- Location: `logs/migrations/YYYYMMDD_HHMMSS_TYPE_userID.json`
- Contains: Migration metadata for rollback
- Format: JSON with migration ID, type, user, results

## Backups

**Automatic (Recommended)**
```bash
python scripts/migrate_to_database.py --all --user-id 1 --backup
```

**Manual**
```python
from scripts.migrations.backup import BackupManager
manager = BackupManager()
result = manager.create_full_backup()
```

**Backup Contents**
- `markdown_files/` - All markdown files
- `database_backup.sql` - PostgreSQL dump
- `BACKUP_SUMMARY.txt` - Backup metadata

## Testing

Run validation tests:
```bash
python scripts/migrations/validators.py
```

Test individual migrations with dry-run:
```bash
python scripts/migrate_to_database.py --health --user-id 1 --dry-run
```

## Documentation

See **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** for:
- Complete step-by-step instructions
- Detailed command reference
- Troubleshooting guide
- FAQ
- Data format specifications
- Best practices

## Support

1. Check `MIGRATION_GUIDE.md` for detailed documentation
2. Review migration logs in `logs/`
3. Run with `--verbose` for debugging
4. Use `--dry-run` to test safely

---

**Version:** 1.0.0
**Last Updated:** 2025-12-14
