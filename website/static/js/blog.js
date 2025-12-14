// Blog functionality for homepage and listing pages

document.addEventListener('DOMContentLoaded', function() {
    const blogPostsContainer = document.getElementById('blog-posts-container');
    const blogPostsList = document.getElementById('blog-posts-list');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const viewToggleButtons = document.querySelectorAll('.view-toggle-btn');
    const noPostsMessage = document.getElementById('no-posts');

    let allPosts = [];
    let currentFilter = 'all';
    let currentView = 'all'; // 'all' or 'saved'
    let bookmarks = {};

    // Load blog posts and bookmarks
    function loadBlogPosts() {
        fetch('/api/blog/posts')
            .then(response => response.json())
            .then(posts => {
                allPosts = posts;
                bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '{}');

                // Load latest posts on homepage
                if (blogPostsContainer) {
                    displayLatestPosts();
                }

                // Display all posts on blog listing page
                if (blogPostsList) {
                    displayAllPosts(currentView === 'saved' ? getSavedPosts() : allPosts);
                }
            })
            .catch(error => console.error('Error loading blog posts:', error));
    }

    // Get saved (bookmarked) posts
    function getSavedPosts() {
        return allPosts.filter(post => bookmarks[post.slug] === true);
    }

    function displayLatestPosts() {
        if (!blogPostsContainer || allPosts.length === 0) return;

        const latestPosts = allPosts.slice(0, 3); // Show 3 latest posts
        blogPostsContainer.innerHTML = '';

        latestPosts.forEach(post => {
            const card = createBlogCard(post);
            blogPostsContainer.appendChild(card);
        });
    }

    function displayAllPosts(posts) {
        if (!blogPostsList) return;

        blogPostsList.innerHTML = '';

        if (posts.length === 0) {
            if (noPostsMessage) {
                noPostsMessage.style.display = 'block';
            }
            return;
        }

        if (noPostsMessage) {
            noPostsMessage.style.display = 'none';
        }

        posts.forEach(post => {
            const card = createBlogCard(post);
            blogPostsList.appendChild(card);
        });
    }

    function createBlogCard(post) {
        const card = document.createElement('a');
        card.href = `/blog/${post.slug}`;
        card.className = 'blog-card';
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

    // View toggle functionality
    if (viewToggleButtons.length > 0) {
        viewToggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                currentView = this.dataset.view;

                // Update active button
                viewToggleButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                // Reload filter buttons
                currentFilter = 'all';
                filterButtons.forEach(btn => btn.classList.remove('active'));
                filterButtons[0].classList.add('active');

                // Display appropriate posts
                const postsToDisplay = currentView === 'saved' ? getSavedPosts() : allPosts;
                displayAllPosts(postsToDisplay);
            });
        });
    }

    // Filter functionality
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                currentFilter = this.dataset.filter;

                // Update active button
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                // Get base posts (all or saved)
                const basePosts = currentView === 'saved' ? getSavedPosts() : allPosts;

                // Filter and display posts
                const filteredPosts = currentFilter === 'all'
                    ? basePosts
                    : basePosts.filter(post => {
                        // Check disciplines first (exact match for discipline filters)
                        if (['code', 'ai', 'fitness', 'meta'].includes(currentFilter)) {
                            return post.disciplines && post.disciplines.includes(currentFilter);
                        }
                        // Fall back to tag matching for other filters
                        return post.tags && post.tags.some(tag =>
                            tag.toLowerCase().includes(currentFilter.toLowerCase()) ||
                            currentFilter.toLowerCase().includes(tag.toLowerCase())
                        );
                    });

                displayAllPosts(filteredPosts);
            });
        });
    }

    // Load posts on page load
    loadBlogPosts();
});
