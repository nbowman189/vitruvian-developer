document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const fileList = document.getElementById('file-list');
    const contentTitle = document.getElementById('content-title');
    const markdownContent = document.getElementById('markdown-content');
    const printButton = document.getElementById('print-button');
    const homeButton = document.getElementById('home-button');
    const projectNavBar = document.getElementById('project-nav-bar');
    const projectTitleNav = document.getElementById('project-title-nav');
    const backToProjectLink = document.getElementById('back-to-project');
    const homepage = document.getElementById('homepage');
    const projectView = document.getElementById('project-view');
    const portfolioGrid = document.getElementById('portfolio-grid');
    const blogPostsContainer = document.getElementById('blog-posts-container');

    // Breadcrumb elements
    const breadcrumbProject = document.getElementById('breadcrumb-project');
    const breadcrumbFile = document.getElementById('breadcrumb-file');

    // Badge elements
    const projectBadges = document.getElementById('project-badges');
    const projectNavBadges = document.getElementById('project-nav-badges');

    // STATE MANAGEMENT
    const projectState = {
        currentView: 'homepage', // 'homepage' | 'project' | 'file'
        currentProject: null,
        currentFile: null,
        projectMetadata: {},

        setState(view, project = null, file = null) {
            this.currentView = view;
            this.currentProject = project;
            this.currentFile = file;
            this.updateUI();
        },

        updateUI() {
            const isHomepage = this.currentView === 'homepage';
            const isProjectView = this.currentView === 'project' || this.currentView === 'file';

            // Toggle visibility
            if (homepage) homepage.classList.toggle('d-none', !isHomepage);
            if (projectView) projectView.classList.toggle('d-none', !isProjectView);

            // Update button visibility
            if (homeButton) homeButton.classList.toggle('d-none', isHomepage);
            if (printButton) printButton.classList.toggle('d-none', isHomepage);

            // Update nav bar
            if (projectNavBar) {
                projectNavBar.classList.toggle('d-none', isHomepage);
            }
        },

        isViewActive(view) {
            return this.currentView === view;
        }
    };

    // Custom title mappings for specific files
    const customTitles = {
        'check-in-log.md': 'Metrics Log',
        'progress-check-in-log.md': 'Exercise Progress Log'
    };

    // UTILITY FUNCTIONS
    function getFileDisplayTitle(filename) {
        return customTitles[filename] || filenameToTitle(filename);
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

    // Load project metadata from API
    async function loadProjectMetadata() {
        try {
            const response = await fetch('/api/projects-metadata');
            const data = await response.json();
            projectState.projectMetadata = data;
        } catch (error) {
            console.error('Error loading project metadata:', error);
        }
    }

    // Create discipline badges
    function createDisciplineBadges(disciplines) {
        const container = document.createElement('div');
        container.className = 'discipline-badges';

        if (!disciplines || disciplines.length === 0) return container;

        disciplines.forEach(discipline => {
            const badge = document.createElement('span');
            badge.className = `badge badge-${discipline}`;
            badge.textContent = getDisciplineNamePortfolio(discipline);
            badge.setAttribute('aria-label', `${getDisciplineNamePortfolio(discipline)} discipline`);
            container.appendChild(badge);
        });

        return container;
    }

    // Apply discipline color to nav bar
    function applyDisciplineColor(projectName) {
        const colors = {
            'Health_and_Fitness': '#ffb347', // amber
            'AI_Development': '#6a5acd'      // purple
        };

        const color = colors[projectName] || '#1a237e';

        if (projectNavBar) {
            projectNavBar.style.borderLeftColor = color;
            projectNavBar.style.setProperty('--accent-color-override', color);
        }
    }

    // Update breadcrumb navigation
    function updateBreadcrumb(projectName, fileName = null) {
        if (!breadcrumbProject) return;

        // Get project metadata for display name
        const metadata = projectState.projectMetadata[projectName];
        const projectDisplayName = metadata?.display_name || projectToTitle(projectName);

        // Update project breadcrumb
        const projectLink = document.createElement('a');
        projectLink.href = '#';
        projectLink.textContent = projectDisplayName;
        projectLink.addEventListener('click', (e) => {
            e.preventDefault();
            projectState.setState('project', projectName);
            loadProject(projectName);
        });

        breadcrumbProject.innerHTML = '';
        breadcrumbProject.appendChild(projectLink);

        // Update file breadcrumb
        if (fileName) {
            breadcrumbFile.textContent = getFileDisplayTitle(fileName);
            breadcrumbFile.setAttribute('aria-current', 'page');
        } else {
            breadcrumbFile.textContent = '—';
            breadcrumbFile.removeAttribute('aria-current');
        }
    }

    // FEATURED PROJECTS
    function loadFeaturedProjects() {
        fetch('/api/featured-projects')
            .then(response => response.json())
            .then(projects => {
                if (portfolioGrid) {
                    portfolioGrid.innerHTML = '';
                    projects.forEach(project => {
                        const card = document.createElement('div');
                        card.className = 'portfolio-card';

                        if (project.disciplines && project.disciplines.length > 0) {
                            card.dataset.disciplines = project.disciplines.join(',');
                            card.classList.add(`card-accent-${project.disciplines[0]}`);
                        }

                        const header = document.createElement('div');
                        header.className = 'portfolio-card-header';

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

                        // Primary link: Browse Documentation (new project page)
                        const docsLink = document.createElement('a');
                        docsLink.className = 'demo';
                        docsLink.href = `/project/${project.project}`;
                        docsLink.textContent = 'Browse Docs';

                        // Secondary link: Case Study
                        const caseStudyLink = document.createElement('a');
                        caseStudyLink.className = 'secondary';
                        caseStudyLink.href = `/project-case-study/${project.project}`;
                        caseStudyLink.textContent = 'Case Study';

                        const githubLink = document.createElement('a');
                        githubLink.className = 'github';
                        githubLink.href = project.links.github;
                        githubLink.target = '_blank';
                        githubLink.textContent = 'GitHub';

                        linksDiv.appendChild(docsLink);
                        linksDiv.appendChild(caseStudyLink);
                        linksDiv.appendChild(githubLink);
                        body.appendChild(linksDiv);

                        card.appendChild(header);
                        card.appendChild(body);
                        portfolioGrid.appendChild(card);
                    });
                }
            })
            .catch(error => console.error('Error fetching featured projects:', error));
    }

    function loadProjectFromPortfolio(projectName) {
        projectState.setState('project', projectName);
        loadProject(projectName);
        window.scrollTo(0, 0);
    }

    // BLOG POSTS
    function loadBlogPosts() {
        if (!blogPostsContainer) return;

        fetch('/api/blog/posts/latest?limit=3')
            .then(response => response.json())
            .then(posts => {
                blogPostsContainer.innerHTML = '';
                posts.forEach(post => {
                    const card = document.createElement('a');
                    card.href = `/blog/${post.slug}`;
                    card.className = 'blog-card';

                    const header = document.createElement('div');
                    header.className = 'blog-card-header';

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
                    dateSpan.textContent = formatDateBlog(post.date);
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
                    blogPostsContainer.appendChild(card);
                });
            })
            .catch(error => console.error('Error loading blog posts:', error));
    }

    function formatDateBlog(dateString) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-US', options);
    }

    // ALL PROJECTS
    function loadAllProjects() {
        const allProjectsList = document.getElementById('all-projects-list');
        if (!allProjectsList) return;

        fetch('/api/projects')
            .then(response => response.json())
            .then(projects => {
                allProjectsList.innerHTML = '';

                const projectsGrid = document.createElement('div');
                projectsGrid.className = 'projects-grid';

                projects.forEach(project => {
                    const projectCard = document.createElement('div');
                    projectCard.className = 'project-card';

                    const projectTitle = document.createElement('h3');
                    projectTitle.textContent = projectToTitle(project);
                    projectTitle.className = 'project-card-title';

                    // Link directly to new project documentation page
                    const projectLink = document.createElement('a');
                    projectLink.href = `/project/${project}`;
                    projectLink.className = 'project-card-link btn btn-primary';
                    projectLink.textContent = 'Explore Project';

                    projectCard.appendChild(projectTitle);
                    projectCard.appendChild(projectLink);
                    projectsGrid.appendChild(projectCard);
                });

                allProjectsList.appendChild(projectsGrid);
            })
            .catch(error => {
                console.error('Error fetching projects:', error);
                allProjectsList.innerHTML = '<p class="text-danger">Error loading projects</p>';
            });
    }

    // PROJECT LOADING
    function loadProject(projectName) {
        if (window.location.pathname !== '/') {
            window.location.href = '/';
            return;
        }

        projectState.setState('project', projectName);

        // Clear previous content
        fileList.innerHTML = '';
        contentTitle.textContent = 'Loading...';
        markdownContent.innerHTML = '';

        // Update project navigation bar
        projectTitleNav.textContent = projectToTitle(projectName);

        // Update breadcrumb
        updateBreadcrumb(projectName);

        // Add badges to nav bar
        const metadata = projectState.projectMetadata[projectName];
        if (metadata && projectNavBadges) {
            projectNavBadges.innerHTML = '';
            projectNavBadges.appendChild(createDisciplineBadges(metadata.disciplines));
        }

        // Add badges to header
        if (metadata && projectBadges) {
            projectBadges.innerHTML = '';
            projectBadges.appendChild(createDisciplineBadges(metadata.disciplines));
        }

        // Apply discipline color
        applyDisciplineColor(projectName);

        // Set up back to project link
        if (backToProjectLink) {
            backToProjectLink.onclick = (e) => {
                e.preventDefault();
                loadProject(projectName);
            };
        }

        // Fetch GEMINI.md content
        fetch(`/api/project/${projectName}`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    contentTitle.textContent = projectToTitle(projectName);
                    markdownContent.innerHTML = `<p class="text-danger">${data.error}</p>`;
                } else {
                    contentTitle.textContent = projectToTitle(data.title);
                    markdownContent.innerHTML = marked.parse(data.content);
                    // Initialize sortable tables after content is loaded
                    initializeSortableTables();
                }
            })
            .catch(error => {
                contentTitle.textContent = projectToTitle(projectName);
                markdownContent.innerHTML = `<p class="text-danger">Error loading project overview: ${error}</p>`;
                console.error('Error fetching project GEMINI.md:', error);
            });

        // Fetch list of markdown files
        fetch(`/api/project/${projectName}/files`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(files => {
                fileList.innerHTML = '';

                files.forEach(file => {
                    const li = document.createElement('li');
                    li.setAttribute('role', 'presentation');

                    const a = document.createElement('a');
                    a.href = '#';
                    a.role = 'tab';
                    a.setAttribute('aria-selected', 'false');
                    a.textContent = getFileDisplayTitle(file);
                    a.addEventListener('click', (e) => {
                        e.preventDefault();
                        fileList.querySelectorAll('a').forEach(link => {
                            link.classList.remove('active');
                            link.setAttribute('aria-selected', 'false');
                        });
                        a.classList.add('active');
                        a.setAttribute('aria-selected', 'true');
                        loadFile(projectName, file);
                    });
                    li.appendChild(a);
                    fileList.appendChild(li);
                });

                // Add Graphs link for Health_and_Fitness
                if (projectName === 'Health_and_Fitness') {
                    const li = document.createElement('li');
                    li.setAttribute('role', 'presentation');
                    const graphsLink = document.createElement('a');
                    graphsLink.href = '/health-and-fitness/graphs';
                    graphsLink.textContent = 'Graphs';
                    graphsLink.role = 'tab';
                    li.appendChild(graphsLink);
                    fileList.appendChild(li);

                    // Add AI Coach link
                    const aiCoachLi = document.createElement('li');
                    aiCoachLi.setAttribute('role', 'presentation');
                    const aiCoachLink = document.createElement('a');
                    aiCoachLink.href = '/health-and-fitness/ai-coach';
                    aiCoachLink.textContent = 'AI Coach';
                    aiCoachLink.role = 'tab';
                    aiCoachLi.appendChild(aiCoachLink);
                    fileList.appendChild(aiCoachLi);
                }

                // Add GEMINI link at end
                if (!Array.from(fileList.querySelectorAll('a')).some(link => link.textContent === 'GEMINI')) {
                    const geminiLi = document.createElement('li');
                    geminiLi.setAttribute('role', 'presentation');
                    const geminiLink = document.createElement('a');
                    geminiLink.href = '#';
                    geminiLink.role = 'tab';
                    geminiLink.setAttribute('aria-selected', 'false');
                    geminiLink.textContent = 'GEMINI';
                    geminiLink.addEventListener('click', (e) => {
                        e.preventDefault();
                        fileList.querySelectorAll('a').forEach(link => {
                            link.classList.remove('active');
                            link.setAttribute('aria-selected', 'false');
                        });
                        geminiLink.classList.add('active');
                        geminiLink.setAttribute('aria-selected', 'true');
                        loadGemini(projectName);
                    });
                    geminiLi.appendChild(geminiLink);
                    fileList.appendChild(geminiLi);
                }
            })
            .catch(error => console.error('Error fetching project files:', error));
    }

    // FILE LOADING
    function loadFile(projectName, filePath) {
        projectState.setState('file', projectName, filePath);

        contentTitle.textContent = getFileDisplayTitle(filePath);
        markdownContent.innerHTML = '';

        // Update breadcrumb
        updateBreadcrumb(projectName, filePath);

        // Ensure project nav bar is visible
        projectTitleNav.textContent = projectToTitle(projectName);

        // Set up back to project link
        if (backToProjectLink) {
            backToProjectLink.onclick = (e) => {
                e.preventDefault();
                loadProject(projectName);
            };
        }

        fetch(`/api/project/${projectName}/file/${filePath}`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    markdownContent.innerHTML = `<p class="text-danger">${data.error}</p>`;
                } else {
                    markdownContent.innerHTML = marked.parse(data.content);
                    // Initialize sortable tables after content is loaded
                    initializeSortableTables();
                }
            })
            .catch(error => {
                markdownContent.innerHTML = `<p class="text-danger">Error loading file: ${error}</p>`;
                console.error('Error fetching file content:', error);
            });
    }

    // GEMINI LOADING
    function loadGemini(projectName) {
        projectState.setState('file', projectName);

        contentTitle.textContent = 'Overview';
        markdownContent.innerHTML = '';

        // Update breadcrumb
        updateBreadcrumb(projectName, 'Overview');

        // Ensure project nav bar is visible
        projectTitleNav.textContent = projectToTitle(projectName);

        // Set up back to project link
        if (backToProjectLink) {
            backToProjectLink.onclick = (e) => {
                e.preventDefault();
                loadProject(projectName);
            };
        }

        fetch(`/api/project/${projectName}`, {
            credentials: 'include'
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    markdownContent.innerHTML = `<p class="text-danger">${data.error}</p>`;
                } else {
                    markdownContent.innerHTML = marked.parse(data.content);
                    // Initialize sortable tables after content is loaded
                    initializeSortableTables();
                }
            })
            .catch(error => {
                markdownContent.innerHTML = `<p class="text-danger">Error loading overview: ${error}</p>`;
                console.error('Error fetching GEMINI.md:', error);
            });
    }

    // SORTABLE TABLES
    function initializeSortableTables() {
        const tables = markdownContent.querySelectorAll('table');

        tables.forEach(table => {
            const headers = table.querySelectorAll('th');

            headers.forEach((header, columnIndex) => {
                // Add sortable class and cursor style
                header.classList.add('sortable');
                header.style.cursor = 'pointer';
                header.style.userSelect = 'none';
                header.style.position = 'relative';

                // Add sort indicator container
                const sortIndicator = document.createElement('span');
                sortIndicator.className = 'sort-indicator';
                sortIndicator.innerHTML = ' ↕';
                header.appendChild(sortIndicator);

                // Store sort state
                let sortDirection = 0; // 0 = unsorted, 1 = ascending, -1 = descending

                header.addEventListener('click', () => {
                    // Remove sort indicators from all other headers
                    headers.forEach(h => {
                        if (h !== header) {
                            const indicator = h.querySelector('.sort-indicator');
                            if (indicator) indicator.innerHTML = ' ↕';
                        }
                    });

                    // Toggle sort direction
                    if (sortDirection === 0 || sortDirection === -1) {
                        sortDirection = 1;
                        sortIndicator.innerHTML = ' ↑';
                    } else {
                        sortDirection = -1;
                        sortIndicator.innerHTML = ' ↓';
                    }

                    // Sort the table
                    sortTable(table, columnIndex, sortDirection);
                });
            });
        });
    }

    function sortTable(table, columnIndex, direction) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Determine data type from first non-empty cell
        let dataType = 'string';
        for (let row of rows) {
            const cell = row.cells[columnIndex];
            if (cell && cell.textContent.trim()) {
                const value = cell.textContent.trim();

                // Check if it's a date (YYYY-MM-DD format)
                if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
                    dataType = 'date';
                    break;
                }

                // Check if it's a number (including decimals, excluding "None" or "N/A")
                if (/^-?\d+\.?\d*$/.test(value) && value !== 'None' && value !== 'N/A') {
                    dataType = 'number';
                    break;
                }

                dataType = 'string';
                break;
            }
        }

        // Sort rows based on data type
        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];

            if (!aCell || !bCell) return 0;

            let aValue = aCell.textContent.trim();
            let bValue = bCell.textContent.trim();

            // Handle empty/None/N/A values (always sort to bottom)
            const aEmpty = !aValue || aValue === 'None' || aValue === 'N/A';
            const bEmpty = !bValue || bValue === 'None' || bValue === 'N/A';

            if (aEmpty && bEmpty) return 0;
            if (aEmpty) return 1;
            if (bEmpty) return -1;

            let comparison = 0;

            if (dataType === 'date') {
                comparison = new Date(aValue) - new Date(bValue);
            } else if (dataType === 'number') {
                comparison = parseFloat(aValue) - parseFloat(bValue);
            } else {
                comparison = aValue.localeCompare(bValue, undefined, { numeric: true, sensitivity: 'base' });
            }

            return comparison * direction;
        });

        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
    }

    // Smooth scrolling for anchor links
    function addSmoothScrolling() {
        const links = document.querySelectorAll('a[href^="#"]');
        links.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href === '#') return;

                const target = document.querySelector(href);
                if (target && homepage && !homepage.classList.contains('d-none')) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && projectState.currentView !== 'homepage') {
            e.preventDefault();
            projectState.setState('homepage');
            window.scrollTo(0, 0);
        }
    });

    // INITIALIZATION
    // Load metadata first
    loadProjectMetadata().then(() => {
        // Load all content
        loadFeaturedProjects();
        loadBlogPosts();
        loadAllProjects();

        // Set up homepage-specific listeners
        if (window.location.pathname === '/') {
            if (printButton) {
                printButton.addEventListener('click', () => {
                    window.print();
                });
            }

            if (homeButton) {
                homeButton.addEventListener('click', () => {
                    projectState.setState('homepage');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });
            }

            addSmoothScrolling();

            // Check for project/file from sessionStorage (graphs page)
            const projectToLoad = sessionStorage.getItem('loadProject');
            const fileToLoad = sessionStorage.getItem('loadFile');

            if (projectToLoad) {
                sessionStorage.removeItem('loadProject');
                sessionStorage.removeItem('loadFile');

                loadProject(projectToLoad);

                if (fileToLoad) {
                    setTimeout(() => {
                        loadFile(projectToLoad, fileToLoad);
                    }, 100);
                }
            }
        } else if (window.location.pathname.startsWith('/health-and-fitness/graphs')) {
            fetch('/api/health-and-fitness/health_data')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error fetching health data:', data.error);
                        return;
                    }

                    if (data.weight && data.weight.length > 0) {
                        createChart('weightChart', 'Weight', data.weight, 'Weight (lbs)');
                    }

                    if (data.bodyfat && data.bodyfat.length > 0) {
                        createChart('bodyfatChart', 'Body Fat %', data.bodyfat, 'Body Fat %');
                    }
                })
                .catch(error => console.error('Error fetching health data:', error));
        }
    });

    // Chart creation (used on graphs page)
    function createChart(canvasId, chartTitle, data, yAxisLabel) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                datasets: [{
                    label: chartTitle,
                    data: data,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.1
                }]
            },
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: {
                                month: 'MMM yyyy'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: yAxisLabel
                        }
                    }
                }
            }
        });
    }
});
