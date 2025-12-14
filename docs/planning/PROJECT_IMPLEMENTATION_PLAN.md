# Project Pages Implementation Plan
## Detailed Roadmap to Brand Alignment

**Author:** The Pragmatic Coder
**Date:** November 18, 2025
**Scope:** Complete refactoring of project pages to align with brand and improve UX/accessibility
**Estimated Timeline:** 4-5 working days (can be parallelized into smaller sessions)

---

## Overview

This plan breaks down the analysis into actionable, sequenced tasks that build on each other. Each task includes:
- **What** to change
- **Why** it matters
- **How** to implement it
- **Expected outcome**
- **Files affected**
- **Complexity** (Low/Medium/High)

**Philosophy:** We'll do this pragmatically—make the highest-impact changes first, then build into smaller refinements. The goal is a cohesive, modern experience that feels intentional.

---

## Phase 1: Foundation & Semantic HTML (Priority: HIGH)
**Goal:** Clean up HTML structure and fix accessibility violations
**Estimated Time:** 3-4 hours
**Files:** `templates/index.html`, `static/css/style.css`

### Task 1.1: Remove Sidebar & Dead Code
**What:** Delete the hidden sidebar from HTML completely

**Why:** The sidebar is confusing and unused. Removing it clarifies the navigation model.

**How:**
1. In `templates/index.html`, locate and remove:
   ```html
   <div id="left-nav" class="d-none">
       <div class="list-group" id="old-file-list">
           <!-- This sidebar is now hidden, content moved to nav bar -->
       </div>
   </div>
   ```

2. Also remove the CSS that supports it in `style.css`:
   ```css
   #left-nav {
       flex: 0 0 280px;
   }
   ```

3. Update the `.row` flex layout since it was designed for a sidebar:
   ```css
   /* BEFORE */
   .row {
       display: flex;
       gap: 2rem;
   }

   /* AFTER */
   .row {
       display: flex;
       flex-direction: column;
       gap: 2rem;
   }
   ```

**Expected Outcome:** Cleaner HTML, no hidden elements, full-width content area

**Complexity:** Low

---

### Task 1.2: Fix Semantic HTML Structure
**What:** Restructure project view with proper semantic HTML

**Why:** Screen readers, SEO, maintainability, and accessibility compliance

**How:**
1. In `templates/index.html`, replace the project view section with:

```html
<!-- Project View (Hidden by default, shown when browsing) -->
<div id="project-view" class="project-view d-none">
    <div class="project-container">
        <!-- Project Header with Breadcrumb -->
        <header class="project-header" role="banner">
            <nav aria-label="Breadcrumb" class="breadcrumb-nav">
                <ol class="breadcrumb-list">
                    <li><a href="/">Home</a></li>
                    <li id="breadcrumb-project">Projects</li>
                    <li id="breadcrumb-file" aria-current="page">—</li>
                </ol>
            </nav>

            <div class="project-header-content">
                <div class="project-header-left">
                    <h1 id="content-title" class="project-title">Loading...</h1>
                    <div id="project-badges" class="project-badges"></div>
                </div>
                <div class="button-group">
                    <button id="home-button" class="btn btn-secondary d-none"
                            aria-label="Return to home page">Home</button>
                    <button id="print-button" class="btn btn-primary d-none"
                            aria-label="Print current page">Print</button>
                </div>
            </div>
        </header>

        <!-- Project Navigation Bar (File List) -->
        <nav id="project-nav-bar" class="project-nav-bar d-none" aria-label="File navigation">
            <div class="container-fluid">
                <div class="project-nav-content">
                    <div class="project-nav-left">
                        <span id="project-title-nav" class="project-title"></span>
                        <div id="project-nav-badges" class="project-nav-badges"></div>
                    </div>
                    <ul id="file-list" class="project-nav-links" role="tablist">
                        <!-- Markdown file links will be loaded here by JavaScript -->
                    </ul>
                    <div class="project-breadcrumb">
                        <a href="#" id="back-to-project" class="breadcrumb-link">Back to Project</a>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <main id="project-content" class="project-content" role="main">
            <div id="markdown-content" class="markdown-content">
                <p>Select a file from the navigation to get started.</p>
            </div>
        </main>
    </div>
</div>
```

2. Key improvements:
   - Use `<header>`, `<nav>`, `<main>` semantic elements
   - Proper heading hierarchy (h1 inside header)
   - ARIA labels on navigation elements
   - Breadcrumb as ordered list (`<ol>`)
   - Tab role on file navigation

**Expected Outcome:** Valid, accessible HTML that screen readers can parse correctly

**Complexity:** Medium

---

### Task 1.3: Fix File List Structure
**What:** Update JavaScript to create proper list items

**Why:** The file list currently creates `<li>` without `<ul>` wrapper, which is invalid HTML

**How:**
In `static/js/script.js`, in the `loadProject()` function, update the file list creation:

```javascript
// BEFORE (line ~351)
files.forEach(file => {
    const li = document.createElement('li');
    const a = document.createElement('a');
    // ...
    li.appendChild(a);
    fileList.appendChild(li);
});

// AFTER
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
        // Remove active/selected from all links
        fileList.querySelectorAll('a').forEach(link => {
            link.classList.remove('active');
            link.setAttribute('aria-selected', 'false');
        });
        // Add active/selected to clicked link
        a.classList.add('active');
        a.setAttribute('aria-selected', 'true');
        loadFile(projectName, file);
    });
    li.appendChild(a);
    fileList.appendChild(li);
});
```

**Expected Outcome:** Valid HTML, proper ARIA attributes for tab navigation

**Complexity:** Low

---

## Phase 2: State Management Refactor (Priority: HIGH)
**Goal:** Centralize state management to prevent bugs and make code maintainable
**Estimated Time:** 2-3 hours
**Files:** `static/js/script.js`

### Task 2.1: Implement State Management Object
**What:** Create a single source of truth for page state

**Why:** Current code has scattered `classList.toggle` calls making it fragile and hard to debug

**How:**
In `static/js/script.js`, add at the top of the DOMContentLoaded listener:

```javascript
// STATE MANAGEMENT
const projectState = {
    currentView: 'homepage', // 'homepage' | 'project' | 'file'
    currentProject: null,
    currentFile: null,

    // Set state and automatically update UI
    setState(view, project = null, file = null) {
        this.currentView = view;
        this.currentProject = project;
        this.currentFile = file;
        this.updateUI();
    },

    // Single source of truth for all UI updates
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

    // Helper to check current state
    isViewActive(view) {
        return this.currentView === view;
    },

    // Helper to get current project
    getProject() {
        return this.currentProject;
    },

    // Helper to get current file
    getFile() {
        return this.currentFile;
    }
};
```

**Expected Outcome:** Predictable state transitions, easier to debug, cleaner code

**Complexity:** Medium

---

### Task 2.2: Replace All State-Related Code
**What:** Update existing functions to use projectState instead of direct DOM manipulation

**Why:** Reduces bugs, makes code clearer, easier to maintain

**How:**

1. In `loadProject()` function, replace:
```javascript
// BEFORE (lines ~300-315)
if (homepage) homepage.classList.add('d-none');
if (projectView) projectView.classList.remove('d-none');
if(printButton) printButton.classList.add('d-none');
if(homeButton) homeButton.classList.remove('d-none');

// AFTER
projectState.setState('project', projectName);
```

2. In `loadFile()` function, replace:
```javascript
// BEFORE (lines ~402-430)
if(printButton) printButton.classList.add('d-none');
if(contentTitle) contentTitle.classList.add('d-none');
// ... multiple manual toggles ...
if(printButton) printButton.classList.remove('d-none');
if(homeButton) homeButton.classList.remove('d-none');

// AFTER
projectState.setState('file', projectName, filePath);
```

3. In `loadGemini()` function, do the same:
```javascript
// BEFORE
if(printButton) printButton.classList.add('d-none');
if(contentTitle) contentTitle.classList.add('d-none');
// ...
if(printButton) printButton.classList.remove('d-none');

// AFTER
projectState.setState('file', projectName);
```

4. In home button click handler:
```javascript
// BEFORE
if (homepage) homepage.classList.remove('d-none');
if (projectView) projectView.classList.add('d-none');

// AFTER
projectState.setState('homepage');
```

**Expected Outcome:** Cleaner code, fewer potential bugs, single source of truth

**Complexity:** Medium (systematic replacement)

---

## Phase 3: Visual Brand Integration (Priority: HIGH)
**Goal:** Add discipline colors and badges to project navigation
**Estimated Time:** 2-3 hours
**Files:** `static/js/script.js`, `static/css/style.css`, `app.py`

### Task 3.1: Update Backend to Include Project Metadata
**What:** Expose project discipline information via API

**Why:** Frontend needs to know which disciplines each project relates to

**How:**

1. In `website/app.py`, update the projects list (around line 15):

```python
# Define the desired file order for Health_and_Fitness project
HEALTH_FITNESS_FILE_ORDER = [
    'fitness-roadmap.md',
    'Full-Meal-Plan.md',
    'Shopping-List-and-Estimate.md',
    'check-in-log.md',
    'progress-check-in-log.md'
]

# Project metadata
PROJECT_METADATA = {
    'Health_and_Fitness': {
        'display_name': 'Health & Fitness',
        'disciplines': ['fitness', 'meta'],
        'description': 'Complete health and fitness management system with meal plans, workout tracking, and progress monitoring.'
    },
    'AI_Development': {
        'display_name': 'AI Development',
        'disciplines': ['ai', 'code'],
        'description': 'Exploration and development of artificial intelligence concepts, applications, and research.'
    }
}
```

2. Create a new API endpoint in `app.py` (after line 114):

```python
@app.route('/api/projects-metadata')
def get_projects_metadata():
    """Get metadata for all projects including disciplines"""
    return jsonify(PROJECT_METADATA)
```

**Expected Outcome:** Frontend can fetch project metadata to display badges

**Complexity:** Low

---

### Task 3.2: Add Discipline Badges to Navigation
**What:** Display discipline badges in project nav bar

**Why:** Reinforce brand and give visual context

**How:**

1. In `static/js/script.js`, add helper function after utilities:

```javascript
// PROJECT METADATA
const projectMetadata = {};

// Load project metadata on page load
async function loadProjectMetadata() {
    try {
        const response = await fetch('/api/projects-metadata');
        const data = await response.json();
        Object.assign(projectMetadata, data);
    } catch (error) {
        console.error('Error loading project metadata:', error);
    }
}

// Call this early in DOMContentLoaded
loadProjectMetadata();

// Function to create discipline badges
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

// Function to apply discipline color to nav bar
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
```

2. Update `loadProject()` function to add badges:

```javascript
// In loadProject(), after fetching project list, add:
const metadata = projectMetadata[projectName];
if (metadata) {
    // Update project nav bar with badges
    const badgesContainer = document.getElementById('project-nav-badges');
    if (badgesContainer) {
        badgesContainer.innerHTML = '';
        badgesContainer.appendChild(createDisciplineBadges(metadata.disciplines));
    }

    // Update project header with badges
    const headerBadgesContainer = document.getElementById('project-badges');
    if (headerBadgesContainer) {
        headerBadgesContainer.innerHTML = '';
        headerBadgesContainer.appendChild(createDisciplineBadges(metadata.disciplines));
    }

    // Apply discipline color to nav bar
    applyDisciplineColor(projectName);
}
```

**Expected Outcome:** Badges displayed with discipline colors in nav bar and header

**Complexity:** Medium

---

### Task 3.3: Add Discipline Badge CSS
**What:** Style the new badge components

**Why:** Badges need to match brand color system

**How:**

In `static/css/style.css`, add after the existing `.tag` styles (around line 125):

```css
/* Discipline Badges (for project navigation) */
.discipline-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    align-items: center;
}

.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    white-space: nowrap;
}

.badge-code {
    background-color: rgba(26, 35, 126, 0.1);
    color: var(--color-code);
    border: 1px solid rgba(26, 35, 126, 0.2);
}

.badge-ai {
    background-color: rgba(124, 58, 237, 0.1);
    color: var(--color-ai);
    border: 1px solid rgba(124, 58, 237, 0.2);
}

.badge-fitness {
    background-color: rgba(255, 138, 61, 0.1);
    color: var(--color-fitness);
    border: 1px solid rgba(255, 138, 61, 0.2);
}

.badge-meta {
    background-color: rgba(6, 182, 212, 0.1);
    color: var(--color-meta);
    border: 1px solid rgba(6, 182, 212, 0.2);
}
```

**Expected Outcome:** Styled badges that match brand color system

**Complexity:** Low

---

## Phase 4: Breadcrumb Navigation (Priority: HIGH)
**Goal:** Add clear navigation context showing user location
**Estimated Time:** 1-2 hours
**Files:** `static/js/script.js`, `static/css/style.css`

### Task 4.1: Implement Breadcrumb Updates
**What:** Update breadcrumb when navigating projects/files

**Why:** Helps users understand where they are in the site hierarchy

**How:**

In `static/js/script.js`, add helper function:

```javascript
function updateBreadcrumb(projectName, fileName = null) {
    const breadcrumbProject = document.getElementById('breadcrumb-project');
    const breadcrumbFile = document.getElementById('breadcrumb-file');

    if (!breadcrumbProject) return;

    // Get project metadata for display name
    const metadata = projectMetadata[projectName];
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
```

2. Call `updateBreadcrumb()` in relevant places:

```javascript
// In loadProject(), after loading overview:
updateBreadcrumb(projectName);

// In loadFile(), after loading file:
updateBreadcrumb(projectName, filePath);

// In loadGemini(), after loading GEMINI:
updateBreadcrumb(projectName, 'Overview');
```

**Expected Outcome:** Breadcrumb shows user location: Home > Project > File

**Complexity:** Medium

---

### Task 4.2: Style Breadcrumb
**What:** Add CSS for breadcrumb navigation

**Why:** Breadcrumb should be visually clear and match brand

**How:**

In `static/css/style.css`, add:

```css
/* Breadcrumb Navigation */
.breadcrumb-nav {
    margin-bottom: 1.5rem;
    background-color: var(--light-bg);
    padding: 1rem;
    border-radius: 6px;
}

.breadcrumb-list {
    display: flex;
    align-items: center;
    list-style: none;
    margin: 0;
    padding: 0;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.breadcrumb-list li {
    display: flex;
    align-items: center;
}

.breadcrumb-list li:not(:last-child)::after {
    content: '›';
    margin-left: 0.75rem;
    color: var(--text-muted);
}

.breadcrumb-list a {
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s ease;
    padding: 0.25rem 0;
    border-bottom: 2px solid transparent;
}

.breadcrumb-list a:hover {
    color: var(--accent-color);
    border-bottom-color: var(--accent-color);
}

.breadcrumb-list li[aria-current="page"] {
    color: var(--text-dark);
    font-weight: 600;
}

@media (max-width: 768px) {
    .breadcrumb-list {
        font-size: 0.95rem;
    }

    .breadcrumb-list li:not(:last-child)::after {
        margin-left: 0.5rem;
    }
}
```

**Expected Outcome:** Breadcrumb styled and responsive

**Complexity:** Low

---

## Phase 5: Mobile Responsiveness (Priority: MEDIUM)
**Goal:** Ensure project pages work well on mobile devices
**Estimated Time:** 1-2 hours
**Files:** `static/css/style.css`

### Task 5.1: Enhance Mobile Navigation
**What:** Improve project nav bar responsiveness

**Why:** Current layout breaks on small screens with horizontal scrolling

**How:**

In `static/css/style.css`, add mobile-specific styling after the project nav bar styles (around line 250):

```css
/* Mobile Responsiveness for Project Navigation */
@media (max-width: 768px) {
    .project-nav-content {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
    }

    .project-nav-left {
        order: 1;
    }

    .project-nav-links {
        order: 2;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 0.5rem;
    }

    .project-breadcrumb {
        order: 3;
        margin-left: 0;
    }

    .project-nav-links a {
        min-width: max-content;
        padding: 0.5rem 0.75rem;
        font-size: 0.9rem;
    }
}

@media (max-width: 480px) {
    .project-nav-bar {
        padding: 0.5rem 0;
        margin-top: 0.5rem;
    }

    .project-title {
        font-size: 0.9rem;
        padding: 0.25rem 0.75rem;
    }

    .project-nav-links a {
        padding: 0.4rem 0.6rem;
        font-size: 0.85rem;
    }

    .breadcrumb-link {
        font-size: 0.9rem;
        padding: 0.4rem 0.5rem;
    }

    .button-group {
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .btn {
        flex: 1;
        min-width: 100px;
    }
}
```

**Expected Outcome:** Project nav bar adapts to mobile screens

**Complexity:** Low

---

### Task 5.2: Responsive Header Layout
**What:** Ensure project header stacks nicely on mobile

**Why:** Header with title, badges, and buttons needs better mobile layout

**How:**

In `static/css/style.css`, add:

```css
/* Project Header Responsive */
@media (max-width: 768px) {
    .project-header-content {
        flex-direction: column;
        gap: 1rem;
        align-items: flex-start;
    }

    .project-header-left {
        width: 100%;
    }

    .button-group {
        width: 100%;
        justify-content: flex-start;
    }

    .button-group .btn {
        flex: 0 1 auto;
    }
}

@media (max-width: 480px) {
    .project-title {
        font-size: 1.75rem;
        margin-bottom: 0.5rem;
    }

    .discipline-badges {
        margin-top: 0.5rem;
    }

    .button-group {
        gap: 0.5rem;
        width: 100%;
    }

    .button-group .btn {
        flex: 1;
    }
}
```

**Expected Outcome:** Header responsive and mobile-friendly

**Complexity:** Low

---

## Phase 6: Accessibility Polish (Priority: MEDIUM)
**Goal:** Achieve WCAG 2.1 AA compliance
**Estimated Time:** 1-2 hours
**Files:** `static/js/script.js`, `static/css/style.css`

### Task 6.1: Add Keyboard Navigation Support
**What:** Add Escape key support and tab order improvements

**Why:** Users should be able to navigate without mouse

**How:**

In `static/js/script.js`, add to the DOMContentLoaded listener:

```javascript
// Keyboard navigation support
document.addEventListener('keydown', (e) => {
    // Escape to return to homepage
    if (e.key === 'Escape' && projectState.currentView !== 'homepage') {
        e.preventDefault();
        projectState.setState('homepage');
        window.scrollTo(0, 0);
    }
});

// Improve tab navigation order
// Add tabindex to ensure logical order
function setTabOrder() {
    const breadcrumb = document.querySelector('.breadcrumb-nav a');
    const fileLinks = document.querySelectorAll('#file-list a');
    const backButton = document.getElementById('back-to-project');
    const homeButton = document.getElementById('home-button');
    const printButton = document.getElementById('print-button');

    if (breadcrumb) breadcrumb.tabIndex = 0;
    fileLinks.forEach(link => link.tabIndex = 0);
    if (backButton) backButton.tabIndex = 0;
    if (homeButton) homeButton.tabIndex = 0;
    if (printButton) printButton.tabIndex = 0;
}

// Call after project is loaded
// (add to projectState.updateUI or similar)
```

**Expected Outcome:** Keyboard users can navigate without issues

**Complexity:** Medium

---

### Task 6.2: Improve Focus States
**What:** Make focused elements more visible

**Why:** Keyboard users need clear visual indication of focused element

**How:**

In `static/css/style.css`, add:

```css
/* Focus States for Accessibility */
a:focus,
button:focus,
input:focus,
select:focus,
textarea:focus {
    outline: 3px solid var(--accent-color);
    outline-offset: 2px;
}

.project-nav-links a:focus {
    background-color: rgba(255, 179, 71, 0.2);
    outline: 2px solid var(--accent-color);
}

.breadcrumb-list a:focus {
    outline: 2px solid var(--accent-color);
    border-radius: 3px;
}

.btn:focus {
    outline: 3px solid var(--accent-color);
    outline-offset: 2px;
}
```

**Expected Outcome:** Clear visual feedback for keyboard navigation

**Complexity:** Low

---

### Task 6.3: Verify Color Contrast
**What:** Ensure all text meets WCAG AA contrast requirements

**Why:** Accessibility and readability

**How:**

Review these elements and ensure they meet 4.5:1 contrast ratio:
1. Active file link text on background - currently uses amber on light bg (check ratio)
2. File link hover states - amber on white (should be fine)
3. Breadcrumb links - primary color on light bg (should be fine)

If needed, update colors in `style.css`:
```css
/* If current amber doesn't meet ratio, use darker version */
/* var(--accent-color): #ffb347 */
/* Alternative: #ff9500 (darker amber) */
```

**Expected Outcome:** WCAG AA contrast compliance

**Complexity:** Low

---

## Phase 7: Testing & Refinement (Priority: MEDIUM)
**Goal:** Ensure everything works correctly
**Estimated Time:** 2-3 hours

### Task 7.1: Manual Testing Checklist
**What:** Test all functionality across devices and browsers

**Checklist:**
- [ ] Desktop (Chrome, Firefox, Safari): All navigation flows work
- [ ] Tablet (iPad): Touch targets are adequate (44px minimum), no horizontal scroll
- [ ] Mobile (iPhone): Layout is clean, buttons are accessible
- [ ] Screen reader (NVDA/JAWS on Windows, VoiceOver on Mac): Page structure makes sense
- [ ] Keyboard only: Can navigate entire site without mouse
- [ ] Print: Page prints cleanly
- [ ] All projects load correctly
- [ ] All files load correctly
- [ ] GEMINI pages load correctly
- [ ] Breadcrumb updates correctly
- [ ] Badges display correctly
- [ ] Colors match brand

**How:**
1. Go through each item systematically
2. Document any issues
3. Fix issues before moving to next phase

**Expected Outcome:** Verified functionality across platforms

**Complexity:** Medium (time-consuming but straightforward)

---

### Task 7.2: Accessibility Audit
**What:** Verify WCAG 2.1 AA compliance

**How:**
1. Use Axe DevTools browser extension (free)
2. Test each page state:
   - Homepage
   - Project overview
   - Project file
   - GEMINI page
3. Document issues
4. Fix any critical issues

**Expected Outcome:** Accessibility compliant site

**Complexity:** Low

---

## Summary: What Gets Done When

### Day 1: Foundation (4-5 hours)
- Remove sidebar (Task 1.1)
- Fix semantic HTML structure (Task 1.2)
- Fix file list structure (Task 1.3)
- Implement state management (Tasks 2.1, 2.2)

**Result:** Clean, accessible HTML with predictable state management

### Day 2: Brand Integration (3-4 hours)
- Add project metadata API (Task 3.1)
- Add discipline badges (Tasks 3.2, 3.3)
- Implement breadcrumb (Tasks 4.1, 4.2)

**Result:** Project pages now reflect discipline context and show user location

### Day 3: Mobile & Accessibility (2-3 hours)
- Mobile responsiveness (Tasks 5.1, 5.2)
- Keyboard navigation (Tasks 6.1, 6.2)
- Color contrast review (Task 6.3)

**Result:** Fully responsive, keyboard accessible, WCAG AA compliant

### Day 4: Testing & Polish (2-3 hours)
- Manual testing (Task 7.1)
- Accessibility audit (Task 7.2)
- Bug fixes and refinements

**Result:** Production-ready code

---

## Risk Mitigation

**Potential Issues & Mitigation:**

1. **Breaking existing navigation** → Test thoroughly on each step, keep git history
2. **ARIA attributes wrong** → Reference examples in analysis, test with screen reader
3. **Mobile layout broken** → Test on real devices (not just browser dev tools)
4. **Performance regression** → Monitor network tab while testing
5. **State bugs** → Log projectState changes during testing

**Recommendations:**
- Commit after each major task
- Test after each phase before moving forward
- Use git branches if making big changes

---

## Success Criteria

When complete, project pages should:
- ✅ Use semantic HTML (`<header>`, `<nav>`, `<main>`)
- ✅ Display discipline badges in nav bar
- ✅ Show clear breadcrumb navigation
- ✅ Have proper ARIA labels and landmarks
- ✅ Support keyboard navigation (Tab, Escape)
- ✅ Work on mobile without horizontal scroll
- ✅ Meet WCAG 2.1 AA accessibility standards
- ✅ Feel visually consistent with homepage
- ✅ Have predictable, testable state management
- ✅ No console errors or warnings

---

## Ready to Proceed?

This plan is comprehensive but sequenced pragmatically. Each phase builds on the previous one, so you can stop at any point and have a working (and improved) site.

**Questions before starting:**
1. Do you want to implement all phases, or start with Phase 1-3 (foundation + brand)?
2. Are you okay with temporary git commits during development?
3. Do you want to test on real devices or just browser dev tools?
4. Should we set a specific deadline?

Let me know and we'll begin!
