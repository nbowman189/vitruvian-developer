# API Documentation

## Overview

This RESTful API provides complete access to the multi-user health & fitness tracking application. All endpoints require authentication and enforce user data isolation.

**Base URL:** `/api`

**Authentication:** All endpoints require user authentication via Flask-Login session cookies.

**Rate Limiting:** 100 requests per minute per IP address (configurable in production).

---

## Table of Contents

1. [Response Format](#response-format)
2. [Error Handling](#error-handling)
3. [Pagination](#pagination)
4. [Health Metrics API](#health-metrics-api)
5. [Workout API](#workout-api)
6. [Coaching API](#coaching-api)
7. [Nutrition API](#nutrition-api)
8. [User Profile API](#user-profile-api)
9. [Code Examples](#code-examples)

---

## Response Format

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data here
  },
  "message": "Success message"
}
```

### Error Response

```json
{
  "success": false,
  "data": {},
  "message": "Error message",
  "errors": ["Detailed error 1", "Detailed error 2"]
}
```

### Paginated Response

```json
{
  "success": true,
  "data": [
    // Array of items
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  },
  "message": "Success message"
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Common Error Responses

**Authentication Required (401)**
```json
{
  "success": false,
  "data": {},
  "message": "Authentication required",
  "errors": []
}
```

**Validation Error (400)**
```json
{
  "success": false,
  "data": {},
  "message": "Missing required fields",
  "errors": ["Missing field: recorded_date", "Missing field: session_type"]
}
```

**Rate Limit Exceeded (429)**
```json
{
  "success": false,
  "data": {},
  "message": "Rate limit exceeded. Please try again later.",
  "errors": []
}
```

---

## Pagination

Many list endpoints support pagination via query parameters:

- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)

**Example:**
```
GET /api/health/metrics?page=2&per_page=50
```

---

## Health Metrics API

### List Health Metrics

**Endpoint:** `GET /api/health/metrics`

**Description:** Get paginated list of health metrics for authenticated user.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `start_date` (str): Filter by start date (ISO format: YYYY-MM-DD)
- `end_date` (str): Filter by end date (ISO format: YYYY-MM-DD)
- `sort` (str): Sort order ('asc' or 'desc', default: 'desc')

**Example Request:**
```http
GET /api/health/metrics?start_date=2024-01-01&end_date=2024-12-31&page=1&per_page=20
```

**Example Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "recorded_date": "2024-12-14",
      "weight_lbs": 175.5,
      "body_fat_percentage": 18.5,
      "muscle_mass_lbs": null,
      "bmi": 23.8,
      "measurements": {
        "waist_inches": 32.0,
        "chest_inches": 40.0,
        "left_arm_inches": 14.5,
        "right_arm_inches": 14.5,
        "left_thigh_inches": 22.0,
        "right_thigh_inches": 22.0,
        "hips_inches": 38.0,
        "neck_inches": 15.5
      },
      "vital_signs": {
        "resting_heart_rate": 65,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "blood_pressure": "120/80"
      },
      "wellness": {
        "energy_level": 8,
        "mood": 7,
        "sleep_quality": 7,
        "stress_level": 4
      },
      "notes": "Feeling strong after consistent training",
      "created_at": "2024-12-14T10:30:00Z",
      "updated_at": "2024-12-14T10:30:00Z",
      "calculated": {
        "lean_body_mass_lbs": 143.03,
        "fat_mass_lbs": 32.47
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  },
  "message": "Retrieved 1 health metrics"
}
```

---

### Create Health Metric

**Endpoint:** `POST /api/health/metrics`

**Description:** Create a new health metric entry.

**Request Body:**
```json
{
  "recorded_date": "2024-12-14",
  "weight_lbs": 175.5,
  "body_fat_percentage": 18.5,
  "waist_inches": 32.0,
  "chest_inches": 40.0,
  "resting_heart_rate": 65,
  "blood_pressure_systolic": 120,
  "blood_pressure_diastolic": 80,
  "energy_level": 8,
  "mood": 7,
  "sleep_quality": 7,
  "stress_level": 4,
  "notes": "Feeling strong"
}
```

**Required Fields:**
- `recorded_date` (str): Date in ISO format (YYYY-MM-DD)

**Optional Fields:**
- `weight_lbs` (float)
- `body_fat_percentage` (float): 0-100
- `muscle_mass_lbs` (float)
- `bmi` (float)
- `waist_inches`, `chest_inches`, `left_arm_inches`, `right_arm_inches`, `left_thigh_inches`, `right_thigh_inches`, `hips_inches`, `neck_inches` (float)
- `resting_heart_rate` (int): 20-300
- `blood_pressure_systolic` (int): 50-300
- `blood_pressure_diastolic` (int): 30-200
- `energy_level`, `mood`, `sleep_quality`, `stress_level` (int): 1-10
- `notes` (str)

**Example Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": 1,
    "recorded_date": "2024-12-14",
    // ... full metric data
  },
  "message": "Health metric created successfully"
}
```

**Error Response (409 - Duplicate):**
```json
{
  "success": false,
  "data": {},
  "message": "Health metric already exists for 2024-12-14",
  "errors": ["Use PUT to update existing metric"]
}
```

---

### Get Health Metric

**Endpoint:** `GET /api/health/metrics/<id>`

**Description:** Get a specific health metric by ID.

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    // ... metric data
  },
  "message": "Health metric retrieved successfully"
}
```

---

### Update Health Metric

**Endpoint:** `PUT /api/health/metrics/<id>`

**Description:** Update an existing health metric. All fields are optional.

**Request Body:**
```json
{
  "weight_lbs": 176.0,
  "body_fat_percentage": 18.3,
  "notes": "Updated notes"
}
```

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    // ... updated metric data
  },
  "message": "Health metric updated successfully"
}
```

---

### Delete Health Metric

**Endpoint:** `DELETE /api/health/metrics/<id>`

**Description:** Delete a health metric.

**Example Response (200):**
```json
{
  "success": true,
  "data": {},
  "message": "Health metric deleted successfully"
}
```

---

### Get Latest Health Metric

**Endpoint:** `GET /api/health/metrics/latest`

**Description:** Get the most recent health metric.

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "recorded_date": "2024-12-14",
    // ... latest metric data
  },
  "message": "Latest health metric retrieved successfully"
}
```

---

### Get Health Metrics Summary

**Endpoint:** `GET /api/health/metrics/summary`

**Description:** Get summary statistics for health metrics.

**Query Parameters:**
- `days` (int): Number of days to include (default: 30, max: 365)

**Example Request:**
```http
GET /api/health/metrics/summary?days=30
```

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-11-14",
      "end_date": "2024-12-14",
      "days": 30
    },
    "total_entries": 25,
    "latest": {
      "id": 45,
      "recorded_date": "2024-12-14",
      // ... latest metric data
    },
    "averages": {
      "weight_lbs": 175.8,
      "body_fat_percentage": 18.6,
      "energy_level": 7.5,
      "mood": 7.2,
      "sleep_quality": 7.0,
      "stress_level": 4.3
    },
    "changes": {
      "weight_lbs": -2.5,
      "body_fat_percentage": -1.2
    }
  },
  "message": "Summary statistics for 30 days"
}
```

---

## Workout API

### List Workouts

**Endpoint:** `GET /api/workouts`

**Description:** Get paginated list of workout sessions.

**Query Parameters:**
- `page`, `per_page`, `start_date`, `end_date`, `sort`
- `session_type` (str): Filter by type (strength, cardio, flexibility, martial_arts, sports, recovery, mixed)

**Example Request:**
```http
GET /api/workouts?session_type=strength&page=1
```

**Example Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "session_date": "2024-12-14",
      "session_type": "strength",
      "duration_minutes": 60,
      "program": {
        "phase": "Hypertrophy",
        "week": 4,
        "day": 2
      },
      "feedback": {
        "intensity": 8,
        "fatigue": 7,
        "soreness": 5
      },
      "notes": "Great session",
      "coach_notes": null,
      "stats": {
        "total_exercises": 5,
        "total_sets": 15,
        "average_rpe": 8.2
      },
      "created_at": "2024-12-14T10:30:00Z",
      "updated_at": "2024-12-14T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 32,
    "pages": 2
  },
  "message": "Success"
}
```

---

### Create Workout

**Endpoint:** `POST /api/workouts`

**Description:** Create a new workout session.

**Request Body:**
```json
{
  "session_date": "2024-12-14",
  "session_type": "strength",
  "duration_minutes": 60,
  "program_phase": "Hypertrophy",
  "week_number": 4,
  "day_number": 2,
  "intensity": 8,
  "fatigue": 7,
  "soreness": 5,
  "notes": "Great session"
}
```

**Required Fields:**
- `session_date` (str): ISO date
- `session_type` (str): One of: strength, cardio, flexibility, martial_arts, sports, recovery, mixed

**Optional Fields:**
- `duration_minutes` (int): 1-480
- `program_phase` (str)
- `week_number`, `day_number` (int)
- `intensity`, `fatigue`, `soreness` (int): 1-10
- `notes`, `coach_notes` (str)

**Example Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    // ... workout data
  },
  "message": "Workout session created successfully"
}
```

---

### Get Workout

**Endpoint:** `GET /api/workouts/<id>`

**Description:** Get a specific workout with exercises.

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "session_date": "2024-12-14",
    // ... workout data
    "exercises": [
      {
        "id": 1,
        "exercise_name": "Bench Press",
        "performance": {
          "sets": 3,
          "reps": 10,
          "weight_lbs": 185,
          "rest_seconds": 90
        },
        "feedback": {
          "form_quality": 9,
          "rpe": 8
        },
        "calculated": {
          "total_volume": 5550
        },
        "notes": "Felt strong"
      }
    ]
  },
  "message": "Workout session retrieved successfully"
}
```

---

### Add Exercise to Workout

**Endpoint:** `POST /api/workouts/<id>/exercises`

**Description:** Add an exercise log to a workout session.

**Request Body:**
```json
{
  "exercise_name": "Bench Press",
  "sets": 3,
  "reps": 10,
  "weight_lbs": 185,
  "rest_seconds": 90,
  "form_quality": 9,
  "rpe": 8,
  "notes": "Felt strong"
}
```

**Required Fields:**
- `exercise_name` (str)

**Optional Fields:**
- `exercise_definition_id` (int)
- `sets` (int): 1-50
- `reps` (int): 1-500
- `weight_lbs` (float)
- `rest_seconds` (int): 0-600
- `duration_seconds` (int)
- `distance_miles` (float)
- `form_quality`, `rpe` (int): 1-10
- `notes` (str)

**Example Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "exercise_name": "Bench Press",
    // ... exercise data
  },
  "message": "Exercise added successfully"
}
```

---

### Get Workout Statistics

**Endpoint:** `GET /api/workouts/stats`

**Description:** Get workout statistics and progress.

**Query Parameters:**
- `days` (int): Number of days (default: 30, max: 365)

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-11-14",
      "end_date": "2024-12-14",
      "days": 30
    },
    "totals": {
      "workouts": 20,
      "duration_minutes": 1200,
      "exercises": 100,
      "sets": 300
    },
    "averages": {
      "duration_minutes": 60.0,
      "intensity": 7.8,
      "workouts_per_week": 4.7
    },
    "by_type": {
      "strength": 15,
      "cardio": 3,
      "martial_arts": 2
    }
  },
  "message": "Statistics for 30 days"
}
```

---

### List Exercise Definitions

**Endpoint:** `GET /api/workouts/exercises/definitions`

**Description:** Get all active exercise definitions.

**Query Parameters:**
- `category` (str): Filter by category
- `search` (str): Search by name

**Example Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Bench Press",
      "category": "compound",
      "muscle_groups": ["chest", "triceps", "shoulders"],
      "equipment_needed": ["barbell", "bench"],
      "difficulty_level": "intermediate",
      "description": "Horizontal pressing movement",
      "instructions": "Step-by-step instructions...",
      "tips": "Form tips...",
      "video_url": "https://example.com/video",
      "image_url": "https://example.com/image",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "message": "Retrieved 1 exercise definitions"
}
```

---

### Create Exercise Definition

**Endpoint:** `POST /api/workouts/exercises/definitions`

**Description:** Create a new exercise definition.

**Request Body:**
```json
{
  "name": "Bench Press",
  "category": "compound",
  "muscle_groups": ["chest", "triceps", "shoulders"],
  "difficulty_level": "intermediate",
  "equipment_needed": ["barbell", "bench"],
  "description": "Horizontal pressing movement",
  "instructions": "Step-by-step instructions...",
  "tips": "Form tips..."
}
```

**Required Fields:**
- `name` (str)
- `category` (str): compound, isolation, cardio, flexibility, core, plyometric, martial_arts
- `muscle_groups` (array of strings)
- `difficulty_level` (str): beginner, intermediate, advanced, expert

**Example Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    // ... exercise definition data
  },
  "message": "Exercise definition created successfully"
}
```

---

## Coaching API

### List Coaching Sessions

**Endpoint:** `GET /api/coaching/sessions`

**Query Parameters:** page, per_page, start_date, end_date, sort

### Create Coaching Session

**Endpoint:** `POST /api/coaching/sessions`

**Request Body:**
```json
{
  "session_date": "2024-12-14",
  "coach_id": 2,
  "duration_minutes": 60,
  "topics": ["nutrition", "training plan"],
  "discussion_notes": "Discussed meal planning strategies",
  "coach_feedback": "Great progress this week",
  "action_items": ["Increase protein intake", "Add mobility work"],
  "next_session_date": "2024-12-21"
}
```

---

### List Goals

**Endpoint:** `GET /api/coaching/goals`

**Query Parameters:**
- `status` (str): active, completed, paused, abandoned
- `goal_type` (str): weight_loss, muscle_gain, strength, endurance, flexibility, skill, habit, nutrition, other

**Example Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "goal_type": "weight_loss",
      "title": "Lose 10 pounds",
      "description": "Gradual weight loss over 3 months",
      "target": {
        "value": 165,
        "unit": "lbs",
        "date": "2025-03-14"
      },
      "progress": {
        "current_value": 170,
        "percentage": 50.0
      },
      "timeline": {
        "start_date": "2024-12-14",
        "completed_date": null,
        "days_remaining": 90,
        "days_active": 0,
        "is_overdue": false
      },
      "status": "active",
      "notes": "On track",
      "milestones": ["Hit 172 lbs", "Hit 168 lbs"],
      "created_at": "2024-12-14T10:00:00Z"
    }
  ],
  "message": "Retrieved 1 goals"
}
```

---

### Create Goal

**Endpoint:** `POST /api/coaching/goals`

**Request Body:**
```json
{
  "goal_type": "weight_loss",
  "title": "Lose 10 pounds",
  "description": "Gradual weight loss over 3 months",
  "target_value": 165,
  "target_unit": "lbs",
  "target_date": "2025-03-14",
  "milestones": ["Hit 172 lbs", "Hit 168 lbs", "Hit 165 lbs"]
}
```

**Required Fields:**
- `goal_type` (str)
- `title` (str)

---

### Complete Goal

**Endpoint:** `PUT /api/coaching/goals/<id>/complete`

**Description:** Mark a goal as completed.

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "status": "completed",
    "completed_date": "2024-12-14",
    "progress": {
      "percentage": 100.0
    }
  },
  "message": "Goal marked as completed"
}
```

---

### List Progress Photos

**Endpoint:** `GET /api/coaching/progress/photos`

**Query Parameters:**
- page, per_page, start_date, end_date
- `photo_type` (str): front, side, back, flex, comparison, other

---

### Upload Progress Photo

**Endpoint:** `POST /api/coaching/progress/photos`

**Request Body:**
```json
{
  "photo_date": "2024-12-14",
  "photo_url": "https://storage.example.com/photos/123.jpg",
  "photo_type": "front",
  "weight_lbs": 175.5,
  "body_fat_percentage": 18.5,
  "notes": "12 weeks into training",
  "is_public": false
}
```

---

## Nutrition API

### List Meals

**Endpoint:** `GET /api/nutrition/meals`

**Query Parameters:**
- page, per_page, start_date, end_date, sort
- `meal_type` (str): breakfast, lunch, dinner, snack, pre_workout, post_workout, other

---

### Create Meal

**Endpoint:** `POST /api/nutrition/meals`

**Request Body:**
```json
{
  "meal_date": "2024-12-14",
  "meal_type": "breakfast",
  "meal_time": "08:30",
  "calories": 650,
  "protein_g": 45,
  "carbs_g": 60,
  "fat_g": 20,
  "fiber_g": 8,
  "water_oz": 16,
  "description": "Scrambled eggs with oatmeal",
  "foods": "4 eggs, 1 cup oatmeal, berries",
  "planned_meal": true,
  "adherence_to_plan": "perfect",
  "satisfaction": 9,
  "hunger_before": 7,
  "hunger_after": 2,
  "notes": "Felt energized"
}
```

**Required Fields:**
- `meal_date` (str)
- `meal_type` (str)

**Optional Fields:**
- `meal_time` (str): HH:MM format
- `calories` (int): 0-10000
- `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `sugar_g` (float)
- `sodium_mg` (int)
- `water_oz` (float)
- `description`, `foods`, `recipe_name` (str)
- `adherence_to_plan` (str): perfect, good, fair, poor, off_plan
- `planned_meal` (bool)
- `satisfaction`, `hunger_before`, `hunger_after` (int): 1-10
- `notes` (str)

---

### Get Daily Nutrition Summary

**Endpoint:** `GET /api/nutrition/daily-summary`

**Query Parameters:**
- `date` (str): Date to summarize (YYYY-MM-DD, default: today)

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "date": "2024-12-14",
    "total_meals": 5,
    "nutrition_totals": {
      "calories": 2100,
      "protein_g": 180,
      "carbs_g": 210,
      "fat_g": 65,
      "fiber_g": 35,
      "water_oz": 80
    },
    "macronutrient_breakdown": {
      "protein_percentage": 34,
      "carbs_percentage": 40,
      "fat_percentage": 26,
      "ratio": "34/40/26"
    },
    "meal_planning": {
      "planned_meals": 4,
      "unplanned_meals": 1,
      "adherence_rate": 80.0
    },
    "meals": [
      // ... meal details
    ]
  },
  "message": "Daily summary for 2024-12-14"
}
```

---

### Get Weekly Nutrition Summary

**Endpoint:** `GET /api/nutrition/weekly-summary`

**Query Parameters:**
- `start_date` (str): Week start date (default: 7 days ago)

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-12-07",
      "end_date": "2024-12-13",
      "days": 7
    },
    "total_meals": 35,
    "weekly_totals": {
      "calories": 14700,
      "protein_g": 1260,
      "carbs_g": 1470,
      "fat_g": 455
    },
    "daily_averages": {
      "calories": 2100,
      "protein_g": 180,
      "carbs_g": 210,
      "fat_g": 65
    },
    "adherence": {
      "planned_meals": 28,
      "total_meals": 35,
      "adherence_rate": 80.0
    },
    "daily_breakdown": [
      // ... daily summaries
    ]
  },
  "message": "Weekly summary from 2024-12-07 to 2024-12-13"
}
```

---

## User Profile API

### Get Profile

**Endpoint:** `GET /api/user/profile`

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "athlete123",
    "email": "athlete@example.com",
    "role": "user",
    "is_active": true,
    "full_name": "John Athlete",
    "profile_photo_url": "https://example.com/photo.jpg",
    "bio": "Fitness enthusiast",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-12-14T10:00:00Z",
    "failed_login_attempts": 0,
    "is_locked": false
  },
  "message": "Profile retrieved successfully"
}
```

---

### Update Profile

**Endpoint:** `PUT /api/user/profile`

**Request Body:**
```json
{
  "full_name": "John Athlete",
  "bio": "Dedicated fitness enthusiast and martial artist",
  "profile_photo_url": "https://example.com/new-photo.jpg"
}
```

---

### Get Dashboard

**Endpoint:** `GET /api/user/dashboard`

**Query Parameters:**
- `days` (int): Number of days (default: 30)

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "athlete123"
      // ... user data
    },
    "period": {
      "start_date": "2024-11-14",
      "end_date": "2024-12-14",
      "days": 30
    },
    "latest_metric": {
      // ... latest health metric
    },
    "recent_metrics": [
      // ... 5 recent metrics
    ],
    "recent_workouts": [
      // ... 5 recent workouts
    ],
    "active_goals": [
      // ... 5 active goals
    ],
    "statistics": {
      "weight_trend": {
        "current": 175.5,
        "previous": 178.0,
        "change": -2.5,
        "direction": "down"
      },
      "workout_frequency": {
        "total_workouts": 20,
        "workouts_per_week": 4.7,
        "days_period": 30
      },
      "goals_summary": {
        "total_active": 3,
        "on_track": 2,
        "overdue": 1,
        "completion_rate": 65.0
      },
      "streaks": {
        "current_workout_streak": 0,
        "current_logging_streak": 0
      }
    }
  },
  "message": "Dashboard data for 30 days"
}
```

---

### Update Settings

**Endpoint:** `PUT /api/user/settings`

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "username": "newusername",
  "current_password": "currentpass123",
  "new_password": "newpass456"
}
```

**All fields are optional, but:**
- `current_password` is required when changing password
- Email and username must be unique

**Example Response (200):**
```json
{
  "success": true,
  "data": {
    // ... updated user data
  },
  "message": "Settings updated successfully"
}
```

**Error Response (401 - Wrong Password):**
```json
{
  "success": false,
  "data": {},
  "message": "Current password is incorrect",
  "errors": []
}
```

**Error Response (409 - Conflict):**
```json
{
  "success": false,
  "data": {},
  "message": "Email already exists",
  "errors": []
}
```

---

## Code Examples

### JavaScript/Fetch

```javascript
// Get health metrics
async function getHealthMetrics(startDate, endDate) {
  const response = await fetch(
    `/api/health/metrics?start_date=${startDate}&end_date=${endDate}`,
    {
      method: 'GET',
      credentials: 'include',  // Important for session cookies
      headers: {
        'Content-Type': 'application/json'
      }
    }
  );

  const result = await response.json();

  if (!result.success) {
    throw new Error(result.message);
  }

  return result.data;
}

// Create health metric
async function createHealthMetric(data) {
  const response = await fetch('/api/health/metrics', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });

  const result = await response.json();

  if (!result.success) {
    throw new Error(result.message);
  }

  return result.data;
}

// Usage
const newMetric = await createHealthMetric({
  recorded_date: '2024-12-14',
  weight_lbs: 175.5,
  body_fat_percentage: 18.5,
  energy_level: 8
});
```

### Python/Requests

```python
import requests

BASE_URL = 'http://localhost:8080/api'

# Create session to persist cookies
session = requests.Session()

# Get health metrics
def get_health_metrics(start_date, end_date):
    response = session.get(
        f'{BASE_URL}/health/metrics',
        params={'start_date': start_date, 'end_date': end_date}
    )

    result = response.json()

    if not result['success']:
        raise Exception(result['message'])

    return result['data']

# Create health metric
def create_health_metric(data):
    response = session.post(
        f'{BASE_URL}/health/metrics',
        json=data
    )

    result = response.json()

    if not result['success']:
        raise Exception(result['message'])

    return result['data']

# Usage
new_metric = create_health_metric({
    'recorded_date': '2024-12-14',
    'weight_lbs': 175.5,
    'body_fat_percentage': 18.5,
    'energy_level': 8
})
```

### cURL

```bash
# Get health metrics
curl -X GET \
  'http://localhost:8080/api/health/metrics?start_date=2024-01-01&end_date=2024-12-31' \
  -H 'Content-Type: application/json' \
  -b cookies.txt

# Create health metric
curl -X POST \
  'http://localhost:8080/api/health/metrics' \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{
    "recorded_date": "2024-12-14",
    "weight_lbs": 175.5,
    "body_fat_percentage": 18.5,
    "energy_level": 8
  }'

# Update health metric
curl -X PUT \
  'http://localhost:8080/api/health/metrics/1' \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{
    "weight_lbs": 176.0,
    "notes": "Updated notes"
  }'

# Delete health metric
curl -X DELETE \
  'http://localhost:8080/api/health/metrics/1' \
  -H 'Content-Type: application/json' \
  -b cookies.txt
```

---

## API Versioning

**Current Version:** v1 (implicit)

**Future Versioning Strategy:**
- New versions will use URL prefix: `/api/v2/...`
- v1 will be maintained for backward compatibility
- Breaking changes will only occur in new versions
- Deprecation notices will be provided 6 months in advance

---

## Rate Limiting

- **Default Limit:** 100 requests per minute per IP address
- **Headers Returned:**
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

**Example Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702555200
```

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Never expose sensitive tokens in URLs**
3. **Implement CSRF protection** (Flask-WTF handles this)
4. **Validate all input data**
5. **Use secure session cookies** (configured in Flask app)
6. **Implement proper error handling** (don't expose internal details)
7. **Log security events** (authentication failures, suspicious activity)
8. **Rate limit aggressively in production**

---

## Contact & Support

For API support or questions, contact: nbowman189@gmail.com

**GitHub:** https://github.com/nbowman189
