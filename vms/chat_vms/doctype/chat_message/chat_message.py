# vms/chat_vms/doctype/chat_message/chat_message.py
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

    def after_insert_hook(self, method=None):
        """Hook method called after message is inserted"""
        try:
            # Send real-time notification
            self.send_real_time_notification()
            
            # Update room's last activity
            self.update_room_last_activity()
            
            # Send push notifications to offline users
            self.send_push_notifications()
            
        except Exception as e:
            frappe.log_error(f"Error in chat message after_insert_hook: {str(e)}")

    def before_save_hook(self, method=None):
        """Hook method called before message is saved"""
        try:
            # Set timestamp if not provided
            if not self.timestamp:
                self.timestamp = now_datetime()
                
            # Validate message length
            if self.message_content and len(self.message_content) > 4000:
                frappe.throw("Message content cannot exceed 4000 characters")
                
            # Auto-detect and validate URLs in message
            self.process_message_content()
            
        except Exception as e:
            frappe.log_error(f"Error in chat message before_save_hook: {str(e)}")

    def on_trash(self):
        """Handle message deletion"""
        try:
            # Soft delete instead of hard delete
            self.is_deleted = 1
            self.delete_timestamp = now_datetime()
            self.message_content = "This message was deleted"
            
            # Don't actually delete the document, just mark as deleted
            frappe.db.sql("""
                UPDATE `tabChat Message`
                SET is_deleted = 1, delete_timestamp = %s, message_content = 'This message was deleted'
                WHERE name = %s
            """, [now_datetime(), self.name])
            
            frappe.db.commit()
            
            # Send real-time notification
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
            
        except Exception as e:
            frappe.log_error(f"Error in chat message on_trash: {str(e)}")

    def update_room_last_activity(self):
        """Update room's last activity timestamp"""
        try:
            if self.chat_room:
                frappe.db.set_value(
                    "Chat Room",
                    self.chat_room,
                    "modified",
                    now_datetime()
                )
                frappe.db.commit()
                
        except Exception as e:
            frappe.log_error(f"Error updating room last activity: {str(e)}")

    def send_push_notifications(self):
        """Send push notifications to offline users"""
        try:
            if self.message_type == "System":
                return  # Don't send notifications for system messages
                
            room = frappe.get_doc("Chat Room", self.chat_room)
            
            # Get room members except sender
            recipients = []
            for member in room.members:
                if member.user != self.sender:
                    recipients.append(member.user)
            
            # Get sender info
            sender_info = frappe.get_value(
                "User",
                self.sender,
                ["full_name", "user_image"],
                as_dict=True
            )
            sender_name = sender_info.full_name if sender_info else self.sender
            
            # Prepare notification content
            notification_title = f"New message from {sender_name}"
            notification_body = self.message_content or "Sent an attachment"
            
            if len(notification_body) > 100:
                notification_body = notification_body[:97] + "..."
            
            # Create notification log entries for offline users
            for recipient in recipients:
                # Check if user is currently online (simplified check)
                is_online = self.is_user_online(recipient)
                
                if not is_online:
                    # Create notification entry
                    notification = frappe.new_doc("Notification Log")
                    notification.for_user = recipient
                    notification.from_user = self.sender
                    notification.subject = notification_title
                    notification.email_content = f"""
                        <div>
                            <h4>{notification_title}</h4>
                            <p><strong>Room:</strong> {room.room_name}</p>
                            <p><strong>Message:</strong> {notification_body}</p>
                            <p><a href="/chat/room/{room.name}">View in Chat</a></p>
                        </div>
                    """
                    notification.document_type = "Chat Message"
                    notification.document_name = self.name
                    notification.type = "Alert"
                    notification.insert(ignore_permissions=True)
                    
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error sending push notifications: {str(e)}")

    def is_user_online(self, user):
        """Check if user is currently online (simplified implementation)"""
        try:
            # Get user's last activity
            last_activity = frappe.db.get_value("User", user, "last_active")
            
            if not last_activity:
                return False
                
            # Consider user online if active in last 5 minutes
            from frappe.utils import time_diff_in_seconds
            time_diff = time_diff_in_seconds(now_datetime(), last_activity)
            return time_diff < 300  # 5 minutes
            
        except Exception:
            return False

    def process_message_content(self):
        """Process message content for URLs, mentions, etc."""
        try:
            if not self.message_content:
                return
                
            # Simple URL validation (you can enhance this)
            import re
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, self.message_content)
            
            # Log if suspicious URLs found (basic security)
            suspicious_domains = ['malicious.com', 'phishing.net']  # Add your blacklist
            for url in urls:
                for domain in suspicious_domains:
                    if domain in url:
                        frappe.log_error(f"Suspicious URL detected in chat: {url}", "Chat Security")
                        break
                        
        except Exception as e:
            frappe.log_error(f"Error processing message content: {str(e)}")

    @staticmethod
    def get_permission_query_conditions(user=None):
        """Permission query conditions for Chat Message"""
        if not user:
            user = frappe.session.user
            
        if user == "Administrator":
            return ""
            
        # Users can only see messages from rooms they are members of
        return f"""
            `tabChat Message`.chat_room IN (
                SELECT parent FROM `tabChat Room Member` 
                WHERE user = '{user}'
            )
        """

    @staticmethod
    def has_permission(doc, ptype, user=None):
        """Check if user has permission for this chat message"""
        if not user:
            user = frappe.session.user
            
        if user == "Administrator":
            return True
            
        # Check if user is a member of the room
        if doc.get("chat_room"):
            is_member = frappe.db.exists(
                "Chat Room Member",
                {"parent": doc.chat_room, "user": user}
            )
            
            if not is_member:
                return False
                
            # For edit/delete, check if user is sender or admin
            if ptype in ["write", "delete"]:
                if doc.get("sender") == user:
                    return True
                    
                # Check if user is admin in the room
                member_role = frappe.db.get_value(
                    "Chat Room Member",
                    {"parent": doc.chat_room, "user": user},
                    "is_admin"
                )
                return bool(member_role)
            
            return True
        
        # For new messages, allow creation if user is room member
        if ptype == "create":
            return True
            
        return False


# Utility API functions

@frappe.whitelist()
def get_user_chat_status():
    """Get current user's chat status and unread count"""
    try:
        current_user = frappe.session.user
        
        # Get user's chat rooms with unread count
        rooms = frappe.db.sql("""
            SELECT 
                cr.name,
                cr.room_name,
                cr.room_type,
                crm.last_read_timestamp,
                COUNT(cm.name) as unread_count
            FROM `tabChat Room` cr
            INNER JOIN `tabChat Room Member` crm ON cr.name = crm.parent
            LEFT JOIN `tabChat Message` cm ON cr.name = cm.chat_room 
                AND cm.timestamp > COALESCE(crm.last_read_timestamp, '1900-01-01')
                AND cm.sender != %(user)s
                AND cm.is_deleted = 0
            WHERE crm.user = %(user)s 
                AND cr.room_status = 'Active'
            GROUP BY cr.name, cr.room_name, cr.room_type, crm.last_read_timestamp
            ORDER BY unread_count DESC, cr.modified DESC
        """, {"user": current_user}, as_dict=True)
        
        total_unread = sum(room.unread_count for room in rooms)
        
        return {
            "success": True,
            "data": {
                "total_unread": total_unread,
                "rooms_with_unread": [room for room in rooms if room.unread_count > 0],
                "total_rooms": len(rooms)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_user_chat_status: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def mark_room_as_read(room_id):
    """Mark all messages in a room as read for current user"""
    try:
        current_user = frappe.session.user
        
        # Update user's last read timestamp
        frappe.db.sql("""
            UPDATE `tabChat Room Member` 
            SET last_read_timestamp = %(timestamp)s
            WHERE parent = %(room_id)s AND user = %(user)s
        """, {
            "room_id": room_id,
            "user": current_user,
            "timestamp": now_datetime()
        })
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Room marked as read"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in mark_room_as_read: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_recent_chat_activity():
    """Get recent chat activity for dashboard/homepage"""
    try:
        current_user = frappe.session.user
        
        # Get recent messages from user's rooms
        recent_activity = frappe.db.sql("""
            SELECT 
                cm.name,
                cm.chat_room,
                cm.sender,
                cm.message_content,
                cm.timestamp,
                cm.message_type,
                cr.room_name,
                cr.room_type,
                u.full_name as sender_name
            FROM `tabChat Message` cm
            INNER JOIN `tabChat Room` cr ON cm.chat_room = cr.name
            INNER JOIN `tabChat Room Member` crm ON cr.name = crm.parent
            LEFT JOIN `tabUser` u ON cm.sender = u.name
            WHERE crm.user = %(user)s
                AND cm.is_deleted = 0
                AND cm.timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND cr.room_status = 'Active'
            ORDER BY cm.timestamp DESC
            LIMIT 10
        """, {"user": current_user}, as_dict=True)
        
        # Format timestamps
        for activity in recent_activity:
            activity.timestamp = str(activity.timestamp)
            if activity.message_content and len(activity.message_content) > 100:
                activity.message_content = activity.message_content[:97] + "..."
        
        return {
            "success": True,
            "data": {
                "recent_activity": recent_activity
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_recent_chat_activity: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# WebSocket event handlers for real-time updates

def handle_websocket_message(data):
    """Handle incoming WebSocket messages for chat"""
    try:
        event_type = data.get('event')
        message_data = data.get('data', {})
        
        if event_type == 'join_room':
            handle_user_join_room(message_data)
        elif event_type == 'leave_room':
            handle_user_leave_room(message_data)
        elif event_type == 'typing_start':
            handle_typing_indicator(message_data, True)
        elif event_type == 'typing_stop':
            handle_typing_indicator(message_data, False)
            
    except Exception as e:
        frappe.log_error(f"Error handling WebSocket message: {str(e)}")

def handle_user_join_room(data):
    """Handle user joining a room"""
    try:
        room_id = data.get('room_id')
        user = data.get('user', frappe.session.user)
        
        if room_id:
            # Update user's last read timestamp
            mark_room_as_read(room_id)
            
            # Broadcast to other room members
            room = frappe.get_doc("Chat Room", room_id)
            other_members = [member.user for member in room.members if member.user != user]
            
            frappe.publish_realtime(
                event="user_joined_room",
                message={
                    "user": user,
                    "room_id": room_id,
                    "timestamp": str(now_datetime())
                },
                user=other_members,
                room=f"chat_room_{room_id}"
            )
            
    except Exception as e:
        frappe.log_error(f"Error in handle_user_join_room: {str(e)}")

def handle_user_leave_room(data):
    """Handle user leaving a room"""
    try:
        room_id = data.get('room_id')
        user = data.get('user', frappe.session.user)
        
        if room_id:
            # Broadcast to other room members
            room = frappe.get_doc("Chat Room", room_id)
            other_members = [member.user for member in room.members if member.user != user]
            
            frappe.publish_realtime(
                event="user_left_room",
                message={
                    "user": user,
                    "room_id": room_id,
                    "timestamp": str(now_datetime())
                },
                user=other_members,
                room=f"chat_room_{room_id}"
            )
            
    except Exception as e:
        frappe.log_error(f"Error in handle_user_leave_room: {str(e)}")

def handle_typing_indicator(data, is_typing):
    """Handle typing indicator events"""
    try:
        room_id = data.get('room_id')
        user = data.get('user', frappe.session.user)
        
        if room_id:
            # Broadcast typing indicator to other room members
            room = frappe.get_doc("Chat Room", room_id)
            other_members = [member.user for member in room.members if member.user != user]
            
            frappe.publish_realtime(
                event="typing_indicator",
                message={
                    "user": user,
                    "room_id": room_id,
                    "is_typing": is_typing,
                    "timestamp": str(now_datetime())
                },
                user=other_members,
                room=f"chat_room_{room_id}"
            )
            
    except Exception as e:
        frappe.log_error(f"Error in handle_typing_indicator: {str(e)}")