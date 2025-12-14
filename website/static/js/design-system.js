/**
 * Design System & Discipline Management
 * Handles "The Vitruvian Developer" theme with discipline-based styling
 */

const DesignSystem = {
    // Color mappings for each discipline
    colors: {
        code: {
            primary: '#1a237e',
            light: 'rgba(26, 35, 126, 0.1)',
            border: 'rgba(26, 35, 126, 0.2)',
            tag: 'tag-code'
        },
        ai: {
            primary: '#7c3aed',
            light: 'rgba(124, 58, 237, 0.1)',
            border: 'rgba(124, 58, 237, 0.2)',
            tag: 'tag-ai'
        },
        fitness: {
            primary: '#ff8a3d',
            light: 'rgba(255, 138, 61, 0.1)',
            border: 'rgba(255, 138, 61, 0.2)',
            tag: 'tag-fitness'
        },
        meta: {
            primary: '#06b6d4',
            light: 'rgba(6, 182, 212, 0.1)',
            border: 'rgba(6, 182, 212, 0.2)',
            tag: 'tag-meta'
        }
    },

    // Discipline definitions
    disciplines: {
        code: {
            name: 'Code',
            color: '#1a237e',
            description: 'Software Engineering & Architecture'
        },
        ai: {
            name: 'AI',
            color: '#7c3aed',
            description: 'Artificial Intelligence & Machine Learning'
        },
        fitness: {
            name: 'Fitness',
            color: '#ff8a3d',
            description: 'Physical Health & Discipline'
        },
        meta: {
            name: 'Meta',
            color: '#06b6d4',
            description: 'Philosophy & Personal Development'
        }
    },

    /**
     * Get tag class name for a discipline
     */
    getTagClass(discipline) {
        const tag = this.colors[discipline]?.tag;
        return tag ? `tag ${tag}` : 'tag';
    },

    /**
     * Get card accent class for a discipline
     */
    getCardAccentClass(discipline) {
        return `card-accent-${discipline}`;
    },

    /**
     * Get highlight class for inline discipline references
     */
    getHighlightClass(discipline) {
        return `highlight-${discipline}`;
    },

    /**
     * Create a discipline tag element
     */
    createDisciplineTag(discipline) {
        const tagClass = this.getTagClass(discipline);
        const name = this.disciplines[discipline]?.name || discipline;
        const tag = document.createElement('span');
        tag.className = tagClass;
        tag.textContent = name;
        return tag;
    },

    /**
     * Create multiple discipline tags
     */
    createDisciplineTags(disciplines) {
        return disciplines.map(d => this.createDisciplineTag(d));
    },

    /**
     * Apply discipline styling to an element
     */
    applyDisciplineStyle(element, discipline) {
        const color = this.colors[discipline]?.primary;
        if (color) {
            element.style.borderLeftColor = color;
        }
    },

    /**
     * Get synergy badge HTML for bridging disciplines
     */
    getSynergyBadge(disciplines = ['code', 'fitness', 'ai']) {
        const badge = document.createElement('div');
        badge.className = 'synergy-badge';
        badge.innerHTML = '🔗 Synergy: ' + disciplines
            .map(d => this.disciplines[d]?.name || d)
            .join(' + ');
        return badge;
    },

    /**
     * Categorize content by disciplines
     */
    categorizeByDiscipline(items, disciplinesField = 'disciplines') {
        const categorized = {};
        Object.keys(this.disciplines).forEach(d => {
            categorized[d] = [];
        });
        categorized['synergy'] = []; // Multi-discipline

        items.forEach(item => {
            const disciplines = item[disciplinesField] || [];
            if (disciplines.length > 1) {
                categorized['synergy'].push(item);
            } else if (disciplines.length === 1) {
                categorized[disciplines[0]].push(item);
            }
        });

        return categorized;
    },

    /**
     * Get color for a discipline
     */
    getColor(discipline) {
        return this.colors[discipline]?.primary || '#1a1a1a';
    },

    /**
     * Create gradient string for multiple disciplines
     */
    createSynergyGradient(disciplines = ['code', 'ai', 'fitness']) {
        const colors = disciplines.map(d => this.getColor(d)).join(', ');
        return `linear-gradient(90deg, ${colors})`;
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DesignSystem;
}
