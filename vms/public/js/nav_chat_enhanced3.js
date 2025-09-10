// Enhanced Chat UI v2 - Better styling, room creation, and message actions
// Provides a modern WhatsApp-like experience with full functionality

class EnhancedChatUIv2 {
    constructor() {
        this.pollInterval = null;
        this.currentOpenRoom = null;
        this.currentRoomData = null;
        this.hasUnreadMessages = false;
        this.replyToMessage = null;
        this.editingMessage = null;
        
        this.init();
    }
    
    init() {
        console.log("🚀 Initializing Enhanced Chat UI v2...");
        this.waitForElement('.nav-item:has([title="Chat Messages"])', () => {
            this.enhanceChatIcon();
            this.enhanceDropdown();
            this.startPolling();
            this.checkInitialUnread();
            this.addCustomStyles();
        });
    }
    
    waitForElement(selector, callback, maxAttempts = 20) {
        let attempts = 0;
        const check = () => {
            attempts++;
            const element = document.querySelector(selector);
            if (element) {
                callback(element);
            } else if (attempts < maxAttempts) {
                setTimeout(check, 500);
            }
        };
        check();
    }
    
    addCustomStyles() {
        if (document.querySelector('#enhanced-chat-styles-v2')) return;
        
        const style = document.createElement('style');
        style.id = 'enhanced-chat-styles-v2';
        style.textContent = `
            /* Enhanced Chat Styles v2 */
            @keyframes pulse-green {
                0% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
                50% { transform: scale(1.2); opacity: 0.8; box-shadow: 0 0 0 4px rgba(40, 167, 69, 0.3); }
                100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
            }
            
            @keyframes slideInUp {
                from { transform: translateY(10px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            .enhanced-chat-dropdown {
                width: 420px !important;
                max-height: 600px !important;
                border-radius: 12px !important;
                overflow: hidden !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.15) !important;
                border: 1px solid #e9ecef !important;
                background: white !important;
            }
            
            .chat-header-gradient {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
                padding: 16px 20px !important;
                border-bottom: none !important;
            }
            
            .chat-rooms-container {
                max-height: 400px;
                overflow-y: auto;
                background: #f8f9fa;
            }
            
            .chat-rooms-container::-webkit-scrollbar {
                width: 6px;
            }
            
            .chat-rooms-container::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            
            .chat-rooms-container::-webkit-scrollbar-thumb {
                background: #c1c1c1;
                border-radius: 3px;
            }
            
            .enhanced-room-item {
                padding: 16px 20px;
                border-bottom: 1px solid #e9ecef;
                cursor: pointer;
                transition: all 0.3s ease;
                background: white;
                display: flex;
                align-items: center;
                gap: 15px;
                position: relative;
                animation: slideInUp 0.3s ease-out;
            }
            
            .enhanced-room-item:hover {
                background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                transform: translateX(3px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .enhanced-room-item.unread {
                background: linear-gradient(90deg, #e3f2fd 0%, #f8f9fa 100%);
                border-left: 4px solid #2196f3;
            }
            
            .enhanced-room-item.unread::before {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                width: 4px;
                background: linear-gradient(135deg, #2196f3, #1976d2);
            }
            
            .room-avatar-enhanced {
                width: 48px;
                height: 48px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                color: white;
                font-weight: bold;
                box-shadow: 0 3px 12px rgba(0,0,0,0.15);
                transition: transform 0.2s ease;
            }
            
            .enhanced-room-item:hover .room-avatar-enhanced {
                transform: scale(1.05);
            }
            
            .room-info-enhanced {
                flex: 1;
                min-width: 0;
            }
            
            .room-name-enhanced {
                font-weight: 600;
                font-size: 15px;
                color: #2c3e50;
                margin-bottom: 4px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            .room-last-message-enhanced {
                font-size: 13px;
                color: #6c757d;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                line-height: 1.3;
            }
            
            .room-meta-enhanced {
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 6px;
            }
            
            .room-time-enhanced {
                font-size: 11px;
                color: #9e9e9e;
                font-weight: 500;
            }
            
            .room-unread-badge {
                background: linear-gradient(135deg, #dc3545, #c82333);
                color: white;
                border-radius: 12px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: bold;
                min-width: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
                animation: pulse 2s infinite;
            }
            
            .create-room-btn {
                background: linear-gradient(135deg, #28a745, #20c997) !important;
                border: none !important;
                color: white !important;
                padding: 12px 20px !important;
                margin: 15px 20px !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                font-size: 14px !important;
                cursor: pointer !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 3px 12px rgba(40, 167, 69, 0.3) !important;
                width: calc(100% - 40px) !important;
            }
            
            .create-room-btn:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4) !important;
            }
            
            /* Messaging Interface */
            .chat-messaging-interface-v2 {
                display: none;
                height: 500px;
                flex-direction: column;
                background: white;
            }
            
            .chat-header-v2 {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .chat-header-left {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .back-btn {
                background: rgba(255, 255, 255, 0.2) !important;
                border: none !important;
                color: white !important;
                width: 36px !important;
                height: 36px !important;
                border-radius: 50% !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
            }
            
            .back-btn:hover {
                background: rgba(255, 255, 255, 0.3) !important;
                transform: scale(1.05) !important;
            }
            
            .chat-room-title {
                font-weight: 600;
                font-size: 16px;
                margin: 0;
            }
            
            .chat-room-status {
                font-size: 12px;
                opacity: 0.9;
                margin-top: 2px;
            }
            
            .chat-messages-container-v2 {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                position: relative;
            }
            
            .chat-messages-container-v2::-webkit-scrollbar {
                width: 6px;
            }
            
            .chat-messages-container-v2::-webkit-scrollbar-track {
                background: rgba(0,0,0,0.1);
            }
            
            .chat-messages-container-v2::-webkit-scrollbar-thumb {
                background: #007bff;
                border-radius: 3px;
            }
            
            .message-bubble {
                max-width: 75%;
                margin-bottom: 15px;
                animation: slideInUp 0.3s ease-out;
                position: relative;
                padding: 10px 15px;
                border-radius: 18px;
                word-wrap: break-word;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .message-bubble.own {
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                margin-left: auto;
                border-bottom-right-radius: 6px;
            }
            
            .message-bubble.other {
                background: white;
                color: #2c3e50;
                border: 1px solid #e9ecef;
                margin-right: auto;
                border-bottom-left-radius: 6px;
            }
            
            .message-sender {
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 4px;
                opacity: 0.8;
            }
            
            .message-content {
                line-height: 1.4;
                margin-bottom: 6px;
                font-size: 14px;
            }
            
            .message-time {
                font-size: 11px;
                opacity: 0.7;
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-top: 4px;
            }
            
            .message-actions {
                display: none;
                position: absolute;
                top: -8px;
                right: 10px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.15);
                padding: 4px;
                gap: 2px;
            }
            
            .message-bubble:hover .message-actions {
                display: flex;
            }
            
            .message-action-btn {
                background: none !important;
                border: none !important;
                color: #6c757d !important;
                width: 28px !important;
                height: 28px !important;
                border-radius: 50% !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
                font-size: 12px !important;
            }
            
            .message-action-btn:hover {
                background: #f8f9fa !important;
                color: #007bff !important;
                transform: scale(1.1) !important;
            }
            
            .reply-preview {
                background: rgba(0, 123, 255, 0.1);
                border-left: 3px solid #007bff;
                padding: 8px 12px;
                margin-bottom: 8px;
                border-radius: 6px;
                font-size: 12px;
                color: #6c757d;
            }
            
            .chat-input-area-v2 {
                background: white;
                border-top: 1px solid #e9ecef;
                padding: 15px 20px;
            }
            
            .chat-input-wrapper {
                display: flex;
                gap: 10px;
                align-items: flex-end;
            }
            
            .chat-input-field {
                flex: 1;
                border: 2px solid #e9ecef !important;
                border-radius: 25px !important;
                padding: 12px 18px !important;
                font-size: 14px !important;
                outline: none !important;
                transition: all 0.3s ease !important;
                resize: none !important;
                max-height: 100px !important;
                min-height: 44px !important;
            }
            
            .chat-input-field:focus {
                border-color: #007bff !important;
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
            }
            
            .send-btn {
                background: linear-gradient(135deg, #007bff, #0056b3) !important;
                border: none !important;
                color: white !important;
                width: 44px !important;
                height: 44px !important;
                border-radius: 50% !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                cursor: pointer !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 3px 12px rgba(0, 123, 255, 0.3) !important;
            }
            
            .send-btn:hover {
                transform: scale(1.05) !important;
                box-shadow: 0 4px 16px rgba(0, 123, 255, 0.4) !important;
            }
            
            .send-btn:disabled {
                opacity: 0.6 !important;
                cursor: not-allowed !important;
                transform: none !important;
            }
            
            /* Modal Styles */
            .chat-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .chat-modal {
                background: white;
                border-radius: 12px;
                padding: 0;
                width: 90%;
                max-width: 500px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                animation: slideInUp 0.3s ease-out;
                overflow: hidden;
            }
            
            .modal-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .modal-title {
                font-weight: 600;
                font-size: 18px;
                margin: 0;
            }
            
            .modal-close {
                background: none !important;
                border: none !important;
                color: white !important;
                font-size: 24px !important;
                cursor: pointer !important;
                width: 32px !important;
                height: 32px !important;
                border-radius: 50% !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                transition: all 0.2s ease !important;
            }
            
            .modal-close:hover {
                background: rgba(255, 255, 255, 0.2) !important;
            }
            
            .modal-body {
                padding: 25px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #2c3e50;
                font-size: 14px;
            }
            
            .form-control {
                width: 100% !important;
                padding: 12px 16px !important;
                border: 2px solid #e9ecef !important;
                border-radius: 8px !important;
                font-size: 14px !important;
                transition: all 0.3s ease !important;
                outline: none !important;
            }
            
            .form-control:focus {
                border-color: #007bff !important;
                box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
            }
            
            .form-select {
                background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e") !important;
                background-position: right 12px center !important;
                background-repeat: no-repeat !important;
                background-size: 16px 12px !important;
                appearance: none !important;
            }
            
            .modal-footer {
                padding: 0 25px 25px;
                display: flex;
                gap: 12px;
                justify-content: flex-end;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #007bff, #0056b3) !important;
                border: none !important;
                color: white !important;
                padding: 12px 24px !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                cursor: pointer !important;
                transition: all 0.3s ease !important;
            }
            
            .btn-primary:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 16px rgba(0, 123, 255, 0.3) !important;
            }
            
            .btn-secondary {
                background: #6c757d !important;
                border: none !important;
                color: white !important;
                padding: 12px 24px !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                cursor: pointer !important;
                transition: all 0.3s ease !important;
            }
            
            .btn-secondary:hover {
                background: #5a6268 !important;
            }
            
            /* Loading and Empty States */
            .loading-state, .empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 40px 20px;
                color: #6c757d;
                text-align: center;
            }
            
            .loading-spinner {
                width: 24px;
                height: 24px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #007bff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 12px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Responsive Design */
            @media (max-width: 768px) {
                .enhanced-chat-dropdown {
                    width: 95vw !important;
                    max-width: 380px !important;
                }
                
                .chat-messaging-interface-v2 {
                    height: 450px;
                }
                
                .message-bubble {
                    max-width: 85%;
                }
                
                .chat-modal {
                    width: 95%;
                    margin: 20px;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    enhanceChatIcon() {
        const chatNavItem = document.querySelector('.nav-item:has([title="Chat Messages"])');
        if (!chatNavItem) return;
        
        const chatIcon = chatNavItem.querySelector('svg') || chatNavItem.querySelector('i');
        if (!chatIcon) return;
        
        // Create wrapper for icon + notification dot
        const iconWrapper = document.createElement('div');
        iconWrapper.style.cssText = 'position: relative; display: inline-block;';
        
        chatIcon.parentNode.insertBefore(iconWrapper, chatIcon);
        iconWrapper.appendChild(chatIcon);
        
        // Add green notification dot
        const notificationDot = document.createElement('span');
        notificationDot.id = 'chat-notification-dot-v2';
        notificationDot.style.cssText = `
            display: none;
            position: absolute;
            top: -2px;
            right: -2px;
            width: 8px;
            height: 8px;
            background: #28a745;
            border-radius: 50%;
            border: 2px solid white;
            animation: pulse-green 2s infinite;
            z-index: 10;
        `;
        
        iconWrapper.appendChild(notificationDot);
        console.log("✅ Chat icon enhanced with notification dot");
    }
    
    enhanceDropdown() {
        const chatDropdown = document.querySelector('.dropdown-menu:has([href*="Chat"]):has([href*="Message"])');
        if (!chatDropdown) return;
        
        chatDropdown.innerHTML = '';
        chatDropdown.className += ' enhanced-chat-dropdown';
        
        chatDropdown.innerHTML = `
            <!-- Header -->
            <div class="chat-header-gradient">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600; font-size: 16px;">💬 Chat Messages</div>
                        <div style="font-size: 12px; opacity: 0.9; margin-top: 2px;">Stay connected with your team</div>
                    </div>
                    <button onclick="enhancedChatV2.openFullChatApp()" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; font-size: 11px; padding: 6px 12px; border-radius: 6px; cursor: pointer; transition: all 0.2s ease;">
                        Open App
                    </button>
                </div>
            </div>
            
            <!-- Chat Rooms List -->
            <div id="enhanced-chat-rooms-list-v2" class="chat-rooms-container">
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <div>Loading your conversations...</div>
                </div>
            </div>
            
            <!-- Create Room Button -->
            <button class="create-room-btn" onclick="enhancedChatV2.showCreateRoomModal()">
                <i class="fa fa-plus" style="margin-right: 8px;"></i>
                Create New Room
            </button>
            
            <!-- Messaging Interface -->
            <div id="enhanced-messaging-interface-v2" class="chat-messaging-interface-v2">
                <div class="chat-header-v2">
                    <div class="chat-header-left">
                        <button class="back-btn" onclick="enhancedChatV2.backToRoomsList()">
                            ←
                        </button>
                        <div>
                            <div class="chat-room-title" id="current-room-title-v2">Room Name</div>
                            <div class="chat-room-status" id="current-room-status">Online • 3 members</div>
                        </div>
                    </div>
                    <div>
                        <span style="background: rgba(40, 167, 69, 0.2); color: #28a745; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">
                            🟢 Active
                        </span>
                    </div>
                </div>
                
                <div class="chat-messages-container-v2" id="chat-messages-display-v2">
                    <!-- Messages will be loaded here -->
                </div>
                
                <div class="chat-input-area-v2">
                    <div id="reply-preview-v2" style="display: none;" class="reply-preview">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: 600; margin-bottom: 2px;">Replying to <span id="reply-sender"></span></div>
                                <div id="reply-content"></div>
                            </div>
                            <button onclick="enhancedChatV2.cancelReply()" style="background: none; border: none; color: #6c757d; cursor: pointer;">×</button>
                        </div>
                    </div>
                    
                    <div class="chat-input-wrapper">
                        <textarea 
                            id="message-input-v2" 
                            class="chat-input-field"
                            placeholder="Type your message..."
                            rows="1"
                            onkeydown="enhancedChatV2.handleInputKeydown(event)"
                            oninput="enhancedChatV2.adjustTextareaHeight(this)"
                        ></textarea>
                        <button class="send-btn" onclick="enhancedChatV2.sendMessage()" id="send-btn-v2">
                            <i class="fa fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        console.log("✅ Dropdown enhanced with modern UI");
    }
    
    startPolling() {
        this.pollInterval = setInterval(() => {
            this.checkForNewMessages();
            
            const dropdown = document.querySelector('.enhanced-chat-dropdown');
            if (dropdown && dropdown.offsetParent !== null) {
                this.loadChatRooms();
            }
        }, 1000);
        
        console.log("✅ Started 1-second polling");
    }
    
    checkInitialUnread() {
        this.checkForNewMessages();
    }
    
    checkForNewMessages() {
        frappe.call({
            method: "vms.get_user_chat_status",
            callback: (response) => {
                if (response.message && response.message.success) {
                    const data = response.message.data;
                    this.updateNotificationDot(data.total_unread > 0);
                }
            },
            error: () => {
                this.checkUnreadFallback();
            }
        });
    }
    
    checkUnreadFallback() {
        frappe.call({
            method: "vms.get_user_chat_rooms",
            args: { page: 1, page_size: 20 },
            callback: (response) => {
                if (response.message && response.message.success) {
                    const rooms = response.message.data.rooms || response.message.data || [];
                    const hasUnread = rooms.some(room => room.unread_count > 0);
                    this.updateNotificationDot(hasUnread);
                }
            }
        });
    }
    
    updateNotificationDot(hasUnread) {
        const notificationDot = document.querySelector('#chat-notification-dot-v2');
        if (notificationDot) {
            notificationDot.style.display = hasUnread ? 'block' : 'none';
            this.hasUnreadMessages = hasUnread;
        }
    }
    
    loadChatRooms() {
        const roomsList = document.querySelector('#enhanced-chat-rooms-list-v2');
        if (!roomsList) return;
        
        frappe.call({
            method: "vms.get_user_chat_rooms",
            args: { page: 1, page_size: 20 },
            callback: (response) => {
                if (response.message && response.message.success) {
                    const rooms = response.message.data.rooms || response.message.data || [];
                    this.displayChatRooms(rooms);
                } else {
                    this.showRoomsError("Failed to load chat rooms");
                }
            },
            error: () => {
                this.showRoomsError("Unable to connect to chat service");
            }
        });
    }
    
    displayChatRooms(rooms) {
        const roomsList = document.querySelector('#enhanced-chat-rooms-list-v2');
        if (!roomsList) return;
        
        if (!rooms || rooms.length === 0) {
            roomsList.innerHTML = `
                <div class="empty-state">
                    <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
                    <div style="font-weight: 600; margin-bottom: 8px;">No conversations yet</div>
                    <div style="font-size: 13px; color: #9e9e9e;">Create a new room to start chatting with your team</div>
                </div>
            `;
            return;
        }
        
        let roomsHTML = '';
        rooms.forEach(room => {
            const roomColor = this.getRoomColor(room.room_type);
            const roomIcon = this.getRoomIcon(room.room_type);
            const unreadClass = room.unread_count > 0 ? 'unread' : '';
            const timeAgo = this.formatTimeAgo(room.last_activity || room.modified);
            
            roomsHTML += `
                <div class="enhanced-room-item ${unreadClass}" onclick="enhancedChatV2.openRoom('${room.name}', '${room.room_name}', '${room.room_type}')">
                    <div class="room-avatar-enhanced" style="background: ${roomColor};">
                        ${roomIcon}
                    </div>
                    <div class="room-info-enhanced">
                        <div class="room-name-enhanced">${room.room_name}</div>
                        <div class="room-last-message-enhanced">
                            ${room.last_message ? room.last_message.substring(0, 60) + (room.last_message.length > 60 ? '...' : '') : 'No messages yet'}
                        </div>
                    </div>
                    <div class="room-meta-enhanced">
                        <div class="room-time-enhanced">${timeAgo}</div>
                        ${room.unread_count > 0 ? `<div class="room-unread-badge">${room.unread_count > 99 ? '99+' : room.unread_count}</div>` : ''}
                    </div>
                </div>
            `;
        });
        
        roomsList.innerHTML = roomsHTML;
    }
    
    showRoomsError(message) {
        const roomsList = document.querySelector('#enhanced-chat-rooms-list-v2');
        if (roomsList) {
            roomsList.innerHTML = `
                <div class="empty-state">
                    <div style="color: #dc3545; font-size: 32px; margin-bottom: 12px;">⚠️</div>
                    <div style="color: #dc3545; font-weight: 600; margin-bottom: 8px;">${message}</div>
                    <button onclick="enhancedChatV2.loadChatRooms()" style="background: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px;">
                        Try Again
                    </button>
                </div>
            `;
        }
    }
    
    showCreateRoomModal() {
        const modalHTML = `
            <div class="chat-modal-overlay" id="create-room-modal" onclick="enhancedChatV2.closeModal(event)">
                <div class="chat-modal" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3 class="modal-title">Create New Chat Room</h3>
                        <button class="modal-close" onclick="enhancedChatV2.closeModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">Room Name *</label>
                            <input type="text" class="form-control" id="room-name-input" placeholder="Enter room name" maxlength="50">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Room Type *</label>
                            <select class="form-control form-select" id="room-type-select">
                                <option value="Group Chat">Group Chat</option>
                                <option value="Team Chat">Team Chat</option>
                                <option value="Announcement">Announcement</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" id="room-description-input" placeholder="Brief description of the room" rows="3" maxlength="200"></textarea>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Privacy Settings</label>
                            <div style="display: flex; align-items: center; gap: 8px; margin-top: 8px;">
                                <input type="checkbox" id="room-private-checkbox" style="width: 16px; height: 16px;">
                                <label for="room-private-checkbox" style="margin: 0; font-size: 14px; color: #6c757d;">Make this room private</label>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary" onclick="enhancedChatV2.closeModal()">Cancel</button>
                        <button class="btn-primary" onclick="enhancedChatV2.createRoom()">Create Room</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Focus on room name input
        setTimeout(() => {
            document.getElementById('room-name-input').focus();
        }, 100);
    }
    
    closeModal(event) {
        if (event && event.target !== event.currentTarget) return;
        
        const modal = document.getElementById('create-room-modal');
        if (modal) {
            modal.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => {
                modal.remove();
            }, 300);
        }
    }
    
    createRoom() {
        const roomName = document.getElementById('room-name-input').value.trim();
        const roomType = document.getElementById('room-type-select').value;
        const description = document.getElementById('room-description-input').value.trim();
        const isPrivate = document.getElementById('room-private-checkbox').checked;
        
        if (!roomName) {
            this.showError('Please enter a room name');
            return;
        }
        
        // Disable create button
        const createBtn = document.querySelector('.btn-primary');
        createBtn.disabled = true;
        createBtn.textContent = 'Creating...';
        
        frappe.call({
            method: "vms.create_chat_room",
            args: {
                room_name: roomName,
                room_type: roomType,
                description: description,
                is_private: isPrivate ? 1 : 0
            },
            callback: (response) => {
                if (response.message && response.message.success) {
                    this.closeModal();
                    this.loadChatRooms();
                    frappe.show_alert({
                        message: `Room "${roomName}" created successfully!`,
                        indicator: 'green'
                    });
                    
                    // Open the newly created room
                    const roomId = response.message.data.room_id;
                    setTimeout(() => {
                        this.openRoom(roomId, roomName, roomType);
                    }, 1000);
                } else {
                    this.showError(response.message?.error || 'Failed to create room');
                    createBtn.disabled = false;
                    createBtn.textContent = 'Create Room';
                }
            },
            error: (error) => {
                this.showError('Unable to create room. Please try again.');
                createBtn.disabled = false;
                createBtn.textContent = 'Create Room';
            }
        });
    }
    
    openRoom(roomId, roomName, roomType) {
        this.currentOpenRoom = roomId;
        this.currentRoomData = { name: roomId, room_name: roomName, room_type: roomType };
        
        // Hide rooms list, show messaging interface
        const roomsList = document.querySelector('#enhanced-chat-rooms-list-v2');
        const createBtn = document.querySelector('.create-room-btn');
        const messagingInterface = document.querySelector('#enhanced-messaging-interface-v2');
        const roomTitle = document.querySelector('#current-room-title-v2');
        const roomStatus = document.querySelector('#current-room-status');
        
        if (roomsList) roomsList.style.display = 'none';
        if (createBtn) createBtn.style.display = 'none';
        if (messagingInterface) messagingInterface.style.display = 'flex';
        if (roomTitle) roomTitle.textContent = roomName;
        if (roomStatus) roomStatus.textContent = `${roomType} • Active`;
        
        this.loadRoomMessages(roomId);
        this.markRoomAsRead(roomId);
    }
    
    backToRoomsList() {
        const roomsList = document.querySelector('#enhanced-chat-rooms-list-v2');
        const createBtn = document.querySelector('.create-room-btn');
        const messagingInterface = document.querySelector('#enhanced-messaging-interface-v2');
        
        if (roomsList) roomsList.style.display = 'block';
        if (createBtn) createBtn.style.display = 'block';
        if (messagingInterface) messagingInterface.style.display = 'none';
        
        this.currentOpenRoom = null;
        this.currentRoomData = null;
        this.cancelReply();
        this.cancelEdit();
        this.loadChatRooms();
    }
    
    loadRoomMessages(roomId) {
        const messagesContainer = document.querySelector('#chat-messages-display-v2');
        if (!messagesContainer) return;
        
        messagesContainer.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <div>Loading messages...</div>
            </div>
        `;
        
        frappe.call({
            method: "vms.get_chat_messages",
            args: { room_id: roomId, page: 1, page_size: 50 },
            callback: (response) => {
                if (response.message && response.message.success) {
                    const messages = response.message.data.messages || [];
                    this.displayMessages(messages);
                } else {
                    messagesContainer.innerHTML = `
                        <div class="empty-state">
                            <div style="color: #dc3545;">❌ Failed to load messages</div>
                        </div>
                    `;
                }
            }
        });
    }
    
    displayMessages(messages) {
        const messagesContainer = document.querySelector('#chat-messages-display-v2');
        if (!messagesContainer) return;
        
        if (messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="empty-state">
                    <div style="font-size: 32px; margin-bottom: 12px;">🎉</div>
                    <div style="font-weight: 600; margin-bottom: 4px;">Start the conversation!</div>
                    <div style="font-size: 13px; color: #9e9e9e;">Be the first to send a message in this room</div>
                </div>
            `;
            return;
        }
        
        const currentUser = frappe.session.user;
        let messagesHTML = '';
        
        messages.reverse().forEach(message => {
            const isOwn = message.sender === currentUser;
            const messageClass = isOwn ? 'own' : 'other';
            const time = this.formatMessageTime(message.timestamp);
            const canEdit = isOwn && !message.is_deleted;
            const canDelete = isOwn && !message.is_deleted;
            
            messagesHTML += `
                <div class="message-bubble ${messageClass}" data-message-id="${message.name}">
                    ${!isOwn ? `<div class="message-sender">${message.sender_name || message.sender}</div>` : ''}
                    
                    ${message.reply_to_message ? `
                        <div class="reply-preview" style="margin-bottom: 8px; background: rgba(255,255,255,0.2); border-left: 3px solid rgba(255,255,255,0.5);">
                            <div style="font-size: 11px; font-weight: 600; margin-bottom: 2px;">↪ Reply to message</div>
                            <div style="font-size: 12px; opacity: 0.8;">Original message content</div>
                        </div>
                    ` : ''}
                    
                    <div class="message-content">${message.is_deleted ? '<em>This message was deleted</em>' : (message.message_content || '')}</div>
                    
                    <div class="message-time">
                        <span>${time}</span>
                        ${message.is_edited ? '<span style="font-style: italic; margin-left: 8px;">edited</span>' : ''}
                    </div>
                    
                    ${!message.is_deleted ? `
                        <div class="message-actions">
                            <button class="message-action-btn" onclick="enhancedChatV2.replyToMessage('${message.name}', '${message.message_content?.substring(0, 50) || ''}', '${message.sender_name || message.sender}')" title="Reply">
                                ↩
                            </button>
                            ${canEdit ? `
                                <button class="message-action-btn" onclick="enhancedChatV2.editMessage('${message.name}', '${message.message_content || ''}')" title="Edit">
                                    ✏
                                </button>
                            ` : ''}
                            ${canDelete ? `
                                <button class="message-action-btn" onclick="enhancedChatV2.deleteMessage('${message.name}')" title="Delete" style="color: #dc3545 !important;">
                                    🗑
                                </button>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        messagesContainer.innerHTML = messagesHTML;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    sendMessage() {
        const messageInput = document.querySelector('#message-input-v2');
        if (!messageInput || !this.currentOpenRoom) return;
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        const sendBtn = document.querySelector('#send-btn-v2');
        sendBtn.disabled = true;
        
        const apiMethod = this.editingMessage ? "vms.edit_message" : "vms.send_message";
        const args = this.editingMessage ? {
            message_id: this.editingMessage.id,
            content: message
        } : {
            room_id: this.currentOpenRoom,
            content: message,
            message_type: 'Text',
            reply_to: this.replyToMessage?.id || null
        };
        
        messageInput.value = '';
        this.adjustTextareaHeight(messageInput);
        
        if (this.editingMessage) {
            this.cancelEdit();
        }
        if (this.replyToMessage) {
            this.cancelReply();
        }
        
        frappe.call({
            method: apiMethod,
            args: args,
            callback: (response) => {
                if (response.message && response.message.success) {
                    setTimeout(() => {
                        this.loadRoomMessages(this.currentOpenRoom);
                    }, 500);
                } else {
                    this.showError('Failed to send message');
                }
                sendBtn.disabled = false;
            },
            error: () => {
                this.showError('Unable to send message');
                sendBtn.disabled = false;
            }
        });
    }
    
    replyToMessage(messageId, content, sender) {
        this.replyToMessage = { id: messageId, content: content, sender: sender };
        
        const replyPreview = document.querySelector('#reply-preview-v2');
        const replySender = document.querySelector('#reply-sender');
        const replyContent = document.querySelector('#reply-content');
        const messageInput = document.querySelector('#message-input-v2');
        
        if (replyPreview) replyPreview.style.display = 'block';
        if (replySender) replySender.textContent = sender;
        if (replyContent) replyContent.textContent = content.length > 50 ? content.substring(0, 50) + '...' : content;
        if (messageInput) messageInput.focus();
    }
    
    cancelReply() {
        this.replyToMessage = null;
        const replyPreview = document.querySelector('#reply-preview-v2');
        if (replyPreview) replyPreview.style.display = 'none';
    }
    
    editMessage(messageId, content) {
        this.editingMessage = { id: messageId, originalContent: content };
        
        const messageInput = document.querySelector('#message-input-v2');
        if (messageInput) {
            messageInput.value = content;
            messageInput.focus();
            messageInput.placeholder = 'Edit your message...';
            this.adjustTextareaHeight(messageInput);
        }
        
        // Visual indication that we're editing
        const sendBtn = document.querySelector('#send-btn-v2');
        if (sendBtn) {
            sendBtn.innerHTML = '<i class="fa fa-check"></i>';
            sendBtn.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
        }
    }
    
    cancelEdit() {
        this.editingMessage = null;
        
        const messageInput = document.querySelector('#message-input-v2');
        const sendBtn = document.querySelector('#send-btn-v2');
        
        if (messageInput) {
            messageInput.value = '';
            messageInput.placeholder = 'Type your message...';
            this.adjustTextareaHeight(messageInput);
        }
        
        if (sendBtn) {
            sendBtn.innerHTML = '<i class="fa fa-paper-plane"></i>';
            sendBtn.style.background = 'linear-gradient(135deg, #007bff, #0056b3)';
        }
    }
    
    deleteMessage(messageId) {
        if (!confirm('Are you sure you want to delete this message?')) return;
        
        frappe.call({
            method: "vms.delete_message",
            args: { message_id: messageId },
            callback: (response) => {
                if (response.message && response.message.success) {
                    setTimeout(() => {
                        this.loadRoomMessages(this.currentOpenRoom);
                    }, 500);
                    frappe.show_alert({
                        message: 'Message deleted',
                        indicator: 'orange'
                    });
                } else {
                    this.showError('Failed to delete message');
                }
            }
        });
    }
    
    handleInputKeydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        } else if (event.key === 'Escape') {
            if (this.editingMessage) {
                this.cancelEdit();
            } else if (this.replyToMessage) {
                this.cancelReply();
            }
        }
    }
    
    adjustTextareaHeight(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
    }
    
    markRoomAsRead(roomId) {
        frappe.call({
            method: "vms.mark_room_as_read",
            args: { room_id: roomId },
            callback: () => {
                setTimeout(() => {
                    this.checkForNewMessages();
                }, 500);
            }
        });
    }
    
    openFullChatApp() {
        try {
            frappe.set_route('List', 'Chat Room');
        } catch (error) {
            window.open('/desk#List/Chat%20Room', '_blank');
        }
    }
    
    showError(message) {
        frappe.show_alert({
            message: message,
            indicator: 'red'
        });
    }
    
    // Utility methods
    getRoomColor(roomType) {
        const colors = {
            'Direct Message': '#28a745',
            'Team Chat': '#007bff',
            'Group Chat': '#17a2b8',
            'Announcement': '#ffc107'
        };
        return colors[roomType] || '#6c757d';
    }
    
    getRoomIcon(roomType) {
        const icons = {
            'Direct Message': '👤',
            'Team Chat': '👥',
            'Group Chat': '💬',
            'Announcement': '📢'
        };
        return icons[roomType] || '💬';
    }
    
    formatTimeAgo(timestamp) {
        if (!timestamp) return '';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffInMinutes = Math.floor((now - time) / (1000 * 60));
        
        if (diffInMinutes < 1) return 'now';
        if (diffInMinutes < 60) return `${diffInMinutes}m`;
        if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h`;
        if (diffInMinutes < 10080) return `${Math.floor(diffInMinutes / 1440)}d`;
        return time.toLocaleDateString();
    }
    
    formatMessageTime(timestamp) {
        if (!timestamp) return '';
        
        const time = new Date(timestamp);
        const now = new Date();
        const isToday = time.toDateString() === now.toDateString();
        
        if (isToday) {
            return time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else {
            return time.toLocaleDateString() + ' ' + time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }
    
    destroy() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
}

// Initialize the enhanced chat
let enhancedChatV2;

function initEnhancedChatV2() {
    if (typeof frappe !== "undefined" && frappe.ready) {
        frappe.ready(() => {
            enhancedChatV2 = new EnhancedChatUIv2();
            
            // Load rooms when dropdown is clicked
            document.addEventListener('click', (e) => {
                const chatDropdown = e.target.closest('.nav-item:has([title="Chat Messages"])');
                if (chatDropdown) {
                    setTimeout(() => {
                        if (enhancedChatV2) {
                            enhancedChatV2.loadChatRooms();
                        }
                    }, 100);
                }
            });
        });
    } else {
        document.addEventListener("DOMContentLoaded", () => {
            enhancedChatV2 = new EnhancedChatUIv2();
        });
    }
}

// Auto-initialize
initEnhancedChatV2();

// Global reference for onclick handlers
window.enhancedChatV2 = enhancedChatV2;