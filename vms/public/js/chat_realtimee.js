// File: vms/public/js/chat_realtime.js
// Real-time WebSocket functionality for chat integration

class ChatRealtimeManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.currentRooms = new Set();
        this.eventHandlers = new Map();
        this.messageQueue = [];
        
        this.init();
    }
    
    init() {
        if (typeof io !== 'undefined') {
            this.connectWebSocket();
        } else {
            console.warn('Socket.IO not available, real-time features disabled');
        }
        
        // Listen for page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && !this.connected) {
                this.reconnect();
            }
        });
        
        // Listen for online/offline events
        window.addEventListener('online', () => this.reconnect());
        window.addEventListener('offline', () => this.handleDisconnect());
    }
    
    connectWebSocket() {
        try {
            const socketUrl = window.location.origin;
            const socketPath = '/socket.io';
            
            this.socket = io(socketUrl, {
                path: socketPath,
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                timeout: 20000,
                forceNew: false
            });
            
            this.setupEventHandlers();
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }
    
    setupEventHandlers() {
        if (!this.socket) return;
        
        this.socket.on('connect', () => {
            console.log('Chat WebSocket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
            
            // Process queued messages
            this.processMessageQueue();
            
            // Rejoin rooms
            this.rejoinRooms();
            
            // Update UI
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('Chat WebSocket disconnected:', reason);
            this.handleDisconnect();
            
            // Attempt reconnection
            if (reason === 'io server disconnect') {
                // Server disconnected, try to reconnect
                this.reconnect();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.handleConnectionError();
        });
        
        // Chat-specific events
        this.socket.on('new_chat_message', (data) => {
            this.handleNewMessage(data);
        });
        
        this.socket.on('message_edited', (data) => {
            this.handleMessageEdited(data);
        });
        
        this.socket.on('message_deleted', (data) => {
            this.handleMessageDeleted(data);
        });
        
        this.socket.on('message_reaction_update', (data) => {
            this.handleReactionUpdate(data);
        });
        
        this.socket.on('typing_indicator', (data) => {
            this.handleTypingIndicator(data);
        });
        
        this.socket.on('user_joined_room', (data) => {
            this.handleUserJoinedRoom(data);
        });
        
        this.socket.on('user_left_room', (data) => {
            this.handleUserLeftRoom(data);
        });
    }
    
    handleDisconnect() {
        this.connected = false;
        this.updateConnectionStatus(false);
        
        // Clear typing indicators
        this.clearAllTypingIndicators();
    }
    
    handleConnectionError() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnect();
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
        }
    }
    
    reconnect() {
        if (this.connected) return;
        
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        if (this.socket) {
            this.socket.connect();
        } else {
            this.connectWebSocket();
        }
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.socket.emit(message.event, message.data);
        }
    }
    
    rejoinRooms() {
        this.currentRooms.forEach(roomId => {
            this.joinRoom(roomId, false); // Don't add to currentRooms again
        });
    }
    
    // Public methods for chat functionality
    
    joinRoom(roomId, addToSet = true) {
        if (addToSet) {
            this.currentRooms.add(roomId);
        }
        
        const message = {
            event: 'join_room',
            data: { room_id: roomId }
        };
        
        if (this.connected && this.socket) {
            this.socket.emit(message.event, message.data);
            this.socket.join(`chat_room_${roomId}`);
        } else {
            this.messageQueue.push(message);
        }
    }
    
    leaveRoom(roomId) {
        this.currentRooms.delete(roomId);
        
        if (this.connected && this.socket) {
            this.socket.emit('leave_room', { room_id: roomId });
            this.socket.leave(`chat_room_${roomId}`);
        }
    }
    
    sendTypingIndicator(roomId, isTyping) {
        const message = {
            event: 'typing_indicator',
            data: { room_id: roomId, is_typing: isTyping }
        };
        
        if (this.connected && this.socket) {
            this.socket.emit(message.event, message.data);
        } else {
            // Don't queue typing indicators
            console.log('Not connected, typing indicator not sent');
        }
    }
    
    // Event handlers
    
    handleNewMessage(data) {
        console.log('New message received:', data);
        
        // Update chat rooms preview
        if (typeof load_chat_rooms_preview === 'function') {
            load_chat_rooms_preview();
        }
        
        // Show desktop notification
        this.showDesktopNotification(data);
        
        // Trigger custom event for other parts of the application
        this.triggerCustomEvent('chat:new_message', data);
        
        // Update navbar unread count
        this.updateNavbarUnreadCount();
    }
    
    handleMessageEdited(data) {
        console.log('Message edited:', data);
        this.triggerCustomEvent('chat:message_edited', data);
    }
    
    handleMessageDeleted(data) {
        console.log('Message deleted:', data);
        this.triggerCustomEvent('chat:message_deleted', data);
    }
    
    handleReactionUpdate(data) {
        console.log('Reaction updated:', data);
        this.triggerCustomEvent('chat:reaction_updated', data);
    }
    
    handleTypingIndicator(data) {
        console.log('Typing indicator:', data);
        this.triggerCustomEvent('chat:typing_indicator', data);
    }
    
    handleUserJoinedRoom(data) {
        console.log('User joined room:', data);
        this.triggerCustomEvent('chat:user_joined', data);
    }
    
    handleUserLeftRoom(data) {
        console.log('User left room:', data);
        this.triggerCustomEvent('chat:user_left', data);
    }
    
    // UI Updates
    
    updateConnectionStatus(connected) {
        const chatIcon = document.querySelector('#chat-icon i');
        if (chatIcon) {
            if (connected) {
                chatIcon.style.opacity = '1';
                chatIcon.title = 'Chat (Connected)';
            } else {
                chatIcon.style.opacity = '0.6';
                chatIcon.title = 'Chat (Disconnected)';
            }
        }
        
        // Show connection status indicator
        this.showConnectionStatus(connected);
    }
    
    showConnectionStatus(connected) {
        // Remove existing status indicator
        const existing = document.querySelector('.chat-connection-status');
        if (existing) {
            existing.remove();
        }
        
        if (!connected) {
            // Show disconnected indicator
            const indicator = document.createElement('div');
            indicator.className = 'chat-connection-status';
            indicator.innerHTML = `
                <div style="
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: #ffc107;
                    color: #212529;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    z-index: 9999;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <i class="fa fa-wifi" style="margin-right: 4px;"></i>
                    Chat disconnected
                </div>
            `;
            document.body.appendChild(indicator);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 5000);
        }
    }
    
    updateNavbarUnreadCount() {
        // Refresh chat status
        frappe.call({
            method: 'vms.get_user_chat_status',
            callback: (response) => {
                if (response.message && response.message.success) {
                    const data = response.message.data;
                    const badge = document.querySelector('#chat-unread-badge');
                    if (badge && data.total_unread > 0) {
                        badge.textContent = data.total_unread > 99 ? '99+' : data.total_unread;
                        badge.style.display = 'block';
                    }
                }
            }
        });
    }
    
    showDesktopNotification(data) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification(
                data.sender_name ? `${data.sender_name} in ${data.room_name}` : 'New Chat Message',
                {
                    body: data.content || 'New message received',
                    icon: '/assets/vms/images/chat-icon.png',
                    badge: '/assets/vms/images/chat-badge.png',
                    tag: `chat-${data.room_id}`,
                    requireInteraction: false,
                    silent: false
                }
            );
            
            notification.onclick = () => {
                window.focus();
                // Open chat room if possible
                if (typeof open_chat_room === 'function') {
                    open_chat_room(data.room_id);
                }
                notification.close();
            };
            
            // Auto close after 5 seconds
            setTimeout(() => notification.close(), 5000);
        }
    }
    
    clearAllTypingIndicators() {
        // Clear any typing indicators in the UI
        this.triggerCustomEvent('chat:clear_all_typing');
    }
    
    // Custom event system
    
    triggerCustomEvent(eventName, data) {
        const event = new CustomEvent(eventName, { 
            detail: data,
            bubbles: true,
            cancelable: true 
        });
        document.dispatchEvent(event);
    }
    
    addEventListener(eventName, handler) {
        if (!this.eventHandlers.has(eventName)) {
            this.eventHandlers.set(eventName, []);
        }
        this.eventHandlers.get(eventName).push(handler);
        
        document.addEventListener(eventName, handler);
    }
    
    removeEventListener(eventName, handler) {
        const handlers = this.eventHandlers.get(eventName);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
        
        document.removeEventListener(eventName, handler);
    }
    
    // Utility methods
    
    isConnected() {
        return this.connected;
    }
    
    getRoomList() {
        return Array.from(this.currentRooms);
    }
    
    getConnectionStatus() {
        return {
            connected: this.connected,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length,
            activeRooms: this.currentRooms.size
        };
    }
}

// Initialize chat real-time manager
let chatRealtimeManager;



function onFrappeReady(callback) {
    if (typeof frappe !== "undefined" && typeof frappe.ready === "function") {
        frappe.ready(callback);
    } else {
        document.addEventListener("DOMContentLoaded", callback);
    }
}


onFrappeReady(() => {
    setTimeout(() => {
        chatRealtimeManager = new ChatRealtimeManager();
        window.chatRealtime = chatRealtimeManager;
        setupGlobalChatEvents();
    }, 1000);
});



function setupGlobalChatEvents() {
    // Listen for custom chat events
    document.addEventListener('chat:new_message', (event) => {
        // Update UI elements that show unread counts
        const data = event.detail;
        console.log('New message event received:', data);
        
        // You can add custom handlers here
        // For example, update specific UI elements, play sounds, etc.
    });
    
    document.addEventListener('chat:typing_indicator', (event) => {
        const data = event.detail;
        console.log('Typing indicator event:', data);
        
        // Update typing indicators in chat UI
        // This would be implemented based on your frontend
    });
    
    // Example: Play notification sound
    document.addEventListener('chat:new_message', (event) => {
        if (document.visibilityState === 'hidden') {
            // Only play sound when tab is not active
            playNotificationSound();
        }
    });
}

function playNotificationSound() {
    try {
        const audio = new Audio('/assets/vms/sounds/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(e => {
            console.log('Could not play notification sound:', e);
        });
    } catch (error) {
        console.log('Audio not supported:', error);
    }
}

// Utility functions for integration with existing chat functionality

function joinChatRoom(roomId) {
    if (window.chatRealtime) {
        window.chatRealtime.joinRoom(roomId);
    }
}

function leaveChatRoom(roomId) {
    if (window.chatRealtime) {
        window.chatRealtime.leaveRoom(roomId);
    }
}

function sendTyping(roomId, isTyping) {
    if (window.chatRealtime) {
        window.chatRealtime.sendTypingIndicator(roomId, isTyping);
    }
}

function getChatConnectionStatus() {
    if (window.chatRealtime) {
        return window.chatRealtime.getConnectionStatus();
    }
    return { connected: false };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatRealtimeManager;
}