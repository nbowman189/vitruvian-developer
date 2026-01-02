# Behavior Tracker Migration Guide

This guide explains how to migrate your behavior tracker data from the markdown file to the new database-backed system.

## What These Scripts Do

1. **Connect** to your remote server (vit-dev-website)
2. **Run** database migrations to create the new behavior tracking tables
3. **Copy** your `behavior-tracker.md` file from local to remote
4. **Parse** the markdown table to extract behavior categories and historical records
5. **Import** all data into the PostgreSQL database
6. **Clean up** temporary files

## Prerequisites

### macOS/Linux
- `sshpass` installed: `brew install hudochenkov/sshpass/sshpass`
- SSH access to the remote server

### Windows
- PuTTY installed (includes `plink` and `pscp`)
- Download from: https://www.putty.org/

## Files Overview

### 1. `migrate_and_import_behaviors.sh` (macOS/Linux)
Main orchestration script that handles the entire migration process.
⚠️ **NOT in git** - Contains credentials

### 2. `migrate_and_import_behaviors.bat` (Windows)
Windows version of the orchestration script using PuTTY tools.
⚠️ **NOT in git** - Contains credentials

### 3. `migrate_and_import_behaviors.sh.template` (macOS/Linux Template)
Template version without credentials - safe to commit to git.
Copy to `migrate_and_import_behaviors.sh` and add your credentials.

### 4. `migrate_and_import_behaviors.bat.template` (Windows Template)
Template version without credentials - safe to commit to git.
Copy to `migrate_and_import_behaviors.bat` and add your credentials.

### 5. `import_behavior_data.py`
Python script that:
- Parses the markdown table
- Creates BehaviorDefinition records for each column
- Imports historical BehaviorLog records for all ✅ marks

## Security Note

⚠️ **IMPORTANT**: The actual migration scripts (`*.sh` and `*.bat`) are excluded from git via `.gitignore` because they contain your server credentials. Only the template files (`*.template`) are committed to the repository. If you need to recreate the scripts:

1. Copy the template file:
   ```bash
   # macOS/Linux
   cp migrate_and_import_behaviors.sh.template migrate_and_import_behaviors.sh

   # Windows
   copy migrate_and_import_behaviors.bat.template migrate_and_import_behaviors.bat
   ```

2. Edit the Configuration section with your actual credentials

3. Make executable (macOS/Linux only):
   ```bash
   chmod +x migrate_and_import_behaviors.sh
   ```

## Usage

### macOS/Linux

```bash
cd /Users/nathanbowman/primary-assistant/scripts
./migrate_and_import_behaviors.sh
```

### Windows

```batch
cd C:\Users\%USERNAME%\primary-assistant\scripts
migrate_and_import_behaviors.bat
```

## What Gets Imported

### Behavior Definitions

The script will create behavior definitions for each column in your tracker:

| Behavior Name | Category | Icon | Color | Target Frequency |
|---------------|----------|------|-------|------------------|
| Weigh-In | HEALTH | bi-heart-pulse | #E27D60 | 7 days/week |
| Breakfast Logged | NUTRITION | bi-egg-fried | #E8A87C | 7 days/week |
| Lunch Logged | NUTRITION | bi-bowl-hot-fill | #E8A87C | 7 days/week |
| Dinner Logged | NUTRITION | bi-cup-hot-fill | #E8A87C | 7 days/week |
| Morning Snack | NUTRITION | bi-apple | #E8A87C | 5 days/week |
| Afternoon Snack | NUTRITION | bi-cookie | #E8A87C | 5 days/week |
| Evening Snack | NUTRITION | bi-moon-stars | #E8A87C | 3 days/week |
| Resistance Workout | FITNESS | bi-fire | #C38D9E | 4 days/week |
| Cardio / Walk | FITNESS | bi-heart | #C38D9E | 5 days/week |
| Tai Chi | WELLNESS | bi-yin-yang | #41B3A3 | 7 days/week |
| AI Curriculum | LEARNING | bi-brain | #4A90E2 | 7 days/week |
| Due Lingo Practice | LEARNING | bi-translate | #4A90E2 | 7 days/week |

### Historical Logs

For each date row in the markdown file:
- ✅ marks are imported as `completed=true`
- `-` marks (N/A) are skipped
- Empty cells are skipped

**Example:**
```
| 2025-12-08 | ✅ | ✅ | ✅ | ...
```
This creates BehaviorLog records for:
- Weigh-In on 2025-12-08 (completed)
- Breakfast Logged on 2025-12-08 (completed)
- Lunch Logged on 2025-12-08 (completed)
- ...and so on for all ✅ marks

## Expected Output

### Successful Migration

```
==================================================
Behavior Tracker Migration and Import
==================================================

[1/6] Copying import script to remote server...
✓ Import script copied

[2/6] Copying behavior-tracker.md to remote server...
✓ Behavior tracker file copied

[3/6] Running database migration...
Note: Migration may already exist

[4/6] Applying database migration...
✓ Database migration applied

[5/6] Importing behavior tracker data...

Reading file: /tmp/behavior-tracker.md
Found 13 columns: ['Date', 'Weigh-In', 'Breakfast Logged', ...]
Found 8 data rows

Importing 12 behavior definitions...
  ✓ Created 'Weigh-In' (Category: health, ID: 1)
  ✓ Created 'Breakfast Logged' (Category: nutrition, ID: 2)
  ...

✓ Behavior definitions created/verified

Importing historical behavior logs...

✓ Imported 87 behavior logs (0 skipped as duplicates)

==================================================
Import Complete!
==================================================

Summary:
  - Behavior Definitions: 12
  - Historical Records: 8 days

[6/6] Cleaning up temporary files...
✓ Cleanup complete

==================================================
Migration and Import Complete!
==================================================
```

## Verification Steps

After running the script:

1. **Visit the Dashboard**
   - Go to: https://vitruvian.bowmanhomelabtech.net/dashboard
   - Scroll to the "Daily Behaviors" section

2. **Check Behavior Definitions**
   - You should see all 12 behaviors listed
   - Each with appropriate icons and colors
   - Click "Manage Behaviors" to view full details

3. **Verify Historical Data**
   - Look at the "Behavior Completion Trends (30 Days)" chart
   - You should see historical completion data plotted
   - Check the stat cards for completion rates and streaks

4. **Test AI Integration**
   - Open AI Coach chat
   - Ask: "Show me my behavior tracking data for the past week"
   - AI should retrieve and discuss your imported data

## Troubleshooting

### "sshpass not found" (macOS/Linux)
```bash
brew install hudochenkov/sshpass/sshpass
```

### "plink not found" (Windows)
- Install PuTTY: https://www.putty.org/
- Add PuTTY directory to PATH (usually `C:\Program Files\PuTTY\`)

### "Connection refused"
- Verify remote server is accessible
- Check firewall settings
- Ensure SSH is running on remote server

### "Admin user not found"
The import script looks for a user with username `admin`. If you use a different username, edit `import_behavior_data.py`:

```python
user = User.query.filter_by(username='your_username').first()
```

### "Duplicate key error"
The script checks for existing behaviors and logs before creating. If you encounter this error:
1. Check if behaviors were already imported
2. Delete existing behaviors via dashboard "Manage Behaviors"
3. Re-run the script

### "Migration already exists"
This is normal if you've run the script before. The migration will be skipped, and only the upgrade step will run.

## Manual Migration (Alternative)

If the automated script fails, you can run steps manually:

### 1. SSH into remote server
```bash
ssh nathan@vit-dev-website
# Password: Serbatik11!!
```

### 2. Run migration
```bash
cd /home/nathan/primary-assistant
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec web flask db migrate -m "Add behavior tracking system"
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec web flask db upgrade
```

### 3. Copy files
```bash
# From local machine:
scp /Users/nathanbowman/primary-assistant/scripts/import_behavior_data.py nathan@vit-dev-website:/tmp/
scp /Users/nathanbowman/primary-assistant/Health_and_Fitness/data/behavior-tracker.md nathan@vit-dev-website:/tmp/
```

### 4. Run import
```bash
# On remote server:
cd /home/nathan/primary-assistant
docker cp /tmp/import_behavior_data.py primary-assistant-web:/tmp/
docker cp /tmp/behavior-tracker.md primary-assistant-web:/tmp/
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec web python /tmp/import_behavior_data.py /tmp/behavior-tracker.md
```

## Data Mapping Reference

### Completion Status
- `✅` → `completed=true` (behavior was done)
- `-` → Skipped (marked as N/A)
- Empty → Skipped (not logged)

### Category Mapping
| Markdown Column | Database Category Enum |
|----------------|------------------------|
| Weigh-In | HEALTH |
| *Logged meals | NUTRITION |
| *Snacks | NUTRITION |
| *Workouts | FITNESS |
| Tai Chi | WELLNESS |
| AI Curriculum, Due Lingo | LEARNING |

### Color Scheme
- **Health** (#E27D60): Coral
- **Nutrition** (#E8A87C): Peach
- **Fitness** (#C38D9E): Mauve
- **Wellness** (#41B3A3): Teal
- **Learning** (#4A90E2): Blue

## Notes

- **Idempotent**: Safe to run multiple times - checks for existing records
- **User Assignment**: All behaviors are assigned to the admin user
- **Soft Delete**: Existing behaviors won't be deleted, only marked inactive
- **Date Format**: Expects YYYY-MM-DD format in markdown
- **UTF-8 Encoding**: Markdown file must be UTF-8 encoded

## Support

If you encounter issues:
1. Check the script output for specific error messages
2. Verify database migration status: `flask db current`
3. Check Docker logs: `docker-compose logs web`
4. Review imported data in Django admin or database directly

---

**Last Updated**: January 2, 2026
**Version**: 1.0
