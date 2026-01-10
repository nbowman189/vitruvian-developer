/**
 * Health Metrics Page JavaScript
 * Handles loading, displaying, and managing health metrics data
 */

// State
let currentPage = 1;
let perPage = 20;
let dateRange = 30;
let bodyfatOnly = false;
let startDate = null;
let endDate = null;
let metricsData = [];
let weightChart = null;
let bodyfatChart = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async function() {
    initializeFilters();
    initializeForm();
    await loadMetrics();
});

/**
 * Initialize filter event handlers
 */
function initializeFilters() {
    const dateRangeFilter = document.getElementById('date-range-filter');
    const bodyfatOnlyFilter = document.getElementById('bodyfat-only-filter');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const exportBtn = document.getElementById('export-csv-btn');

    if (dateRangeFilter) {
        dateRangeFilter.addEventListener('change', async function() {
            const value = this.value;
            const customStartGroup = document.getElementById('custom-date-range');
            const customEndGroup = document.getElementById('custom-date-range-end');

            if (value === 'custom') {
                customStartGroup.style.display = 'block';
                customEndGroup.style.display = 'block';
            } else {
                customStartGroup.style.display = 'none';
                customEndGroup.style.display = 'none';
                dateRange = value === 'all' ? null : parseInt(value);
                startDate = null;
                endDate = null;
                currentPage = 1;
                await loadMetrics();
            }
        });
    }

    if (bodyfatOnlyFilter) {
        bodyfatOnlyFilter.addEventListener('change', async function() {
            bodyfatOnly = this.checked;
            currentPage = 1;
            await loadMetrics();
        });
    }

    if (startDateInput && endDateInput) {
        const applyCustomRange = async () => {
            if (startDateInput.value && endDateInput.value) {
                startDate = startDateInput.value;
                endDate = endDateInput.value;
                dateRange = null;
                currentPage = 1;
                await loadMetrics();
            }
        };
        startDateInput.addEventListener('change', applyCustomRange);
        endDateInput.addEventListener('change', applyCustomRange);
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCSV);
    }

    // Initialize sortable columns
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', function() {
            const column = this.dataset.column;
            sortTable(column);
        });
    });
}

/**
 * Initialize form event handlers
 */
function initializeForm() {
    const form = document.getElementById('metric-form');
    const addBtn = document.getElementById('add-metric-btn');

    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    if (addBtn) {
        addBtn.addEventListener('click', function() {
            resetForm();
            document.getElementById('metricModalLabel').textContent = 'Add Health Metric';
            document.getElementById('metric-date').value = DateUtils.getToday();
        });
    }
}

/**
 * Load metrics from API
 */
async function loadMetrics() {
    try {
        showTableLoading();

        // Build query params
        let params = new URLSearchParams();
        params.append('page', currentPage);
        params.append('per_page', perPage);
        params.append('sort', 'desc');

        if (dateRange && !startDate) {
            const end = new Date();
            const start = new Date();
            start.setDate(start.getDate() - dateRange);
            params.append('start_date', DateUtils.formatDate(start));
            params.append('end_date', DateUtils.formatDate(end));
        } else if (startDate && endDate) {
            params.append('start_date', startDate);
            params.append('end_date', endDate);
        }

        const response = await API.get(`/api/health/metrics?${params.toString()}`);

        // Handle paginated response - data is in response.data.items
        metricsData = response.data?.items || response.data || [];
        const total = response.data?.total || metricsData.length;

        renderTable(metricsData);
        renderPagination(total);
        updateSummary(response.data);
        await loadCharts();

    } catch (error) {
        console.error('Error loading metrics:', error);
        showTableError('Failed to load metrics. Please try again.');
    }
}

/**
 * Render metrics table
 */
function renderTable(metrics) {
    const tbody = document.getElementById('metrics-table-body');

    if (!metrics || metrics.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                    <p class="mt-2 mb-0">No metrics found</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = metrics.map(metric => {
        const leanMass = metric.weight_lbs && metric.body_fat_percentage
            ? (metric.weight_lbs * (1 - metric.body_fat_percentage / 100)).toFixed(1)
            : '-';

        return `
            <tr data-id="${metric.id}">
                <td>${DateUtils.formatDateDisplay(metric.recorded_date)}</td>
                <td>${metric.weight_lbs ? metric.weight_lbs.toFixed(1) : '-'}</td>
                <td>${metric.body_fat_percentage ? metric.body_fat_percentage.toFixed(1) + '%' : '-'}</td>
                <td>${leanMass !== '-' ? leanMass + ' lbs' : '-'}</td>
                <td class="notes-cell">${metric.notes || '-'}</td>
                <td class="actions-col">
                    <button class="btn btn-sm btn-outline-primary" onclick="editMetric(${metric.id})" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmDelete(${metric.id})" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Show loading state in table
 */
function showTableLoading() {
    const tbody = document.getElementById('metrics-table-body');
    tbody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </td>
        </tr>
    `;
}

/**
 * Show error in table
 */
function showTableError(message) {
    const tbody = document.getElementById('metrics-table-body');
    tbody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-4">
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-exclamation-triangle"></i> ${message}
                </div>
            </td>
        </tr>
    `;
}

/**
 * Update summary cards
 */
function updateSummary(data) {
    const metrics = data?.items || data || [];

    // Get latest metric
    const latest = metrics.length > 0 ? metrics[0] : null;
    const oldest = metrics.length > 1 ? metrics[metrics.length - 1] : null;

    // Current weight
    const currentWeightEl = document.getElementById('current-weight');
    const weightChangeEl = document.getElementById('weight-change');
    if (latest?.weight_lbs) {
        currentWeightEl.textContent = latest.weight_lbs.toFixed(1) + ' lbs';
        if (oldest?.weight_lbs) {
            const change = latest.weight_lbs - oldest.weight_lbs;
            weightChangeEl.textContent = (change >= 0 ? '+' : '') + change.toFixed(1) + ' lbs';
            weightChangeEl.className = 'summary-change ' + (change < 0 ? 'positive' : change > 0 ? 'negative' : '');
        }
    } else {
        currentWeightEl.textContent = '--';
        weightChangeEl.textContent = '--';
    }

    // Current body fat
    const currentBfEl = document.getElementById('current-bodyfat');
    const bfChangeEl = document.getElementById('bodyfat-change');
    if (latest?.body_fat_percentage) {
        currentBfEl.textContent = latest.body_fat_percentage.toFixed(1) + '%';
        if (oldest?.body_fat_percentage) {
            const change = latest.body_fat_percentage - oldest.body_fat_percentage;
            bfChangeEl.textContent = (change >= 0 ? '+' : '') + change.toFixed(1) + '%';
            bfChangeEl.className = 'summary-change ' + (change < 0 ? 'positive' : change > 0 ? 'negative' : '');
        }
    } else {
        currentBfEl.textContent = '--';
        bfChangeEl.textContent = '--';
    }

    // Lean mass
    const leanMassEl = document.getElementById('lean-mass');
    const leanMassChangeEl = document.getElementById('lean-mass-change');
    if (latest?.weight_lbs && latest?.body_fat_percentage) {
        const leanMass = latest.weight_lbs * (1 - latest.body_fat_percentage / 100);
        leanMassEl.textContent = leanMass.toFixed(1) + ' lbs';
        if (oldest?.weight_lbs && oldest?.body_fat_percentage) {
            const oldLeanMass = oldest.weight_lbs * (1 - oldest.body_fat_percentage / 100);
            const change = leanMass - oldLeanMass;
            leanMassChangeEl.textContent = (change >= 0 ? '+' : '') + change.toFixed(1) + ' lbs';
            leanMassChangeEl.className = 'summary-change ' + (change > 0 ? 'positive' : change < 0 ? 'negative' : '');
        }
    } else {
        leanMassEl.textContent = '--';
        leanMassChangeEl.textContent = '--';
    }

    // Total entries
    const totalEntriesEl = document.getElementById('total-entries');
    totalEntriesEl.textContent = data?.total || metrics.length;
}

/**
 * Load and render charts
 */
async function loadCharts() {
    try {
        // Get trend data
        const days = dateRange || 30;
        const response = await API.get(`/api/health/metrics/trend?days=${days}`);
        const trendData = response.data || {};

        renderWeightChart(trendData);
        renderBodyfatChart();
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

/**
 * Render weight trend chart
 */
function renderWeightChart(trendData) {
    const ctx = document.getElementById('weightChart');
    if (!ctx) return;

    // Destroy existing chart
    if (weightChart) {
        weightChart.destroy();
    }

    const dates = trendData.dates || [];
    const weights = trendData.weights || [];

    if (dates.length === 0) {
        ctx.parentElement.innerHTML = '<p class="text-muted text-center py-4">No weight data available</p>';
        return;
    }

    weightChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Weight (lbs)',
                data: weights,
                borderColor: '#1a237e',
                backgroundColor: 'rgba(26, 35, 126, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    type: 'category',
                    title: { display: true, text: 'Date' }
                },
                y: {
                    beginAtZero: false,
                    title: { display: true, text: 'Weight (lbs)' }
                }
            }
        }
    });
}

/**
 * Render body fat chart from loaded metrics data
 */
function renderBodyfatChart() {
    const ctx = document.getElementById('bodyfatChart');
    if (!ctx) return;

    // Destroy existing chart
    if (bodyfatChart) {
        bodyfatChart.destroy();
    }

    // Filter metrics with body fat data
    const bfData = metricsData
        .filter(m => m.body_fat_percentage !== null)
        .reverse();

    if (bfData.length === 0) {
        ctx.parentElement.innerHTML = '<p class="text-muted text-center py-4">No body fat data available</p>';
        return;
    }

    const dates = bfData.map(m => DateUtils.formatDateDisplay(m.recorded_date));
    const values = bfData.map(m => m.body_fat_percentage);

    bodyfatChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Body Fat %',
                data: values,
                borderColor: '#c62828',
                backgroundColor: 'rgba(198, 40, 40, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    type: 'category',
                    title: { display: true, text: 'Date' }
                },
                y: {
                    beginAtZero: false,
                    title: { display: true, text: 'Body Fat %' }
                }
            }
        }
    });
}

/**
 * Render pagination controls
 */
function renderPagination(total) {
    const container = document.getElementById('pagination-container');
    if (!container) return;

    const totalPages = Math.ceil(total / perPage);

    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '<nav aria-label="Metrics pagination"><ul class="pagination justify-content-center">';

    // Previous button
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="goToPage(${currentPage - 1}); return false;">&laquo;</a>
        </li>
    `;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="goToPage(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }

    // Next button
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="goToPage(${currentPage + 1}); return false;">&raquo;</a>
        </li>
    `;

    html += '</ul></nav>';
    container.innerHTML = html;
}

/**
 * Go to specific page
 */
async function goToPage(page) {
    currentPage = page;
    await loadMetrics();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Handle form submission
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const metricId = document.getElementById('metric-id').value;
    const isEdit = !!metricId;

    const data = {
        recorded_date: document.getElementById('metric-date').value,
        weight_lbs: parseFloat(document.getElementById('metric-weight').value) || null,
        body_fat_percentage: parseFloat(document.getElementById('metric-bodyfat').value) || null,
        notes: document.getElementById('metric-notes').value || null
    };

    try {
        let response;
        if (isEdit) {
            response = await API.put(`/api/health/metrics/${metricId}`, data);
        } else {
            response = await API.post('/api/health/metrics', data);
        }

        if (response.success) {
            UIUtils.showToast(isEdit ? 'Metric updated successfully' : 'Metric added successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('metricModal')).hide();
            await loadMetrics();
        } else {
            UIUtils.showToast(response.message || 'Failed to save metric', 'error');
        }
    } catch (error) {
        console.error('Error saving metric:', error);
        UIUtils.showToast('Failed to save metric', 'error');
    }
}

/**
 * Edit a metric
 */
async function editMetric(id) {
    try {
        const response = await API.get(`/api/health/metrics/${id}`);
        const metric = response.data;

        document.getElementById('metric-id').value = metric.id;
        document.getElementById('metric-date').value = metric.recorded_date;
        document.getElementById('metric-weight').value = metric.weight_lbs || '';
        document.getElementById('metric-bodyfat').value = metric.body_fat_percentage || '';
        document.getElementById('metric-notes').value = metric.notes || '';

        document.getElementById('metricModalLabel').textContent = 'Edit Health Metric';
        new bootstrap.Modal(document.getElementById('metricModal')).show();
    } catch (error) {
        console.error('Error loading metric:', error);
        UIUtils.showToast('Failed to load metric', 'error');
    }
}

/**
 * Confirm deletion
 */
function confirmDelete(id) {
    const modal = document.getElementById('deleteMetricModal');
    if (modal) {
        modal.dataset.metricId = id;
        new bootstrap.Modal(modal).show();

        // Attach delete handler
        const confirmBtn = modal.querySelector('.btn-danger');
        confirmBtn.onclick = () => deleteMetric(id);
    } else {
        if (confirm('Are you sure you want to delete this metric?')) {
            deleteMetric(id);
        }
    }
}

/**
 * Delete a metric
 */
async function deleteMetric(id) {
    try {
        const response = await API.delete(`/api/health/metrics/${id}`);

        if (response.success) {
            UIUtils.showToast('Metric deleted successfully', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteMetricModal'));
            if (modal) modal.hide();
            await loadMetrics();
        } else {
            UIUtils.showToast(response.message || 'Failed to delete metric', 'error');
        }
    } catch (error) {
        console.error('Error deleting metric:', error);
        UIUtils.showToast('Failed to delete metric', 'error');
    }
}

/**
 * Reset form to add mode
 */
function resetForm() {
    document.getElementById('metric-id').value = '';
    document.getElementById('metric-form').reset();
}

/**
 * Sort table by column
 */
function sortTable(column) {
    // For now, just reload with different sort order
    // This could be enhanced to sort client-side
    loadMetrics();
}

/**
 * Export data to CSV
 */
function exportToCSV() {
    if (!metricsData || metricsData.length === 0) {
        UIUtils.showToast('No data to export', 'warning');
        return;
    }

    const headers = ['Date', 'Weight (lbs)', 'Body Fat %', 'Lean Mass (lbs)', 'Notes'];
    const rows = metricsData.map(m => {
        const leanMass = m.weight_lbs && m.body_fat_percentage
            ? (m.weight_lbs * (1 - m.body_fat_percentage / 100)).toFixed(1)
            : '';
        return [
            m.recorded_date,
            m.weight_lbs || '',
            m.body_fat_percentage || '',
            leanMass,
            (m.notes || '').replace(/,/g, ';')
        ];
    });

    let csv = headers.join(',') + '\n';
    csv += rows.map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `health-metrics-${DateUtils.getToday()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);

    UIUtils.showToast('CSV exported successfully', 'success');
}
