# Database Architecture Documentation

## Overview

Complete PostgreSQL database schema with SQLAlchemy models for multi-user health & fitness tracking application. This document provides comprehensive documentation for the database architecture, models, and migration system.

## Project Structure

```
primary-assistant/
├── website/
│   └── models/
│       ├── __init__.py           # Models package initialization and db instance
│       ├── user.py               # User authentication and profiles
│       ├── health.py             # Health metrics tracking
│       ├── workout.py            # Workout sessions and exercises
│       ├── coaching.py           # Coaching, goals, and progress photos
│       ├── nutrition.py          # Meal logs and nutrition tracking
│       └── session.py            # Session management and security
├── migrations/
│   ├── env.py                    # Alembic environment configuration
│   ├── script.py.mako            # Migration template
│   └── versions/
│       └── 001_initial_schema.py # Initial database migration
├── scripts/
│   └── init_db.sql               # PostgreSQL initialization script
└── alembic.ini                   # Alembic configuration file
```

## Database Models

### 1. User Model (`website/models/user.py`)

**Purpose**: User authentication and profile management with Flask-Login integration.

**Key Features**:
- Password hashing with bcrypt
- Role-based access control (user, admin, coach)
- Account security (login attempts, account locking)
- Profile information (name, photo, bio)

**Fields**:
- `id`: Primary key
- `username`: Unique username (indexed)
- `email`: Unique email (indexed)
- `password_hash`: Bcrypt hashed password
- `role`: User role (user/admin/coach)
- `is_active`: Account status
- `full_name`, `profile_photo_url`, `bio`: Profile fields
- `created_at`, `updated_at`, `last_login`: Timestamps
- `failed_login_attempts`, `locked_until`: Security fields

**Relationships**:
- One-to-many: health_metrics, workout_sessions, goals, progress_photos, meal_logs, sessions
- One-to-many (as coach): coached_sessions

**Methods**:
- `set_password(password)`: Hash and store password
- `check_password(password)`: Verify password
- `is_locked()`: Check if account is locked
- `lock_account(duration_minutes)`: Lock account
- `unlock_account()`: Unlock account
- `to_dict(include_sensitive)`: Serialize to dictionary

### 2. HealthMetric Model (`website/models/health.py`)

**Purpose**: Track health measurements like weight, body fat, BMI, and body measurements.

**Replaces**: `Health_and_Fitness/data/check-in-log.md`

**Fields**:
- `id`: Primary key
- `user_id`: Foreign key to users (CASCADE)
- `recorded_date`: Date of measurement
- Body composition: `weight_lbs`, `body_fat_percentage`, `muscle_mass_lbs`, `bmi`
- Measurements: `waist_inches`, `chest_inches`, `left_arm_inches`, `right_arm_inches`, etc.
- Vital signs: `resting_heart_rate`, `blood_pressure_systolic`, `blood_pressure_diastolic`
- Wellness: `energy_level`, `mood`, `sleep_quality`, `stress_level` (1-10 scale)
- `notes`: Additional context

**Constraints**:
- Unique: (user_id, recorded_date)
- Check constraints on all rating scales and vital sign ranges

**Calculated Properties**:
- `lean_body_mass_lbs`: Calculated from weight and body fat
- `fat_mass_lbs`: Calculated fat mass
- `blood_pressure_formatted`: "120/80" format

### 3. Workout Models (`website/models/workout.py`)

#### WorkoutSession

**Purpose**: Track overall workout sessions.

**Replaces**: `Health_and_Fitness/data/progress-check-in-log.md`

**Fields**:
- `id`: Primary key
- `user_id`: Foreign key to users (CASCADE)
- `session_date`: Workout date
- `session_type`: Enum (strength, cardio, flexibility, martial_arts, sports, recovery, mixed)
- `duration_minutes`: Session duration
- Program tracking: `program_phase`, `week_number`, `day_number`
- Feedback: `intensity`, `fatigue`, `soreness` (1-10 scale)
- `notes`, `coach_notes`: Text notes

**Calculated Properties**:
- `total_exercises`: Count of exercises
- `total_sets`: Sum of all sets
- `average_rpe`: Average rate of perceived exertion

#### ExerciseLog

**Purpose**: Track individual exercise performance within a workout.

**Fields**:
- `id`: Primary key
- `workout_session_id`: Foreign key to workout_sessions (CASCADE)
- `exercise_definition_id`: Optional foreign key to exercise_definitions
- `exercise_name`: Exercise name
- Performance: `sets`, `reps`, `weight_lbs`, `rest_seconds`
- Cardio: `duration_seconds`, `distance_miles`
- Feedback: `form_quality`, `rpe` (1-10 scale)
- `order_index`: Order within workout
- `notes`: Additional context

**Calculated Properties**:
- `total_volume`: sets × reps × weight
- `pace_per_mile`: Minutes per mile for cardio

#### ExerciseDefinition

**Purpose**: Shared exercise reference database.

**Fields**:
- `id`: Primary key
- `name`: Exercise name (unique)
- `category`: Enum (compound, isolation, cardio, flexibility, core, plyometric, martial_arts)
- `muscle_groups`: Array of muscle groups
- `equipment_needed`: Array of equipment
- `difficulty_level`: Enum (beginner, intermediate, advanced, expert)
- Rich content: `description`, `instructions`, `tips`, `video_url`, `image_url`
- `is_active`: Whether exercise is active

### 4. Coaching Models (`website/models/coaching.py`)

#### CoachingSession

**Purpose**: Track coaching sessions and feedback.

**Replaces**: `Health_and_Fitness/data/Coaching_sessions.md`

**Fields**:
- `id`: Primary key
- `user_id`: Foreign key to users (CASCADE)
- `coach_id`: Foreign key to users (CASCADE)
- `session_date`: Session date
- `duration_minutes`: Session duration
- Content: `topics` (array), `discussion_notes`, `coach_feedback`, `action_items` (array)
- Follow-up: `next_session_date`, `completed`, `completion_notes`
- `user_rating`: Session rating (1-10 scale)

**Calculated Properties**:
- `is_overdue`: Check if action items are overdue
- `days_until_next_session`: Days until next session

#### UserGoal

**Purpose**: Track user goals with progress monitoring.

**Fields**:
- `id`: Primary key
- `user_id`: Foreign key to users (CASCADE)
- `goal_type`: Enum (weight_loss, muscle_gain, strength, endurance, flexibility, skill, habit, nutrition, other)
- `title`, `description`: Goal information
- Target: `target_value`, `target_unit`, `target_date`
- Progress: `current_value`, `progress_percentage`
- Timeline: `start_date`, `completed_date`
- `status`: Enum (active, completed, paused, abandoned)
- `notes`, `milestones` (array)

**Methods**:
- `calculate_progress(current_value)`: Calculate progress percentage
- `update_progress(current_value, auto_complete)`: Update progress and auto-complete if target reached

**Calculated Properties**:
- `is_overdue`: Check if goal is overdue
- `days_remaining`: Days until target date
- `days_active`: Days since start

#### ProgressPhoto

**Purpose**: Track progress photos with metadata.

**Fields**:
- `id`: Primary key
- `user_id`: Foreign key to users (CASCADE)
- `photo_date`: Photo date
- `photo_url`: Photo URL
- `photo_type`: Enum (front, side, back, flex, comparison, other)
- Snapshot: `weight_lbs`, `body_fat_percentage`
- `notes`: Context
- `is_public`: Whether photo is public

### 5. MealLog Model (`website/models/nutrition.py`)

**Purpose**: Track meal logs and nutrition intake.

**Fields**:
- `id`: Primary key
- `user_id`: Foreign key to users (CASCADE)
- `meal_date`, `meal_time`: When meal was consumed
- `meal_type`: Enum (breakfast, lunch, dinner, snack, pre_workout, post_workout, other)
- Nutrition: `calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `sugar_g`, `sodium_mg`, `water_oz`
- Meal details: `description`, `foods`, `recipe_name`
- Adherence: `adherence_to_plan` (enum), `planned_meal` (boolean)
- Feedback: `satisfaction`, `hunger_before`, `hunger_after` (1-10 scale)
- `notes`: Additional context

**Calculated Properties**:
- `calories_from_protein/carbs/fat`: Calculated calories from macros
- `calculated_total_calories`: Sum of macro calories
- `protein/carbs/fat_percentage`: Percentage of calories from each macro
- `macronutrient_ratio`: "40/30/30" format

### 6. UserSession Model (`website/models/session.py`)

**Purpose**: Manage user sessions for authentication and security.

**Fields**:
- `session_id`: Primary key (UUID)
- `user_id`: Foreign key to users (CASCADE)
- Timestamps: `created_at`, `expires_at`, `last_activity`
- Security: `ip_address`, `user_agent`
- Status: `is_active`, `revoked_at`, `revocation_reason`
- Device: `device_type`, `browser`, `os`
- `remember_me`: Persistent session flag

**Methods**:
- `create_session()`: Class method to create new session
- `is_expired()`: Check if session expired
- `is_valid()`: Check if session is valid
- `revoke(reason)`: Revoke session
- `extend_session(hours)`: Extend expiration
- `update_activity()`: Update last activity
- `parse_user_agent()`: Parse user agent string

**Calculated Properties**:
- `time_until_expiration`: Time remaining
- `time_since_activity`: Time since last activity
- `session_age`: Total session age

## Database Constraints

### Foreign Keys
All user_id foreign keys use `ON DELETE CASCADE` to automatically clean up user data when a user is deleted.

### Unique Constraints
- User: username, email
- HealthMetric: (user_id, recorded_date)
- ExerciseDefinition: name

### Check Constraints
- All rating scales (1-10): energy_level, mood, intensity, fatigue, rpe, etc.
- Vital signs: Valid ranges for heart rate, blood pressure
- Nutrition: Valid ranges for calories, macronutrients
- Body composition: Valid ranges for body fat %, BMI

### Indexes
Performance indexes on:
- All foreign keys (user_id)
- Date fields (recorded_date, session_date, meal_date, photo_date)
- Composite indexes for common queries (user_id + date)
- Status and type fields for filtering

## Alembic Migrations

### Setup

1. **Install Alembic**:
   ```bash
   pip install alembic
   ```

2. **Configure database URL** in `alembic.ini` or set environment variable:
   ```bash
   export DATABASE_URL="postgresql://fitness_user:fitness_password@localhost:5432/fitness_db"
   ```

3. **Run initial migration**:
   ```bash
   alembic upgrade head
   ```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create blank migration
alembic revision -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## PostgreSQL Setup

### Using Docker

```bash
# Start PostgreSQL container
docker run --name fitness-postgres \
  -e POSTGRES_USER=fitness_user \
  -e POSTGRES_PASSWORD=fitness_password \
  -e POSTGRES_DB=fitness_db \
  -p 5432:5432 \
  -d postgres:15

# Initialize database
docker exec -i fitness-postgres psql -U fitness_user -d fitness_db < scripts/init_db.sql

# Run migrations
alembic upgrade head
```

### Manual Setup

```bash
# Create database and user
psql -U postgres -c "CREATE DATABASE fitness_db;"
psql -U postgres -c "CREATE USER fitness_user WITH PASSWORD 'fitness_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE fitness_db TO fitness_user;"

# Initialize database
psql -U fitness_user -d fitness_db -f scripts/init_db.sql

# Run migrations
alembic upgrade head
```

## Data Migration from Markdown

To migrate existing markdown data to the database, you'll need to create migration scripts:

### Health Metrics Migration
```python
# Example: Migrate from check-in-log.md
from website.models import db, User, HealthMetric
import pandas as pd
from datetime import datetime

def migrate_health_data(user_id, markdown_file):
    # Parse markdown table
    df = pd.read_table(markdown_file, sep='|', skipinitialspace=True)

    for _, row in df.iterrows():
        metric = HealthMetric(
            user_id=user_id,
            recorded_date=datetime.strptime(row['Date'], '%Y-%m-%d').date(),
            weight_lbs=row['Weight (lbs)'],
            body_fat_percentage=row['Body Fat %'],
            notes=row['Notes']
        )
        db.session.add(metric)

    db.session.commit()
```

### Workout Migration
Similar approach for workout data from `progress-check-in-log.md`.

## Row-Level Security (Optional)

For enhanced security, enable PostgreSQL Row-Level Security:

```sql
-- Enable RLS on health_metrics
ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY health_metrics_user_isolation ON health_metrics
    FOR ALL
    TO fitness_user
    USING (user_id = current_setting('app.current_user_id')::integer);

-- Set user context in application
SET app.current_user_id = '123';
```

## API Serialization

All models include `to_dict()` methods for JSON API responses:

```python
# Example: Get user health metrics
user = User.query.get(1)
metrics = HealthMetric.query.filter_by(user_id=user.id).all()

# Serialize to JSON
response = {
    'user': user.to_dict(),
    'metrics': [m.to_dict() for m in metrics]
}
```

## Performance Considerations

1. **Indexes**: All foreign keys and frequently queried fields are indexed
2. **Pagination**: Use limit/offset for large result sets
3. **Query Optimization**: Use `joinedload()` for eager loading relationships
4. **Connection Pooling**: Configure SQLAlchemy pool size appropriately
5. **Caching**: Consider Redis for session storage and frequently accessed data

## Security Best Practices

1. **User Isolation**: Always filter by user_id in queries
2. **Password Security**: Passwords hashed with bcrypt (12 rounds)
3. **Session Management**: Sessions expire after 24 hours (30 days with remember me)
4. **Account Locking**: Accounts locked after 5 failed login attempts
5. **SQL Injection**: Use SQLAlchemy ORM to prevent injection attacks
6. **Audit Logging**: Track important actions in audit_log table

## Testing

```python
# Example: Unit test for HealthMetric model
def test_health_metric_calculated_properties():
    metric = HealthMetric(
        weight_lbs=200,
        body_fat_percentage=20
    )
    assert metric.lean_body_mass_lbs == 160
    assert metric.fat_mass_lbs == 40
```

## Troubleshooting

### Common Issues

1. **Migration conflicts**: `alembic downgrade -1` then re-apply
2. **Connection errors**: Check DATABASE_URL and PostgreSQL service
3. **Permission errors**: Grant proper privileges to fitness_user
4. **Import errors**: Ensure all models imported in `models/__init__.py`

## Next Steps

1. Create Flask routes for CRUD operations on each model
2. Implement authentication and session management
3. Create data migration scripts for existing markdown data
4. Build API endpoints with proper serialization
5. Implement row-level security policies
6. Add comprehensive test coverage
7. Set up database backups and monitoring

## Contact

For questions about the database architecture, contact the development team.
