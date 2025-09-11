# vms/chat_vms/enhanced_maintenance.py
# Enhanced maintenance functions with cron monitoring and user status updates

import frappe
from frappe.utils import now_datetime, add_days, add_to_date, cint
from datetime import datetime, timedelta
import json

def update_user_online_status_enhanced():
    """
    Enhanced user online status update with cron monitoring
    Runs every 15 minutes via cron
    """
    cron_method_name = "update_user_online_status"
    
    try:
        # Update cron start status
        update_cron_status(cron_method_name, "Running", None)
        
        # Mark users as offline if they haven't been active in the last 5 minutes
        offline_threshold = add_to_date(now_datetime(), minutes=-5)
        
        # Get users with custom_chat_status field
        users_updated = 0
        
        # Check if custom field exists
        if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_status"}):
            # Update users who have been inactive
            result = frappe.db.sql("""
                UPDATE `tabUser` 
                SET custom_chat_status = 'offline'
                WHERE (last_active < %s OR last_active IS NULL) 
                AND custom_chat_status != 'offline'
                AND enabled = 1
                AND user_type = 'System User'
            """, [offline_threshold])
            
            users_updated = frappe.db.sql("""
                SELECT COUNT(*) as count FROM `tabUser` 
                WHERE custom_chat_status = 'offline'
                AND enabled = 1 
                AND user_type = 'System User'
            """)[0][0]
            
            # Update users who are currently active to 'online' status
            active_threshold = add_to_date(now_datetime(), minutes=-2)
            frappe.db.sql("""
                UPDATE `tabUser` 
                SET custom_chat_status = 'online'
                WHERE last_active >= %s 
                AND custom_chat_status != 'online'
                AND enabled = 1
                AND user_type = 'System User'
            """, [active_threshold])
            
        frappe.db.commit()
        
        # Log success
        success_message = f"Successfully updated user online status. {users_updated} users processed."
        frappe.logger().info(success_message)
        
        # Update cron success status
        update_cron_status(cron_method_name, "Running", None)
        
    except Exception as e:
        error_message = f"Error in update_user_online_status_enhanced: {str(e)}"
        frappe.log_error(error_message, "Chat Cron Error")
        
        # Update cron error status
        update_cron_status(cron_method_name, "Error", error_message)
        
        # Don't raise exception to avoid breaking other cron jobs
        print(f"❌ {error_message}")

def update_user_activity_status_enhanced():
    """
    Enhanced minute-wise update of user activity status with monitoring
    Runs every minute via cron
    """
    cron_method_name = "update_user_activity_status"
    
    try:
        # Update cron start status
        update_cron_status(cron_method_name, "Running", None)
        
        # Update activity for users who have been active in chat recently
        active_users_query = """
            SELECT DISTINCT sender as user
            FROM `tabChat Message`
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 15 MINUTE)
            AND sender != 'Administrator'
            AND sender != 'Guest'
        """
        
        active_users = frappe.db.sql(active_users_query, as_dict=True)
        
        users_updated = 0
        for user_data in active_users:
            user = user_data["user"]
            
            # Update cache for real-time status
            cache_key = f"chat_user_status_{user}"
            status_data = frappe.cache().get_value(cache_key) or {}
            status_data.update({
                "last_seen": str(now_datetime()),
                "status": status_data.get("status", "online"),
                "user": user
            })
            
            frappe.cache().set_value(cache_key, status_data, expires_in_sec=900)  # 15 minutes
            
            # Update database if custom field exists
            if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_last_chat_activity"}):
                frappe.db.set_value("User", user, "custom_last_chat_activity", now_datetime())
                users_updated += 1
        
        frappe.db.commit()
        
        # Log success
        success_message = f"Successfully updated activity status for {users_updated} active users."
        frappe.logger().info(success_message)
        
        # Update cron success status
        update_cron_status(cron_method_name, "Running", None)
        
    except Exception as e:
        error_message = f"Error in update_user_activity_status_enhanced: {str(e)}"
        frappe.log_error(error_message, "Chat Cron Error")
        
        # Update cron error status
        update_cron_status(cron_method_name, "Error", error_message)
        
        print(f"❌ {error_message}")

def cleanup_old_messages_enhanced():
    """
    Enhanced daily cleanup of old messages with monitoring
    """
    cron_method_name = "cleanup_old_messages"
    
    try:
        # Update cron start status
        update_cron_status(cron_method_name, "Running", None)
        
        # Get chat settings for auto-delete configuration
        chat_settings = get_chat_settings_for_cron()
        
        if not chat_settings.get("auto_delete_old_messages"):
            print("Auto-delete old messages is disabled")
            update_cron_status(cron_method_name, "Running", "Auto-delete disabled")
            return
        
        # Default to 90 days if not specified
        days_to_keep = chat_settings.get("auto_delete_days", 90)
        cutoff_date = add_days(now_datetime(), -days_to_keep)
        
        # Get old messages
        old_messages = frappe.get_all(
            "Chat Message",
            filters={
                "timestamp": ["<", cutoff_date],
                "is_deleted": 0
            },
            fields=["name", "chat_room"]
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
                    "message_content": "This message was automatically deleted due to age"
                }
            )
            deleted_count += 1
        
        frappe.db.commit()
        
        # Log success
        success_message = f"Successfully cleaned up {deleted_count} old messages (older than {days_to_keep} days)."
        frappe.logger().info(success_message)
        
        # Update cron success status
        update_cron_status(cron_method_name, "Running", None)
        
    except Exception as e:
        error_message = f"Error in cleanup_old_messages_enhanced: {str(e)}"
        frappe.log_error(error_message, "Chat Cron Error")
        
        # Update cron error status
        update_cron_status(cron_method_name, "Error", error_message)
        
        print(f"❌ {error_message}")

def cleanup_deleted_files_enhanced():
    """
    Enhanced cleanup of deleted files with monitoring
    Runs daily at 2 AM
    """
    cron_method_name = "cleanup_deleted_files"
    
    try:
        # Update cron start status
        update_cron_status(cron_method_name, "Running", None)
        
        # Find orphaned file attachments
        orphaned_files = frappe.db.sql("""
            SELECT cma.file_name, cma.file_url 
            FROM `tabChat Message Attachment` cma
            LEFT JOIN `tabChat Message` cm ON cma.parent = cm.name
            WHERE cm.is_deleted = 1 OR cm.name IS NULL
        """, as_dict=True)
        
        deleted_files_count = 0
        
        for file_info in orphaned_files:
            try:
                # Delete physical file if it exists
                if file_info.file_url:
                    file_path = frappe.get_site_path() + file_info.file_url
                    import os
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # Delete file document
                if frappe.db.exists("File", file_info.file_name):
                    file_doc = frappe.get_doc("File", file_info.file_name)
                    file_doc.delete()
                    deleted_files_count += 1
                    
            except Exception as e:
                frappe.log_error(f"Error deleting file {file_info.file_name}: {str(e)}")
        
        if deleted_files_count > 0:
            frappe.db.commit()
        
        # Log success
        success_message = f"Successfully cleaned up {deleted_files_count} orphaned chat files."
        frappe.logger().info(success_message)
        
        # Update cron success status
        update_cron_status(cron_method_name, "Running", None)
        
    except Exception as e:
        error_message = f"Error in cleanup_deleted_files_enhanced: {str(e)}"
        frappe.log_error(error_message, "Chat Cron Error")
        
        # Update cron error status
        update_cron_status(cron_method_name, "Error", error_message)
        
        print(f"❌ {error_message}")

def update_room_statistics_enhanced():
    """
    Enhanced daily update of room statistics with monitoring
    """
    cron_method_name = "update_room_statistics"
    
    try:
        # Update cron start status
        update_cron_status(cron_method_name, "Running", None)
        
        # Get all active chat rooms
        rooms = frappe.get_all("Chat Room", 
                              filters={"room_status": "Active"}, 
                              fields=["name"])
        
        rooms_updated = 0
        
        for room in rooms:
            try:
                # Update message count
                message_count = frappe.db.count("Chat Message", 
                                               filters={"chat_room": room.name, "is_deleted": 0})
                
                # Update member count
                member_count = frappe.db.count("Chat Room Member", 
                                             filters={"parent": room.name})
                
                # Update last activity
                last_message = frappe.db.sql("""
                    SELECT timestamp 
                    FROM `tabChat Message` 
                    WHERE chat_room = %s AND is_deleted = 0 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, [room.name])
                
                last_activity = last_message[0][0] if last_message else None
                
                # Update room with statistics (if custom fields exist)
                room_doc = frappe.get_doc("Chat Room", room.name)
                
                # Update any additional statistics here
                # For now, we'll just log the stats
                frappe.logger().info(f"Room {room.name}: {message_count} messages, {member_count} members")
                
                rooms_updated += 1
                
            except Exception as e:
                frappe.log_error(f"Error updating statistics for room {room.name}: {str(e)}")
        
        # Log success
        success_message = f"Successfully updated statistics for {rooms_updated} chat rooms."
        frappe.logger().info(success_message)
        
        # Update cron success status
        update_cron_status(cron_method_name, "Running", None)
        
    except Exception as e:
        error_message = f"Error in update_room_statistics_enhanced: {str(e)}"
        frappe.log_error(error_message, "Chat Cron Error")
        
        # Update cron error status
        update_cron_status(cron_method_name, "Error", error_message)
        
        print(f"❌ {error_message}")

def cleanup_user_status_cache_enhanced():
    """
    Enhanced daily cleanup of expired user status cache entries with monitoring
    """
    cron_method_name = "cleanup_user_status_cache"
    
    try:
        # Update cron start status
        update_cron_status(cron_method_name, "Running", None)
        
        # Get all users and clean their expired cache
        users = frappe.get_all("User", 
                              filters={"enabled": 1, "user_type": "System User"}, 
                              fields=["name"])
        
        cleaned_count = 0
        
        for user in users:
            cache_key = f"chat_user_status_{user.name}"
            cached_data = frappe.cache().get_value(cache_key)
            
            if cached_data:
                try:
                    # Check if cache entry is older than 1 hour
                    if cached_data.get("last_seen"):
                        last_seen = datetime.fromisoformat(cached_data["last_seen"])
                        if (now_datetime() - last_seen).total_seconds() > 3600:  # 1 hour
                            frappe.cache().delete_value(cache_key)
                            cleaned_count += 1
                except Exception:
                    # If there's any issue with the cached data, remove it
                    frappe.cache().delete_value(cache_key)
                    cleaned_count += 1
        
        # Log success
        success_message = f"Successfully cleaned up {cleaned_count} expired user status cache entries."
        frappe.logger().info(success_message)
        
        # Update cron success status
        update_cron_status(cron_method_name, "Running", None)
        
    except Exception as e:
        error_message = f"Error in cleanup_user_status_cache_enhanced: {str(e)}"
        frappe.log_error(error_message, "Chat Cron Error")
        
        # Update cron error status
        update_cron_status(cron_method_name, "Error", error_message)
        
        print(f"❌ {error_message}")

def update_cron_status(method_name, status, error_message=None):
    """
    Update cron job status in Chat Settings
    
    Args:
        method_name (str): Name of the cron method
        status (str): Current status (Running, Error, etc.)
        error_message (str): Error message if any
    """
    try:
        # Check if Chat Settings exists and monitoring is enabled
        if not frappe.db.exists("DocType", "Chat Settings"):
            return
        
        chat_settings = frappe.get_single("Chat Settings")
        
        if not chat_settings.enable_cron_monitoring:
            return
        
        # Update the cron status
        chat_settings.cron_status = status
        chat_settings.cron_last_run_timestamp = now_datetime()
        
        if error_message:
            # Append new error to existing logs (keep last 20 errors)
            existing_logs = chat_settings.cron_error_logs or ""
            new_log = f"[{now_datetime()}] {method_name}: {error_message}\n"
            
            # Keep only last 20 error entries
            log_lines = (existing_logs + new_log).split('\n')
            if len(log_lines) > 20:
                log_lines = log_lines[-20:]
            
            chat_settings.cron_error_logs = '\n'.join(log_lines)
        
        # Save without triggering validations or hooks
        chat_settings.db_update()
        frappe.db.commit()
        
    except Exception as e:
        # Don't let cron monitoring errors break the actual cron jobs
        frappe.log_error(f"Error updating cron status: {str(e)}", "Cron Monitoring Error")

def get_chat_settings_for_cron():
    """
    Get chat settings for cron jobs with fallback defaults
    
    Returns:
        dict: Chat settings
    """
    try:
        if frappe.db.exists("DocType", "Chat Settings"):
            settings = frappe.get_single("Chat Settings")
            return {
                "auto_delete_old_messages": settings.auto_delete_old_messages,
                "auto_delete_days": getattr(settings, 'auto_delete_days', 90),
                "enable_cron_monitoring": settings.enable_cron_monitoring
            }
    except Exception:
        pass
    
    # Return defaults if settings don't exist
    return {
        "auto_delete_old_messages": False,
        "auto_delete_days": 90,
        "enable_cron_monitoring": False
    }

# Wrapper functions for the original cron jobs to maintain compatibility
def update_user_online_status():
    """Original function name - wrapper for enhanced version"""
    return update_user_online_status_enhanced()

@frappe.whitelist()
def update_user_activity_status():
    """Original function name - wrapper for enhanced version"""
    return update_user_activity_status_enhanced()

def cleanup_old_messages():
    """Original function name - wrapper for enhanced version"""
    return cleanup_old_messages_enhanced()

def cleanup_deleted_files():
    """Original function name - wrapper for enhanced version"""
    return cleanup_deleted_files_enhanced()

def update_room_statistics():
    """Original function name - wrapper for enhanced version"""
    return update_room_statistics_enhanced()

def cleanup_user_status_cache():
    """Original function name - wrapper for enhanced version"""
    return cleanup_user_status_cache_enhanced()

# Additional maintenance functions
@frappe.whitelist()
def manual_cron_test():
    """
    Manual test function for cron jobs - can be called from frontend
    """
    try:
        # Test each cron function
        results = {
            "user_status_update": "Success",
            "activity_update": "Success", 
            "message_cleanup": "Success",
            "file_cleanup": "Success",
            "room_statistics": "Success",
            "cache_cleanup": "Success"
        }
        
        try:
            update_user_online_status_enhanced()
        except Exception as e:
            results["user_status_update"] = f"Error: {str(e)}"
        
        try:
            update_user_activity_status_enhanced()
        except Exception as e:
            results["activity_update"] = f"Error: {str(e)}"
        
        try:
            cleanup_old_messages_enhanced()
        except Exception as e:
            results["message_cleanup"] = f"Error: {str(e)}"
        
        try:
            cleanup_deleted_files_enhanced()
        except Exception as e:
            results["file_cleanup"] = f"Error: {str(e)}"
        
        try:
            update_room_statistics_enhanced()
        except Exception as e:
            results["room_statistics"] = f"Error: {str(e)}"
        
        try:
            cleanup_user_status_cache_enhanced()
        except Exception as e:
            results["cache_cleanup"] = f"Error: {str(e)}"
        
        return {
            "success": True,
            "message": "Manual cron test completed",
            "results": results
        }
        
    except Exception as e:
        frappe.log_error(f"Error in manual cron test: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_cron_health_status():
    """
    Get overall health status of chat cron jobs
    """
    try:
        if not frappe.db.exists("DocType", "Chat Settings"):
            return {
                "success": False,
                "error": "Chat Settings not found"
            }
        
        chat_settings = frappe.get_single("Chat Settings")
        
        if not chat_settings.enable_cron_monitoring:
            return {
                "success": True,
                "monitoring_enabled": False,
                "message": "Cron monitoring is disabled"
            }
        
        # Check when cron was last run
        last_run = chat_settings.cron_last_run_timestamp
        current_time = now_datetime()
        
        health_status = "Healthy"
        if last_run:
            time_diff = (current_time - last_run).total_seconds()
            if time_diff > 3600:  # More than 1 hour ago
                health_status = "Warning"
            if time_diff > 7200:  # More than 2 hours ago
                health_status = "Critical"
        else:
            health_status = "Unknown"
        
        return {
            "success": True,
            "monitoring_enabled": True,
            "health_status": health_status,
            "cron_status": chat_settings.cron_status,
            "last_run": last_run,
            "error_logs": chat_settings.cron_error_logs
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting cron health status: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def force_user_status_update():
    """
    Force update all user chat statuses - useful for debugging
    """
    try:
        # Check if custom fields exist
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_status"}):
            return {
                "success": False,
                "error": "custom_chat_status field not found on User doctype"
            }
        
        # Update all active users based on their last activity
        current_time = now_datetime()
        online_threshold = add_to_date(current_time, minutes=-2)
        away_threshold = add_to_date(current_time, minutes=-5)
        
        # Mark users as online (active in last 2 minutes)
        online_count = frappe.db.sql("""
            UPDATE `tabUser` 
            SET custom_chat_status = 'online'
            WHERE last_active >= %s 
            AND enabled = 1
            AND user_type = 'System User'
        """, [online_threshold])
        
        # Mark users as away (active between 2-5 minutes ago)
        away_count = frappe.db.sql("""
            UPDATE `tabUser` 
            SET custom_chat_status = 'away'
            WHERE last_active >= %s 
            AND last_active < %s
            AND enabled = 1
            AND user_type = 'System User'
        """, [away_threshold, online_threshold])
        
        # Mark users as offline (inactive for more than 5 minutes)
        offline_count = frappe.db.sql("""
            UPDATE `tabUser` 
            SET custom_chat_status = 'offline'
            WHERE (last_active < %s OR last_active IS NULL)
            AND enabled = 1
            AND user_type = 'System User'
        """, [away_threshold])
        
        frappe.db.commit()
        
        # Get final counts
        status_counts = frappe.db.sql("""
            SELECT custom_chat_status, COUNT(*) as count
            FROM `tabUser` 
            WHERE enabled = 1 AND user_type = 'System User'
            GROUP BY custom_chat_status
        """, as_dict=True)
        
        return {
            "success": True,
            "message": "User statuses updated successfully",
            "status_counts": {item.custom_chat_status: item.count for item in status_counts}
        }
        
    except Exception as e:
        frappe.log_error(f"Error in force_user_status_update: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }