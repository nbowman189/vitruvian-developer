# API Endpoints Specification

Complete API endpoint reference for the Vitruvian Tracker backend implementation.

## Response Format

All endpoints return JSON in this format:

```json
{
    "success": true,
    "data": { ... },
    "message": "Optional message"
}
```

Error responses:
```json
{
    "success": false,
    "error": "Error message",
    "details": { ... }
}
```

---

## Dashboard Endpoints

### Get Latest Weight Metric
```
GET /api/health/metrics/latest
```

**Response:**
```json
{
    "success": true,
    "data": {
        "weight": 175.5,
        "change": "-2.5",
        "date": "2024-01-15"
    }
}
```

### Get Recent Workout
```
GET /api/workout/recent
```

**Response:**
```json
{
    "success": true,
    "data": {
        "name": "Upper Body Strength",
        "duration": 60,
        "date": "2024-01-15"
    }
}
```

### Get Next Coaching Session
```
GET /api/coaching/next-session
```

**Response:**
```json
{
    "success": true,
    "data": {
        "date": "2024-01-20",
        "countdown": "5 days",
        "active_goals": 3
    }
}
```

### Get Nutrition Streak
```
GET /api/nutrition/streak
```

**Response:**
```json
{
    "success": true,
    "data": {
        "streak": 7,
        "calories_today": 1850,
        "protein_today": 145
    }
}
```

### Get Weight Trend
```
GET /api/health/metrics/trend?days=7
```

**Response:**
```json
{
    "success": true,
    "data": {
        "dates": ["2024-01-09", "2024-01-10", "..."],
        "weights": [177.0, 176.5, 176.0, "..."]
    }
}
```

### Get Workout Volume Trend
```
GET /api/workout/volume-trend?days=7
```

**Response:**
```json
{
    "success": true,
    "data": {
        "dates": ["2024-01-09", "2024-01-10", "..."],
        "volumes": [12500, 0, 13200, "..."]
    }
}
```

### Get Nutrition Adherence Trend
```
GET /api/nutrition/adherence-trend?days=7
```

**Response:**
```json
{
    "success": true,
    "data": {
        "dates": ["2024-01-09", "..."],
        "calories": [1950, 1850, "..."],
        "protein": [150, 145, "..."]
    }
}
```

### Get Recent Activity
```
GET /api/activity/recent?limit=5
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "type": "health",
            "title": "Weight Logged",
            "description": "175.5 lbs",
            "date": "2024-01-15"
        },
        "..."
    ]
}
```

---

## Health Metrics Endpoints

### List Metrics
```
GET /api/health/metrics?page=1&date_range=30&bodyfat_only=false
```

**Parameters:**
- `page` (int): Page number
- `date_range` (int): Days to include (7, 30, 90, or 0 for all)
- `bodyfat_only` (bool): Only show entries with body fat

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "date": "2024-01-15",
            "weight": 175.5,
            "bodyfat": 22.5,
            "lean_mass": 136.0,
            "notes": "Feeling strong"
        }
    ],
    "pagination": {
        "page": 1,
        "pages": 10,
        "per_page": 20,
        "total": 195,
        "has_prev": false,
        "has_next": true,
        "prev_num": null,
        "next_num": 2
    }
}
```

### Create Metric
```
POST /api/health/metrics
```

**Request Body:**
```json
{
    "date": "2024-01-15",
    "weight": 175.5,
    "bodyfat": 22.5,
    "notes": "Optional notes"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "date": "2024-01-15",
        "weight": 175.5,
        "bodyfat": 22.5,
        "lean_mass": 136.0,
        "notes": "Optional notes"
    },
    "message": "Metric created successfully"
}
```

### Update Metric
```
PUT /api/health/metrics/<id>
```

**Request Body:** Same as Create

**Response:** Same as Create

### Delete Metric
```
DELETE /api/health/metrics/<id>
```

**Response:**
```json
{
    "success": true,
    "message": "Metric deleted successfully"
}
```

### Get Metrics Summary
```
GET /api/health/metrics/summary?date_range=30
```

**Response:**
```json
{
    "success": true,
    "data": {
        "current_weight": 175.5,
        "weight_change": -2.5,
        "current_bodyfat": 22.5,
        "bodyfat_change": -0.5,
        "lean_mass": 136.0,
        "lean_mass_change": -1.0,
        "total_entries": 50
    }
}
```

---

## Workout Endpoints

### List Workouts
```
GET /api/workout/workouts?page=1&date_range=30&type=all
```

**Parameters:**
- `page` (int): Page number
- `date_range` (int): Days to include
- `type` (str): strength, cardio, flexibility, mixed, or all

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "date": "2024-01-15",
            "duration": 60,
            "workout_type": "strength",
            "total_volume": 12500,
            "total_sets": 15,
            "total_reps": 120,
            "exercise_count": 5
        }
    ],
    "pagination": { "..." },
    "summary": {
        "total_workouts": 25,
        "total_volume": 312500,
        "total_time": 1500,
        "avg_duration": 60
    }
}
```

### Get Workout Details
```
GET /api/workout/workout/<id>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "date": "2024-01-15",
        "duration": 60,
        "workout_type": "strength",
        "notes": "Great session",
        "exercise_logs": [
            {
                "exercise_name": "Barbell Bench Press",
                "sets": [
                    { "reps": 10, "weight": 135 },
                    { "reps": 8, "weight": 145 },
                    { "reps": 6, "weight": 155 }
                ],
                "total_volume": 4100
            }
        ]
    }
}
```

### Create Workout
```
POST /api/workout/workout
```

**Request Body:**
```json
{
    "date": "2024-01-15",
    "duration": 60,
    "workout_type": "strength",
    "notes": "Great session",
    "exercises": [
        {
            "name": "Barbell Bench Press",
            "sets": [
                { "reps": 10, "weight": 135 },
                { "reps": 8, "weight": 145 }
            ]
        }
    ]
}
```

### Update Workout
```
PUT /api/workout/workout/<id>
```

**Request Body:** Same as Create

### Delete Workout
```
DELETE /api/workout/workout/<id>
```

### Search Exercises
```
GET /api/workout/exercises?search=bench
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "Barbell Bench Press",
            "category": "chest",
            "equipment": "barbell",
            "muscle_groups": ["Chest", "Triceps", "Shoulders"]
        }
    ]
}
```

### Add Exercise to Library
```
POST /api/workout/exercise
```

**Request Body:**
```json
{
    "name": "Barbell Bench Press",
    "category": "chest",
    "equipment": "barbell",
    "muscle_groups": "Chest, Triceps, Shoulders",
    "description": "Classic chest exercise"
}
```

### Get Workout Comparison
```
GET /api/workout/comparison/<workout_id>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "current_workout": { "..." },
        "previous_workout": { "..." },
        "comparisons": [
            {
                "exercise": "Barbell Bench Press",
                "current_volume": 4100,
                "previous_volume": 3900,
                "change": "+5.1%"
            }
        ]
    }
}
```

---

## Coaching Endpoints

### List Sessions
```
GET /api/coaching/sessions?page=1&date_range=30
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "date": "2024-01-15",
            "coach": "John Doe",
            "highlights": "Discussed nutrition plan",
            "action_items_count": 3,
            "completed_actions": 1
        }
    ],
    "pagination": { "..." }
}
```

### Get Session Details
```
GET /api/coaching/session/<id>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "date": "2024-01-15",
        "coach": "John Doe",
        "notes": "Full session notes...",
        "highlights": "Key takeaways",
        "action_items": [
            {
                "id": 1,
                "description": "Increase protein to 150g/day",
                "due_date": "2024-01-20",
                "completed": false
            }
        ],
        "related_goals": [1, 2]
    }
}
```

### Create Session
```
POST /api/coaching/session
```

**Request Body:**
```json
{
    "date": "2024-01-15",
    "coach": "John Doe",
    "notes": "Session notes...",
    "highlights": "Key takeaways"
}
```

### Update Session
```
PUT /api/coaching/session/<id>
```

### Delete Session
```
DELETE /api/coaching/session/<id>
```

### List Goals
```
GET /api/coaching/goals?status=active
```

**Parameters:**
- `status` (str): active, completed, archived

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "title": "Lose 20 lbs",
            "description": "Target weight: 155 lbs",
            "category": "fitness",
            "status": "active",
            "target_date": "2024-06-01",
            "measurable": true,
            "current_value": 175,
            "target_value": 155,
            "unit": "lbs",
            "progress_percentage": 25
        }
    ]
}
```

### Create Goal
```
POST /api/coaching/goal
```

**Request Body:**
```json
{
    "title": "Lose 20 lbs",
    "description": "Target weight: 155 lbs",
    "category": "fitness",
    "target_date": "2024-06-01",
    "measurable": true,
    "current_value": 175,
    "target_value": 155,
    "unit": "lbs"
}
```

### Update Goal
```
PUT /api/coaching/goal/<id>
```

### Delete Goal
```
DELETE /api/coaching/goal/<id>
```

### List Progress Photos
```
GET /api/coaching/progress-photos?date_range=90
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "date": "2024-01-15",
            "photo_url": "/static/uploads/progress/photo1.jpg",
            "notes": "Front view"
        }
    ]
}
```

### Upload Progress Photo
```
POST /api/coaching/progress-photo
Content-Type: multipart/form-data
```

**Form Data:**
- `date` (string): Date of photo
- `photo` (file): Photo file
- `notes` (string): Optional notes

### Delete Progress Photo
```
DELETE /api/coaching/progress-photo/<id>
```

---

## Nutrition Endpoints

### List Meals for Date
```
GET /api/nutrition/meals?date=2024-01-15
```

**Response:**
```json
{
    "success": true,
    "data": {
        "meals": [
            {
                "id": 1,
                "meal_type": "breakfast",
                "time": "08:00",
                "description": "Oatmeal with berries",
                "calories": 350,
                "protein": 15,
                "carbs": 60,
                "fat": 8
            }
        ],
        "daily_totals": {
            "calories": 1850,
            "protein": 145,
            "carbs": 200,
            "fat": 62
        }
    }
}
```

### Create Meal
```
POST /api/nutrition/meal
```

**Request Body:**
```json
{
    "date": "2024-01-15",
    "meal_type": "breakfast",
    "time": "08:00",
    "description": "Oatmeal with berries",
    "calories": 350,
    "protein": 15,
    "carbs": 60,
    "fat": 8
}
```

### Update Meal
```
PUT /api/nutrition/meal/<id>
```

### Delete Meal
```
DELETE /api/nutrition/meal/<id>
```

### Get Nutrition Summary
```
GET /api/nutrition/summary?days=7
```

**Response:**
```json
{
    "success": true,
    "data": {
        "avg_calories": 1875,
        "avg_protein": 147,
        "avg_carbs": 198,
        "avg_fat": 64,
        "adherence_rate": 85,
        "logging_streak": 7,
        "calorie_trend": {
            "dates": ["2024-01-09", "..."],
            "values": [1900, 1850, "..."]
        },
        "macro_distribution": {
            "protein_pct": 31,
            "carbs_pct": 42,
            "fat_pct": 27
        },
        "adherence_calendar": [
            {
                "date": "2024-01-09",
                "adherence": "excellent"
            }
        ]
    }
}
```

### Get Nutrition Targets
```
GET /api/nutrition/targets
```

**Response:**
```json
{
    "success": true,
    "data": {
        "target_calories": 2000,
        "target_protein": 150,
        "target_carbs": 200,
        "target_fat": 65
    }
}
```

---

## User Endpoints

### Get User Profile
```
GET /api/user/profile
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "Nathan Bowman",
        "email": "nathan@example.com",
        "role": "user",
        "birthdate": "1990-01-15",
        "height": 70,
        "avatar_url": "/static/uploads/avatars/user1.jpg",
        "target_calories": 2000,
        "target_protein": 150,
        "target_carbs": 200,
        "target_fat": 65,
        "created_at": "2024-01-01"
    }
}
```

### Update User Profile
```
PUT /api/user/profile
```

**Request Body:**
```json
{
    "name": "Nathan Bowman",
    "email": "nathan@example.com",
    "birthdate": "1990-01-15",
    "height": 70,
    "target_calories": 2000,
    "target_protein": 150,
    "target_carbs": 200,
    "target_fat": 65
}
```

### Upload Avatar
```
POST /api/user/avatar
Content-Type: multipart/form-data
```

**Form Data:**
- `avatar` (file): Avatar image file

### Update Password
```
PUT /api/user/password
```

**Request Body:**
```json
{
    "current_password": "oldpassword",
    "new_password": "newpassword"
}
```

### Get User Settings
```
GET /api/user/settings
```

**Response:**
```json
{
    "success": true,
    "data": {
        "weight_unit": "lbs",
        "height_unit": "inches",
        "date_format": "MM/DD/YYYY",
        "time_format": "12h",
        "items_per_page": 20,
        "email_notifications": true,
        "workout_reminders": true,
        "nutrition_reminders": true,
        "goal_progress_updates": true,
        "coaching_session_reminders": true,
        "profile_visible": true,
        "share_progress_photos": false
    }
}
```

### Update User Settings
```
PUT /api/user/settings
```

**Request Body:** Same as Get Settings response

### Get User Stats
```
GET /api/user/stats
```

**Response:**
```json
{
    "success": true,
    "data": {
        "member_since": "2024-01-01",
        "total_workouts": 45,
        "total_metrics": 120,
        "total_sessions": 8
    }
}
```

### Export User Data
```
POST /api/user/export-data
```

**Response:**
```json
{
    "success": true,
    "data": {
        "download_url": "/api/user/export/download/abc123.json",
        "expires_at": "2024-01-16T00:00:00Z"
    }
}
```

### Delete Account
```
DELETE /api/user/account
```

**Request Body:**
```json
{
    "confirmation": "DELETE"
}
```

---

## Error Codes

- `400` - Bad Request (validation errors)
- `401` - Unauthorized (not authenticated)
- `403` - Forbidden (not authorized)
- `404` - Not Found
- `409` - Conflict (duplicate entry)
- `500` - Internal Server Error

**Example Error Response:**
```json
{
    "success": false,
    "error": "Validation failed",
    "details": {
        "weight": "Weight must be a positive number",
        "date": "Date is required"
    }
}
```

---

## Authentication

All endpoints (except public portfolio routes) require authentication:

```
Authorization: Bearer <jwt_token>
```

Or session-based authentication with cookies.

---

**End of API Specification**
