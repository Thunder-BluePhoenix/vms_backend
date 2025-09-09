# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class ChatMessage(Document):
    def validate(self):
        self.validate_sender_permissions()
        self.validate_message_content()
        
    def before_save(self):
        if not self.timestamp:
            self.timestamp = now_datetime()
            
    def validate_sender_permissions(self):
        """Validate that sender has permission to send message in this room"""
        if not self.chat_room or not self.sender:
            return
            
        room = frappe.get_doc("Chat Room", self.chat_room)
        permissions = room.get_member_permissions(self.sender)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        if permissions.get("is_muted"):
            frappe.throw("You are muted in this chat room")
            
    def validate_message_content(self):
        """Validate message content based on type"""
        if self.message_type == "Text" and not self.message_content:
            frappe.throw("Text message cannot be empty")
            
        if self.message_type in ["File", "Image"] and not self.file_attachments:
            frappe.throw(f"{self.message_type} message must have attachments")
            
    def after_insert(self):
        """Actions after message is inserted"""
        self.send_real_time_notification()
        
    def send_real_time_notification(self):
        """Send real-time notification to room members"""
        room = frappe.get_doc("Chat Room", self.chat_room)
        
        # Get all room members except sender
        recipients = [member.user for member in room.members if member.user != self.sender]
        
        # Prepare message data
        message_data = {
            "message_id": self.name,
            "chat_room": self.chat_room,
            "sender": self.sender,
            "message_type": self.message_type,
            "content": self.message_content,
            "timestamp": str(self.timestamp),
            "attachments": [
                {
                    "file_name": att.file_name,
                    "file_url": att.file_url,
                    "file_type": att.file_type
                } for att in self.file_attachments
            ]
        }
        
        # Send real-time notification
        frappe.publish_realtime(
            event="new_chat_message",
            message=message_data,
            user=recipients,
            room=f"chat_room_{self.chat_room}"
        )
        
    def add_reaction(self, user_id, emoji):
        """Add reaction to message"""
        # Check if user already reacted with this emoji
        existing_reaction = None
        for reaction in self.reactions:
            if reaction.user == user_id and reaction.reaction_emoji == emoji:
                existing_reaction = reaction
                break
                
        if existing_reaction:
            # Remove existing reaction
            self.reactions.remove(existing_reaction)
        else:
            # Add new reaction
            self.append("reactions", {
                "user": user_id,
                "reaction_emoji": emoji,
                "timestamp": now_datetime()
            })
            
        self.save(ignore_permissions=True)
        
        # Send real-time notification for reaction update
        self.send_reaction_notification()
        
    def send_reaction_notification(self):
        """Send real-time notification for reaction updates"""
        room = frappe.get_doc("Chat Room", self.chat_room)
        recipients = [member.user for member in room.members]
        
        # Group reactions by emoji
        reaction_summary = {}
        for reaction in self.reactions:
            emoji = reaction.reaction_emoji
            if emoji not in reaction_summary:
                reaction_summary[emoji] = {"count": 0, "users": []}
            reaction_summary[emoji]["count"] += 1
            reaction_summary[emoji]["users"].append(reaction.user)
            
        frappe.publish_realtime(
            event="message_reaction_update",
            message={
                "message_id": self.name,
                "reactions": reaction_summary
            },
            user=recipients,
            room=f"chat_room_{self.chat_room}"
        )
        
    def edit_message(self, new_content, user_id):
        """Edit message content"""
        if self.sender != user_id:
            frappe.throw("You can only edit your own messages")
            
        if self.message_type != "Text":
            frappe.throw("Only text messages can be edited")
            
        # Check if message is too old (24 hours)
        from frappe.utils import get_datetime, time_diff_in_hours
        if time_diff_in_hours(now_datetime(), get_datetime(self.timestamp)) > 24:
            frappe.throw("Messages older than 24 hours cannot be edited")
            
        self.message_content = new_content
        self.is_edited = 1
        self.edit_timestamp = now_datetime()
        self.save(ignore_permissions=True)
        
        # Send real-time notification for edit
        self.send_edit_notification()
        
    def send_edit_notification(self):
        """Send real-time notification for message edit"""
        room = frappe.get_doc("Chat Room", self.chat_room)
        recipients = [member.user for member in room.members]
        
        frappe.publish_realtime(
            event="message_edited",
            message={
                "message_id": self.name,
                "new_content": self.message_content,
                "edit_timestamp": str(self.edit_timestamp)
            },
            user=recipients,
            room=f"chat_room_{self.chat_room}"
        )
        
    def delete_message(self, user_id):
        """Soft delete message"""
        if self.sender != user_id:
            # Check if user is admin
            room = frappe.get_doc("Chat Room", self.chat_room)
            permissions = room.get_member_permissions(user_id)
            if not permissions.get("is_admin"):
                frappe.throw("You can only delete your own messages or you must be an admin")
                
        self.is_deleted = 1
        self.delete_timestamp = now_datetime()
        self.message_content = "This message was deleted"
        self.save(ignore_permissions=True)
        
        # Send real-time notification for deletion
        room = frappe.get_doc("Chat Room", self.chat_room)
        recipients = [member.user for member in room.members]
        
        frappe.publish_realtime(
            event="message_deleted",
            message={
                "message_id": self.name,
                "delete_timestamp": str(self.delete_timestamp)
            },
            user=recipients,
            room=f"chat_room_{self.chat_room}"
        )
