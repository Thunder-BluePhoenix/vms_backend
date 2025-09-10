# vms/APIs/notification_chatroom/chat_apis/realtime_enhanced.py
# Enhanced real-time chat API with improved notification and status tracking

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, get_datetime, time_diff_in_seconds
import json
from typing import Dict, List, Optional, Any

@frappe.whitelist()
def get_user_chat_status():
    """
    Get comprehensive chat status for the current user
    
    Returns:
        dict: User's chat status including unread counts, online status, etc.
    """
    try:
        current_user = frappe.session.user
        
        # Get total unread count across all rooms
        unread_query = """
            SELECT 
                COUNT(*) as total_unread,
                COUNT(DISTINCT cm.chat_room) as rooms_with_unread
            FROM `tabChat Message` cm
            INNER JOIN `tabChat Room Member` crm ON cm.chat_room = crm.parent
            WHERE crm.user = %(user)s 
            AND cm.timestamp > COALESCE(crm.last_read, '1900-01-01')
            AND cm.sender != %(user)s
            AND cm.is_deleted = 0
        """
        
        unread_result = frappe.db.sql(unread_query, {
            "user": current_user
        }, as_dict=True)[0]
        
        # Get recent activity status
        recent_activity_query = """
            SELECT 
                MAX(cm.timestamp) as last_message_time,
                COUNT(*) as total_messages_today
            FROM `tabChat Message` cm
            INNER JOIN `tabChat Room Member` crm ON cm.chat_room = crm.parent
            WHERE crm.user = %(user)s 
            AND DATE(cm.timestamp) = CURDATE()
            AND cm.is_deleted = 0
        """
        
        activity_result = frappe.db.sql(recent_activity_query, {
            "user": current_user
        }, as_dict=True)[0]
        
        # Check if there's new activity since last check
        last_check = frappe.cache().get_value(f"chat_last_check_{current_user}")
        current_time = now_datetime()
        
        has_new_activity = False
        if last_check and activity_result.get('last_message_time'):
            last_message_time = get_datetime(activity_result['last_message_time'])
            last_check_time = get_datetime(last_check)
            has_new_activity = last_message_time > last_check_time
        
        # Update last check time
        frappe.cache().set_value(f"chat_last_check_{current_user}", current_time, expires_in_sec=3600)
        
        # Get user's online status
        online_status = get_user_online_status(current_user)
        
        return {
            "success": True,
            "data": {
                "total_unread": unread_result.get('total_unread', 0),
                "rooms_with_unread": unread_result.get('rooms_with_unread', 0),
                "messages_today": activity_result.get('total_messages_today', 0),
                "last_message_time": str(activity_result.get('last_message_time')) if activity_result.get('last_message_time') else None,
                "has_new_activity": has_new_activity,
                "online_status": online_status,
                "timestamp": str(current_time)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_user_chat_status: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_recent_chat_activity():
    """
    Check for recent chat activity for real-time updates
    
    Returns:
        dict: Information about recent activity
    """
    try:
        current_user = frappe.session.user
        
        # Get last check time from cache
        cache_key = f"chat_activity_check_{current_user}"
        last_check = frappe.cache().get_value(cache_key)
        current_time = now_datetime()
        
        if not last_check:
            # First time check - set current time and return no new activity
            frappe.cache().set_value(cache_key, current_time, expires_in_sec=300)
            return {
                "success": True,
                "data": {
                    "has_new_activity": False,
                    "new_messages_count": 0,
                    "timestamp": str(current_time)
                }
            }
        
        # Check for new messages since last check
        new_messages_query = """
            SELECT 
                COUNT(*) as new_messages,
                COUNT(DISTINCT cm.chat_room) as affected_rooms
            FROM `tabChat Message` cm
            INNER JOIN `tabChat Room Member` crm ON cm.chat_room = crm.parent
            WHERE crm.user = %(user)s 
            AND cm.timestamp > %(last_check)s
            AND cm.sender != %(user)s
            AND cm.is_deleted = 0
        """
        
        result = frappe.db.sql(new_messages_query, {
            "user": current_user,
            "last_check": last_check
        }, as_dict=True)[0]
        
        has_new_activity = result.get('new_messages', 0) > 0
        
        # Update last check time
        frappe.cache().set_value(cache_key, current_time, expires_in_sec=300)
        
        return {
            "success": True,
            "data": {
                "has_new_activity": has_new_activity,
                "new_messages_count": result.get('new_messages', 0),
                "affected_rooms": result.get('affected_rooms', 0),
                "timestamp": str(current_time)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_recent_chat_activity: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def update_user_online_status(status="online"):
    """
    Update user's online status for chat
    
    Args:
        status (str): online, away, busy, offline
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Update user's last activity timestamp
        cache_key = f"chat_user_status_{current_user}"
        status_data = {
            "status": status,
            "last_seen": str(now_datetime()),
            "user": current_user
        }
        
        # Cache for 10 minutes
        frappe.cache().set_value(cache_key, status_data, expires_in_sec=600)
        
        # Also update in database if user record has custom fields
        try:
            if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_status"}):
                frappe.db.set_value("User", current_user, "custom_chat_status", status)
                
            if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_last_chat_activity"}):
                frappe.db.set_value("User", current_user, "custom_last_chat_activity", now_datetime())
                
        except Exception as e:
            # Custom fields might not exist, continue without error
            pass
        
        # Notify other users about status change
        frappe.publish_realtime(
            event="user_status_changed",
            message={
                "user": current_user,
                "status": status,
                "timestamp": str(now_datetime())
            },
            room="chat_global"
        )
        
        return {
            "success": True,
            "message": f"Status updated to {status}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in update_user_online_status: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def send_message_with_realtime(room_id, content, message_type="Text", reply_to=None):
    """
    Enhanced send message with real-time notifications
    
    Args:
        room_id (str): Chat room ID
        content (str): Message content
        message_type (str): Type of message
        reply_to (str): Message ID being replied to
        
    Returns:
        dict: Success response with message data
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        member_permissions = room.get_member_permissions(current_user)
        
        if not member_permissions.get("is_member"):
            return {"success": False, "error": "You are not a member of this chat room"}
        
        if member_permissions.get("is_muted"):
            return {"success": False, "error": "You are muted in this chat room"}
        
        # Create new message
        message_doc = frappe.new_doc("Chat Message")
        message_doc.chat_room = room_id
        message_doc.sender = current_user
        message_doc.message_content = content
        message_doc.message_type = message_type
        message_doc.timestamp = now_datetime()
        
        if reply_to:
            message_doc.reply_to_message = reply_to
        
        message_doc.insert(ignore_permissions=True)
        
        # Get sender information
        sender_info = frappe.db.get_value("User", current_user, 
                                        ["full_name", "user_image"], as_dict=True)
        
        # Prepare real-time notification data
        notification_data = {
            "message_id": message_doc.name,
            "room_id": room_id,
            "room_name": room.room_name,
            "room_type": room.room_type,
            "sender": current_user,
            "sender_name": sender_info.get("full_name") or current_user,
            "sender_image": sender_info.get("user_image"),
            "content": content,
            "message_type": message_type,
            "timestamp": str(message_doc.timestamp),
            "reply_to": reply_to
        }
        
        # Get room members for notifications
        room_members = [member.user for member in room.members if member.user != current_user]
        
        # Send real-time notification to room members
        frappe.publish_realtime(
            event="chat_new_message",
            message=notification_data,
            user=room_members,
            room=f"chat_room_{room_id}"
        )
        
        # Send desktop notifications to offline members
        send_desktop_notifications(room_members, notification_data)
        
        # Update room's last activity
        room.db_set("modified", now_datetime())
        
        return {
            "success": True,
            "data": {
                "message_id": message_doc.name,
                "timestamp": str(message_doc.timestamp)
            },
            "message": "Message sent successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in send_message_with_realtime: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def mark_room_as_read_enhanced(room_id):
    """
    Enhanced mark room as read with real-time updates
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Update user's last read timestamp for this room
        frappe.db.sql("""
            UPDATE `tabChat Room Member` 
            SET last_read = %s 
            WHERE parent = %s AND user = %s
        """, (now_datetime(), room_id, current_user))
        
        # Clear unread cache for this user
        cache_key = f"chat_unread_{current_user}"
        frappe.cache().delete_value(cache_key)
        
        # Notify real-time about read status change
        frappe.publish_realtime(
            event="room_read_status_changed",
            message={
                "room_id": room_id,
                "user": current_user,
                "timestamp": str(now_datetime())
            },
            room=f"chat_room_{room_id}"
        )
        
        return {
            "success": True,
            "message": "Room marked as read"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in mark_room_as_read_enhanced: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def send_typing_indicator_enhanced(room_id, is_typing=True):
    """
    Enhanced typing indicator with user information
    
    Args:
        room_id (str): Chat room ID
        is_typing (bool): Whether user is typing
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get user info
        user_info = frappe.db.get_value("User", current_user, 
                                      ["full_name", "user_image"], as_dict=True)
        
        # Send typing indicator to room members
        frappe.publish_realtime(
            event="user_typing",
            message={
                "room_id": room_id,
                "user": current_user,
                "user_name": user_info.get("full_name") or current_user,
                "user_image": user_info.get("user_image"),
                "is_typing": is_typing,
                "timestamp": str(now_datetime())
            },
            room=f"chat_room_{room_id}"
        )
        
        return {"success": True}
        
    except Exception as e:
        frappe.log_error(f"Error in send_typing_indicator_enhanced: {str(e)}")
        return {"success": False, "error": str(e)}

def get_user_online_status(user):
    """
    Get user's online status from cache
    
    Args:
        user (str): User ID
        
    Returns:
        str: User's online status
    """
    try:
        cache_key = f"chat_user_status_{user}"
        status_data = frappe.cache().get_value(cache_key)
        
        if not status_data:
            return "offline"
        
        # Check if user was seen recently (within 10 minutes)
        last_seen = get_datetime(status_data.get("last_seen"))
        current_time = now_datetime()
        
        if time_diff_in_seconds(current_time, last_seen) > 600:  # 10 minutes
            return "offline"
        
        return status_data.get("status", "offline")
        
    except Exception:
        return "offline"

def send_desktop_notifications(users, notification_data):
    """
    Send desktop notifications to specified users
    
    Args:
        users (list): List of user IDs
        notification_data (dict): Notification data
    """
    try:
        # This would integrate with your notification system
        # For now, we'll use Frappe's publish_realtime for browser notifications
        
        frappe.publish_realtime(
            event="chat_desktop_notification",
            message=notification_data,
            user=users
        )
        
    except Exception as e:
        frappe.log_error(f"Error sending desktop notifications: {str(e)}")

# Enhanced room management functions

@frappe.whitelist()
def get_user_chat_rooms_enhanced(page=1, page_size=20, room_type=None, search=None, include_activity=True):
    """
    Enhanced get user chat rooms with activity information
    
    Args:
        page (int): Page number
        page_size (int): Records per page
        room_type (str): Filter by room type
        search (str): Search in room names
        include_activity (bool): Include last activity information
        
    Returns:
        dict: Chat rooms with enhanced information
    """
    try:
        current_user = frappe.session.user
        page = cint(page) or 1
        page_size = min(cint(page_size) or 20, 100)
        offset = (page - 1) * page_size
        
        # Build conditions
        conditions = ["crm.user = %(user)s", "cr.room_status = 'Active'"]
        values = {"user": current_user}
        
        if room_type:
            conditions.append("cr.room_type = %(room_type)s")
            values["room_type"] = room_type
            
        if search:
            conditions.append("cr.room_name LIKE %(search)s")
            values["search"] = f"%{search}%"
        
        where_clause = " AND ".join(conditions)
        
        # Enhanced query with last message and unread count
        query = f"""
            SELECT 
                cr.name,
                cr.room_name,
                cr.room_type,
                cr.description,
                cr.is_private,
                cr.modified as last_activity,
                crm.role as member_role,
                crm.last_read,
                (
                    SELECT COUNT(*) 
                    FROM `tabChat Message` cm 
                    WHERE cm.chat_room = cr.name 
                    AND cm.timestamp > COALESCE(crm.last_read, '1900-01-01')
                    AND cm.sender != %(user)s
                    AND cm.is_deleted = 0
                ) as unread_count,
                (
                    SELECT CONCAT(
                        COALESCE(u.full_name, cm.sender), ': ', 
                        SUBSTRING(cm.message_content, 1, 50)
                    )
                    FROM `tabChat Message` cm
                    LEFT JOIN `tabUser` u ON cm.sender = u.name
                    WHERE cm.chat_room = cr.name 
                    AND cm.is_deleted = 0
                    ORDER BY cm.timestamp DESC 
                    LIMIT 1
                ) as last_message,
                (
                    SELECT cm.timestamp
                    FROM `tabChat Message` cm
                    WHERE cm.chat_room = cr.name 
                    AND cm.is_deleted = 0
                    ORDER BY cm.timestamp DESC 
                    LIMIT 1
                ) as last_message_time
            FROM `tabChat Room` cr
            INNER JOIN `tabChat Room Member` crm ON cr.name = crm.parent
            WHERE {where_clause}
            ORDER BY last_message_time DESC, cr.modified DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        values.update({"limit": page_size, "offset": offset})
        
        rooms = frappe.db.sql(query, values, as_dict=True)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT cr.name) as total
            FROM `tabChat Room` cr
            INNER JOIN `tabChat Room Member` crm ON cr.name = crm.parent
            WHERE {where_clause}
        """
        
        total_count = frappe.db.sql(count_query, values, as_dict=True)[0]["total"]
        
        return {
            "success": True,
            "data": {
                "rooms": rooms,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_user_chat_rooms_enhanced: {str(e)}")
        return {"success": False, "error": str(e)}
    


# vms/APIs/notification_chatroom/chat_apis/realtime_enhanced.py
# Additional event handlers and maintenance functions

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, get_datetime, time_diff_in_seconds
import json

# Event Handlers for real-time notifications

def handle_new_message_notification(doc, method):
    """
    Handle real-time notification when a new message is created
    
    Args:
        doc: Chat Message document
        method: Frappe event method
    """
    try:
        # Get room and sender information
        room = frappe.get_doc("Chat Room", doc.chat_room)
        sender_info = frappe.db.get_value("User", doc.sender, 
                                        ["full_name", "user_image"], as_dict=True)
        
        # Prepare notification data
        notification_data = {
            "message_id": doc.name,
            "room_id": doc.chat_room,
            "room_name": room.room_name,
            "room_type": room.room_type,
            "sender": doc.sender,
            "sender_name": sender_info.get("full_name") or doc.sender,
            "sender_image": sender_info.get("user_image"),
            "content": doc.message_content,
            "message_type": doc.message_type,
            "timestamp": str(doc.timestamp),
            "reply_to": doc.reply_to_message
        }
        
        # Get room members (excluding sender)
        room_members = [member.user for member in room.members if member.user != doc.sender]
        
        # Send real-time notification
        frappe.publish_realtime(
            event="chat_new_message",
            message=notification_data,
            user=room_members,
            room=f"chat_room_{doc.chat_room}"
        )
        
        # Send desktop notification
        frappe.publish_realtime(
            event="chat_desktop_notification",
            message=notification_data,
            user=room_members
        )
        
        # Update unread counts cache
        for member in room_members:
            cache_key = f"chat_unread_{member}"
            frappe.cache().delete_value(cache_key)
        
    except Exception as e:
        frappe.log_error(f"Error in handle_new_message_notification: {str(e)}")

def handle_message_update_notification(doc, method):
    """
    Handle real-time notification when a message is updated
    
    Args:
        doc: Chat Message document
        method: Frappe event method
    """
    try:
        if doc.has_value_changed("message_content") or doc.has_value_changed("is_deleted"):
            room = frappe.get_doc("Chat Room", doc.chat_room)
            room_members = [member.user for member in room.members]
            
            notification_data = {
                "message_id": doc.name,
                "room_id": doc.chat_room,
                "action": "deleted" if doc.is_deleted else "edited",
                "content": doc.message_content if not doc.is_deleted else None,
                "timestamp": str(now_datetime())
            }
            
            frappe.publish_realtime(
                event="chat_message_updated",
                message=notification_data,
                user=room_members,
                room=f"chat_room_{doc.chat_room}"
            )
            
    except Exception as e:
        frappe.log_error(f"Error in handle_message_update_notification: {str(e)}")

def handle_new_room_notification(doc, method):
    """
    Handle real-time notification when a new room is created
    
    Args:
        doc: Chat Room document
        method: Frappe event method
    """
    try:
        # Notify all members about new room
        room_members = [member.user for member in doc.members]
        
        notification_data = {
            "room_id": doc.name,
            "room_name": doc.room_name,
            "room_type": doc.room_type,
            "created_by": doc.created_by,
            "timestamp": str(doc.creation_date),
            "members": room_members
        }
        
        frappe.publish_realtime(
            event="chat_new_room",
            message=notification_data,
            user=room_members
        )
        
    except Exception as e:
        frappe.log_error(f"Error in handle_new_room_notification: {str(e)}")

def handle_room_update_notification(doc, method):
    """
    Handle real-time notification when a room is updated
    
    Args:
        doc: Chat Room document
        method: Frappe event method
    """
    try:
        # Check what changed
        changes = []
        if doc.has_value_changed("room_name"):
            changes.append("name")
        if doc.has_value_changed("description"):
            changes.append("description")
        if doc.has_value_changed("room_status"):
            changes.append("status")
        
        if changes:
            room_members = [member.user for member in doc.members]
            
            notification_data = {
                "room_id": doc.name,
                "changes": changes,
                "new_values": {
                    "room_name": doc.room_name,
                    "description": doc.description,
                    "room_status": doc.room_status
                },
                "timestamp": str(now_datetime())
            }
            
            frappe.publish_realtime(
                event="chat_room_updated",
                message=notification_data,
                user=room_members,
                room=f"chat_room_{doc.name}"
            )
            
    except Exception as e:
        frappe.log_error(f"Error in handle_room_update_notification: {str(e)}")

def handle_member_added_notification(doc, method):
    """
    Handle real-time notification when a member is added to a room
    
    Args:
        doc: Chat Room Member document
        method: Frappe event method
    """
    try:
        room = frappe.get_doc("Chat Room", doc.parent)
        user_info = frappe.db.get_value("User", doc.user, 
                                      ["full_name", "user_image"], as_dict=True)
        
        # Notify existing members
        existing_members = [member.user for member in room.members if member.user != doc.user]
        
        notification_data = {
            "room_id": doc.parent,
            "room_name": room.room_name,
            "action": "member_added",
            "user": doc.user,
            "user_name": user_info.get("full_name") or doc.user,
            "user_image": user_info.get("user_image"),
            "role": doc.role,
            "timestamp": str(now_datetime())
        }
        
        frappe.publish_realtime(
            event="chat_member_changed",
            message=notification_data,
            user=existing_members,
            room=f"chat_room_{doc.parent}"
        )
        
        # Notify the new member
        frappe.publish_realtime(
            event="chat_room_joined",
            message={
                "room_id": doc.parent,
                "room_name": room.room_name,
                "room_type": room.room_type,
                "role": doc.role,
                "timestamp": str(now_datetime())
            },
            user=[doc.user]
        )
        
    except Exception as e:
        frappe.log_error(f"Error in handle_member_added_notification: {str(e)}")

def handle_member_removed_notification(doc, method):
    """
    Handle real-time notification when a member is removed from a room
    
    Args:
        doc: Chat Room Member document
        method: Frappe event method
    """
    try:
        room = frappe.get_doc("Chat Room", doc.parent)
        user_info = frappe.db.get_value("User", doc.user, 
                                      ["full_name", "user_image"], as_dict=True)
        
        # Notify remaining members
        remaining_members = [member.user for member in room.members if member.user != doc.user]
        
        notification_data = {
            "room_id": doc.parent,
            "room_name": room.room_name,
            "action": "member_removed",
            "user": doc.user,
            "user_name": user_info.get("full_name") or doc.user,
            "timestamp": str(now_datetime())
        }
        
        frappe.publish_realtime(
            event="chat_member_changed",
            message=notification_data,
            user=remaining_members,
            room=f"chat_room_{doc.parent}"
        )
        
        # Notify the removed user
        frappe.publish_realtime(
            event="chat_room_left",
            message={
                "room_id": doc.parent,
                "room_name": room.room_name,
                "timestamp": str(now_datetime())
            },
            user=[doc.user]
        )
        
    except Exception as e:
        frappe.log_error(f"Error in handle_member_removed_notification: {str(e)}")

# Maintenance and cleanup functions

def cleanup_user_status_cache():
    """
    Daily cleanup of expired user status cache entries
    """
    try:
        # This would clean up old status entries
        # Implementation depends on your cache system
        print("🧹 Cleaning up user status cache entries...")
        
        # Get all users and check their status timestamps
        users = frappe.get_all("User", filters={"enabled": 1}, pluck="name")
        
        current_time = now_datetime()
        cleaned_count = 0
        
        for user in users:
            cache_key = f"chat_user_status_{user}"
            status_data = frappe.cache().get_value(cache_key)
            
            if status_data and status_data.get("last_seen"):
                last_seen = get_datetime(status_data["last_seen"])
                
                # Remove status if older than 24 hours
                if time_diff_in_seconds(current_time, last_seen) > 86400:  # 24 hours
                    frappe.cache().delete_value(cache_key)
                    cleaned_count += 1
        
        print(f"✅ Cleaned up {cleaned_count} expired user status entries")
        
    except Exception as e:
        frappe.log_error(f"Error in cleanup_user_status_cache: {str(e)}")

def update_user_activity_status():
    """
    Minute-wise update of user activity status
    """
    try:
        # Update activity for users who have been active in chat recently
        active_users_query = """
            SELECT DISTINCT sender as user
            FROM `tabChat Message`
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 15 MINUTE)
            AND sender != 'Administrator'
        """
        
        active_users = frappe.db.sql(active_users_query, as_dict=True)
        
        for user_data in active_users:
            user = user_data["user"]
            cache_key = f"chat_user_status_{user}"
            
            # Update last activity timestamp
            status_data = frappe.cache().get_value(cache_key) or {}
            status_data.update({
                "last_seen": str(now_datetime()),
                "status": status_data.get("status", "online"),
                "user": user
            })
            
            frappe.cache().set_value(cache_key, status_data, expires_in_sec=900)  # 15 minutes
        
    except Exception as e:
        frappe.log_error(f"Error in update_user_activity_status: {str(e)}")

# Additional utility functions for enhanced chat

@frappe.whitelist()
def get_online_users_in_room(room_id):
    """
    Get list of online users in a specific room
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: List of online users
    """
    try:
        # Get room members
        room = frappe.get_doc("Chat Room", room_id)
        members = [member.user for member in room.members]
        
        online_users = []
        for user in members:
            status = get_user_online_status(user)
            if status in ["online", "busy", "away"]:
                user_info = frappe.db.get_value("User", user, 
                                              ["full_name", "user_image"], as_dict=True)
                online_users.append({
                    "user": user,
                    "full_name": user_info.get("full_name") or user,
                    "user_image": user_info.get("user_image"),
                    "status": status
                })
        
        return {
            "success": True,
            "data": {
                "online_users": online_users,
                "total_online": len(online_users),
                "total_members": len(members)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_online_users_in_room: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def bulk_mark_rooms_as_read(room_ids):
    """
    Mark multiple rooms as read for the current user
    
    Args:
        room_ids (str): JSON string of room IDs
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        room_list = json.loads(room_ids) if isinstance(room_ids, str) else room_ids
        
        current_time = now_datetime()
        
        for room_id in room_list:
            # Update last read timestamp
            frappe.db.sql("""
                UPDATE `tabChat Room Member` 
                SET last_read = %s 
                WHERE parent = %s AND user = %s
            """, (current_time, room_id, current_user))
        
        # Clear cache
        cache_key = f"chat_unread_{current_user}"
        frappe.cache().delete_value(cache_key)
        
        return {
            "success": True,
            "message": f"Marked {len(room_list)} rooms as read"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in bulk_mark_rooms_as_read: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_chat_notification_settings():
    """
    Get user's chat notification preferences
    
    Returns:
        dict: Notification settings
    """
    try:
        current_user = frappe.session.user
        
        # Check if user has custom notification fields
        settings = {
            "desktop_notifications": True,
            "sound_notifications": True,
            "email_notifications": False,
            "mention_notifications": True
        }
        
        try:
            # Try to get from custom fields if they exist
            if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_notifications_enabled"}):
                settings["desktop_notifications"] = frappe.db.get_value("User", current_user, "custom_chat_notifications_enabled") or False
        except:
            pass
        
        return {
            "success": True,
            "data": settings
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_chat_notification_settings: {str(e)}")
        return {"success": False, "error": str(e)}