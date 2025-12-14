# API Quick Start Guide

## Getting Started in 5 Minutes

### 1. Import the API Client

```javascript
// In your frontend JavaScript
const API_BASE = '/api';

// Helper function for API calls
async function apiCall(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include',  // Important for session cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  });

  const result = await response.json();

  if (!result.success) {
    throw new Error(result.message);
  }

  return result.data;
}
```

### 2. Common Operations

#### Health Metrics

```javascript
// Get latest health metric
const latest = await apiCall('/health/metrics/latest');
console.log(`Current weight: ${latest.weight_lbs} lbs`);

// Create new health metric
const newMetric = await apiCall('/health/metrics', {
  method: 'POST',
  body: JSON.stringify({
    recorded_date: '2024-12-14',
    weight_lbs: 175.5,
    body_fat_percentage: 18.5,
    energy_level: 8
  })
});

// Get 30-day summary
const summary = await apiCall('/health/metrics/summary?days=30');
console.log(`Average weight: ${summary.averages.weight_lbs} lbs`);
console.log(`Weight change: ${summary.changes.weight_lbs} lbs`);
```

#### Workouts

```javascript
// Create workout session
const workout = await apiCall('/workouts', {
  method: 'POST',
  body: JSON.stringify({
    session_date: '2024-12-14',
    session_type: 'strength',
    duration_minutes: 60,
    intensity: 8
  })
});

// Add exercises to workout
const exercise = await apiCall(`/workouts/${workout.id}/exercises`, {
  method: 'POST',
  body: JSON.stringify({
    exercise_name: 'Bench Press',
    sets: 3,
    reps: 10,
    weight_lbs: 185,
    rpe: 8
  })
});

// Get workout stats
const stats = await apiCall('/workouts/stats?days=30');
console.log(`Total workouts: ${stats.totals.workouts}`);
console.log(`Workouts per week: ${stats.averages.workouts_per_week}`);
```

#### Goals

```javascript
// Create a goal
const goal = await apiCall('/coaching/goals', {
  method: 'POST',
  body: JSON.stringify({
    goal_type: 'weight_loss',
    title: 'Lose 10 pounds',
    target_value: 165,
    target_unit: 'lbs',
    target_date: '2025-03-14',
    milestones: ['Hit 172 lbs', 'Hit 168 lbs', 'Hit 165 lbs']
  })
});

// Update goal progress
await apiCall(`/coaching/goals/${goal.id}`, {
  method: 'PUT',
  body: JSON.stringify({
    current_value: 170,
    notes: 'Making good progress!'
  })
});

// Complete goal
await apiCall(`/coaching/goals/${goal.id}/complete`, {
  method: 'PUT'
});
```

#### Nutrition

```javascript
// Log a meal
const meal = await apiCall('/nutrition/meals', {
  method: 'POST',
  body: JSON.stringify({
    meal_date: '2024-12-14',
    meal_type: 'breakfast',
    meal_time: '08:30',
    calories: 650,
    protein_g: 45,
    carbs_g: 60,
    fat_g: 20,
    planned_meal: true,
    satisfaction: 9
  })
});

// Get daily summary
const daily = await apiCall('/nutrition/daily-summary?date=2024-12-14');
console.log(`Total calories: ${daily.nutrition_totals.calories}`);
console.log(`Macro ratio: ${daily.macronutrient_breakdown.ratio}`);
console.log(`Adherence: ${daily.meal_planning.adherence_rate}%`);

// Get weekly summary
const weekly = await apiCall('/nutrition/weekly-summary');
console.log(`Avg calories per day: ${weekly.daily_averages.calories}`);
```

#### Dashboard

```javascript
// Get complete dashboard
const dashboard = await apiCall('/user/dashboard?days=30');

console.log('Latest Metric:', dashboard.latest_metric);
console.log('Recent Workouts:', dashboard.recent_workouts);
console.log('Active Goals:', dashboard.active_goals);
console.log('Weight Trend:', dashboard.statistics.weight_trend);
console.log('Workout Frequency:', dashboard.statistics.workout_frequency);
```

### 3. Error Handling

```javascript
async function safeApiCall(endpoint, options = {}) {
  try {
    const data = await apiCall(endpoint, options);
    return { success: true, data };
  } catch (error) {
    console.error('API Error:', error.message);
    return { success: false, error: error.message };
  }
}

// Usage
const result = await safeApiCall('/health/metrics/latest');
if (result.success) {
  console.log('Latest metric:', result.data);
} else {
  console.error('Failed to fetch metric:', result.error);
}
```

### 4. Pagination

```javascript
// Fetch paginated data
async function fetchAllMetrics(startDate, endDate) {
  let page = 1;
  const perPage = 50;
  let allMetrics = [];

  while (true) {
    const response = await fetch(
      `${API_BASE}/health/metrics?start_date=${startDate}&end_date=${endDate}&page=${page}&per_page=${perPage}`,
      { credentials: 'include' }
    );

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.message);
    }

    allMetrics = allMetrics.concat(result.data);

    // Check if we've fetched all pages
    if (page >= result.pagination.pages) {
      break;
    }

    page++;
  }

  return allMetrics;
}
```

### 5. Date Filtering

```javascript
// Get metrics for last 30 days
const thirtyDaysAgo = new Date();
thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

const startDate = thirtyDaysAgo.toISOString().split('T')[0];
const endDate = new Date().toISOString().split('T')[0];

const metrics = await apiCall(
  `/health/metrics?start_date=${startDate}&end_date=${endDate}&sort=asc`
);
```

---

## Common Response Formats

### Success Response
```json
{
  "success": true,
  "data": { /* your data here */ },
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
  "data": [ /* array of items */ ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  },
  "message": "Success"
}
```

---

## Quick Reference: All Endpoints

### Health Metrics
- `GET /api/health/metrics` - List metrics
- `POST /api/health/metrics` - Create metric
- `GET /api/health/metrics/<id>` - Get metric
- `PUT /api/health/metrics/<id>` - Update metric
- `DELETE /api/health/metrics/<id>` - Delete metric
- `GET /api/health/metrics/latest` - Get latest
- `GET /api/health/metrics/summary` - Get summary

### Workouts
- `GET /api/workouts` - List workouts
- `POST /api/workouts` - Create workout
- `GET /api/workouts/<id>` - Get workout
- `PUT /api/workouts/<id>` - Update workout
- `DELETE /api/workouts/<id>` - Delete workout
- `POST /api/workouts/<id>/exercises` - Add exercise
- `GET /api/workouts/stats` - Get statistics
- `GET /api/workouts/exercises/definitions` - List exercises
- `POST /api/workouts/exercises/definitions` - Create exercise

### Coaching
- `GET /api/coaching/sessions` - List sessions
- `POST /api/coaching/sessions` - Create session
- `GET /api/coaching/sessions/<id>` - Get session
- `PUT /api/coaching/sessions/<id>` - Update session
- `DELETE /api/coaching/sessions/<id>` - Delete session
- `GET /api/coaching/goals` - List goals
- `POST /api/coaching/goals` - Create goal
- `PUT /api/coaching/goals/<id>` - Update goal
- `PUT /api/coaching/goals/<id>/complete` - Complete goal
- `GET /api/coaching/progress/photos` - List photos
- `POST /api/coaching/progress/photos` - Upload photo

### Nutrition
- `GET /api/nutrition/meals` - List meals
- `POST /api/nutrition/meals` - Create meal
- `GET /api/nutrition/meals/<id>` - Get meal
- `PUT /api/nutrition/meals/<id>` - Update meal
- `DELETE /api/nutrition/meals/<id>` - Delete meal
- `GET /api/nutrition/daily-summary` - Daily summary
- `GET /api/nutrition/weekly-summary` - Weekly summary

### User
- `GET /api/user/profile` - Get profile
- `PUT /api/user/profile` - Update profile
- `GET /api/user/dashboard` - Get dashboard
- `PUT /api/user/settings` - Update settings

---

## Common Patterns

### Create → Get → Update → Delete

```javascript
// 1. Create
const created = await apiCall('/health/metrics', {
  method: 'POST',
  body: JSON.stringify({ recorded_date: '2024-12-14', weight_lbs: 175 })
});

// 2. Get
const fetched = await apiCall(`/health/metrics/${created.id}`);

// 3. Update
const updated = await apiCall(`/health/metrics/${created.id}`, {
  method: 'PUT',
  body: JSON.stringify({ weight_lbs: 176 })
});

// 4. Delete
await apiCall(`/health/metrics/${created.id}`, { method: 'DELETE' });
```

### List → Filter → Sort

```javascript
// Get all strength workouts from last month, sorted oldest first
const workouts = await apiCall(
  '/workouts?session_type=strength&start_date=2024-11-14&end_date=2024-12-14&sort=asc'
);
```

### Summary Statistics

```javascript
// Get 90-day health summary
const healthSummary = await apiCall('/health/metrics/summary?days=90');

// Get 30-day workout stats
const workoutStats = await apiCall('/workouts/stats?days=30');

// Get today's nutrition
const today = new Date().toISOString().split('T')[0];
const nutritionToday = await apiCall(`/nutrition/daily-summary?date=${today}`);
```

---

## Tips & Best Practices

1. **Always include `credentials: 'include'`** - Required for session authentication
2. **Check `result.success`** before using data
3. **Use try-catch** for error handling
4. **Paginate large datasets** - Don't fetch everything at once
5. **Filter on the server** - Use query parameters instead of client-side filtering
6. **Cache when appropriate** - Store dashboard data, refresh periodically
7. **Validate dates** - Use ISO format (YYYY-MM-DD)
8. **Handle rate limits** - Implement exponential backoff on 429 errors

---

## Full Example: Health Tracking App

```javascript
class HealthTracker {
  constructor() {
    this.apiBase = '/api';
  }

  async call(endpoint, options = {}) {
    const response = await fetch(`${this.apiBase}${endpoint}`, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    const result = await response.json();
    if (!result.success) throw new Error(result.message);
    return result.data;
  }

  // Health Metrics
  async getMetrics(startDate, endDate) {
    return this.call(`/health/metrics?start_date=${startDate}&end_date=${endDate}`);
  }

  async logMetric(data) {
    return this.call('/health/metrics', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getLatestMetric() {
    return this.call('/health/metrics/latest');
  }

  async getSummary(days = 30) {
    return this.call(`/health/metrics/summary?days=${days}`);
  }

  // Workouts
  async logWorkout(data) {
    return this.call('/workouts', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async addExercise(workoutId, exercise) {
    return this.call(`/workouts/${workoutId}/exercises`, {
      method: 'POST',
      body: JSON.stringify(exercise)
    });
  }

  async getWorkoutStats(days = 30) {
    return this.call(`/workouts/stats?days=${days}`);
  }

  // Dashboard
  async getDashboard(days = 30) {
    return this.call(`/user/dashboard?days=${days}`);
  }
}

// Usage
const tracker = new HealthTracker();

// Log today's metrics
await tracker.logMetric({
  recorded_date: new Date().toISOString().split('T')[0],
  weight_lbs: 175.5,
  body_fat_percentage: 18.5,
  energy_level: 8
});

// Get dashboard
const dashboard = await tracker.getDashboard(30);
console.log('Weight trend:', dashboard.statistics.weight_trend);
console.log('Workouts per week:', dashboard.statistics.workout_frequency.workouts_per_week);
```

---

For complete documentation, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
