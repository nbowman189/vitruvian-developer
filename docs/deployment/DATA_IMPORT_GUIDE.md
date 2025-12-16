# Data Import Guide for Health & Fitness Logs

## Status: Health Data Import Complete ✅

You've successfully imported **118 health metrics** from `check-in-log.md`. These are now visible in the Health Metrics Log virtual page.

---

## Remaining Log Files - Import Strategy

### Challenge: Data Model Mismatch

The remaining log files (`meal-log.md`, `exercise-log.md`, `Coaching_sessions.md`) contain **detailed, granular data**, but the database models are designed for **daily aggregates**:

| Markdown File | Contains | Database Model Expects |
|---------------|----------|----------------------|
| **meal-log.md** | Individual meals per day (Breakfast, Lunch, Dinner, Snacks) | Daily totals: protein_g, carbs_g, fat_g, calories |
| **exercise-log.md** | Individual exercises per date (Ring Push-ups, Tai Chi, etc.) | Workout sessions: workout_type, duration_minutes, summary |
| **Coaching_sessions.md** | Free-form markdown with headers and narrative | Structured sessions: session_date, session_type, notes |

---

## Recommended Approach

### Option 1: Start Fresh (Recommended)

**Use the database going forward** for new entries:

- **Virtual pages** are already set up to display database data
- Input new meals, workouts, and coaching sessions directly into the database
- Keep the markdown files as historical reference

**Benefits:**
- No data loss (markdown files remain intact)
- Clean slate with proper structure
- Immediate visibility in web interface

### Option 2: Manual Historical Data Entry

If specific historical data is valuable, manually enter key dates:

**Example: Meal Log**
```python
# For Dec 7, 2025 (example aggregation):
# Total from all meals: ~1000 calories
# Estimated macros based on meal descriptions

docker-compose exec web python -c "
from website import create_app, db
from website.models.nutrition import MealLog
from website.models.user import User
from datetime import date

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='admin').first()

    meal = MealLog(
        user_id=user.id,
        meal_date=date(2025, 12, 7),
        calories=1000,
        protein_g=60,  # Estimate
        carbs_g=80,    # Estimate
        fat_g=40,      # Estimate
        notes='Full day aggregated from meal-log.md'
    )
    db.session.add(meal)
    db.session.commit()
    print('✅ Meal log entry added')
"
```

**Example: Workout Session**
```python
docker-compose exec web python -c "
from website import create_app, db
from website.models.workout import WorkoutSession
from website.models.user import User
from datetime import date

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='admin').first()

    workout = WorkoutSession(
        user_id=user.id,
        session_date=date(2025, 12, 8),
        workout_type='Full Body Rings + Cardio',
        duration_minutes=180,  # 2 hours walking + 1 hour rings
        notes='Ring Push-ups, Support Holds, Tai Chi, 2hr walk'
    )
    db.session.add(workout)
    db.session.commit()
    print('✅ Workout session added')
"
```

**Example: Coaching Session**
```python
docker-compose exec web python -c "
from website import create_app, db
from website.models.coaching import CoachingSession
from website.models.user import User
from datetime import date

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='admin').first()

    session = CoachingSession(
        user_id=user.id,
        session_date=date(2025, 12, 10),
        session_type='Mid-Week Check-in',
        notes='Caloric analysis and strategic adjustments',
        trainer_notes='3-day deficit: ~4,965 calories. Stay the course.'
    )
    db.session.add(session)
    db.session.commit()
    print('✅ Coaching session added')
"
```

### Option 3: Complex Aggregation Scripts (Future Enhancement)

If you want to automatically aggregate and import all historical data, we can create advanced scripts that:

1. **Parse `meal-log.md`**: Sum calories/macros by date, calculate estimates for missing data
2. **Parse `exercise-log.md`**: Group exercises by date, calculate total duration
3. **Parse `Coaching_sessions.md`**: Extract headers and body content into structured format

**Time estimate:** 2-3 hours to develop and test
**Benefit:** Complete historical data in database
**Trade-off:** Complexity vs. value (most recent data is more actionable)

---

## Current Database Models

### MealLog Fields
- `meal_date` - Date of meals
- `calories` - Total daily calories
- `protein_g` - Total grams of protein
- `carbs_g` - Total grams of carbohydrates
- `fat_g` - Total grams of fat
- `notes` - Optional notes

### WorkoutSession Fields
- `session_date` - Date of workout
- `workout_type` - Type/name of workout
- `duration_minutes` - Total workout duration
- `notes` - Exercise details and notes
- `calories_burned` - Optional calorie burn estimate

### CoachingSession Fields
- `session_date` - Date of coaching session
- `session_type` - Type of session (check-in, strategy, etc.)
- `notes` - Session notes and observations
- `trainer_notes` - Coach's recommendations
- `goals` - Session goals (optional)

---

## Verification Commands

**Check imported data:**

```bash
# View recent meal logs
docker-compose exec web python -c "
from website import create_app, db
from website.models.nutrition import MealLog
app = create_app()
with app.app_context():
    meals = MealLog.query.order_by(MealLog.meal_date.desc()).limit(10).all()
    for m in meals:
        print(f'{m.meal_date}: {m.calories} cal, P:{m.protein_g}g C:{m.carbs_g}g F:{m.fat_g}g')
"

# View recent workout sessions
docker-compose exec web python -c "
from website import create_app, db
from website.models.workout import WorkoutSession
app = create_app()
with app.app_context():
    workouts = WorkoutSession.query.order_by(WorkoutSession.session_date.desc()).limit(10).all()
    for w in workouts:
        print(f'{w.session_date}: {w.workout_type} - {w.duration_minutes} min')
"

# View coaching sessions
docker-compose exec web python -c "
from website import create_app, db
from website.models.coaching import CoachingSession
app = create_app()
with app.app_context():
    sessions = CoachingSession.query.order_by(CoachingSession.session_date.desc()).all()
    for s in sessions:
        print(f'{s.session_date}: {s.session_type}')
"
```

---

## Recommendation

**Start with Option 1** (use database going forward) and **Option 2** (manually enter 5-10 key historical dates if needed). This gives you:

1. ✅ Clean, structured data in the database
2. ✅ Immediate visibility in web interface
3. ✅ Historical markdown files preserved for reference
4. ✅ No time lost on complex aggregation scripts

The markdown files will remain in your project as historical records. The virtual database pages will show new data as you add it.

---

## Next Steps

1. Deploy the latest code changes to your remote server
2. View the Health Metrics Log page (already populated with 118 entries!)
3. Start adding new meal logs, workout sessions, and coaching notes via Python commands or future web forms
4. Keep the markdown files for historical reference

---

*Generated: December 16, 2024*
