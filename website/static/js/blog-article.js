// Blog article page functionality

document.addEventListener('DOMContentLoaded', function() {
    const slug = window.location.pathname.split('/blog/')[1];

    const articleTitle = document.getElementById('article-title');
    const articleDate = document.getElementById('article-date');
    const articleAuthor = document.getElementById('article-author');
    const articleReadingTime = document.getElementById('article-reading-time');
    const articleTagsContainer = document.getElementById('article-tags-container');
    const articleBody = document.getElementById('article-body');
    const relatedPostsContainer = document.getElementById('related-posts');
    const prevArticle = document.getElementById('prev-article');
    const nextArticle = document.getElementById('next-article');
    const readingProgress = document.getElementById('reading-progress');
    const articleProgress = document.getElementById('article-progress');
    const bookmarkBtn = document.getElementById('bookmark-btn');
    const recommendationsSection = document.getElementById('recommendations-section');
    const personalisedRecommendationsContainer = document.getElementById('personalized-recommendations');
    const breadcrumbArticle = document.getElementById('breadcrumb-article');

    let allPosts = [];
    let isBookmarked = false;
    let recommendationEngine = null;
    let recommendationWidget = null;

    // Load all posts first (for navigation and related articles)
    function loadAllPosts() {
        fetch('/api/blog/posts?per_page=50')
            .then(response => response.json())
            .then(data => {
                // Handle paginated response - extract items array
                allPosts = data.items || data || [];
                loadArticle();
            })
            .catch(error => {
                console.error('Error loading posts:', error);
                articleBody.innerHTML = '<p>Error loading article.</p>';
            });
    }

    function loadArticle() {
        fetch(`/api/blog/post/${slug}`)
            .then(response => {
                if (!response.ok) throw new Error('Article not found');
                return response.json();
            })
            .then(post => {
                displayArticle(post);
                displayRelatedArticles(post);
                displayArticleNavigation(post);
                initializeRecommendations(post);
            })
            .catch(error => {
                articleBody.innerHTML = `<p>Error loading article: ${error.message}</p>`;
            });
    }

    // Initialize recommendation engine
    function initializeRecommendations(currentPost) {
        if (!recommendationEngine) {
            recommendationEngine = new RecommendationEngine();
            recommendationWidget = new RecommendationWidget(recommendationEngine);
        }

        // Initialize with all posts
        recommendationEngine.initialize(allPosts).then(() => {
            // Display personalized recommendations if user has reading history
            const readingHistory = JSON.parse(localStorage.getItem('readArticles') || '[]');
            if (readingHistory.length > 0) {
                recommendationWidget.displayPersonalizedRecommendations(
                    'personalized-recommendations',
                    4,
                    [slug]
                );
                if (recommendationsSection) {
                    recommendationsSection.style.display = 'block';
                }
            }
        });
    }

    function displayArticle(post) {
        // Set title
        if (articleTitle) {
            articleTitle.textContent = post.metadata.title;
            document.title = `${post.metadata.title} - Blog`;
        }

        // Update breadcrumb
        updateBreadcrumb(post.metadata.title);

        // Set metadata
        if (articleDate) {
            articleDate.textContent = formatDate(post.metadata.date);
        }

        if (articleAuthor) {
            articleAuthor.textContent = post.metadata.author || 'Nathan Bowman';
        }

        if (articleReadingTime) {
            articleReadingTime.textContent = `${post.metadata.reading_time || 5} min read`;
        }

        // Display tags
        if (articleTagsContainer && post.metadata.tags) {
            articleTagsContainer.innerHTML = '';
            post.metadata.tags.forEach(tag => {
                const tagElement = document.createElement('span');
                tagElement.className = 'article-tag';
                tagElement.textContent = tag;
                articleTagsContainer.appendChild(tagElement);
            });
        }

        // Display content
        if (articleBody) {
            articleBody.innerHTML = post.content;
        }

        // Load connection map and related projects
        loadConnectionMap(post.slug);
        loadRelatedProjects(post.slug);
    }

    // Update breadcrumb with article title
    function updateBreadcrumb(title) {
        if (breadcrumbArticle) {
            breadcrumbArticle.textContent = title;
            breadcrumbArticle.setAttribute('aria-current', 'page');
        }
    }

    function displayRelatedArticles(currentPost) {
        if (!relatedPostsContainer) return;

        // Find posts with similar tags (excluding current post)
        const relatedPosts = allPosts
            .filter(post => post.slug !== currentPost.slug)
            .filter(post => {
                if (!post.tags || !currentPost.metadata.tags) return false;
                return post.tags.some(tag => currentPost.metadata.tags.includes(tag));
            })
            .slice(0, 3); // Show up to 3 related posts

        relatedPostsContainer.innerHTML = '';

        if (relatedPosts.length === 0) {
            // If no related posts by tags, show latest posts
            const latestPosts = allPosts
                .filter(post => post.slug !== currentPost.slug)
                .slice(0, 3);

            latestPosts.forEach(post => {
                const card = createBlogCard(post);
                relatedPostsContainer.appendChild(card);
            });
        } else {
            relatedPosts.forEach(post => {
                const card = createBlogCard(post);
                relatedPostsContainer.appendChild(card);
            });
        }
    }

    function displayArticleNavigation(currentPost) {
        const currentIndex = allPosts.findIndex(post => post.slug === currentPost.slug);

        // Previous article
        if (currentIndex < allPosts.length - 1) {
            const prevPost = allPosts[currentIndex + 1];
            prevArticle.style.display = 'flex';
            prevArticle.href = `/blog/${prevPost.slug}`;
            document.getElementById('prev-title').textContent = prevPost.title;
        }

        // Next article
        if (currentIndex > 0) {
            const nextPost = allPosts[currentIndex - 1];
            nextArticle.style.display = 'flex';
            nextArticle.href = `/blog/${nextPost.slug}`;
            document.getElementById('next-title').textContent = nextPost.title;
        }
    }

    function createBlogCard(post) {
        const card = document.createElement('a');
        card.href = `/blog/${post.slug}`;
        card.className = 'blog-card';

        const header = document.createElement('div');
        header.className = 'blog-card-header';

        // Add first tag as category
        if (post.tags && post.tags.length > 0) {
            const category = document.createElement('div');
            category.className = 'blog-card-category';
            category.textContent = post.tags[0];
            header.appendChild(category);
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

        card.appendChild(header);
        card.appendChild(body);

        return card;
    }

    function getDisciplineNamePortfolio(discipline) {
        const names = {
            'code': 'Code',
            'ai': 'AI',
            'fitness': 'Fitness',
            'meta': 'Meta'
        };
        return names[discipline] || discipline;
    }

    function loadConnectionMap(slug) {
        const connectionMapSection = document.getElementById('connection-map-section');
        const connectionDisciplines = document.getElementById('connection-disciplines');
        const connectionPosts = document.getElementById('connection-posts');

        if (!connectionMapSection || !connectionDisciplines || !connectionPosts) return;

        fetch(`/api/content/related?type=post&id=${slug}`)
            .then(response => response.json())
            .then(data => {
                // Show section if there are connections
                if (data.primary && (data.related_posts.length > 0 || data.shared_disciplines.length > 0)) {
                    connectionMapSection.style.display = 'block';

                    // Display discipline badges
                    connectionDisciplines.innerHTML = '';
                    if (data.shared_disciplines && data.shared_disciplines.length > 0) {
                        data.shared_disciplines.forEach(discipline => {
                            const badge = document.createElement('span');
                            badge.className = `discipline-badge badge-${discipline}`;
                            badge.textContent = getDisciplineNamePortfolio(discipline);
                            badge.title = `This article explores ${getDisciplineNamePortfolio(discipline)}`;
                            connectionDisciplines.appendChild(badge);
                        });
                    }

                    // Display connected posts
                    connectionPosts.innerHTML = '';
                    if (data.related_posts && data.related_posts.length > 0) {
                        data.related_posts.forEach(post => {
                            const connectionItem = document.createElement('a');
                            connectionItem.href = `/blog/${post.slug}`;
                            connectionItem.className = 'connection-item';

                            const title = document.createElement('span');
                            title.className = 'connection-item-title';
                            title.textContent = post.title;
                            connectionItem.appendChild(title);

                            if (post.shared_disciplines) {
                                const sharedBadges = document.createElement('div');
                                sharedBadges.className = 'connection-item-badges';
                                post.shared_disciplines.forEach(d => {
                                    const badge = document.createElement('span');
                                    badge.className = `small-badge badge-${d}`;
                                    badge.textContent = getDisciplineNamePortfolio(d);
                                    sharedBadges.appendChild(badge);
                                });
                                connectionItem.appendChild(sharedBadges);
                            }

                            connectionPosts.appendChild(connectionItem);
                        });
                    }
                } else {
                    connectionMapSection.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error loading connection map:', error);
                connectionMapSection.style.display = 'none';
            });
    }

    function loadRelatedProjects(slug) {
        const relatedProjectsSection = document.getElementById('related-projects-section');
        const relatedProjectsGrid = document.getElementById('related-projects-grid');

        if (!relatedProjectsSection || !relatedProjectsGrid) return;

        fetch(`/api/blog/post/${slug}/related-projects`)
            .then(response => response.json())
            .then(projects => {
                if (projects.length === 0) {
                    relatedProjectsSection.style.display = 'none';
                    return;
                }

                relatedProjectsSection.style.display = 'block';
                relatedProjectsGrid.innerHTML = '';

                projects.forEach(project => {
                    const card = document.createElement('div');
                    card.className = 'portfolio-card';

                    // Add discipline data attributes
                    if (project.disciplines && project.disciplines.length > 0) {
                        card.dataset.disciplines = project.disciplines.join(',');
                        card.classList.add(`card-accent-${project.disciplines[0]}`);
                    }

                    const header = document.createElement('div');
                    header.className = 'portfolio-card-header';

                    // Add discipline badges
                    if (project.disciplines && project.disciplines.length > 0) {
                        const disciplineContainer = document.createElement('div');
                        disciplineContainer.className = 'portfolio-card-disciplines';
                        project.disciplines.forEach(discipline => {
                            const badge = document.createElement('span');
                            badge.className = `tag tag-${discipline}`;
                            badge.textContent = getDisciplineNamePortfolio(discipline);
                            disciplineContainer.appendChild(badge);
                        });
                        header.appendChild(disciplineContainer);

                        // Add synergy badge for multi-discipline projects
                        if (project.disciplines.length > 1) {
                            const synergyBadge = document.createElement('div');
                            synergyBadge.className = 'portfolio-card-synergy';
                            synergyBadge.textContent = '🔗 Synergy';
                            header.appendChild(synergyBadge);
                        }
                    }

                    const title = document.createElement('h3');
                    title.className = 'portfolio-card-title';
                    title.textContent = project.title;
                    header.appendChild(title);

                    const body = document.createElement('div');
                    body.className = 'portfolio-card-body';

                    const description = document.createElement('p');
                    description.className = 'portfolio-card-description';
                    description.textContent = project.description;
                    body.appendChild(description);

                    const techDiv = document.createElement('div');
                    techDiv.className = 'portfolio-card-tech';
                    project.technologies.forEach(tech => {
                        const tag = document.createElement('span');
                        tag.className = 'portfolio-card-tech-tag';
                        tag.textContent = tech;
                        techDiv.appendChild(tag);
                    });
                    body.appendChild(techDiv);

                    const linksDiv = document.createElement('div');
                    linksDiv.className = 'portfolio-card-links';

                    const demoLink = document.createElement('a');
                    demoLink.className = 'demo';
                    demoLink.href = project.links.demo;
                    demoLink.textContent = 'View Demo';

                    const githubLink = document.createElement('a');
                    githubLink.className = 'github';
                    githubLink.href = project.links.github;
                    githubLink.target = '_blank';
                    githubLink.textContent = 'GitHub';

                    linksDiv.appendChild(demoLink);
                    linksDiv.appendChild(githubLink);
                    body.appendChild(linksDiv);

                    card.appendChild(header);
                    card.appendChild(body);
                    relatedProjectsGrid.appendChild(card);
                });
            })
            .catch(error => {
                console.error('Error loading related projects:', error);
                relatedProjectsSection.style.display = 'none';
            });
    }

    function formatDate(dateString) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-US', options);
    }

    function setupReadingProgress() {
        // Update progress on scroll
        window.addEventListener('scroll', updateReadingProgress);
        updateReadingProgress(); // Initial call

        function updateReadingProgress() {
            const article = document.getElementById('article-body');
            if (!article) return;

            const articleTop = article.offsetTop;
            const articleHeight = article.offsetHeight;
            const windowHeight = window.innerHeight;
            const scrolled = window.scrollY;

            // Calculate progress: 0-100%
            let progress = 0;
            if (scrolled >= articleTop) {
                const articleEndPosition = articleTop + articleHeight - windowHeight;
                if (scrolled >= articleEndPosition) {
                    progress = 100;
                } else {
                    progress = Math.round(((scrolled - articleTop) / (articleHeight - windowHeight)) * 100);
                }
            }

            // Update progress bar
            if (readingProgress) {
                readingProgress.style.width = progress + '%';
            }

            // Update progress text
            if (articleProgress) {
                articleProgress.textContent = progress + '% read';
            }

            // Mark as fully read at 90%
            if (progress >= 90) {
                recordArticleRead();
            }
        }
    }

    function setupBookmarking() {
        // Check if article is already bookmarked
        const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '{}');
        isBookmarked = bookmarks[slug] === true;
        updateBookmarkButton();

        // Toggle bookmark on button click
        if (bookmarkBtn) {
            bookmarkBtn.addEventListener('click', function(e) {
                e.preventDefault();
                toggleBookmark();
            });
        }
    }

    function toggleBookmark() {
        const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '{}');

        if (isBookmarked) {
            delete bookmarks[slug];
        } else {
            bookmarks[slug] = true;
        }

        localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
        isBookmarked = !isBookmarked;
        updateBookmarkButton();

        // Show feedback
        showNotification(isBookmarked ? 'Article saved!' : 'Article removed from saves');
    }

    function updateBookmarkButton() {
        if (bookmarkBtn) {
            if (isBookmarked) {
                bookmarkBtn.classList.add('bookmarked');
                bookmarkBtn.setAttribute('title', 'Remove from saved');
            } else {
                bookmarkBtn.classList.remove('bookmarked');
                bookmarkBtn.setAttribute('title', 'Save this article');
            }
        }
    }

    function recordArticleRead() {
        // Record that user has read this article
        const readArticles = JSON.parse(localStorage.getItem('readArticles') || '[]');
        if (!readArticles.includes(slug)) {
            readArticles.push(slug);
            localStorage.setItem('readArticles', JSON.stringify(readArticles));
        }
    }

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

    // Load the article
    loadAllPosts();
    setupReadingProgress();
    setupBookmarking();
});
