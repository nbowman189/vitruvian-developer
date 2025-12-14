# RESTful API Layer

## Overview

This directory contains the complete RESTful API implementation for the multi-user health & fitness tracking application. The API provides 38 endpoints across 5 domains with comprehensive authentication, validation, and user data isolation.

**Base URL:** `/api`

**Authentication:** Flask-Login session-based authentication (all endpoints require login)

**Rate Limiting:** 100 requests per minute per IP address

---

## Quick Links

- **[API Documentation](./API_DOCUMENTATION.md)** - Complete API reference with examples
- **[Quick Start Guide](./QUICK_START.md)** - Get started in 5 minutes
- **[Implementation Summary](./IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[Deliverables Checklist](./DELIVERABLES_CHECKLIST.md)** - Verification of requirements

---

## Directory Structure

```
api/
├── __init__.py                     # Main API blueprint, helpers, validators
├── health.py                       # Health metrics endpoints (7)
├── workout.py                      # Workout & exercise endpoints (9)
├── coaching.py                     # Coaching, goals, photos endpoints (11)
├── nutrition.py                    # Nutrition & meal endpoints (7)
├── user.py                         # User profile & dashboard endpoints (4)
├── API_DOCUMENTATION.md            # Complete API reference
├── QUICK_START.md                  # Quick start guide
├── IMPLEMENTATION_SUMMARY.md       # Technical summary
├── DELIVERABLES_CHECKLIST.md       # Requirements checklist
└── README.md                       # This file
```

---

## API Modules

### 1. Health Metrics (`health.py`)
Track body composition, measurements, vital signs, and wellness indicators.

**Endpoints:** 7 total
- CRUD operations for health metrics
- Latest metric retrieval
- Summary statistics with trends

**Key Features:**
- One metric per user per date
- Calculated fields (lean body mass, fat mass)
- 30/60/90-day summaries

### 2. Workouts (`workout.py`)
Track workout sessions, exercises, and exercise definitions.

**Endpoints:** 9 total
- CRUD operations for workout sessions
- Add exercises to workouts
- Exercise definition library
- Workout statistics

**Key Features:**
- Session type filtering (strength, cardio, martial_arts, etc.)
- Volume and pace calculations
- Performance tracking (sets, reps, weight, RPE)

### 3. Coaching (`coaching.py`)
Manage coaching sessions, goals, and progress photos.

**Endpoints:** 11 total
- CRUD operations for coaching sessions
- CRUD operations for goals
- Goal completion tracking
- Progress photo management

**Key Features:**
- Coach-client relationship tracking
- Goal progress auto-calculation
- Overdue detection
- Photo categorization

### 4. Nutrition (`nutrition.py`)
Track meals, macronutrients, and adherence to meal plans.

**Endpoints:** 7 total
- CRUD operations for meal logs
- Daily nutrition summary
- Weekly nutrition summary

**Key Features:**
- Macronutrient tracking (protein, carbs, fat, fiber)
- Meal planning adherence
- Macro percentage calculations
- Daily and weekly aggregations

### 5. User Profile (`user.py`)
Manage user profiles, settings, and view dashboard.

**Endpoints:** 4 total
- Get/update user profile
- Get comprehensive dashboard
- Update user settings

**Key Features:**
- Profile management (name, bio, photo)
- Dashboard with recent data and statistics
- Email/username/password updates
- Weight trends and workout frequency

---

## Response Format

All endpoints use consistent JSON response format:

### Success Response
```json
{
  "success": true,
  "data": { /* response data */ },
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

## Quick Examples

### JavaScript/Fetch

```javascript
// Create health metric
const response = await fetch('/api/health/metrics', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    recorded_date: '2024-12-14',
    weight_lbs: 175.5,
    body_fat_percentage: 18.5,
    energy_level: 8
  })
});

const result = await response.json();
if (result.success) {
  console.log('Metric created:', result.data);
}
```

### Python/Requests

```python
import requests

session = requests.Session()

# Create workout
response = session.post(
    'http://localhost:8080/api/workouts',
    json={
        'session_date': '2024-12-14',
        'session_type': 'strength',
        'duration_minutes': 60
    }
)

result = response.json()
if result['success']:
    print('Workout created:', result['data'])
```

### cURL

```bash
# Get dashboard
curl -X GET \
  'http://localhost:8080/api/user/dashboard?days=30' \
  -H 'Content-Type: application/json' \
  -b cookies.txt
```

---

## Common Query Parameters

### Pagination
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)

### Filtering
- `start_date` (str): Start date filter (YYYY-MM-DD)
- `end_date` (str): End date filter (YYYY-MM-DD)
- `sort` (str): Sort order ('asc' or 'desc', default: 'desc')
- Type filters: `session_type`, `meal_type`, `goal_type`, `photo_type`
- Status filters: `status` (for goals)

### Summaries
- `days` (int): Number of days to include (default: 30, max: 365)
- `date` (str): Specific date for daily summaries (YYYY-MM-DD)

---

## Security Features

- ✅ **Authentication Required** - All endpoints require login
- ✅ **User Data Isolation** - Users can only access their own data
- ✅ **Active Account Check** - Inactive accounts cannot access API
- ✅ **Input Validation** - All inputs validated and sanitized
- ✅ **SQL Injection Prevention** - SQLAlchemy ORM usage
- ✅ **Rate Limiting** - 100 requests per minute
- ✅ **Secure Cookies** - HTTPOnly, SameSite protection
- ✅ **Password Hashing** - Bcrypt with proper rounds
- ✅ **Error Sanitization** - No internal details exposed

---

## Error Handling

### Common HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Example Error Response

```json
{
  "success": false,
  "data": {},
  "message": "Missing required fields",
  "errors": [
    "Missing field: recorded_date",
    "Missing field: session_type"
  ]
}
```

---

## Development Workflow

### Adding a New Endpoint

1. Add route to appropriate module (`health.py`, `workout.py`, etc.)
2. Apply `@require_active_user` decorator
3. Validate request data using `validate_request_data()`
4. Filter queries by `current_user.id`
5. Use `success_response()` or `error_response()`
6. Add error handling with try-catch
7. Log operation with `logger.info()` or `logger.error()`
8. Update documentation

### Testing

```python
# Example test
def test_create_health_metric(client, auth_user):
    data = {
        'recorded_date': '2024-12-14',
        'weight_lbs': 175.5
    }

    response = client.post('/api/health/metrics', json=data)

    assert response.status_code == 201
    assert response.json['success'] == True
```

---

## Integration with Frontend

### Recommended Approach

1. **Create API Client Class**
   ```javascript
   class APIClient {
     async call(endpoint, options = {}) {
       const response = await fetch(`/api${endpoint}`, {
         ...options,
         credentials: 'include',
         headers: { 'Content-Type': 'application/json', ...options.headers }
       });
       const result = await response.json();
       if (!result.success) throw new Error(result.message);
       return result.data;
     }
   }
   ```

2. **Use Async/Await**
   ```javascript
   const api = new APIClient();
   const metrics = await api.call('/health/metrics?days=30');
   ```

3. **Handle Errors**
   ```javascript
   try {
     await api.call('/health/metrics', { method: 'POST', body: JSON.stringify(data) });
   } catch (error) {
     console.error('Failed to create metric:', error.message);
   }
   ```

---

## Performance Considerations

- ✅ Database indexes on filtered fields
- ✅ Pagination for large datasets
- ✅ Connection pooling configured
- ✅ Query result limits (latest 10, etc.)
- ✅ Selective field loading

### Recommended Optimizations
- Add response caching for summaries
- Use database read replicas for heavy queries
- Implement data export for large date ranges
- Add database query caching

---

## Monitoring & Maintenance

### Logging
All operations are logged with:
- User ID
- Operation type (create, update, delete)
- Resource ID
- Timestamp
- Error details (if applicable)

### Metrics to Track
- Request count by endpoint
- Response time by endpoint
- Error rate by endpoint
- Rate limit violations
- Most active users
- Popular features

---

## Future Enhancements

Potential additions for future phases:

- [ ] API key authentication for programmatic access
- [ ] WebSocket support for real-time updates
- [ ] Bulk operations (batch create/update)
- [ ] Data export endpoints (CSV, JSON)
- [ ] Advanced analytics endpoints
- [ ] Social features (sharing, following)
- [ ] Notification system integration
- [ ] Third-party integrations (Fitbit, MyFitnessPal, etc.)

---

## Support & Contributing

### Getting Help
- Review [API Documentation](./API_DOCUMENTATION.md) for detailed endpoint information
- Check [Quick Start Guide](./QUICK_START.md) for common patterns
- Review [Implementation Summary](./IMPLEMENTATION_SUMMARY.md) for technical details

### Reporting Issues
- Check logs for detailed error information
- Include request/response examples
- Provide steps to reproduce
- Note expected vs actual behavior

### Contributing
- Follow existing code patterns
- Add tests for new endpoints
- Update documentation
- Use consistent error handling
- Include logging for operations

---

## Version History

### v1.0 (Current) - December 14, 2024
- Initial release
- 38 endpoints across 5 domains
- Complete CRUD operations for all models
- Authentication and authorization
- Input validation and error handling
- Rate limiting
- Comprehensive documentation

---

## License & Contact

**Project:** Primary Assistant - Multi-User Health & Fitness Tracking
**Developer:** Nathan Bowman
**Email:** nbowman189@gmail.com
**GitHub:** https://github.com/nbowman189

---

**Status:** ✅ Production Ready
