// vms/public/js/chat_error_handler.js
// Enhanced error handling for chat application frontend

class ChatErrorHandler {
    constructor() {
        this.retryAttempts = 0;
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 second
        this.errorLog = [];
        this.isOnline = navigator.onLine;
        
        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.handleReconnection();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.handleDisconnection();
        });
    }
    
    /**
     * Enhanced frappe.call wrapper with retry logic and error handling
     */
    makeApiCall(options) {
        const originalCallback = options.callback;
        const originalError = options.error;
        
        // Add our enhanced error handling
        options.error = (xhr, status, error) => {
            this.handleApiError(xhr, status, error, options, originalError);
        };
        
        options.callback = (response) => {
            // Reset retry attempts on success
            this.retryAttempts = 0;
            
            // Handle timestamp mismatch errors even in successful responses
            if (response.exc && response.exc.includes('TimestampMismatchError')) {
                this.handleTimestampMismatch(options, originalCallback);
                return;
            }
            
            if (originalCallback) {
                originalCallback(response);
            }
        };
        
        // Make the API call
        frappe.call(options);
    }
    
    /**
     * Handle API errors with intelligent retry logic
     */
    handleApiError(xhr, status, error, originalOptions, originalErrorCallback) {
        const errorInfo = {
            status: status,
            error: error,
            timestamp: new Date().toISOString(),
            method: originalOptions.method,
            xhr: xhr
        };
        
        // Log the error
        this.logError(errorInfo);
        
        // Check if it's a timestamp mismatch error
        if (xhr.responseText && xhr.responseText.includes('TimestampMismatchError')) {
            this.handleTimestampMismatch(originalOptions, originalErrorCallback);
            return;
        }
        
        // Check if it's a network error and we should retry
        if (this.shouldRetry(xhr, status)) {
            this.retryApiCall(originalOptions, originalErrorCallback);
            return;
        }
        
        // Handle specific error types
        if (status === 403 || status === 401) {
            this.handleAuthError();
            return;
        }
        
        if (status === 500) {
            this.handleServerError(originalOptions, originalErrorCallback);
            return;
        }
        
        // Fall back to original error handler
        if (originalErrorCallback) {
            originalErrorCallback(xhr, status, error);
        } else {
            this.showGenericError(errorInfo);
        }
    }
    
    /**
     * Handle timestamp mismatch errors with automatic refresh
     */
    handleTimestampMismatch(originalOptions, callback) {
        console.warn('Timestamp mismatch detected, attempting to refresh and retry...');
        
        // Show user-friendly message
        frappe.show_alert({
            message: __('Document was updated by another user. Refreshing...'),
            indicator: 'yellow'
        }, 3);
        
        // Wait a moment, then retry with fresh data
        setTimeout(() => {
            if (originalOptions.method === 'vms.get_user_chat_status' || 
                originalOptions.method === 'vms.update_user_online_status') {
                
                // For status updates, just retry without refresh
                this.retryApiCall(originalOptions, callback);
            } else {
                // For other operations, might need to refresh the page/data
                if (window.location.href.includes('/app/')) {
                    // Refresh current page data
                    if (typeof cur_frm !== 'undefined' && cur_frm) {
                        cur_frm.reload_doc();
                    } else {
                        // Fallback: reload page
                        location.reload();
                    }
                } else {
                    // Retry the API call
                    this.retryApiCall(originalOptions, callback);
                }
            }
        }, 500);
    }
    
    /**
     * Retry API call with exponential backoff
     */
    retryApiCall(originalOptions, callback) {
        if (this.retryAttempts >= this.maxRetries) {
            frappe.show_alert({
                message: __('Unable to connect after multiple attempts. Please refresh the page.'),
                indicator: 'red'
            }, 5);
            this.retryAttempts = 0;
            return;
        }
        
        this.retryAttempts++;
        const delay = this.retryDelay * Math.pow(2, this.retryAttempts - 1); // Exponential backoff
        
        console.log(`Retrying API call (attempt ${this.retryAttempts}/${this.maxRetries}) in ${delay}ms...`);
        
        setTimeout(() => {
            // Remove our custom error handler for the retry to avoid infinite loops
            const retryOptions = { ...originalOptions };
            delete retryOptions.error;
            
            frappe.call(retryOptions);
        }, delay);
    }
    
    /**
     * Check if we should retry the API call
     */
    shouldRetry(xhr, status) {
        // Don't retry if offline
        if (!this.isOnline) return false;
        
        // Don't retry if we've exceeded max attempts
        if (this.retryAttempts >= this.maxRetries) return false;
        
        // Retry on network errors, timeouts, and 500 errors
        return (
            status === 0 ||           // Network error
            status === 408 ||         // Timeout
            status === 500 ||         // Server error
            status === 502 ||         // Bad gateway
            status === 503 ||         // Service unavailable
            status === 504            // Gateway timeout
        );
    }
    
    /**
     * Handle authentication errors
     */
    handleAuthError() {
        frappe.show_alert({
            message: __('Session expired. Please login again.'),
            indicator: 'red'
        }, 5);
        
        setTimeout(() => {
            window.location.href = '/login';
        }, 2000);
    }
    
    /**
     * Handle server errors
     */
    handleServerError(originalOptions, callback) {
        frappe.show_alert({
            message: __('Server error occurred. Retrying...'),
            indicator: 'orange'
        }, 3);
        
        // Retry server errors
        this.retryApiCall(originalOptions, callback);
    }
    
    /**
     * Handle reconnection after going online
     */
    handleReconnection() {
        frappe.show_alert({
            message: __('Connection restored'),
            indicator: 'green'
        }, 3);
        
        // Reload chat data if chat is open
        if (typeof load_enhanced_chat_rooms_stable === 'function') {
            load_enhanced_chat_rooms_stable();
        }
        
        // Update online status
        this.makeApiCall({
            method: 'vms.update_user_online_status',
            args: { status: 'online' },
            callback: function(response) {
                console.log('Online status updated after reconnection');
            }
        });
    }
    
    /**
     * Handle disconnection
     */
    handleDisconnection() {
        frappe.show_alert({
            message: __('Connection lost. Working offline...'),
            indicator: 'red'
        }, 5);
    }
    
    /**
     * Show generic error message
     */
    showGenericError(errorInfo) {
        frappe.show_alert({
            message: __('An error occurred. Please try again.'),
            indicator: 'red'
        }, 4);
        
        console.error('Chat API Error:', errorInfo);
    }
    
    /**
     * Log errors for debugging
     */
    logError(errorInfo) {
        this.errorLog.push(errorInfo);
        
        // Keep only last 50 errors
        if (this.errorLog.length > 50) {
            this.errorLog = this.errorLog.slice(-50);
        }
        
        console.error('Chat Error:', errorInfo);
    }
    
    /**
     * Get error log for debugging
     */
    getErrorLog() {
        return this.errorLog;
    }
}

// Create global instance
window.chatErrorHandler = new ChatErrorHandler();

// Enhanced chat API wrapper functions
window.safeChatApiCall = function(options) {
    chatErrorHandler.makeApiCall(options);
};

// Enhanced status check with error handling
function check_for_new_messages_enhanced_safe() {
    if (!chatEnabled) return;
    
    safeChatApiCall({
        method: "vms.get_user_chat_status",
        callback: function(response) {
            if (response.message && response.message.success) {
                const data = response.message.data;
                update_notification_dot_enhanced(data.total_unread > 0);
                
                // Update user status if changed
                if (data.online_status !== frappe.boot.user.custom_chat_status) {
                    update_user_chat_status(data.online_status);
                }
            }
        },
        error: function(xhr, status, error) {
            // This will be handled by chatErrorHandler automatically
            console.log('Status check failed, will retry automatically');
        }
    });
}

// Enhanced room loading with error handling
function load_enhanced_chat_rooms_safe() {
    safeChatApiCall({
        method: "vms.get_user_chat_rooms",
        args: { 
            page: 1, 
            page_size: 20,
            include_activity: true 
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                const data = response.message.data;
                const rooms = data.rooms || data || [];
                
                // Update UI with rooms
                update_chat_rooms_ui(rooms);
                
                // Update notification dot
                const hasUnread = rooms.some(room => room.unread_count > 0);
                update_notification_dot_enhanced(hasUnread);
                
            } else {
                show_chat_rooms_error();
            }
        },
        error: function(xhr, status, error) {
            show_chat_rooms_error();
        }
    });
}

// Enhanced message sending with error handling
function send_message_safe(room_id, content, message_type = "Text") {
    safeChatApiCall({
        method: "vms.send_message",
        args: {
            room_id: room_id,
            content: content,
            message_type: message_type
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                // Message sent successfully
                if (typeof refresh_chat_messages === 'function') {
                    refresh_chat_messages(room_id);
                }
                
                // Clear input
                const messageInput = document.querySelector('#message-input');
                if (messageInput) {
                    messageInput.value = '';
                }
                
                frappe.show_alert({
                    message: __('Message sent'),
                    indicator: 'green'
                }, 2);
                
            } else {
                frappe.show_alert({
                    message: __('Failed to send message'),
                    indicator: 'red'
                }, 3);
            }
        },
        error: function(xhr, status, error) {
            frappe.show_alert({
                message: __('Failed to send message. Please try again.'),
                indicator: 'red'
            }, 3);
        }
    });
}

// Enhanced online status update
function update_online_status_safe(status) {
    safeChatApiCall({
        method: "vms.update_user_online_status",
        args: { status: status },
        callback: function(response) {
            if (response.message && response.message.success) {
                console.log(`Status updated to: ${status}`);
                
                // Update local status indicator
                update_status_indicator(status);
                
            } else {
                console.warn('Failed to update status:', response.message);
            }
        },
        error: function(xhr, status, error) {
            console.warn('Status update failed, will be retried automatically');
        }
    });
}

// Helper functions
function update_chat_rooms_ui(rooms) {
    const chatRoomsContainer = document.querySelector('#chat-rooms-container');
    if (!chatRoomsContainer) return;
    
    if (rooms.length === 0) {
        chatRoomsContainer.innerHTML = `
            <div class="text-center p-3">
                <p style="color: #8d99a6;">No chat rooms found</p>
                <button class="btn btn-sm btn-primary" onclick="create_new_chat_room()">
                    Create Room
                </button>
            </div>
        `;
        return;
    }
    
    let html = '';
    rooms.forEach(room => {
        const unreadBadge = room.unread_count > 0 ? 
            `<span class="badge bg-danger">${room.unread_count}</span>` : '';
        
        const lastActivity = room.last_activity ? 
            format_time_enhanced(room.last_activity) : 'No activity';
            
        html += `
            <div class="chat-room-item" data-room-id="${room.name}" onclick="open_chat_room('${room.name}')">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${room.room_name}</h6>
                        <small class="text-muted">${lastActivity}</small>
                    </div>
                    ${unreadBadge}
                </div>
            </div>
        `;
    });
    
    chatRoomsContainer.innerHTML = html;
}

function show_chat_rooms_error() {
    const chatRoomsContainer = document.querySelector('#chat-rooms-container');
    if (chatRoomsContainer) {
        chatRoomsContainer.innerHTML = `
            <div class="text-center p-3">
                <p style="color: #dc3545;">Failed to load chat rooms</p>
                <button class="btn btn-sm btn-secondary" onclick="load_enhanced_chat_rooms_safe()">
                    Retry
                </button>
            </div>
        `;
    }
}

function update_status_indicator(status) {
    const statusIndicator = document.querySelector('#user-status-indicator');
    if (statusIndicator) {
        const statusColors = {
            'online': '#28a745',
            'away': '#ffc107', 
            'busy': '#dc3545',
            'offline': '#6c757d'
        };
        
        statusIndicator.style.backgroundColor = statusColors[status] || statusColors['offline'];
        statusIndicator.title = `Status: ${status}`;
    }
}

// Page lifecycle handlers with enhanced error handling
$(document).ready(function() {
    // Initialize chat error handling
    if (typeof chatEnabled !== 'undefined' && chatEnabled) {
        console.log('Chat error handler initialized');
        
        // Update status to online on page load
        update_online_status_safe('online');
        
        // Start periodic status checks
        setInterval(check_for_new_messages_enhanced_safe, 30000); // Every 30 seconds
        
        // Update status when user becomes active
        let userActiveTimeout;
        document.addEventListener('mousemove', function() {
            clearTimeout(userActiveTimeout);
            userActiveTimeout = setTimeout(() => {
                update_online_status_safe('online');
            }, 1000);
        });
        
        // Update status to away when user is inactive
        let inactivityTimeout;
        const resetInactivityTimer = () => {
            clearTimeout(inactivityTimeout);
            inactivityTimeout = setTimeout(() => {
                update_online_status_safe('away');
            }, 300000); // 5 minutes
        };
        
        document.addEventListener('mousemove', resetInactivityTimer);
        document.addEventListener('keypress', resetInactivityTimer);
        resetInactivityTimer();
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (typeof chatEnabled !== 'undefined' && chatEnabled) {
        if (document.hidden) {
            update_online_status_safe('away');
        } else {
            update_online_status_safe('online');
            // Refresh chat data when user returns
            if (typeof load_enhanced_chat_rooms_safe === 'function') {
                load_enhanced_chat_rooms_safe();
            }
        }
    }
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (typeof chatEnabled !== 'undefined' && chatEnabled) {
        // Use navigator.sendBeacon for reliable offline status update
        if (navigator.sendBeacon) {
            const formData = new FormData();
            formData.append('cmd', 'vms.update_user_online_status');
            formData.append('status', 'offline');
            navigator.sendBeacon('/api/method/vms.update_user_online_status', formData);
        }
    }
});

// Export for global use
window.load_enhanced_chat_rooms_safe = load_enhanced_chat_rooms_safe;
window.check_for_new_messages_enhanced_safe = check_for_new_messages_enhanced_safe;
window.send_message_safe = send_message_safe;
window.update_online_status_safe = update_online_status_safe;