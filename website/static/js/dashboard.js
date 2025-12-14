/**
 * Dashboard Page JavaScript
 * Handles dashboard data loading, charts, and quick actions
 */

document.addEventListener('DOMContentLoaded', async function() {
    await loadDashboardData();
    initializeCharts();
    initializeQuickActions();
    initializeActivityFeed();
});

/**
 * Load all dashboard data
 */
async function loadDashboardData() {
    try {
        // Load latest stats
        await Promise.all([
            loadLatestWeight(),
            loadRecentWorkout(),
            loadNextSession(),
            loadNutritionStreak()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        UIUtils.showToast('Error loading dashboard data', 'error');
    }
}

/**
 * Load latest weight metric
 */
async function loadLatestWeight() {
    try {
        const data = await API.get('/api/health/metrics/latest');
        document.getElementById('latest-weight').textContent = data.weight || '--';
        document.getElementById('weight-change').textContent = data.change || '--';
        document.getElementById('weight-date').textContent = data.date ? DateUtils.formatDateDisplay(data.date) : '--';
    } catch (error) {
        console.error('Error loading latest weight:', error);
    }
}

/**
 * Load recent workout
 */
async function loadRecentWorkout() {
    try {
        const data = await API.get('/api/workout/recent');
        document.getElementById('recent-workout-name').textContent = data.name || 'No recent workout';
        document.getElementById('workout-duration').textContent = data.duration ? `${data.duration} mins` : '--';
        document.getElementById('workout-date').textContent = data.date ? DateUtils.formatDateDisplay(data.date) : '--';
    } catch (error) {
        console.error('Error loading recent workout:', error);
    }
}

/**
 * Load next coaching session
 */
async function loadNextSession() {
    try {
        const data = await API.get('/api/coaching/next-session');
        document.getElementById('next-session-date').textContent = data.date ? DateUtils.formatDateDisplay(data.date) : 'Not scheduled';
        document.getElementById('session-countdown').textContent = data.countdown || '--';
        document.getElementById('active-goals-count').textContent = `${data.active_goals || 0} active goals`;
    } catch (error) {
        console.error('Error loading next session:', error);
    }
}

/**
 * Load nutrition streak
 */
async function loadNutritionStreak() {
    try {
        const data = await API.get('/api/nutrition/streak');
        document.getElementById('nutrition-streak').textContent = data.streak || '0';
        document.getElementById('calories-today').textContent = data.calories_today ? `${data.calories_today} cal` : '--';
        document.getElementById('protein-today').textContent = data.protein_today ? `${data.protein_today}g protein` : '--';
    } catch (error) {
        console.error('Error loading nutrition streak:', error);
    }
}

/**
 * Initialize dashboard charts
 */
function initializeCharts() {
    createWeightTrendChart();
    createWorkoutVolumeChart();
    createNutritionAdherenceChart();
}

/**
 * Create weight trend chart (7 days)
 */
async function createWeightTrendChart() {
    try {
        const data = await API.get('/api/health/metrics/trend?days=7');

        const ctx = document.getElementById('weightTrendChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: 'Weight (lbs)',
                    data: data.weights,
                    borderColor: '#1a237e',
                    backgroundColor: 'rgba(26, 35, 126, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating weight trend chart:', error);
    }
}

/**
 * Create workout volume chart (7 days)
 */
async function createWorkoutVolumeChart() {
    try {
        const data = await API.get('/api/workout/volume-trend?days=7');

        const ctx = document.getElementById('workoutVolumeChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.dates,
                datasets: [{
                    label: 'Volume (lbs)',
                    data: data.volumes,
                    backgroundColor: '#ffb347',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                }
            }
        });
    } catch (error) {
        console.error('Error creating workout volume chart:', error);
    }
}

/**
 * Create nutrition adherence chart (7 days)
 */
async function createNutritionAdherenceChart() {
    try {
        const data = await API.get('/api/nutrition/adherence-trend?days=7');

        const ctx = document.getElementById('nutritionAdherenceChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [
                    {
                        label: 'Calories',
                        data: data.calories,
                        borderColor: '#1a237e',
                        backgroundColor: 'rgba(26, 35, 126, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Protein',
                        data: data.protein,
                        borderColor: '#6a5acd',
                        backgroundColor: 'rgba(106, 90, 205, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });
    } catch (error) {
        console.error('Error creating nutrition adherence chart:', error);
    }
}

/**
 * Initialize quick action buttons
 */
function initializeQuickActions() {
    document.querySelectorAll('.action-card').forEach(card => {
        card.addEventListener('click', (e) => {
            e.preventDefault();
            const action = card.dataset.action;
            handleQuickAction(action);
        });
    });
}

/**
 * Handle quick action clicks
 * @param {string} action - Action identifier
 */
function handleQuickAction(action) {
    switch (action) {
        case 'log-weight':
            window.location.href = '/health/metrics';
            break;
        case 'log-workout':
            window.location.href = '/workout/new';
            break;
        case 'log-meal':
            window.location.href = '/nutrition/meals';
            break;
    }
}

/**
 * Initialize activity feed
 */
async function initializeActivityFeed() {
    const feedContainer = document.getElementById('activity-feed');
    UIUtils.showLoading(feedContainer);

    try {
        const activities = await API.get('/api/activity/recent?limit=5');
        displayActivities(activities);
        initializeActivityFilters();
    } catch (error) {
        console.error('Error loading activity feed:', error);
        UIUtils.showError(feedContainer, 'Failed to load activity feed');
    }
}

/**
 * Display activities in feed
 * @param {Array} activities - Activity items
 */
function displayActivities(activities) {
    const feedContainer = document.getElementById('activity-feed');

    if (!activities || activities.length === 0) {
        UIUtils.showEmpty(feedContainer, 'No recent activity');
        return;
    }

    feedContainer.innerHTML = activities.map(activity => `
        <div class="activity-item" data-type="${activity.type}">
            <div class="activity-icon activity-icon-${activity.type}">
                <i class="bi ${getActivityIcon(activity.type)}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${activity.title}</div>
                <div class="activity-description">${activity.description}</div>
                <div class="activity-date">${DateUtils.formatDateDisplay(activity.date)}</div>
            </div>
        </div>
    `).join('');
}

/**
 * Get icon for activity type
 * @param {string} type - Activity type
 * @returns {string} Bootstrap icon class
 */
function getActivityIcon(type) {
    const icons = {
        'health': 'bi-heart-pulse',
        'workout': 'bi-fire',
        'coaching': 'bi-chat-left-text',
        'nutrition': 'bi-egg-fried'
    };
    return icons[type] || 'bi-circle';
}

/**
 * Initialize activity filter buttons
 */
function initializeActivityFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Filter activities
            const filter = btn.dataset.filter;
            filterActivities(filter);
        });
    });
}

/**
 * Filter activities by type
 * @param {string} filter - Filter type
 */
function filterActivities(filter) {
    const activityItems = document.querySelectorAll('.activity-item');

    activityItems.forEach(item => {
        if (filter === 'all' || item.dataset.type === filter) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}
