# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

# vms/chat_vms/doctype/chat_settings/chat_settings.py

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime
import json

class ChatSettings(Document):
    def validate(self):
        """Validate chat settings"""
        # Validate max file size
        if self.max_file_size and self.max_file_size <= 0:
            frappe.throw("Max file size must be greater than 0")
            
        # Validate message edit time limit
        if self.message_edit_time_limit and self.message_edit_time_limit < 0:
            frappe.throw("Message edit time limit cannot be negative")
            
        # Validate default room max members
        if self.default_room_max_members and self.default_room_max_members <= 0:
            frappe.throw("Default room max members must be greater than 0")

    def on_update(self):
        """Actions after updating chat settings"""
        # Clear cache to reflect new settings
        frappe.cache().delete_key("chat_settings")
        frappe.cache().delete_key("chat_enabled_status")
        
        # Update website context for chat enable/disable
        self.update_website_context()
        
        # Broadcast settings update to all connected clients
        if frappe.flags.in_request:
            frappe.publish_realtime(
                event="chat_settings_updated",
                message={
                    "enable_chat": self.enable_chat,
                    "max_file_size": self.max_file_size,
                    "allowed_file_types": self.allowed_file_types,
                    "enable_message_editing": self.enable_message_editing,
                    "enable_message_reactions": self.enable_message_reactions,
                    "enable_typing_indicators": self.enable_typing_indicators
                },
                user="all"
            )
        
        # Log the chat enable/disable action
        if hasattr(self, '_doc_before_save'):
            old_enable_status = self._doc_before_save.get('enable_chat', 0)
            new_enable_status = self.enable_chat
            
            if old_enable_status != new_enable_status:
                action = "enabled" if new_enable_status else "disabled"
                frappe.logger().info(f"Chat module {action} by {frappe.session.user}")
                
                # Create system notification for all users
                self.notify_users_chat_status_change(action)
    
    def before_save(self):
        """Store previous state for comparison"""
        if self.name and frappe.db.exists("Chat Settings", self.name):
            self._doc_before_save = frappe.db.get_value(
                "Chat Settings", self.name, 
                ["enable_chat", "enable_cron_monitoring"], 
                as_dict=True
            ) or {}
    
    def update_website_context(self):
        """Update website context for chat module status"""
        try:
            # Update the website context in hooks.py dynamically
            website_context = {
                "chat_enabled": bool(self.enable_chat),
                "max_file_size": self.max_file_size or 10485760,
                "supported_file_types": (self.allowed_file_types or "").split(",") if self.allowed_file_types else []
            }
            
            # Cache the chat enabled status for quick access
            frappe.cache().set_value("chat_enabled_status", bool(self.enable_chat), expires_in_sec=3600)
            
        except Exception as e:
            frappe.log_error(f"Error updating website context: {str(e)}")
    
    def notify_users_chat_status_change(self, action):
        """Notify all users about chat status change"""
        try:
            # Get all active users
            users = frappe.get_all("User", 
                                 filters={"enabled": 1, "user_type": "System User"}, 
                                 fields=["name"])
            
            message = f"Chat module has been {action}."
            
            for user in users:
                try:
                    # Create notification
                    notification = frappe.new_doc("Notification Log")
                    notification.for_user = user.name
                    notification.from_user = frappe.session.user
                    notification.subject = f"Chat Module {action.title()}"
                    notification.email_content = f"""
                        <div>
                            <h4>Chat Module Status Update</h4>
                            <p>{message}</p>
                            <p>This change was made by: {frappe.session.user}</p>
                            <p>Timestamp: {now_datetime()}</p>
                        </div>
                    """
                    notification.document_type = "Chat Settings"
                    notification.document_name = self.name
                    notification.type = "Alert"
                    notification.insert(ignore_permissions=True)
                    
                except Exception as e:
                    frappe.log_error(f"Error creating notification for user {user.name}: {str(e)}")
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error notifying users of chat status change: {str(e)}")
    
    def update_cron_status(self, status, error_message=None):
        """Update cron job status and logs"""
        try:
            self.cron_status = status
            self.cron_last_run_timestamp = now_datetime()
            
            if error_message:
                # Append new error to existing logs (keep last 10 errors)
                existing_logs = self.cron_error_logs or ""
                new_log = f"[{now_datetime()}] {error_message}\n"
                
                # Keep only last 10 error entries
                log_lines = (existing_logs + new_log).split('\n')
                if len(log_lines) > 10:
                    log_lines = log_lines[-10:]
                
                self.cron_error_logs = '\n'.join(log_lines)
            
            self.save(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error updating cron status: {str(e)}")

@frappe.whitelist()
def get_chat_settings():
    """Get current chat settings"""
    settings = frappe.cache().get_value("chat_settings")
    
    if not settings:
        try:
            doc = frappe.get_single("Chat Settings")
            settings = {
                "enable_chat": bool(doc.enable_chat),
                "max_file_size": doc.max_file_size or 10485760,
                "allowed_file_types": doc.allowed_file_types or "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx",
                "default_room_max_members": doc.default_room_max_members or 50,
                "enable_desktop_notifications": doc.enable_desktop_notifications,
                "auto_delete_old_messages": doc.auto_delete_old_messages,
                "enable_message_editing": doc.enable_message_editing,
                "message_edit_time_limit": doc.message_edit_time_limit or 24,
                "enable_message_reactions": doc.enable_message_reactions,
                "enable_typing_indicators": doc.enable_typing_indicators,
                "enable_cron_monitoring": doc.enable_cron_monitoring,
                "cron_status": doc.cron_status or "Unknown",
                "cron_last_run_timestamp": doc.cron_last_run_timestamp
            }
        except Exception:
            # Return default settings if DocType doesn't exist or has issues
            settings = {
                "enable_chat": True,  # Default to enabled
                "max_file_size": 10485760,
                "allowed_file_types": "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx",
                "default_room_max_members": 50,
                "enable_desktop_notifications": 1,
                "auto_delete_old_messages": 0,
                "enable_message_editing": 1,
                "message_edit_time_limit": 24,
                "enable_message_reactions": 1,
                "enable_typing_indicators": 1,
                "enable_cron_monitoring": 1,
                "cron_status": "Unknown",
                "cron_last_run_timestamp": None
            }
        
        frappe.cache().set_value("chat_settings", settings, expires_in_sec=3600)
    
    return settings

@frappe.whitelist()
def is_chat_enabled():
    """Quick check if chat is enabled"""
    try:
        # First check cache
        enabled_status = frappe.cache().get_value("chat_enabled_status")
        if enabled_status is not None:
            return bool(enabled_status)
        
        # If not in cache, get from database
        doc = frappe.get_single("Chat Settings")
        enabled = bool(doc.enable_chat)
        
        # Cache the result
        frappe.cache().set_value("chat_enabled_status", enabled, expires_in_sec=3600)
        
        return enabled
        
    except Exception:
        # Default to enabled if there's any error
        return True

@frappe.whitelist()
def get_cron_monitoring_status():
    """Get current cron monitoring status"""
    try:
        doc = frappe.get_single("Chat Settings")
        return {
            "enable_cron_monitoring": doc.enable_cron_monitoring,
            "cron_status": doc.cron_status or "Unknown",
            "cron_last_run_timestamp": doc.cron_last_run_timestamp,
            "cron_error_logs": doc.cron_error_logs
        }
    except Exception as e:
        frappe.log_error(f"Error getting cron monitoring status: {str(e)}")
        return {
            "enable_cron_monitoring": False,
            "cron_status": "Error",
            "cron_last_run_timestamp": None,
            "cron_error_logs": f"Error getting status: {str(e)}"
        }

@frappe.whitelist()
def update_cron_status_via_api(status, error_message=None):
    """API endpoint to update cron status from cron jobs"""
    try:
        doc = frappe.get_single("Chat Settings")
        doc.update_cron_status(status, error_message)
        
        return {
            "success": True,
            "message": f"Cron status updated to {status}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating cron status via API: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }