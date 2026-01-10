/**
 * Dashboard Page JavaScript
 * Handles dashboard data loading, charts, and quick actions
 */

document.addEventListener('DOMContentLoaded', async function() {
    await loadDashboardData();
    initializeCharts();
    initializeBehaviorTracker();
    initializeQuickActions();
    initializeLogForms();
    initializeActivityFeed();
});

/**
 * Check if user is authenticated
 * @returns {Promise<boolean>} True if authenticated, false otherwise
 */
async function checkAuthStatus() {
    try {
        console.log('[Dashboard] Checking authentication status...');
        const response = await fetch('/auth/status', {
            method: 'GET',
            credentials: 'same-origin'
        });

        console.log('[Dashboard] Auth status response:', response.status, response.ok);

        if (!response.ok) {
            console.warn('[Dashboard] Auth check failed, response not OK');
            return false;
        }

        const data = await response.json();
        console.log('[Dashboard] Auth status data:', data);
        console.log('[Dashboard] Is authenticated:', data.authenticated);
        return data.authenticated || false;
    } catch (error) {
        console.error('[Dashboard] Error checking auth status:', error);
        return false;
    }
}

/**
 * Show login prompts for unauthenticated users
 */
function showLoginPrompts() {
    // Hide loading spinners
    document.querySelectorAll('.spinner-border').forEach(spinner => {
        spinner.style.display = 'none';
    });

    // Quick stats - show login prompt
    const quickStatsCards = [
        'latest-weight',
        'recent-workout-title',
        'next-session-title',
        'nutrition-streak-value'
    ];

    quickStatsCards.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.innerHTML = '<a href="/auth/login" class="text-primary">Log in to view</a>';
        }
    });

    // Activity feed
    const activityFeed = document.getElementById('activity-feed');
    if (activityFeed) {
        activityFeed.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-lock" style="font-size: 3rem; color: var(--text-muted);"></i>
                <p class="mt-3">Please log in to view your activity</p>
                <a href="/auth/login" class="btn btn-primary">Log In</a>
            </div>
        `;
    }

    // Behavior tracker handled by its own error handling
}

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
        const response = await API.get('/api/health/metrics/latest');
        const metric = response.data;

        // Extract weight and calculate change
        const weight = metric.weight_lbs || null;
        document.getElementById('latest-weight').textContent = weight ? weight : '--';

        // Calculate change (placeholder - could enhance with previous metric)
        document.getElementById('weight-change').textContent = '--';

        document.getElementById('weight-date').textContent = metric.recorded_date ? DateUtils.formatDateDisplay(metric.recorded_date) : '--';
    } catch (error) {
        // 404 means no data yet - this is expected for new users, don't log as error
        if (!error.message || !error.message.includes('404')) {
            console.error('Error loading latest weight:', error);
        }
        // Set placeholders (already set in HTML, but being explicit)
        document.getElementById('latest-weight').textContent = '--';
        document.getElementById('weight-change').textContent = '--';
        document.getElementById('weight-date').textContent = '--';
    }
}

/**
 * Load recent workout
 */
async function loadRecentWorkout() {
    try {
        const response = await API.get('/api/workouts/recent');
        const data = response.data;
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
        const response = await API.get('/api/coaching/next-session');
        const data = response.data;
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
        const response = await API.get('/api/nutrition/streak');
        const data = response.data;
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
        const response = await API.get('/api/health/metrics/trend?days=7');
        const data = response.data;

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
        const response = await API.get('/api/workouts/volume-trend?days=7');
        const data = response.data;

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
        const response = await API.get('/api/nutrition/adherence-trend?days=7');
        const data = response.data;

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
 * Handle quick action clicks - opens modals instead of redirecting
 * @param {string} action - Action identifier
 */
function handleQuickAction(action) {
    const today = new Date().toISOString().split('T')[0];

    switch (action) {
        case 'log-weight':
            document.getElementById('weight-date').value = today;
            document.getElementById('log-weight-form').reset();
            document.getElementById('weight-date').value = today;
            new bootstrap.Modal(document.getElementById('logWeightModal')).show();
            break;
        case 'log-workout':
            document.getElementById('workout-date').value = today;
            document.getElementById('log-workout-form').reset();
            document.getElementById('workout-date').value = today;
            new bootstrap.Modal(document.getElementById('logWorkoutModal')).show();
            break;
        case 'log-meal':
            document.getElementById('meal-date').value = today;
            document.getElementById('log-meal-form').reset();
            document.getElementById('meal-date').value = today;
            new bootstrap.Modal(document.getElementById('logMealModal')).show();
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
        const response = await API.get('/api/activity/recent?limit=5');
        const activities = Array.isArray(response.data) ? response.data : [];
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

// ====================================================================================
// Behavior Tracker Functions
// ====================================================================================

/**
 * Initialize behavior tracker section
 */
async function initializeBehaviorTracker() {
    try {
        await Promise.all([
            loadTodaysBehaviors(),
            loadBehaviorStats()
        ]);

        createBehaviorTrendChart(30); // Default 30 days
        initializeBehaviorFilters();
        initializeManageBehaviorsButton();
    } catch (error) {
        console.error('Error initializing behavior tracker:', error);
    }
}

/**
 * Load today's behavior checklist
 */
async function loadTodaysBehaviors() {
    const container = document.getElementById('behavior-checklist');

    try {
        const response = await API.get('/api/behavior/logs/today');
        const behaviors = Array.isArray(response.data) ? response.data : [];

        if (!behaviors || behaviors.length === 0) {
            container.innerHTML = `
                <div class="behavior-empty-state">
                    <i class="bi bi-inbox" style="font-size: 3rem; color: var(--text-muted);"></i>
                    <p>No behaviors configured yet.</p>
                    <button class="btn-primary" id="setup-behaviors-btn">
                        <i class="bi bi-plus-circle"></i> Set up your first behavior
                    </button>
                </div>
            `;

            // Wire up setup button
            document.getElementById('setup-behaviors-btn')?.addEventListener('click', () => {
                // TODO: Open behavior management modal or page
                alert('Behavior management UI coming soon! For now, behaviors can be created via the AI Coach.');
            });

            return;
        }

        // Render checklist
        container.innerHTML = behaviors.map(behavior => `
            <div class="behavior-item">
                <label class="behavior-checkbox">
                    <input
                        type="checkbox"
                        data-behavior-id="${behavior.behavior_id}"
                        ${behavior.completed ? 'checked' : ''}
                        onchange="toggleBehavior(${behavior.behavior_id}, this.checked)"
                    >
                    <span class="behavior-icon" style="color: ${behavior.color || '#1a237e'}">
                        <i class="bi ${behavior.icon || 'bi-check-circle'}"></i>
                    </span>
                    <span class="behavior-name">${behavior.name}</span>
                </label>
                ${behavior.target_frequency ? `
                    <span class="behavior-target">${behavior.target_frequency}x/week</span>
                ` : ''}
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading today\'s behaviors:', error);

        // Check if it's an authentication error
        if (error.message && error.message.includes('401')) {
            container.innerHTML = `
                <div class="behavior-auth-required">
                    <i class="bi bi-lock" style="font-size: 3rem; color: var(--text-muted);"></i>
                    <p>Please log in to track your behaviors</p>
                    <a href="/auth/login" class="btn-primary">Log In</a>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="behavior-error-state">
                    <i class="bi bi-exclamation-triangle" style="color: var(--danger);"></i>
                    <p>Failed to load behaviors. Please try again.</p>
                </div>
            `;
        }
    }
}

/**
 * Toggle behavior completion
 * @param {number} behaviorId - Behavior definition ID
 * @param {boolean} completed - Whether behavior was completed
 */
async function toggleBehavior(behaviorId, completed) {
    try {
        const today = new Date().toISOString().split('T')[0];

        await API.post('/api/behavior/logs', {
            behavior_definition_id: behaviorId,
            tracked_date: today,
            completed: completed
        });

        // Refresh stats after update
        await loadBehaviorStats();

        // Show toast notification
        const message = completed ? 'Behavior marked complete!' : 'Behavior unmarked';
        UIUtils.showToast(message, 'success');

    } catch (error) {
        console.error('Error toggling behavior:', error);
        UIUtils.showToast('Failed to update behavior', 'error');

        // Revert checkbox on error
        const checkbox = document.querySelector(`input[data-behavior-id="${behaviorId}"]`);
        if (checkbox) {
            checkbox.checked = !completed;
        }
    }
}

/**
 * Load behavior statistics
 */
async function loadBehaviorStats() {
    try {
        const response = await API.get('/api/behavior/stats?days=30');
        const stats = response.data;

        // Update stat cards
        document.getElementById('behavior-week-completion').textContent =
            stats.week_completion_rate ? `${Math.round(stats.week_completion_rate)}%` : '--';

        document.getElementById('behavior-best-streak').textContent =
            stats.best_streak || '0';

        document.getElementById('behavior-current-streak').textContent =
            stats.current_streak || '0';

    } catch (error) {
        console.error('Error loading behavior stats:', error);
        // Leave placeholders in place on error
    }
}

/**
 * Create behavior trend chart
 * @param {number} days - Number of days to show (30 or 90)
 */
async function createBehaviorTrendChart(days = 30) {
    const canvas = document.getElementById('behaviorTrendChart');
    if (!canvas) return;

    try {
        const response = await API.get(`/api/behavior/trends?days=${days}`);
        const data = response.data;

        if (!data.behaviors || data.behaviors.length === 0) {
            // No behaviors to chart
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = '16px Arial';
            ctx.fillStyle = '#999';
            ctx.textAlign = 'center';
            ctx.fillText('No behavior data to display', canvas.width / 2, canvas.height / 2);
            return;
        }

        // Destroy existing chart if it exists
        if (window.behaviorChart) {
            window.behaviorChart.destroy();
        }

        // Color palette for behaviors
        const CHART_COLORS = [
            '#1a237e', '#6a5acd', '#ffb347', '#06b6d4',
            '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
        ];

        // Create datasets
        const datasets = data.behaviors.map((behavior, index) => ({
            label: behavior.name,
            data: behavior.values,
            borderColor: behavior.color || CHART_COLORS[index % CHART_COLORS.length],
            backgroundColor: `${behavior.color || CHART_COLORS[index % CHART_COLORS.length]}20`,
            tension: 0.4,
            borderWidth: 2
        }));

        // Create chart
        const ctx = canvas.getContext('2d');
        window.behaviorChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 15,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                return `${label}: ${value > 0 ? '✓ Completed' : '✗ Missed'}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 50,
                            callback: function(value) {
                                return value === 100 ? '✓' : value === 0 ? '✗' : '';
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            font: {
                                size: 10
                            },
                            callback: function(value, index) {
                                // Show every 7th date label to avoid crowding
                                if (days === 90) {
                                    return index % 14 === 0 ? this.getLabelForValue(value) : '';
                                } else {
                                    return index % 7 === 0 ? this.getLabelForValue(value) : '';
                                }
                            }
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error creating behavior trend chart:', error);
    }
}

/**
 * Initialize behavior chart filter buttons
 */
function initializeBehaviorFilters() {
    const filterButtons = document.querySelectorAll('.dashboard-behaviors .chart-filters .filter-btn');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            // Update active state
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Reload chart with new period
            const period = parseInt(btn.dataset.period);
            await createBehaviorTrendChart(period);
        });
    });
}

/**
 * Initialize manage behaviors button
 */
function initializeManageBehaviorsButton() {
    const manageBtn = document.getElementById('manage-behaviors-btn');

    if (manageBtn) {
        manageBtn.addEventListener('click', () => {
            // TODO: Open behavior management modal or navigate to management page
            alert('Behavior management UI coming soon! For now, behaviors can be created and managed via the AI Coach.');
        });
    }
}

/**
 * Initialize log form handlers
 */
function initializeLogForms() {
    // Log Weight Form
    const weightForm = document.getElementById('log-weight-form');
    if (weightForm) {
        weightForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitLogForm('weight', '/api/health/metrics', weightForm, 'logWeightModal');
        });
    }

    // Log Workout Form
    const workoutForm = document.getElementById('log-workout-form');
    if (workoutForm) {
        workoutForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitLogForm('workout', '/api/workouts', workoutForm, 'logWorkoutModal');
        });
    }

    // Log Meal Form
    const mealForm = document.getElementById('log-meal-form');
    if (mealForm) {
        mealForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitLogForm('meal', '/api/nutrition/meals', mealForm, 'logMealModal');
        });
    }
}

/**
 * Submit a log form to the API
 * @param {string} type - Type of log (weight, workout, meal)
 * @param {string} endpoint - API endpoint
 * @param {HTMLFormElement} form - Form element
 * @param {string} modalId - Modal element ID
 */
async function submitLogForm(type, endpoint, form, modalId) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    try {
        // Disable button and show loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';

        // Collect form data
        const formData = new FormData(form);
        const data = {};

        for (const [key, value] of formData.entries()) {
            if (value !== '' && value !== null) {
                // Convert numeric fields
                if (['weight_lbs', 'body_fat_percentage', 'duration_minutes', 'calories', 'protein_g', 'carbs_g', 'fat_g'].includes(key)) {
                    data[key] = parseFloat(value);
                } else {
                    data[key] = value;
                }
            }
        }

        // Send to API
        const response = await API.post(endpoint, data);

        if (response.success) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
            if (modal) modal.hide();

            // Show success message
            UIUtils.showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} logged successfully!`, 'success');

            // Reset form
            form.reset();

            // Refresh relevant dashboard data
            await refreshDashboardData(type);
        } else {
            throw new Error(response.message || 'Failed to save');
        }

    } catch (error) {
        console.error(`Error logging ${type}:`, error);
        UIUtils.showToast(error.message || `Failed to log ${type}. Please try again.`, 'error');
    } finally {
        // Restore button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

/**
 * Refresh dashboard data after logging
 * @param {string} type - Type of data logged
 */
async function refreshDashboardData(type) {
    try {
        switch (type) {
            case 'weight':
                await initializeStatsCards();
                await createWeightTrendChart();
                break;
            case 'workout':
                await initializeStatsCards();
                await createWorkoutVolumeChart();
                break;
            case 'meal':
                await initializeStatsCards();
                await createNutritionAdherenceChart();
                break;
        }
        // Also refresh activity feed
        await initializeActivityFeed();
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    }
}
