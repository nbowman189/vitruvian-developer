/**
 * Convert filename to title case
 * @param {string} filename - Filename with extension (e.g., "my-file.md")
 * @returns {string} Title case without extension (e.g., "My File")
 */
function filenameToTitle(filename) {
    return filename
        .replace(/\.md$/, '') // Remove .md extension
        .replace(/[-_]/g, ' ') // Replace hyphens and underscores with spaces
        .replace(/\b\w/g, char => char.toUpperCase()); // Capitalize first letter of each word
}

/**
 * Convert project name to title case
 * @param {string} projectName - Project name with underscores (e.g., "Health_and_Fitness")
 * @returns {string} Title case (e.g., "Health And Fitness")
 */
function projectToTitle(projectName) {
    return projectName
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
}
