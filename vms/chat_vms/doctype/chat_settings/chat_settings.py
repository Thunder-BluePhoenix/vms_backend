# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

# vms/chat_vms/doctype/chat_settings/chat_settings.py

import frappe
from frappe.model.document import Document

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
        
        # Broadcast settings update to all connected clients
        if frappe.flags.in_request:
            frappe.publish_realtime(
                event="chat_settings_updated",
                message={
                    "max_file_size": self.max_file_size,
                    "allowed_file_types": self.allowed_file_types,
                    "enable_message_editing": self.enable_message_editing,
                    "enable_message_reactions": self.enable_message_reactions,
                    "enable_typing_indicators": self.enable_typing_indicators
                },
                user="all"
            )

@frappe.whitelist()
def get_chat_settings():
    """Get current chat settings"""
    settings = frappe.cache().get_value("chat_settings")
    
    if not settings:
        try:
            doc = frappe.get_single("Chat Settings")
            settings = {
                "max_file_size": doc.max_file_size or 10485760,
                "allowed_file_types": doc.allowed_file_types or "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx",
                "default_room_max_members": doc.default_room_max_members or 50,
                "enable_desktop_notifications": doc.enable_desktop_notifications,
                "auto_delete_old_messages": doc.auto_delete_old_messages,
                "enable_message_editing": doc.enable_message_editing,
                "message_edit_time_limit": doc.message_edit_time_limit or 24,
                "enable_message_reactions": doc.enable_message_reactions,
                "enable_typing_indicators": doc.enable_typing_indicators
            }
        except Exception:
            # Return default settings if DocType doesn't exist or has issues
            settings = {
                "max_file_size": 10485760,
                "allowed_file_types": "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx",
                "default_room_max_members": 50,
                "enable_desktop_notifications": 1,
                "auto_delete_old_messages": 0,
                "enable_message_editing": 1,
                "message_edit_time_limit": 24,
                "enable_message_reactions": 1,
                "enable_typing_indicators": 1
            }
        
        frappe.cache().set_value("chat_settings", settings, expires_in_sec=3600)
    
    return settings