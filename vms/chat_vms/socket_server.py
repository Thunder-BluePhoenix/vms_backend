# vms/chat_vms/socket_server.py
# Socket.IO server setup for real-time chat functionality

import frappe
import socketio
import eventlet
import eventlet.wsgi
from frappe.utils import get_site_name

# Create Socket.IO server instance
sio = socketio.Server(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='eventlet'
)

# Wrap with WSGI application
app = socketio.WSGIApp(sio)

# Store user sessions
user_sessions = {}
room_sessions = {}

@sio.event
def connect(sid, environ):
    """Handle client connection"""
    try:
        # Get user from session (you may need to implement proper authentication)
        user = frappe.session.user if hasattr(frappe, 'session') else 'Guest'
        
        print(f"Client {sid} connected as {user}")
        
        # Store user session
        user_sessions[sid] = {
            'user': user,
            'rooms': []
        }
        
        # Emit connection success
        sio.emit('connected', {'message': 'Connected to chat server'}, room=sid)
        
    except Exception as e:
        print(f"Connection error: {e}")

@sio.event
def disconnect(sid):
    """Handle client disconnection"""
    try:
        if sid in user_sessions:
            user = user_sessions[sid]['user']
            rooms = user_sessions[sid]['rooms']
            
            # Leave all rooms
            for room in rooms:
                sio.leave_room(sid, room)
                if room in room_sessions:
                    room_sessions[room].discard(sid)
                    
                    # Notify others in room about user leaving
                    sio.emit('user_left_room', {
                        'user': user,
                        'room': room
                    }, room=room)
            
            # Remove user session
            del user_sessions[sid]
            
            print(f"Client {sid} ({user}) disconnected")
            
    except Exception as e:
        print(f"Disconnection error: {e}")

@sio.event
def join_room(sid, data):
    """Handle room join requests"""
    try:
        room_id = data.get('room_id')
        user = user_sessions.get(sid, {}).get('user', 'Guest')
        
        if not room_id:
            sio.emit('error', {'message': 'Room ID required'}, room=sid)
            return
        
        # Join the room
        sio.enter_room(sid, room_id)
        
        # Update session
        if sid in user_sessions:
            user_sessions[sid]['rooms'].append(room_id)
        
        # Update room sessions
        if room_id not in room_sessions:
            room_sessions[room_id] = set()
        room_sessions[room_id].add(sid)
        
        # Notify others in room
        sio.emit('user_joined_room', {
            'user': user,
            'room': room_id
        }, room=room_id, skip_sid=sid)
        
        # Confirm join to user
        sio.emit('room_joined', {
            'room_id': room_id,
            'message': f'Joined room {room_id}'
        }, room=sid)
        
        print(f"User {user} ({sid}) joined room {room_id}")
        
    except Exception as e:
        print(f"Join room error: {e}")
        sio.emit('error', {'message': 'Failed to join room'}, room=sid)

@sio.event
def leave_room(sid, data):
    """Handle room leave requests"""
    try:
        room_id = data.get('room_id')
        user = user_sessions.get(sid, {}).get('user', 'Guest')
        
        if not room_id:
            sio.emit('error', {'message': 'Room ID required'}, room=sid)
            return
        
        # Leave the room
        sio.leave_room(sid, room_id)
        
        # Update session
        if sid in user_sessions and room_id in user_sessions[sid]['rooms']:
            user_sessions[sid]['rooms'].remove(room_id)
        
        # Update room sessions
        if room_id in room_sessions:
            room_sessions[room_id].discard(sid)
        
        # Notify others in room
        sio.emit('user_left_room', {
            'user': user,
            'room': room_id
        }, room=room_id)
        
        # Confirm leave to user
        sio.emit('room_left', {
            'room_id': room_id,
            'message': f'Left room {room_id}'
        }, room=sid)
        
        print(f"User {user} ({sid}) left room {room_id}")
        
    except Exception as e:
        print(f"Leave room error: {e}")
        sio.emit('error', {'message': 'Failed to leave room'}, room=sid)

@sio.event
def send_message(sid, data):
    """Handle message sending"""
    try:
        room_id = data.get('room_id')
        message_content = data.get('content')
        user = user_sessions.get(sid, {}).get('user', 'Guest')
        
        if not room_id or not message_content:
            sio.emit('error', {'message': 'Room ID and message content required'}, room=sid)
            return
        
        # Create message data
        message_data = {
            'room_id': room_id,
            'sender': user,
            'content': message_content,
            'timestamp': frappe.utils.now(),
            'message_type': data.get('message_type', 'Text')
        }
        
        # Broadcast message to room
        sio.emit('new_message', message_data, room=room_id)
        
        print(f"Message sent by {user} in room {room_id}: {message_content}")
        
    except Exception as e:
        print(f"Send message error: {e}")
        sio.emit('error', {'message': 'Failed to send message'}, room=sid)

@sio.event
def typing_indicator(sid, data):
    """Handle typing indicators"""
    try:
        room_id = data.get('room_id')
        is_typing = data.get('is_typing', False)
        user = user_sessions.get(sid, {}).get('user', 'Guest')
        
        if not room_id:
            return
        
        # Broadcast typing indicator to room (except sender)
        sio.emit('typing_indicator', {
            'room_id': room_id,
            'user': user,
            'is_typing': is_typing
        }, room=room_id, skip_sid=sid)
        
    except Exception as e:
        print(f"Typing indicator error: {e}")

def start_socket_server(host='127.0.0.1', port=8013):
    """Start the Socket.IO server"""
    print(f"Starting Socket.IO server on {host}:{port}")
    try:
        eventlet.wsgi.server(eventlet.listen((host, port)), app)
    except Exception as e:
        print(f"Failed to start Socket.IO server: {e}")

if __name__ == '__main__':
    # Start the server when run directly
    start_socket_server()