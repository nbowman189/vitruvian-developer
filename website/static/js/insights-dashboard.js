// Insights Dashboard
// Displays engagement metrics and reading insights

class InsightsDashboard {
    constructor(analyticsService) {
        this.analytics = analyticsService;
        this.allPosts = [];
    }

    /**
     * Initialize with posts data
     */
    async initialize(posts) {
        this.allPosts = posts;
    }

    /**
     * Render main insights dashboard
     */
    renderDashboard(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const summary = this.analytics.getAnalyticsSummary();
        const engagementScore = this.analytics.getEngagementScore(this.allPosts);
        const readingStreak = this.analytics.getReadingStreak();
        const patterns = this.analytics.getReadingPatternsByDiscipline(this.allPosts);
        const ctr = this.analytics.getRecommendationCTR();
        const popularArticles = this.analytics.getPopularArticles(5);

        const html = `
            <div class="insights-dashboard">
                <!-- Header -->
                <div class="insights-header">
                    <h2>Your Reading Insights</h2>
                    <p class="insights-subtitle">Track your engagement and reading patterns</p>
                </div>

                <!-- Key Metrics -->
                <div class="insights-grid">
                    <div class="insight-card primary">
                        <div class="insight-icon">🎯</div>
                        <div class="insight-content">
                            <div class="insight-value">${engagementScore}</div>
                            <div class="insight-label">Engagement Score</div>
                            <div class="insight-description">Your overall platform engagement</div>
                        </div>
                    </div>

                    <div class="insight-card">
                        <div class="insight-icon">📚</div>
                        <div class="insight-content">
                            <div class="insight-value">${summary.totalViews}</div>
                            <div class="insight-label">Articles Read</div>
                            <div class="insight-description">Total articles viewed</div>
                        </div>
                    </div>

                    <div class="insight-card">
                        <div class="insight-icon">🔥</div>
                        <div class="insight-content">
                            <div class="insight-value">${readingStreak}</div>
                            <div class="insight-label">Reading Streak</div>
                            <div class="insight-description">Days in a row reading</div>
                        </div>
                    </div>

                    <div class="insight-card">
                        <div class="insight-icon">⏱️</div>
                        <div class="insight-content">
                            <div class="insight-value">${summary.averageTimePerArticle}</div>
                            <div class="insight-label">Avg. Read Time</div>
                            <div class="insight-description">Minutes per article</div>
                        </div>
                    </div>

                    <div class="insight-card">
                        <div class="insight-icon">🔖</div>
                        <div class="insight-content">
                            <div class="insight-value">${summary.totalBookmarks}</div>
                            <div class="insight-label">Articles Saved</div>
                            <div class="insight-description">In your collections</div>
                        </div>
                    </div>

                    <div class="insight-card">
                        <div class="insight-icon">✨</div>
                        <div class="insight-content">
                            <div class="insight-value">${ctr}%</div>
                            <div class="insight-label">Recommendation CTR</div>
                            <div class="insight-description">Clicks on recommendations</div>
                        </div>
                    </div>
                </div>

                <!-- Reading by Discipline -->
                <div class="insights-section">
                    <h3>Reading by Discipline</h3>
                    <div class="discipline-breakdown">
                        ${this.renderDisciplineBreakdown(patterns)}
                    </div>
                </div>

                <!-- Most Popular Articles -->
                <div class="insights-section">
                    <h3>Your Most Read Articles</h3>
                    <div class="popular-articles">
                        ${this.renderPopularArticles(popularArticles)}
                    </div>
                </div>

                <!-- Activity Timeline -->
                <div class="insights-section">
                    <h3>Activity by Hour</h3>
                    <div class="activity-timeline">
                        ${this.renderActivityTimeline()}
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    /**
     * Render discipline breakdown
     */
    renderDisciplineBreakdown(patterns) {
        if (Object.keys(patterns).length === 0) {
            return '<p class="empty-state">No reading activity yet. Start reading to see your patterns!</p>';
        }

        const disciplineNames = {
            'code': 'Code & Engineering',
            'ai': 'AI & Learning',
            'fitness': 'Fitness & Discipline',
            'meta': 'Philosophy & Meta'
        };

        const total = Object.values(patterns).reduce((sum, p) => sum + p.views, 0);
        const maxViews = Math.max(...Object.values(patterns).map(p => p.views));

        return Object.entries(patterns)
            .sort((a, b) => b[1].views - a[1].views)
            .map(([discipline, data]) => {
                const percentage = Math.round((data.views / total) * 100);
                const barWidth = (data.views / maxViews) * 100;
                const avgTime = data.views > 0 ? Math.round(data.timeSpent / data.views / 60) : 0;

                return `
                    <div class="discipline-stat-card">
                        <div class="discipline-header">
                            <span class="discipline-name">${disciplineNames[discipline] || discipline}</span>
                            <span class="discipline-percentage">${percentage}%</span>
                        </div>
                        <div class="discipline-bar-container">
                            <div class="discipline-bar" style="width: ${barWidth}%;"></div>
                        </div>
                        <div class="discipline-footer">
                            <span>${data.views} articles</span>
                            <span>${avgTime} min avg</span>
                            <span>${data.bookmarks} saved</span>
                        </div>
                    </div>
                `;
            })
            .join('');
    }

    /**
     * Render popular articles list
     */
    renderPopularArticles(articles) {
        if (articles.length === 0) {
            return '<p class="empty-state">No articles read yet.</p>';
        }

        return articles
            .map(article => {
                const post = this.allPosts.find(p => p.slug === article.slug);
                if (!post) return '';

                return `
                    <div class="popular-article-item">
                        <a href="/blog/${article.slug}" class="article-link">
                            <div class="article-info">
                                <h4>${post.title}</h4>
                                <div class="article-meta">
                                    <span class="meta-item">👁️ ${article.views} view${article.views !== 1 ? 's' : ''}</span>
                                    <span class="meta-item">📅 ${this.formatDate(post.date)}</span>
                                </div>
                            </div>
                            <span class="article-arrow">→</span>
                        </a>
                    </div>
                `;
            })
            .join('');
    }

    /**
     * Render activity timeline
     */
    renderActivityTimeline() {
        const hours = this.analytics.getDailyActiveHours();

        if (Object.keys(hours).length === 0) {
            return '<p class="empty-state">No activity data yet.</p>';
        }

        const maxActivity = Math.max(...Object.values(hours));
        const hours24 = Array.from({ length: 24 }, (_, i) => i);

        return `
            <div class="timeline-chart">
                ${hours24.map(hour => {
                    const activity = hours[hour] || 0;
                    const height = maxActivity > 0 ? (activity / maxActivity) * 100 : 0;
                    const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
                    const period = hour >= 12 ? 'PM' : 'AM';

                    return `
                        <div class="timeline-bar" title="${displayHour}${period}: ${activity} events">
                            <div class="timeline-fill" style="height: ${height}%;"></div>
                            <span class="timeline-label">${hour % 6 === 0 ? displayHour + period : ''}</span>
                        </div>
                    `;
                }).join('')}
            </div>
            <p class="timeline-note">Most active: ${this.analytics.getMostActiveDayOfWeek() || 'N/A'}</p>
        `;
    }

    /**
     * Render compact metrics widget
     */
    renderCompactMetrics(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const summary = this.analytics.getAnalyticsSummary();
        const engagementScore = this.analytics.getEngagementScore(this.allPosts);

        const html = `
            <div class="compact-metrics">
                <div class="metric-row">
                    <span class="metric-label">Engagement Score</span>
                    <span class="metric-value">${engagementScore}/100</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Articles Read</span>
                    <span class="metric-value">${summary.totalViews}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Saved Articles</span>
                    <span class="metric-value">${summary.totalBookmarks}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Avg. Read Time</span>
                    <span class="metric-value">${summary.averageTimePerArticle} min</span>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    /**
     * Render achievement badges
     */
    renderAchievements(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const summary = this.analytics.getAnalyticsSummary();
        const readingStreak = this.analytics.getReadingStreak();
        const patterns = this.analytics.getReadingPatternsByDiscipline(this.allPosts);
        const engagementScore = this.analytics.getEngagementScore(this.allPosts);

        const achievements = [];

        // Check various achievement conditions
        if (summary.totalViews >= 1) achievements.push({
            name: 'Getting Started',
            description: 'Read your first article',
            icon: '🚀',
            unlocked: true
        });

        if (summary.totalViews >= 5) achievements.push({
            name: 'Curious Reader',
            description: 'Read 5 articles',
            icon: '📚',
            unlocked: true
        });

        if (summary.totalViews >= 10) achievements.push({
            name: 'Avid Reader',
            description: 'Read 10 articles',
            icon: '🎓',
            unlocked: true
        });

        if (summary.totalViews >= 25) achievements.push({
            name: 'Knowledge Seeker',
            description: 'Read 25 articles',
            icon: '🔍',
            unlocked: true
        });

        if (summary.totalBookmarks >= 5) achievements.push({
            name: 'Collector',
            description: 'Save 5 articles',
            icon: '🔖',
            unlocked: true
        });

        if (readingStreak >= 3) achievements.push({
            name: 'Consistent Reader',
            description: '3-day reading streak',
            icon: '🔥',
            unlocked: true
        });

        if (readingStreak >= 7) achievements.push({
            name: 'Weekly Champion',
            description: '7-day reading streak',
            icon: '🏆',
            unlocked: true
        });

        if (Object.keys(patterns).length >= 3) achievements.push({
            name: 'Multidisciplinary',
            description: 'Read from 3 disciplines',
            icon: '🎯',
            unlocked: true
        });

        if (engagementScore >= 75) achievements.push({
            name: 'Engagement Master',
            description: 'Reach 75+ engagement score',
            icon: '⭐',
            unlocked: true
        });

        if (engagementScore === 100) achievements.push({
            name: 'Perfect Engagement',
            description: 'Reach 100 engagement score',
            icon: '💎',
            unlocked: true
        });

        // Add locked achievements
        const allAchievements = [
            ...achievements,
            ...[
                { name: 'Super Reader', description: 'Read 50 articles', icon: '📖', unlocked: summary.totalViews >= 50 },
                { name: 'Book Club Member', description: 'Save 25 articles', icon: '📚', unlocked: summary.totalBookmarks >= 25 },
                { name: 'Unstoppable', description: '30-day reading streak', icon: '🚀', unlocked: readingStreak >= 30 }
            ].filter(a => !achievements.some(e => e.name === a.name && e.unlocked))
        ];

        const unlockedCount = achievements.length;
        const totalCount = allAchievements.length;

        const html = `
            <div class="achievements-widget">
                <div class="achievements-header">
                    <h3>Achievements</h3>
                    <span class="achievement-progress">${unlockedCount}/${totalCount}</span>
                </div>
                <div class="achievements-grid">
                    ${allAchievements.map(achievement => `
                        <div class="achievement ${achievement.unlocked ? 'unlocked' : 'locked'}">
                            <div class="achievement-icon">${achievement.icon}</div>
                            <div class="achievement-name">${achievement.name}</div>
                            <div class="achievement-description">${achievement.description}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    formatDate(dateString) {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-US', options);
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.InsightsDashboard = InsightsDashboard;
}
