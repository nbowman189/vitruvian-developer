// Recommendation Widget
// Displays personalized content recommendations in various locations

class RecommendationWidget {
    constructor(engine) {
        this.engine = engine;
    }

    /**
     * Display article recommendations in the blog article page
     */
    displayArticleRecommendations(slug, containerId, count = 4) {
        const recommendations = this.engine.getArticleRecommendations(slug, count);

        if (!recommendations || recommendations.length === 0) {
            return;
        }

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';
        container.className = 'recommendations-grid';

        recommendations.forEach(post => {
            const card = this.createRecommendationCard(post, 'similar');
            container.appendChild(card);
        });
    }

    /**
     * Display personalized recommendations (homepage, dashboard, etc.)
     */
    displayPersonalizedRecommendations(containerId, count = 6, excludeSlugs = []) {
        const recommendations = this.engine.getPersonalizedRecommendations(count, excludeSlugs);

        if (!recommendations || recommendations.length === 0) {
            return;
        }

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';
        container.className = 'recommendations-grid';

        recommendations.forEach(post => {
            const card = this.createRecommendationCard(post, 'personalized');
            container.appendChild(card);
        });
    }

    /**
     * Display trending recommendations based on bookmarks
     */
    displayTrendingRecommendations(containerId, count = 4) {
        const recommendations = this.engine.getTrendingRecommendations(count);

        if (!recommendations || recommendations.length === 0) {
            return;
        }

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';
        container.className = 'recommendations-grid';

        recommendations.forEach(post => {
            const card = this.createRecommendationCard(post, 'trending');
            container.appendChild(card);
        });
    }

    /**
     * Create a recommendation card element
     */
    createRecommendationCard(post, type = 'similar') {
        const card = document.createElement('div');
        card.className = 'recommendation-card';
        card.setAttribute('data-slug', post.slug);

        // Determine badge type and content
        let badge = '';
        if (type === 'similar') {
            const similarity = Math.round(post.similarity);
            badge = `<div class="recommendation-badge similarity-badge">${similarity}% Match</div>`;
        } else if (type === 'trending') {
            badge = `<div class="recommendation-badge trending-badge">🔥 Trending</div>`;
        } else if (type === 'personalized') {
            badge = `<div class="recommendation-badge personalized-badge">⭐ For You</div>`;
        }

        // Build disciplines display
        let disciplinesHtml = '';
        if (post.disciplines && post.disciplines.length > 0) {
            disciplinesHtml = post.disciplines
                .map(d => `<span class="rec-discipline-tag tag-${d}">${this.getDisciplineName(d)}</span>`)
                .join('');
        }

        card.innerHTML = `
            <div class="recommendation-card-inner">
                ${badge}
                <div class="recommendation-content">
                    <div class="recommendation-disciplines">
                        ${disciplinesHtml}
                    </div>
                    <h4 class="recommendation-title">${post.title}</h4>
                    <p class="recommendation-excerpt">${post.excerpt || ''}</p>
                    <div class="recommendation-meta">
                        <span class="recommendation-date">${this.formatDate(post.date)}</span>
                        <span class="recommendation-reading-time">${post.reading_time} min</span>
                    </div>
                </div>
                <div class="recommendation-actions">
                    <a href="/blog/${post.slug}" class="recommendation-link">Read Article</a>
                </div>
            </div>
        `;

        // Add click handler
        card.addEventListener('click', () => {
            window.location.href = `/blog/${post.slug}`;
        });

        return card;
    }

    /**
     * Display reading statistics widget
     */
    displayReadingStats(containerId) {
        const stats = this.engine.getReadingStats();
        const container = document.getElementById(containerId);

        if (!container) return;

        const statsHtml = `
            <div class="reading-stats-widget">
                <div class="stats-header">
                    <h3>Your Reading Journey</h3>
                </div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${stats.totalRead}</div>
                        <div class="stat-label">Articles Read</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.totalBookmarked}</div>
                        <div class="stat-label">Articles Saved</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.averageReadingTime}</div>
                        <div class="stat-label">Avg. Read Time (min)</div>
                    </div>
                </div>
                ${this.buildDisciplineStats(stats.disciplineStats)}
            </div>
        `;

        container.innerHTML = statsHtml;
    }

    /**
     * Build discipline statistics display
     */
    buildDisciplineStats(stats) {
        if (Object.keys(stats).length === 0) {
            return '';
        }

        const disciplineHtml = Object.entries(stats)
            .map(([discipline, count]) => `
                <div class="discipline-stat">
                    <span class="discipline-name">${this.getDisciplineName(discipline)}</span>
                    <div class="discipline-bar">
                        <div class="discipline-bar-fill" style="width: ${(count / Object.values(stats).reduce((a, b) => Math.max(a, b)) * 100)}%"></div>
                    </div>
                    <span class="discipline-count">${count}</span>
                </div>
            `)
            .join('');

        return `
            <div class="stats-disciplines">
                <h4>Reading by Discipline</h4>
                ${disciplineHtml}
            </div>
        `;
    }

    /**
     * Display related articles in saved articles page
     */
    displayCollectionRecommendations(slugs, containerId, count = 5) {
        const recommendations = this.engine.getSimilarToCollection(slugs, count);

        if (!recommendations || recommendations.length === 0) {
            return;
        }

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';
        container.className = 'recommendations-list';

        recommendations.forEach(post => {
            const item = document.createElement('div');
            item.className = 'recommendation-list-item';

            item.innerHTML = `
                <a href="/blog/${post.slug}" class="recommendation-list-link">
                    <div class="recommendation-list-content">
                        <h5>${post.title}</h5>
                        <div class="recommendation-list-meta">
                            <span>${post.reading_time} min read</span>
                            <span>${this.formatDate(post.date)}</span>
                        </div>
                    </div>
                    <span class="recommendation-list-arrow">→</span>
                </a>
            `;

            container.appendChild(item);
        });
    }

    getDisciplineName(discipline) {
        const names = {
            'code': 'Code',
            'ai': 'AI',
            'fitness': 'Fitness',
            'meta': 'Meta'
        };
        return names[discipline] || discipline;
    }

    formatDate(dateString) {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-US', options);
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.RecommendationWidget = RecommendationWidget;
}
