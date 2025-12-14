# Vitruvian Tracker - Frontend Guide

Complete documentation for the frontend user interface implementation.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Template Hierarchy](#template-hierarchy)
3. [Component Library](#component-library)
4. [JavaScript Modules](#javascript-modules)
5. [CSS Framework](#css-framework)
6. [API Integration](#api-integration)
7. [Responsive Design](#responsive-design)
8. [Accessibility](#accessibility)

---

## Architecture Overview

### Technology Stack

- **Template Engine**: Jinja2 (Flask)
- **CSS Framework**: Bootstrap 5.3.2 + Custom CSS
- **JavaScript**: Vanilla ES6+ (no framework)
- **Charts**: Chart.js 4.4.0
- **Icons**: Bootstrap Icons

### Design Philosophy

The frontend follows the **Vitruvian Developer** theme, emphasizing:
- **Code**: Deep Navy Blue (#1a237e)
- **AI**: Purple/Slate Blue (#6a5acd)
- **Fitness**: Warm Orange/Amber (#ffb347)
- **Meta/Philosophy**: Cyan (#06b6d4)

### File Structure

```
website/
├── templates/
│   ├── base.html                    # Base template
│   ├── dashboard.html               # Main dashboard
│   ├── components/                  # Reusable components
│   │   ├── navbar_auth.html
│   │   ├── flash_messages.html
│   │   ├── pagination.html
│   │   └── modal.html
│   ├── health/                      # Health tracking
│   │   └── metrics.html
│   ├── workout/                     # Workout tracking
│   │   ├── workouts.html
│   │   ├── workout_detail.html
│   │   ├── workout_form.html
│   │   └── exercise_library.html
│   ├── coaching/                    # Coaching interface
│   │   ├── sessions.html
│   │   ├── session_detail.html
│   │   ├── session_form.html
│   │   ├── goals.html
│   │   └── progress_photos.html
│   ├── nutrition/                   # Nutrition tracking
│   │   ├── meals.html
│   │   └── nutrition_summary.html
│   └── user/                        # User management
│       ├── profile.html
│       └── settings.html
├── static/
│   ├── css/
│   │   ├── style.css                # Base styles (existing)
│   │   └── dashboard.css            # Dashboard components
│   └── js/
│       ├── utils.js                 # Existing utilities
│       ├── common.js                # Shared utilities
│       ├── dashboard.js             # Dashboard logic
│       ├── health.js                # Health metrics
│       ├── workout.js               # Workout tracking
│       ├── coaching.js              # Coaching/goals
│       └── nutrition.js             # Nutrition tracking
```

---

## Template Hierarchy

### Base Template (`base.html`)

All templates extend `base.html`:

```jinja2
{% extends "base.html" %}

{% block title %}Page Title{% endblock %}

{% block content %}
    <!-- Page content -->
{% endblock %}

{% block scripts %}
    <!-- Additional JavaScript -->
{% endblock %}
```

**Blocks Available:**
- `title`: Page title (appears in browser tab)
- `meta_description`: SEO meta description
- `content`: Main page content
- `scripts`: Additional JavaScript files

### Common Pattern

```jinja2
{% extends "base.html" %}

{% block title %}Dashboard - Vitruvian Tracker{% endblock %}

{% block content %}
    {% include 'components/navbar_auth.html' %}

    <div class="container mt-3">
        {% include 'components/flash_messages.html' %}
    </div>

    <div class="page-container">
        <!-- Your page content -->
    </div>
{% endblock %}

{% block scripts %}
    <script src="/static/js/common.js"></script>
    <script src="/static/js/your-page.js"></script>
{% endblock %}
```

---

## Component Library

### 1. Authenticated Navbar

**File:** `components/navbar_auth.html`

**Usage:**
```jinja2
{% include 'components/navbar_auth.html' %}
```

**Features:**
- Main navigation links (Dashboard, Health, Workouts, Coaching, Nutrition)
- User dropdown menu
- Active page highlighting
- Mobile hamburger menu

**Customization:**
The navbar automatically highlights the active section using `request.endpoint`.

---

### 2. Flash Messages

**File:** `components/flash_messages.html`

**Usage:**
```jinja2
<div class="container mt-3">
    {% include 'components/flash_messages.html' %}
</div>
```

**Backend Integration:**
```python
from flask import flash

flash('Success message', 'success')
flash('Error message', 'error')
flash('Warning message', 'warning')
flash('Info message', 'info')
```

**Features:**
- Auto-dismissible alerts
- Icon based on message category
- Bootstrap 5 styled

---

### 3. Pagination

**File:** `components/pagination.html`

**Usage:**
```jinja2
{% include 'components/pagination.html' with endpoint='workout.workouts', url_params={'filter': 'all'} %}
```

**Required Variables:**
- `pagination`: Pagination object with properties:
  - `page`: Current page
  - `pages`: Total pages
  - `has_prev`: Boolean
  - `has_next`: Boolean
  - `prev_num`: Previous page number
  - `next_num`: Next page number
  - `total`: Total items
  - `per_page`: Items per page
- `endpoint`: Route endpoint name
- `url_params`: Additional URL parameters (optional)

**Features:**
- First/Last page links
- Previous/Next navigation
- Page number display (with ellipsis for many pages)
- Result count display

---

### 4. Modal Templates

**File:** `components/modal.html`

**Macros Available:**

#### Generic Modal
```jinja2
{% from 'components/modal.html' import modal %}

{% call modal('myModal', 'Modal Title', size='modal-lg') %}
    <!-- Modal body content -->
{% endcall %}
```

#### Confirmation Modal
```jinja2
{% from 'components/modal.html' import confirm_modal %}
{{ confirm_modal('confirmModal', 'Confirm Action') }}
```

#### Delete Modal
```jinja2
{% from 'components/modal.html' import delete_modal %}
{{ delete_modal('deleteModal') }}
```

**Parameters:**
- `modal_id`: Unique modal identifier
- `title`: Modal title
- `size`: Modal size (`modal-sm`, `modal-lg`, `modal-xl`)
- `centered`: Center modal vertically (default: `True`)

---

## JavaScript Modules

### Common.js - Shared Utilities

**Location:** `/static/js/common.js`

#### API Helper

```javascript
// GET request
const data = await API.get('/api/endpoint');

// POST request
const response = await API.post('/api/endpoint', { key: 'value' });

// PUT request
const response = await API.put('/api/endpoint/1', { key: 'value' });

// DELETE request
const response = await API.delete('/api/endpoint/1');
```

#### Date Utilities

```javascript
// Format date as YYYY-MM-DD
const dateStr = DateUtils.formatDate(new Date());

// Format date for display
const displayDate = DateUtils.formatDateDisplay('2024-01-15');
// Output: "Jan 15, 2024"

// Format time
const time = DateUtils.formatTime('14:30');
// Output: "2:30 PM"

// Get today's date
const today = DateUtils.getToday();

// Get date N days ago
const weekAgo = DateUtils.getDaysAgo(7);

// Calculate days between dates
const days = DateUtils.daysBetween('2024-01-01', '2024-01-15');
```

#### Form Utilities

```javascript
// Validate form
const isValid = FormUtils.validateForm(form);

// Reset validation
FormUtils.resetValidation(form);

// Get form data as object
const data = FormUtils.getFormData(form);

// Populate form with data
FormUtils.populateForm(form, { name: 'John', email: 'john@example.com' });

// Clear form
FormUtils.clearForm(form);
```

#### UI Utilities

```javascript
// Show loading spinner
UIUtils.showLoading(container);

// Show error message
UIUtils.showError(container, 'Error message');

// Show empty state
UIUtils.showEmpty(container, 'No items found');

// Show toast notification
UIUtils.showToast('Success!', 'success');
UIUtils.showToast('Error occurred', 'error');
UIUtils.showToast('Warning!', 'warning');
UIUtils.showToast('Info message', 'info');
```

#### Number Utilities

```javascript
// Format number with commas
const formatted = NumberUtils.formatNumber(1234567);
// Output: "1,234,567"

// Format to decimal places
const decimal = NumberUtils.formatDecimal(3.14159, 2);
// Output: "3.14"

// Calculate percentage
const percent = NumberUtils.calculatePercentage(75, 100);
// Output: 75
```

#### Modal Utilities

```javascript
// Show modal
ModalUtils.show('myModal');

// Hide modal
ModalUtils.hide('myModal');
```

---

### Dashboard.js

**Location:** `/static/js/dashboard.js`

**Purpose:** Main dashboard page functionality

**Key Functions:**
- `loadDashboardData()`: Load all dashboard data
- `loadLatestWeight()`: Fetch latest weight metric
- `loadRecentWorkout()`: Fetch recent workout
- `loadNextSession()`: Fetch next coaching session
- `loadNutritionStreak()`: Fetch nutrition streak
- `initializeCharts()`: Create all dashboard charts
- `createWeightTrendChart()`: Weight trend chart (7 days)
- `createWorkoutVolumeChart()`: Workout volume chart (7 days)
- `createNutritionAdherenceChart()`: Nutrition adherence chart
- `initializeQuickActions()`: Set up quick action buttons
- `initializeActivityFeed()`: Load and display activity feed

**API Endpoints Used:**
- `GET /api/health/metrics/latest`
- `GET /api/workout/recent`
- `GET /api/coaching/next-session`
- `GET /api/nutrition/streak`
- `GET /api/health/metrics/trend?days=7`
- `GET /api/workout/volume-trend?days=7`
- `GET /api/nutrition/adherence-trend?days=7`
- `GET /api/activity/recent?limit=5`

---

### Health.js

**Location:** `/static/js/health.js`

**Purpose:** Health metrics tracking page

**Expected Functionality:**
- Load metrics table with pagination
- Filter by date range and body fat availability
- Sort table columns
- Create weight and body fat charts
- Add/edit/delete metrics via modal forms
- Export data to CSV
- Calculate lean body mass

**Required API Endpoints:**
- `GET /api/health/metrics?page=1&date_range=30&bodyfat_only=false`
- `POST /api/health/metrics`
- `PUT /api/health/metrics/<id>`
- `DELETE /api/health/metrics/<id>`
- `GET /api/health/metrics/summary?date_range=30`

---

### Workout.js

**Location:** `/static/js/workout.js`

**Purpose:** Workout tracking pages

**Expected Functionality:**
- Load workouts list with filters
- Display workout cards
- Dynamic exercise entry form
- Exercise autocomplete
- Set management (add/remove sets)
- Calculate total volume
- Performance comparison

**Required API Endpoints:**
- `GET /api/workout/workouts?page=1&date_range=30&type=all`
- `GET /api/workout/workout/<id>`
- `POST /api/workout/workout`
- `PUT /api/workout/workout/<id>`
- `DELETE /api/workout/workout/<id>`
- `GET /api/workout/exercises?search=bench`
- `GET /api/workout/comparison/<workout_id>`

---

### Coaching.js

**Location:** `/static/js/coaching.js`

**Purpose:** Coaching sessions and goals tracking

**Expected Functionality:**
- Load sessions timeline
- Display session details with action items
- Manage goals (active, completed, archived)
- Goal progress tracking
- Progress photo upload and display
- Before/after photo comparison

**Required API Endpoints:**
- `GET /api/coaching/sessions?page=1&date_range=30`
- `GET /api/coaching/session/<id>`
- `POST /api/coaching/session`
- `PUT /api/coaching/session/<id>`
- `DELETE /api/coaching/session/<id>`
- `GET /api/coaching/goals?status=active`
- `POST /api/coaching/goal`
- `PUT /api/coaching/goal/<id>`
- `GET /api/coaching/progress-photos?date_range=90`
- `POST /api/coaching/progress-photo` (multipart/form-data)

---

### Nutrition.js

**Location:** `/static/js/nutrition.js`

**Purpose:** Meal tracking and nutrition summary

**Expected Functionality:**
- Date navigation
- Daily macro summary with progress bars
- Meal logging by type (breakfast, lunch, dinner, snacks)
- Macro percentage calculation
- Macro distribution pie chart
- Weekly/monthly nutrition trends
- Adherence calendar heatmap

**Required API Endpoints:**
- `GET /api/nutrition/meals?date=2024-01-15`
- `POST /api/nutrition/meal`
- `PUT /api/nutrition/meal/<id>`
- `DELETE /api/nutrition/meal/<id>`
- `GET /api/nutrition/summary?days=7`
- `GET /api/nutrition/targets`

---

## CSS Framework

### Base Styles (style.css)

Existing styles from the portfolio site, including:
- CSS variables (colors, shadows, gradients)
- Typography system
- Discipline tag system
- Navbar styling
- Project navigation bar
- Footer

### Dashboard Styles (dashboard.css)

**New styles for dashboard application:**

#### Layout Components
- `.page-container`: Main page wrapper
- `.page-header`: Page header with title and actions
- `.page-title`: Main page heading
- `.page-subtitle`: Page description

#### Dashboard Components
- `.dashboard-welcome`: Welcome banner with synergy gradient
- `.stats-grid`: Grid for stat cards
- `.stat-card`: Individual stat card
- `.chart-card`: Chart container
- `.activity-feed`: Activity timeline

#### Form Components
- `.form-container`: Form wrapper
- `.form-section`: Form section
- `.form-actions`: Form action buttons
- Form validation styles

#### Data Display
- `.data-table-card`: Table container
- `.data-table`: Styled table
- `.filters-section`: Filter controls
- `.pagination-nav`: Pagination wrapper

#### Responsive Breakpoints
- Desktop: 1400px max-width
- Tablet: 768px
- Mobile: 480px

### Using CSS Classes

#### Stat Cards

```html
<div class="stat-card stat-card-fitness">
    <div class="stat-header">
        <i class="bi bi-heart-pulse stat-icon"></i>
        <h3 class="stat-title">Latest Weight</h3>
    </div>
    <div class="stat-body">
        <div class="stat-value">175</div>
        <div class="stat-unit">lbs</div>
    </div>
    <div class="stat-footer">
        <span class="stat-change positive">-2.5 lbs</span>
        <span class="stat-date">Jan 15, 2024</span>
    </div>
</div>
```

#### Chart Cards

```html
<div class="chart-card">
    <div class="chart-header">
        <h3 class="chart-title">Weight Trend</h3>
        <a href="/health/metrics" class="chart-link">
            View All <i class="bi bi-arrow-right"></i>
        </a>
    </div>
    <div class="chart-body">
        <canvas id="weightChart"></canvas>
    </div>
</div>
```

#### Activity Feed

```html
<div class="activity-item" data-type="health">
    <div class="activity-icon activity-icon-health">
        <i class="bi bi-heart-pulse"></i>
    </div>
    <div class="activity-content">
        <div class="activity-title">Weight Logged</div>
        <div class="activity-description">175.0 lbs</div>
        <div class="activity-date">Jan 15, 2024</div>
    </div>
</div>
```

---

## API Integration

### Expected API Response Format

All API endpoints should return JSON in the following format:

#### Success Response
```json
{
    "success": true,
    "data": { ... },
    "message": "Optional success message"
}
```

#### Error Response
```json
{
    "success": false,
    "error": "Error message",
    "details": { ... }
}
```

#### Paginated Response
```json
{
    "success": true,
    "data": [ ... ],
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

### Chart.js Integration

All charts use Chart.js 4.4.0 with date-fns adapter for time scales.

**Basic Line Chart:**
```javascript
new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Jan 1', 'Jan 2', 'Jan 3'],
        datasets: [{
            label: 'Weight',
            data: [175, 174.5, 174],
            borderColor: '#1a237e',
            backgroundColor: 'rgba(26, 35, 126, 0.1)',
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: true }
        },
        scales: {
            y: { beginAtZero: false }
        }
    }
});
```

**Time Series Chart:**
```javascript
new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [{
            label: 'Weight',
            data: [
                { x: '2024-01-01', y: 175 },
                { x: '2024-01-02', y: 174.5 }
            ]
        }]
    },
    options: {
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'day',
                    displayFormats: {
                        day: 'MMM d'
                    }
                }
            }
        }
    }
});
```

---

## Responsive Design

### Breakpoints

- **Desktop**: ≥ 1400px (default)
- **Laptop**: 1024px - 1399px
- **Tablet**: 768px - 1023px
- **Mobile**: < 768px
- **Small Mobile**: < 480px

### Mobile Optimizations

1. **Navigation**: Hamburger menu on mobile
2. **Stats Grid**: Single column on mobile
3. **Charts**: Maintain aspect ratio, scrollable if needed
4. **Forms**: Full-width inputs on mobile
5. **Tables**: Horizontal scroll on mobile
6. **Modals**: Full-screen on small mobile devices

### Testing Checklist

- [ ] Test all pages on mobile (< 480px)
- [ ] Test all pages on tablet (768px - 1023px)
- [ ] Test all pages on desktop (≥ 1400px)
- [ ] Verify touch interactions work on mobile
- [ ] Ensure modals are usable on all screen sizes
- [ ] Check chart responsiveness
- [ ] Verify navigation menu works on mobile

---

## Accessibility

### ARIA Labels

All interactive elements include appropriate ARIA labels:

```html
<button class="btn btn-primary" aria-label="Add new metric">
    <i class="bi bi-plus-circle"></i> Add Metric
</button>

<div class="modal" role="dialog" aria-labelledby="modalTitle" aria-describedby="modalDesc">
    ...
</div>
```

### Keyboard Navigation

- All forms support Tab navigation
- Modal dialogs can be closed with Escape key
- Dropdowns support arrow key navigation
- Tables support keyboard sorting

### Focus Management

- Focus states visible on all interactive elements
- Focus trapped in modals when open
- Focus returned to trigger element when modal closes

### Color Contrast

All text meets WCAG AA standards:
- Primary text: #1a1a1a on white (contrast ratio 16:1)
- Secondary text: #6b7280 on white (contrast ratio 4.5:1)
- Links: #1a237e on white (contrast ratio 8.6:1)

### Screen Reader Support

- Semantic HTML elements (nav, main, article, section)
- Proper heading hierarchy (h1 → h6)
- Alt text for all images
- Labels for all form inputs
- Live regions for dynamic content

---

## Quick Start Checklist

### Adding a New Page

1. [ ] Create template in appropriate directory (`templates/module/`)
2. [ ] Extend `base.html`
3. [ ] Include `navbar_auth.html`
4. [ ] Include `flash_messages.html`
5. [ ] Add page-specific JavaScript in `static/js/`
6. [ ] Include JavaScript in `{% block scripts %}`
7. [ ] Import `common.js` for shared utilities
8. [ ] Use existing CSS classes from `dashboard.css`
9. [ ] Add responsive styles if needed
10. [ ] Test on mobile, tablet, and desktop
11. [ ] Verify accessibility (ARIA labels, keyboard navigation)

### Adding a New Form

1. [ ] Use Bootstrap form classes
2. [ ] Include validation states (`.is-invalid`, `.is-valid`)
3. [ ] Add invalid/valid feedback divs
4. [ ] Use `FormUtils.validateForm()` for validation
5. [ ] Use `FormUtils.getFormData()` to extract data
6. [ ] Handle form submission with `API.post()` or `API.put()`
7. [ ] Show success/error toast with `UIUtils.showToast()`
8. [ ] Clear form with `FormUtils.clearForm()` on success

### Adding a New Chart

1. [ ] Include Chart.js in template: `{% block scripts %}`
2. [ ] Create canvas element with unique ID
3. [ ] Fetch data from API endpoint
4. [ ] Create chart using `new Chart()`
5. [ ] Use Vitruvian color scheme:
   - Code: `#1a237e`
   - AI: `#6a5acd`
   - Fitness: `#ffb347`
   - Meta: `#06b6d4`
6. [ ] Set `responsive: true`
7. [ ] Set appropriate chart type (line, bar, pie, doughnut)

---

## Additional Resources

### Bootstrap 5 Documentation
https://getbootstrap.com/docs/5.3/

### Chart.js Documentation
https://www.chartjs.org/docs/latest/

### Bootstrap Icons
https://icons.getbootstrap.com/

### Flask Jinja2 Documentation
https://jinja.palletsprojects.com/

---

## Support

For questions or issues, consult:
1. This documentation
2. CLAUDE.md in project root
3. Existing template examples
4. Bootstrap 5 documentation
5. Chart.js documentation

---

**Last Updated:** January 2025
**Version:** 1.0
**Maintainer:** Nathan Bowman
