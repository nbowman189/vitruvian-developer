/**
 * Documents Management JavaScript
 *
 * Handles document listing, filtering, and search functionality.
 */

class DocumentManager {
    constructor() {
        this.currentPage = 1;
        this.perPage = 12;
        this.currentType = 'all';
        this.searchQuery = '';
        this.documents = [];

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDocuments();
    }

    setupEventListeners() {
        // Type filter chips
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.currentType = chip.dataset.type;
                this.currentPage = 1;
                this.loadDocuments();
            });
        });

        // Search
        const searchInput = document.getElementById('search-input');
        const searchBtn = document.getElementById('search-btn');

        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.performSearch());
        }

        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
    }

    async loadDocuments() {
        const container = document.getElementById('documents-container');
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;

        try {
            let url = `/api/document/?page=${this.currentPage}&per_page=${this.perPage}`;

            if (this.currentType !== 'all') {
                url += `&document_type=${this.currentType}`;
            }

            const response = await API.get(url);

            // API returns data as array directly, pagination separately
            this.documents = response.data || [];
            this.renderDocuments({ items: response.data, total: response.pagination?.total });
            this.renderPagination({ total: response.pagination?.total });

        } catch (error) {
            console.error('Error loading documents:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle"></i> Failed to load documents
                </div>
            `;
        }
    }

    async performSearch() {
        const searchInput = document.getElementById('search-input');
        this.searchQuery = searchInput.value.trim();

        if (!this.searchQuery) {
            this.loadDocuments();
            return;
        }

        const container = document.getElementById('documents-container');
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Searching...</span>
                </div>
            </div>
        `;

        try {
            let url = `/api/document/search?q=${encodeURIComponent(this.searchQuery)}&limit=20`;

            if (this.currentType !== 'all') {
                url += `&document_type=${this.currentType}`;
            }

            const response = await API.get(url);
            const documents = response.data || [];

            this.documents = documents;
            this.renderDocuments({ items: documents, total: documents.length });
            document.getElementById('pagination-container').innerHTML = ''; // No pagination for search

        } catch (error) {
            console.error('Error searching documents:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle"></i> Search failed
                </div>
            `;
        }
    }

    renderDocuments(data) {
        const container = document.getElementById('documents-container');
        const documents = data.items || [];

        if (documents.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-file-earmark-text"></i>
                    <h4>No Documents Found</h4>
                    <p>You haven't created any documents yet. Ask the AI Coach to create a workout plan, meal plan, or progress report!</p>
                    <a href="/ai-coach" class="btn btn-primary">
                        <i class="bi bi-robot"></i> Go to AI Coach
                    </a>
                </div>
            `;
            return;
        }

        const cardsHtml = documents.map(doc => this.renderDocumentCard(doc)).join('');

        container.innerHTML = `
            <div class="row g-4">
                ${cardsHtml}
            </div>
        `;
    }

    renderDocumentCard(doc) {
        const tagsHtml = doc.tags && doc.tags.length > 0
            ? doc.tags.slice(0, 3).map(tag => `<span class="badge bg-light text-dark">${this.escapeHtml(tag)}</span>`).join('')
            : '';

        return `
            <div class="col-md-6 col-lg-4">
                <div class="card document-card h-100" onclick="window.location.href='/documents/${doc.slug}'">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="badge document-type-badge document-type-${doc.document_type}">
                                ${doc.document_type_display}
                            </span>
                            <span class="document-meta">
                                <i class="bi bi-calendar3"></i> ${DateUtils.formatDateDisplay(doc.created_at)}
                            </span>
                        </div>
                        <h5 class="card-title mb-2">${this.escapeHtml(doc.title)}</h5>
                        ${doc.summary ? `<p class="document-summary">${this.escapeHtml(doc.summary)}</p>` : ''}
                        ${tagsHtml ? `<div class="document-tags mt-2">${tagsHtml}</div>` : ''}
                    </div>
                    <div class="card-footer bg-transparent border-0">
                        <small class="text-muted">
                            <i class="bi bi-${doc.source === 'ai_coach' ? 'robot' : 'person'}"></i>
                            ${doc.source_display}
                        </small>
                    </div>
                </div>
            </div>
        `;
    }

    renderPagination(data) {
        const container = document.getElementById('pagination-container');
        const total = data.total || 0;
        const totalPages = Math.ceil(total / this.perPage);

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let paginationHtml = '<nav><ul class="pagination justify-content-center">';

        // Previous button
        paginationHtml += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="documentManager.goToPage(${this.currentPage - 1}); return false;">Previous</a>
            </li>
        `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                paginationHtml += `
                    <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="documentManager.goToPage(${i}); return false;">${i}</a>
                    </li>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                paginationHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }

        // Next button
        paginationHtml += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="documentManager.goToPage(${this.currentPage + 1}); return false;">Next</a>
            </li>
        `;

        paginationHtml += '</ul></nav>';
        container.innerHTML = paginationHtml;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadDocuments();
        window.scrollTo(0, 0);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
let documentManager;
document.addEventListener('DOMContentLoaded', () => {
    documentManager = new DocumentManager();
});
