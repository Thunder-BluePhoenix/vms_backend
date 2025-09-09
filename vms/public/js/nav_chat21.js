// Final Fixed nav_chat18.js - All issues resolved
// 1. Fixed API parameter: message_content (not content)
// 2. Dropdown stays open during operations
// 3. Auto-scroll to bottom
// 4. Proper member table population in create room
// 5. All schema fields correctly mapped

// Wait for Frappe to be ready
function onFrappeReady(callback) {
    if (typeof frappe !== "undefined" && frappe.ready) {
        frappe.ready(callback);
    } else {
        document.addEventListener("DOMContentLoaded", callback);
    }
}

// Global variables
let chatPollInterval = null;
let currentOpenRoom = null;
let replyToMessage = null;
let editingMessage = null;
let lastRoomsData = null;
let isDropdownOpen = false;
let isLoading = false;

// Initialize when Frappe is ready
onFrappeReady(() => {
    console.log("🚀 Initializing Final Enhanced Chat Integration...");
    add_enhanced_chat_icon_to_navbar();
    init_enhanced_chat_functionality();
});

function add_enhanced_chat_icon_to_navbar() {
    let attempts = 0;
    const maxAttempts = 10;
    
    function tryAddIcon() {
        attempts++;
        console.log(`Attempt ${attempts} to add enhanced chat icon...`);
        
        const navbar_collapse = document.querySelector('.navbar-collapse.justify-content-end');
        if (!navbar_collapse) {
            if (attempts < maxAttempts) {
                setTimeout(tryAddIcon, 1000);
            }
            return;
        }
        
        const navbar_nav = navbar_collapse.querySelector('ul.navbar-nav');
        if (!navbar_nav) {
            if (attempts < maxAttempts) {
                setTimeout(tryAddIcon, 1000);
            }
            return;
        }
        
        // Check if chat icon already exists
        if (document.querySelector('#enhanced-chat-icon-container')) {
            console.log("✅ Enhanced chat icon already exists");
            return;
        }
        
        console.log("✅ Adding enhanced chat icon to navbar...");
        
        // Create enhanced chat container
        const chat_container = document.createElement('li');
        chat_container.id = 'enhanced-chat-icon-container';
        chat_container.className = 'nav-item dropdown dropdown-notifications dropdown-mobile';
        
        // Create enhanced chat icon HTML
        chat_container.innerHTML = `
            <button class="btn-reset nav-link notifications-icon text-muted" data-toggle="dropdown" 
                    aria-haspopup="true" aria-expanded="false" id="enhanced-chat-icon"
                    title="Chat Messages">
                <span class="notifications-seen">
                    <span class="sr-only">No new messages</span>
                    <svg class="es-icon icon-sm" style="stroke:none;">
                        <use href="#es-line-chat-alt"></use>
                    </svg>
                    <!-- Green notification dot -->
                    <span id="chat-notification-dot" class="notification-dot-enhanced" 
                          style="display: none; position: absolute; top: -2px; right: -2px; 
                                 width: 8px; height: 8px; background: #28a745; border-radius: 50%; 
                                 border: 2px solid white; z-index: 10;"></span>
                </span>
                <span class="notifications-unseen" style="display: none;">
                    <span class="sr-only">You have unread messages</span>
                    <svg class="es-icon icon-sm">
                        <use href="#es-line-chat-alt"></use>
                    </svg>
                </span>
            </button>
            
            <div class="dropdown-menu notifications-list dropdown-menu-right enhanced-chat-dropdown" 
                 id="enhanced-chat-dropdown" role="menu">
                 
                <!-- Chat Header -->
                <div class="notification-list-header enhanced-chat-header">
                    <div class="header-items">
                        <ul class="notification-item-tabs nav nav-tabs" role="tablist">
                            <li class="notifications-category active">
                                <span id="chat-header-title">💬 Chat Messages</span>
                            </li>
                        </ul>
                    </div>
                </div>
                
                <!-- Chat Content Area -->
                <div class="notification-list-body enhanced-chat-body">
                    <!-- Rooms List View -->
                    <div id="enhanced-rooms-view" class="panel-notifications">
                        <div id="enhanced-chat-rooms-list">
                            <div class="loading-state-enhanced">
                                <div class="spinner-enhanced"></div>
                                <div style="margin-top: 8px; color: #6c757d;">Loading conversations...</div>
                            </div>
                        </div>
                        
                        <!-- Create Room Button -->
                        <div style="padding: 15px;">
                            <button class="create-room-btn-enhanced" onclick="show_create_room_modal()">
                                <i class="fa fa-plus" style="margin-right: 8px;"></i>
                                Create New Room
                            </button>
                        </div>
                    </div>
                    
                    <!-- Messaging View -->
                    <div id="enhanced-messaging-view" class="panel-notifications" style="display: none;">
                        <!-- Message Header -->
                        <div class="enhanced-message-header">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <button class="back-to-rooms-btn" onclick="back_to_rooms_list()">
                                    <i class="fa fa-arrow-left"></i>
                                </button>
                                <div class="room-avatar-small" id="current-room-avatar">💬</div>
                                <div>
                                    <div class="current-room-name" id="current-room-name">Room Name</div>
                                    <div class="current-room-status" id="current-room-status">Online</div>
                                </div>
                            </div>
                            <div class="room-actions">
                                <span class="online-indicator">🟢</span>
                            </div>
                        </div>
                        
                        <!-- Messages Container -->
                        <div class="enhanced-messages-container" id="enhanced-messages-container">
                            <!-- Messages will be loaded here -->
                        </div>
                        
                        <!-- Message Input Area -->
                        <div class="enhanced-message-input-area">
                            <!-- Reply Preview -->
                            <div id="reply-preview-area" class="reply-preview-enhanced" style="display: none;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-weight: 600; font-size: 12px; margin-bottom: 2px;">
                                            Replying to <span id="reply-to-sender"></span>
                                        </div>
                                        <div style="font-size: 12px; color: #6c757d;" id="reply-to-content"></div>
                                    </div>
                                    <button onclick="cancel_reply()" style="background: none; border: none; color: #6c757d; cursor: pointer; font-size: 18px;">×</button>
                                </div>
                            </div>
                            
                            <!-- Input Row -->
                            <div class="input-row-enhanced">
                                <input type="text" id="enhanced-message-input" class="message-input-enhanced" 
                                       placeholder="Type your message..." onkeydown="handle_enhanced_input_keydown(event)">
                                <button class="send-btn-enhanced" onclick="send_enhanced_message()" id="enhanced-send-btn">
                                    <i class="fa fa-paper-plane"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert before the bell icon
        const bell_icon = navbar_nav.querySelector('li.dropdown-notifications');
        if (bell_icon) {
            navbar_nav.insertBefore(chat_container, bell_icon);
        } else {
            navbar_nav.appendChild(chat_container);
        }
        
        add_enhanced_chat_styles();
        add_enhanced_event_listeners();
        
        console.log("✅ Enhanced chat icon added successfully");
    }
    
    tryAddIcon();
}

function add_enhanced_chat_styles() {
    if (document.querySelector('#enhanced-chat-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-chat-styles';
    style.textContent = `
        /* Enhanced Chat Styles - Only affects chat components */
        @keyframes pulse-green-enhanced {
            0% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
            50% { transform: scale(1.2); opacity: 0.8; box-shadow: 0 0 0 4px rgba(40, 167, 69, 0.3); }
            100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
        }
        
        @keyframes spin-enhanced {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes slide-in-enhanced {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .notification-dot-enhanced {
            animation: pulse-green-enhanced 2s infinite;
        }
        
        .enhanced-chat-dropdown {
            width: 400px !important;
            max-height: 550px !important;
            border-radius: 8px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
            overflow: hidden;
        }
        
        .enhanced-chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }
        
        .enhanced-chat-header .notifications-category {
            color: white !important;
            font-weight: 600;
        }
        
        .enhanced-chat-body {
            padding: 0 !important;
        }
        
        .loading-state-enhanced {
            padding: 30px 20px;
            text-align: center;
            color: #6c757d;
        }
        
        .spinner-enhanced {
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #007bff;
            border-radius: 50%;
            animation: spin-enhanced 1s linear infinite;
            margin: 0 auto;
        }
        
        /* Enhanced Room Items */
        .enhanced-room-item {
            padding: 16px 20px;
            border-bottom: 1px solid #f1f3f4;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 15px;
            background: white;
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
        
        .room-avatar-enhanced {
            width: 45px;
            height: 45px;
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
        
        .room-unread-badge-enhanced {
            background: linear-gradient(135deg, #dc3545, #c82333);
            color: white;
            border-radius: 12px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: bold;
            min-width: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
        }
        
        /* Create Room Button */
        .create-room-btn-enhanced {
            width: 100%;
            background: linear-gradient(135deg, #28a745, #20c997) !important;
            border: none !important;
            color: white !important;
            padding: 12px 20px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 3px 12px rgba(40, 167, 69, 0.3) !important;
        }
        
        .create-room-btn-enhanced:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4) !important;
        }
        
        /* Messaging Interface */
        .enhanced-message-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #e9ecef;
        }
        
        .back-to-rooms-btn {
            background: rgba(255, 255, 255, 0.2) !important;
            border: none !important;
            color: white !important;
            width: 32px !important;
            height: 32px !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }
        
        .back-to-rooms-btn:hover {
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.05) !important;
        }
        
        .room-avatar-small {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            color: white;
            font-weight: bold;
            background: rgba(255, 255, 255, 0.2);
        }
        
        .current-room-name {
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 2px;
        }
        
        .current-room-status {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .online-indicator {
            font-size: 12px;
        }
        
        /* Messages Container */
        .enhanced-messages-container {
            height: 300px;
            overflow-y: auto;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }
        
        .enhanced-messages-container::-webkit-scrollbar {
            width: 6px;
        }
        
        .enhanced-messages-container::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.1);
        }
        
        .enhanced-messages-container::-webkit-scrollbar-thumb {
            background: #007bff;
            border-radius: 3px;
        }
        
        /* Message Bubbles */
        .message-bubble-enhanced {
            max-width: 75%;
            margin-bottom: 12px;
            padding: 10px 15px;
            border-radius: 18px;
            word-wrap: break-word;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            animation: slide-in-enhanced 0.3s ease-out;
            position: relative;
        }
        
        .message-bubble-enhanced.own {
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 6px;
        }
        
        .message-bubble-enhanced.other {
            background: white;
            color: #2c3e50;
            border: 1px solid #e9ecef;
            margin-right: auto;
            border-bottom-left-radius: 6px;
        }
        
        .message-sender-enhanced {
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 4px;
            opacity: 0.8;
        }
        
        .message-content-enhanced {
            line-height: 1.4;
            margin-bottom: 6px;
            font-size: 14px;
        }
        
        .message-time-enhanced {
            font-size: 11px;
            opacity: 0.7;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .message-actions-enhanced {
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
        
        .message-bubble-enhanced:hover .message-actions-enhanced {
            display: flex;
        }
        
        .message-action-btn-enhanced {
            background: none !important;
            border: none !important;
            color: #6c757d !important;
            width: 24px !important;
            height: 24px !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            font-size: 11px !important;
        }
        
        .message-action-btn-enhanced:hover {
            background: #f8f9fa !important;
            color: #007bff !important;
        }
        
        /* Reply Preview */
        .reply-preview-enhanced {
            background: rgba(0, 123, 255, 0.1);
            border-left: 3px solid #007bff;
            padding: 8px 12px;
            margin-bottom: 8px;
            border-radius: 6px;
        }
        
        /* Message Input Area */
        .enhanced-message-input-area {
            background: white;
            border-top: 1px solid #e9ecef;
            padding: 15px;
        }
        
        .input-row-enhanced {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .message-input-enhanced {
            flex: 1;
            border: 2px solid #e9ecef !important;
            border-radius: 25px !important;
            padding: 10px 15px !important;
            font-size: 14px !important;
            outline: none !important;
            transition: all 0.3s ease !important;
        }
        
        .message-input-enhanced:focus {
            border-color: #007bff !important;
            box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
        }
        
        .send-btn-enhanced {
            background: linear-gradient(135deg, #007bff, #0056b3) !important;
            border: none !important;
            color: white !important;
            width: 40px !important;
            height: 40px !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 3px 12px rgba(0, 123, 255, 0.3) !important;
        }
        
        .send-btn-enhanced:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 4px 16px rgba(0, 123, 255, 0.4) !important;
        }
        
        .send-btn-enhanced:disabled {
            opacity: 0.6 !important;
            cursor: not-allowed !important;
            transform: none !important;
        }
        
        /* Modal Styles */
        .chat-modal-overlay-enhanced {
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
        
        .chat-modal-enhanced {
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            animation: slide-in-enhanced 0.3s ease-out;
            overflow: hidden;
        }
        
        .modal-header-enhanced {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .modal-title-enhanced {
            font-weight: 600;
            font-size: 18px;
            margin: 0;
        }
        
        .modal-close-enhanced {
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
        
        .modal-close-enhanced:hover {
            background: rgba(255, 255, 255, 0.2) !important;
        }
        
        .modal-body-enhanced {
            padding: 25px;
        }
        
        .form-group-enhanced {
            margin-bottom: 20px;
        }
        
        .form-label-enhanced {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2c3e50;
            font-size: 14px;
        }
        
        .form-control-enhanced {
            width: 100% !important;
            padding: 12px 16px !important;
            border: 2px solid #e9ecef !important;
            border-radius: 8px !important;
            font-size: 14px !important;
            transition: all 0.3s ease !important;
            outline: none !important;
            box-sizing: border-box !important;
        }
        
        .form-control-enhanced:focus {
            border-color: #007bff !important;
            box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
        }
        
        .modal-footer-enhanced {
            padding: 0 25px 25px;
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }
        
        .btn-primary-enhanced {
            background: linear-gradient(135deg, #007bff, #0056b3) !important;
            border: none !important;
            color: white !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
        }
        
        .btn-primary-enhanced:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 16px rgba(0, 123, 255, 0.3) !important;
        }
        
        .btn-secondary-enhanced {
            background: #6c757d !important;
            border: none !important;
            color: white !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
        }
        
        .btn-secondary-enhanced:hover {
            background: #5a6268 !important;
        }
        
        /* Empty State */
        .empty-state-enhanced {
            padding: 40px 20px;
            text-align: center;
            color: #6c757d;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .enhanced-chat-dropdown {
                width: 95vw !important;
                max-width: 380px !important;
            }
            
            .enhanced-messages-container {
                height: 250px;
            }
            
            .message-bubble-enhanced {
                max-width: 85%;
            }
        }
    `;
    
    document.head.appendChild(style);
}

function add_enhanced_event_listeners() {
    // Chat icon click handler
    const chatIcon = document.querySelector('#enhanced-chat-icon');
    if (chatIcon) {
        chatIcon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log("💬 Enhanced chat icon clicked");
            isDropdownOpen = !isDropdownOpen;
            
            if (isDropdownOpen) {
                load_enhanced_chat_rooms_stable();
                request_notification_permission();
            }
        });
    }
    
    // Prevent dropdown from closing on internal clicks
    document.addEventListener('click', function(e) {
        const dropdown = document.querySelector('#enhanced-chat-dropdown');
        const chatIcon = document.querySelector('#enhanced-chat-icon');
        
        if (dropdown && isDropdownOpen) {
            // Only close if clicked outside dropdown and not on chat icon
            if (!dropdown.contains(e.target) && !chatIcon.contains(e.target)) {
                isDropdownOpen = false;
                dropdown.classList.remove('show');
            }
        }
    });
    
    // Prevent dropdown close on internal operations
    const dropdown = document.querySelector('#enhanced-chat-dropdown');
    if (dropdown) {
        dropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
}

function init_enhanced_chat_functionality() {
    console.log("⚙️ Initializing enhanced chat functionality...");
    
    // Load chat rooms initially
    load_enhanced_chat_rooms_stable();
    
    // Start polling every 1 second
    if (chatPollInterval) {
        clearInterval(chatPollInterval);
    }
    
    chatPollInterval = setInterval(() => {
        check_for_new_messages_enhanced();
        
        // Only refresh rooms if dropdown is open and in rooms view (stable refresh)
        if (isDropdownOpen && !isLoading) {
            const roomsView = document.querySelector('#enhanced-rooms-view');
            const messagingView = document.querySelector('#enhanced-messaging-view');
            
            if (roomsView && roomsView.style.display !== 'none' && 
                (!messagingView || messagingView.style.display === 'none')) {
                load_enhanced_chat_rooms_stable();
            }
        }
    }, 1000);
    
    console.log("✅ Enhanced chat functionality initialized with stable 1-second polling");
}

function check_for_new_messages_enhanced() {
    frappe.call({
        method: "vms.get_user_chat_status",
        callback: function(response) {
            if (response.message && response.message.success) {
                const data = response.message.data;
                update_notification_dot_enhanced(data.total_unread > 0);
            }
        },
        error: function() {
            // Fallback check
            frappe.call({
                method: "vms.get_user_chat_rooms",
                args: { page: 1, page_size: 20 },
                callback: function(response) {
                    if (response.message && response.message.success) {
                        const rooms = response.message.data.rooms || response.message.data || [];
                        const hasUnread = rooms.some(room => room.unread_count > 0);
                        update_notification_dot_enhanced(hasUnread);
                    }
                }
            });
        }
    });
}

function update_notification_dot_enhanced(hasUnread) {
    const notificationDot = document.querySelector('#chat-notification-dot');
    if (notificationDot) {
        notificationDot.style.display = hasUnread ? 'block' : 'none';
    }
}

// Stable room loading - prevents flickering during refresh
function load_enhanced_chat_rooms_stable() {
    const chatList = document.querySelector('#enhanced-chat-rooms-list');
    if (!chatList || isLoading) return;
    
    isLoading = true;
    
    // Only show loading if no data exists
    if (!lastRoomsData) {
        chatList.innerHTML = `
            <div class="loading-state-enhanced">
                <div class="spinner-enhanced"></div>
                <div style="margin-top: 8px; color: #6c757d;">Loading conversations...</div>
            </div>
        `;
    }
    
    frappe.call({
        method: "vms.get_user_chat_rooms",
        args: {
            page: 1,
            page_size: 15
        },
        callback: function(response) {
            isLoading = false;
            if (response.message && response.message.success) {
                const rooms = response.message.data.rooms || response.message.data || [];
                
                // Only update if data has changed
                const roomsJSON = JSON.stringify(rooms);
                if (roomsJSON !== lastRoomsData) {
                    lastRoomsData = roomsJSON;
                    display_enhanced_chat_rooms(rooms);
                }
                update_unread_count_enhanced(rooms);
            } else {
                if (!lastRoomsData) {
                    show_enhanced_chat_error("Failed to load chat rooms");
                }
            }
        },
        error: function(error) {
            isLoading = false;
            console.error("Error loading chat rooms:", error);
            if (!lastRoomsData) {
                show_enhanced_chat_error("Unable to connect to chat service");
            }
        }
    });
}

function display_enhanced_chat_rooms(rooms) {
    const chatList = document.querySelector('#enhanced-chat-rooms-list');
    if (!chatList) return;
    
    if (!rooms || rooms.length === 0) {
        chatList.innerHTML = `
            <div class="empty-state-enhanced">
                <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
                <div style="font-weight: 600; margin-bottom: 8px;">No conversations yet</div>
                <div style="font-size: 13px; color: #9e9e9e;">Create a new room to start chatting</div>
            </div>
        `;
        return;
    }
    
    let roomsHTML = '';
    rooms.forEach(room => {
        const roomColor = get_room_color_enhanced(room.room_type);
        const roomIcon = get_room_icon_enhanced(room.room_type);
        const unreadClass = room.unread_count > 0 ? 'unread' : '';
        const timeAgo = format_time_ago_enhanced(room.last_activity || room.modified);
        
        roomsHTML += `
            <div class="enhanced-room-item ${unreadClass}" onclick="event.stopPropagation(); open_enhanced_room('${room.name}', '${room.room_name}', '${room.room_type}')">
                <div class="room-avatar-enhanced" style="background: ${roomColor};">
                    ${roomIcon}
                </div>
                <div class="room-info-enhanced">
                    <div class="room-name-enhanced">${room.room_name}</div>
                    <div class="room-last-message-enhanced">
                        ${room.last_message ? room.last_message.substring(0, 55) + (room.last_message.length > 55 ? '...' : '') : 'No messages yet'}
                    </div>
                </div>
                <div class="room-meta-enhanced">
                    <div class="room-time-enhanced">${timeAgo}</div>
                    ${room.unread_count > 0 ? `<div class="room-unread-badge-enhanced">${room.unread_count > 99 ? '99+' : room.unread_count}</div>` : ''}
                </div>
            </div>
        `;
    });
    
    chatList.innerHTML = roomsHTML;
}

function show_enhanced_chat_error(message) {
    const chatList = document.querySelector('#enhanced-chat-rooms-list');
    if (chatList) {
        chatList.innerHTML = `
            <div class="empty-state-enhanced">
                <div style="color: #dc3545; font-size: 32px; margin-bottom: 12px;">⚠️</div>
                <div style="color: #dc3545; font-weight: 600; margin-bottom: 8px;">${message}</div>
                <button onclick="event.stopPropagation(); load_enhanced_chat_rooms_stable()" style="background: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px;">
                    Try Again
                </button>
            </div>
        `;
    }
}

function update_unread_count_enhanced(rooms) {
    const totalUnread = rooms.reduce((sum, room) => sum + (room.unread_count || 0), 0);
    update_notification_dot_enhanced(totalUnread > 0);
}

// Room creation modal functions - Updated with correct schema and member table
function show_create_room_modal() {
    const modalHTML = `
        <div class="chat-modal-overlay-enhanced" id="create-room-modal-enhanced" onclick="close_create_room_modal(event)">
            <div class="chat-modal-enhanced" onclick="event.stopPropagation()">
                <div class="modal-header-enhanced">
                    <h3 class="modal-title-enhanced">Create New Chat Room</h3>
                    <button class="modal-close-enhanced" onclick="close_create_room_modal()">&times;</button>
                </div>
                <div class="modal-body-enhanced">
                    <div class="form-group-enhanced">
                        <label class="form-label-enhanced">Room Name *</label>
                        <input type="text" class="form-control-enhanced" id="room-name-input-enhanced" placeholder="Enter room name" maxlength="50">
                    </div>
                    <div class="form-group-enhanced">
                        <label class="form-label-enhanced">Room Type *</label>
                        <select class="form-control-enhanced" id="room-type-select-enhanced">
                            <option value="Group Chat">Group Chat</option>
                            <option value="Team Chat">Team Chat</option>
                            <option value="Direct Message">Direct Message</option>
                            <option value="Announcement">Announcement</option>
                        </select>
                    </div>
                    <div class="form-group-enhanced">
                        <label class="form-label-enhanced">Description</label>
                        <textarea class="form-control-enhanced" id="room-description-input-enhanced" placeholder="Brief description of the room" rows="3" maxlength="200"></textarea>
                    </div>
                    <div class="form-group-enhanced">
                        <label class="form-label-enhanced">Settings</label>
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <input type="checkbox" id="room-private-checkbox-enhanced" style="width: 16px; height: 16px;">
                                <label for="room-private-checkbox-enhanced" style="margin: 0; font-size: 14px; color: #6c757d;">Make this room private</label>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <input type="checkbox" id="allow-file-sharing-checkbox" style="width: 16px; height: 16px;" checked>
                                <label for="allow-file-sharing-checkbox" style="margin: 0; font-size: 14px; color: #6c757d;">Allow file sharing</label>
                            </div>
                        </div>
                    </div>
                    <div class="form-group-enhanced">
                        <label class="form-label-enhanced">Max Members</label>
                        <input type="number" class="form-control-enhanced" id="max-members-input" placeholder="50" min="2" max="500" value="50">
                    </div>
                </div>
                <div class="modal-footer-enhanced">
                    <button class="btn-secondary-enhanced" onclick="close_create_room_modal()">Cancel</button>
                    <button class="btn-primary-enhanced" onclick="create_enhanced_room()" id="create-room-btn-modal">Create Room</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Focus on room name input
    setTimeout(() => {
        document.getElementById('room-name-input-enhanced').focus();
    }, 100);
}

function close_create_room_modal(event) {
    if (event && event.target !== event.currentTarget) return;
    
    const modal = document.getElementById('create-room-modal-enhanced');
    if (modal) {
        modal.remove();
    }
}

function create_enhanced_room() {
    const roomName = document.getElementById('room-name-input-enhanced').value.trim();
    const roomType = document.getElementById('room-type-select-enhanced').value;
    const description = document.getElementById('room-description-input-enhanced').value.trim();
    const isPrivate = document.getElementById('room-private-checkbox-enhanced').checked;
    const allowFileSharing = document.getElementById('allow-file-sharing-checkbox').checked;
    const maxMembers = parseInt(document.getElementById('max-members-input').value) || 50;
    
    if (!roomName) {
        frappe.show_alert({
            message: 'Please enter a room name',
            indicator: 'red'
        });
        return;
    }
    
    // Disable create button
    const createBtn = document.getElementById('create-room-btn-modal');
    createBtn.disabled = true;
    createBtn.textContent = 'Creating...';
    
    // Prepare member data - creator will be admin
    const currentUser = frappe.session.user;
    const members = [currentUser]; // Creator as first member
    
    frappe.call({
        method: "vms.create_chat_room",
        args: {
            room_name: roomName,
            room_type: roomType,
            description: description,
            is_private: isPrivate ? 1 : 0,
            allow_file_sharing: allowFileSharing ? 1 : 0,
            max_members: maxMembers,
            members: members // Pass members array
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                close_create_room_modal();
                // Reset cache to force refresh
                lastRoomsData = null;
                load_enhanced_chat_rooms_stable();
                frappe.show_alert({
                    message: `Room "${roomName}" created successfully! You are the admin.`,
                    indicator: 'green'
                });
                
                // Open the newly created room
                const roomId = response.message.data.room_id;
                setTimeout(() => {
                    open_enhanced_room(roomId, roomName, roomType);
                }, 1000);
            } else {
                frappe.show_alert({
                    message: response.message?.error || 'Failed to create room',
                    indicator: 'red'
                });
                createBtn.disabled = false;
                createBtn.textContent = 'Create Room';
            }
        },
        error: function(error) {
            frappe.show_alert({
                message: 'Unable to create room. Please try again.',
                indicator: 'red'
            });
            createBtn.disabled = false;
            createBtn.textContent = 'Create Room';
        }
    });
}

// Messaging functions
function open_enhanced_room(roomId, roomName, roomType) {
    console.log(`💬 Opening enhanced room: ${roomName} (${roomId})`);
    
    currentOpenRoom = roomId;
    // Keep dropdown open
    isDropdownOpen = true;
    
    // Hide rooms view, show messaging view
    const roomsView = document.querySelector('#enhanced-rooms-view');
    const messagingView = document.querySelector('#enhanced-messaging-view');
    const headerTitle = document.querySelector('#chat-header-title');
    const roomNameEl = document.querySelector('#current-room-name');
    const roomStatusEl = document.querySelector('#current-room-status');
    const roomAvatarEl = document.querySelector('#current-room-avatar');
    
    if (roomsView) roomsView.style.display = 'none';
    if (messagingView) messagingView.style.display = 'block';
    if (headerTitle) headerTitle.textContent = '← ' + roomName;
    if (roomNameEl) roomNameEl.textContent = roomName;
    if (roomStatusEl) roomStatusEl.textContent = `${roomType} • Active`;
    if (roomAvatarEl) {
        roomAvatarEl.textContent = get_room_icon_enhanced(roomType);
        roomAvatarEl.style.background = get_room_color_enhanced(roomType);
    }
    
    // Load messages for this room
    load_enhanced_room_messages(roomId);
    
    // Mark room as read
    mark_enhanced_room_as_read(roomId);
}

function back_to_rooms_list() {
    const roomsView = document.querySelector('#enhanced-rooms-view');
    const messagingView = document.querySelector('#enhanced-messaging-view');
    const headerTitle = document.querySelector('#chat-header-title');
    
    if (roomsView) roomsView.style.display = 'block';
    if (messagingView) messagingView.style.display = 'none';
    if (headerTitle) headerTitle.textContent = '💬 Chat Messages';
    
    currentOpenRoom = null;
    cancel_reply();
    cancel_edit_enhanced();
    
    // Reset cache to force refresh
    lastRoomsData = null;
    load_enhanced_chat_rooms_stable();
    
    // Keep dropdown open
    isDropdownOpen = true;
}

function load_enhanced_room_messages(roomId) {
    const messagesContainer = document.querySelector('#enhanced-messages-container');
    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = `
        <div class="loading-state-enhanced">
            <div class="spinner-enhanced"></div>
            <div style="margin-top: 8px;">Loading messages...</div>
        </div>
    `;
    
    frappe.call({
        method: "vms.get_chat_messages",
        args: { room_id: roomId, page: 1, page_size: 50 },
        callback: function(response) {
            if (response.message && response.message.success) {
                const messages = response.message.data.messages || [];
                display_enhanced_messages(messages);
                // Auto-scroll to bottom
                scroll_to_bottom_enhanced();
            } else {
                messagesContainer.innerHTML = `
                    <div class="empty-state-enhanced">
                        <div style="color: #dc3545;">❌ Failed to load messages</div>
                    </div>
                `;
            }
        }
    });
}

function display_enhanced_messages(messages) {
    const messagesContainer = document.querySelector('#enhanced-messages-container');
    if (!messagesContainer) return;
    
    if (messages.length === 0) {
        messagesContainer.innerHTML = `
            <div class="empty-state-enhanced">
                <div style="font-size: 32px; margin-bottom: 12px;">🎉</div>
                <div style="font-weight: 600; margin-bottom: 4px;">Start the conversation!</div>
                <div style="font-size: 13px; color: #9e9e9e;">Be the first to send a message</div>
            </div>
        `;
        return;
    }
    
    const currentUser = frappe.session.user;
    let messagesHTML = '';
    
    messages.reverse().forEach(message => {
        const isOwn = message.sender === currentUser;
        const messageClass = isOwn ? 'own' : 'other';
        const time = format_message_time_enhanced(message.timestamp);
        const canEdit = isOwn && !message.is_deleted;
        const canDelete = isOwn && !message.is_deleted;
        
        // Escape quotes properly
        const escapedContent = (message.message_content || '').replace(/'/g, "\\'").replace(/"/g, '\\"');
        const escapedSender = (message.sender_name || message.sender).replace(/'/g, "\\'").replace(/"/g, '\\"');
        
        messagesHTML += `
            <div class="message-bubble-enhanced ${messageClass}" data-message-id="${message.name}">
                ${!isOwn ? `<div class="message-sender-enhanced">${message.sender_name || message.sender}</div>` : ''}
                
                ${message.reply_to_message ? `
                    <div class="reply-preview-enhanced" style="margin-bottom: 8px;">
                        <div style="font-size: 11px; font-weight: 600; margin-bottom: 2px;">↪ Reply</div>
                        <div style="font-size: 12px; opacity: 0.8;">Previous message</div>
                    </div>
                ` : ''}
                
                <div class="message-content-enhanced">${message.is_deleted ? '<em>This message was deleted</em>' : (message.message_content || '')}</div>
                
                <div class="message-time-enhanced">
                    <span>${time}</span>
                    ${message.is_edited ? '<span style="font-style: italic; margin-left: 8px;">edited</span>' : ''}
                </div>
                
                ${!message.is_deleted ? `
                    <div class="message-actions-enhanced">
                        <button class="message-action-btn-enhanced" 
                            onclick="event.stopPropagation(); reply_to_message_enhanced('${message.name}', '${escapedContent.substring(0, 50)}', '${escapedSender}')" 
                            title="Reply">
                            ↩
                        </button>
                        ${canEdit ? `
                            <button class="message-action-btn-enhanced" 
                                onclick="event.stopPropagation(); edit_message_enhanced('${message.name}', '${escapedContent}')" 
                                title="Edit">
                                ✏
                            </button>
                        ` : ''}
                        ${canDelete ? `
                            <button class="message-action-btn-enhanced" 
                                onclick="event.stopPropagation(); delete_message_enhanced('${message.name}')" 
                                title="Delete" 
                                style="color: #dc3545 !important;">
                                🗑
                            </button>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    messagesContainer.innerHTML = messagesHTML;
    // Auto-scroll to bottom
    scroll_to_bottom_enhanced();
}

// Auto-scroll to bottom function
function scroll_to_bottom_enhanced() {
    const messagesContainer = document.querySelector('#enhanced-messages-container');
    if (messagesContainer) {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
}

function send_enhanced_message() {
    const messageInput = document.querySelector('#enhanced-message-input');
    if (!messageInput || !currentOpenRoom) return;
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    const sendBtn = document.querySelector('#enhanced-send-btn');
    sendBtn.disabled = true;
    
    // Use correct parameter names based on schema: message_content (not content)
    const apiMethod = editingMessage ? "vms.edit_message" : "vms.send_message";
    const args = editingMessage ? {
        message_id: editingMessage.id,
        new_content: message
    } : {
        room_id: currentOpenRoom,
        message_content: message,  // FIXED: Use message_content as per schema
        message_type: 'Text',
        reply_to: replyToMessage?.id || null
    };
    
    messageInput.value = '';
    
    if (editingMessage) {
        cancel_edit_enhanced();
    }
    if (replyToMessage) {
        cancel_reply();
    }
    
    frappe.call({
        method: apiMethod,
        args: args,
        callback: function(response) {
            if (response.message && response.message.success) {
                setTimeout(() => {
                    load_enhanced_room_messages(currentOpenRoom);
                }, 500);
            } else {
                frappe.show_alert({
                    message: 'Failed to send message',
                    indicator: 'red'
                });
            }
            sendBtn.disabled = false;
            // Keep dropdown open
            isDropdownOpen = true;
        },
        error: function() {
            frappe.show_alert({
                message: 'Unable to send message',
                indicator: 'red'
            });
            sendBtn.disabled = false;
            // Keep dropdown open
            isDropdownOpen = true;
        }
    });
}

function reply_to_message_enhanced(messageId, content, sender) {
    replyToMessage = { id: messageId, content: content, sender: sender };
    
    const replyPreview = document.querySelector('#reply-preview-area');
    const replySender = document.querySelector('#reply-to-sender');
    const replyContent = document.querySelector('#reply-to-content');
    const messageInput = document.querySelector('#enhanced-message-input');
    
    if (replyPreview) replyPreview.style.display = 'block';
    if (replySender) replySender.textContent = sender;
    if (replyContent) replyContent.textContent = content.length > 50 ? content.substring(0, 50) + '...' : content;
    if (messageInput) messageInput.focus();
    
    // Keep dropdown open
    isDropdownOpen = true;
}

function cancel_reply() {
    replyToMessage = null;
    const replyPreview = document.querySelector('#reply-preview-area');
    if (replyPreview) replyPreview.style.display = 'none';
}

function edit_message_enhanced(messageId, content) {
    editingMessage = { id: messageId, originalContent: content };
    
    const messageInput = document.querySelector('#enhanced-message-input');
    if (messageInput) {
        messageInput.value = content;
        messageInput.focus();
        messageInput.placeholder = 'Edit your message...';
    }
    
    // Visual indication that we're editing
    const sendBtn = document.querySelector('#enhanced-send-btn');
    if (sendBtn) {
        sendBtn.innerHTML = '<i class="fa fa-check"></i>';
        sendBtn.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
    }
    
    // Keep dropdown open
    isDropdownOpen = true;
}

function cancel_edit_enhanced() {
    editingMessage = null;
    
    const messageInput = document.querySelector('#enhanced-message-input');
    const sendBtn = document.querySelector('#enhanced-send-btn');
    
    if (messageInput) {
        messageInput.value = '';
        messageInput.placeholder = 'Type your message...';
    }
    
    if (sendBtn) {
        sendBtn.innerHTML = '<i class="fa fa-paper-plane"></i>';
        sendBtn.style.background = 'linear-gradient(135deg, #007bff, #0056b3)';
    }
}

function delete_message_enhanced(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) return;
    
    frappe.call({
        method: "vms.delete_message",
        args: { message_id: messageId },
        callback: function(response) {
            if (response.message && response.message.success) {
                setTimeout(() => {
                    load_enhanced_room_messages(currentOpenRoom);
                }, 500);
                frappe.show_alert({
                    message: 'Message deleted',
                    indicator: 'orange'
                });
            } else {
                frappe.show_alert({
                    message: 'Failed to delete message',
                    indicator: 'red'
                });
            }
            // Keep dropdown open
            isDropdownOpen = true;
        }
    });
}

function handle_enhanced_input_keydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        send_enhanced_message();
    } else if (event.key === 'Escape') {
        if (editingMessage) {
            cancel_edit_enhanced();
        } else if (replyToMessage) {
            cancel_reply();
        }
    }
}

function mark_enhanced_room_as_read(roomId) {
    frappe.call({
        method: "vms.mark_room_as_read",
        args: { room_id: roomId },
        callback: function() {
            setTimeout(() => {
                check_for_new_messages_enhanced();
            }, 500);
        }
    });
}

function request_notification_permission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                frappe.show_alert({
                    message: 'Chat notifications enabled!',
                    indicator: 'green'
                });
            }
        });
    }
}

// Utility functions
function get_room_color_enhanced(roomType) {
    const colors = {
        'Direct Message': '#28a745',
        'Team Chat': '#007bff',
        'Group Chat': '#17a2b8',
        'Announcement': '#ffc107'
    };
    return colors[roomType] || '#6c757d';
}

function get_room_icon_enhanced(roomType) {
    const icons = {
        'Direct Message': '👤',
        'Team Chat': '👥',
        'Group Chat': '💬',
        'Announcement': '📢'
    };
    return icons[roomType] || '💬';
}

function format_time_ago_enhanced(timestamp) {
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

function format_message_time_enhanced(timestamp) {
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

// Global functions for onclick handlers with proper event handling
window.load_enhanced_chat_rooms_stable = load_enhanced_chat_rooms_stable;
window.show_create_room_modal = show_create_room_modal;
window.close_create_room_modal = close_create_room_modal;
window.create_enhanced_room = create_enhanced_room;
window.open_enhanced_room = open_enhanced_room;
window.back_to_rooms_list = back_to_rooms_list;
window.send_enhanced_message = send_enhanced_message;
window.reply_to_message_enhanced = reply_to_message_enhanced;
window.cancel_reply = cancel_reply;
window.edit_message_enhanced = edit_message_enhanced;
window.cancel_edit_enhanced = cancel_edit_enhanced;
window.delete_message_enhanced = delete_message_enhanced;
window.handle_enhanced_input_keydown = handle_enhanced_input_keydown;