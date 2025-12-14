// Insights Page Controller
// Manages the insights dashboard and user interactions

document.addEventListener('DOMContentLoaded', function() {
    const dashboardContainer = document.getElementById('insights-dashboard');
    const metricsContainer = document.getElementById('compact-metrics');
    const achievementsContainer = document.getElementById('achievements-widget');
    const refreshBtn = document.getElementById('refresh-insights');
    const exportBtn = document.getElementById('export-insights');
    const clearBtn = document.getElementById('clear-insights');
    const lastUpdatedEl = document.getElementById('last-updated');
    const storageStatusEl = document.getElementById('storage-status');

    let analyticsService = null;
    let dashboard = null;
    let allPosts = [];

    // Initialize
    async function initialize() {
        // Create analytics service
        analyticsService = new AnalyticsService();

        // Load all posts
        try {
            const response = await fetch('/api/blog/posts');
            allPosts = await response.json();

            // Create dashboard
            dashboard = new InsightsDashboard(analyticsService);
            await dashboard.initialize(allPosts);

            // Render dashboard
            renderDashboard();
            updateStorageStatus();
            updateLastUpdated();
        } catch (error) {
            console.error('Error loading posts:', error);
            dashboardContainer.innerHTML = '<p class="error">Error loading insights data.</p>';
        }
    }

    // Render the dashboard
    function renderDashboard() {
        if (!dashboard) return;

        dashboard.renderDashboard('insights-dashboard');
        dashboard.renderCompactMetrics('compact-metrics');
        dashboard.renderAchievements('achievements-widget');
    }

    // Refresh insights data
    function refreshInsights() {
        renderDashboard();
        updateLastUpdated();
        showNotification('Insights refreshed!');
    }

    // Export analytics data
    function exportInsights() {
        if (!analyticsService) return;

        const data = analyticsService.exportAnalytics();
        const dataString = JSON.stringify(data, null, 2);
        const blob = new Blob([dataString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `reading-insights-${new Date().toISOString().split('T')[0]}.json`;
        link.click();

        showNotification('Analytics data exported!');
    }

    // Clear analytics data with confirmation
    function clearInsights() {
        const confirmed = confirm(
            'Are you sure you want to clear all analytics data? This action cannot be undone.'
        );

        if (confirmed) {
            analyticsService.clearAnalytics();
            renderDashboard();
            updateStorageStatus();
            updateLastUpdated();
            showNotification('Analytics data cleared');
        }
    }

    // Update storage status
    function updateStorageStatus() {
        if (!analyticsService) return;

        try {
            const data = JSON.stringify(analyticsService.events);
            const bytes = new Blob([data]).size;
            const kb = (bytes / 1024).toFixed(2);

            if (storageStatusEl) {
                storageStatusEl.textContent = `${analyticsService.events.length} events (${kb} KB)`;
            }
        } catch (error) {
            console.error('Error calculating storage:', error);
        }
    }

    // Update last updated timestamp
    function updateLastUpdated() {
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = new Date().toLocaleTimeString();
        }
    }

    // Show notification
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    // Event listeners
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshInsights);
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', exportInsights);
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', clearInsights);
    }

    // Initialize on page load
    initialize();

    // Auto-refresh every 5 minutes
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            refreshInsights();
        }
    }, 5 * 60 * 1000);
});
