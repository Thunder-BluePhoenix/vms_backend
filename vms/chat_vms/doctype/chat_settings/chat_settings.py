# vms/chat_vms/doctype/chat_settings/chat_settings.py
# Enhanced Chat Settings with Enable/Disable functionality

import frappe
from frappe.model.document import Document
from frappe import _

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
        
        # If chat is disabled, stop all chat-related processes
        if not self.enable_chat:
            self.disable_chat_functionality()
        else:
            self.enable_chat_functionality()
        
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
                    "enable_typing_indicators": self.enable_typing_indicators,
                    "enable_cron_monitoring": self.enable_cron_monitoring
                },
                user="all"
            )
    
    def disable_chat_functionality(self):
        """Disable chat functionality system-wide"""
        try:
            # Update all users' chat status to offline
            frappe.db.sql("""
                UPDATE `tabUser` 
                SET custom_chat_status = 'offline'
                WHERE custom_chat_status != 'offline'
            """)
            
            # Clear all chat-related caches
            keys_to_clear = frappe.cache().get_keys("chat_*")
            for key in keys_to_clear:
                frappe.cache().delete_value(key)
            
            frappe.db.commit()
            frappe.log_note("Chat functionality disabled")
            
        except Exception as e:
            frappe.log_error(f"Error disabling chat: {str(e)}")
    
    def enable_chat_functionality(self):
        """Re-enable chat functionality"""
        try:
            frappe.log_note("Chat functionality enabled")
        except Exception as e:
            frappe.log_error(f"Error enabling chat: {str(e)}")

@frappe.whitelist()
def get_chat_settings():
    """Get current chat settings"""
    settings = frappe.cache().get_value("chat_settings")
    
    if not settings:
        try:
            doc = frappe.get_single("Chat Settings")
            settings = {
                "enable_chat": doc.enable_chat if hasattr(doc, 'enable_chat') else True,
                "max_file_size": doc.max_file_size or 10485760,
                "allowed_file_types": doc.allowed_file_types or "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx",
                "default_room_max_members": doc.default_room_max_members or 50,
                "enable_desktop_notifications": doc.enable_desktop_notifications if hasattr(doc, 'enable_desktop_notifications') else True,
                "enable_message_editing": doc.enable_message_editing if hasattr(doc, 'enable_message_editing') else True,
                "message_edit_time_limit": doc.message_edit_time_limit or 24,
                "enable_message_reactions": doc.enable_message_reactions if hasattr(doc, 'enable_message_reactions') else True,
                "enable_typing_indicators": doc.enable_typing_indicators if hasattr(doc, 'enable_typing_indicators') else True,
                "auto_delete_old_messages": doc.auto_delete_old_messages if hasattr(doc, 'auto_delete_old_messages') else False,
                "enable_cron_monitoring": doc.enable_cron_monitoring if hasattr(doc, 'enable_cron_monitoring') else True
            }
            # Cache for 5 minutes
            frappe.cache().set_value("chat_settings", settings, expires_in_sec=300)
        except Exception as e:
            # Return default settings if none exist
            settings = {
                "enable_chat": True,
                "max_file_size": 10485760,
                "allowed_file_types": "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx",
                "default_room_max_members": 50,
                "enable_desktop_notifications": True,
                "enable_message_editing": True,
                "message_edit_time_limit": 24,
                "enable_message_reactions": True,
                "enable_typing_indicators": True,
                "auto_delete_old_messages": False,
                "enable_cron_monitoring": True
            }
    
    return settings

@frappe.whitelist()
def is_chat_enabled():
    """Check if chat is enabled"""
    settings = get_chat_settings()
    return settings.get("enable_chat", True)

@frappe.whitelist()
def get_cron_logs():
    """Get cron job logs for chat monitoring"""
    if not is_chat_enabled():
        return {"success": False, "message": "Chat is disabled"}
    
    settings = get_chat_settings()
    if not settings.get("enable_cron_monitoring", True):
        return {"success": False, "message": "Cron monitoring is disabled"}
    
    try:
        # Get recent scheduled job logs
        logs = frappe.db.sql("""
            SELECT 
                name,
                scheduled_job_type,
                status,
                creation,
                error
            FROM `tabScheduled Job Log`
            WHERE scheduled_job_type LIKE '%chat%'
                OR scheduled_job_type LIKE '%update_user_activity_status%'
                OR scheduled_job_type LIKE '%cleanup_old_messages%'
                OR scheduled_job_type LIKE '%update_room_statistics%'
            ORDER BY creation DESC
            LIMIT 50
        """, as_dict=True)
        
        return {
            "success": True,
            "data": logs
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting cron logs: {str(e)}")
        return {"success": False, "error": str(e)}