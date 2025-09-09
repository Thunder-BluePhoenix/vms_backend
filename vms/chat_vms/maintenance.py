# vms/chat_vms/maintenance.py
import frappe
from frappe.utils import now_datetime, add_days, get_datetime
import os

def cleanup_old_messages():
    """
    Clean up old messages based on room settings
    This function runs daily via scheduler
    """
    try:
        # Get rooms with auto-delete settings
        rooms_with_auto_delete = frappe.get_all(
            "Chat Room",
            filters={
                "auto_delete_messages_after_days": [">", 0],
                "room_status": "Active"
            },
            fields=["name", "auto_delete_messages_after_days"]
        )
        
        deleted_count = 0
        
        for room in rooms_with_auto_delete:
            # Calculate cutoff date
            cutoff_date = add_days(now_datetime(), -room.auto_delete_messages_after_days)
            
            # Get old messages
            old_messages = frappe.get_all(
                "Chat Message",
                filters={
                    "chat_room": room.name,
                    "timestamp": ["<", cutoff_date],
                    "is_deleted": 0
                },
                fields=["name"]
            )
            
            # Soft delete old messages
            for message in old_messages:
                frappe.db.set_value(
                    "Chat Message",
                    message.name,
                    {
                        "is_deleted": 1,
                        "delete_timestamp": now_datetime(),
                        "message_content": "This message was automatically deleted"
                    }
                )
                deleted_count += 1
                
        if deleted_count > 0:
            frappe.db.commit()
            frappe.logger().info(f"Auto-deleted {deleted_count} old chat messages")
            
    except Exception as e:
        frappe.log_error(f"Error in cleanup_old_messages: {str(e)}")

def update_room_statistics():
    """
    Update room statistics for better performance
    This function runs daily via scheduler
    """
    try:
        rooms = frappe.get_all("Chat Room", filters={"room_status": "Active"})
        
        for room in rooms:
            # Calculate message statistics
            stats = frappe.db.sql("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT sender) as unique_senders,
                    MAX(timestamp) as last_message_time
                FROM `tabChat Message`
                WHERE chat_room = %s AND is_deleted = 0
            """, (room.name,), as_dict=True)[0]
            
            # Update room with statistics (you might want to add custom fields for this)
            # For now, we'll just log the statistics
            frappe.logger().info(
                f"Room {room.name}: {stats.total_messages} messages, "
                f"{stats.unique_senders} unique senders, "
                f"last message: {stats.last_message_time}"
            )
            
    except Exception as e:
        frappe.log_error(f"Error in update_room_statistics: {str(e)}")

def cleanup_deleted_files():
    """
    Clean up orphaned chat files
    This function runs daily via scheduler
    """
    try:
        # Find files that are attached to deleted messages
        orphaned_files = frappe.db.sql("""
            SELECT DISTINCT cma.file_url, f.name as file_name
            FROM `tabChat Message Attachment` cma
            LEFT JOIN `tabChat Message` cm ON cma.parent = cm.name
            LEFT JOIN `tabFile` f ON cma.file_url = f.file_url
            WHERE cm.is_deleted = 1 
                AND cm.delete_timestamp < %s
                AND f.name IS NOT NULL
        """, (add_days(now_datetime(), -7),), as_dict=True)  # 7 days grace period
        
        deleted_files_count = 0
        
        for file_info in orphaned_files:
            try:
                # Delete file document
                if frappe.db.exists("File", file_info.file_name):
                    file_doc = frappe.get_doc("File", file_info.file_name)
                    file_doc.delete()
                    deleted_files_count += 1
                    
            except Exception as e:
                frappe.log_error(f"Error deleting file {file_info.file_name}: {str(e)}")
                
        if deleted_files_count > 0:
            frappe.db.commit()
            frappe.logger().info(f"Cleaned up {deleted_files_count} orphaned chat files")
            
    except Exception as e:
        frappe.log_error(f"Error in cleanup_deleted_files: {str(e)}")

@frappe.whitelist()
def manual_cleanup_room(room_id, days_old=30):
    """
    Manually cleanup messages older than specified days for a room
    
    Args:
        room_id (str): Chat room ID
        days_old (int): Delete messages older than this many days
        
    Returns:
        dict: Cleanup results
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is admin of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_admin"]:
            frappe.throw("Only admins can perform manual cleanup")
            
        # Calculate cutoff date
        cutoff_date = add_days(now_datetime(), -int(days_old))
        
        # Get old messages
        old_messages = frappe.get_all(
            "Chat Message",
            filters={
                "chat_room": room_id,
                "timestamp": ["<", cutoff_date],
                "is_deleted": 0
            },
            fields=["name"]
        )
        
        # Soft delete old messages
        deleted_count = 0
        for message in old_messages:
            frappe.db.set_value(
                "Chat Message",
                message.name,
                {
                    "is_deleted": 1,
                    "delete_timestamp": now_datetime(),
                    "message_content": "This message was manually deleted"
                }
            )
            deleted_count += 1
            
        frappe.db.commit()
        
        # Create system message
        room.create_system_message(f"Manual cleanup completed. {deleted_count} old messages removed.")
        
        return {
            "success": True,
            "data": {
                "deleted_count": deleted_count,
                "cutoff_date": str(cutoff_date)
            },
            "message": f"Successfully deleted {deleted_count} old messages"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in manual_cleanup_room: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
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