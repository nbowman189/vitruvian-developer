/**
 * Common JavaScript utilities for Vitruvian Tracker
 * Shared functions used across multiple pages
 */

// API Base URL
const API_BASE = window.location.origin;

/**
 * API Helper Functions
 */
const API = {
    /**
     * Make a GET request to the API
     * @param {string} endpoint - API endpoint path
     * @returns {Promise} Response data
     */
    async get(endpoint) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`GET ${endpoint} failed:`, error);
            throw error;
        }
    },

    /**
     * Make a POST request to the API
     * @param {string} endpoint - API endpoint path
     * @param {Object} data - Request body data
     * @returns {Promise} Response data
     */
    async post(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`POST ${endpoint} failed:`, error);
            throw error;
        }
    },

    /**
     * Make a PUT request to the API
     * @param {string} endpoint - API endpoint path
     * @param {Object} data - Request body data
     * @returns {Promise} Response data
     */
    async put(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`PUT ${endpoint} failed:`, error);
            throw error;
        }
    },

    /**
     * Make a DELETE request to the API
     * @param {string} endpoint - API endpoint path
     * @returns {Promise} Response data
     */
    async delete(endpoint) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`DELETE ${endpoint} failed:`, error);
            throw error;
        }
    }
};

/**
 * Date/Time Utility Functions
 */
const DateUtils = {
    /**
     * Format date as YYYY-MM-DD
     * @param {Date} date - Date object
     * @returns {string} Formatted date
     */
    formatDate(date) {
        return date.toISOString().split('T')[0];
    },

    /**
     * Format date for display (e.g., "Jan 15, 2024")
     * @param {string|Date} date - Date string or object
     * @returns {string} Formatted date
     */
    formatDateDisplay(date) {
        if (typeof date === 'string') {
            // Parse YYYY-MM-DD format directly to avoid timezone issues
            const parts = date.split('T')[0].split('-');
            if (parts.length === 3) {
                const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
                return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
            }
        }
        const d = typeof date === 'string' ? new Date(date) : date;
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    },

    /**
     * Format time (e.g., "2:30 PM")
     * @param {string} time - Time string (HH:MM)
     * @returns {string} Formatted time
     */
    formatTime(time) {
        if (!time) return '';
        const [hours, minutes] = time.split(':');
        const h = parseInt(hours);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const displayHours = h % 12 || 12;
        return `${displayHours}:${minutes} ${ampm}`;
    },

    /**
     * Get today's date as YYYY-MM-DD
     * @returns {string} Today's date
     */
    getToday() {
        return this.formatDate(new Date());
    },

    /**
     * Get date N days ago
     * @param {number} days - Number of days
     * @returns {string} Date string
     */
    getDaysAgo(days) {
        const date = new Date();
        date.setDate(date.getDate() - days);
        return this.formatDate(date);
    },

    /**
     * Calculate days between two dates
     * @param {string|Date} date1 - First date
     * @param {string|Date} date2 - Second date
     * @returns {number} Number of days
     */
    daysBetween(date1, date2) {
        const d1 = typeof date1 === 'string' ? new Date(date1) : date1;
        const d2 = typeof date2 === 'string' ? new Date(date2) : date2;
        const diffTime = Math.abs(d2 - d1);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }
};

/**
 * Form Validation Utilities
 */
const FormUtils = {
    /**
     * Validate form and show Bootstrap validation feedback
     * @param {HTMLFormElement} form - Form element
     * @returns {boolean} True if valid
     */
    validateForm(form) {
        form.classList.add('was-validated');
        return form.checkValidity();
    },

    /**
     * Reset form validation state
     * @param {HTMLFormElement} form - Form element
     */
    resetValidation(form) {
        form.classList.remove('was-validated');
    },

    /**
     * Get form data as object
     * @param {HTMLFormElement} form - Form element
     * @returns {Object} Form data
     */
    getFormData(form) {
        const formData = new FormData(form);
        const data = {};
        for (const [key, value] of formData.entries()) {
            data[key] = value;
        }
        return data;
    },

    /**
     * Populate form with data
     * @param {HTMLFormElement} form - Form element
     * @param {Object} data - Data to populate
     */
    populateForm(form, data) {
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = data[key];
                } else {
                    input.value = data[key] || '';
                }
            }
        });
    },

    /**
     * Clear form fields
     * @param {HTMLFormElement} form - Form element
     */
    clearForm(form) {
        form.reset();
        this.resetValidation(form);
    }
};

/**
 * UI Utility Functions
 */
const UIUtils = {
    /**
     * Show loading spinner
     * @param {HTMLElement} element - Container element
     */
    showLoading(element) {
        element.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    },

    /**
     * Show error message
     * @param {HTMLElement} element - Container element
     * @param {string} message - Error message
     */
    showError(element, message) {
        element.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle"></i> ${message}
            </div>
        `;
    },

    /**
     * Show empty state
     * @param {HTMLElement} element - Container element
     * @param {string} message - Empty state message
     */
    showEmpty(element, message) {
        element.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="bi bi-inbox" style="font-size: 3rem;"></i>
                <p class="mt-3">${message}</p>
            </div>
        `;
    },

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, warning, info)
     */
    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();

        // Remove toast after hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
};

/**
 * Number Formatting Utilities
 */
const NumberUtils = {
    /**
     * Format number with commas
     * @param {number} num - Number to format
     * @returns {string} Formatted number
     */
    formatNumber(num) {
        return num.toLocaleString('en-US');
    },

    /**
     * Format number to fixed decimal places
     * @param {number} num - Number to format
     * @param {number} decimals - Decimal places
     * @returns {string} Formatted number
     */
    formatDecimal(num, decimals = 1) {
        return parseFloat(num).toFixed(decimals);
    },

    /**
     * Calculate percentage
     * @param {number} value - Current value
     * @param {number} total - Total value
     * @returns {number} Percentage
     */
    calculatePercentage(value, total) {
        if (total === 0) return 0;
        return Math.round((value / total) * 100);
    }
};

/**
 * Modal Utilities
 */
const ModalUtils = {
    /**
     * Show modal
     * @param {string} modalId - Modal element ID
     */
    show(modalId) {
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
    },

    /**
     * Hide modal
     * @param {string} modalId - Modal element ID
     */
    hide(modalId) {
        const modalElement = document.getElementById(modalId);
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    }
};

/**
 * Confirmation Dialog
 * @param {string} message - Confirmation message
 * @param {Function} onConfirm - Callback on confirm
 * @param {Function} onCancel - Callback on cancel (optional)
 */
function confirmDialog(message, onConfirm, onCancel = null) {
    const result = confirm(message);
    if (result && onConfirm) {
        onConfirm();
    } else if (!result && onCancel) {
        onCancel();
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize page - call this on DOMContentLoaded
 */
function initializePage() {
    initTooltips();

    // Set current date in display
    const currentDateEl = document.getElementById('current-date');
    if (currentDateEl) {
        currentDateEl.textContent = DateUtils.formatDateDisplay(new Date());
    }
}

// Auto-initialize on DOM load
document.addEventListener('DOMContentLoaded', initializePage);
