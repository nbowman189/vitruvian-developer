# AI Coach Batch Records - Manual Test Plan

## Overview

This document outlines the manual testing procedure for the AI Coach batch records feature, which allows the AI to create multiple database records in a single function call.

## Feature Description

**Backend**: `_save_batch_records()` in `/website/api/ai_coach.py`
**Frontend**: Batch UI handling in `/website/static/js/ai-coach.js`
**Function Schema**: `create_batch_records_schema()` in `/website/utils/ai_coach_tools.py`

The feature supports:
- Creating multiple records in one operation
- Mixed record types (workout + meal + health metric)
- Partial success (some records can fail while others succeed)
- Batch preview card UI with tabbed modal for editing
- Individual record validation

## Prerequisites

1. Docker containers running (`docker-compose up -d`)
2. Web app accessible at `http://localhost:8001`
3. Logged in as admin user (username: `admin`, password: `admin123`)
4. AI Coach page accessible at `http://localhost:8001/ai-coach.html`

## Test Cases

### Test 1: Single Record in Batch (Edge Case)
**Expected Behavior**: AI should handle single record gracefully

**Test Message**:
```
I weighed myself today at 176 lbs
```

**Expected AI Behavior**:
- Should call `create_health_metric` (single record function) OR
- Should call `create_batch_records` with 1 record

**Verification**:
- [ ] Record preview card appears
- [ ] Can click "Review & Save"
- [ ] Modal shows weight data
- [ ] Saves successfully
- [ ] Health metric appears in database/dashboard

---

### Test 2: Multiple Different Record Types
**Expected Behavior**: AI creates workout + meal + health metric in one batch

**Test Message**:
```
Today I weighed 176.5 lbs, did a 60-minute strength workout (bench press 3x8 at 185lbs, squats 4x10 at 225lbs), and ate breakfast: eggs, oatmeal, and a protein shake (650 calories, 45g protein).
```

**Expected AI Behavior**:
- Should call `create_batch_records` with 3 records:
  1. health_metric (weight: 176.5)
  2. workout (STRENGTH, 60 min, 2 exercises)
  3. meal_log (BREAKFAST, 650 cal, 45g protein)

**Verification**:
- [ ] Batch preview card shows "Multiple Records (3)"
- [ ] Preview lists all 3 records with summaries
- [ ] Click "Review & Save" opens tabbed modal
- [ ] Tabs show: "1. Health Metric", "2. Workout Session", "3. Meal Log"
- [ ] Each tab has correct pre-filled data
- [ ] Can edit any record
- [ ] Save button creates all 3 records
- [ ] Success message shows "3 records saved successfully!"
- [ ] All records appear in respective pages

---

### Test 3: Multiple Same Record Type
**Expected Behavior**: AI creates multiple meals for the same day

**Test Message**:
```
For today's meals: Lunch was chicken breast, rice, and vegetables (800 calories, 50g protein). Dinner was salmon, sweet potato, and broccoli (750 calories, 55g protein). Snack was a protein bar and almonds (200 calories, 20g protein).
```

**Expected AI Behavior**:
- Should call `create_batch_records` with 3 meal_log records:
  1. LUNCH (800 cal, 50g protein)
  2. DINNER (750 cal, 55g protein)
  3. SNACK (200 cal, 20g protein)

**Verification**:
- [ ] Batch preview card shows "Multiple Records (3)"
- [ ] All 3 records show as "Meal Log"
- [ ] Modal has 3 tabs, all for meals
- [ ] Each meal has correct type, calories, protein
- [ ] Saves all 3 meals successfully
- [ ] Meals appear in nutrition page

---

### Test 4: AI Suggests Invalid Data (Partial Success)
**Expected Behavior**: Some records succeed, some fail with clear error messages

**Test Message**:
```
Today I weighed 177 lbs, did a workout, and had lunch with 500 calories
```
*Note: The workout is vague (missing type), lunch is vague (missing meal type)*

**Expected AI Behavior**:
- May call `create_batch_records` with incomplete data, OR
- May ask for clarification first

**If Batch Called with Missing Data**:
- Backend should return partial success
- Frontend should show which records failed and why

**Verification**:
- [ ] Health metric saves successfully
- [ ] Workout or meal might fail validation (missing required fields)
- [ ] Error messages are clear and specific
- [ ] User can edit and retry failed records

---

### Test 5: Complex Multi-Day Scenario
**Expected Behavior**: AI should ask for clarification or use today's date

**Test Message**:
```
Yesterday I did chest day and ate 2200 calories. Today I weighed 176 lbs and did cardio for 30 minutes.
```

**Expected AI Behavior**:
- Should create records with appropriate dates, OR
- Should ask for clarification about "yesterday" vs "today"

**Verification**:
- [ ] Records have correct dates
- [ ] If batch used, shows all records clearly
- [ ] Dates are editable in modal
- [ ] Saves with correct timestamps

---

### Test 6: User Edits Batch Records Before Saving
**Expected Behavior**: User can modify any record in the batch before saving

**Test Message**:
```
I did a workout today (45 min cardio) and had breakfast (400 calories, 30g protein)
```

**Steps**:
1. AI suggests batch with workout + meal
2. Click "Review & Save"
3. Edit workout: change duration to 60 minutes
4. Switch to meal tab
5. Edit meal: change calories to 450
6. Click "Save All Records"

**Verification**:
- [ ] Edits persist when switching tabs
- [ ] Save uses edited values (60 min, 450 cal)
- [ ] Database reflects edited values, not original AI suggestions

---

### Test 7: User Cancels Batch Save
**Expected Behavior**: No records created, conversation continues

**Test Message**:
```
I weighed 175 lbs and did a workout today
```

**Steps**:
1. AI suggests batch with health metric + workout
2. Click "Review & Save"
3. Click "Cancel" or close modal without saving
4. Type new message

**Verification**:
- [ ] Modal closes
- [ ] No records created in database
- [ ] Can send new message normally
- [ ] Record preview card remains visible in chat

---

## UI/UX Verification

### Batch Preview Card Styling
- [ ] Card has distinct "batch-records" styling (gradient background, stack icon)
- [ ] Shows record count: "Multiple Records (N)"
- [ ] Lists each record with number, type, and key fields
- [ ] Has "Review & Save All" button
- [ ] Visually distinct from single-record cards

### Tabbed Modal Interface
- [ ] Modal title shows "Review Records"
- [ ] Tabs display as numbered: "1. Record Type", "2. Record Type", etc.
- [ ] Active tab is highlighted
- [ ] Can click tabs to switch between records
- [ ] Each tab shows appropriate form for record type
- [ ] "Save All Records" button is clear
- [ ] Cancel button works

### Success/Error States
- [ ] Success message shows record count: "N records saved successfully!"
- [ ] Partial success shows which records failed
- [ ] Error messages are specific (e.g., "meal_type is required")
- [ ] Failed records can be retried

---

## Backend Verification

### Database Checks
After each successful test, verify in the database or dashboard:

```bash
# Check health metrics
docker-compose exec -T web python -c "
from website import create_app
from website.models.health import HealthMetric
app = create_app()
with app.app_context():
    count = HealthMetric.query.count()
    print(f'Health Metrics: {count}')
"

# Check workouts
docker-compose exec -T web python -c "
from website import create_app
from website.models.workout import WorkoutSession
app = create_app()
with app.app_context():
    count = WorkoutSession.query.count()
    print(f'Workouts: {count}')
"

# Check meals
docker-compose exec -T web python -c "
from website import create_app
from website.models.nutrition import MealLog
app = create_app()
with app.app_context():
    count = MealLog.query.count()
    print(f'Meals: {count}')
"
```

### Conversation Log Verification
- [ ] `records_created` counter increments correctly
- [ ] Function call metadata saved in conversation
- [ ] Messages appear in conversation history

---

## Expected Issues & Known Limitations

1. **Gemini Model Selection**: The AI might not always use batch function even when appropriate
   - Solution: Explicitly mention multiple items in one sentence

2. **Date Handling**: AI might struggle with relative dates ("yesterday", "last Monday")
   - Workaround: Use specific dates or "today"

3. **Partial Success**: Frontend shows all records initially, even if some fail
   - This is intentional - user can see what succeeded/failed

4. **Empty Batch**: Should be rejected by backend validation
   - Expected error: "records array is required and cannot be empty"

---

## Test Results

**Date**: ___________
**Tester**: ___________
**Environment**: Local Docker / Remote Server (circle one)

### Summary

| Test Case | Status | Notes |
|-----------|--------|-------|
| 1. Single record batch | ⬜ Pass / ⬜ Fail | |
| 2. Multiple different types | ⬜ Pass / ⬜ Fail | |
| 3. Multiple same type | ⬜ Pass / ⬜ Fail | |
| 4. Partial success | ⬜ Pass / ⬜ Fail | |
| 5. Multi-day scenario | ⬜ Pass / ⬜ Fail | |
| 6. Edit before save | ⬜ Pass / ⬜ Fail | |
| 7. Cancel save | ⬜ Pass / ⬜ Fail | |

### Issues Found

1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

### Overall Assessment

⬜ **PASS** - Feature is production-ready
⬜ **PASS WITH MINOR ISSUES** - Works but has non-critical bugs
⬜ **FAIL** - Critical issues found, needs fixes

---

## Next Steps After Testing

1. Fix any critical bugs found
2. Update documentation if behavior differs from expected
3. Consider adding automated tests for critical paths
4. Deploy to remote server if tests pass
5. Monitor Gemini API usage for batch vs. individual function calls
