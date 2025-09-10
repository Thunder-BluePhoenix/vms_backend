# vms/APIs/notification_chatroom/chat_apis/maintenance.py
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

def update_user_online_status():
    """Update user online status based on last activity"""
    try:
        # Mark users as offline if they haven't been active in the last 5 minutes
        offline_threshold = frappe.utils.add_to_date(now_datetime(), minutes=-5)
        
        # This is a simple implementation - in production you might want more sophisticated tracking
        frappe.db.sql("""
            UPDATE `tabUser` 
            SET custom_chat_status = 'offline'
            WHERE last_active < %s AND custom_chat_status != 'offline'
        """, [offline_threshold])
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error updating user online status: {str(e)}")

def update_user_chat_permissions(doc, method=None):
    """Update chat permissions when user is updated"""
    try:
        if not doc.enabled:
            # Remove user from all chat rooms if disabled
            frappe.db.sql("""
                DELETE FROM `tabChat Room Member` 
                WHERE user = %s
            """, [doc.name])
            
            # Mark their messages as deleted
            frappe.db.sql("""
                UPDATE `tabChat Message`
                SET is_deleted = 1, delete_timestamp = %s, message_content = 'User account disabled'
                WHERE sender = %s AND is_deleted = 0
            """, [now_datetime(), doc.name])
            
            frappe.db.commit()
            
    except Exception as e:
        frappe.log_error(f"Error updating user chat permissions: {str(e)}")

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

@frappe.whitelist()
def get_chat_system_stats():
    """
    Get overall chat system statistics
    
    Returns:
        dict: System statistics
    """
    try:
        current_user = frappe.session.user
        
        # Only allow System Manager to view system stats
        if not frappe.has_permission("Chat Room", "report"):
            frappe.throw("You don't have permission to view system statistics")
        
        # Get overall statistics
        stats = frappe.db.sql("""
            SELECT 
                (SELECT COUNT(*) FROM `tabChat Room` WHERE room_status = 'Active') as active_rooms,
                (SELECT COUNT(*) FROM `tabChat Message` WHERE is_deleted = 0) as total_messages,
                (SELECT COUNT(DISTINCT sender) FROM `tabChat Message` WHERE is_deleted = 0) as active_users,
                (SELECT COUNT(*) FROM `tabChat Message Attachment`) as total_files,
                (SELECT SUM(COALESCE(file_size, 0)) FROM `tabChat Message Attachment`) as total_storage
        """, as_dict=True)[0]
        
        # Get messages by day for the last 30 days
        daily_stats = frappe.db.sql("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as message_count
            FROM `tabChat Message`
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                AND is_deleted = 0
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, as_dict=True)
        
        # Get room type distribution
        room_types = frappe.db.sql("""
            SELECT 
                room_type,
                COUNT(*) as count
            FROM `tabChat Room`
            WHERE room_status = 'Active'
            GROUP BY room_type
        """, as_dict=True)
        
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
                "overview": {
                    "active_rooms": stats.active_rooms,
                    "total_messages": stats.total_messages,
                    "active_users": stats.active_users,
                    "total_files": stats.total_files,
                    "total_storage": stats.total_storage,
                    "total_storage_formatted": format_file_size(stats.total_storage)
                },
                "daily_activity": daily_stats,
                "room_distribution": room_types
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_chat_system_stats: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def optimize_chat_database():
    """
    Optimize chat database tables for better performance
    
    Returns:
        dict: Optimization results
    """
    try:
        current_user = frappe.session.user
        
        # Only allow System Manager to optimize
        if not frappe.has_permission("Chat Room", "report"):
            frappe.throw("You don't have permission to optimize database")
        
        optimization_results = []
        
        # Optimize Chat Room table
        try:
            frappe.db.sql("OPTIMIZE TABLE `tabChat Room`")
            optimization_results.append("Chat Room table optimized")
        except Exception as e:
            optimization_results.append(f"Chat Room optimization failed: {str(e)}")
        
        # Optimize Chat Message table
        try:
            frappe.db.sql("OPTIMIZE TABLE `tabChat Message`")
            optimization_results.append("Chat Message table optimized")
        except Exception as e:
            optimization_results.append(f"Chat Message optimization failed: {str(e)}")
        
        # Optimize Chat Room Member table
        try:
            frappe.db.sql("OPTIMIZE TABLE `tabChat Room Member`")
            optimization_results.append("Chat Room Member table optimized")
        except Exception as e:
            optimization_results.append(f"Chat Room Member optimization failed: {str(e)}")
        
        # Add indexes if they don't exist
        try:
            # Index for chat room and timestamp
            frappe.db.sql("""
                ALTER TABLE `tabChat Message` 
                ADD INDEX IF NOT EXISTS idx_chat_room_timestamp (chat_room, timestamp)
            """)
            optimization_results.append("Added chat_room_timestamp index")
        except Exception as e:
            optimization_results.append(f"Index creation failed: {str(e)}")
        
        try:
            # Index for sender and timestamp
            frappe.db.sql("""
                ALTER TABLE `tabChat Message` 
                ADD INDEX IF NOT EXISTS idx_sender_timestamp (sender, timestamp)
            """)
            optimization_results.append("Added sender_timestamp index")
        except Exception as e:
            optimization_results.append(f"Sender index creation failed: {str(e)}")
        
        try:
            # Index for user and parent in Chat Room Member
            frappe.db.sql("""
                ALTER TABLE `tabChat Room Member` 
                ADD INDEX IF NOT EXISTS idx_user_parent (user, parent)
            """)
            optimization_results.append("Added user_parent index")
        except Exception as e:
            optimization_results.append(f"Member index creation failed: {str(e)}")
        
        frappe.db.commit()
        
        return {
            "success": True,
            "data": {
                "optimization_results": optimization_results
            },
            "message": "Database optimization completed"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in optimize_chat_database: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
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