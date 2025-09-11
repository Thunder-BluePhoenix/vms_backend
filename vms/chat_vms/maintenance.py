# vms/APIs/notification_chatroom/chat_apis/maintenance.py
import frappe
import os
from frappe import _
from frappe.utils import now_datetime, add_days, cint, get_datetime
import json

def cleanup_old_messages():
    """
    Clean up old chat messages based on settings
    This function runs daily via scheduler
    """
    try:
        # Check if chat is enabled
        settings = frappe.get_single("Chat Settings")
        if not settings.enable_chat:
            frappe.logger().info("Chat is disabled, skipping cleanup")
            return
            
        if not settings.auto_delete_old_messages:
            return
            
        # Get deletion period (default 30 days)
        deletion_days = cint(settings.get("message_deletion_days", 30))
        cutoff_date = add_days(now_datetime(), -deletion_days)
        
        # Soft delete old messages
        deleted_count = frappe.db.sql("""
            UPDATE `tabChat Message`
            SET is_deleted = 1, 
                delete_timestamp = %(now)s,
                message_content = 'Message deleted due to retention policy'
            WHERE timestamp < %(cutoff)s 
                AND is_deleted = 0
        """, {
            "now": now_datetime(),
            "cutoff": cutoff_date
        })
        
        frappe.db.commit()
        
        if deleted_count:
            frappe.logger().info(f"Cleaned up {deleted_count} old chat messages")
            
    except Exception as e:
        frappe.log_error(f"Error in cleanup_old_messages: {str(e)}", "Chat Maintenance")


def update_room_statistics():
    """
    Update room statistics for better performance
    This function runs daily via scheduler
    """
    try:
        # Check if chat is enabled
        if not is_chat_enabled():
            return
            
        rooms = frappe.get_all("Chat Room", filters={"room_status": "Active"})
        
        for room in rooms:
            try:
                # Calculate message statistics with proper error handling
                stats = frappe.db.sql("""
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT sender) as unique_senders,
                        MAX(timestamp) as last_message_time
                    FROM `tabChat Message`
                    WHERE chat_room = %s AND is_deleted = 0
                """, (room.name,), as_dict=True)[0]
                
                # Log statistics
                frappe.logger().info(
                    f"Room {room.name}: {stats.total_messages} messages, "
                    f"{stats.unique_senders} unique senders, "
                    f"last message: {stats.last_message_time}"
                )
                
                # Update room document with stats if needed
                room_doc = frappe.get_doc("Chat Room", room.name)
                if hasattr(room_doc, 'message_count'):
                    room_doc.message_count = stats.total_messages
                    room_doc.save(ignore_permissions=True)
                    
            except Exception as e:
                frappe.log_error(f"Error updating stats for room {room.name}: {str(e)}", 
                               "Room Statistics Update")
                continue
            
    except Exception as e:
        frappe.log_error(f"Error in update_room_statistics: {str(e)}", "Chat Maintenance")

def cleanup_deleted_files():
    """
    Clean up orphaned chat files
    This function runs daily at 2 AM via scheduler
    """
    try:
        if not is_chat_enabled():
            return
            
        # Find files that are attached to deleted messages (with 7 days grace period)
        grace_period = add_days(now_datetime(), -7)
        
        orphaned_files = frappe.db.sql("""
            SELECT DISTINCT cma.file_url, f.name as file_name
            FROM `tabChat Message Attachment` cma
            LEFT JOIN `tabChat Message` cm ON cma.parent = cm.name
            LEFT JOIN `tabFile` f ON cma.file_url = f.file_url
            WHERE cm.is_deleted = 1 
                AND cm.delete_timestamp < %(grace_period)s
                AND f.name IS NOT NULL
        """, {"grace_period": grace_period}, as_dict=True)
        
        deleted_files_count = 0
        
        for file_info in orphaned_files:
            try:
                # Delete file document
                if frappe.db.exists("File", file_info.file_name):
                    file_doc = frappe.get_doc("File", file_info.file_name)
                    file_doc.delete()
                    deleted_files_count += 1
                    
            except Exception as e:
                frappe.log_error(f"Error deleting file {file_info.file_name}: {str(e)}", 
                               "File Cleanup")
                
        if deleted_files_count > 0:
            frappe.db.commit()
            frappe.logger().info(f"Cleaned up {deleted_files_count} orphaned chat files")
            
    except Exception as e:
        frappe.log_error(f"Error in cleanup_deleted_files: {str(e)}", "Chat Maintenance")

def update_user_online_status():
    """
    Update user online status based on last activity
    This function runs every 15 minutes via scheduler
    """
    try:
        if not is_chat_enabled():
            return
            
        # Mark users as offline if they haven't been active in the last 5 minutes
        offline_threshold = add_days(now_datetime(), minutes=-5)
        
        # Update with proper error handling
        try:
            updated = frappe.db.sql("""
                UPDATE `tabUser` 
                SET custom_chat_status = 'offline'
                WHERE custom_chat_status != 'offline'
                AND (
                    custom_last_chat_activity IS NULL 
                    OR custom_last_chat_activity < %(threshold)s
                )
            """, {"threshold": offline_threshold})
            
            frappe.db.commit()
            
            if updated:
                frappe.logger().info(f"Updated {updated} users to offline status")
                
        except Exception as e:
            # Handle cases where custom fields might not exist
            if "Unknown column" in str(e):
                frappe.logger().warning("Chat custom fields not found in User doctype")
            else:
                raise e
        
    except Exception as e:
        frappe.log_error(f"Error updating user online status: {str(e)}", "Chat Maintenance")

def update_user_chat_permissions(doc, method=None):
    """
    Update chat permissions when user is updated
    Hook function called on User update
    """
    try:
        if not is_chat_enabled():
            return
            
        if not doc.enabled:
            # Remove user from all chat rooms if disabled
            frappe.db.sql("""
                DELETE FROM `tabChat Room Member` 
                WHERE user = %s
            """, [doc.name])
            
            # Mark their messages as deleted
            frappe.db.sql("""
                UPDATE `tabChat Message`
                SET is_deleted = 1, 
                    delete_timestamp = %(now)s, 
                    message_content = 'User account disabled'
                WHERE sender = %(user)s AND is_deleted = 0
            """, {
                "now": now_datetime(),
                "user": doc.name
            })
            
            frappe.db.commit()
            frappe.logger().info(f"Cleaned up chat data for disabled user: {doc.name}")
            
    except Exception as e:
        frappe.log_error(f"Error updating chat permissions for user {doc.name}: {str(e)}", 
                       "Chat Permissions Update")

# Helper function to check if chat is enabled
def is_chat_enabled():
    """Check if chat is enabled in settings"""
    try:
        settings = frappe.get_single("Chat Settings")
        return settings.enable_chat if hasattr(settings, 'enable_chat') else True
    except:
        return True  # Default to enabled if settings don't exist
    





@frappe.whitelist()
def manual_cleanup_room(room_id):
    """Manually clean up a specific chat room"""
    try:
        if not frappe.has_permission("Chat Room", "delete"):
            frappe.throw(_("You don't have permission to clean up chat rooms"))
            
        room = frappe.get_doc("Chat Room", room_id)
        
        # Delete all messages in the room
        frappe.db.sql("""
            UPDATE `tabChat Message`
            SET is_deleted = 1,
                delete_timestamp = %(now)s,
                message_content = 'Room cleaned up by administrator'
            WHERE chat_room = %(room)s
        """, {
            "now": now_datetime(),
            "room": room_id
        })
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Room {room.room_name} cleaned up successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in manual_cleanup_room: {str(e)}", "Manual Cleanup")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_room_storage_usage(room_id):
    """
    Get storage usage statistics for a room
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: Storage usage data
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Get storage statistics
        storage_stats = frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT cm.name) as messages_with_files,
                COUNT(cma.name) as total_files,
                SUM(COALESCE(cma.file_size, 0)) as total_size,
                AVG(COALESCE(cma.file_size, 0)) as avg_file_size
            FROM `tabChat Message` cm
            LEFT JOIN `tabChat Message Attachment` cma ON cm.name = cma.parent
            WHERE cm.chat_room = %s 
                AND cm.is_deleted = 0
                AND cma.name IS NOT NULL
        """, (room_id,), as_dict=True)[0]
        
        # Get file types breakdown
        file_types = frappe.db.sql("""
            SELECT 
                cma.file_type,
                COUNT(*) as count,
                SUM(COALESCE(cma.file_size, 0)) as total_size
            FROM `tabChat Message` cm
            LEFT JOIN `tabChat Message Attachment` cma ON cm.name = cma.parent
            WHERE cm.chat_room = %s 
                AND cm.is_deleted = 0
                AND cma.name IS NOT NULL
            GROUP BY cma.file_type
            ORDER BY total_size DESC
        """, (room_id,), as_dict=True)
        
        # Format file size
        def format_file_size(size_bytes):
            if not size_bytes:
                return "0 B"
            size_bytes = int(size_bytes)
            if size_bytes == 0:
                return "0 B"
            size_name = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_name) - 1:
                size_bytes /= 1024.0
                i += 1
            return f"{size_bytes:.1f} {size_name[i]}"
            
        return {
            "success": True,
            "data": {
                "messages_with_files": storage_stats.messages_with_files or 0,
                "total_files": storage_stats.total_files or 0,
                "total_size": storage_stats.total_size or 0,
                "total_size_formatted": format_file_size(storage_stats.total_size or 0),
                "avg_file_size": storage_stats.avg_file_size or 0,
                "avg_file_size_formatted": format_file_size(storage_stats.avg_file_size or 0),
                "file_types": [
                    {
                        "file_type": ft.file_type,
                        "count": ft.count,
                        "total_size": ft.total_size,
                        "total_size_formatted": format_file_size(ft.total_size)
                    } for ft in file_types
                ]
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_room_storage_usage: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def get_chat_system_stats():
    """Get chat system statistics for monitoring"""
    try:
        if not frappe.has_permission("Chat Settings", "read"):
            frappe.throw(_("You don't have permission to view chat statistics"))
            
        stats = {
            "total_rooms": frappe.db.count("Chat Room", {"room_status": "Active"}),
            "total_messages": frappe.db.count("Chat Message", {"is_deleted": 0}),
            "total_users": frappe.db.sql("""
                SELECT COUNT(DISTINCT user) 
                FROM `tabChat Room Member`
            """)[0][0],
            "messages_today": frappe.db.sql("""
                SELECT COUNT(*) 
                FROM `tabChat Message` 
                WHERE DATE(timestamp) = CURDATE() 
                    AND is_deleted = 0
            """)[0][0],
            "active_users_today": frappe.db.sql("""
                SELECT COUNT(DISTINCT sender) 
                FROM `tabChat Message` 
                WHERE DATE(timestamp) = CURDATE()
            """)[0][0]
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting chat stats: {str(e)}", "Chat Statistics")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def optimize_chat_database():
    """Optimize chat database tables for better performance"""
    try:
        if not frappe.has_permission("System Manager"):
            frappe.throw(_("Only System Managers can optimize the database"))
            
        # Optimize tables
        tables = ["Chat Room", "Chat Message", "Chat Room Member"]
        
        for table in tables:
            frappe.db.sql(f"OPTIMIZE TABLE `tab{table}`")
            
        # Rebuild indexes
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Chat database optimized successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error optimizing database: {str(e)}", "Database Optimization")
        return {
            "success": False,
            "error": str(e)
        }
def validate_chat_permissions(room_id, user=None):
    """Validate user permissions for a chat room"""
    try:
        if not user:
            user = frappe.session.user
            
        # Check if user is member of the room
        is_member = frappe.db.exists(
            "Chat Room Member",
            {"parent": room_id, "user": user}
        )
        
        if not is_member:
            frappe.throw("You are not a member of this chat room")
            
        # Check if user is muted
        member_info = frappe.db.get_value(
            "Chat Room Member",
            {"parent": room_id, "user": user},
            ["is_muted", "role"],
            as_dict=True
        )
        
        if member_info and member_info.is_muted:
            frappe.throw("You are muted in this chat room")
            
        return {
            "is_member": True,
            "is_muted": member_info.is_muted if member_info else False,
            "role": member_info.role if member_info else "Member"
        }
        
    except Exception as e:
        frappe.log_error(f"Error validating chat permissions: {str(e)}")
        frappe.throw("Permission validation failed")

def moderate_message_content(content):
    """Basic content moderation for chat messages"""
    try:
        if not content:
            return True
            
        # Basic profanity filter (you can enhance this)
        inappropriate_words = [
            # Add your list of inappropriate words
            'spam', 'scam'  # Example words
        ]
        
        content_lower = content.lower()
        for word in inappropriate_words:
            if word in content_lower:
                frappe.log_error(f"Inappropriate content detected: {word}", "Chat Moderation")
                return False
                
        # Check message length
        if len(content) > 4000:
            return False
            
        return True
        
    except Exception as e:
        frappe.log_error(f"Error in content moderation: {str(e)}")
        return True  # Allow message if moderation fails