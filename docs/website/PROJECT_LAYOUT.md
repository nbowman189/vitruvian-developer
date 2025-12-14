# Project Layout Update: Analysis and Plan

## Analysis of Current Project Presentation Structure

### Backend (`website/app.py`)

1.  **Hardcoded Project Data:** The `FEATURED_PROJECTS` list is directly embedded in `app.py`. This couples content tightly with application logic, making updates cumbersome as they require modifying Python code and redeploying the application.
2.  **File-Browser API:** The API endpoints (`/api/project/<project_name>/files`, `/api/project/<project_name>/file/<path:file_path>`) primarily serve as a file browser, returning lists of Markdown files or their raw content.
3.  **The Gap:** The current backend lacks a mechanism to provide a structured narrative (problem, process, solution, outcome) for each project, which is crucial for a compelling portfolio.

### Frontend (`website/templates/index.html`)

1.  **JavaScript-driven Content:** Both the "Featured Projects" (`#portfolio-grid`) and "All Projects" (`#all-projects-list`) sections are dynamically populated by JavaScript.
2.  **Featured Projects:** This section currently displays hardcoded `title` and `description` from the `FEATURED_PROJECTS` list in `app.py`. It provides a high-level summary but lacks depth.
3.  **All Projects:** This section functions as a basic file list, offering no narrative or context beyond the file names themselves.
4.  **The Presentation Gap:** Neither section effectively presents projects as rich case studies, which is the standard for professional portfolios.

### Overall Comparison to Best Practices

*   **Current Site:** Presents projects either as hardcoded, high-level summaries or as raw file lists. It shows the "what" (the files) but largely misses the "why" and the "so what" (the problem, process, and impact).
*   **Best Practices (from Webflow article):** Emphasize presenting each project as a rich, self-contained case study. This involves telling a story with a clear structure (Problem, Process, Solution, Outcome), using strong visuals, and focusing on the measurable results and impact of the work.

**Core Problem:** The current structure separates the *idea* of a project (the hardcoded summary) from its *content* (the Markdown files). A proper case study needs to integrate these elements to tell a compelling story.

## Proposed Plan to Enhance Project Presentation Structure

This plan is a pragmatic, step-by-step refactoring that builds upon the existing architecture to transform the portfolio from a file browser into a showcase of case studies.

1.  **Establish a Content Standard (The Case Study File):**
    *   **Action:** For each project directory (e.g., `AI_Development`, `Health_and_Fitness`), create a single, standardized Markdown file named `_project_summary.md`. The underscore (`_`) is used to ensure it sorts to the top and signifies its special purpose.
    *   **Content:** This file will use YAML front matter to store structured metadata (e.g., `title`, `description`, `technologies`, `role`, `problem`, `solution`, `outcome`). The main body of the Markdown file will contain the detailed, long-form narrative of the case study.
    *   **Benefit:** This centralizes project content, moving it out of `app.py` and placing it directly within the project's directory, making it easier to manage and update.

2.  **Refactor the Backend (Serve Case Studies, Not Files):**
    *   **Action:** Modify the `/api/featured-projects` endpoint (and potentially create a new `/api/project/<project_name>/summary` endpoint). This endpoint will scan project directories, locate and parse the `_project_summary.md` file for each project, extract the YAML front matter, and convert the Markdown body to HTML. It will then return this structured case study data.
    *   **Benefit:** This makes the portfolio dynamic. Adding a new featured project will only require creating a new project folder with its `_project_summary.md` file, eliminating the need to modify and redeploy `app.py`.

3.  **Enhance the Frontend (Display Case Studies):**
    *   **Action:** Update the JavaScript responsible for populating the `#portfolio-grid` to consume the richer case study data from the refactored API endpoint. Additionally, create a dedicated frontend template (e.g., `project_case_study.html`) for displaying the full, detailed case study. When a user clicks on a project, they will be directed to this new view, which will present the title, description, technologies, and the comprehensive narrative from the Markdown body in a visually appealing format.
    *   **Benefit:** This aligns the portfolio with best practices, allowing for a compelling, narrative-driven presentation of each project, effectively showcasing problem-solving skills and project impact.

### Why this plan is the right approach:

*   **Maintainability:** Separates content from application logic, allowing for easier updates and management of portfolio entries.
*   **Scalability:** Simplifies the process of adding new projects; just create a new folder and a `_project_summary.md` file.
*   **Effectiveness:** Transforms the portfolio into a powerful storytelling tool, demonstrating expertise and project impact in a way that resonates with potential clients or employers.
*   **Pragmatism:** Builds upon the existing Flask and Markdown-based architecture, avoiding a complete rewrite while significantly enhancing functionality.
