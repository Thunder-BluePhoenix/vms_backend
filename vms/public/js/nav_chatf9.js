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
let chatEnabled = false;

// Initialize when Frappe is ready
onFrappeReady(() => {
    console.log("🚀 Checking chat settings...");
    check_chat_enabled();
});



function check_chat_enabled() {
    // Check if chat is enabled in settings
    frappe.call({
        method: "vms.chat_vms.doctype.chat_settings.chat_settings.is_chat_enabled",
        callback: function(response) {
            chatEnabled = response.message;
            if (chatEnabled) {
                console.log("✅ Chat is enabled, initializing...");
                add_enhanced_chat_icon_to_navbar();
                init_enhanced_chat_functionality();
            } else {
                console.log("❌ Chat is disabled in settings");
                // Remove chat icon if it exists
                const existingIcon = document.querySelector('#enhanced-chat-icon-container');
                if (existingIcon) {
                    existingIcon.remove();
                }
                // Clear any running intervals
                if (chatPollInterval) {
                    clearInterval(chatPollInterval);
                    chatPollInterval = null;
                }
            }
        },
        error: function() {
            // Default to enabled if can't get settings
            console.log("⚠️ Could not get chat settings, defaulting to enabled");
            chatEnabled = true;
            add_enhanced_chat_icon_to_navbar();
            init_enhanced_chat_functionality();
        }
    });
}





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
                        <!-- Sticky Create Room Button -->
                        <div class="enhanced-create-room-container">
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
                                    <div class="current-room-status" id="current-room-status">online</div>
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

        /* Sticky create room button */
        .enhanced-create-room-container {
            position: sticky;
            bottom: 0;
            background: white;
            padding: 12px 15px;
            border-top: 1px solid #e9ecef;
            z-index: 5;
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
    const chatIcon = document.querySelector('#enhanced-chat-icon');
    const dropdown = document.querySelector('#enhanced-chat-dropdown');

    // Chat icon click handler (manual toggle)
    if (chatIcon && dropdown) {
        chatIcon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log("💬 Enhanced chat icon clicked");

            isDropdownOpen = !isDropdownOpen;
            if (isDropdownOpen) {
                dropdown.classList.add('show');
                load_enhanced_chat_rooms_stable();
                request_notification_permission();
            } else {
                dropdown.classList.remove('show');
            }
        });
    }

    // Prevent dropdown from closing on internal clicks
    if (dropdown) {
        dropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    // Close when clicking outside (not on chat icon or dropdown)
    document.addEventListener('click', function(e) {
        if (dropdown && isDropdownOpen) {
            if (!dropdown.contains(e.target) && !chatIcon.contains(e.target)) {
                isDropdownOpen = false;
                dropdown.classList.remove('show');
            }
        }
    });

    // Optional: close button inside dropdown (if you add it in header)
    const closeBtn = document.querySelector('#close-chat-dropdown');
    if (closeBtn && dropdown) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            isDropdownOpen = false;
            dropdown.classList.remove('show');
        });
    }
}

function init_enhanced_chat_functionality() {
    if (!chatEnabled) return;
    
    console.log("⚙️ Initializing enhanced chat functionality...");
    
    // Set user status to online
    // update_user_chat_status('online');
    
    // Load chat rooms initially
    load_enhanced_chat_rooms_stable();
    
    // Start polling every 1 second
    if (chatPollInterval) {
        clearInterval(chatPollInterval);
    }
    
    chatPollInterval = setInterval(() => {
        // Periodically check if chat is still enabled (every 30 seconds)
        if (Date.now() % 30000 < 1000) {
            check_chat_enabled();
        }
        
        if (chatEnabled) {
            check_for_new_messages_enhanced();
            
            if (isDropdownOpen && !isLoading) {
                const roomsView = document.querySelector('#enhanced-rooms-view');
                const messagingView = document.querySelector('#enhanced-messaging-view');
                
                if (roomsView && roomsView.style.display !== 'none') {
                    // Refresh rooms if in rooms view
                    load_enhanced_chat_rooms_stable();
                } else if (messagingView && messagingView.style.display !== 'none' && currentOpenRoom) {
                    // Refresh messages if in chat view
                    load_enhanced_room_messages(currentOpenRoom);
                }
            }
        }
    }, 1000);
    
    // Set user offline on page unload
    window.addEventListener('beforeunload', () => {
        if (chatEnabled) {
            update_user_chat_status('offline');
        }
    });
    
    console.log("✅ Enhanced chat functionality initialized");
}

function edit_chat_room(room_id, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log(`🔧 Editing chat room: ${room_id}`);
    
    frappe.call({
        method: "vms.get_room_details",
        args: { room_id: room_id },
        callback: function(response) {
            if (response.message && response.message.success && response.message.data) {
                const roomData = response.message.data;
                const room = roomData.room || roomData;
                
                if (room && (room.room_name || room.name)) {
                    show_edit_room_dialog_with_enhanced_members(room);
                } else {
                    frappe.show_alert({
                        message: 'Failed to add users: ' + (response.message?.error || 'Unknown error'),
                        indicator: 'red'
                    });
                }
            } else {
                frappe.show_alert({
                    message: 'Invalid response from server',
                    indicator: 'red'
                });
            }
        },
        error: function() {
            frappe.show_alert({
                message: 'Network error adding users',
                indicator: 'red'
            });
        }
    });
}


// 10. NEW: Load current members
function load_current_members(dialog, roomId) {
    frappe.call({
        method: "vms.get_room_details",
        args: { room_id: roomId },
        callback: function(response) {
            if (response.message && response.message.success) {
                const roomData = response.message.data;
                const room = roomData.room || roomData;
                
                let membersHTML = `
                    <div class="current-members-container">
                        <div style="max-height: 250px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 8px;">
                            <table class="table table-sm mb-0">
                                <thead style="background: #f8f9fa; position: sticky; top: 0;">
                                    <tr>
                                        <th style="padding: 10px;">Member</th>
                                        <th style="padding: 10px;">Role</th>
                                        <th style="padding: 10px;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                `;
                
                if (room.members && room.members.length > 0) {
                    room.members.forEach(member => {
                        const memberName = member.user_full_name || member.full_name || member.user;
                        const memberRole = member.role || 'Member';
                        const userId = member.user || member.name;
                        const isCurrentUser = userId === frappe.session.user;
                        
                        membersHTML += `
                            <tr data-user="${userId}">
                                <td style="padding: 8px 10px;">
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <div style="width: 24px; height: 24px; border-radius: 50%; background: #007bff; color: white; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold;">
                                            ${memberName.charAt(0).toUpperCase()}
                                        </div>
                                        <span style="font-size: 13px;">${memberName}</span>
                                        ${isCurrentUser ? '<small style="color: #007bff;">(You)</small>' : ''}
                                    </div>
                                </td>
                                <td style="padding: 8px 10px;">
                                    <select class="form-control form-control-sm member-role-select" data-user="${userId}" style="font-size: 12px;">
                                        <option value="Member" ${memberRole === 'Member' ? 'selected' : ''}>Member</option>
                                        <option value="Moderator" ${memberRole === 'Moderator' ? 'selected' : ''}>Moderator</option>
                                        <option value="Admin" ${memberRole === 'Admin' ? 'selected' : ''}>Admin</option>
                                    </select>
                                </td>
                                <td style="padding: 8px 10px;">
                                    ${!isCurrentUser ? `
                                        <button class="btn btn-sm btn-outline-danger remove-member-btn" data-user="${userId}" style="font-size: 11px; padding: 2px 6px;">
                                            <i class="fa fa-times"></i>
                                        </button>
                                    ` : `
                                        <span style="font-size: 11px; color: #6c757d;">-</span>
                                    `}
                                </td>
                            </tr>
                        `;
                    });
                } else {
                    membersHTML += `
                        <tr>
                            <td colspan="3" style="padding: 20px; text-align: center; color: #6c757d;">
                                No members found
                            </td>
                        </tr>
                    `;
                }
                
                membersHTML += `
                            </tbody>
                        </table>
                    </div>
                </div>
                `;
                
                dialog.fields_dict.members_html.$wrapper.html(membersHTML);
                
                // Add event handlers for member management
                setup_member_management_handlers(dialog, roomId);
            }
        }
    });
}

// 11. NEW: Setup member management handlers
function setup_member_management_handlers(dialog, roomId) {
    // Handle role changes
    dialog.$wrapper.off('change', '.member-role-select').on('change', '.member-role-select', function() {
        const $select = $(this);
        const user = $select.data('user');
        const newRole = $select.val();
        const originalRole = $select.find('option:not(:selected)').first().val();
        
        frappe.call({
            method: 'vms.update_member_role',
            args: {
                room_id: roomId,
                user_id: user,
                new_role: newRole
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: `Role updated for ${user}`,
                        indicator: 'green'
                    });
                } else {
                    $select.val(originalRole);
                    frappe.show_alert({
                        message: 'Failed to update role',
                        indicator: 'red'
                    });
                }
            }
        });
    });
    
    // Handle member removal
    dialog.$wrapper.off('click', '.remove-member-btn').on('click', '.remove-member-btn', function(e) {
        e.preventDefault();
        const user = $(this).data('user');
        const $row = $(this).closest('tr');
        
        frappe.confirm(
            `Are you sure you want to remove ${user} from this room?`,
            () => {
                frappe.call({
                    method: 'vms.remove_room_member',
                    args: {
                        room_id: roomId,
                        user_id: user
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            $row.fadeOut(300, function() {
                                $(this).remove();
                            });
                            frappe.show_alert({
                                message: `${user} removed from room`,
                                indicator: 'green'
                            });
                        } else {
                            frappe.show_alert({
                                message: 'Failed to remove member',
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
        );
    });
}

function show_edit_room_dialog(room) {
    console.log("📝 Showing edit dialog for room:", room);
    
    const roomName = room.room_name || room.name || room.title || 'Unknown Room';
    const roomDescription = room.description || '';
    const roomType = room.room_type || 'Group Chat';
    const roomId = room.name || room.id || room.room_id;
    
    if (!roomId) {
        frappe.msgprint({
            title: 'Error',
            message: 'Cannot edit room: Missing room identifier',
            indicator: 'red'
        });
        return;
    }
    
    // Create dialog with enhanced fields including Add Members
    const dialog = new frappe.ui.Dialog({
        title: `Edit Room: ${roomName}`,
        fields: [
            {
                fieldtype: 'Section Break',
                label: 'Basic Information'
            },
            {
                label: 'Room Name',
                fieldname: 'room_name',
                fieldtype: 'Data',
                default: roomName,
                reqd: 1
            },
            {
                label: 'Description',
                fieldname: 'description',
                fieldtype: 'Text',
                default: roomDescription
            },
            {
                label: 'Room Type',
                fieldname: 'room_type',
                fieldtype: 'Select',
                options: 'Direct Message\nTeam Chat\nGroup Chat\nAnnouncement',
                default: roomType,
                reqd: 1
            },
            {
                fieldtype: 'Section Break',
                label: 'Room Settings'
            },
            {
                label: 'Private Room',
                fieldname: 'is_private',
                fieldtype: 'Check',
                default: room.is_private || 0
            },
            {
                label: 'Allow File Sharing',
                fieldname: 'allow_file_sharing',
                fieldtype: 'Check',
                default: room.allow_file_sharing !== undefined ? room.allow_file_sharing : 1
            },
            {
                label: 'Max Members',
                fieldname: 'max_members',
                fieldtype: 'Int',
                default: room.max_members || 50,
                description: 'Maximum number of members allowed in this room'
            },
            {
                fieldtype: 'Section Break',
                label: 'Add New Members'
            },
            {
                label: 'Search and Add Users',
                fieldname: 'new_members',
                fieldtype: 'MultiSelectList',
                get_data: function(txt) {
                    // FIXED: Enhanced user search with better filtering
                    return frappe.call({
                        method: 'vms.search_users_for_room',
                        args: {
                            search_term: txt || '',
                            room_id: roomId,
                            exclude_existing: 1  // Don't show already added members
                        }
                    }).then(r => {
                        if (r.message && r.message.success) {
                            return r.message.data.map(user => ({
                                value: user.name,
                                description: `${user.full_name || user.first_name || user.name} (${user.email || user.name})`
                            }));
                        }
                        return [];
                    }).catch(err => {
                        console.error('Error searching users:', err);
                        return [];
                    });
                },
                description: 'Search for users by name or email to add them to this room'
            },
            {
                fieldtype: 'Section Break',
                label: 'Current Members'
            },
            {
                label: 'Members List',
                fieldname: 'members_html',
                fieldtype: 'HTML',
                options: '<div id="members-container" style="min-height: 200px;"><div class="text-center text-muted">Loading members...</div></div>'
            }
        ],
        primary_action_label: 'Update Room',
        primary_action(values) {
            update_chat_room_enhanced(roomId, values, dialog);
        },
        secondary_action_label: 'Cancel'
    });
    
    dialog.show();
    
    // Load members after dialog is shown
    load_room_members_enhanced(roomId, dialog);
}



function update_chat_room_with_error_handling(room_id, values, dialog) {
    if (!values.room_name || values.room_name.trim() === '') {
        frappe.msgprint({
            title: 'Validation Error',
            message: 'Room name cannot be empty',
            indicator: 'red'
        });
        return;
    }
    
    const primaryBtn = dialog.$wrapper.find('.btn-primary');
    const originalText = primaryBtn.text();
    
    primaryBtn.prop('disabled', true).text('Updating...');
    
    frappe.call({
        method: 'vms.update_room_settings',
        args: {
            room_id: room_id,
            settings: {
                room_name: values.room_name.trim(),
                description: values.description || '',
                room_type: values.room_type,
                is_private: values.is_private || 0,
                allow_file_sharing: values.allow_file_sharing !== undefined ? values.allow_file_sharing : 1,
                max_members: values.max_members || 50
            }
        },
        callback: function(r) {
            primaryBtn.prop('disabled', false).text(originalText);
            
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: 'Room updated successfully',
                    indicator: 'green'
                });
                
                dialog.hide();
                
                // Refresh room list
                lastRoomsData = null;
                load_enhanced_chat_rooms_stable();
                
                if (currentOpenRoom === room_id) {
                    lastMessagesData = null;
                    load_enhanced_room_messages(room_id);
                }
            } else {
                // FIXED: Handle server messages properly
                let errorMessage = 'Failed to update room';
                
                if (r.message && typeof r.message === 'string') {
                    errorMessage = r.message;
                } else if (r.message && r.message.error) {
                    errorMessage = r.message.error;
                } else if (r.servermessages) {
                    try {
                        const serverMessages = JSON.parse(r.servermessages);
                        if (serverMessages.length > 0) {
                            const firstMessage = JSON.parse(serverMessages[0]);
                            errorMessage = firstMessage.message || errorMessage;
                        }
                    } catch (e) {
                        console.error('Error parsing server messages:', e);
                    }
                }
                
                frappe.show_alert({
                    message: errorMessage,
                    indicator: 'red'
                });
            }
        },
        error: function(xhr, textStatus, errorThrown) {
            primaryBtn.prop('disabled', false).text(originalText);
            
            let errorMessage = 'Network error. Please check your connection.';
            
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            } else if (xhr.responseText) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    errorMessage = response.message || errorMessage;
                } catch (e) {
                    // Use default error message
                }
            }
            
            frappe.show_alert({
                message: errorMessage,
                indicator: 'red'
            });
        }
    });
}



function update_chat_room_fixed(room_id, values, dialog) {
    if (!values.room_name || values.room_name.trim() === '') {
        frappe.msgprint({
            title: 'Validation Error',
            message: 'Room name cannot be empty',
            indicator: 'red'
        });
        return;
    }
    
    // FIXED: Correct way to disable and change button text in Frappe Dialog
    const primaryBtn = dialog.$wrapper.find('.btn-primary');
    const originalText = primaryBtn.text();
    
    primaryBtn.prop('disabled', true).text('Updating...');
    
    frappe.call({
        method: 'vms.update_room_settings',
        args: {
            room_id: room_id,
            settings: {
                room_name: values.room_name.trim(),
                description: values.description || '',
                room_type: values.room_type,
                is_private: values.is_private || 0,
                allow_file_sharing: values.allow_file_sharing !== undefined ? values.allow_file_sharing : 1,
                max_members: values.max_members || 50
            }
        },
        callback: function(r) {
            // FIXED: Restore button state
            primaryBtn.prop('disabled', false).text(originalText);
            
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: 'Room updated successfully',
                    indicator: 'green'
                });
                
                dialog.hide();
                
                // Refresh room list
                lastRoomsData = null;
                load_enhanced_chat_rooms_stable();
                
                // Refresh current room if open
                if (currentOpenRoom === room_id) {
                    lastMessagesData = null;
                    load_enhanced_room_messages(room_id);
                }
            } else {
                frappe.msgprint({
                    title: 'Update Failed',
                    message: r.message?.error || 'Failed to update room',
                    indicator: 'red'
                });
            }
        },
        error: function(error) {
            // FIXED: Restore button state on error
            primaryBtn.prop('disabled', false).text(originalText);
            
            frappe.msgprint({
                title: 'Network Error',
                message: 'Unable to update room. Please check your connection.',
                indicator: 'red'
            });
        }
    });
}


function update_chat_room_enhanced(room_id, values, dialog) {
    if (!values.room_name || values.room_name.trim() === '') {
        frappe.msgprint({
            title: 'Validation Error',
            message: 'Room name cannot be empty',
            indicator: 'red'
        });
        return;
    }
    
    dialog.set_primary_action_label('Updating...');
    dialog.disable_primary_action();
    
    // First update room settings
    frappe.call({
        method: 'vms.update_room_settings',
        args: {
            room_id: room_id,
            settings: {
                room_name: values.room_name.trim(),
                description: values.description || '',
                room_type: values.room_type,
                is_private: values.is_private || 0,
                allow_file_sharing: values.allow_file_sharing !== undefined ? values.allow_file_sharing : 1,
                max_members: values.max_members || 50
            }
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                // Add new members if any selected
                if (values.new_members && values.new_members.length > 0) {
                    add_multiple_members(room_id, values.new_members, dialog);
                } else {
                    finish_room_update(dialog, room_id);
                }
            } else {
                dialog.set_primary_action_label('Update Room');
                dialog.enable_primary_action();
                frappe.msgprint({
                    title: 'Update Failed',
                    message: r.message?.error || 'Failed to update room settings',
                    indicator: 'red'
                });
            }
        },
        error: function(error) {
            dialog.set_primary_action_label('Update Room');
            dialog.enable_primary_action();
            frappe.msgprint({
                title: 'Network Error',
                message: 'Unable to update room. Please check your connection.',
                indicator: 'red'
            });
        }
    });
}

// 6. NEW: Add multiple members function
function add_multiple_members(room_id, members, dialog) {
    let addedCount = 0;
    let errorCount = 0;
    
    const addMember = (index) => {
        if (index >= members.length) {
            // All members processed
            const message = addedCount > 0 ? 
                `Room updated successfully! ${addedCount} member(s) added.` :
                'Room updated successfully!';
            
            if (errorCount > 0) {
                message += ` (${errorCount} member(s) could not be added)`;
            }
            
            finish_room_update(dialog, room_id, message);
            return;
        }
        
        frappe.call({
            method: 'vms.add_room_member',
            args: {
                room_id: room_id,
                user_id: members[index],
                role: 'Member'
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    addedCount++;
                } else {
                    errorCount++;
                    console.error(`Failed to add member ${members[index]}:`, r.message);
                }
                // Process next member
                addMember(index + 1);
            },
            error: function() {
                errorCount++;
                // Process next member
                addMember(index + 1);
            }
        });
    };
    
    // Start adding members
    addMember(0);
}

// 7. NEW: Finish room update
function finish_room_update(dialog, room_id, customMessage) {
    dialog.set_primary_action_label('Update Room');
    dialog.enable_primary_action();
    
    frappe.show_alert({
        message: customMessage || 'Room updated successfully',
        indicator: 'green'
    });
    
    dialog.hide();
    
    // Refresh the room list and current room if needed
    lastRoomsData = null;
    load_enhanced_chat_rooms_stable();
    
    if (currentOpenRoom === room_id) {
        lastMessagesData = null;
        load_enhanced_room_messages(room_id);
    }
}


// 4. NEW: Function to load room members separately
function load_room_members_enhanced(roomId, dialog) {
    frappe.call({
        method: "vms.get_room_details",
        args: { room_id: roomId },
        callback: function(response) {
            if (response.message && response.message.success) {
                const roomData = response.message.data;
                const room = roomData.room || roomData;
                
                let membersHTML = `
                    <div class="members-management-container">
                        <div class="members-table-container" style="max-height: 250px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 8px; background: white;">
                            <table class="table table-sm table-hover mb-0">
                                <thead style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); position: sticky; top: 0; z-index: 10;">
                                    <tr>
                                        <th style="padding: 12px; font-size: 13px; font-weight: 600; color: #495057; border-bottom: 2px solid #dee2e6;">Member</th>
                                        <th style="padding: 12px; font-size: 13px; font-weight: 600; color: #495057; border-bottom: 2px solid #dee2e6;">Role</th>
                                        <th style="padding: 12px; font-size: 13px; font-weight: 600; color: #495057; border-bottom: 2px solid #dee2e6;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                `;
                
                if (room.members && room.members.length > 0) {
                    room.members.forEach((member, index) => {
                        const memberName = member.user_full_name || member.full_name || member.user || member.name;
                        const memberRole = member.role || 'Member';
                        const userId = member.user || member.name;
                        const isCurrentUser = userId === frappe.session.user;
                        
                        const memberInitial = memberName.charAt(0).toUpperCase();
                        const avatarColors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6f42c1'];
                        const avatarColor = avatarColors[index % avatarColors.length];
                        
                        membersHTML += `
                            <tr data-user="${userId}" style="border-bottom: 1px solid #f8f9fa; transition: background-color 0.2s ease;">
                                <td style="padding: 12px;">
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <div style="width: 32px; height: 32px; border-radius: 50%; background: ${avatarColor}; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                            ${memberInitial}
                                        </div>
                                        <div>
                                            <div style="font-weight: 500; color: #2c3e50; font-size: 14px;">${memberName}</div>
                                            ${isCurrentUser ? '<small style="color: #007bff; font-weight: 500;">(You)</small>' : ''}
                                        </div>
                                    </div>
                                </td>
                                <td style="padding: 12px;">
                                    <select class="form-control form-control-sm member-role" data-user="${userId}" 
                                            style="font-size: 12px; border-radius: 6px; border: 1px solid #e9ecef; padding: 4px 8px;"
                                            ${memberRole === 'Admin' && isCurrentUser ? 'disabled title="Cannot change your own admin role"' : ''}>
                                        <option value="Member" ${memberRole === 'Member' ? 'selected' : ''}>Member</option>
                                        <option value="Moderator" ${memberRole === 'Moderator' ? 'selected' : ''}>Moderator</option>
                                        <option value="Admin" ${memberRole === 'Admin' ? 'selected' : ''}>Admin</option>
                                    </select>
                                </td>
                                <td style="padding: 12px;">
                                    ${!isCurrentUser ? `
                                        <button class="btn btn-sm btn-outline-danger remove-member" 
                                                data-user="${userId}" 
                                                style="font-size: 11px; padding: 4px 8px; border-radius: 6px;" 
                                                title="Remove ${memberName} from room">
                                            <i class="fa fa-user-times"></i> Remove
                                        </button>
                                    ` : `
                                        <span style="color: #6c757d; font-size: 12px; font-style: italic;">Cannot remove yourself</span>
                                    `}
                                </td>
                            </tr>
                        `;
                    });
                } else {
                    membersHTML += `
                        <tr>
                            <td colspan="3" style="padding: 30px; text-align: center; color: #6c757d;">
                                <i class="fa fa-users" style="font-size: 24px; margin-bottom: 8px; opacity: 0.5;"></i><br>
                                <span style="font-style: italic;">No members found</span>
                            </td>
                        </tr>
                    `;
                }
                
                membersHTML += `
                            </tbody>
                        </table>
                    </div>
                    <div style="margin-top: 15px; padding: 12px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 8px; border-left: 4px solid #007bff;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <i class="fa fa-info-circle" style="color: #007bff;"></i>
                            <span style="font-weight: 600; color: #495057; font-size: 13px;">Member Management Tips</span>
                        </div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #6c757d; line-height: 1.4;">
                            <li>Use the "Search and Add Users" field above to add new members</li>
                            <li>Change member roles using the dropdown menus</li>
                            <li>Remove members using the remove button (except yourself)</li>
                            <li>Admin users can manage all aspects of the room</li>
                        </ul>
                    </div>
                </div>
                `;
                
                if (dialog.fields_dict.members_html && dialog.fields_dict.members_html.$wrapper) {
                    dialog.fields_dict.members_html.$wrapper.html(membersHTML);
                    add_member_management_handlers_enhanced(dialog, roomId);
                }
            } else {
                if (dialog.fields_dict.members_html && dialog.fields_dict.members_html.$wrapper) {
                    dialog.fields_dict.members_html.$wrapper.html(`
                        <div style="padding: 30px; text-align: center; color: #dc3545;">
                            <i class="fa fa-exclamation-triangle" style="font-size: 24px; margin-bottom: 8px;"></i><br>
                            <span>Failed to load members</span>
                        </div>
                    `);
                }
            }
        },
        error: function(error) {
            console.error("Error loading members:", error);
            if (dialog.fields_dict.members_html && dialog.fields_dict.members_html.$wrapper) {
                dialog.fields_dict.members_html.$wrapper.html(`
                    <div style="padding: 30px; text-align: center; color: #dc3545;">
                        <i class="fa fa-wifi" style="font-size: 24px; margin-bottom: 8px;"></i><br>
                        <span>Network error loading members</span>
                    </div>
                `);
            }
        }
    });
}

// 4. ENHANCED: Member management with better UX
function add_member_management_handlers_enhanced(dialog, roomId) {
    // Handle role changes
    dialog.$wrapper.on('change', '.member-role', function() {
        const $select = $(this);
        const user = $select.data('user');
        const newRole = $select.val();
        const originalRole = $select.find('option:not(:selected)').first().val();
        
        $select.prop('disabled', true);
        
        frappe.call({
            method: 'vms.update_member_role',
            args: {
                room_id: roomId,
                user_id: user,
                new_role: newRole
            },
            callback: function(r) {
                $select.prop('disabled', false);
                
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: `Role updated to ${newRole} for ${user}`,
                        indicator: 'green'
                    });
                } else {
                    $select.val(originalRole);
                    frappe.show_alert({
                        message: 'Failed to update role: ' + (r.message?.error || 'Unknown error'),
                        indicator: 'red'
                    });
                }
            },
            error: function() {
                $select.prop('disabled', false);
                $select.val(originalRole);
                frappe.show_alert({
                    message: 'Network error updating role',
                    indicator: 'red'
                });
            }
        });
    });
    
    // Handle member removal
    dialog.$wrapper.on('click', '.remove-member', function(e) {
        e.preventDefault();
        const $button = $(this);
        const user = $button.data('user');
        const $row = $button.closest('tr');
        
        frappe.confirm(
            `Are you sure you want to remove <strong>${user}</strong> from this room?<br><br>They will no longer have access to room messages and will need to be re-invited to rejoin.`,
            () => {
                $button.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Removing...');
                
                frappe.call({
                    method: 'vms.remove_room_member',
                    args: {
                        room_id: roomId,
                        user_id: user
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            $row.fadeOut(400, function() {
                                $(this).remove();
                                
                                // Check if no members left
                                const remainingRows = dialog.$wrapper.find('.members-table-container tbody tr').length;
                                if (remainingRows === 0) {
                                    dialog.$wrapper.find('.members-table-container tbody').html(`
                                        <tr>
                                            <td colspan="3" style="padding: 30px; text-align: center; color: #6c757d;">
                                                <i class="fa fa-users" style="font-size: 24px; margin-bottom: 8px; opacity: 0.5;"></i><br>
                                                <span style="font-style: italic;">No members remaining</span>
                                            </td>
                                        </tr>
                                    `);
                                }
                            });
                            
                            frappe.show_alert({
                                message: `${user} removed from room`,
                                indicator: 'green'
                            });
                        } else {
                            $button.prop('disabled', false).html('<i class="fa fa-user-times"></i> Remove');
                            frappe.show_alert({
                                message: 'Failed to remove member: ' + (r.message?.error || 'Unknown error'),
                                indicator: 'red'
                            });
                        }
                    },
                    error: function() {
                        $button.prop('disabled', false).html('<i class="fa fa-user-times"></i> Remove');
                        frappe.show_alert({
                            message: 'Network error removing member',
                            indicator: 'red'
                        });
                    }
                });
            }
        );
    });
}


function create_room_item_html_enhanced(room) {
    const unreadBadge = room.unread_count > 0 
        ? `<span class="unread-badge-enhanced">${room.unread_count > 99 ? '99+' : room.unread_count}</span>`
        : '';
    
    const roomIcon = get_room_icon_enhanced(room.room_type);
    const roomColor = get_room_color_enhanced(room.room_type);
    
    // Use room_name if available, otherwise use document name (ID)
    const displayName = room.room_name || room.name;
    const roomId = room.name; // This is the document ID
    
    return `
        <div class="enhanced-room-item ${room.unread_count > 0 ? 'unread' : ''}" 
             onclick="open_enhanced_room('${roomId}', '${displayName}', '${room.room_type}')"
             data-room-id="${roomId}">
            <div class="room-avatar-enhanced" style="background: ${roomColor};">
                ${roomIcon}
            </div>
            <div class="room-info-enhanced">
                <div class="room-header-enhanced">
                    <div class="room-name-enhanced" title="Room: ${displayName} (ID: ${roomId})">${displayName}</div>
                    <div class="room-actions-enhanced">
                        <button class="room-options-btn-enhanced" 
                                onclick="show_room_options('${roomId}', event)"
                                title="Room Options">
                            <i class="fa fa-ellipsis-v"></i>
                        </button>
                    </div>
                </div>
                <div class="room-last-message-enhanced">
                    ${room.last_message ? 
                        room.last_message.substring(0, 55) + (room.last_message.length > 55 ? '...' : '') : 
                        'No messages yet'}
                </div>
            </div>
            <div class="room-meta-enhanced">
                <div class="room-time-enhanced">${format_time_ago_enhanced(room.last_activity || room.modified)}</div>
                ${unreadBadge}
            </div>
        </div>
    `;
}


// Enhanced room item HTML with edit option
function create_room_item_html(room) {
    const unreadBadge = room.unread_count > 0 
        ? `<span class="unread-badge-enhanced">${room.unread_count > 99 ? '99+' : room.unread_count}</span>`
        : '';
    
    const roomIcon = room.room_type === 'Direct Message' ? '👤' 
                   : room.room_type === 'Team Chat' ? '👥'
                   : room.room_type === 'Announcement' ? '📢' 
                   : '💬';
    
    return `
        <div class="room-item-enhanced ${room.unread_count > 0 ? 'has-unread' : ''}" 
             onclick="open_enhanced_room('${room.name}')"
             data-room-id="${room.name}">
            <div class="room-icon">${roomIcon}</div>
            <div class="room-info">
                <div class="room-header">
                    <span class="room-name">${room.room_name}</span>
                    <div class="room-actions">
                        <button class="btn btn-xs btn-ghost room-options-btn" 
                                onclick="show_room_options('${room.name}', event)"
                                title="Room Options">
                            <i class="fa fa-ellipsis-v"></i>
                        </button>
                    </div>
                </div>
                ${room.last_message ? `
                    <div class="last-message">
                        <span class="sender">${room.last_message_sender}:</span>
                        <span class="content">${room.last_message}</span>
                    </div>
                ` : '<div class="last-message no-messages">No messages yet</div>'}
            </div>
            <div class="room-meta">
                ${room.last_message_time ? `
                    <div class="time">${format_time_enhanced(room.last_message_time)}</div>
                ` : ''}
                ${unreadBadge}
            </div>
        </div>
    `;
}



let currentDropdown = null;

let currentRoomOptionsDropdown = null;
let dropdownCloseHandlers = [];

function show_room_options(room_id, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    // Close any existing dropdown
    close_room_options_menu();
    
    const dropdown = document.createElement('div');
    dropdown.className = 'room-options-dropdown-fixed';
    dropdown.setAttribute('data-room-id', room_id);
    
    dropdown.style.cssText = `
        position: fixed;
        z-index: 9999;
        min-width: 180px;
        background: white;
        border: 1px solid #e1e8ed;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        padding: 6px 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    `;
    
    dropdown.innerHTML = `
        <div class="room-option-item-fixed" data-action="edit">
            <i class="fa fa-edit"></i>
            <span>Edit Room</span>
        </div>
        <div class="room-option-item-fixed" data-action="leave">
            <i class="fa fa-sign-out"></i>
            <span>Leave Room</span>
        </div>
        <div class="dropdown-divider-fixed"></div>
        <div class="room-option-item-fixed danger" data-action="archive">
            <i class="fa fa-archive"></i>
            <span>Archive Room</span>
        </div>
    `;
    
    // Position dropdown
    const rect = event.target.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const dropdownWidth = 180;
    const dropdownHeight = 120;
    
    let left = rect.left - dropdownWidth + rect.width;
    let top = rect.bottom + 2;
    
    // Adjust if dropdown goes off screen
    if (left < 10) left = rect.right + 2;
    if (left + dropdownWidth > viewportWidth - 10) left = viewportWidth - dropdownWidth - 10;
    if (top + dropdownHeight > viewportHeight - 10) top = rect.top - dropdownHeight - 2;
    
    dropdown.style.left = left + 'px';
    dropdown.style.top = top + 'px';
    
    // Add styles for dropdown items
    add_dropdown_styles();
    
    // Add to document
    document.body.appendChild(dropdown);
    currentRoomOptionsDropdown = dropdown;
    
    // Handle clicks on dropdown items
    const itemClickHandler = function(e) {
        e.stopPropagation();
        const item = e.target.closest('.room-option-item-fixed');
        if (item) {
            const action = item.getAttribute('data-action');
            
            close_room_options_menu();
            
            switch (action) {
                case 'edit':
                    edit_chat_room(room_id);
                    break;
                case 'leave':
                    leave_chat_room(room_id);
                    break;
                case 'archive':
                    archive_chat_room(room_id);
                    break;
            }
        }
    };
    
    dropdown.addEventListener('click', itemClickHandler);
    dropdownCloseHandlers.push(() => dropdown.removeEventListener('click', itemClickHandler));
    
    // Outside click handler
    const outsideClickHandler = function(e) {
        if (currentRoomOptionsDropdown && !currentRoomOptionsDropdown.contains(e.target)) {
            close_room_options_menu();
        }
    };
    
    // Escape key handler
    const escapeKeyHandler = function(e) {
        if (e.key === 'Escape') {
            close_room_options_menu();
        }
    };
    
    // Add handlers with delay to prevent immediate closure
    setTimeout(() => {
        document.addEventListener('click', outsideClickHandler, true);
        document.addEventListener('keydown', escapeKeyHandler, true);
        
        dropdownCloseHandlers.push(() => {
            document.removeEventListener('click', outsideClickHandler, true);
            document.removeEventListener('keydown', escapeKeyHandler, true);
        });
    }, 100);
}

// 5. NEW: Proper cleanup function for dropdown
function close_room_options_menu() {
    if (currentRoomOptionsDropdown && currentRoomOptionsDropdown.parentNode) {
        currentRoomOptionsDropdown.remove();
        currentRoomOptionsDropdown = null;
    }
    
    // Remove all event handlers
    dropdownCloseHandlers.forEach(handler => handler());
    dropdownCloseHandlers = [];
}

// 6. NEW: Add dropdown styles
function add_dropdown_styles() {
    if (document.querySelector('#room-options-dropdown-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'room-options-dropdown-styles';
    style.textContent = `
        .room-option-item-fixed {
            padding: 10px 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            color: #495057;
            transition: all 0.2s ease;
            user-select: none;
        }
        
        .room-option-item-fixed:hover {
            background: #f8f9fa;
            color: #2c3e50;
        }
        
        .room-option-item-fixed.danger {
            color: #dc3545;
        }
        
        .room-option-item-fixed.danger:hover {
            background: #f8d7da;
            color: #721c24;
        }
        
        .room-option-item-fixed i {
            width: 14px;
            text-align: center;
            font-size: 12px;
        }
        
        .dropdown-divider-fixed {
            height: 1px;
            background: #e9ecef;
            margin: 4px 0;
        }
        
        .room-options-dropdown-fixed {
            animation: dropdownFadeIn 0.15s ease-out;
        }
        
        @keyframes dropdownFadeIn {
            from {
                opacity: 0;
                transform: translateY(-5px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
    `;
    
    document.head.appendChild(style);
}

function close_room_options_dropdown() {
    if (currentDropdown && currentDropdown.parentNode) {
        currentDropdown.remove();
        currentDropdown = null;
    }
    document.removeEventListener('click', handleOutsideClick);
    document.removeEventListener('keydown', handleEscapeKey);
}

function handleOutsideClick(e) {
    if (currentDropdown && !currentDropdown.contains(e.target)) {
        close_room_options_dropdown();
    }
}

function handleEscapeKey(e) {
    if (e.key === 'Escape') {
        close_room_options_dropdown();
    }
}

function update_chat_room(room_id, values, dialog) {
    // Validate input
    if (!values.room_name || values.room_name.trim() === '') {
        frappe.msgprint({
            title: 'Validation Error',
            message: 'Room name cannot be empty',
            indicator: 'red'
        });
        return;
    }
    
    // Show loading
    dialog.set_primary_action_label('Updating...');
    dialog.disable_primary_action();
    
    // Update room settings
    frappe.call({
        method: 'vms.update_room_settings',
        args: {
            room_id: room_id,
            settings: {
                room_name: values.room_name.trim(),
                description: values.description || '',
                room_type: values.room_type,
                is_private: values.is_private || 0,
                allow_file_sharing: values.allow_file_sharing !== undefined ? values.allow_file_sharing : 1,
                max_members: values.max_members || 50
            }
        },
        callback: function(r) {
            dialog.set_primary_action_label('Update Room');
            dialog.enable_primary_action();
            
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: 'Room updated successfully',
                    indicator: 'green'
                });
                
                dialog.hide();
                
                // Refresh the room list to show changes
                lastRoomsData = null;
                load_enhanced_chat_rooms_stable();
                
                // If we're currently in this room, refresh messages too
                if (currentOpenRoom === room_id) {
                    lastMessagesData = null;
                    load_enhanced_room_messages(room_id);
                }
            } else {
                frappe.msgprint({
                    title: 'Update Failed',
                    message: r.message?.error || r.message?.message || 'Failed to update room settings',
                    indicator: 'red'
                });
            }
        },
        error: function(error) {
            dialog.set_primary_action_label('Update Room');
            dialog.enable_primary_action();
            
            console.error("Error updating room:", error);
            frappe.msgprint({
                title: 'Network Error',
                message: 'Unable to update room. Please check your connection and try again.',
                indicator: 'red'
            });
        }
    });
}


// Monitor cron logs
function show_cron_logs() {
    frappe.call({
        method: 'vms.chat_vms.doctype.chat_settings.chat_settings.get_cron_logs',
        callback: function(r) {
            if (r.message && r.message.success) {
                const logs = r.message.data;
                
                let logsHTML = `
                    <div class="cron-logs-container">
                        <h4>Chat Cron Job Logs</h4>
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Job Type</th>
                                    <th>Status</th>
                                    <th>Time</th>
                                    <th>Error</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                logs.forEach(log => {
                    const statusClass = log.status === 'Success' ? 'text-success' : 'text-danger';
                    logsHTML += `
                        <tr>
                            <td>${log.scheduled_job_type}</td>
                            <td class="${statusClass}">${log.status}</td>
                            <td>${frappe.datetime.str_to_user(log.creation)}</td>
                            <td>${log.error || '-'}</td>
                        </tr>
                    `;
                });
                
                logsHTML += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                const dialog = new frappe.ui.Dialog({
                    title: 'Cron Job Logs',
                    fields: [{
                        fieldname: 'logs_html',
                        fieldtype: 'HTML'
                    }],
                    primary_action_label: 'Close',
                    primary_action() {
                        dialog.hide();
                    }
                });
                
                dialog.fields_dict.logs_html.$wrapper.html(logsHTML);
                dialog.show();
            } else {
                frappe.msgprint({
                    title: 'Info',
                    message: r.message.message || 'Could not fetch cron logs',
                    indicator: 'orange'
                });
            }
        }
    });
}

// Archive room function
function archive_chat_room(room_id, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    frappe.confirm(
        'Are you sure you want to archive this room? It will be hidden from your chat list.',
        () => {
            frappe.call({
                method: 'vms.archive_room',
                args: { room_id: room_id },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: 'Room archived successfully',
                            indicator: 'green'
                        });
                        load_enhanced_chat_rooms_stable();
                    }
                }
            });
        }
    );
}

// Leave room function
function leave_chat_room(room_id, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    frappe.confirm(
        'Are you sure you want to leave this room?',
        () => {
            frappe.call({
                method: 'vms.remove_room_member',
                args: {
                    room_id: room_id,
                    user_id: frappe.session.user
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: 'You have left the room',
                            indicator: 'green'
                        });
                        load_enhanced_chat_rooms_stable();
                    }
                }
            });
        }
    );
}

// Update user chat status in User doctype
function update_user_chat_status(status) {
    frappe.call({
        method: 'frappe.client.set_value',
        args: {
            doctype: 'User',
            name: frappe.session.user,
            fieldname: 'custom_chat_status',
            value: status
        },
        callback: function(r) {
            console.log(`User chat status updated to: ${status}`);
        }
    });
}

// Handle timestamp errors in polling
function safe_datetime_parse(datetime_str) {
    try {
        if (!datetime_str) return null;
        
        // Handle different datetime formats
        if (datetime_str.includes('T')) {
            return new Date(datetime_str);
        } else {
            // Handle MySQL datetime format
            return new Date(datetime_str.replace(' ', 'T'));
        }
    } catch (e) {
        console.error('Error parsing datetime:', datetime_str, e);
        return new Date();
    }
}

// Enhanced polling with error handling
function check_for_new_messages_enhanced() {
    if (!chatEnabled) return;
    
    frappe.call({
        method: "vms.get_user_chat_status",
        callback: function(response) {
            if (response.message && response.message.success) {
                const data = response.message.data;
                update_notification_dot_enhanced(data.total_unread > 0);
                
                // Update user status if changed
                // if (data.online_status !== frappe.boot.user.custom_chat_status) {
                //     update_user_chat_status(data.online_status);
                // }
            }
        },
        error: function(err) {
            // Handle timestamp or other errors gracefully
            console.error('Error checking messages:', err);
            
            // Fallback check
            setTimeout(() => {
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
            }, 1000);
        }
    });
}


// function update_notification_dot_enhanced(hasUnread) {
//     const notificationDot = document.querySelector('#chat-notification-dot');
//     if (notificationDot) {
//         notificationDot.style.display = hasUnread ? 'block' : 'none';
//     }
// }

// Stable room loading - prevents flickering during refresh
function load_enhanced_chat_rooms_stable() {
    if (!chatEnabled || isLoading) return;
    
    isLoading = true;
    
    frappe.call({
        method: "vms.get_user_chat_rooms",
        args: { page: 1, page_size: 20 },
        callback: function(response) {
            isLoading = false;
            
            if (response.message && response.message.success) {
                const rooms = response.message.data.rooms || response.message.data || [];
                
                // Check if data has changed
                const roomsDataStr = JSON.stringify(rooms);
                if (roomsDataStr === lastRoomsData) {
                    return; // No changes, skip update
                }
                lastRoomsData = roomsDataStr;
                
                const roomsList = document.querySelector('#enhanced-chat-rooms-list');
                if (!roomsList) return;
                
                if (rooms.length === 0) {
                    roomsList.innerHTML = `
                        <div class="empty-state-enhanced">
                            <i class="fa fa-comments-o" style="font-size: 48px; color: #d1d8dd; margin-bottom: 16px;"></i>
                            <p style="color: #8d99a6;">No chat rooms yet</p>
                            <p style="color: #8d99a6; font-size: 12px;">Create a room to start chatting</p>
                        </div>
                    `;
                } else {
                    const roomsHTML = rooms.map(room => create_room_item_html(room)).join('');
                    roomsList.innerHTML = roomsHTML;
                }
                
                // Update notification dot
                const hasUnread = rooms.some(room => room.unread_count > 0);
                update_notification_dot_enhanced(hasUnread);
            }
        },
        error: function(err) {
            isLoading = false;
            console.error('Error loading rooms:', err);
            
            // Show error state
            const roomsList = document.querySelector('#enhanced-chat-rooms-list');
            if (roomsList) {
                roomsList.innerHTML = `
                    <div class="empty-state-enhanced">
                        <i class="fa fa-exclamation-triangle" style="font-size: 48px; color: #ff5858; margin-bottom: 16px;"></i>
                        <p style="color: #8d99a6;">Failed to load chat rooms</p>
                        <button class="btn btn-sm btn-secondary" onclick="load_enhanced_chat_rooms_stable()">
                            Retry
                        </button>
                    </div>
                `;
            }
        }
    });
}

// Format time helper
function format_time_enhanced(datetime_str) {
    const date = safe_datetime_parse(datetime_str);
    if (!date) return '';
    
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        return date.toLocaleDateString();
    }
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
}

// Update notification dot
function update_notification_dot_enhanced(hasUnread) {
    const notificationDot = document.querySelector('#chat-notification-dot');
    if (notificationDot) {
        notificationDot.style.display = hasUnread ? 'block' : 'none';
    }
}

// Add Settings button to chat dropdown
function add_chat_settings_button() {
    const chatHeader = document.querySelector('.enhanced-chat-header');
    if (chatHeader && !chatHeader.querySelector('.chat-settings-btn')) {
        const settingsBtn = document.createElement('button');
        settingsBtn.className = 'btn btn-xs btn-ghost chat-settings-btn';
        settingsBtn.innerHTML = '<i class="fa fa-cog"></i>';
        settingsBtn.title = 'Chat Settings';
        settingsBtn.onclick = () => {
            frappe.set_route('Form', 'Chat Settings');
        };
        
        const cronBtn = document.createElement('button');
        cronBtn.className = 'btn btn-xs btn-ghost chat-cron-btn';
        cronBtn.innerHTML = '<i class="fa fa-clock-o"></i>';
        cronBtn.title = 'View Cron Logs';
        cronBtn.onclick = show_cron_logs;
        
        const btnContainer = document.createElement('div');
        btnContainer.style.cssText = 'position: absolute; right: 10px; top: 10px;';
        btnContainer.appendChild(cronBtn);
        btnContainer.appendChild(settingsBtn);
        
        chatHeader.appendChild(btnContainer);
    }
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
    
    const roomsHTML = rooms.map(room => create_room_item_html_enhanced(room)).join('');
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
                    <div class="form-group-enhanced">
                        <label class="form-label-enhanced">Add Members</label>
                        <input type="text" class="form-control-enhanced" 
                            id="room-members-input-enhanced" 
                            placeholder="Enter user IDs separated by commas">
                        <small style="color:#6c757d; font-size:12px;">You will be added as Admin automatically</small>
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

    const createBtn = document.getElementById('create-room-btn-modal');
    createBtn.disabled = true;
    createBtn.textContent = 'Creating...';

    // ✅ Parse members
    const membersInput = document.getElementById('room-members-input-enhanced');
    let members = [];
    if (membersInput && membersInput.value) {
        members = membersInput.value.split(',')
            .map(m => m.trim())
            .filter(m => m.length > 0);
    }

    // Always include creator as Admin
    const currentUser = frappe.session.user;
    if (!members.includes(currentUser)) {
        members.unshift(currentUser);
    }

    frappe.call({
        method: "vms.create_chat_room",
        args: {
            room_name: roomName,
            room_type: roomType,
            description: description,
            is_private: isPrivate ? 1 : 0,
            allow_file_sharing: allowFileSharing ? 1 : 0,
            max_members: maxMembers,
            members: JSON.stringify(members)   // ✅ now includes extra users
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                close_create_room_modal();
                lastRoomsData = null;
                load_enhanced_chat_rooms_stable();
                frappe.show_alert({
                    message: `Room "${roomName}" created successfully!`,
                    indicator: 'green'
                });

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
        error: function() {
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
    isDropdownOpen = true;
    
    // If room name is not provided or is the document ID, fetch the actual room name
    if (!roomName || roomName === roomId || roomName.startsWith('CR-')) {
        fetch_and_display_room_details(roomId, roomType);
    } else {
        display_room_header(roomId, roomName, roomType);
    }
    
    // Switch views
    const roomsView = document.querySelector('#enhanced-rooms-view');
    const messagingView = document.querySelector('#enhanced-messaging-view');
    
    if (roomsView) roomsView.style.display = 'none';
    if (messagingView) messagingView.style.display = 'block';
    
    // Load messages and mark as read
    load_enhanced_room_messages(roomId);
    mark_enhanced_room_as_read(roomId);
}

// 2. NEW: Fetch room details to get proper room name
function fetch_and_display_room_details(roomId, roomType) {
    frappe.call({
        method: "vms.get_room_details",
        args: { room_id: roomId },
        callback: function(response) {
            if (response.message && response.message.success && response.message.data) {
                const roomData = response.message.data;
                const room = roomData.room || roomData;
                
                const actualRoomName = room.room_name || room.name || roomId;
                const actualRoomType = room.room_type || roomType || 'Chat Room';
                
                display_room_header(roomId, actualRoomName, actualRoomType);
            } else {
                // Fallback to document ID if fetch fails
                display_room_header(roomId, roomId, roomType || 'Chat Room');
            }
        },
        error: function() {
            // Fallback to document ID on error
            display_room_header(roomId, roomId, roomType || 'Chat Room');
        }
    });
}

// 3. NEW: Display room header with proper information
function display_room_header(roomId, roomName, roomType) {
    const headerTitle = document.querySelector('#chat-header-title');
    const roomNameEl = document.querySelector('#current-room-name');
    const roomStatusEl = document.querySelector('#current-room-status');
    const roomAvatarEl = document.querySelector('#current-room-avatar');
    
    // Update main header with back button and room name
    if (headerTitle) {
        headerTitle.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 4px 0;" onclick="back_to_rooms_list()">
                <i class="fa fa-arrow-left" style="color: white; font-size: 16px;"></i>
                <span style="color: white; font-weight: 600; font-size: 16px;">${roomName}</span>
            </div>
        `;
    }
    
    // Update room details in messaging header
    if (roomNameEl) {
        roomNameEl.innerHTML = `
            <div style="display: flex; flex-direction: column;">
                <div style="font-weight: 600; font-size: 15px; color: #2c3e50;">${roomName}</div>
                <div style="font-size: 11px; color: #6c757d;" title="Room ID: ${roomId}">ID: ${roomId}</div>
            </div>
        `;
    }
    
    if (roomStatusEl) {
        roomStatusEl.innerHTML = `
            <div style="display: flex; align-items: center; gap: 6px; font-size: 12px;">
                <span style="color: #28a745; font-size: 8px;">●</span>
                <span style="color: #495057;">${roomType}</span>
                <span style="color: #6c757d;">•</span>
                <span style="color: #28a745;">Active</span>
            </div>
        `;
    }
    
    if (roomAvatarEl) {
        roomAvatarEl.textContent = get_room_icon_enhanced(roomType);
        roomAvatarEl.style.background = get_room_color_enhanced(roomType);
        roomAvatarEl.title = `${roomType}: ${roomName} (${roomId})`;
    }
}
// Add CSS for dropdown animation
const additionalStyles = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .room-options-dropdown {
        animation: fadeIn 0.2s ease-out;
    }
    
    .room-options-dropdown .dropdown-item {
        padding: 10px 16px;
        font-size: 13px;
        color: #495057;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s ease;
        border-bottom: 1px solid rgba(0,0,0,0.05);
    }
    
    .room-options-dropdown .dropdown-item:last-child {
        border-bottom: none;
    }
    
    .room-options-dropdown .dropdown-item:hover {
        background: #f8f9fa;
        color: #2c3e50;
        text-decoration: none;
        transform: translateX(2px);
    }
    
    .room-options-dropdown .dropdown-item.text-danger:hover {
        background: #f8d7da;
        color: #721c24;
    }
    
    .room-options-dropdown .dropdown-divider {
        margin: 0;
        border-top: 1px solid #e9ecef;
        background: #f9fafb;
        height: 1px;
    }
`;

// Add the additional styles to head
if (!document.querySelector('#room-options-styles')) {
    const style = document.createElement('style');
    style.id = 'room-options-styles';
    style.textContent = additionalStyles;
    document.head.appendChild(style);
}
function back_to_rooms_list() {
    const roomsView = document.querySelector('#enhanced-rooms-view');
    const messagingView = document.querySelector('#enhanced-messaging-view');
    const headerTitle = document.querySelector('#chat-header-title');
    
    if (roomsView) roomsView.style.display = 'block';
    if (messagingView) messagingView.style.display = 'none';
    
    // Reset header to original chat list state
    if (headerTitle) {
        headerTitle.innerHTML = '💬 Chat Messages';
    }
    
    currentOpenRoom = null;
    
    // Close any open dropdown menus
    close_room_options_menu();
    
    // Refresh rooms list
    lastRoomsData = null;
    load_enhanced_chat_rooms_stable();
    
    // Keep dropdown open
    isDropdownOpen = true;
}


window.removeSelectedUser = function(userName) {
    // This function will be called from the onclick in the HTML
    // You can implement this to remove users from the selected list
    console.log('Remove user:', userName);
};



function show_edit_room_dialog_with_enhanced_members(room) {
    const roomName = room.room_name || room.name || 'Unknown Room';
    const roomDescription = room.description || '';
    const roomType = room.room_type || 'Group Chat';
    const roomId = room.name || room.id || room.room_id;
    
    const dialog = new frappe.ui.Dialog({
        title: `Edit Room: ${roomName}`,
        fields: [
            {
                fieldtype: 'Section Break',
                label: 'Basic Information'
            },
            {
                label: 'Room Name',
                fieldname: 'room_name',
                fieldtype: 'Data',
                default: roomName,
                reqd: 1
            },
            {
                label: 'Description', 
                fieldname: 'description',
                fieldtype: 'Text',
                default: roomDescription
            },
            {
                label: 'Room Type',
                fieldname: 'room_type',
                fieldtype: 'Select',
                options: 'Direct Message\nTeam Chat\nGroup Chat\nAnnouncement',
                default: roomType
            },
            {
                fieldtype: 'Section Break',
                label: 'Room Settings'
            },
            {
                label: 'Private Room',
                fieldname: 'is_private', 
                fieldtype: 'Check',
                default: room.is_private || 0
            },
            {
                label: 'Allow File Sharing',
                fieldname: 'allow_file_sharing',
                fieldtype: 'Check', 
                default: room.allow_file_sharing !== undefined ? room.allow_file_sharing : 1
            },
            {
                label: 'Max Members',
                fieldname: 'max_members',
                fieldtype: 'Int',
                default: room.max_members || 50
            },
            {
                fieldtype: 'Section Break',
                label: 'Add New Members'
            },
            {
                label: 'Search Users to Add',
                fieldname: 'user_search',
                fieldtype: 'Data',
                description: 'Type to search for users and select their roles'
            },
            {
                label: 'User Selection',
                fieldname: 'search_results_html',
                fieldtype: 'HTML'
            },
            {
                fieldtype: 'Section Break',
                label: 'Current Members'
            },
            {
                label: 'Members List',
                fieldname: 'members_html',
                fieldtype: 'HTML'
            }
        ],
        primary_action_label: 'Update Room',
        primary_action(values) {
            update_chat_room_with_error_handling(roomId, values, dialog);
        }
    });
    
    dialog.show();
    
    // Set up enhanced user search with roles
    setup_user_search_with_roles(dialog, roomId);
    
    // Load current members
    load_current_members(dialog, roomId);
}

function show_edit_room_dialog_fixed(room) {
    const roomName = room.room_name || room.name || 'Unknown Room';
    const roomDescription = room.description || '';
    const roomType = room.room_type || 'Group Chat';
    const roomId = room.name || room.id || room.room_id;
    
    const dialog = new frappe.ui.Dialog({
        title: `Edit Room: ${roomName}`,
        fields: [
            {
                fieldtype: 'Section Break',
                label: 'Basic Information'
            },
            {
                label: 'Room Name',
                fieldname: 'room_name',
                fieldtype: 'Data',
                default: roomName,
                reqd: 1
            },
            {
                label: 'Description', 
                fieldname: 'description',
                fieldtype: 'Text',
                default: roomDescription
            },
            {
                label: 'Room Type',
                fieldname: 'room_type',
                fieldtype: 'Select',
                options: 'Direct Message\nTeam Chat\nGroup Chat\nAnnouncement',
                default: roomType
            },
            {
                fieldtype: 'Section Break',
                label: 'Room Settings'
            },
            {
                label: 'Private Room',
                fieldname: 'is_private', 
                fieldtype: 'Check',
                default: room.is_private || 0
            },
            {
                label: 'Allow File Sharing',
                fieldname: 'allow_file_sharing',
                fieldtype: 'Check', 
                default: room.allow_file_sharing !== undefined ? room.allow_file_sharing : 1
            },
            {
                label: 'Max Members',
                fieldname: 'max_members',
                fieldtype: 'Int',
                default: room.max_members || 50
            },
            {
                fieldtype: 'Section Break',
                label: 'Add New Members'
            },
            {
                label: 'Search Users to Add',
                fieldname: 'user_search',
                fieldtype: 'Data',
                description: 'Type to search for users to add to this room'
            },
            {
                label: 'Search Results',
                fieldname: 'search_results_html',
                fieldtype: 'HTML'
            },
            {
                fieldtype: 'Section Break',
                label: 'Current Members'
            },
            {
                label: 'Members List',
                fieldname: 'members_html',
                fieldtype: 'HTML'
            }
        ],
        primary_action_label: 'Update Room',
        primary_action(values) {
            // FIXED: Use the corrected update function
            update_chat_room_fixed(roomId, values, dialog);
        },
        secondary_action_label: 'Cancel'
    });
    
    dialog.show();
    
    // Set up user search functionality
    setup_user_search(dialog, roomId);
    
    // Load current members
    load_current_members(dialog, roomId);
}

// UTILITY: Helper functions for managing dialog state
function disable_dialog_completely(dialog) {
    dialog.$wrapper.find('input, select, textarea, button').prop('disabled', true);
    dialog.$wrapper.addClass('dialog-loading');
}

function enable_dialog_completely(dialog) {
    dialog.$wrapper.find('input, select, textarea, button').prop('disabled', false);
    dialog.$wrapper.removeClass('dialog-loading');
}

function update_primary_button_text(dialog, newText) {
    const primaryBtn = dialog.$wrapper.find('.btn-primary');
    primaryBtn.text(newText);
    return primaryBtn;
}

function disable_primary_button(dialog, loadingText = 'Processing...') {
    const primaryBtn = dialog.$wrapper.find('.btn-primary');
    const originalText = primaryBtn.text();
    primaryBtn.prop('disabled', true).text(loadingText);
    return originalText;
}

function enable_primary_button(dialog, originalText = 'Update') {
    const primaryBtn = dialog.$wrapper.find('.btn-primary');
    primaryBtn.prop('disabled', false).text(originalText);
}

// CSS for loading state
const dialogLoadingStyles = `
    .dialog-loading {
        position: relative;
        pointer-events: none;
        opacity: 0.7;
    }
    
    .dialog-loading::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.8);
        z-index: 1000;
        pointer-events: none;
    }
    
    .dialog-loading::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 20px;
        height: 20px;
        margin: -10px 0 0 -10px;
        border: 2px solid #007bff;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        z-index: 1001;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;

// Add the styles to document head
if (!document.querySelector('#dialog-loading-styles')) {
    const style = document.createElement('style');
    style.id = 'dialog-loading-styles';
    style.textContent = dialogLoadingStyles;
    document.head.appendChild(style);
}




function setup_user_search_with_roles(dialog, roomId) {
    const searchField = dialog.fields_dict.user_search;
    const resultsField = dialog.fields_dict.search_results_html;
    
    let searchTimeout;
    let selectedUsers = []; // Array of {user: userData, role: string}
    
    // Show initial state with add button section
    resultsField.$wrapper.html(`
        <div class="user-search-container">
            <div class="search-results-area">
                <div class="text-muted text-center p-3">
                    <i class="fa fa-search"></i><br>
                    Start typing to search for users
                </div>
            </div>
            
            <!-- Selected Users Management Section -->
            <div class="selected-users-section" style="margin-top: 15px; display: none;">
                <div class="selected-users-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <strong>Selected Users:</strong>
                    <button type="button" class="btn btn-sm btn-secondary" id="clear-selected-users">Clear All</button>
                </div>
                <div class="selected-users-table-container" style="max-height: 200px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 6px;">
                    <table class="table table-sm mb-0" id="selected-users-table">
                        <thead style="background: #f8f9fa; position: sticky; top: 0;">
                            <tr>
                                <th style="padding: 8px;">User</th>
                                <th style="padding: 8px;">Role</th>
                                <th style="padding: 8px; width: 50px;">Action</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
                <div style="margin-top: 10px; text-align: right;">
                    <button type="button" class="btn btn-primary" id="add-selected-users-with-roles">
                        Add Selected Users
                    </button>
                </div>
            </div>
        </div>
    `);
    
    // Set up search input handler
    searchField.$input.on('input', function() {
        const searchTerm = $(this).val().trim();
        
        clearTimeout(searchTimeout);
        
        if (searchTerm.length < 2) {
            resultsField.$wrapper.find('.search-results-area').html(`
                <div class="text-muted text-center p-3">
                    <i class="fa fa-search"></i><br>
                    Type at least 2 characters to search
                </div>
            `);
            return;
        }
        
        resultsField.$wrapper.find('.search-results-area').html(`
            <div class="text-center p-3">
                <i class="fa fa-spinner fa-spin"></i> Searching users...
            </div>
        `);
        
        searchTimeout = setTimeout(() => {
            search_users_for_room_with_roles(searchTerm, roomId, resultsField, selectedUsers);
        }, 500);
    });
    
    // Handle clear selected users
    resultsField.$wrapper.on('click', '#clear-selected-users', function() {
        selectedUsers.length = 0;
        update_selected_users_table(selectedUsers, resultsField);
    });
    
    // Handle add selected users with roles
    resultsField.$wrapper.on('click', '#add-selected-users-with-roles', function() {
        if (selectedUsers.length > 0) {
            add_users_with_roles_to_room(roomId, selectedUsers, dialog);
        }
    });
}

// 3. NEW: Search users and display with role selection
function search_users_for_room_with_roles(searchTerm, roomId, resultsField, selectedUsers) {
    frappe.call({
        method: 'vms.search_users_for_chat_room',
        args: {
            search_term: searchTerm,
            room_id: roomId,
            exclude_existing: true
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                display_user_search_results_with_roles(response.message.data, resultsField, selectedUsers);
            } else {
                resultsField.$wrapper.find('.search-results-area').html(`
                    <div class="text-danger text-center p-3">
                        <i class="fa fa-exclamation-triangle"></i><br>
                        Error searching users
                    </div>
                `);
            }
        },
        error: function() {
            resultsField.$wrapper.find('.search-results-area').html(`
                <div class="text-danger text-center p-3">
                    <i class="fa fa-wifi"></i><br>
                    Network error. Please try again.
                </div>
            `);
        }
    });
}

// 4. NEW: Display search results with selection capability
function display_user_search_results_with_roles(users, resultsField, selectedUsers) {
    if (users.length === 0) {
        resultsField.$wrapper.find('.search-results-area').html(`
            <div class="text-muted text-center p-3">
                <i class="fa fa-user-times"></i><br>
                No users found matching your search
            </div>
        `);
        return;
    }
    
    let resultsHTML = `
        <div class="user-search-results" style="max-height: 200px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 6px;">
    `;
    
    users.forEach(user => {
        const isSelected = selectedUsers.some(u => u.user.name === user.name);
        const selectedClass = isSelected ? 'selected' : '';
        
        resultsHTML += `
            <div class="user-result-item ${selectedClass}" 
                 data-user-name="${user.name}" 
                 style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: background 0.2s;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: #007bff; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">
                    ${user.full_name ? user.full_name.charAt(0).toUpperCase() : user.name.charAt(0).toUpperCase()}
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 500; font-size: 13px;">${user.full_name || user.name}</div>
                    <div style="font-size: 11px; color: #6c757d;">${user.email}</div>
                </div>
                <div style="width: 20px; height: 20px; border: 2px solid #dee2e6; border-radius: 3px; display: flex; align-items: center; justify-content: center;">
                    ${isSelected ? '<i class="fa fa-check" style="color: #28a745; font-size: 12px;"></i>' : ''}
                </div>
            </div>
        `;
    });
    
    resultsHTML += `</div>`;
    resultsField.$wrapper.find('.search-results-area').html(resultsHTML);
    
    // Add click handlers for user selection
    resultsField.$wrapper.off('click', '.user-result-item').on('click', '.user-result-item', function() {
        const userName = $(this).data('user-name');
        const userData = users.find(u => u.name === userName);
        const isSelected = $(this).hasClass('selected');
        
        if (isSelected) {
            // Remove from selected
            const index = selectedUsers.findIndex(u => u.user.name === userData.name);
            if (index > -1) {
                selectedUsers.splice(index, 1);
            }
            $(this).removeClass('selected');
            $(this).find('.fa-check').remove();
        } else {
            // Add to selected with default role
            selectedUsers.push({
                user: userData,
                role: 'Member'
            });
            $(this).addClass('selected');
            $(this).find('div:last-child').html('<i class="fa fa-check" style="color: #28a745; font-size: 12px;"></i>');
        }
        
        update_selected_users_table(selectedUsers, resultsField);
    });
    
    // Add hover styles
    const style = document.createElement('style');
    style.textContent = `
        .user-result-item:hover {
            background: #f8f9fa !important;
        }
        .user-result-item.selected {
            background: #e3f2fd !important;
        }
    `;
    document.head.appendChild(style);
}

// 5. NEW: Update selected users table with role selection
function update_selected_users_table(selectedUsers, resultsField) {
    const selectedSection = resultsField.$wrapper.find('.selected-users-section');
    const tableBody = resultsField.$wrapper.find('#selected-users-table tbody');
    const addButton = resultsField.$wrapper.find('#add-selected-users-with-roles');
    
    if (selectedUsers.length === 0) {
        selectedSection.hide();
        return;
    }
    
    selectedSection.show();
    
    let tableHTML = '';
    selectedUsers.forEach((item, index) => {
        const user = item.user;
        tableHTML += `
            <tr data-user-index="${index}">
                <td style="padding: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 24px; height: 24px; border-radius: 50%; background: #007bff; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 10px;">
                            ${user.full_name ? user.full_name.charAt(0).toUpperCase() : user.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <div style="font-weight: 500; font-size: 12px;">${user.full_name || user.name}</div>
                            <div style="font-size: 10px; color: #6c757d;">${user.email}</div>
                        </div>
                    </div>
                </td>
                <td style="padding: 8px;">
                    <select class="form-control form-control-sm user-role-select" data-user-index="${index}" style="font-size: 11px;">
                        <option value="Member" ${item.role === 'Member' ? 'selected' : ''}>Member</option>
                        <option value="Moderator" ${item.role === 'Moderator' ? 'selected' : ''}>Moderator</option>
                        <option value="Admin" ${item.role === 'Admin' ? 'selected' : ''}>Admin</option>
                    </select>
                </td>
                <td style="padding: 8px;">
                    <button class="btn btn-sm btn-outline-danger remove-selected-user" data-user-index="${index}" style="font-size: 10px; padding: 2px 6px;">
                        <i class="fa fa-times"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.html(tableHTML);
    addButton.text(`Add ${selectedUsers.length} User${selectedUsers.length > 1 ? 's' : ''} to Room`);
    
    // Handle role changes
    resultsField.$wrapper.off('change', '.user-role-select').on('change', '.user-role-select', function() {
        const userIndex = parseInt($(this).data('user-index'));
        const newRole = $(this).val();
        
        if (selectedUsers[userIndex]) {
            selectedUsers[userIndex].role = newRole;
        }
    });
    
    // Handle user removal
    resultsField.$wrapper.off('click', '.remove-selected-user').on('click', '.remove-selected-user', function(e) {
        e.preventDefault();
        const userIndex = parseInt($(this).data('user-index'));
        const removedUser = selectedUsers[userIndex];
        
        selectedUsers.splice(userIndex, 1);
        update_selected_users_table(selectedUsers, resultsField);
        
        // Update search results to show user as unselected
        const userResultItem = resultsField.$wrapper.find(`.user-result-item[data-user-name="${removedUser.user.name}"]`);
        if (userResultItem.length > 0) {
            userResultItem.removeClass('selected');
            userResultItem.find('.fa-check').remove();
        }
    });
}

// 6. NEW: Add users with their selected roles to room
function add_users_with_roles_to_room(roomId, selectedUsers, dialog) {
    if (selectedUsers.length === 0) return;
    
    // Show progress
    frappe.show_alert({
        message: `Adding ${selectedUsers.length} user(s) to room...`,
        indicator: 'blue'
    });
    
    let addedCount = 0;
    let errorCount = 0;
    let errors = [];
    
    function addNextUser(index) {
        if (index >= selectedUsers.length) {
            // All users processed
            const message = addedCount > 0 ? 
                `Successfully added ${addedCount} user(s) to the room.` : 
                'No users were added.';
            
            frappe.show_alert({
                message: message + (errorCount > 0 ? ` ${errorCount} failed.` : ''),
                indicator: addedCount > 0 ? 'green' : 'orange'
            });
            
            if (errors.length > 0) {
                frappe.msgprint({
                    title: 'Some Users Could Not Be Added',
                    message: errors.join('<br>'),
                    indicator: 'orange'
                });
            }
            
            // Clear selected users and refresh
            selectedUsers.length = 0;
            update_selected_users_table(selectedUsers, dialog.fields_dict.search_results_html);
            load_current_members(dialog, roomId);
            
            return;
        }
        
        const userItem = selectedUsers[index];
        
        frappe.call({
            method: 'vms.add_member_to_room',
            args: {
                room_id: roomId,
                user_id: userItem.user.name,
                role: userItem.role
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    addedCount++;
                } else {
                    errorCount++;
                    errors.push(`${userItem.user.full_name || userItem.user.name}: ${r.message?.error || 'Unknown error'}`);
                }
                addNextUser(index + 1);
            },
            error: function() {
                errorCount++;
                errors.push(`${userItem.user.full_name || userItem.user.name}: Network error`);
                addNextUser(index + 1);
            }
        });
    }
    
    addNextUser(0);
}



// 5. NEW: Set up user search functionality
function setup_user_search(dialog, roomId) {
    const searchField = dialog.fields_dict.user_search;
    const resultsField = dialog.fields_dict.search_results_html;
    
    let searchTimeout;
    let selectedUsers = [];
    
    // Show initial empty state
    resultsField.$wrapper.html(`
        <div class="user-search-container">
            <div class="text-muted text-center p-3">
                <i class="fa fa-search"></i><br>
                Start typing to search for users
            </div>
        </div>
    `);
    
    // Set up search input handler
    searchField.$input.on('input', function() {
        const searchTerm = $(this).val().trim();
        
        clearTimeout(searchTimeout);
        
        if (searchTerm.length < 2) {
            resultsField.$wrapper.html(`
                <div class="user-search-container">
                    <div class="text-muted text-center p-3">
                        <i class="fa fa-search"></i><br>
                        Type at least 2 characters to search
                    </div>
                </div>
            `);
            return;
        }
        
        // Show loading
        resultsField.$wrapper.html(`
            <div class="user-search-container">
                <div class="text-center p-3">
                    <i class="fa fa-spinner fa-spin"></i> Searching users...
                </div>
            </div>
        `);
        
        searchTimeout = setTimeout(() => {
            search_users_for_room(searchTerm, roomId, resultsField, selectedUsers);
        }, 500);
    });
    
    // Add selected users display
    const addSelectedButton = `
        <div class="selected-users-section" style="margin-top: 15px;">
            <div class="selected-users-display" id="selected-users-display"></div>
            <button type="button" class="btn btn-primary btn-sm" id="add-selected-users" style="display: none;">
                Add Selected Users
            </button>
        </div>
    `;
    
    resultsField.$wrapper.append(addSelectedButton);
    
    // Handle add selected users
    resultsField.$wrapper.on('click', '#add-selected-users', function() {
        if (selectedUsers.length > 0) {
            add_selected_users_to_room(roomId, selectedUsers, dialog);
        }
    });
}

// 6. NEW: Search users function
function search_users_for_room(searchTerm, roomId, resultsField, selectedUsers) {
    frappe.call({
        method: 'vms.search_users_for_chat_room',
        args: {
            search_term: searchTerm,
            room_id: roomId,
            exclude_existing: true
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                display_user_search_results(response.message.data, resultsField, selectedUsers);
            } else {
                resultsField.$wrapper.find('.user-search-container').html(`
                    <div class="text-danger text-center p-3">
                        <i class="fa fa-exclamation-triangle"></i><br>
                        Error searching users: ${response.message?.error || 'Unknown error'}
                    </div>
                `);
            }
        },
        error: function(error) {
            resultsField.$wrapper.find('.user-search-container').html(`
                <div class="text-danger text-center p-3">
                    <i class="fa fa-wifi"></i><br>
                    Network error. Please try again.
                </div>
            `);
        }
    });
}

// 7. NEW: Display search results
function display_user_search_results(users, resultsField, selectedUsers) {
    if (users.length === 0) {
        resultsField.$wrapper.find('.user-search-container').html(`
            <div class="text-muted text-center p-3">
                <i class="fa fa-user-times"></i><br>
                No users found matching your search
            </div>
        `);
        return;
    }
    
    let resultsHTML = `
        <div class="user-search-results" style="max-height: 200px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 6px;">
    `;
    
    users.forEach(user => {
        const isSelected = selectedUsers.some(u => u.name === user.name);
        const selectedClass = isSelected ? 'selected' : '';
        
        resultsHTML += `
            <div class="user-result-item ${selectedClass}" data-user='${JSON.stringify(user).replace(/'/g, "&#39;")}' 
                 style="padding: 8px 12px; border-bottom: 1px solid #f1f3f4; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: background 0.2s;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: #007bff; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">
                    ${user.full_name ? user.full_name.charAt(0).toUpperCase() : user.name.charAt(0).toUpperCase()}
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 500; font-size: 13px;">${user.full_name || user.name}</div>
                    <div style="font-size: 11px; color: #6c757d;">${user.email}</div>
                </div>
                <div style="width: 20px; height: 20px; border: 2px solid #dee2e6; border-radius: 3px; display: flex; align-items: center; justify-content: center;">
                    ${isSelected ? '<i class="fa fa-check" style="color: #28a745; font-size: 12px;"></i>' : ''}
                </div>
            </div>
        `;
    });
    
    resultsHTML += `</div>`;
    
    resultsField.$wrapper.find('.user-search-container').html(resultsHTML);
    
    // Add click handlers for user selection
    resultsField.$wrapper.off('click', '.user-result-item').on('click', '.user-result-item', function() {
        const userData = JSON.parse($(this).attr('data-user').replace(/&#39;/g, "'"));
        const isSelected = $(this).hasClass('selected');
        
        if (isSelected) {
            // Remove from selected
            selectedUsers = selectedUsers.filter(u => u.name !== userData.name);
            $(this).removeClass('selected');
            $(this).find('.fa-check').remove();
        } else {
            // Add to selected
            selectedUsers.push(userData);
            $(this).addClass('selected');
            $(this).find('div:last-child').html('<i class="fa fa-check" style="color: #28a745; font-size: 12px;"></i>');
        }
        
        update_selected_users_display(selectedUsers, resultsField);
    });
    
    // Add hover styles
    const style = document.createElement('style');
    style.textContent = `
        .user-result-item:hover {
            background: #f8f9fa !important;
        }
        .user-result-item.selected {
            background: #e3f2fd !important;
        }
    `;
    document.head.appendChild(style);
}

// 8. NEW: Update selected users display
function update_selected_users_display(selectedUsers, resultsField) {
    const displayEl = resultsField.$wrapper.find('#selected-users-display');
    const addButton = resultsField.$wrapper.find('#add-selected-users');
    
    if (selectedUsers.length === 0) {
        displayEl.empty();
        addButton.hide();
        return;
    }
    
    let displayHTML = '<div style="margin-bottom: 10px;"><strong>Selected Users:</strong></div>';
    displayHTML += '<div style="display: flex; flex-wrap: wrap; gap: 5px;">';
    
    selectedUsers.forEach(user => {
        displayHTML += `
            <span class="badge badge-primary" style="display: flex; align-items: center; gap: 5px; padding: 5px 8px;">
                ${user.full_name || user.name}
                <i class="fa fa-times" style="cursor: pointer; margin-left: 3px;" onclick="removeSelectedUser('${user.name}')"></i>
            </span>
        `;
    });
    
    displayHTML += '</div>';
    displayEl.html(displayHTML);
    addButton.show().text(`Add ${selectedUsers.length} User${selectedUsers.length > 1 ? 's' : ''}`);
}

// 9. NEW: Add selected users to room
function add_selected_users_to_room(roomId, selectedUsers, dialog) {
    if (selectedUsers.length === 0) return;

    const userIds = selectedUsers.map(u => u.name);

    frappe.call({
        method: 'vms.add_multiple_members_to_room',
        args: {
            room_id: roomId,
            user_list: JSON.stringify(userIds),
            role: 'Member'
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                const result = response.message;

                let message = `Successfully added ${result.total_added} user(s) to the room.`;
                if (result.already_members.length > 0) {
                    message += ` ${result.already_members.length} user(s) were already members.`;
                }
                if (result.total_failed > 0) {
                    message += ` ${result.total_failed} user(s) could not be added.`;
                }

                frappe.show_alert({
                    message: message,
                    indicator: 'green'
                });

                // Clear selected users and refresh
                selectedUsers.length = 0;
                update_selected_users_display(selectedUsers, dialog.fields_dict.search_results_html);
                load_current_members(dialog, roomId);

            } else {
                frappe.show_alert({
                    message: 'Failed to add users: ' + (response.message?.error || 'Unknown error'),
                    indicator: 'red'
                });
            }
        },
        error: function(xhr, textStatus, errorThrown) {
            console.error('Network error adding users:', {
                status: xhr.status,
                statusText: xhr.statusText,
                textStatus: textStatus,
                errorThrown: errorThrown
            });
            
            frappe.show_alert({
                message: 'Network error while adding users. Please check your connection and try again.',
                indicator: 'red'
            });
        }
    });
}

// Helper function to update selected users display
function update_selected_users_display(selectedUsers, resultsField) {
    const displayEl = resultsField.$wrapper.find('#selected-users-display');
    const addButton = resultsField.$wrapper.find('#add-selected-users');
    
    if (selectedUsers.length === 0) {
        displayEl.empty();
        addButton.hide();
        return;
    }
    
    let displayHTML = '<div style="margin-bottom: 10px;"><strong>Selected Users:</strong></div>';
    displayHTML += '<div style="display: flex; flex-wrap: wrap; gap: 5px;">';
    
    selectedUsers.forEach((user, index) => {
        displayHTML += `
            <span class="badge badge-primary selected-user-badge" 
                  data-user-index="${index}"
                  style="display: flex; align-items: center; gap: 5px; padding: 5px 8px; background: #007bff; color: white; border-radius: 12px; font-size: 11px;">
                ${user.full_name || user.name}
                <i class="fa fa-times remove-selected-user" 
                   data-user-index="${index}"
                   style="cursor: pointer; margin-left: 3px; opacity: 0.8;"
                   title="Remove ${user.full_name || user.name}"></i>
            </span>
        `;
    });
    
    displayHTML += '</div>';
    displayEl.html(displayHTML);
    addButton.show().text(`Add ${selectedUsers.length} User${selectedUsers.length > 1 ? 's' : ''}`);
    
    // Add click handler for removing individual users
    displayEl.off('click', '.remove-selected-user').on('click', '.remove-selected-user', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const userIndex = parseInt($(this).data('user-index'));
        const removedUser = selectedUsers[userIndex];
        
        // Remove from selected users array
        selectedUsers.splice(userIndex, 1);
        
        // Update display
        update_selected_users_display(selectedUsers, resultsField);
        
        // Update the search results to show the user as unselected
        const userResultItem = resultsField.$wrapper.find(`.user-result-item[data-user*='"name":"${removedUser.name}"']`);
        if (userResultItem.length > 0) {
            userResultItem.removeClass('selected');
            userResultItem.find('.fa-check').remove();
        }
        
        frappe.show_alert({
            message: `${removedUser.full_name || removedUser.name} removed from selection`,
            indicator: 'orange'
        });
    });
}

// Additional helper function to clear all selected users
function clear_all_selected_users(selectedUsers, resultsField) {
    selectedUsers.length = 0;
    update_selected_users_display(selectedUsers, resultsField);
    
    // Update all search result items to show as unselected
    resultsField.$wrapper.find('.user-result-item.selected').each(function() {
        $(this).removeClass('selected');
        $(this).find('.fa-check').remove();
    });
    
    frappe.show_alert({
        message: 'All users removed from selection',
        indicator: 'orange'
    });
}

// Function to handle bulk user operations with progress feedback
function add_users_with_progress(roomId, selectedUsers, dialog) {
    if (selectedUsers.length === 0) return;

    // Show progress dialog for bulk operations
    const progressDialog = new frappe.ui.Dialog({
        title: 'Adding Users to Room',
        fields: [
            {
                fieldname: 'progress_html',
                fieldtype: 'HTML',
                options: `
                    <div class="progress-container">
                        <div class="progress" style="height: 20px; margin-bottom: 15px;">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 0%; background-color: #007bff;">
                                <span class="progress-text">0%</span>
                            </div>
                        </div>
                        <div class="progress-details">
                            <div id="current-action">Preparing to add users...</div>
                            <div id="progress-log" style="max-height: 200px; overflow-y: auto; margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px; font-family: monospace; font-size: 12px;"></div>
                        </div>
                    </div>
                `
            }
        ],
        primary_action_label: 'Cancel',
        primary_action() {
            progressDialog.hide();
        }
    });
    
    progressDialog.show();
    
    const userIds = selectedUsers.map(u => u.name);
    let processedCount = 0;
    const totalUsers = userIds.length;
    
    // Log function for progress updates
    function logProgress(message, type = 'info') {
        const logEl = progressDialog.$wrapper.find('#progress-log');
        const timestamp = new Date().toLocaleTimeString();
        const colorClass = type === 'error' ? 'text-danger' : type === 'success' ? 'text-success' : 'text-info';
        
        logEl.append(`<div class="${colorClass}">[${timestamp}] ${message}</div>`);
        logEl.scrollTop(logEl[0].scrollHeight);
    }
    
    // Update progress bar
    function updateProgress(current, total, message) {
        const percentage = Math.round((current / total) * 100);
        const progressBar = progressDialog.$wrapper.find('.progress-bar');
        const progressText = progressDialog.$wrapper.find('.progress-text');
        const currentAction = progressDialog.$wrapper.find('#current-action');
        
        progressBar.css('width', percentage + '%');
        progressText.text(percentage + '%');
        currentAction.text(message);
    }
    
    logProgress(`Starting bulk add operation for ${totalUsers} users`);
    
    frappe.call({
        method: 'vms.add_multiple_members_to_room',
        args: {
            room_id: roomId,
            user_list: JSON.stringify(userIds),
            role: 'Member'
        },
        callback: function(response) {
            updateProgress(totalUsers, totalUsers, 'Completed');
            
            if (response.message && response.message.success) {
                const result = response.message;
                
                logProgress(`✓ Successfully added ${result.total_added} users`, 'success');
                if (result.already_members.length > 0) {
                    logProgress(`⚠ ${result.already_members.length} users were already members`, 'info');
                }
                if (result.total_failed > 0) {
                    logProgress(`✗ ${result.total_failed} users could not be added`, 'error');
                    result.failed_users.forEach(failed => {
                        logProgress(`  - ${failed.user_id}: ${failed.reason}`, 'error');
                    });
                }
                
                setTimeout(() => {
                    progressDialog.hide();
                    
                    let message = `Operation completed! Added ${result.total_added} user(s) to the room.`;
                    if (result.already_members.length > 0 || result.total_failed > 0) {
                        message += ` (${result.already_members.length} already members, ${result.total_failed} failed)`;
                    }
                    
                    frappe.show_alert({
                        message: message,
                        indicator: result.total_added > 0 ? 'green' : 'orange'
                    });
                    
                    // Clear selected users and refresh
                    selectedUsers.length = 0;
                    update_selected_users_display(selectedUsers, dialog.fields_dict.search_results_html);
                    load_current_members(dialog, roomId);
                    
                }, 2000);
                
            } else {
                logProgress(`✗ Operation failed: ${response.message?.error || 'Unknown error'}`, 'error');
                
                setTimeout(() => {
                    progressDialog.hide();
                    frappe.show_alert({
                        message: 'Failed to add users: ' + (response.message?.error || 'Unknown error'),
                        indicator: 'red'
                    });
                }, 1500);
            }
        },
        error: function(xhr, textStatus, errorThrown) {
            logProgress(`✗ Network error: ${textStatus} - ${errorThrown}`, 'error');
            
            setTimeout(() => {
                progressDialog.hide();
                frappe.show_alert({
                    message: 'Network error while adding users. Please try again.',
                    indicator: 'red'
                });
            }, 1500);
        }
    });
}




let lastMessagesData = null;

function load_enhanced_room_messages(roomId) {
    const messagesContainer = document.querySelector('#enhanced-messages-container');
    if (!messagesContainer || isLoading) return;

    isLoading = true;

    // Only show spinner on first load
    if (!lastMessagesData) {
        messagesContainer.innerHTML = `
            <div class="loading-state-enhanced">
                <div class="spinner-enhanced"></div>
                <div style="margin-top: 8px;">Loading messages...</div>
            </div>
        `;
    }

    frappe.call({
        method: "vms.get_chat_messages",
        args: { room_id: roomId, page: 1, page_size: 50 },
        callback: function(response) {
            isLoading = false;
            if (response.message && response.message.success) {
                const messages = response.message.data.messages || [];

                // Compare JSON data
                const messagesJSON = JSON.stringify(messages);
                if (messagesJSON !== lastMessagesData) {
                    lastMessagesData = messagesJSON;

                    // Save scroll position
                    const isAtBottom = Math.abs(messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight) < 5;

                    display_enhanced_messages(messages);

                    // Restore scroll (if user at bottom → auto-scroll, otherwise don’t disturb)
                    if (isAtBottom) {
                        scroll_to_bottom_enhanced();
                    }
                }
            } else {
                if (!lastMessagesData) {
                    messagesContainer.innerHTML = `
                        <div class="empty-state-enhanced">
                            <div style="color: #dc3545;">❌ Failed to load messages</div>
                        </div>
                    `;
                }
            }
        },
        error: function() {
            isLoading = false;
            console.error("Error loading messages");
            if (!lastMessagesData) {
                messagesContainer.innerHTML = `
                    <div class="empty-state-enhanced">
                        <div style="color: #dc3545;">❌ Unable to connect to chat service</div>
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

        const escapedContent = (message.message_content || '').replace(/'/g, "\\'").replace(/"/g, '\\"');
        const escapedSender = (message.sender_info?.full_name || message.sender).replace(/'/g, "\\'").replace(/"/g, '\\"');
        
        messagesHTML += `
            <div class="message-bubble-enhanced ${messageClass}" data-message-id="${message.name}">
                ${!isOwn ? `<div class="message-sender-enhanced">${message.sender_info?.full_name || message.sender}</div>` : ''}
                
                ${message.reply_to_message ? `
                    <div class="reply-preview-enhanced" style="margin-bottom: 8px;">
                        <div style="font-size: 11px; font-weight: 600; margin-bottom: 2px;">↪ Reply to ${message.reply_to_sender || 'User'}</div>
                        <div style="font-size: 12px; opacity: 0.8;">${message.reply_to_content || ''}</div>
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
                            title="Reply">↩</button>
                        ${canEdit ? `
                            <button class="message-action-btn-enhanced" 
                                onclick="event.stopPropagation(); edit_message_enhanced('${message.name}', '${escapedContent}')" 
                                title="Edit">✏</button>` : ''}
                        ${canDelete ? `
                            <button class="message-action-btn-enhanced" 
                                onclick="event.stopPropagation(); delete_message_enhanced('${message.name}')" 
                                title="Delete" style="color: #dc3545 !important;">🗑</button>` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    messagesContainer.innerHTML = messagesHTML;
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
window.show_room_options = show_room_options;
window.edit_chat_room = edit_chat_room;
// window.open_enhanced_room = open_enhanced_room;
// window.back_to_rooms_list = back_to_rooms_list;
window.add_selected_users_to_room = add_selected_users_to_room;
window.update_selected_users_display = update_selected_users_display;
window.clear_all_selected_users = clear_all_selected_users;
window.add_users_with_progress = add_users_with_progress;
// window.show_room_options = show_room_options;
window.close_room_options_menu = close_room_options_menu;
window.display_enhanced_chat_rooms = display_enhanced_chat_rooms;
window.update_chat_room_fixed = update_chat_room_fixed;
// window.update_chat_room_alternative = update_chat_room_alternative;
// window.show_edit_room_dialog_corrected = show_edit_room_dialog_corrected;
window.disable_dialog_completely = disable_dialog_completely;
window.enable_dialog_completely = enable_dialog_completely;
window.update_chat_room_with_error_handling = update_chat_room_with_error_handling;
window.show_edit_room_dialog_with_enhanced_members = show_edit_room_dialog_with_enhanced_members;
window.setup_user_search_with_roles = setup_user_search_with_roles;
window.add_users_with_roles_to_room = add_users_with_roles_to_room;