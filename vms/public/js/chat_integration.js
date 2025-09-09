// File: vms/public/js/chat_integration.js
// This file adds chat functionality to Frappe's navbar

frappe.ready(function() {
    // Add chat icon to navbar when page loads
    add_chat_icon_to_navbar();
    
    // Initialize chat functionality
    init_chat_functionality();
});

function add_chat_icon_to_navbar() {
    // Wait for navbar to load
    setTimeout(() => {
        const navbar_right = document.querySelector('.navbar-nav.navbar-right');
        if (!navbar_right) return;
        
        // Check if chat icon already exists
        if (document.querySelector('#chat-icon-container')) return;
        
        // Create chat icon container
        const chat_container = document.createElement('li');
        chat_container.id = 'chat-icon-container';
        chat_container.className = 'dropdown';
        
        // Create chat icon
        chat_container.innerHTML = `
            <a href="#" class="dropdown-toggle" data-toggle="dropdown" id="chat-icon" 
               style="padding: 15px 12px; position: relative;">
                <i class="fa fa-comments" style="font-size: 16px; color: #6c757d;"></i>
                <span id="chat-unread-badge" class="badge badge-danger" 
                      style="position: absolute; top: 8px; right: 8px; display: none; 
                             background: #dc3545; color: white; border-radius: 50%; 
                             width: 18px; height: 18px; font-size: 10px; line-height: 18px; 
                             text-align: center;">0</span>
            </a>
            <ul class="dropdown-menu" id="chat-dropdown" style="width: 350px; max-height: 400px; overflow-y: auto;">
                <li class="dropdown-header" style="padding: 10px 20px; border-bottom: 1px solid #eee;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>Messages</strong>
                        <button class="btn btn-xs btn-primary" onclick="open_chat_application()" 
                                style="font-size: 11px; padding: 2px 8px;">
                            Open Chat
                        </button>
                    </div>
                </li>
                <li id="chat-rooms-list">
                    <div style="padding: 20px; text-align: center; color: #6c757d;">
                        <i class="fa fa-spinner fa-spin"></i> Loading chats...
                    </div>
                </li>
                <li class="divider"></li>
                <li>
                    <a href="#" onclick="open_chat_application()" style="text-align: center; padding: 10px;">
                        <i class="fa fa-external-link"></i> View All Messages
                    </a>
                </li>
            </ul>
        `;
        
        // Find the notification icon and insert chat icon before it
        const notification_icon = navbar_right.querySelector('li:has(.dropdown-toggle[data-label="Notifications"])') 
                                || navbar_right.querySelector('li:has([data-original-title*="notification" i])');
        
        if (notification_icon) {
            navbar_right.insertBefore(chat_container, notification_icon);
        } else {
            // If notification icon not found, add at the end
            navbar_right.appendChild(chat_container);
        }
        
        // Load chat rooms
        load_chat_rooms_preview();
        
    }, 1000);
}

function init_chat_functionality() {
    // Initialize real-time chat updates
    if (typeof io !== 'undefined') {
        init_websocket_connection();
    }
    
    // Refresh chat data every 30 seconds
    setInterval(() => {
        if (document.querySelector('#chat-icon-container')) {
            load_chat_rooms_preview();
        }
    }, 30000);
}

function load_chat_rooms_preview() {
    frappe.call({
        method: 'vms.get_user_chat_rooms',
        args: {
            page: 1,
            page_size: 5 // Show only recent 5 chats in dropdown
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                render_chat_rooms_preview(response.message.data.rooms);
                update_unread_count(response.message.data.rooms);
            } else {
                show_chat_error('Failed to load chats');
            }
        },
        error: function() {
            show_chat_error('Error loading chats');
        }
    });
}

function render_chat_rooms_preview(rooms) {
    const chat_list = document.querySelector('#chat-rooms-list');
    if (!chat_list) return;
    
    if (!rooms || rooms.length === 0) {
        chat_list.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #6c757d;">
                <i class="fa fa-comments-o"></i><br>
                No chat rooms found<br>
                <small>Create your first chat room!</small>
            </div>
        `;
        return;
    }
    
    let rooms_html = '';
    rooms.forEach(room => {
        const unread_badge = room.unread_count > 0 ? 
            `<span class="badge badge-primary" style="background: #007bff; margin-left: 5px;">${room.unread_count}</span>` : '';
        
        const last_message = room.last_message ? 
            `<small style="color: #6c757d; display: block; margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${room.last_message.substring(0, 50)}${room.last_message.length > 50 ? '...' : ''}
            </small>` : '';
        
        const room_icon = get_room_type_icon(room.room_type);
        
        rooms_html += `
            <li>
                <a href="#" onclick="open_chat_room('${room.name}')" 
                   style="padding: 10px 20px; border-bottom: 1px solid #f8f9fa; display: block;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="flex: 1; min-width: 0;">
                            <div style="display: flex; align-items: center;">
                                <i class="${room_icon}" style="margin-right: 8px; color: #6c757d;"></i>
                                <strong style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                    ${room.room_name}
                                </strong>
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
        case 'Group Chat': return 'fa fa-comment';
        case 'Announcement': return 'fa fa-bullhorn';
        default: return 'fa fa-comment';
    }
}

function update_unread_count(rooms) {
    const badge = document.querySelector('#chat-unread-badge');
    if (!badge) return;
    
    let total_unread = 0;
    if (rooms) {
        total_unread = rooms.reduce((sum, room) => sum + (room.unread_count || 0), 0);
    }
    
    if (total_unread > 0) {
        badge.textContent = total_unread > 99 ? '99+' : total_unread;
        badge.style.display = 'block';
        
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

function show_chat_error(message) {
    const chat_list = document.querySelector('#chat-rooms-list');
    if (chat_list) {
        chat_list.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #dc3545;">
                <i class="fa fa-exclamation-triangle"></i><br>
                ${message}
            </div>
        `;
    }
}

function open_chat_application() {
    // Close dropdown
    const dropdown = document.querySelector('#chat-dropdown');
    if (dropdown && dropdown.classList.contains('open')) {
        dropdown.classList.remove('open');
    }
    
    // Open chat application in a new window/tab or modal
    // You can customize this based on your frontend implementation
    if (typeof window !== 'undefined') {
        // Option 1: Open in new tab (for Next.js frontend)
        window.open('/chat', '_blank');
        
        // Option 2: Open in modal (if you have a modal implementation)
        // open_chat_modal();
        
        // Option 3: Navigate to chat page in same window
        // window.location.href = '/chat';
    }
}

function open_chat_room(room_id) {
    // Close dropdown
    const dropdown = document.querySelector('#chat-dropdown');
    if (dropdown && dropdown.classList.contains('open')) {
        dropdown.classList.remove('open');
    }
    
    // Open specific chat room
    if (typeof window !== 'undefined') {
        // Option 1: Open specific room in new tab
        window.open(`/chat/room/${room_id}`, '_blank');
        
        // Option 2: Open in modal with room context
        // open_chat_modal(room_id);
    }
}

function init_websocket_connection() {
    // Initialize WebSocket connection for real-time updates
    try {
        const socket = io(window.location.origin, {
            path: '/socket.io'
        });
        
        socket.on('connect', function() {
            console.log('Chat WebSocket connected');
        });
        
        socket.on('new_chat_message', function(data) {
            // Refresh chat preview when new message arrives
            load_chat_rooms_preview();
            
            // Show desktop notification if permission granted
            if (Notification.permission === 'granted') {
                new Notification(`New message in ${data.room_name || 'Chat'}`, {
                    body: data.content || 'New message received',
                    icon: '/assets/vms/images/chat-icon.png'
                });
            }
        });
        
        socket.on('disconnect', function() {
            console.log('Chat WebSocket disconnected');
        });
        
    } catch (error) {
        console.log('WebSocket not available:', error);
    }
}

// Request notification permission when user first interacts with chat
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

// Auto-request notification permission when chat icon is first clicked
document.addEventListener('click', function(e) {
    if (e.target.closest('#chat-icon')) {
        request_notification_permission();
    }
});

// CSS Styles for better integration
const chat_styles = `
<style>
#chat-icon-container:hover #chat-icon i {
    color: #007bff !important;
}

#chat-dropdown {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border: 1px solid #dee2e6;
}

#chat-dropdown li a:hover {
    background-color: #f8f9fa;
}

#chat-dropdown .dropdown-header {
    background-color: #fff;
    font-weight: 600;
}

@media (max-width: 768px) {
    #chat-dropdown {
        width: 300px !important;
        right: 0;
        left: auto;
    }
}
</style>
`;

// Inject styles
if (!document.querySelector('#chat-integration-styles')) {
    const style_element = document.createElement('div');
    style_element.id = 'chat-integration-styles';
    style_element.innerHTML = chat_styles;
    document.head.appendChild(style_element);
}