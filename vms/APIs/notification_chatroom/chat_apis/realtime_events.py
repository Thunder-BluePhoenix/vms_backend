# vms/APIs/notification_chatroom/chat_apis/realtime_events.py
import frappe
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist()
def join_chat_room(room_id):
    """
    Join a chat room for real-time updates
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: Success response with room subscription
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Subscribe user to room's real-time events
        room_channel = f"chat_room_{room_id}"
        
        # Update user's last seen timestamp
        room.update_last_read(current_user)
        
        # Notify other members that user is online
        frappe.publish_realtime(
            event="user_joined_room",
            message={
                "user": current_user,
                "room_id": room_id,
                "timestamp": str(now_datetime())
            },
            user=[member.user for member in room.members if member.user != current_user],
            room=room_channel
        )
        
        return {
            "success": True,
            "data": {
                "room_channel": room_channel,
                "user_permissions": permissions
            },
            "message": "Successfully joined room for real-time updates"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in join_chat_room: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def leave_chat_room(room_id):
    """
    Leave a chat room's real-time updates
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Update user's last read timestamp
        room.update_last_read(current_user)
        
        # Notify other members that user left
        room_channel = f"chat_room_{room_id}"
        frappe.publish_realtime(
            event="user_left_room",
            message={
                "user": current_user,
                "room_id": room_id,
                "timestamp": str(now_datetime())
            },
            user=[member.user for member in room.members if member.user != current_user],
            room=room_channel
        )
        
        return {
            "success": True,
            "message": "Successfully left room real-time updates"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in leave_chat_room: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def send_typing_indicator(room_id, is_typing):
    """
    Send typing indicator to room members
    
    Args:
        room_id (str): Chat room ID
        is_typing (int): 1 if typing, 0 if stopped typing
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Send typing indicator to other members
        room_channel = f"chat_room_{room_id}"
        frappe.publish_realtime(
            event="typing_indicator",
            message={
                "user": current_user,
                "room_id": room_id,
                "is_typing": bool(int(is_typing)),
                "timestamp": str(now_datetime())
            },
            user=[member.user for member in room.members if member.user != current_user],
            room=room_channel
        )
        
        return {
            "success": True,
            "message": "Typing indicator sent"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in send_typing_indicator: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def get_online_users(room_id):
    """
    Get list of online users in a chat room
    Note: This is a simplified version. For production, you'd need to track
    user sessions and websocket connections more accurately.
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: List of online users
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Get room members with their last activity
        # This is a simplified implementation
        # In production, you'd track actual websocket connections
        online_users = []
        
        for member in room.members:
            # Check if user has been active in last 5 minutes
            last_activity = frappe.db.get_value(
                "User",
                member.user,
                "last_active"
            )
            
            user_info = frappe.db.get_value(
                "User",
                member.user,
                ["full_name", "user_image"],
                as_dict=True
            )
            
            # Consider user online if active in last 5 minutes
            is_online = False
            if last_activity:
                from frappe.utils import time_diff_in_seconds
                if time_diff_in_seconds(now_datetime(), last_activity) < 300:  # 5 minutes
                    is_online = True
                    
            online_users.append({
                "user": member.user,
                "full_name": user_info.full_name if user_info else member.user,
                "user_image": user_info.user_image if user_info else None,
                "is_online": is_online,
                "last_activity": str(last_activity) if last_activity else None
            })
            
        return {
            "success": True,
            "data": {
                "online_users": online_users,
                "total_members": len(room.members)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_online_users: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }