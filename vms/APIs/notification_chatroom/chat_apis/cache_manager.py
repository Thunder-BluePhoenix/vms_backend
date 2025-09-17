# vms/APIs/notification_chatroom/chat_apis/cache_manager.py
# Cache management utility for chat status

import frappe
from frappe.utils import now_datetime, add_to_date
import json

@frappe.whitelist()
def cleanup_status_cache():
    """
    Clean up expired status cache entries
    Runs every 6 hours via cron
    """
    try:
        cache = frappe.cache()
        current_time = now_datetime()
        
        # Get all cache keys with the chat status prefix
        pattern = "chat_user_status_*"
        
        # Since frappe.cache doesn't have a direct pattern scan,
        # we'll track active users and clean their cache if expired
        active_users = frappe.db.sql("""
            SELECT name FROM `tabUser` 
            WHERE enabled = 1 
            AND user_type = 'System User'
        """, as_list=True)
        
        cleaned_count = 0
        for user_tuple in active_users:
            user = user_tuple[0]
            cache_key = f"chat_user_status_{user}"
            
            try:
                status_data = cache.get_value(cache_key)
                if status_data:
                    # Check if cache entry is expired
                    from frappe.utils import get_datetime, time_diff_in_seconds
                    last_seen = get_datetime(status_data.get("last_seen"))
                    
                    if time_diff_in_seconds(current_time, last_seen) > 3600:  # 1 hour old
                        cache.delete_value(cache_key)
                        cleaned_count += 1
                        
            except Exception as e:
                # If there's an error with a specific cache entry, just continue
                continue
        
        # Also clean up activity check cache
        try:
            activity_pattern_users = frappe.db.sql("""
                SELECT DISTINCT name FROM `tabUser` 
                WHERE enabled = 1 
                AND user_type = 'System User'
            """, as_list=True)
            
            for user_tuple in activity_pattern_users:
                user = user_tuple[0]
                activity_cache_key = f"chat_activity_check_{user}"
                
                # These expire automatically, but let's clean old ones
                try:
                    cache.delete_value(activity_cache_key)
                except:
                    pass
                    
        except Exception as e:
            frappe.log_error(f"Error cleaning activity cache: {str(e)}")
        
        return {
            "success": True,
            "cleaned_entries": cleaned_count,
            "timestamp": str(current_time)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in cleanup_status_cache: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_cache_statistics():
    """
    Get statistics about chat cache usage
    """
    try:
        active_users = frappe.db.sql("""
            SELECT name FROM `tabUser` 
            WHERE enabled = 1 
            AND user_type = 'System User'
        """, as_list=True)
        
        cache = frappe.cache()
        cached_users = 0
        total_users = len(active_users)
        cache_entries = []
        
        for user_tuple in active_users:
            user = user_tuple[0]
            cache_key = f"chat_user_status_{user}"
            
            try:
                status_data = cache.get_value(cache_key)
                if status_data:
                    cached_users += 1
                    cache_entries.append({
                        "user": user,
                        "status": status_data.get("status"),
                        "last_seen": status_data.get("last_seen"),
                        "source": status_data.get("source")
                    })
            except:
                continue
        
        return {
            "success": True,
            "statistics": {
                "total_users": total_users,
                "cached_users": cached_users,
                "cache_hit_rate": f"{(cached_users/total_users*100):.1f}%" if total_users > 0 else "0%",
                "timestamp": str(now_datetime())
            },
            "cache_entries": cache_entries[:10]  # Show first 10 for debugging
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting cache statistics: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def force_refresh_user_cache(user=None):
    """
    Force refresh a specific user's cache
    """
    try:
        if not user:
            user = frappe.session.user
            
        cache = frappe.cache()
        cache_key = f"chat_user_status_{user}"
        
        # Delete existing cache
        cache.delete_value(cache_key)
        
        # Create fresh cache entry
        from vms.APIs.notification_chatroom.chat_apis.status_manager import chat_status_manager
        result = chat_status_manager.update_user_status_safe(user, "online", "force_refresh")
        
        return {
            "success": True,
            "message": f"Cache refreshed for user {user}",
            "result": result
        }
        
    except Exception as e:
        frappe.log_error(f"Error force refreshing cache for user {user}: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def reset_all_user_statuses():
    """
    Emergency function to reset all user statuses
    Should only be used in case of major issues
    """
    try:
        if not frappe.has_permission("System Manager"):
            frappe.throw("Insufficient permissions")
            
        # Clear all status cache
        active_users = frappe.db.sql("""
            SELECT name FROM `tabUser` 
            WHERE enabled = 1 
            AND user_type = 'System User'
        """, as_list=True)
        
        cache = frappe.cache()
        cleared_cache = 0
        
        for user_tuple in active_users:
            user = user_tuple[0]
            cache_key = f"chat_user_status_{user}"
            try:
                cache.delete_value(cache_key)
                cleared_cache += 1
            except:
                continue
        
        # Reset database statuses
        updated_db = 0
        try:
            if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_status"}):
                frappe.db.sql("""
                    UPDATE `tabUser` 
                    SET custom_chat_status = 'offline'
                    WHERE enabled = 1 
                    AND user_type = 'System User'
                """)
                
                updated_db = frappe.db.sql("""
                    SELECT COUNT(*) FROM `tabUser` 
                    WHERE custom_chat_status = 'offline'
                    AND enabled = 1 
                    AND user_type = 'System User'
                """)[0][0]
                
                frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error updating database statuses: {str(e)}")
        
        return {
            "success": True,
            "message": "All user statuses reset successfully",
            "cache_cleared": cleared_cache,
            "database_updated": updated_db,
            "timestamp": str(now_datetime())
        }
        
    except Exception as e:
        frappe.log_error(f"Error resetting all user statuses: {str(e)}")
        return {"success": False, "error": str(e)}