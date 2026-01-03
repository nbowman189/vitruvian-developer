/**
 * Manage Behaviors Page JavaScript
 * Handles CRUD operations, icon picker, color picker, and drag-and-drop reordering
 */

// ==================== Constants ====================

const COMMON_ICONS = [
    'star', 'heart', 'fire', 'lightning', 'trophy',
    'book', 'pen', 'laptop', 'code', 'briefcase',
    'calendar', 'clock', 'alarm', 'stopwatch', 'hourglass',
    'cup-hot', 'egg-fried', 'apple', 'droplet', 'moon',
    'sun', 'cloud', 'umbrella', 'bicycle', 'rocket',
    'music-note', 'camera', 'palette', 'chat', 'people',
    'house', 'tree', 'flower', 'bug', 'gem'
];

const COLOR_PALETTE = [
    { name: 'Blue', hex: '#2563eb' },
    { name: 'Indigo', hex: '#4f46e5' },
    { name: 'Purple', hex: '#9333ea' },
    { name: 'Pink', hex: '#ec4899' },
    { name: 'Red', hex: '#ef4444' },
    { name: 'Orange', hex: '#f97316' },
    { name: 'Amber', hex: '#f59e0b' },
    { name: 'Yellow', hex: '#eab308' },
    { name: 'Lime', hex: '#84cc16' },
    { name: 'Green', hex: '#22c55e' },
    { name: 'Emerald', hex: '#10b981' },
    { name: 'Teal', hex: '#14b8a6' },
    { name: 'Cyan', hex: '#06b6d4' },
    { name: 'Sky', hex: '#0ea5e9' },
    { name: 'Slate', hex: '#64748b' },
    { name: 'Gray', hex: '#6b7280' },
    { name: 'Zinc', hex: '#71717a' },
    { name: 'Stone', hex: '#78716c' }
];

// ==================== State ====================

let allBehaviors = [];
let currentView = 'active';
let draggedElement = null;
let originalOrder = [];
let behaviorToArchive = null;

// ==================== Page Initialization ====================

document.addEventListener('DOMContentLoaded', async () => {
    await loadBehaviors();
    initDragAndDrop();
    initIconPicker();
    initColorPicker();
    initEventListeners();

    // Expose functions to global scope for inline onclick handlers
    window.openAddModal = openAddModal;
    window.editBehavior = editBehavior;
    window.saveBehavior = saveBehavior;
    window.archiveBehavior = archiveBehavior;
    window.confirmArchive = confirmArchive;
    window.restoreBehavior = restoreBehavior;
    window.openIconPicker = openIconPicker;
    window.selectIcon = selectIcon;
    window.filterIcons = filterIcons;
    window.selectColor = selectColor;
    window.formatCategoryLabel = formatCategoryLabel;
});

function initEventListeners() {
    // Add behavior button
    document.getElementById('add-behavior-btn').addEventListener('click', openAddModal);

    // View toggles
    document.querySelectorAll('[data-view]').forEach(btn => {
        btn.addEventListener('click', (e) => switchView(e.target.dataset.view));
    });

    // Color input sync
    const colorInput = document.getElementById('behavior-color');
    const colorHexInput = document.getElementById('behavior-color-hex');

    if (colorInput && colorHexInput) {
        colorInput.addEventListener('input', (e) => {
            const hex = e.target.value;
            colorHexInput.value = hex;
            selectColor(hex);
        });

        colorHexInput.addEventListener('input', (e) => {
            const hex = e.target.value;
            if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
                colorInput.value = hex;
                selectColor(hex);
            }
        });
    }
}

// ==================== Data Loading ====================

async function loadBehaviors() {
    try {
        const response = await API.get('/api/behavior/definitions?include_inactive=true');
        allBehaviors = response.data;
        console.log('Loaded behaviors:', allBehaviors); // Debug logging
        renderBehaviors();
    } catch (error) {
        console.error('Failed to load behaviors:', error);
        showToast('Failed to load behaviors', 'error');
    }
}

function renderBehaviors() {
    const container = document.getElementById('behaviors-container');
    const emptyState = document.getElementById('empty-state');

    // Filter based on current view
    const behaviors = allBehaviors
        .filter(b => currentView === 'active' ? b.is_active : !b.is_active)
        .sort((a, b) => a.display_order - b.display_order);

    // Update count badge
    document.getElementById('behavior-count').textContent = behaviors.length;

    // Show empty state or behaviors
    if (behaviors.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    container.style.display = 'block';
    emptyState.style.display = 'none';

    // Render behavior cards
    container.innerHTML = behaviors.map(behavior => {
        // Strip 'bi-' prefix if it exists in icon field
        const iconName = behavior.icon ? behavior.icon.replace(/^bi-/, '') : 'star';

        return `
        <div class="behavior-card" data-behavior-id="${behavior.id}" draggable="true">
            <div class="drag-handle">
                <i class="bi bi-grip-vertical"></i>
            </div>
            <div class="behavior-icon" style="background-color: ${behavior.color};">
                <i class="bi bi-${iconName}"></i>
            </div>
            <div class="behavior-info">
                <h5>${behavior.name}</h5>
                <p class="text-muted">${behavior.description || 'No description'}</p>
                <div class="behavior-meta">
                    <span class="badge bg-${getCategoryColor(behavior.category)}">${formatCategoryLabel(behavior.category)}</span>
                    <span class="target-badge">
                        <i class="bi bi-target"></i> ${behavior.target_frequency}x/week
                    </span>
                </div>
            </div>
            <div class="behavior-actions">
                <button type="button" class="btn-icon" onclick="editBehavior(${behavior.id})" title="Edit">
                    <i class="bi bi-pencil"></i>
                </button>
                ${currentView === 'active' ?
                    `<button type="button" class="btn-icon" onclick="archiveBehavior(${behavior.id})" title="Archive">
                        <i class="bi bi-archive"></i>
                    </button>` :
                    `<button type="button" class="btn-icon" onclick="restoreBehavior(${behavior.id})" title="Restore">
                        <i class="bi bi-arrow-counterclockwise"></i>
                    </button>`}
            </div>
        </div>
        `;
    }).join('');
}

function switchView(view) {
    currentView = view;
    document.querySelectorAll('[data-view]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    renderBehaviors();
}

// ==================== Icon Picker ====================

function initIconPicker() {
    const iconGrid = document.querySelector('#icon-picker-dropdown .icon-grid');
    if (!iconGrid) return;

    COMMON_ICONS.forEach(icon => {
        const iconBtn = document.createElement('button');
        iconBtn.type = 'button';
        iconBtn.className = 'icon-option';
        iconBtn.dataset.icon = icon;
        iconBtn.innerHTML = `<i class="bi bi-${icon}"></i>`;
        iconBtn.title = icon;
        iconBtn.onclick = () => selectIcon(icon);

        iconGrid.appendChild(iconBtn);
    });
}

function openIconPicker() {
    const dropdown = document.getElementById('icon-picker-dropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
}

function selectIcon(iconName) {
    document.getElementById('behavior-icon').value = iconName;
    document.getElementById('selected-icon-preview').className = `bi bi-${iconName}`;
    document.getElementById('icon-picker-dropdown').style.display = 'none';
}

function filterIcons(searchTerm) {
    const icons = document.querySelectorAll('.icon-option');
    const term = searchTerm.toLowerCase();

    icons.forEach(icon => {
        const iconName = icon.dataset.icon;
        icon.style.display = iconName.includes(term) ? 'inline-block' : 'none';
    });
}

// ==================== Color Picker ====================

function initColorPicker() {
    const swatchContainer = document.querySelector('.color-swatches');
    if (!swatchContainer) return;

    COLOR_PALETTE.forEach(color => {
        const swatch = document.createElement('button');
        swatch.type = 'button';
        swatch.className = 'color-swatch';
        swatch.style.backgroundColor = color.hex;
        swatch.title = color.name;
        swatch.dataset.color = color.hex;
        swatch.onclick = () => selectColor(color.hex);

        swatchContainer.appendChild(swatch);
    });
}

function selectColor(hexColor) {
    document.getElementById('behavior-color').value = hexColor;
    document.getElementById('behavior-color-hex').value = hexColor;

    // Update active swatch
    document.querySelectorAll('.color-swatch').forEach(swatch => {
        swatch.classList.toggle('active', swatch.dataset.color === hexColor);
    });
}

// ==================== Drag and Drop ====================

function initDragAndDrop() {
    const container = document.getElementById('behaviors-container');

    container.addEventListener('dragstart', handleDragStart);
    container.addEventListener('dragover', handleDragOver);
    container.addEventListener('drop', handleDrop);
    container.addEventListener('dragend', handleDragEnd);
}

function handleDragStart(e) {
    if (!e.target.classList.contains('behavior-card')) return;

    draggedElement = e.target;
    e.target.classList.add('dragging');

    // Store original order for rollback on error
    originalOrder = Array.from(document.querySelectorAll('.behavior-card'))
        .map(card => card.dataset.behaviorId);
}

function handleDragOver(e) {
    e.preventDefault();

    const afterElement = getDragAfterElement(e.clientY);
    const container = document.getElementById('behaviors-container');

    if (afterElement == null) {
        container.appendChild(draggedElement);
    } else {
        container.insertBefore(draggedElement, afterElement);
    }
}

function getDragAfterElement(y) {
    const cards = Array.from(document.querySelectorAll('.behavior-card:not(.dragging)'));

    return cards.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function handleDrop(e) {
    e.preventDefault();
}

async function handleDragEnd(e) {
    e.target.classList.remove('dragging');

    // Get new order
    const newOrder = Array.from(document.querySelectorAll('.behavior-card'))
        .map((card, index) => ({
            id: parseInt(card.dataset.behaviorId),
            display_order: index
        }));

    // Save to backend
    try {
        await API.put('/api/behavior/definitions/reorder', { order: newOrder });
        showToast('Order saved successfully', 'success');
    } catch (error) {
        console.error('Failed to save order:', error);
        showToast('Failed to save order', 'error');

        // Rollback to original order
        restoreOriginalOrder();
    }
}

function restoreOriginalOrder() {
    const container = document.getElementById('behaviors-container');
    const cards = Array.from(document.querySelectorAll('.behavior-card'));

    originalOrder.forEach(id => {
        const card = cards.find(c => c.dataset.behaviorId === id);
        if (card) container.appendChild(card);
    });
}

// ==================== CRUD Operations ====================

function openAddModal() {
    document.getElementById('modal-title').textContent = 'Add Behavior';
    document.getElementById('save-btn-text').textContent = 'Add Behavior';
    document.getElementById('behavior-form').reset();

    // Set defaults
    selectIcon('star');
    selectColor('#2563eb');

    // Remove edit mode data
    delete document.getElementById('behaviorModal').dataset.editId;

    const modal = new bootstrap.Modal(document.getElementById('behaviorModal'));
    modal.show();
}

function editBehavior(id) {
    const behavior = allBehaviors.find(b => b.id === id);
    if (!behavior) return;

    document.getElementById('modal-title').textContent = 'Edit Behavior';
    document.getElementById('save-btn-text').textContent = 'Save Changes';

    // Populate form
    document.getElementById('behavior-name').value = behavior.name;
    document.getElementById('behavior-description').value = behavior.description || '';
    document.getElementById('behavior-category').value = behavior.category;
    document.getElementById('behavior-frequency').value = behavior.target_frequency;

    selectIcon(behavior.icon);
    selectColor(behavior.color);

    // Store edit ID
    document.getElementById('behaviorModal').dataset.editId = id;

    const modal = new bootstrap.Modal(document.getElementById('behaviorModal'));
    modal.show();
}

async function saveBehavior() {
    const form = document.getElementById('behavior-form');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const data = {
        name: document.getElementById('behavior-name').value,
        description: document.getElementById('behavior-description').value || null,
        category: document.getElementById('behavior-category').value,
        icon: document.getElementById('behavior-icon').value,
        color: document.getElementById('behavior-color').value,
        target_frequency: parseInt(document.getElementById('behavior-frequency').value)
    };

    const editId = document.getElementById('behaviorModal').dataset.editId;

    try {
        if (editId) {
            // Update existing
            await API.put(`/api/behavior/definitions/${editId}`, data);
            showToast('Behavior updated successfully', 'success');
        } else {
            // Create new
            await API.post('/api/behavior/definitions', data);
            showToast('Behavior created successfully', 'success');
        }

        // Reload and close modal
        await loadBehaviors();
        bootstrap.Modal.getInstance(document.getElementById('behaviorModal')).hide();

    } catch (error) {
        console.error('Failed to save behavior:', error);
        showToast(error.response?.data?.message || 'Failed to save behavior', 'error');
    }
}

function archiveBehavior(id) {
    behaviorToArchive = id;
    const modal = new bootstrap.Modal(document.getElementById('archiveModal'));
    modal.show();
}

async function confirmArchive() {
    if (!behaviorToArchive) return;

    try {
        await API.delete(`/api/behavior/definitions/${behaviorToArchive}`);
        showToast('Behavior archived successfully', 'success');
        await loadBehaviors();

        bootstrap.Modal.getInstance(document.getElementById('archiveModal')).hide();
        behaviorToArchive = null;

    } catch (error) {
        console.error('Failed to archive behavior:', error);
        showToast('Failed to archive behavior', 'error');
    }
}

async function restoreBehavior(id) {
    try {
        await API.put(`/api/behavior/definitions/${id}`, { is_active: true });
        showToast('Behavior restored successfully', 'success');
        await loadBehaviors();
    } catch (error) {
        console.error('Failed to restore behavior:', error);
        showToast('Failed to restore behavior', 'error');
    }
}

// ==================== Helper Functions ====================

function getCategoryColor(category) {
    const colors = {
        health: 'danger',
        fitness: 'primary',
        nutrition: 'success',
        learning: 'info',
        productivity: 'warning',
        wellness: 'secondary',
        custom: 'dark'
    };
    return colors[category] || 'secondary';
}

function formatCategoryLabel(category) {
    const labels = {
        health: 'Health',
        fitness: 'Fitness',
        nutrition: 'Nutrition',
        learning: 'Learning',
        productivity: 'Productivity',
        wellness: 'Wellness',
        custom: 'Custom'
    };
    return labels[category] || category;
}

function showToast(message, type = 'info') {
    // Use common.js toast if available, otherwise console log
    if (window.Toast && typeof window.Toast.show === 'function') {
        window.Toast.show(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}
