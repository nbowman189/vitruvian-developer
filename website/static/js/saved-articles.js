// Saved Articles functionality

document.addEventListener('DOMContentLoaded', function() {
    const blogPostsList = document.getElementById('blog-posts-list');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const noPostsMessage = document.getElementById('no-posts');
    const articlesView = document.getElementById('articles-view');
    const collectionsView = document.getElementById('collections-view');
    const collectionsGrid = document.getElementById('collections-grid');
    const viewToggles = document.querySelectorAll('.view-toggle');
    const sortSelect = document.getElementById('sort-select');
    const newCollectionInput = document.getElementById('new-collection-name');
    const createCollectionBtn = document.getElementById('create-collection-btn');

    let allPosts = [];
    let currentFilter = 'all';
    let currentView = 'grid';
    let currentSort = 'recent';
    let collections = {};

    // Initialize collections from localStorage
    function initializeCollections() {
        const saved = localStorage.getItem('collections');
        collections = saved ? JSON.parse(saved) : {};
    }

    // Save collections to localStorage
    function saveCollections() {
        localStorage.setItem('collections', JSON.stringify(collections));
    }

    // Load all blog posts and bookmarks
    function loadBookmarkedArticles() {
        Promise.all([
            fetch('/api/blog/posts?per_page=50').then(r => r.json()),
            Promise.resolve(JSON.parse(localStorage.getItem('bookmarks') || '{}'))
        ]).then(([data, bookmarks]) => {
            // Handle paginated response - extract items array
            const posts = data.items || data || [];
            // Filter to only bookmarked posts
            allPosts = posts.filter(post => bookmarks[post.slug] === true);

            // Add saved timestamp to posts if they don't have one
            allPosts.forEach(post => {
                const timestamp = localStorage.getItem(`bookmark-date-${post.slug}`);
                post.savedAt = timestamp ? parseInt(timestamp) : Date.now();
            });

            displayArticles(allPosts);
        }).catch(error => console.error('Error loading bookmarked articles:', error));
    }

    // Display articles based on current filter and sort
    function displayArticles(posts) {
        // Apply filter
        let filteredPosts = posts;
        if (currentFilter !== 'all') {
            filteredPosts = posts.filter(post => {
                return post.disciplines && post.disciplines.includes(currentFilter);
            });
        }

        // Apply sort
        const sortedPosts = sortArticles(filteredPosts);

        if (blogPostsList) {
            blogPostsList.innerHTML = '';

            if (sortedPosts.length === 0) {
                if (noPostsMessage) {
                    noPostsMessage.style.display = 'block';
                }
                return;
            }

            if (noPostsMessage) {
                noPostsMessage.style.display = 'none';
            }

            blogPostsList.className = `blog-posts view-${currentView}`;
            sortedPosts.forEach(post => {
                const card = createBlogCard(post);
                blogPostsList.appendChild(card);
            });
        }
    }

    // Sort articles based on current sort option
    function sortArticles(posts) {
        const sorted = [...posts];

        switch (currentSort) {
            case 'recent':
                sorted.sort((a, b) => (b.savedAt || 0) - (a.savedAt || 0));
                break;
            case 'date':
                sorted.sort((a, b) => new Date(b.date) - new Date(a.date));
                break;
            case 'title':
                sorted.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
                break;
            case 'reading-time':
                sorted.sort((a, b) => (a.reading_time || 0) - (b.reading_time || 0));
                break;
            default:
                break;
        }

        return sorted;
    }

    function createBlogCard(post) {
        const card = document.createElement('a');
        card.href = `/blog/${post.slug}`;
        card.className = 'blog-card';
        card.dataset.slug = post.slug;
        card.dataset.tags = (post.tags || []).join(',');
        card.dataset.disciplines = (post.disciplines || []).join(',');

        // Apply discipline accent to card
        if (post.disciplines && post.disciplines.length > 0) {
            const primaryDiscipline = post.disciplines[0];
            card.classList.add(`card-accent-${primaryDiscipline}`);
        }

        const header = document.createElement('div');
        header.className = 'blog-card-header';

        // Add discipline badges if available
        if (post.disciplines && post.disciplines.length > 0) {
            const disciplineContainer = document.createElement('div');
            disciplineContainer.className = 'blog-card-disciplines';

            post.disciplines.forEach(discipline => {
                const badge = document.createElement('span');
                badge.className = `tag tag-${discipline}`;
                badge.textContent = getDisciplineName(discipline);
                disciplineContainer.appendChild(badge);
            });

            header.appendChild(disciplineContainer);
        }

        // Add synergy badge for multi-discipline posts
        if (post.disciplines && post.disciplines.length > 1) {
            const synergyBadge = document.createElement('div');
            synergyBadge.className = 'blog-card-synergy';
            synergyBadge.textContent = '🔗 Synergy';
            header.appendChild(synergyBadge);
        }

        const title = document.createElement('h3');
        title.className = 'blog-card-title';
        title.textContent = post.title;
        header.appendChild(title);

        const body = document.createElement('div');
        body.className = 'blog-card-body';

        const meta = document.createElement('div');
        meta.className = 'blog-card-meta';

        const dateSpan = document.createElement('span');
        dateSpan.className = 'blog-card-date';
        dateSpan.textContent = formatDate(post.date);
        meta.appendChild(dateSpan);

        const readingTime = document.createElement('span');
        readingTime.className = 'blog-card-reading-time';
        readingTime.textContent = `${post.reading_time} min read`;
        meta.appendChild(readingTime);

        body.appendChild(meta);

        const excerpt = document.createElement('p');
        excerpt.className = 'blog-card-excerpt';
        excerpt.textContent = post.excerpt;
        body.appendChild(excerpt);

        if (post.tags && post.tags.length > 0) {
            const tagsDiv = document.createElement('div');
            tagsDiv.className = 'blog-card-tags';

            post.tags.forEach(tag => {
                const tagSpan = document.createElement('span');
                tagSpan.className = 'blog-card-tag';
                tagSpan.textContent = tag;
                tagsDiv.appendChild(tagSpan);
            });

            body.appendChild(tagsDiv);
        }

        // Add card actions (remove bookmark, add to collection)
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'blog-card-actions';

        const removeBtn = document.createElement('button');
        removeBtn.className = 'card-action-btn remove-bookmark-btn';
        removeBtn.title = 'Remove from saved';
        removeBtn.innerHTML = '✕ Remove';
        removeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            removeBookmark(post.slug);
        });
        actionsDiv.appendChild(removeBtn);

        const addToCollectionBtn = document.createElement('button');
        addToCollectionBtn.className = 'card-action-btn add-to-collection-btn';
        addToCollectionBtn.title = 'Add to collection';
        addToCollectionBtn.innerHTML = '+ Collection';
        addToCollectionBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showCollectionSelector(post.slug, post.title);
        });
        actionsDiv.appendChild(addToCollectionBtn);

        body.appendChild(actionsDiv);

        card.appendChild(header);
        card.appendChild(body);

        return card;
    }

    function getDisciplineName(discipline) {
        const names = {
            'code': 'Code',
            'ai': 'AI',
            'fitness': 'Fitness',
            'meta': 'Meta'
        };
        return names[discipline] || discipline;
    }

    function formatDate(dateString) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-US', options);
    }

    function removeBookmark(slug) {
        const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '{}');
        delete bookmarks[slug];
        localStorage.setItem('bookmarks', JSON.stringify(bookmarks));

        // Remove from collections as well
        Object.keys(collections).forEach(collectionName => {
            collections[collectionName] = collections[collectionName].filter(s => s !== slug);
            if (collections[collectionName].length === 0) {
                delete collections[collectionName];
            }
        });
        saveCollections();

        // Reload articles
        allPosts = allPosts.filter(p => p.slug !== slug);
        displayArticles(allPosts);

        showNotification('Article removed from saved');
    }

    // Collection Management Functions
    function showCollectionSelector(slug, title) {
        const collectionNames = Object.keys(collections);
        let html = `<div class="collection-selector-modal">
            <div class="modal-content">
                <h3>Add to Collection</h3>
                <p class="modal-subtitle">${title}</p>
                <div class="collection-list">`;

        collectionNames.forEach(name => {
            const isInCollection = collections[name].includes(slug);
            html += `<label class="collection-checkbox">
                <input type="checkbox" value="${name}" ${isInCollection ? 'checked' : ''}>
                <span>${name} (${collections[name].length})</span>
            </label>`;
        });

        html += `</div>
                <div class="modal-actions">
                    <button class="btn-primary" id="confirm-collections">Add</button>
                    <button class="btn-secondary" id="cancel-modal">Cancel</button>
                </div>
            </div>
        </div>`;

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = html;
        document.body.appendChild(modal);

        // Handle confirm
        modal.querySelector('#confirm-collections').addEventListener('click', function() {
            const checkboxes = modal.querySelectorAll('.collection-checkbox input');
            const selectedCollections = [];

            checkboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    selectedCollections.push(checkbox.value);
                }
            });

            // Update collections
            collectionNames.forEach(name => {
                if (selectedCollections.includes(name)) {
                    if (!collections[name].includes(slug)) {
                        collections[name].push(slug);
                    }
                } else {
                    collections[name] = collections[name].filter(s => s !== slug);
                }
            });

            saveCollections();
            modal.remove();
            showNotification('Article added to collections');
        });

        // Handle cancel
        modal.querySelector('#cancel-modal').addEventListener('click', function() {
            modal.remove();
        });

        // Close on backdrop click
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    // Create new collection
    function createCollection(name) {
        if (!name || name.trim() === '') {
            showNotification('Please enter a collection name', 'error');
            return;
        }

        if (collections[name]) {
            showNotification('Collection already exists', 'error');
            return;
        }

        collections[name] = [];
        saveCollections();
        loadCollections();
        newCollectionInput.value = '';
        showNotification(`Collection "${name}" created`);
    }

    // Display collections
    function loadCollections() {
        if (!collectionsGrid) return;

        collectionsGrid.innerHTML = '';
        const collectionNames = Object.keys(collections);

        if (collectionNames.length === 0) {
            collectionsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 2rem;">No collections yet. Create one to organize your saved articles.</p>';
            return;
        }

        collectionNames.forEach(name => {
            const count = collections[name].length;
            const collectionCard = document.createElement('div');
            collectionCard.className = 'collection-card';

            collectionCard.innerHTML = `
                <div class="collection-card-header">
                    <h3>${name}</h3>
                    <button class="delete-collection-btn" title="Delete collection">✕</button>
                </div>
                <div class="collection-card-content">
                    <p class="collection-count">${count} article${count !== 1 ? 's' : ''}</p>
                    <button class="view-collection-btn" data-collection="${name}">View Collection</button>
                </div>
            `;

            // Delete collection handler
            collectionCard.querySelector('.delete-collection-btn').addEventListener('click', function(e) {
                e.stopPropagation();
                if (confirm(`Delete collection "${name}"?`)) {
                    delete collections[name];
                    saveCollections();
                    loadCollections();
                    showNotification(`Collection "${name}" deleted`);
                }
            });

            // View collection handler
            collectionCard.querySelector('.view-collection-btn').addEventListener('click', function(e) {
                e.stopPropagation();
                viewCollection(name);
            });

            collectionsGrid.appendChild(collectionCard);
        });
    }

    // View a specific collection
    function viewCollection(name) {
        const slugs = collections[name] || [];
        const collectionPosts = allPosts.filter(post => slugs.includes(post.slug));

        // Switch to articles view
        currentFilter = 'all';
        filterButtons.forEach(btn => btn.classList.remove('active'));
        filterButtons[0].classList.add('active');
        collectionsView.style.display = 'none';
        articlesView.style.display = 'block';

        // Display collection articles
        blogPostsList.innerHTML = '';
        const title = document.querySelector('.blog-header h1');
        title.textContent = `${name}`;

        displayArticles(collectionPosts);
    }

    // Filter functionality
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const filterValue = this.dataset.filter;

                // Update active button
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                if (filterValue === 'collections') {
                    articlesView.style.display = 'none';
                    collectionsView.style.display = 'block';
                    loadCollections();
                    document.querySelector('.blog-header h1').textContent = 'Collections';
                } else {
                    articlesView.style.display = 'block';
                    collectionsView.style.display = 'none';
                    currentFilter = filterValue;
                    document.querySelector('.blog-header h1').textContent = 'Saved Articles';
                    displayArticles(allPosts);
                }
            });
        });
    }

    // View toggle functionality
    if (viewToggles.length > 0) {
        viewToggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                viewToggles.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                currentView = this.dataset.view;
                displayArticles(allPosts);
            });
        });
    }

    // Sort functionality
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            currentSort = this.value;
            displayArticles(allPosts);
        });
    }

    // Collection creation
    if (createCollectionBtn) {
        createCollectionBtn.addEventListener('click', function() {
            const name = newCollectionInput.value;
            createCollection(name);
        });

        newCollectionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                createCollection(this.value);
            }
        });
    }

    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
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

    // Initialize
    initializeCollections();
    loadBookmarkedArticles();
});
