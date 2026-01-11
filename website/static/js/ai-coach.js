/**
 * AI Coach Chat Interface
 * ========================
 *
 * Handles the complete chat interface for AI coaching:
 * - Conversation management
 * - Message sending/receiving
 * - Function call handling (record previews)
 * - Record editing and saving
 * - Real-time UI updates
 */

class AICoachChat {
    constructor() {
        this.currentConversationId = null;
        this.pendingRecordData = null;
        this.isSending = false;

        this.init();
    }

    /**
     * Initialize the chat interface
     */
    init() {
        this.loadConversations();
        this.setupEventListeners();
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // New conversation button
        document.getElementById('new-conversation-btn').addEventListener('click', () => {
            this.startNewConversation();
        });

        // Chat form submission
        document.getElementById('chat-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Enter key handling (Enter = send, Shift+Enter = new line)
        document.getElementById('message-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });

        // Save record button
        document.getElementById('save-record-btn').addEventListener('click', () => {
            this.saveRecord();
        });
    }

    /**
     * Load user's conversations from API
     */
    async loadConversations() {
        try {
            const response = await fetch('/api/ai-coach/conversations?per_page=50', {
                credentials: 'include'
            });
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to load conversations');
            }

            this.renderConversations(data.data);
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.showError('Failed to load conversations');
        }
    }

    /**
     * Render conversations in sidebar
     */
    renderConversations(conversations) {
        const list = document.getElementById('conversation-list');

        if (conversations.length === 0) {
            list.innerHTML = `
                <div class="loading-state">
                    <i class="bi bi-chat-dots" style="font-size: 3rem; color: #6c757d;"></i>
                    <p style="margin-top: 15px;">No conversations yet</p>
                    <p style="font-size: 0.85rem;">Click "New Chat" to start!</p>
                </div>
            `;
            return;
        }

        list.innerHTML = conversations.map(conv => `
            <div class="conversation-item ${conv.id === this.currentConversationId ? 'active' : ''}"
                 data-conversation-id="${conv.id}">
                <div class="conversation-item-title">${this.escapeHtml(conv.title)}</div>
                <div class="conversation-item-meta">
                    <span><i class="bi bi-chat"></i> ${conv.message_count}</span>
                    <span><i class="bi bi-clipboard-check"></i> ${conv.records_created}</span>
                </div>
            </div>
        `).join('');

        // Add click handlers
        list.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                const convId = parseInt(item.dataset.conversationId);
                this.loadConversation(convId);
            });
        });
    }

    /**
     * Load a specific conversation
     */
    async loadConversation(conversationId) {
        try {
            this.showLoading(true);

            const response = await fetch(`/api/ai-coach/conversations/${conversationId}`, {
                credentials: 'include'
            });
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to load conversation');
            }

            this.currentConversationId = conversationId;
            this.renderMessages(data.data.messages);

            // Update sidebar active state
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.toggle('active',
                    parseInt(item.dataset.conversationId) === conversationId
                );
            });

            // Hide welcome message
            const welcomeMsg = document.getElementById('welcome-message');
            if (welcomeMsg) {
                welcomeMsg.style.display = 'none';
            }

        } catch (error) {
            console.error('Error loading conversation:', error);
            this.showError('Failed to load conversation');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Start a new conversation
     */
    startNewConversation() {
        this.currentConversationId = null;
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = '';

        // Show welcome message
        const welcomeMsg = document.getElementById('welcome-message');
        if (welcomeMsg) {
            welcomeMsg.style.display = 'block';
        }

        // Clear active state in sidebar
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });

        // Focus input
        document.getElementById('message-input').focus();
    }

    /**
     * Handle form submission (send message)
     */
    async handleSubmit() {
        if (this.isSending) return;

        const input = document.getElementById('message-input');
        const message = input.value.trim();

        if (!message) return;

        this.isSending = true;
        const sendBtn = document.getElementById('send-btn');
        sendBtn.disabled = true;

        try {
            // Hide welcome message if showing
            const welcomeMsg = document.getElementById('welcome-message');
            if (welcomeMsg) {
                welcomeMsg.style.display = 'none';
            }

            // Add user message to UI immediately
            this.addMessageToUI('user', message);

            // Clear input
            input.value = '';

            // Show typing indicator
            const typingId = this.addTypingIndicator();

            // Send to API
            const requestBody = {
                message: message
            };

            if (this.currentConversationId) {
                requestBody.conversation_id = this.currentConversationId;
            }

            const response = await fetch('/api/ai-coach/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            // Remove typing indicator
            this.removeTypingIndicator(typingId);

            if (!data.success) {
                // Check for specific error types
                const errorInfo = data.errors?.[0];

                if (errorInfo?.type === 'quota_exhausted') {
                    // Quota exhausted - show countdown
                    const secondsUntilReset = errorInfo.seconds_until_reset;
                    if (secondsUntilReset) {
                        this.showQuotaCountdown(data.message, secondsUntilReset);
                    } else {
                        this.showError(data.message);
                    }
                    return;
                }

                if (errorInfo?.type === 'api_error') {
                    // API error - show detailed info for troubleshooting
                    let errorMsg = data.message;
                    if (errorInfo.error_class) {
                        errorMsg += ` (${errorInfo.error_class})`;
                    }
                    this.showError(errorMsg);
                    return;
                }

                // Generic error - show message from API
                this.showError(data.message || 'Failed to send message');
                return;
            }

            // Update conversation ID if new conversation
            if (!this.currentConversationId) {
                this.currentConversationId = data.data.conversation_id;
                // Reload conversation list to show new conversation
                this.loadConversations();
            }

            // Add assistant response to UI
            this.addMessageToUI('assistant', data.data.response);

            // Handle function call if present
            if (data.data.function_call) {
                this.handleFunctionCall(data.data.function_call);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            // Show the actual error message from the API if available
            const errorMessage = error.message || 'Failed to send message. Please try again.';
            this.showError(errorMessage);
            this.removeTypingIndicator();
        } finally {
            this.isSending = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    /**
     * Convert markdown-style text to HTML
     */
    formatMessageContent(text) {
        // Escape HTML to prevent XSS
        const escapeHtml = (str) => {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        };

        // Escape the text first
        let formatted = escapeHtml(text);

        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Convert *italic* (but not ** bold which we already handled)
        formatted = formatted.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

        // Convert numbered lists (lines starting with "1. ", "2. ", etc.)
        formatted = formatted.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="list-item"><strong>$1.</strong> $2</div>');

        // Convert double newlines to paragraph breaks
        formatted = formatted.replace(/\n\n/g, '</p><p>');

        // Convert single newlines to <br>
        formatted = formatted.replace(/\n/g, '<br>');

        // Wrap in paragraph tags
        formatted = `<p>${formatted}</p>`;

        // Clean up empty paragraphs
        formatted = formatted.replace(/<p><\/p>/g, '');
        formatted = formatted.replace(/<p>\s*<\/p>/g, '');

        return formatted;
    }

    /**
     * Add message to UI
     */
    addMessageToUI(role, content) {
        const messagesContainer = document.getElementById('chat-messages');

        const messageGroup = document.createElement('div');
        messageGroup.className = `message-group ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-robot"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        // Format markdown-style content to HTML for assistant messages
        if (role === 'assistant') {
            bubble.innerHTML = this.formatMessageContent(content);
        } else {
            bubble.textContent = content;
        }

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit'
        });

        messageContent.appendChild(bubble);
        messageContent.appendChild(time);

        if (role === 'assistant') {
            messageGroup.appendChild(avatar);
            messageGroup.appendChild(messageContent);
        } else {
            messageGroup.appendChild(messageContent);
            messageGroup.appendChild(avatar);
        }

        messagesContainer.appendChild(messageGroup);
        this.scrollToBottom();

        return messageContent;
    }

    /**
     * Handle function call from AI (record preview)
     */
    handleFunctionCall(functionCall) {
        const messagesContainer = document.getElementById('chat-messages');
        const lastMessageContent = messagesContainer.querySelector('.message-group:last-child .message-content');

        if (!lastMessageContent) return;

        // Handle batch records specially
        if (functionCall.name === 'create_batch_records') {
            this.handleBatchRecords(functionCall.args, lastMessageContent);
            return;
        }

        // Handle multiple function calls from Gemini
        if (functionCall.name === 'multiple_function_calls') {
            this.handleMultipleFunctionCalls(functionCall.function_calls, lastMessageContent);
            return;
        }

        // Create record preview card
        const previewCard = document.createElement('div');
        previewCard.className = 'record-preview-card';

        const recordType = this.getFriendlyRecordType(functionCall.name);
        const fields = this.formatRecordFields(functionCall.name, functionCall.args);

        previewCard.innerHTML = `
            <h4><i class="bi bi-clipboard-check"></i> ${recordType}</h4>
            <div class="record-preview-fields">
                ${fields}
            </div>
            <div class="record-preview-actions">
                <button class="btn btn-primary btn-sm review-record-btn">
                    <i class="bi bi-pencil"></i> Review & Save
                </button>
            </div>
        `;

        lastMessageContent.appendChild(previewCard);

        // Add click handler
        previewCard.querySelector('.review-record-btn').addEventListener('click', () => {
            this.showRecordModal(functionCall.name, functionCall.args);
        });

        this.scrollToBottom();
    }

    /**
     * Handle multiple function calls from Gemini
     */
    handleMultipleFunctionCalls(functionCalls, containerElement) {
        if (!functionCalls || functionCalls.length === 0) {
            return;
        }

        // Create batch preview card
        const batchCard = document.createElement('div');
        batchCard.className = 'record-preview-card batch-records';

        let recordPreviews = functionCalls.map((fc, idx) => {
            const recordType = this.getFriendlyRecordType(fc.name);
            const fields = this.formatRecordFields(fc.name, fc.args);

            return `
                <div class="batch-record-item">
                    <h5>${idx + 1}. ${recordType}</h5>
                    <div class="record-preview-fields">
                        ${fields}
                    </div>
                </div>
            `;
        }).join('');

        batchCard.innerHTML = `
            <h4><i class="bi bi-stack"></i> Multiple Records (${functionCalls.length})</h4>
            <div class="batch-records-list">
                ${recordPreviews}
            </div>
            <div class="record-preview-actions">
                <button class="btn btn-primary review-record-btn">
                    <i class="bi bi-pencil"></i> Review & Save All
                </button>
            </div>
        `;

        containerElement.appendChild(batchCard);

        // Store function calls for modal
        this.pendingRecordData = { function_calls: functionCalls };

        // Add click handler
        batchCard.querySelector('.review-record-btn').addEventListener('click', () => {
            this.showMultiRecordModal(functionCalls);
        });

        this.scrollToBottom();
    }

    /**
     * Handle batch records display
     */
    handleBatchRecords(args, containerElement) {
        const records = args.records || [];

        if (records.length === 0) {
            return;
        }

        // Create batch preview card
        const batchCard = document.createElement('div');
        batchCard.className = 'record-preview-card batch-records';

        let recordPreviews = records.map((record, idx) => {
            const recordType = this.getFriendlyRecordType(`create_${record.record_type}`);
            const fields = this.formatRecordFields(`create_${record.record_type}`, record.data);

            return `
                <div class="batch-record-item">
                    <h5>${idx + 1}. ${recordType}</h5>
                    <div class="record-preview-fields">
                        ${fields}
                    </div>
                </div>
            `;
        }).join('');

        batchCard.innerHTML = `
            <h4><i class="bi bi-stack"></i> Multiple Records (${records.length})</h4>
            <div class="batch-records-list">
                ${recordPreviews}
            </div>
            <div class="record-preview-actions">
                <button class="btn btn-primary btn-sm review-record-btn">
                    <i class="bi bi-pencil"></i> Review & Save All
                </button>
            </div>
        `;

        containerElement.appendChild(batchCard);

        // Add click handler
        batchCard.querySelector('.review-record-btn').addEventListener('click', () => {
            this.showRecordModal('create_batch_records', args);
        });

        this.scrollToBottom();
    }

    /**
     * Format record fields for preview
     */
    formatRecordFields(functionName, args) {
        const fields = [];

        Object.entries(args).forEach(([key, value]) => {
            if (key === 'exercises' || key === 'action_items') return; // Handle arrays separately

            const label = this.formatFieldLabel(key);
            const formattedValue = this.formatFieldValue(key, value);

            if (formattedValue) {
                fields.push(`
                    <div class="record-field">
                        <div class="record-field-label">${label}:</div>
                        <div class="record-field-value">${formattedValue}</div>
                    </div>
                `);
            }
        });

        return fields.join('');
    }

    /**
     * Show record edit modal
     */
    showRecordModal(functionName, recordData) {
        this.pendingRecordData = { functionName, recordData };

        const modalBody = document.getElementById('record-preview-body');
        modalBody.innerHTML = this.generateRecordForm(functionName, recordData);

        const modal = new bootstrap.Modal(document.getElementById('record-preview-modal'));
        modal.show();
    }

    /**
     * Show modal for multiple function calls from Gemini
     */
    showMultiRecordModal(functionCalls) {
        // Convert multiple function calls to batch records format
        const records = functionCalls.map(fc => ({
            record_type: fc.name.replace('create_', ''),
            data: fc.args
        }));

        this.pendingRecordData = {
            functionName: 'create_batch_records',
            recordData: { records }
        };

        const modalBody = document.getElementById('record-preview-body');
        modalBody.innerHTML = this.generateBatchRecordsForm({ records });

        const modal = new bootstrap.Modal(document.getElementById('record-preview-modal'));
        modal.show();
    }

    /**
     * Generate record edit form
     */
    generateRecordForm(functionName, data) {
        let formHtml = '';

        if (functionName === 'create_batch_records') {
            return this.generateBatchRecordsForm(data);
        }

        switch (functionName) {
            case 'create_health_metric':
                formHtml = this.generateHealthMetricForm(data);
                break;
            case 'create_meal_log':
                formHtml = this.generateMealLogForm(data);
                break;
            case 'create_workout':
                formHtml = this.generateWorkoutForm(data);
                break;
            case 'create_coaching_session':
                formHtml = this.generateCoachingSessionForm(data);
                break;
            case 'create_behavior_definition':
                formHtml = this.generateBehaviorDefinitionForm(data);
                break;
            case 'log_behavior':
                formHtml = this.generateBehaviorLogForm(data);
                break;
            case 'create_document':
                formHtml = this.generateDocumentForm(data);
                break;
        }

        return formHtml;
    }

    /**
     * Generate batch records form with tabs
     */
    generateBatchRecordsForm(data) {
        const records = data.records || [];

        if (records.length === 0) {
            return '<p>No records to display.</p>';
        }

        // Create tab navigation
        let tabNav = '<ul class="nav nav-tabs mb-3" role="tablist">';
        let tabContent = '<div class="tab-content">';

        records.forEach((record, idx) => {
            const recordType = this.getFriendlyRecordType(`create_${record.record_type}`);
            const isActive = idx === 0 ? 'active' : '';

            // Tab button
            tabNav += `
                <li class="nav-item" role="presentation">
                    <button class="nav-link ${isActive}" id="record-tab-${idx}"
                            data-bs-toggle="tab" data-bs-target="#record-pane-${idx}"
                            type="button" role="tab">
                        ${idx + 1}. ${recordType}
                    </button>
                </li>
            `;

            // Tab content
            let recordForm = '';
            switch (record.record_type) {
                case 'health_metric':
                    recordForm = this.generateHealthMetricForm(record.data);
                    break;
                case 'meal_log':
                    recordForm = this.generateMealLogForm(record.data);
                    break;
                case 'workout':
                    recordForm = this.generateWorkoutForm(record.data);
                    break;
                case 'coaching_session':
                    recordForm = this.generateCoachingSessionForm(record.data);
                    break;
                case 'behavior_definition':
                    recordForm = this.generateBehaviorDefinitionForm(record.data);
                    break;
                case 'behavior_log':
                    recordForm = this.generateBehaviorLogForm(record.data);
                    break;
                case 'document':
                    recordForm = this.generateDocumentForm(record.data);
                    break;
                default:
                    recordForm = '<p>Unknown record type</p>';
            }

            tabContent += `
                <div class="tab-pane fade ${isActive ? 'show active' : ''}"
                     id="record-pane-${idx}" role="tabpanel"
                     data-record-type="${record.record_type}">
                    ${recordForm}
                </div>
            `;
        });

        tabNav += '</ul>';
        tabContent += '</div>';

        return tabNav + tabContent;
    }

    /**
     * Generate health metric form
     */
    generateHealthMetricForm(data) {
        return `
            <div class="record-form-group">
                <label class="record-form-label">Date *</label>
                <input type="date" class="record-form-input" name="recorded_date"
                       value="${data.recorded_date || ''}" required>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Weight (lbs)</label>
                        <input type="number" step="0.1" class="record-form-input" name="weight_lbs"
                               value="${data.weight_lbs || ''}">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Body Fat %</label>
                        <input type="number" step="0.1" class="record-form-input" name="body_fat_percentage"
                               value="${data.body_fat_percentage || ''}">
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Waist (inches)</label>
                        <input type="number" step="0.1" class="record-form-input" name="waist_inches"
                               value="${data.waist_inches || ''}">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Chest (inches)</label>
                        <input type="number" step="0.1" class="record-form-input" name="chest_inches"
                               value="${data.chest_inches || ''}">
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-4">
                    <div class="record-form-group">
                        <label class="record-form-label">Energy (1-10)</label>
                        <input type="number" min="1" max="10" class="record-form-input" name="energy_level"
                               value="${data.energy_level || ''}">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="record-form-group">
                        <label class="record-form-label">Mood (1-10)</label>
                        <input type="number" min="1" max="10" class="record-form-input" name="mood"
                               value="${data.mood || ''}">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="record-form-group">
                        <label class="record-form-label">Sleep (1-10)</label>
                        <input type="number" min="1" max="10" class="record-form-input" name="sleep_quality"
                               value="${data.sleep_quality || ''}">
                    </div>
                </div>
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Notes</label>
                <textarea class="record-form-textarea" name="notes" rows="3">${data.notes || ''}</textarea>
            </div>
        `;
    }

    /**
     * Generate meal log form
     */
    generateMealLogForm(data) {
        const mealTypes = ['BREAKFAST', 'LUNCH', 'DINNER', 'SNACK', 'PRE_WORKOUT', 'POST_WORKOUT', 'OTHER'];

        return `
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Date *</label>
                        <input type="date" class="record-form-input" name="meal_date"
                               value="${data.meal_date || ''}" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Meal Type *</label>
                        <select class="record-form-select" name="meal_type" required>
                            ${mealTypes.map(type =>
                                `<option value="${type}" ${data.meal_type === type ? 'selected' : ''}>
                                    ${type.replace('_', ' ')}
                                </option>`
                            ).join('')}
                        </select>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Calories</label>
                        <input type="number" class="record-form-input" name="calories"
                               value="${data.calories || ''}">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Protein (g)</label>
                        <input type="number" step="0.1" class="record-form-input" name="protein_g"
                               value="${data.protein_g || ''}">
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Carbs (g)</label>
                        <input type="number" step="0.1" class="record-form-input" name="carbs_g"
                               value="${data.carbs_g || ''}">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Fat (g)</label>
                        <input type="number" step="0.1" class="record-form-input" name="fat_g"
                               value="${data.fat_g || ''}">
                    </div>
                </div>
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Description</label>
                <textarea class="record-form-textarea" name="description" rows="3">${data.description || ''}</textarea>
            </div>
        `;
    }

    /**
     * Generate workout form
     */
    generateWorkoutForm(data) {
        const sessionTypes = ['STRENGTH', 'CARDIO', 'FLEXIBILITY', 'MARTIAL_ARTS', 'SPORTS', 'RECOVERY', 'MIXED'];

        let exercisesHtml = '';
        if (data.exercises && data.exercises.length > 0) {
            exercisesHtml = data.exercises.map((ex, idx) => `
                <div class="exercise-item">
                    <h6>Exercise ${idx + 1}: ${ex.exercise_name}</h6>
                    <p>Sets: ${ex.sets || 'N/A'}, Reps: ${ex.reps || 'N/A'}, Weight: ${ex.weight_lbs || 'N/A'} lbs</p>
                </div>
            `).join('');
        }

        return `
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Date *</label>
                        <input type="date" class="record-form-input" name="session_date"
                               value="${data.session_date || ''}" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Session Type *</label>
                        <select class="record-form-select" name="session_type" required>
                            ${sessionTypes.map(type =>
                                `<option value="${type}" ${data.session_type === type ? 'selected' : ''}>
                                    ${type.replace('_', ' ')}
                                </option>`
                            ).join('')}
                        </select>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Duration (minutes)</label>
                        <input type="number" class="record-form-input" name="duration_minutes"
                               value="${data.duration_minutes || ''}">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Intensity (1-10)</label>
                        <input type="number" min="1" max="10" class="record-form-input" name="intensity_level"
                               value="${data.intensity_level || ''}">
                    </div>
                </div>
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Notes</label>
                <textarea class="record-form-textarea" name="notes" rows="2">${data.notes || ''}</textarea>
            </div>
            ${exercisesHtml ? `<div class="mt-3"><h6>Exercises:</h6>${exercisesHtml}</div>` : ''}
        `;
    }

    /**
     * Generate coaching session form
     */
    generateCoachingSessionForm(data) {
        return `
            <div class="record-form-group">
                <label class="record-form-label">Date *</label>
                <input type="date" class="record-form-input" name="session_date"
                       value="${data.session_date || ''}" required>
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Discussion Notes</label>
                <textarea class="record-form-textarea" name="discussion_notes" rows="4">${data.discussion_notes || ''}</textarea>
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Coach Feedback</label>
                <textarea class="record-form-textarea" name="coach_feedback" rows="4">${data.coach_feedback || ''}</textarea>
            </div>
        `;
    }

    /**
     * Generate behavior definition form
     */
    generateBehaviorDefinitionForm(data) {
        const categories = ['HEALTH', 'FITNESS', 'NUTRITION', 'LEARNING', 'PRODUCTIVITY', 'WELLNESS', 'CUSTOM'];

        return `
            <div class="record-form-group">
                <label class="record-form-label">Behavior Name *</label>
                <input type="text" class="record-form-input" name="name"
                       value="${data.name || ''}" required placeholder="e.g., Morning Meditation">
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Category</label>
                <select class="record-form-select" name="category">
                    ${categories.map(cat =>
                        `<option value="${cat}" ${data.category === cat ? 'selected' : ''}>
                            ${cat}
                        </option>`
                    ).join('')}
                </select>
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Description</label>
                <textarea class="record-form-textarea" name="description" rows="3">${data.description || ''}</textarea>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Target Frequency (days/week)</label>
                        <input type="number" min="1" max="7" class="record-form-input" name="target_frequency"
                               value="${data.target_frequency || 7}">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Icon</label>
                        <input type="text" class="record-form-input" name="icon"
                               value="${data.icon || ''}" placeholder="bi-heart">
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Generate behavior log form
     */
    generateBehaviorLogForm(data) {
        return `
            <div class="record-form-group">
                <label class="record-form-label">Behavior Name *</label>
                <input type="text" class="record-form-input" name="behavior_name"
                       value="${data.behavior_name || ''}" required placeholder="Name of the behavior">
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Date *</label>
                        <input type="date" class="record-form-input" name="tracked_date"
                               value="${data.tracked_date || ''}" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="record-form-group">
                        <label class="record-form-label">Completed</label>
                        <select class="record-form-select" name="completed">
                            <option value="true" ${data.completed !== false ? 'selected' : ''}>Yes</option>
                            <option value="false" ${data.completed === false ? 'selected' : ''}>No</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Notes</label>
                <textarea class="record-form-textarea" name="notes" rows="2">${data.notes || ''}</textarea>
            </div>
        `;
    }

    /**
     * Generate document form with markdown preview
     */
    generateDocumentForm(data) {
        const documentTypes = [
            { value: 'workout_plan', label: 'Workout Plan' },
            { value: 'meal_plan', label: 'Meal Plan' },
            { value: 'progress_report', label: 'Progress Report' },
            { value: 'fitness_roadmap', label: 'Fitness Roadmap' },
            { value: 'analysis', label: 'Analysis' },
            { value: 'coaching_notes', label: 'Coaching Notes' },
            { value: 'educational', label: 'Educational' },
            { value: 'custom', label: 'Custom' }
        ];

        const tagsValue = Array.isArray(data.tags) ? data.tags.join(', ') : (data.tags || '');

        return `
            <div class="row">
                <div class="col-md-8">
                    <div class="record-form-group">
                        <label class="record-form-label">Title *</label>
                        <input type="text" class="record-form-input" name="title"
                               value="${this.escapeHtml(data.title || '')}" required>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="record-form-group">
                        <label class="record-form-label">Type *</label>
                        <select class="record-form-select" name="document_type" required>
                            ${documentTypes.map(type =>
                                `<option value="${type.value}" ${data.document_type === type.value ? 'selected' : ''}>
                                    ${type.label}
                                </option>`
                            ).join('')}
                        </select>
                    </div>
                </div>
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Summary</label>
                <input type="text" class="record-form-input" name="summary"
                       value="${this.escapeHtml(data.summary || '')}" maxlength="500"
                       placeholder="Brief description (max 500 characters)">
            </div>
            <div class="record-form-group">
                <label class="record-form-label">Tags</label>
                <input type="text" class="record-form-input" name="tags"
                       value="${this.escapeHtml(tagsValue)}"
                       placeholder="Comma-separated tags (e.g., strength, beginner, 4-week)">
            </div>

            <!-- Content with Preview Toggle -->
            <div class="record-form-group">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <label class="record-form-label mb-0">Content (Markdown) *</label>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-secondary active" id="doc-edit-btn" onclick="window.aiCoachChat.toggleDocumentView('edit')">
                            <i class="bi bi-pencil"></i> Edit
                        </button>
                        <button type="button" class="btn btn-outline-secondary" id="doc-preview-btn" onclick="window.aiCoachChat.toggleDocumentView('preview')">
                            <i class="bi bi-eye"></i> Preview
                        </button>
                    </div>
                </div>
                <div id="doc-edit-view">
                    <textarea class="record-form-textarea" name="content" rows="15" required
                              style="font-family: monospace; font-size: 0.9rem;">${this.escapeHtml(data.content || '')}</textarea>
                </div>
                <div id="doc-preview-view" class="document-preview p-3 border rounded bg-light" style="display: none; max-height: 400px; overflow-y: auto;">
                    <div class="markdown-content">${this.renderMarkdown(data.content || '')}</div>
                </div>
            </div>
        `;
    }

    /**
     * Toggle between edit and preview views for document content
     */
    toggleDocumentView(view) {
        const editView = document.getElementById('doc-edit-view');
        const previewView = document.getElementById('doc-preview-view');
        const editBtn = document.getElementById('doc-edit-btn');
        const previewBtn = document.getElementById('doc-preview-btn');

        if (view === 'preview') {
            // Update preview content from textarea
            const content = document.querySelector('textarea[name="content"]').value;
            previewView.querySelector('.markdown-content').innerHTML = this.renderMarkdown(content);

            editView.style.display = 'none';
            previewView.style.display = 'block';
            editBtn.classList.remove('active');
            previewBtn.classList.add('active');
        } else {
            editView.style.display = 'block';
            previewView.style.display = 'none';
            editBtn.classList.add('active');
            previewBtn.classList.remove('active');
        }
    }

    /**
     * Render markdown content to HTML
     */
    renderMarkdown(content) {
        if (!content) return '<p class="text-muted">No content</p>';

        // Use marked.js if available, otherwise fallback to basic conversion
        if (typeof marked !== 'undefined') {
            return marked.parse(content);
        }

        // Basic fallback - just escape and preserve newlines
        return `<pre style="white-space: pre-wrap;">${this.escapeHtml(content)}</pre>`;
    }

    /**
     * Save record to database
     */
    async saveRecord() {
        if (!this.pendingRecordData) return;

        const { functionName, recordData } = this.pendingRecordData;
        const modal = bootstrap.Modal.getInstance(document.getElementById('record-preview-modal'));
        const modalBody = document.getElementById('record-preview-body');

        let finalData = {};

        // Handle batch records differently
        if (functionName === 'create_batch_records') {
            const records = [];

            // Loop through all tab panes
            modalBody.querySelectorAll('.tab-pane').forEach((pane, idx) => {
                const recordType = pane.getAttribute('data-record-type');
                const data = {};

                // Collect form inputs from this specific tab
                pane.querySelectorAll('input, select, textarea').forEach(input => {
                    if (input.value) {
                        data[input.name] = input.type === 'number' ?
                            parseFloat(input.value) : input.value;
                    }
                });

                // Include special fields from original recordData
                const originalRecord = recordData.records[idx];
                if (originalRecord) {
                    // Include exercises if workout
                    if (recordType === 'workout' && originalRecord.data.exercises) {
                        data.exercises = originalRecord.data.exercises;
                    }

                    // Include action items if coaching
                    if (recordType === 'coaching_session' && originalRecord.data.action_items) {
                        data.action_items = originalRecord.data.action_items;
                    }
                }

                records.push({
                    record_type: recordType,
                    data: data
                });
            });

            finalData = { records: records };
        } else {
            // Single record - existing logic
            const formData = {};
            modalBody.querySelectorAll('input, select, textarea').forEach(input => {
                if (input.value) {
                    formData[input.name] = input.type === 'number' ?
                        parseFloat(input.value) : input.value;
                }
            });

            // Include exercises if workout
            if (functionName === 'create_workout' && recordData.exercises) {
                formData.exercises = recordData.exercises;
            }

            // Include action items if coaching
            if (functionName === 'create_coaching_session' && recordData.action_items) {
                formData.action_items = recordData.action_items;
            }

            // Handle document-specific fields
            if (functionName === 'create_document') {
                // Convert tags from comma-separated string to array
                if (formData.tags && typeof formData.tags === 'string') {
                    formData.tags = formData.tags.split(',').map(t => t.trim()).filter(t => t);
                }
                // Include metadata from original record if present
                if (recordData.metadata) {
                    formData.metadata = recordData.metadata;
                }
            }

            finalData = formData;
        }

        try {
            this.showLoading(true);

            const response = await fetch('/api/ai-coach/save-record', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    conversation_id: this.currentConversationId,
                    function_name: functionName,
                    record_data: finalData
                })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to save record');
            }

            // Close modal
            modal.hide();

            // Show success message
            const recordCount = functionName === 'create_batch_records' ?
                finalData.records.length : 1;
            const message = recordCount > 1 ?
                `${recordCount} records saved successfully!` :
                'Record saved successfully!';
            this.showSuccess(message);

            // Reload conversation to update records count
            this.loadConversations();

        } catch (error) {
            console.error('Error saving record:', error);
            this.showError('Failed to save record. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Render full conversation messages
     */
    renderMessages(messages) {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = '';

        messages.forEach(msg => {
            this.addMessageToUI(msg.role, msg.content);

            // Check for function call metadata
            if (msg.metadata && msg.metadata.function_call) {
                this.handleFunctionCall(msg.metadata.function_call);
            }
        });

        this.scrollToBottom();
    }

    /**
     * Add typing indicator
     */
    addTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        const indicator = document.createElement('div');
        indicator.className = 'message-group assistant';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = `
            <div class="message-avatar">
                <i class="bi bi-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(indicator);
        this.scrollToBottom();
        return 'typing-indicator';
    }

    /**
     * Remove typing indicator
     */
    removeTypingIndicator(id = 'typing-indicator') {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Utility functions
     */

    scrollToBottom() {
        const container = document.getElementById('chat-messages');
        container.scrollTop = container.scrollHeight;
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    showError(message) {
        // Display error in chat interface for better visibility
        const messagesContainer = document.getElementById('chat-messages');

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message-bubble';
        errorDiv.innerHTML = `
            <div class="alert alert-danger" style="margin: 10px 0;">
                <div style="display: flex; align-items: flex-start; gap: 10px;">
                    <i class="bi bi-exclamation-triangle-fill" style="font-size: 1.2rem;"></i>
                    <div>
                        <strong>Error</strong>
                        <p style="margin: 5px 0 0 0; word-break: break-word;">${this.escapeHtml(message)}</p>
                    </div>
                </div>
            </div>
        `;

        messagesContainer.appendChild(errorDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showQuotaCountdown(message, totalSeconds) {
        const messagesContainer = document.getElementById('chat-messages');

        // Create countdown message element
        const countdownDiv = document.createElement('div');
        countdownDiv.className = 'quota-countdown-message';
        countdownDiv.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-clock-history"></i>
                <p>${this.escapeHtml(message)}</p>
                <p class="countdown-timer" style="font-size: 1.2rem; font-weight: bold; margin-top: 10px;">
                    <span id="countdown-value"></span>
                </p>
            </div>
        `;

        messagesContainer.appendChild(countdownDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Update countdown every second
        const countdownElement = document.getElementById('countdown-value');
        let remaining = totalSeconds;

        const updateCountdown = () => {
            if (remaining <= 0) {
                countdownElement.textContent = "Quota should be reset now. You can try again!";
                countdownElement.style.color = "#28a745";  // Green
                return;
            }

            const hours = Math.floor(remaining / 3600);
            const minutes = Math.floor((remaining % 3600) / 60);
            const seconds = remaining % 60;

            let parts = [];
            if (hours > 0) parts.push(`${hours}h`);
            if (minutes > 0) parts.push(`${minutes}m`);
            if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);

            countdownElement.textContent = `Resets in: ${parts.join(' ')}`;

            remaining--;
            setTimeout(updateCountdown, 1000);
        };

        updateCountdown();
    }

    showSuccess(message) {
        alert(message);
    }

    getFriendlyRecordType(functionName) {
        const types = {
            'create_health_metric': 'Health Metric',
            'create_meal_log': 'Meal Log',
            'create_workout': 'Workout Session',
            'create_coaching_session': 'Coaching Session',
            'create_behavior_definition': 'Behavior',
            'log_behavior': 'Behavior Log',
            'create_document': 'Document'
        };
        return types[functionName] || 'Record';
    }

    formatFieldLabel(key) {
        return key.replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatFieldValue(key, value) {
        if (value === null || value === undefined || value === '') return null;
        if (key.includes('date')) {
            return new Date(value).toLocaleDateString();
        }
        return value.toString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.aiCoachChat = new AICoachChat();
});
