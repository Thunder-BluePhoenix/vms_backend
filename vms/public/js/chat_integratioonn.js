// vms/public/js/chat_integration_frappe_socketio.js
// Chat integration using Frappe's built-in Socket.IO server

function onFrappeReady(callback) {
    if (typeof frappe !== "undefined" && frappe.ready) {
        frappe.ready(callback);
    } else {
        document.addEventListener("DOMContentLoaded", callback);
    }
}

// Initialize when Frappe is ready
onFrappeReady(() => {
    console.log("Initializing chat integration with Frappe Socket.IO...");
    add_chat_icon_to_navbar();
    init_chat_functionality();
});

function add_chat_icon_to_navbar() {
    // Wait for navbar to be fully loaded
    setTimeout(() => {
        const navbar_right = document.querySelector('.navbar-nav.navbar-right') 
                          || document.querySelector('.navbar-nav.ms-auto')
                          || document.querySelector('nav .nav');
        
        if (!navbar_right) {
            console.log("Navbar not found, retrying...");
            setTimeout(add_chat_icon_to_navbar, 1000);
            return;
        }
        
        // Check if chat icon already exists
        if (document.querySelector('#chat-icon-container')) {
            console.log("Chat icon already exists");
            return;
        }
        
        console.log("Adding chat icon to navbar...");
        
        // Create chat icon container
        const chat_container = document.createElement('li');
        chat_container.id = 'chat-icon-container';
        chat_container.className = 'dropdown';
        
        // Create chat icon with dropdown
        chat_container.innerHTML = `
            <a href="#" class="dropdown-toggle" data-toggle="dropdown" id="chat-icon" 
               style="padding: 15px 12px; position: relative; text-decoration: none;">
                <i class="fa fa-comments" style="font-size: 18px; color: #6c757d;"></i>
                <span id="chat-unread-badge" class="badge badge-danger" 
                      style="position: absolute; top: 6px; right: 6px; display: none; 
                             background: #dc3545; color: white; border-radius: 50%; 
                             width: 18px; height: 18px; font-size: 10px; line-height: 18px; 
                             text-align: center; min-width: 18px;">0</span>
            </a>
            <ul class="dropdown-menu dropdown-menu-right" id="chat-dropdown" 
                style="width: 350px; max-height: 400px; overflow-y: auto; 
                       box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 1px solid #dee2e6;">
                <li class="dropdown-header" style="padding: 12px 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; border-bottom: none;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="font-size: 14px;">Chat Messages</strong>
                        <button class="btn btn-xs" onclick="open_chat_application()" 
                                style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); 
                                       color: white; font-size: 11px; padding: 4px 8px; border-radius: 3px;">
                            Open Chat
                        </button>
                    </div>
                </li>
                <li id="chat-rooms-list">
                    <div style="padding: 20px; text-align: center; color: #6c757d;">
                        <i class="fa fa-spinner fa-spin" style="margin-right: 8px;"></i>
                        Loading chats...
                    </div>
                </li>
                <li class="divider" style="margin: 0;"></li>
                <li>
                    <a href="#" onclick="open_chat_application()" 
                       style="text-align: center; padding: 12px; color: #007bff; font-size: 13px;">
                        <i class="fa fa-external-link" style="margin-right: 5px;"></i>
                        View All Messages
                    </a>
                </li>
            </ul>
        `;
        
        // Find a good position for the chat icon
        const user_dropdown = navbar_right.querySelector('li:last-child');
        const help_icon = navbar_right.querySelector('li:has(.fa-question)');
        
        // Insert chat icon at appropriate position
        if (help_icon) {
            navbar_right.insertBefore(chat_container, help_icon);
        } else if (user_dropdown) {
            navbar_right.insertBefore(chat_container, user_dropdown);
        } else {
            navbar_right.appendChild(chat_container);
        }
        
        console.log("Chat icon added to navbar successfully");
        
        // Add click handler for the chat icon
        const chatIcon = document.querySelector('#chat-icon');
        if (chatIcon) {
            chatIcon.addEventListener('click', function(e) {
                e.preventDefault();
                load_chat_rooms_preview();
                request_notification_permission();
            });
        }
        
    }, 500);
}

function init_chat_functionality() {
    console.log("Initializing chat functionality...");
    
    // Load chat rooms when chat icon is clicked
    load_chat_rooms_preview();
    
    // Initialize Frappe's Socket.IO integration
    init_frappe_socketio_integration();
    
    // Set up periodic refresh for chat data
    setInterval(() => {
        if (document.querySelector('#chat-dropdown.open, #chat-dropdown.show')) {
            load_chat_rooms_preview();
        }
    }, 30000); // Refresh every 30 seconds when dropdown is open
}

function init_frappe_socketio_integration() {
    console.log("Setting up Frappe Socket.IO integration...");
    
    // Use Frappe's built-in Socket.IO functionality
    if (typeof frappe !== 'undefined' && frappe.socketio) {
        console.log("Using Frappe's Socket.IO connection");
        
        // Listen for chat-related real-time events
        frappe.realtime.on('chat_message_received', function(data) {
            console.log('New chat message received via Frappe realtime:', data);
            handle_new_message(data);
        });
        
        frappe.realtime.on('chat_room_updated', function(data) {
            console.log('Chat room updated via Frappe realtime:', data);
            load_chat_rooms_preview();
        });
        
        frappe.realtime.on('chat_user_status_changed', function(data) {
            console.log('User status changed via Frappe realtime:', data);
            // Update UI accordingly
        });
        
    } else if (typeof io !== 'undefined') {
        console.log("Setting up direct Socket.IO connection...");
        
        // Fallback: Direct Socket.IO connection to Frappe's port
        const socketio_port = 9013; // From your config
        const socket_url = `${window.location.protocol}//${window.location.hostname}:${socketio_port}`;
        
        const socket = io(socket_url, {
            transports: ['polling', 'websocket'],
            timeout: 20000,
            forceNew: false
        });
        
        socket.on('connect', function() {
            console.log('Connected to Frappe Socket.IO server');
            
            // Join user to their chat channels
            if (frappe.session && frappe.session.user) {
                socket.emit('join_user_channel', {
                    user: frappe.session.user,
                    type: 'chat'
                });
            }
        });
        
        socket.on('chat_message', function(data) {
            console.log('Chat message received:', data);
            handle_new_message(data);
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from Frappe Socket.IO server');
        });
        
        socket.on('connect_error', function(error) {
            console.log('Socket.IO connection error:', error);
        });
        
        // Store socket for later use
        window.chat_socket = socket;
        
    } else {
        console.log("No Socket.IO available, using polling only");
    }
}

function handle_new_message(data) {
    // Refresh chat rooms preview
    load_chat_rooms_preview();
    
    // Show desktop notification
    show_desktop_notification(data);
    
    // Update unread badge
    update_unread_badge();
}

function load_chat_rooms_preview() {
    const chat_list = document.querySelector('#chat-rooms-list');
    if (!chat_list) return;
    
    // Show loading state
    chat_list.innerHTML = `
        <div style="padding: 20px; text-align: center; color: #6c757d;">
            <i class="fa fa-spinner fa-spin" style="margin-right: 8px;"></i>
            Loading chats...
        </div>
    `;
    
    // Make API call to get user's chat rooms
    frappe.call({
        method: "vms.get_user_chat_rooms",
        args: {
            page: 1,
            page_size: 10
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                const rooms = response.message.data || [];
                display_chat_rooms(rooms);
                update_unread_count(rooms);
            } else {
                show_chat_error("Failed to load chats");
            }
        },
        error: function(error) {
            console.error("Error loading chat rooms:", error);
            show_chat_error("Unable to connect to chat service");
        }
    });
}

function display_chat_rooms(rooms) {
    const chat_list = document.querySelector('#chat-rooms-list');
    if (!chat_list) return;
    
    if (!rooms || rooms.length === 0) {
        chat_list.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #6c757d;">
                <i class="fa fa-comment-o" style="font-size: 24px; margin-bottom: 8px;"></i><br>
                No chat rooms found<br>
                <small>Create a new room to get started</small>
            </div>
        `;
        return;
    }
    
    let rooms_html = '';
    rooms.forEach(room => {
        const unread_badge = room.unread_count > 0 ? 
            `<span class="badge badge-primary" style="background: #007bff; margin-left: 5px; font-size: 9px; padding: 2px 6px;">${room.unread_count > 99 ? '99+' : room.unread_count}</span>` : '';
        
        const last_message = room.last_message ? 
            `<div style="color: #6c757d; font-size: 12px; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${room.last_message.substring(0, 45)}${room.last_message.length > 45 ? '...' : ''}
            </div>` : '';
        
        const room_icon = get_room_type_icon(room.room_type);
        const room_color = get_room_type_color(room.room_type);
        
        rooms_html += `
            <li style="border-bottom: 1px solid #f8f9fa;">
                <a href="#" onclick="open_chat_room('${room.name}')" 
                   style="padding: 12px 20px; display: block; text-decoration: none; color: #333; transition: all 0.2s ease;"
                   onmouseover="this.style.backgroundColor='#f8f9fa'; this.style.transform='translateX(2px)'"
                   onmouseout="this.style.backgroundColor=''; this.style.transform=''">
                    <div style="display: flex; align-items: flex-start; justify-content: space-between;">
                        <div style="flex: 1; min-width: 0;">
                            <div style="display: flex; align-items: center; margin-bottom: 2px;">
                                <i class="${room_icon}" style="margin-right: 8px; color: ${room_color}; font-size: 14px; min-width: 16px;"></i>
                                <span style="font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px;">
                                    ${room.room_name}
                                </span>
                                ${unread_badge}
                            </div>
                            ${last_message}
                        </div>
                    </div>
                </a>
            </li>
        `;
    });
    
    chat_list.innerHTML = rooms_html;
}

function get_room_type_icon(room_type) {
    switch(room_type) {
        case 'Direct Message': return 'fa fa-user';
        case 'Team Chat': return 'fa fa-users';
        case 'Group Chat': return 'fa fa-comments';
        case 'Announcement': return 'fa fa-bullhorn';
        default: return 'fa fa-comment';
    }
}

function get_room_type_color(room_type) {
    switch(room_type) {
        case 'Direct Message': return '#28a745';
        case 'Team Chat': return '#007bff';
        case 'Group Chat': return '#17a2b8';
        case 'Announcement': return '#ffc107';
        default: return '#6c757d';
    }
}

function update_unread_count(rooms) {
    const badge = document.querySelector('#chat-unread-badge');
    if (!badge) return;
    
    let total_unread = 0;
    if (rooms && Array.isArray(rooms)) {
        total_unread = rooms.reduce((sum, room) => sum + (room.unread_count || 0), 0);
    }
    
    if (total_unread > 0) {
        badge.textContent = total_unread > 99 ? '99+' : total_unread;
        badge.style.display = 'block';
        
        // Add pulse animation to badge
        badge.style.animation = 'pulse 2s infinite';
        
        // Make chat icon more prominent
        const chat_icon = document.querySelector('#chat-icon i');
        if (chat_icon) {
            chat_icon.style.color = '#007bff';
        }
    } else {
        badge.style.display = 'none';
        
        // Reset chat icon color
        const chat_icon = document.querySelector('#chat-icon i');
        if (chat_icon) {
            chat_icon.style.color = '#6c757d';
        }
    }
}

function update_unread_badge() {
    // Reload chat rooms to get updated unread counts
    frappe.call({
        method: "vms.get_user_chat_rooms",
        args: { page: 1, page_size: 20 },
        callback: function(response) {
            if (response.message && response.message.success) {
                update_unread_count(response.message.data || []);
            }
        }
    });
}

function show_chat_error(message) {
    const chat_list = document.querySelector('#chat-rooms-list');
    if (chat_list) {
        chat_list.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #dc3545;">
                <i class="fa fa-exclamation-triangle" style="font-size: 20px; margin-bottom: 8px;"></i><br>
                ${message}<br>
                <button onclick="load_chat_rooms_preview()" 
                        style="margin-top: 8px; background: none; border: 1px solid #dc3545; color: #dc3545; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 11px;">
                    Retry
                </button>
            </div>
        `;
    }
}

function open_chat_application() {
    // Close dropdown first
    const dropdown = document.querySelector('#chat-dropdown');
    if (dropdown) {
        dropdown.classList.remove('open', 'show');
        const parent = dropdown.closest('.dropdown');
        if (parent) {
            parent.classList.remove('open', 'show');
        }
    }
    
    try {
        // Option 1: Open Chat Room List in Frappe Desk
        frappe.set_route('List', 'Chat Room');
        
        // Option 2: Alternative - open in new tab
        // window.open('/desk#List/Chat%20Room', '_blank');
        
    } catch (error) {
        console.error("Error opening chat application:", error);
        frappe.msgprint({
            title: 'Chat Application',
            message: 'Opening chat rooms list...',
            indicator: 'blue'
        });
    }
}

function open_chat_room(room_id) {
    // Close dropdown first
    const dropdown = document.querySelector('#chat-dropdown');
    if (dropdown) {
        dropdown.classList.remove('open', 'show');
        const parent = dropdown.closest('.dropdown');
        if (parent) {
            parent.classList.remove('open', 'show');
        }
    }
    
    try {
        // Open specific chat room in Frappe Desk
        frappe.set_route('Form', 'Chat Room', room_id);
        
        // Mark room as read
        frappe.call({
            method: "vms.mark_room_as_read",
            args: { room_id: room_id },
            callback: function() {
                // Refresh chat preview to update unread counts
                setTimeout(load_chat_rooms_preview, 500);
            }
        });
        
    } catch (error) {
        console.error("Error opening chat room:", error);
        frappe.msgprint({
            title: 'Chat Room',
            message: `Opening chat room: ${room_id}`,
            indicator: 'blue'
        });
    }
}

function show_desktop_notification(data) {
    // Check if notifications are supported and permitted
    if (!('Notification' in window) || Notification.permission !== 'granted') {
        return;
    }
    
    try {
        const notification = new Notification(
            data.sender_name ? `${data.sender_name}` : 'New Chat Message',
            {
                body: data.content ? data.content.substring(0, 100) : 'You have a new message',
                icon: '/assets/vms/images/chat-icon.png',
                badge: '/assets/vms/images/chat-badge.png',
                tag: `chat-${data.room_id}`,
                requireInteraction: false,
                silent: false,
                data: {
                    room_id: data.room_id,
                    room_name: data.room_name
                }
            }
        );
        
        notification.onclick = function(event) {
            event.preventDefault();
            window.focus();
            
            // Open the chat room
            if (data.room_id) {
                open_chat_room(data.room_id);
            }
            
            notification.close();
        };
        
        // Auto close after 8 seconds
        setTimeout(() => {
            notification.close();
        }, 8000);
        
    } catch (error) {
        console.log('Desktop notification error:', error);
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
            } else {
                console.log('Notification permission denied');
            }
        });
    }
}

// Publish real-time events for chat (to be used by server-side)
function publish_chat_event(event, data) {
    if (typeof frappe !== 'undefined' && frappe.publish_realtime) {
        frappe.publish_realtime(event, data);
    }
}

// Listen for Frappe's real-time events
function setup_frappe_realtime_listeners() {
    if (typeof frappe !== 'undefined' && frappe.realtime) {
        // Listen for new messages
        frappe.realtime.on('chat_new_message', function(data) {
            console.log('Real-time: New chat message', data);
            handle_new_message(data);
        });
        
        // Listen for room updates
        frappe.realtime.on('chat_room_update', function(data) {
            console.log('Real-time: Chat room update', data);
            load_chat_rooms_preview();
        });
        
        // Listen for user status changes
        frappe.realtime.on('chat_user_status', function(data) {
            console.log('Real-time: User status change', data);
            // Update user status in UI if needed
        });
    }
}

// CSS styles injection for better visual integration
function inject_chat_styles() {
    if (document.querySelector('#chat-integration-styles')) {
        return; // Already injected
    }
    
    const style = document.createElement('style');
    style.id = 'chat-integration-styles';
    style.textContent = `
        @keyframes pulse {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
            }
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 4px rgba(220, 53, 69, 0);
            }
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(220, 53, 69, 0);
            }
        }
        
        #chat-icon-container:hover #chat-icon i {
            color: #007bff !important;
            transform: scale(1.1);
            transition: all 0.3s ease;
        }
        
        #chat-dropdown {
            border-radius: 8px;
            overflow: hidden;
            margin-top: 8px;
        }
        
        #chat-dropdown li a:hover {
            background-color: #f8f9fa !important;
        }
        
        @media (max-width: 768px) {
            #chat-dropdown {
                width: 300px !important;
                right: 0;
                left: auto;
            }
        }
        
        .dropdown-menu.dropdown-menu-right {
            right: 0;
            left: auto;
        }
        
        /* Chat icon loading animation */
        .chat-icon-loading {
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    
    document.head.appendChild(style);
}

// Initialize everything
inject_chat_styles();
setup_frappe_realtime_listeners();

// Global functions for external access
window.load_chat_rooms_preview = load_chat_rooms_preview;
window.open_chat_application = open_chat_application;
window.open_chat_room = open_chat_room;
window.publish_chat_event = publish_chat_event;