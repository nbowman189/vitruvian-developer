// Content Recommendation Engine
// Analyzes user behavior and content similarity to recommend relevant articles

class RecommendationEngine {
    constructor() {
        this.readingHistory = JSON.parse(localStorage.getItem('readArticles') || '[]');
        this.bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '{}');
        this.allPosts = [];
        this.similarities = {};
    }

    /**
     * Initialize engine with all posts
     */
    async initialize(posts) {
        this.allPosts = posts;
        await this.calculateSimilarities();
    }

    /**
     * Calculate similarity scores between all articles
     */
    async calculateSimilarities() {
        for (let i = 0; i < this.allPosts.length; i++) {
            for (let j = i + 1; j < this.allPosts.length; j++) {
                const post1 = this.allPosts[i];
                const post2 = this.allPosts[j];
                const similarity = this.calculatePostSimilarity(post1, post2);

                const key = `${post1.slug}|${post2.slug}`;
                this.similarities[key] = similarity;
            }
        }
    }

    /**
     * Calculate similarity between two posts based on:
     * - Discipline overlap (primary factor)
     * - Tag overlap
     * - Content metadata
     */
    calculatePostSimilarity(post1, post2) {
        let score = 0;

        // Discipline similarity (0-40 points)
        const disciplines1 = post1.disciplines || [];
        const disciplines2 = post2.disciplines || [];
        const sharedDisciplines = disciplines1.filter(d => disciplines2.includes(d)).length;
        const disciplineScore = (sharedDisciplines / Math.max(disciplines1.length, disciplines2.length, 1)) * 40;
        score += disciplineScore;

        // Tag similarity (0-40 points)
        const tags1 = (post1.tags || []).map(t => t.toLowerCase());
        const tags2 = (post2.tags || []).map(t => t.toLowerCase());
        const sharedTags = tags1.filter(t => tags2.includes(t)).length;
        const tagScore = (sharedTags / Math.max(tags1.length, tags2.length, 1)) * 40;
        score += tagScore;

        // Reading time similarity (0-20 points)
        const timeDiff = Math.abs((post1.reading_time || 5) - (post2.reading_time || 5));
        const timeScore = Math.max(0, 20 - (timeDiff * 2));
        score += timeScore;

        return Math.round(score * 10) / 10;
    }

    /**
     * Get similarity between two specific posts
     */
    getSimilarity(slug1, slug2) {
        if (slug1 === slug2) return 0;
        const key = slug1 < slug2 ? `${slug1}|${slug2}` : `${slug2}|${slug1}`;
        return this.similarities[key] || 0;
    }

    /**
     * Get recommendations for a specific article
     */
    getArticleRecommendations(slug, count = 4) {
        const currentPost = this.allPosts.find(p => p.slug === slug);
        if (!currentPost) return [];

        const recommendations = this.allPosts
            .filter(post => post.slug !== slug) // Exclude current post
            .map(post => ({
                ...post,
                similarity: this.getSimilarity(slug, post.slug),
                isRead: this.readingHistory.includes(post.slug),
                isBookmarked: this.bookmarks[post.slug] === true
            }))
            .sort((a, b) => {
                // Prioritize unread articles with high similarity
                const aScore = a.similarity * (a.isRead ? 0.7 : 1);
                const bScore = b.similarity * (b.isRead ? 0.7 : 1);
                return bScore - aScore;
            })
            .slice(0, count);

        return recommendations;
    }

    /**
     * Get personalized recommendations based on reading history
     */
    getPersonalizedRecommendations(count = 6, excludeSlugs = []) {
        if (this.readingHistory.length === 0) {
            // No reading history - recommend popular/recent articles
            return this.getPopularRecommendations(count, excludeSlugs);
        }

        const readPosts = this.allPosts.filter(p => this.readingHistory.includes(p.slug));

        // Calculate recommendation score for each unread post
        const recommendations = this.allPosts
            .filter(post => !this.readingHistory.includes(post.slug) && !excludeSlugs.includes(post.slug))
            .map(post => {
                let score = 0;
                let matchCount = 0;

                // Calculate average similarity to read posts
                readPosts.forEach(readPost => {
                    const similarity = this.getSimilarity(readPost.slug, post.slug);
                    if (similarity > 10) {
                        score += similarity;
                        matchCount++;
                    }
                });

                // Bonus for matching discipline
                const readDisciplines = new Set();
                readPosts.forEach(p => {
                    (p.disciplines || []).forEach(d => readDisciplines.add(d));
                });
                const disciplineBonus = (post.disciplines || []).filter(d => readDisciplines.has(d)).length * 5;

                // Bonus for bookmarked content
                const bookmarkBonus = this.bookmarks[post.slug] ? 15 : 0;

                return {
                    ...post,
                    score: (matchCount > 0 ? score / matchCount : 0) + disciplineBonus + bookmarkBonus,
                    matchCount: matchCount
                };
            })
            .filter(rec => rec.score > 0) // Only include posts with positive scores
            .sort((a, b) => b.score - a.score)
            .slice(0, count);

        return recommendations;
    }

    /**
     * Get popular recommendations (for new users with no reading history)
     */
    getPopularRecommendations(count = 6, excludeSlugs = []) {
        return this.allPosts
            .filter(post => !excludeSlugs.includes(post.slug))
            .map(post => ({
                ...post,
                // Score based on multiple disciplines and recency
                score: (post.disciplines?.length || 1) * 10 + 50 // Bias towards multi-discipline content
            }))
            .sort((a, b) => {
                // Sort by disciplines count (multi-discipline first), then by date
                const disciplineCompare = (b.disciplines?.length || 0) - (a.disciplines?.length || 0);
                if (disciplineCompare !== 0) return disciplineCompare;
                return new Date(b.date) - new Date(a.date);
            })
            .slice(0, count);
    }

    /**
     * Get trending recommendations (based on shared discipline with bookmarks)
     */
    getTrendingRecommendations(count = 4) {
        const bookmarkedPosts = this.allPosts.filter(p => this.bookmarks[p.slug] === true);

        if (bookmarkedPosts.length === 0) {
            return this.getPopularRecommendations(count);
        }

        const bookmarkedDisciplines = new Set();
        bookmarkedPosts.forEach(post => {
            (post.disciplines || []).forEach(d => bookmarkedDisciplines.add(d));
        });

        return this.allPosts
            .filter(post => !this.bookmarks[post.slug] && !this.readingHistory.includes(post.slug))
            .map(post => ({
                ...post,
                matchingDisciplines: (post.disciplines || []).filter(d => bookmarkedDisciplines.has(d)).length
            }))
            .filter(post => post.matchingDisciplines > 0)
            .sort((a, b) => {
                const disciplineCompare = b.matchingDisciplines - a.matchingDisciplines;
                if (disciplineCompare !== 0) return disciplineCompare;
                return new Date(b.date) - new Date(a.date);
            })
            .slice(0, count);
    }

    /**
     * Get similar articles to a collection of articles
     */
    getSimilarToCollection(slugs, count = 5) {
        const basePosts = this.allPosts.filter(p => slugs.includes(p.slug));

        if (basePosts.length === 0) return [];

        const recommendations = this.allPosts
            .filter(post => !slugs.includes(post.slug))
            .map(post => {
                let totalSimilarity = 0;
                basePosts.forEach(basePost => {
                    totalSimilarity += this.getSimilarity(basePost.slug, post.slug);
                });

                return {
                    ...post,
                    avgSimilarity: totalSimilarity / basePosts.length
                };
            })
            .filter(post => post.avgSimilarity > 10)
            .sort((a, b) => b.avgSimilarity - a.avgSimilarity)
            .slice(0, count);

        return recommendations;
    }

    /**
     * Record that a user has read an article
     */
    recordRead(slug) {
        if (!this.readingHistory.includes(slug)) {
            this.readingHistory.push(slug);
            localStorage.setItem('readArticles', JSON.stringify(this.readingHistory));
        }
    }

    /**
     * Get reading statistics
     */
    getReadingStats() {
        const totalRead = this.readingHistory.length;
        const totalBookmarked = Object.values(this.bookmarks).filter(v => v === true).length;

        const disciplineStats = {};
        this.allPosts.forEach(post => {
            if (this.readingHistory.includes(post.slug)) {
                (post.disciplines || []).forEach(d => {
                    disciplineStats[d] = (disciplineStats[d] || 0) + 1;
                });
            }
        });

        return {
            totalRead,
            totalBookmarked,
            disciplineStats,
            averageReadingTime: this.calculateAverageReadingTime(),
            readingStreak: this.calculateReadingStreak()
        };
    }

    /**
     * Calculate average reading time for read articles
     */
    calculateAverageReadingTime() {
        const readPosts = this.allPosts.filter(p => this.readingHistory.includes(p.slug));
        if (readPosts.length === 0) return 0;

        const totalTime = readPosts.reduce((sum, p) => sum + (p.reading_time || 5), 0);
        return Math.round(totalTime / readPosts.length);
    }

    /**
     * Calculate reading streak (days with articles read)
     */
    calculateReadingStreak() {
        // This would require tracking dates - for now return a placeholder
        // Implementation would require storing read timestamps
        return 0;
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.RecommendationEngine = RecommendationEngine;
}
