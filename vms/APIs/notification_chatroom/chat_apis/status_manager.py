# vms/APIs/notification_chatroom/chat_apis/status_manager.py
# Enhanced status management with proper concurrency handling

import frappe
from frappe.utils import now_datetime, add_to_date, cint
from frappe.model.document import Document
import json
from typing import Dict, List, Optional

class ChatStatusManager:
    """
    Centralized chat status manager to handle all user status updates
    with proper concurrency control and error handling
    """
    
    def __init__(self):
        self.cache_prefix = "chat_user_status"
        self.cache_expiry = 600  # 10 minutes
        
    @frappe.whitelist()
    def update_user_status_safe(self, user=None, status="online", source="manual"):
        """
        Safely update user status with proper error handling and retry logic
        
        Args:
            user (str): User ID (defaults to current user)
            status (str): online, away, busy, offline
            source (str): Source of update (manual, cron, realtime)
            
        Returns:
            dict: Success response with status
        """
        try:
            if not user:
                user = frappe.session.user
                
            current_time = now_datetime()
            
            # Method 1: Cache-first approach (primary method)
            cache_success = self._update_status_cache(user, status, current_time, source)
            
            # Method 2: Database update with retry logic (secondary method)
            db_success = self._update_status_database_safe(user, status, current_time)
            
            # Notify other users about status change (only if manual update)
            if source == "manual" and (cache_success or db_success):
                self._broadcast_status_change(user, status, current_time)
            
            return {
                "success": True,
                "status": status,
                "timestamp": str(current_time),
                "cache_updated": cache_success,
                "database_updated": db_success,
                "source": source
            }
            
        except Exception as e:
            frappe.log_error(f"Error in update_user_status_safe: {str(e)}", "Chat Status Manager")
            return {
                "success": False,
                "error": str(e),
                "fallback_status": self.get_user_status_fallback(user)
            }
    
    def _update_status_cache(self, user, status, timestamp, source):
        """Update status in cache (always succeeds)"""
        try:
            cache_key = f"{self.cache_prefix}_{user}"
            status_data = {
                "status": status,
                "last_seen": str(timestamp),
                "user": user,
                "source": source,
                "updated_at": str(timestamp)
            }
            
            frappe.cache().set_value(cache_key, status_data, expires_in_sec=self.cache_expiry)
            return True
            
        except Exception as e:
            frappe.log_error(f"Cache update failed for user {user}: {str(e)}")
            return False
    
    def _update_status_database_safe(self, user, status, timestamp, max_retries=3):
        """
        Safely update database with retry logic and concurrency handling
        """
        for attempt in range(max_retries):
            try:
                # Check if custom fields exist before updating
                if not self._check_custom_fields():
                    return False
                
                # Use direct SQL update to avoid document locking issues
                affected_rows = frappe.db.sql("""
                    UPDATE `tabUser` 
                    SET 
                        custom_chat_status = %(status)s,
                        custom_last_chat_activity = %(timestamp)s
                    WHERE name = %(user)s
                    AND enabled = 1
                """, {
                    "status": status,
                    "timestamp": timestamp,
                    "user": user
                })
                
                frappe.db.commit()
                return True
                
            except frappe.exceptions.TimestampMismatchError:
                # Handle the specific timestamp mismatch error
                if attempt < max_retries - 1:
                    frappe.log_error(f"Timestamp mismatch for user {user}, retrying attempt {attempt + 1}")
                    # Wait a bit before retry
                    import time
                    time.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    frappe.log_error(f"Failed to update user {user} status after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                if "Unknown column" in str(e):
                    # Custom fields don't exist, this is acceptable
                    return False
                else:
                    frappe.log_error(f"Database update failed for user {user}: {str(e)}")
                    if attempt == max_retries - 1:
                        return False
                    continue
        
        return False
    
    def _check_custom_fields(self):
        """Check if required custom fields exist"""
        try:
            status_field_exists = frappe.db.exists("Custom Field", {
                "dt": "User", 
                "fieldname": "custom_chat_status"
            })
            activity_field_exists = frappe.db.exists("Custom Field", {
                "dt": "User", 
                "fieldname": "custom_last_chat_activity"
            })
            return status_field_exists and activity_field_exists
        except Exception:
            return False
    
    def _broadcast_status_change(self, user, status, timestamp):
        """Broadcast status change to other users"""
        try:
            frappe.publish_realtime(
                event="user_status_changed",
                message={
                    "user": user,
                    "status": status,
                    "timestamp": str(timestamp)
                },
                room="chat_global"
            )
        except Exception as e:
            frappe.log_error(f"Failed to broadcast status change: {str(e)}")
    
    @frappe.whitelist()
    def get_user_status(self, user=None):
        """
        Get user status with fallback mechanisms
        """
        try:
            if not user:
                user = frappe.session.user
                
            # Try cache first
            cache_key = f"{self.cache_prefix}_{user}"
            status_data = frappe.cache().get_value(cache_key)
            
            if status_data:
                # Check if status is still valid (not too old)
                from frappe.utils import get_datetime, time_diff_in_seconds
                last_seen = get_datetime(status_data.get("last_seen"))
                current_time = now_datetime()
                
                if time_diff_in_seconds(current_time, last_seen) <= self.cache_expiry:
                    return {
                        "status": status_data.get("status", "offline"),
                        "last_seen": status_data.get("last_seen"),
                        "source": "cache"
                    }
            
            # Fallback to database
            return self.get_user_status_fallback(user)
            
        except Exception as e:
            frappe.log_error(f"Error getting user status: {str(e)}")
            return {"status": "offline", "source": "error_fallback"}
    
    def get_user_status_fallback(self, user):
        """Fallback method to get user status from database or default"""
        try:
            if self._check_custom_fields():
                user_data = frappe.db.get_value("User", user, [
                    "custom_chat_status", 
                    "custom_last_chat_activity",
                    "last_active"
                ], as_dict=True)
                
                if user_data and user_data.get("custom_chat_status"):
                    return {
                        "status": user_data.get("custom_chat_status", "offline"),
                        "last_seen": str(user_data.get("custom_last_chat_activity") or user_data.get("last_active")),
                        "source": "database"
                    }
            
            # Ultimate fallback based on last_active
            last_active = frappe.db.get_value("User", user, "last_active")
            if last_active:
                from frappe.utils import time_diff_in_seconds
                diff_seconds = time_diff_in_seconds(now_datetime(), last_active)
                if diff_seconds < 300:  # 5 minutes
                    status = "online"
                elif diff_seconds < 900:  # 15 minutes
                    status = "away"
                else:
                    status = "offline"
            else:
                status = "offline"
                
            return {
                "status": status,
                "last_seen": str(last_active) if last_active else None,
                "source": "calculated"
            }
            
        except Exception as e:
            frappe.log_error(f"Fallback status check failed: {str(e)}")
            return {"status": "offline", "source": "error"}
    
    @frappe.whitelist()
    def bulk_update_user_statuses(self, status_threshold_minutes=5):
        """
        Safely update multiple user statuses in bulk
        Used by cron jobs to avoid individual document conflicts
        """
        try:
            current_time = now_datetime()
            offline_threshold = add_to_date(current_time, minutes=-status_threshold_minutes)
            
            if not self._check_custom_fields():
                return {"success": False, "error": "Custom fields not found"}
            
            # Update users to offline who haven't been active
            offline_result = frappe.db.sql("""
                UPDATE `tabUser` 
                SET custom_chat_status = 'offline'
                WHERE (
                    last_active < %(threshold)s 
                    OR last_active IS NULL
                )
                AND custom_chat_status != 'offline'
                AND enabled = 1
                AND user_type = 'System User'
            """, {"threshold": offline_threshold})
            
            # Update recently active users to online
            online_threshold = add_to_date(current_time, minutes=-2)
            online_result = frappe.db.sql("""
                UPDATE `tabUser` 
                SET custom_chat_status = 'online'
                WHERE last_active >= %(threshold)s 
                AND custom_chat_status != 'online'
                AND enabled = 1
                AND user_type = 'System User'
            """, {"threshold": online_threshold})
            
            frappe.db.commit()
            
            return {
                "success": True,
                "updated_offline": offline_result,
                "updated_online": online_result,
                "timestamp": str(current_time)
            }
            
        except Exception as e:
            frappe.log_error(f"Bulk status update failed: {str(e)}")
            return {"success": False, "error": str(e)}


# Global instance
chat_status_manager = ChatStatusManager()

# Exposed API methods
@frappe.whitelist()
def update_user_online_status(status="online"):
    """API wrapper for status updates"""
    return chat_status_manager.update_user_status_safe(
        user=frappe.session.user, 
        status=status, 
        source="manual"
    )

@frappe.whitelist()
def get_user_online_status(user=None):
    """API wrapper for getting status"""
    return chat_status_manager.get_user_status(user)

def update_user_statuses_cron():
    """Cron job function for bulk status updates"""
    return chat_status_manager.bulk_update_user_statuses()

# Enhanced error handling for existing APIs
@frappe.whitelist()
def get_user_chat_status_enhanced():
    """
    Enhanced version of get_user_chat_status with proper error handling
    """
    try:
        current_user = frappe.session.user
        
        # Get user status safely
        status_info = chat_status_manager.get_user_status(current_user)
        
        # Get unread counts safely
        unread_count = 0
        try:
            unread_result = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabChat Message` cm
                INNER JOIN `tabChat Room Member` crm ON cm.chat_room = crm.parent
                WHERE crm.user = %(user)s 
                AND cm.sender != %(user)s
                AND cm.timestamp > COALESCE(crm.last_read_timestamp, '1900-01-01')
                AND cm.is_deleted = 0
            """, {"user": current_user}, as_dict=True)
            
            if unread_result:
                unread_count = unread_result[0].get('count', 0)
                
        except Exception as e:
            frappe.log_error(f"Error getting unread count: {str(e)}")
        
        return {
            "success": True,
            "data": {
                "total_unread": unread_count,
                "online_status": status_info.get("status", "offline"),
                "last_seen": status_info.get("last_seen"),
                "timestamp": str(now_datetime()),
                "status_source": status_info.get("source", "unknown")
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_user_chat_status_enhanced: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "total_unread": 0,
                "online_status": "offline",
                "timestamp": str(now_datetime())
            }
        }