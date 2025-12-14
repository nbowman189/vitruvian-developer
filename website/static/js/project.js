/**
 * Project Documentation Page JavaScript
 * Handles sidebar navigation, content loading, TOC generation, and URL management
 */

(function() {
    'use strict';

    // ==========================================================================
    // State Management
    // ==========================================================================
    const state = {
        projectName: window.PROJECT_DATA?.name || '',
        projectDisplayName: window.PROJECT_DATA?.displayName || '',
        currentFile: null,
        categories: [],
        allFiles: [],
        sidebarOpen: false
    };

    // ==========================================================================
    // DOM Elements
    // ==========================================================================
    const elements = {
        sidebar: document.getElementById('docs-sidebar'),
        sidebarToggle: document.getElementById('sidebar-toggle'),
        sidebarOverlay: document.getElementById('sidebar-overlay'),
        navCategories: document.getElementById('nav-categories'),
        contentTitle: document.getElementById('content-title'),
        contentBody: document.getElementById('content-body'),
        breadcrumbFile: document.getElementById('breadcrumb-file'),
        tocNav: document.getElementById('toc-nav'),
        printBtn: document.getElementById('print-btn'),
        navPrev: document.getElementById('nav-prev'),
        navNext: document.getElementById('nav-next'),
        prevTitle: document.getElementById('prev-title'),
        nextTitle: document.getElementById('next-title')
    };

    // ==========================================================================
    // Initialization
    // ==========================================================================
    document.addEventListener('DOMContentLoaded', init);

    function init() {
        setupEventListeners();
        loadCategorizedFiles();
    }

    function setupEventListeners() {
        // Sidebar toggle (mobile)
        if (elements.sidebarToggle) {
            elements.sidebarToggle.addEventListener('click', toggleSidebar);
        }

        // Sidebar overlay click
        if (elements.sidebarOverlay) {
            elements.sidebarOverlay.addEventListener('click', closeSidebar);
        }

        // Print button
        if (elements.printBtn) {
            elements.printBtn.addEventListener('click', () => window.print());
        }

        // Browser back/forward
        window.addEventListener('popstate', handlePopState);

        // Escape key closes sidebar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.sidebarOpen) {
                closeSidebar();
            }
        });
    }

    // ==========================================================================
    // Sidebar Functions
    // ==========================================================================
    function toggleSidebar() {
        state.sidebarOpen = !state.sidebarOpen;
        elements.sidebar?.classList.toggle('open', state.sidebarOpen);
        elements.sidebarOverlay?.classList.toggle('active', state.sidebarOpen);
        elements.sidebarToggle?.classList.toggle('active', state.sidebarOpen);
        document.body.style.overflow = state.sidebarOpen ? 'hidden' : '';
    }

    function closeSidebar() {
        state.sidebarOpen = false;
        elements.sidebar?.classList.remove('open');
        elements.sidebarOverlay?.classList.remove('active');
        elements.sidebarToggle?.classList.remove('active');
        document.body.style.overflow = '';
    }

    // ==========================================================================
    // File Loading and Navigation
    // ==========================================================================
    async function loadCategorizedFiles() {
        try {
            const response = await fetch(`/api/project/${state.projectName}/categorized-files`);
            if (!response.ok) throw new Error('Failed to load files');

            const data = await response.json();
            state.categories = data.categories;

            // Build flat file list for prev/next navigation
            state.allFiles = [];
            data.categories.forEach(cat => {
                cat.files.forEach(file => {
                    state.allFiles.push({
                        path: file.path,
                        name: file.name,
                        category: cat.name
                    });
                });
            });

            renderSidebarNav(data.categories);

            // Load initial content
            const initialFile = window.PROJECT_DATA?.initialFile;
            if (initialFile) {
                loadFile(initialFile);
            } else {
                loadOverview();
            }

        } catch (error) {
            console.error('Error loading categorized files:', error);
            elements.navCategories.innerHTML = '<p class="text-danger">Error loading navigation</p>';
        }
    }

    function renderSidebarNav(categories) {
        let html = '';

        categories.forEach((category, index) => {
            const isExpanded = index < 3; // First 3 categories expanded by default
            const collapseClass = isExpanded ? '' : 'collapsed';

            html += `
                <div class="nav-section ${collapseClass}" data-category="${category.id}">
                    <div class="nav-section-header" onclick="toggleCategory('${category.id}')">
                        <span>${category.name}</span>
                        <span class="nav-section-toggle">&#9660;</span>
                    </div>
                    <ul class="nav-section-items">
            `;

            category.files.forEach(file => {
                html += `
                    <li>
                        <a href="/project/${state.projectName}/${file.path}"
                           class="nav-link"
                           data-file="${file.path}"
                           onclick="handleNavClick(event, '${file.path}')">
                            ${file.name}
                        </a>
                    </li>
                `;
            });

            html += `
                    </ul>
                </div>
            `;
        });

        elements.navCategories.innerHTML = html;
    }

    // Global function for category toggle
    window.toggleCategory = function(categoryId) {
        const section = document.querySelector(`[data-category="${categoryId}"]`);
        if (section) {
            section.classList.toggle('collapsed');
        }
    };

    // Global function for nav link clicks
    window.handleNavClick = function(event, filePath) {
        event.preventDefault();

        // Update URL without page reload
        const newUrl = `/project/${state.projectName}/${filePath}`;
        history.pushState({ file: filePath }, '', newUrl);

        loadFile(filePath);
        closeSidebar();
    };

    function handlePopState(event) {
        if (event.state && event.state.file) {
            loadFile(event.state.file);
        } else {
            // Check URL path
            const path = window.location.pathname;
            const match = path.match(/^\/project\/[^\/]+\/(.+)$/);
            if (match) {
                loadFile(match[1]);
            } else {
                loadOverview();
            }
        }
    }

    async function loadFile(filePath) {
        state.currentFile = filePath;

        // Update active state in sidebar
        updateActiveNavLink(filePath);

        // Show loading state
        elements.contentBody.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Loading content...</p>
            </div>
        `;

        try {
            const response = await fetch(`/api/project/${state.projectName}/file/${filePath}`);
            if (!response.ok) throw new Error('Failed to load file');

            const data = await response.json();

            // Update title
            const fileInfo = state.allFiles.find(f => f.path === filePath);
            const title = fileInfo?.name || filenameToTitle(filePath);
            elements.contentTitle.textContent = title;

            // Update breadcrumb
            elements.breadcrumbFile.textContent = title;

            // Render markdown content
            elements.contentBody.innerHTML = marked.parse(data.content);

            // Generate table of contents
            generateTOC();

            // Setup sortable tables
            initializeSortableTables();

            // Update prev/next navigation
            updatePrevNextNav(filePath);

            // Scroll to top
            window.scrollTo(0, 0);

        } catch (error) {
            console.error('Error loading file:', error);
            elements.contentBody.innerHTML = `
                <div class="callout callout-danger">
                    <div class="callout-title">Error</div>
                    <p>Failed to load the file. Please try again.</p>
                </div>
            `;
        }
    }

    async function loadOverview() {
        state.currentFile = null;

        // Update active state
        updateActiveNavLink(null);

        // Show loading state
        elements.contentBody.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Loading content...</p>
            </div>
        `;

        try {
            const response = await fetch(`/api/project/${state.projectName}`);
            if (!response.ok) throw new Error('Failed to load overview');

            const data = await response.json();

            // Update title
            elements.contentTitle.textContent = state.projectDisplayName;

            // Update breadcrumb
            elements.breadcrumbFile.textContent = '';

            // Render markdown content
            elements.contentBody.innerHTML = marked.parse(data.content);

            // Generate table of contents
            generateTOC();

            // Update prev/next navigation
            updatePrevNextNav(null);

            // Scroll to top
            window.scrollTo(0, 0);

        } catch (error) {
            console.error('Error loading overview:', error);
            elements.contentBody.innerHTML = `
                <div class="callout callout-danger">
                    <div class="callout-title">Error</div>
                    <p>Failed to load the overview. Please try again.</p>
                </div>
            `;
        }
    }

    function updateActiveNavLink(currentFile) {
        // Remove all active states
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        if (currentFile) {
            // Find and activate the current file link
            const activeLink = document.querySelector(`[data-file="${currentFile}"]`);
            if (activeLink) {
                activeLink.classList.add('active');

                // Ensure parent category is expanded
                const section = activeLink.closest('.nav-section');
                if (section) {
                    section.classList.remove('collapsed');
                }
            }
        } else {
            // Activate overview link
            const overviewLink = document.querySelector('.nav-overview');
            if (overviewLink) {
                overviewLink.classList.add('active');
            }
        }
    }

    function updatePrevNextNav(currentFile) {
        const currentIndex = currentFile
            ? state.allFiles.findIndex(f => f.path === currentFile)
            : -1;

        // Previous
        if (currentIndex > 0) {
            const prev = state.allFiles[currentIndex - 1];
            elements.navPrev.style.visibility = 'visible';
            elements.navPrev.href = `/project/${state.projectName}/${prev.path}`;
            elements.navPrev.onclick = (e) => {
                e.preventDefault();
                window.handleNavClick(e, prev.path);
            };
            elements.prevTitle.textContent = prev.name;
        } else if (currentIndex === 0) {
            // Link back to overview
            elements.navPrev.style.visibility = 'visible';
            elements.navPrev.href = `/project/${state.projectName}`;
            elements.navPrev.onclick = (e) => {
                e.preventDefault();
                history.pushState({}, '', `/project/${state.projectName}`);
                loadOverview();
            };
            elements.prevTitle.textContent = 'Overview';
        } else {
            elements.navPrev.style.visibility = 'hidden';
        }

        // Next
        if (currentFile === null && state.allFiles.length > 0) {
            // From overview, go to first file
            const next = state.allFiles[0];
            elements.navNext.style.visibility = 'visible';
            elements.navNext.href = `/project/${state.projectName}/${next.path}`;
            elements.navNext.onclick = (e) => {
                e.preventDefault();
                window.handleNavClick(e, next.path);
            };
            elements.nextTitle.textContent = next.name;
        } else if (currentIndex >= 0 && currentIndex < state.allFiles.length - 1) {
            const next = state.allFiles[currentIndex + 1];
            elements.navNext.style.visibility = 'visible';
            elements.navNext.href = `/project/${state.projectName}/${next.path}`;
            elements.navNext.onclick = (e) => {
                e.preventDefault();
                window.handleNavClick(e, next.path);
            };
            elements.nextTitle.textContent = next.name;
        } else {
            elements.navNext.style.visibility = 'hidden';
        }
    }

    // ==========================================================================
    // Table of Contents Generation
    // ==========================================================================
    function generateTOC() {
        const headings = elements.contentBody.querySelectorAll('h2, h3');
        const tocNav = elements.tocNav;

        if (!tocNav || headings.length === 0) {
            if (tocNav) tocNav.innerHTML = '<p class="text-muted">No sections</p>';
            return;
        }

        let html = '';

        headings.forEach((heading, index) => {
            // Add ID to heading if not present
            if (!heading.id) {
                heading.id = `section-${index}`;
            }

            const level = heading.tagName.toLowerCase();
            const linkClass = level === 'h3' ? 'toc-link toc-link-h3' : 'toc-link';

            html += `
                <a href="#${heading.id}" class="${linkClass}" data-target="${heading.id}">
                    ${heading.textContent}
                </a>
            `;
        });

        tocNav.innerHTML = html;

        // Setup scroll spy
        setupScrollSpy();
    }

    function setupScrollSpy() {
        const tocLinks = document.querySelectorAll('.toc-link');
        if (tocLinks.length === 0) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // Remove active from all
                        tocLinks.forEach(link => link.classList.remove('active'));

                        // Add active to current
                        const activeLink = document.querySelector(`[data-target="${entry.target.id}"]`);
                        if (activeLink) {
                            activeLink.classList.add('active');
                        }
                    }
                });
            },
            {
                rootMargin: '-100px 0px -66%',
                threshold: 0
            }
        );

        // Observe all headings
        document.querySelectorAll('.content-body h2, .content-body h3').forEach(heading => {
            observer.observe(heading);
        });

        // Smooth scroll for TOC links
        tocLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('data-target');
                const target = document.getElementById(targetId);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    // ==========================================================================
    // Sortable Tables
    // ==========================================================================
    function initializeSortableTables() {
        const tables = elements.contentBody.querySelectorAll('table');

        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            let firstColumnIsDate = false;

            // Check if first column contains dates
            if (headers.length > 0) {
                const tbody = table.querySelector('tbody') || table;
                const firstDataRow = Array.from(tbody.querySelectorAll('tr')).find(row => row.querySelector('td'));

                if (firstDataRow && firstDataRow.cells[0]) {
                    const firstCellValue = firstDataRow.cells[0].textContent.trim();
                    // Check if it matches date format (YYYY-MM-DD)
                    firstColumnIsDate = /^\d{4}-\d{2}-\d{2}$/.test(firstCellValue) ||
                                       /^\*\*\d{4}-\d{2}-\d{2}\*\*$/.test(firstCellValue);
                }
            }

            headers.forEach((header, columnIndex) => {
                header.classList.add('sortable');
                header.style.cursor = 'pointer';

                // Add sort indicator
                const indicator = document.createElement('span');
                indicator.className = 'sort-indicator';
                indicator.innerHTML = ' &#8645;';
                header.appendChild(indicator);

                let sortDirection = 0;

                header.addEventListener('click', () => {
                    // Reset other headers
                    headers.forEach(h => {
                        if (h !== header) {
                            const ind = h.querySelector('.sort-indicator');
                            if (ind) ind.innerHTML = ' &#8645;';
                        }
                    });

                    // Toggle direction
                    sortDirection = sortDirection === 1 ? -1 : 1;
                    indicator.innerHTML = sortDirection === 1 ? ' &#8593;' : ' &#8595;';

                    sortTable(table, columnIndex, sortDirection);
                });
            });

            // Auto-sort by first column (descending) if it's a date column
            if (firstColumnIsDate && headers.length > 0) {
                const firstHeader = headers[0];
                const indicator = firstHeader.querySelector('.sort-indicator');
                if (indicator) {
                    indicator.innerHTML = ' &#8595;';
                }
                sortTable(table, 0, -1); // -1 for descending order
            }
        });
    }

    function sortTable(table, columnIndex, direction) {
        const tbody = table.querySelector('tbody') || table;
        const rows = Array.from(tbody.querySelectorAll('tr')).filter(row => row.querySelector('td'));

        if (rows.length === 0) return;

        // Determine data type
        let dataType = 'string';
        for (const row of rows) {
            const cell = row.cells[columnIndex];
            if (cell?.textContent.trim()) {
                const value = cell.textContent.trim();
                // Check for date (including bold dates like in DAILY TOTAL rows)
                if (/^\d{4}-\d{2}-\d{2}$/.test(value) || /^\*\*\d{4}-\d{2}-\d{2}\*\*$/.test(value)) {
                    dataType = 'date';
                    break;
                }
                if (/^-?\d+\.?\d*$/.test(value)) {
                    dataType = 'number';
                    break;
                }
                break;
            }
        }

        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];

            if (!aCell || !bCell) return 0;

            let aValue = aCell.textContent.trim();
            let bValue = bCell.textContent.trim();

            // Handle empty/None values
            const aEmpty = !aValue || aValue === 'None' || aValue === 'N/A';
            const bEmpty = !bValue || bValue === 'None' || bValue === 'N/A';

            if (aEmpty && bEmpty) return 0;
            if (aEmpty) return 1;
            if (bEmpty) return -1;

            let comparison = 0;

            if (dataType === 'date') {
                // Strip markdown bold formatting for date comparison
                const cleanA = aValue.replace(/\*\*/g, '');
                const cleanB = bValue.replace(/\*\*/g, '');
                comparison = new Date(cleanA) - new Date(cleanB);
            } else if (dataType === 'number') {
                comparison = parseFloat(aValue) - parseFloat(bValue);
            } else {
                comparison = aValue.localeCompare(bValue, undefined, { numeric: true });
            }

            return comparison * direction;
        });

        rows.forEach(row => tbody.appendChild(row));
    }

    // ==========================================================================
    // Utility Functions
    // ==========================================================================
    function filenameToTitle(filename) {
        const customTitles = {
            'check-in-log.md': 'Metrics Log',
            'progress-check-in-log.md': 'Exercise Progress Log',
            'GEMINI.md': 'Overview',
            'README.md': 'Introduction'
        };

        if (customTitles[filename]) return customTitles[filename];

        // Get basename
        let name = filename.split('/').pop();
        // Remove extension
        name = name.replace(/\.md$/, '');
        // Replace separators
        name = name.replace(/[-_]/g, ' ');
        // Title case
        return name.replace(/\b\w/g, c => c.toUpperCase());
    }

})();
