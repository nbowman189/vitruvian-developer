# Database Schema Diagram

## Entity Relationship Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MULTI-USER FITNESS TRACKER                         │
│                          PostgreSQL Database Schema                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│       USERS          │ ◄─────────────────────────┐
├──────────────────────┤                           │
│ PK  id               │                           │
│ UK  username         │                           │
│ UK  email            │                           │
│     password_hash    │                           │
│     role             │                           │
│     is_active        │                           │
│     full_name        │                           │
│     profile_photo_url│                           │
│     bio              │                           │
│     created_at       │                           │
│     updated_at       │                           │
│     last_login       │                           │
│     failed_login...  │                           │
│     locked_until     │                           │
└──────────────────────┘                           │
         │                                          │
         │                                          │
         ├──────────────────────────────────────────┼──────────────────┐
         │                                          │                  │
         │                                          │                  │
         ▼                                          │                  │
┌──────────────────────┐                           │                  │
│   HEALTH_METRICS     │                           │                  │
├──────────────────────┤                           │                  │
│ PK  id               │                           │                  │
│ FK  user_id          │───────────────────────────┘                  │
│ UK  (user_id, date)  │                                              │
│     recorded_date    │                                              │
│     weight_lbs       │                                              │
│     body_fat_%       │                                              │
│     muscle_mass_lbs  │                                              │
│     bmi              │                                              │
│     waist_inches     │                                              │
│     chest_inches     │                                              │
│     [arms, legs...]  │                                              │
│     resting_hr       │                                              │
│     blood_pressure   │                                              │
│     energy_level     │                                              │
│     mood             │                                              │
│     sleep_quality    │                                              │
│     stress_level     │                                              │
│     notes            │                                              │
└──────────────────────┘                                              │
                                                                       │
         ┌─────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────┐            ┌──────────────────────┐
│  WORKOUT_SESSIONS    │            │  EXERCISE_DEFINITIONS│
├──────────────────────┤            ├──────────────────────┤
│ PK  id               │            │ PK  id               │
│ FK  user_id          │            │ UK  name             │
│     session_date     │            │     category         │
│     session_type     │            │     muscle_groups[]  │
│     duration_minutes │            │     equipment[]      │
│     program_phase    │            │     difficulty_level │
│     week_number      │            │     description      │
│     day_number       │            │     instructions     │
│     intensity        │            │     tips             │
│     fatigue          │            │     video_url        │
│     soreness         │            │     image_url        │
│     notes            │            │     is_active        │
│     coach_notes      │            │     created_by       │
└──────────────────────┘            └──────────────────────┘
         │                                    ▲
         │                                    │
         │                                    │
         ▼                                    │
┌──────────────────────┐                     │
│   EXERCISE_LOGS      │─────────────────────┘
├──────────────────────┤
│ PK  id               │
│ FK  workout_session  │
│ FK  exercise_def_id  │
│     exercise_name    │
│     sets             │
│     reps             │
│     weight_lbs       │
│     rest_seconds     │
│     duration_seconds │
│     distance_miles   │
│     form_quality     │
│     rpe              │
│     order_index      │
│     notes            │
└──────────────────────┘


┌──────────────────────┐            ┌──────────────────────┐
│  COACHING_SESSIONS   │            │     USER_GOALS       │
├──────────────────────┤            ├──────────────────────┤
│ PK  id               │            │ PK  id               │
│ FK  user_id          │◄───────┐   │ FK  user_id          │◄──────┐
│ FK  coach_id         │◄───┐   │   │     goal_type        │       │
│     session_date     │    │   │   │     title            │       │
│     duration_minutes │    │   │   │     description      │       │
│     topics[]         │    │   │   │     target_value     │       │
│     discussion_notes │    │   │   │     target_unit      │       │
│     coach_feedback   │    │   │   │     current_value    │       │
│     action_items[]   │    │   │   │     progress_%       │       │
│     next_session_date│    │   │   │     start_date       │       │
│     completed        │    │   │   │     target_date      │       │
│     completion_notes │    │   │   │     completed_date   │       │
│     user_rating      │    │   │   │     status           │       │
└──────────────────────┘    │   │   │     notes            │       │
      (coach is User)       │   │   │     milestones[]     │       │
                            │   │   └──────────────────────┘       │
                            │   │                                  │
                            │   │                                  │
                            │   └──────────────────────────────────┘
                            │
                            │
┌──────────────────────┐    │
│   PROGRESS_PHOTOS    │    │
├──────────────────────┤    │
│ PK  id               │    │
│ FK  user_id          │◄───┤
│     photo_date       │    │
│     photo_url        │    │
│     photo_type       │    │
│     weight_lbs       │    │
│     body_fat_%       │    │
│     notes            │    │
│     is_public        │    │
└──────────────────────┘    │
                            │
                            │
┌──────────────────────┐    │
│     MEAL_LOGS        │    │
├──────────────────────┤    │
│ PK  id               │    │
│ FK  user_id          │◄───┤
│     meal_date        │    │
│     meal_time        │    │
│     meal_type        │    │
│     calories         │    │
│     protein_g        │    │
│     carbs_g          │    │
│     fat_g            │    │
│     fiber_g          │    │
│     sugar_g          │    │
│     sodium_mg        │    │
│     water_oz         │    │
│     description      │    │
│     foods            │    │
│     recipe_name      │    │
│     adherence_to_plan│    │
│     planned_meal     │    │
│     satisfaction     │    │
│     hunger_before    │    │
│     hunger_after     │    │
│     notes            │    │
└──────────────────────┘    │
                            │
                            │
┌──────────────────────┐    │
│   USER_SESSIONS      │    │
├──────────────────────┤    │
│ PK  session_id (UUID)│    │
│ FK  user_id          │◄───┘
│     created_at       │
│     expires_at       │
│     last_activity    │
│     ip_address       │
│     user_agent       │
│     is_active        │
│     revoked_at       │
│     revocation_reason│
│     device_type      │
│     browser          │
│     os               │
│     remember_me      │
└──────────────────────┘


┌──────────────────────┐
│     APP_CONFIG       │  (Application Configuration)
├──────────────────────┤
│ PK  key              │
│     value            │
│     description      │
│     created_at       │
│     updated_at       │
└──────────────────────┘


┌──────────────────────┐
│     AUDIT_LOG        │  (Audit Trail)
├──────────────────────┤
│ PK  id               │
│     user_id          │
│     action           │
│     table_name       │
│     record_id        │
│     old_values (JSON)│
│     new_values (JSON)│
│     ip_address       │
│     user_agent       │
│     created_at       │
└──────────────────────┘
```

## Table Relationships Summary

### User Relationships (1:Many)
- **User → Health Metrics**: One user has many health check-ins
- **User → Workout Sessions**: One user has many workout sessions
- **User → Coaching Sessions** (as client): One user has many coaching sessions
- **User → Coaching Sessions** (as coach): One coach has many coaching sessions
- **User → Goals**: One user has many goals
- **User → Progress Photos**: One user has many progress photos
- **User → Meal Logs**: One user has many meal logs
- **User → Sessions**: One user has many active sessions

### Workout Relationships
- **Workout Session → Exercise Logs** (1:Many): One workout contains many exercises
- **Exercise Definition → Exercise Logs** (1:Many): One definition referenced by many logs

### Cascade Behavior
All foreign keys to `users` use `ON DELETE CASCADE`:
- Deleting a user removes all their data automatically
- Exercise definitions use `ON DELETE SET NULL` (preserve logs even if definition deleted)

## Key Features

### Data Isolation
- **Strict user_id filtering**: Users can ONLY see their own data
- **Optional Row-Level Security**: PostgreSQL RLS for database-level enforcement
- **No shared data tables** except ExerciseDefinitions (reference data)

### Audit & Security
- **Password Security**: Bcrypt hashing with salt
- **Session Management**: UUID-based sessions with expiration
- **Account Locking**: Auto-lock after failed login attempts
- **Audit Log**: Track all important changes

### Performance Optimization
- **Indexes**: All foreign keys and date fields indexed
- **Composite Indexes**: (user_id, date) for common queries
- **Check Constraints**: Database-level validation
- **Unique Constraints**: Prevent duplicate entries

### Data Validation
- **1-10 Rating Scales**: energy, mood, intensity, fatigue, rpe, satisfaction, etc.
- **Range Checks**: Valid ranges for vital signs, body composition
- **Enum Types**: Controlled vocabularies for types and statuses
- **Required Fields**: NOT NULL constraints on critical fields

## Migration Path

### From Markdown Files

1. **Health_and_Fitness/data/check-in-log.md** → `health_metrics` table
2. **Health_and_Fitness/data/progress-check-in-log.md** → `workout_sessions` + `exercise_logs`
3. **Health_and_Fitness/data/Coaching_sessions.md** → `coaching_sessions`

### Shared Content (Remains in Markdown)
- **Full-Meal-Plan.md**: Stays in docs/ (shared meal plan templates)
- **fitness-roadmap.md**: Stays in docs/ (shared program phases)
- **AI_Development/docs/curriculum.md**: Stays in docs/ (shared curriculum)

## Database Statistics

### Total Tables: 11
- **User Management**: 1 table (users)
- **Health Tracking**: 1 table (health_metrics)
- **Workout Tracking**: 3 tables (workout_sessions, exercise_logs, exercise_definitions)
- **Coaching & Goals**: 3 tables (coaching_sessions, user_goals, progress_photos)
- **Nutrition**: 1 table (meal_logs)
- **Security**: 1 table (user_sessions)
- **System**: 2 tables (app_config, audit_log)

### Estimated Storage (per user, 1 year)
- **Health Metrics**: ~50 entries × 0.5 KB = 25 KB
- **Workout Sessions**: ~156 sessions × 1 KB = 156 KB
- **Exercise Logs**: ~2000 exercises × 0.5 KB = 1000 KB
- **Meal Logs**: ~1095 meals × 1 KB = 1095 KB
- **Progress Photos**: ~24 photos × 0.5 KB (metadata only) = 12 KB
- **Total**: ~2.3 MB per user per year (excluding photo files)

### Scalability
- **1000 users**: ~2.3 GB database size
- **10000 users**: ~23 GB database size
- **Well-indexed queries**: Sub-100ms response time even at 10k users
