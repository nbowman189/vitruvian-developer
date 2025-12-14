// Analytics Service
// Tracks user engagement, reading patterns, and interaction metrics

class AnalyticsService {
    constructor() {
        this.events = [];
        this.sessionStart = Date.now();
        this.sessionId = this.generateSessionId();
        this.loadEvents();
        this.initializeTracking();
    }

    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Load events from localStorage
     */
    loadEvents() {
        const stored = localStorage.getItem('analytics_events');
        this.events = stored ? JSON.parse(stored) : [];
    }

    /**
     * Save events to localStorage
     */
    saveEvents() {
        localStorage.setItem('analytics_events', JSON.stringify(this.events));
    }

    /**
     * Track an event
     */
    trackEvent(eventType, eventData = {}) {
        const event = {
            id: this.generateSessionId(),
            type: eventType,
            timestamp: Date.now(),
            sessionId: this.sessionId,
            data: eventData,
            url: window.location.pathname
        };

        this.events.push(event);
        this.saveEvents();

        // Log for debugging
        console.log(`[Analytics] ${eventType}:`, eventData);

        return event;
    }

    /**
     * Track article view
     */
    trackArticleView(slug, title) {
        return this.trackEvent('article_view', {
            slug,
            title,
            timestamp: Date.now()
        });
    }

    /**
     * Track reading milestone (when user reaches certain completion percentage)
     */
    trackReadingMilestone(slug, percentage) {
        return this.trackEvent('reading_milestone', {
            slug,
            percentage,
            completedAt: Date.now()
        });
    }

    /**
     * Track article bookmark
     */
    trackBookmark(slug, action) {
        return this.trackEvent('bookmark_action', {
            slug,
            action, // 'saved' or 'removed'
            timestamp: Date.now()
        });
    }

    /**
     * Track collection interaction
     */
    trackCollectionAction(action, collectionName, slug = null) {
        return this.trackEvent('collection_action', {
            action, // 'created', 'deleted', 'added', 'removed'
            collectionName,
            slug,
            timestamp: Date.now()
        });
    }

    /**
     * Track article link click
     */
    trackLinkClick(slug, sourceType) {
        return this.trackEvent('link_click', {
            slug,
            sourceType, // 'recommended', 'related', 'navigation', 'search'
            timestamp: Date.now()
        });
    }

    /**
     * Track filter/search action
     */
    trackSearch(query, filterType, resultsCount) {
        return this.trackEvent('search_action', {
            query,
            filterType,
            resultsCount,
            timestamp: Date.now()
        });
    }

    /**
     * Track time spent on article
     */
    trackTimeSpent(slug, seconds) {
        return this.trackEvent('time_spent', {
            slug,
            seconds,
            timestamp: Date.now()
        });
    }

    /**
     * Initialize automatic tracking
     */
    initializeTracking() {
        // Track page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.trackEvent('session_pause', { pausedAt: Date.now() });
            } else {
                this.trackEvent('session_resume', { resumedAt: Date.now() });
            }
        });

        // Track unload
        window.addEventListener('beforeunload', () => {
            this.trackEvent('session_end', {
                duration: Date.now() - this.sessionStart,
                endedAt: Date.now()
            });
        });

        // Track clicks on article links
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href*="/blog/"]');
            if (link) {
                const href = link.getAttribute('href');
                const match = href.match(/\/blog\/([^/]+)/);
                if (match) {
                    const slug = match[1];
                    const sourceType = this.detectSourceType(e.target);
                    this.trackLinkClick(slug, sourceType);
                }
            }
        });
    }

    /**
     * Detect where a link click came from
     */
    detectSourceType(element) {
        if (element.closest('.recommendation-card')) return 'recommended';
        if (element.closest('.blog-card')) return 'related';
        if (element.closest('.article-nav')) return 'navigation';
        if (element.closest('.search-results')) return 'search';
        return 'other';
    }

    /**
     * Get all events
     */
    getEvents(filter = null) {
        if (!filter) return this.events;

        return this.events.filter(event => {
            if (filter.type && event.type !== filter.type) return false;
            if (filter.slug && event.data.slug !== filter.slug) return false;
            if (filter.startDate && event.timestamp < filter.startDate) return false;
            if (filter.endDate && event.timestamp > filter.endDate) return false;
            return true;
        });
    }

    /**
     * Get analytics summary
     */
    getAnalyticsSummary() {
        const views = this.getEvents({ type: 'article_view' });
        const bookmarks = this.getEvents({ type: 'bookmark_action' });
        const clicks = this.getEvents({ type: 'link_click' });
        const timeSpent = this.getEvents({ type: 'time_spent' });

        return {
            totalViews: views.length,
            totalBookmarks: bookmarks.filter(b => b.data.action === 'saved').length,
            totalClicks: clicks.length,
            totalTimeSpent: timeSpent.reduce((sum, t) => sum + (t.data.seconds || 0), 0),
            averageTimePerArticle: timeSpent.length > 0
                ? Math.round(timeSpent.reduce((sum, t) => sum + (t.data.seconds || 0), 0) / timeSpent.length)
                : 0,
            sessionsCount: new Set(this.events.map(e => e.sessionId)).size
        };
    }

    /**
     * Get popular articles based on views
     */
    getPopularArticles(limit = 10) {
        const views = this.getEvents({ type: 'article_view' });
        const counts = {};

        views.forEach(view => {
            const slug = view.data.slug;
            counts[slug] = (counts[slug] || 0) + 1;
        });

        return Object.entries(counts)
            .map(([slug, count]) => ({ slug, views: count }))
            .sort((a, b) => b.views - a.views)
            .slice(0, limit);
    }

    /**
     * Get reading patterns by discipline
     */
    getReadingPatternsByDiscipline(posts) {
        const views = this.getEvents({ type: 'article_view' });
        const patterns = {};

        views.forEach(view => {
            const post = posts.find(p => p.slug === view.data.slug);
            if (post && post.disciplines) {
                post.disciplines.forEach(discipline => {
                    if (!patterns[discipline]) {
                        patterns[discipline] = {
                            views: 0,
                            timeSpent: 0,
                            bookmarks: 0
                        };
                    }
                    patterns[discipline].views++;
                });
            }
        });

        // Add time spent and bookmarks
        const timeSpent = this.getEvents({ type: 'time_spent' });
        const bookmarks = this.getEvents({ type: 'bookmark_action' });

        timeSpent.forEach(t => {
            const post = posts.find(p => p.slug === t.data.slug);
            if (post && post.disciplines) {
                post.disciplines.forEach(discipline => {
                    if (patterns[discipline]) {
                        patterns[discipline].timeSpent += t.data.seconds || 0;
                    }
                });
            }
        });

        bookmarks.forEach(b => {
            if (b.data.action === 'saved') {
                const post = posts.find(p => p.slug === b.data.slug);
                if (post && post.disciplines) {
                    post.disciplines.forEach(discipline => {
                        if (patterns[discipline]) {
                            patterns[discipline].bookmarks++;
                        }
                    });
                }
            }
        });

        return patterns;
    }

    /**
     * Get click-through rate for recommendations
     */
    getRecommendationCTR() {
        const recommendedClicks = this.getEvents().filter(e =>
            e.type === 'link_click' && e.data.sourceType === 'recommended'
        ).length;

        const allClicks = this.getEvents({ type: 'link_click' }).length;

        return allClicks > 0 ? Math.round((recommendedClicks / allClicks) * 100) : 0;
    }

    /**
     * Get engagement score (0-100)
     */
    getEngagementScore(allPosts) {
        const summary = this.getAnalyticsSummary();
        const patterns = this.getReadingPatternsByDiscipline(allPosts);

        let score = 0;

        // Views component (30 points max)
        score += Math.min(30, Math.round((summary.totalViews / allPosts.length) * 30));

        // Bookmarks component (20 points max)
        score += Math.min(20, Math.round((summary.totalBookmarks / allPosts.length) * 20));

        // Time spent component (25 points max)
        const avgSessionTime = summary.totalTimeSpent > 0 ? summary.totalTimeSpent / summary.sessionsCount : 0;
        score += Math.min(25, Math.round((avgSessionTime / 3600) * 25)); // Up to 1 hour per session

        // Discipline diversity component (15 points max)
        const disciplineCount = Object.keys(patterns).length;
        score += Math.min(15, Math.round((disciplineCount / 4) * 15)); // 4 disciplines max

        // Click-through rate component (10 points max)
        const ctr = this.getRecommendationCTR();
        score += Math.round((ctr / 100) * 10);

        return Math.min(100, Math.round(score));
    }

    /**
     * Get reading streak
     */
    getReadingStreak() {
        const views = this.getEvents({ type: 'article_view' });
        if (views.length === 0) return 0;

        // Group views by date
        const dates = {};
        views.forEach(view => {
            const date = new Date(view.timestamp).toLocaleDateString();
            dates[date] = true;
        });

        // Calculate consecutive days from today backwards
        const sortedDates = Object.keys(dates).sort((a, b) => new Date(b) - new Date(a));
        let streak = 0;
        let currentDate = new Date();

        for (const date of sortedDates) {
            const viewDate = new Date(date);
            const expectedDate = new Date(currentDate);
            expectedDate.setDate(expectedDate.getDate() - streak);

            if (viewDate.toLocaleDateString() === expectedDate.toLocaleDateString()) {
                streak++;
            } else {
                break;
            }
        }

        return streak;
    }

    /**
     * Clear all analytics data
     */
    clearAnalytics() {
        this.events = [];
        localStorage.removeItem('analytics_events');
        console.log('[Analytics] Data cleared');
    }

    /**
     * Export analytics data
     */
    exportAnalytics() {
        return {
            sessionId: this.sessionId,
            sessionStart: this.sessionStart,
            events: this.events,
            summary: this.getAnalyticsSummary()
        };
    }

    /**
     * Get daily active hours
     */
    getDailyActiveHours() {
        const events = this.events;
        const hours = {};

        events.forEach(event => {
            const hour = new Date(event.timestamp).getHours();
            hours[hour] = (hours[hour] || 0) + 1;
        });

        return hours;
    }

    /**
     * Get most active day of week
     */
    getMostActiveDayOfWeek() {
        const events = this.events;
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayCount = {};

        events.forEach(event => {
            const day = days[new Date(event.timestamp).getDay()];
            dayCount[day] = (dayCount[day] || 0) + 1;
        });

        if (Object.keys(dayCount).length === 0) return null;

        return Object.entries(dayCount)
            .sort((a, b) => b[1] - a[1])[0][0];
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.AnalyticsService = AnalyticsService;
}
