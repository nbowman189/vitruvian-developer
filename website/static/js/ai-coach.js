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
                throw new Error(data.message || 'Failed to send message');
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
            this.showError('Failed to send message. Please try again.');
            this.removeTypingIndicator();
        } finally {
            this.isSending = false;
            sendBtn.disabled = false;
            input.focus();
        }
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
        bubble.textContent = content;

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
     * Generate record edit form
     */
    generateRecordForm(functionName, data) {
        let formHtml = '';

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
        }

        return formHtml;
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
     * Save record to database
     */
    async saveRecord() {
        if (!this.pendingRecordData) return;

        const { functionName, recordData } = this.pendingRecordData;
        const modal = bootstrap.Modal.getInstance(document.getElementById('record-preview-modal'));

        // Collect form data
        const formData = {};
        const modalBody = document.getElementById('record-preview-body');
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
                    record_data: formData
                })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Failed to save record');
            }

            // Close modal
            modal.hide();

            // Show success message
            this.showSuccess('Record saved successfully!');

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
        // Use Bootstrap toast or alert
        alert(`Error: ${message}`);
    }

    showSuccess(message) {
        alert(message);
    }

    getFriendlyRecordType(functionName) {
        const types = {
            'create_health_metric': 'Health Metric',
            'create_meal_log': 'Meal Log',
            'create_workout': 'Workout Session',
            'create_coaching_session': 'Coaching Session'
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
