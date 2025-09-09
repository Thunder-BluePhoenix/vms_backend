// vms/public/js/cchhaat.js
// Fixed chat integration with proper positioning and messaging functionality

function onFrappeReady(callback) {
    if (typeof frappe !== "undefined" && frappe.ready) {
        frappe.ready(callback);
    } else {
        document.addEventListener("DOMContentLoaded", callback);
    }
}

// Initialize when Frappe is ready
onFrappeReady(() => {
    console.log("🚀 Initializing chat integration with cchhaat.js...");
    add_chat_icon_to_navbar();
    init_chat_functionality();
});

function add_chat_icon_to_navbar() {
    // Wait for navbar to be fully loaded and try multiple times
    let attempts = 0;
    const maxAttempts = 10;
    
    function tryAddIcon() {
        attempts++;
        console.log(`Attempt ${attempts} to add chat icon...`);
        
        // Target the CORRECT navbar - the one inside .navbar-collapse that has the search and bell
        const navbar_collapse = document.querySelector('.navbar-collapse.justify-content-end');
        if (!navbar_collapse) {
            console.log(`❌ Navbar collapse not found (attempt ${attempts}/${maxAttempts})`);
            if (attempts < maxAttempts) {
                setTimeout(tryAddIcon, 1000);
            }
            return;
        }
        
        // Find the UL inside the collapse that contains the search and bell
        const navbar_nav = navbar_collapse.querySelector('ul.navbar-nav');
        if (!navbar_nav) {
            console.log(`❌ Main navbar-nav not found (attempt ${attempts}/${maxAttempts})`);
            if (attempts < maxAttempts) {
                setTimeout(tryAddIcon, 1000);
            }
            return;
        }
        
        // Check if chat icon already exists
        if (document.querySelector('#chat-icon-container')) {
            console.log("✅ Chat icon already exists - removing old one first");
            document.querySelector('#chat-icon-container').remove();
        }
        
        console.log("✅ Adding chat icon to MAIN navbar (between search and bell)...");
        console.log("Target navbar structure:", navbar_nav.innerHTML.substring(0, 200));
        
        // Create chat icon container
        const chat_container = document.createElement('li');
        chat_container.id = 'chat-icon-container';
        chat_container.className = 'nav-item dropdown dropdown-notifications dropdown-mobile';
        
        // Create chat icon HTML - exactly like the bell icon
        chat_container.innerHTML = `
            <button class="btn-reset nav-link notifications-icon text-muted" data-toggle="dropdown" 
                    aria-haspopup="true" aria-expanded="false" id="chat-icon"
                    title="Chat Messages">
                <span class="notifications-seen">
                    <span class="sr-only">No new messages</span>
                    <svg class="es-icon icon-sm" style="stroke:none;">
                        <use href="#es-line-chat-alt"></use>
                    </svg>
                </span>
                <span class="notifications-unseen" style="display: none;">
                    <span class="sr-only">You have unread messages</span>
                    <svg class="es-icon icon-sm">
                        <use href="#es-line-chat-alt"></use>
                    </svg>
                </span>
            </button>
            <div class="dropdown-menu notifications-list dropdown-menu-right" id="chat-dropdown" role="menu">
                <div class="notification-list-header">
                    <div class="header-items">
                        <ul class="notification-item-tabs nav nav-tabs" role="tablist">
                            <li class="notifications-category active">Chat Messages</li>
                        </ul>
                    </div>
                    <div class="header-actions">
                        <span class="notification-settings pull-right" onclick="open_chat_application()" 
                              title="Open Chat Application" style="cursor: pointer;">
                            <svg class="icon icon-sm" aria-hidden="true">
                                <use href="#icon-external-link"></use>
                            </svg>
                        </span>
                    </div>
                </div>
                <div class="notification-list-body">
                    <div class="panel-notifications">
                        <div id="chat-rooms-list">
                            <div style="padding: 20px; text-align: center; color: #6c757d;">
                                Loading chats...
                            </div>
                        </div>
                        <a class="list-footer" href="#" onclick="open_chat_application()">
                            <div class="full-log-btn">See all Messages</div>
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        // Insert BEFORE the bell icon (first li in the main navbar)
        const bell_icon = navbar_nav.querySelector('li.dropdown-notifications');
        if (bell_icon) {
            navbar_nav.insertBefore(chat_container, bell_icon);
            console.log("✅ SUCCESS: Inserted chat icon BEFORE bell icon in main navbar");
        } else {
            // Fallback: insert as first child of main navbar
            if (navbar_nav.firstElementChild) {
                navbar_nav.insertBefore(chat_container, navbar_nav.firstElementChild);
                console.log("✅ FALLBACK: Inserted as first child of main navbar");
            } else {
                navbar_nav.appendChild(chat_container);
                console.log("✅ FALLBACK: Appended to main navbar");
            }
        }
        
        addClickHandler();
        
        function addClickHandler() {
            const chatIcon = document.querySelector('#chat-icon');
            if (chatIcon) {
                chatIcon.addEventListener('click', function(e) {
                    e.preventDefault();
                    console.log("💬 Chat icon clicked");
                    load_chat_rooms_preview();
                    request_notification_permission();
                });
            }
            
            // Add visual confirmation
            setTimeout(() => {
                const container = document.querySelector('#chat-icon-container');
                if (container) {
                    const rect = container.getBoundingClientRect();
                    console.log(`Chat icon positioned at: x=${rect.x}, y=${rect.y}, width=${rect.width}`);
                    
                    // Temporary visual marker
                    container.style.border = '2px solid lime';
                    container.style.boxShadow = '0 0 10px lime';
                    
                    setTimeout(() => {
                        container.style.border = 'none';
                        container.style.boxShadow = 'none';
                    }, 3000);
                }
            }, 1000);
        }
    }
    
    // Start the first attempt immediately
    tryAddIcon();
}

function init_chat_functionality() {
    console.log("⚙️ Initializing chat functionality...");
    
    // Load chat rooms initially
    load_chat_rooms_preview();
    
    // Initialize Frappe's Socket.IO integration
    init_frappe_socketio_integration();
    
    // Set up periodic refresh
    setInterval(() => {
        const dropdown = document.querySelector('#chat-dropdown');
        if (dropdown && dropdown.classList.contains('show')) {
            load_chat_rooms_preview();
        }
    }, 30000);
}

function init_frappe_socketio_integration() {
    console.log("🔌 Setting up Frappe Socket.IO integration...");
    
    if (typeof frappe !== 'undefined' && frappe.realtime) {
        console.log("✅ Using Frappe's real-time system");
        
        frappe.realtime.on('chat_new_message', function(data) {
            console.log('📨 New chat message:', data);
            handle_new_message(data);
        });
        
        frappe.realtime.on('chat_room_updated', function(data) {
            console.log('🔄 Chat room updated:', data);
            load_chat_rooms_preview();
        });
        
    } else {
        console.log("⚠️ Frappe realtime not available");
    }
}

function handle_new_message(data) {
    load_chat_rooms_preview();
    show_desktop_notification(data);
    update_unread_badge();
}

// Define messaging functions before they're used
function open_chat_messaging(doc_name, room_name, room_type) {
    console.log(`💬 Opening chat messaging for: ${room_name} (${doc_name})`);
    
    // Close dropdown first
    const dropdown = document.querySelector('#chat-dropdown');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
    
    try {
        // Create a custom chat messaging interface
        create_chat_messaging_modal(doc_name, room_name, room_type);
        
        // Also mark room as read
        frappe.call({
            method: "vms.mark_room_as_read",
            args: { room_id: doc_name },
            callback: function() {
                setTimeout(load_chat_rooms_preview, 500);
            }
        });
        
    } catch (error) {
        console.error("❌ Error opening chat messaging:", error);
        // Fallback to form view
        frappe.set_route('Form', 'Chat Room', doc_name);
    }
}

function create_chat_messaging_modal(doc_name, room_name, room_type) {
    // Remove existing modal if any
    const existing_modal = document.querySelector('#chat-messaging-modal');
    if (existing_modal) {
        existing_modal.remove();
    }
    
    // Create modal backdrop
    const modal_backdrop = document.createElement('div');
    modal_backdrop.id = 'chat-messaging-modal';
    modal_backdrop.style.cssText = `
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
    `;
    
    // Create modal content
    const modal_content = document.createElement('div');
    modal_content.style.cssText = `
        background: white;
        border-radius: 8px;
        width: 90%;
        max-width: 800px;
        height: 80%;
        max-height: 600px;
        display: flex;
        flex-direction: column;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    `;
    
    // Modal header
    const header = document.createElement('div');
    header.style.cssText = `
        padding: 15px 20px;
        border-bottom: 1px solid #dee2e6;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px 8px 0 0;
    `;
    
    header.innerHTML = `
        <div>
            <h4 style="margin: 0; font-weight: 600;">${room_name}</h4>
            <small style="opacity: 0.8;">Doc: ${doc_name} • Type: ${room_type}</small>
        </div>
        <button onclick="close_chat_messaging_modal()" style="background: none; border: none; color: white; font-size: 24px; cursor: pointer; padding: 0; width: 30px; height: 30px;">×</button>
    `;
    
    // Messages container
    const messages_container = document.createElement('div');
    messages_container.id = 'chat-messages-container';
    messages_container.style.cssText = `
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        background: #f8f9fa;
    `;
    
    // Message input area
    const input_area = document.createElement('div');
    input_area.style.cssText = `
        padding: 15px 20px;
        border-top: 1px solid #dee2e6;
        background: white;
        border-radius: 0 0 8px 8px;
    `;
    
    input_area.innerHTML = `
        <div style="display: flex; gap: 10px; align-items: flex-end;">
            <textarea id="chat-message-input" placeholder="Type your message here..." 
                      style="flex: 1; border: 1px solid #ced4da; border-radius: 20px; padding: 10px 15px; resize: none; min-height: 40px; max-height: 120px;"
                      onkeydown="handle_chat_input_keydown(event, '${doc_name}')"></textarea>
            <button onclick="send_chat_message('${doc_name}')" 
                    style="background: #007bff; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                📤
            </button>
        </div>
    `;
    
    // Assemble modal
    modal_content.appendChild(header);
    modal_content.appendChild(messages_container);
    modal_content.appendChild(input_area);
    modal_backdrop.appendChild(modal_content);
    
    // Add to page
    document.body.appendChild(modal_backdrop);
    
    // Close modal when clicking backdrop
    modal_backdrop.addEventListener('click', function(e) {
        if (e.target === modal_backdrop) {
            close_chat_messaging_modal();
        }
    });
    
    // Load messages
    load_chat_messages(doc_name);
    
    // Focus input
    setTimeout(() => {
        const input = document.querySelector('#chat-message-input');
        if (input) input.focus();
    }, 100);
}

function close_chat_messaging_modal() {
    const modal = document.querySelector('#chat-messaging-modal');
    if (modal) {
        modal.remove();
    }
}

function handle_chat_input_keydown(event, room_id) {
    // Send message on Enter (but allow Shift+Enter for new line)
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        send_chat_message(room_id);
    }
}

function send_chat_message(room_id) {
    const input = document.querySelector('#chat-message-input');
    if (!input) return;
    
    const message_content = input.value.trim();
    
    if (!message_content) {
        return;
    }
    
    // Disable input while sending
    input.disabled = true;
    
    frappe.call({
        method: "vms.send_message",
        args: {
            room_id: room_id,
            message_content: message_content,
            message_type: "Text"
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                // Clear input
                input.value = '';
                input.disabled = false;
                input.focus();
                
                // Reload messages
                load_chat_messages(room_id);
                
                // Update chat rooms preview
                load_chat_rooms_preview();
                
            } else {
                frappe.show_alert({
                    message: 'Failed to send message',
                    indicator: 'red'
                });
                input.disabled = false;
            }
        },
        error: function(error) {
            console.error("Error sending message:", error);
            frappe.show_alert({
                message: 'Error sending message',
                indicator: 'red'
            });
            input.disabled = false;
        }
    });
}

function load_chat_messages(room_id) {
    const container = document.querySelector('#chat-messages-container');
    if (!container) return;

    // Show loading
    container.innerHTML = `
        <div style="text-align: center; color: #6c757d; padding: 20px;">
            Loading messages...
        </div>
    `;

    frappe.call({
        method: "vms.get_chat_messages",
        args: {
            room_id: room_id,
            page: 1,
            page_size: 50
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                const data = response.message.data || {};
                const messages = Array.isArray(data.messages) ? data.messages : [];
                display_chat_messages(messages);
            } else {
                container.innerHTML = `
                    <div style="text-align: center; color: #dc3545; padding: 20px;">
                        Failed to load messages
                    </div>
                `;
            }
        },
        error: function(error) {
            console.error("Error loading messages:", error);
            container.innerHTML = `
                <div style="text-align: center; color: #dc3545; padding: 20px;">
                    Error loading messages
                </div>
            `;
        }
    });
}


function display_chat_messages(messages) {
    const container = document.querySelector('#chat-messages-container');
    if (!container) return;

    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: #6c757d; padding: 20px;">
                No messages yet. Start the conversation!
            </div>
        `;
        return;
    }

    let messages_html = '';
    const current_user = frappe.session.user;

    // ✅ Messages are already old → new, so just render in order
    messages.forEach(msg => {
        const is_own_message = msg.sender === current_user;
        const sender_name = msg.sender_name || msg.sender || 'Unknown';
        const timestamp = msg.timestamp ? frappe.datetime.str_to_user(msg.timestamp) : '';

        const message_style = is_own_message 
            ? 'background: #007bff; color: white; margin-left: 60px; text-align: right;' 
            : 'background: white; color: #333; margin-right: 60px; text-align: left;';

        messages_html += `
            <div style="margin-bottom: 15px;">
                <div style="${message_style} padding: 10px 15px; border-radius: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                    ${!is_own_message ? `<div style="font-size: 11px; opacity: 0.7; margin-bottom: 3px;">${sender_name}</div>` : ''}
                    <div style="word-wrap: break-word;">${msg.message_content || msg.content || ''}</div>
                    <div style="font-size: 10px; opacity: 0.6; margin-top: 3px;">${timestamp}</div>
                </div>
            </div>
        `;
    });

    container.innerHTML = messages_html;

    // ✅ Always scroll to bottom to show the latest message
    container.scrollTop = container.scrollHeight;
}


function load_chat_rooms_preview() {
    const chat_list = document.querySelector('#chat-rooms-list');
    if (!chat_list) return;
    
    // Show loading state
    chat_list.innerHTML = `
        <div style="padding: 20px; text-align: center; color: #6c757d;">
            <span>Loading chats...</span>
        </div>
    `;
    
    // Make API call
    frappe.call({
        method: "vms.get_user_chat_rooms",
        args: {
            page: 1,
            page_size: 10
        },
        callback: function(response) {
            console.log("API Response:", response);
            
            let rooms = [];
            
            // Handle different response formats safely - CHECK MOST SPECIFIC FIRST
            try {
                if (response && response.message) {
                    // PRIORITY 1: Check if it's success format with data.rooms (YOUR FORMAT)
                    if (response.message.success && response.message.data && response.message.data.rooms && Array.isArray(response.message.data.rooms)) {
                        rooms = response.message.data.rooms;
                        console.log("✅ Using response.message.data.rooms format - Found", rooms.length, "rooms");
                    }
                    // PRIORITY 2: Check if it's direct rooms array format
                    else if (response.message.rooms && Array.isArray(response.message.rooms)) {
                        rooms = response.message.rooms;
                        console.log("✅ Using response.message.rooms format");
                    }
                    // PRIORITY 3: Check if it's success format with data as array
                    else if (response.message.success && Array.isArray(response.message.data)) {
                        rooms = response.message.data;
                        console.log("✅ Using response.message.data array format");
                    }
                    // PRIORITY 4: Check if message is directly an array
                    else if (Array.isArray(response.message)) {
                        rooms = response.message;
                        console.log("✅ Using response.message array format");
                    }
                    // PRIORITY 5: Check if it's wrapped in an array with rooms property
                    else if (Array.isArray(response.message) && response.message[0] && response.message[0].rooms) {
                        rooms = response.message[0].rooms;
                        console.log("✅ Using response.message[0].rooms format");
                    }
                    else {
                        console.log("❌ No matching response format found. Response structure:", response.message);
                    }
                }
                
                // Ensure rooms is an array
                if (!Array.isArray(rooms)) {
                    console.log("❌ Converting to array - rooms type:", typeof rooms, "value:", rooms);
                    rooms = [];
                } else {
                    console.log("✅ Final rooms array:", rooms.length, "rooms found");
                }
                
                display_chat_rooms(rooms);
                update_unread_count(rooms);
                
            } catch (error) {
                console.error("❌ Error processing API response:", error);
                show_chat_error("Error processing chat data");
            }
        },
        error: function(error) {
            console.error("❌ Error loading chat rooms:", error);
            show_chat_error("Unable to connect to chat service");
        }
    });
}

function display_chat_rooms(rooms) {
    const chat_list = document.querySelector('#chat-rooms-list');
    if (!chat_list) return;
    
    console.log("Displaying rooms (type: " + typeof rooms + ", length: " + (rooms ? rooms.length : 'N/A') + "):", rooms);
    
    if (!rooms || !Array.isArray(rooms) || rooms.length === 0) {
        chat_list.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #6c757d;">
                <div>No Chat Rooms</div>
                <small>Create a new room to get started</small>
            </div>
        `;
        return;
    }
    
    let rooms_html = '';
    
    try {
        rooms.forEach(room => {
            // Extract both doc name and room_name for display
            const doc_name = room.name || room.id || 'unknown';
            const room_name = room.room_name || room.title || 'Unknown Room';
            const unread_count = room.unread_count || 0;
            const room_type = room.room_type || 'Group Chat';
            
            const unread_badge = unread_count > 0 ? 
                `<span style="background: #007bff; color: white; font-size: 9px; padding: 2px 6px; border-radius: 10px; margin-left: 5px;">${unread_count > 99 ? '99+' : unread_count}</span>` : '';
            
            const last_message = room.last_message ? 
                `<div style="color: #6c757d; font-size: 12px; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${room.last_message.substring(0, 45)}${room.last_message.length > 45 ? '...' : ''}
                </div>` : '';
            
            // Get room type icon
            const room_icon = get_room_type_icon(room_type);
            
            rooms_html += `
                <a class="recent-item notification-item" href="#" onclick="open_chat_messaging('${doc_name}', '${room_name.replace(/'/g, "&apos;")}', '${room_type}')" style="text-decoration: none;">
                    <div class="notification-body">
                        <span class="avatar avatar-medium" title="${room_name} (${doc_name})">
                            <div class="avatar-frame standard-image" style="background-color: #007bff; color: white; display: flex; align-items: center; justify-content: center;">
                                <svg class="es-icon icon-sm" style="stroke:none;">
                                    <use href="#${room_icon}"></use>
                                </svg>
                            </div>
                        </span>
                        <div class="message">
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <div style="flex: 1; min-width: 0;">
                                    <div style="font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                        ${room_name}
                                    </div>
                                    <div style="font-size: 11px; color: #6c757d; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                        Doc: ${doc_name}
                                    </div>
                                </div>
                                ${unread_badge}
                            </div>
                            ${last_message}
                        </div>
                    </div>
                </a>
            `;
        });
        
        chat_list.innerHTML = rooms_html;
        
    } catch (error) {
        console.error("Error in forEach:", error);
        show_chat_error("Error displaying chat rooms");
    }
}

function get_room_type_icon(room_type) {
    switch(room_type) {
        case 'Direct Message': return 'es-line-user';
        case 'Team Chat': return 'es-line-users';
        case 'Group Chat': return 'es-line-chat-alt';
        case 'Announcement': return 'es-line-megaphone';
        default: return 'es-line-chat-alt';
    }
}

function update_unread_count(rooms) {
    const notifications_seen = document.querySelector('#chat-icon-container .notifications-seen');
    const notifications_unseen = document.querySelector('#chat-icon-container .notifications-unseen');
    
    if (!notifications_seen || !notifications_unseen) return;
    
    let total_unread = 0;
    if (rooms && Array.isArray(rooms)) {
        total_unread = rooms.reduce((sum, room) => sum + (room.unread_count || 0), 0);
    }
    
    if (total_unread > 0) {
        notifications_seen.style.display = 'none';
        notifications_unseen.style.display = 'block';
        
        const srText = notifications_unseen.querySelector('.sr-only');
        if (srText) {
            srText.textContent = `You have ${total_unread} unread messages`;
        }
    } else {
        notifications_seen.style.display = 'block';
        notifications_unseen.style.display = 'none';
    }
}

function update_unread_badge() {
    frappe.call({
        method: "vms.get_user_chat_rooms",
        args: { page: 1, page_size: 20 },
        callback: function(response) {
            let rooms = [];
            if (response && response.message) {
                // Use the same priority order as load_chat_rooms_preview
                if (response.message.success && response.message.data && response.message.data.rooms && Array.isArray(response.message.data.rooms)) {
                    rooms = response.message.data.rooms;
                }
                else if (response.message.rooms && Array.isArray(response.message.rooms)) {
                    rooms = response.message.rooms;
                }
                else if (response.message.success && Array.isArray(response.message.data)) {
                    rooms = response.message.data;
                }
                else if (Array.isArray(response.message)) {
                    rooms = response.message;
                }
            }
            update_unread_count(rooms);
        }
    });
}

function show_chat_error(message) {
    const chat_list = document.querySelector('#chat-rooms-list');
    if (chat_list) {
        chat_list.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #dc3545;">
                <div>${message}</div>
                <button onclick="load_chat_rooms_preview()" 
                        style="margin-top: 8px; padding: 4px 8px; border: 1px solid #dc3545; background: none; color: #dc3545; border-radius: 3px; cursor: pointer;">
                    Retry
                </button>
            </div>
        `;
    }
}

function open_chat_application() {
    console.log("🚀 Opening chat application...");
    
    const dropdown = document.querySelector('#chat-dropdown');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
    
    try {
        frappe.set_route('List', 'Chat Room');
    } catch (error) {
        console.error("❌ Error opening chat application:", error);
        frappe.msgprint({
            title: 'Chat Application',
            message: 'Opening chat rooms list...',
            indicator: 'blue'
        });
    }
}

function show_desktop_notification(data) {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
        return;
    }
    
    try {
        const notification = new Notification(
            data.sender_name ? `${data.sender_name}` : 'New Chat Message',
            {
                body: data.content ? data.content.substring(0, 100) : 'You have a new message',
                icon: '/assets/vms/images/chat-icon.png',
                requireInteraction: false,
                silent: false
            }
        );
        
        notification.onclick = function(event) {
            event.preventDefault();
            window.focus();
            
            if (data.room_id) {
                open_chat_messaging(data.room_id, data.room_name || 'Chat', data.room_type || 'Group Chat');
            }
            
            notification.close();
        };
        
        setTimeout(() => {
            notification.close();
        }, 8000);
        
    } catch (error) {
        console.log('❌ Desktop notification error:', error);
    }
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

// Add CSS for positioning
if (!document.querySelector('#chat-positioning-styles')) {
    const style = document.createElement('style');
    style.id = 'chat-positioning-styles';
    style.textContent = `
        #chat-icon-container {
            order: -1 !important;
            margin-right: 15px !important;
        }
        
        ul.navbar-nav {
            display: flex !important;
        }`
        
// Add CSS for positioning
if (!document.querySelector('#chat-positioning-styles')) {
    const style = document.createElement('style');
    style.id = 'chat-positioning-styles';
    style.textContent = `
        #chat-icon-container {
            order: -1 !important;
            margin-right: 15px !important;
        }
        
        ul.navbar-nav {
            display: flex !important;
        }
        
        #chat-icon-container .btn-reset:hover {
            background-color: rgba(0, 123, 255, 0.1) !important;
        }
        
        #chat-messaging-modal {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        
        #chat-messaging-modal textarea:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
        }
        
        #chat-messaging-modal button:hover {
            opacity: 0.9;
            transform: scale(1.02);
        }
    `;
    document.head.appendChild(style);
    }
}
// Global functions
window.load_chat_rooms_preview = load_chat_rooms_preview;
window.open_chat_application = open_chat_application;
window.open_chat_messaging = open_chat_messaging;
window.close_chat_messaging_modal = close_chat_messaging_modal;
window.handle_chat_input_keydown = handle_chat_input_keydown;
window.send_chat_message = send_chat_message;