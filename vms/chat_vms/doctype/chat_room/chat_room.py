# vms/chat_vms/doctype/chat_room/chat_room.py
# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class ChatRoom(Document):
    def validate(self):
        self.validate_room_type()
        self.validate_members()
        
    def before_save(self):
        if self.room_type == "Team Chat" and self.team_master:
            self.populate_team_members()
            
    def validate_room_type(self):
        """Validate room type specific requirements"""
        if self.room_type == "Direct Message" and len(self.members) > 2:
            frappe.throw("Direct Message rooms can only have 2 members")
            
        if self.room_type == "Team Chat" and not self.team_master:
            frappe.throw("Team Master is required for Team Chat rooms")
            
    def validate_members(self):
        """Validate member limits"""
        if len(self.members) > self.max_members:
            frappe.throw(f"Room cannot have more than {self.max_members} members")
            
        # Check for duplicate members
        user_list = [member.user for member in self.members]
        if len(user_list) != len(set(user_list)):
            frappe.throw("Duplicate members are not allowed")
            
    def populate_team_members(self):
        """Auto-populate team members when team_master is selected"""
        if not self.team_master:
            return
            
        # Get team members from Employee doctype
        team_employees = frappe.get_all(
            "Employee",
            filters={"team": self.team_master, "status": "Active"},
            fields=["user_id", "full_name"]
        )
        
        # Clear existing members if this is team chat
        if self.room_type == "Team Chat":
            self.members = []
            
        existing_users = [member.user for member in self.members]
        
        for employee in team_employees:
            if employee.user_id and employee.user_id not in existing_users:
                self.append("members", {
                    "user": employee.user_id,
                    "role": "Member",
                    "joined_date": now_datetime()
                })
                
        # Make team reporting head as admin
        team_head = frappe.get_value("Team Master", self.team_master, "reporting_head")
        if team_head:
            head_user = frappe.get_value("Employee", team_head, "user_id")
            if head_user:
                for member in self.members:
                    if member.user == head_user:
                        member.role = "Admin"
                        member.is_admin = 1
                        break
                        
    def add_member(self, user_id, role="Member"):
        """Add a new member to the chat room"""
        # Check if user already exists
        existing_member = None
        for member in self.members:
            if member.user == user_id:
                existing_member = member
                break
                
        if existing_member:
            frappe.throw(f"User {user_id} is already a member of this room")
            
        # Check member limit
        if len(self.members) >= self.max_members:
            frappe.throw(f"Room has reached maximum member limit of {self.max_members}")
            
        # Add new member
        self.append("members", {
            "user": user_id,
            "role": role,
            "is_admin": 1 if role == "Admin" else 0,
            "joined_date": now_datetime()
        })
        
        self.save(ignore_permissions=True)
        
        # Create system message
        self.create_system_message(f"{user_id} joined the chat")
        
    def remove_member(self, user_id):
        """Remove a member from the chat room"""
        member_to_remove = None
        for i, member in enumerate(self.members):
            if member.user == user_id:
                member_to_remove = i
                break
                
        if member_to_remove is None:
            frappe.throw(f"User {user_id} is not a member of this room")
            
        # Remove member
        self.members.pop(member_to_remove)
        self.save(ignore_permissions=True)
        
        # Create system message
        self.create_system_message(f"{user_id} left the chat")
        
    def create_system_message(self, content):
        """Create a system message in the chat room"""
        message = frappe.new_doc("Chat Message")
        message.chat_room = self.name
        message.sender = "Administrator"
        message.message_type = "System"
        message.message_content = content
        message.timestamp = now_datetime()
        message.insert(ignore_permissions=True)
        
    def get_member_permissions(self, user_id):
        """Get permissions for a specific member"""
        for member in self.members:
            if member.user == user_id:
                return {
                    "is_member": True,
                    "is_admin": member.is_admin,
                    "role": member.role,
                    "is_muted": member.is_muted
                }
        return {"is_member": False}
        
    def update_last_read(self, user_id):
        """Update last read timestamp for a user"""
        for member in self.members:
            if member.user == user_id:
                member.last_read_timestamp = now_datetime()
                self.save(ignore_permissions=True)
                break

    def after_insert_hook(self, method=None):
        """Hook method called after chat room is created"""
        try:
            # Send notification to team members if it's a team chat
            if self.room_type == "Team Chat" and self.team_master:
                self.notify_team_members_of_new_room()
                
            # Create welcome system message
            self.create_system_message(f"Welcome to {self.room_name}! Start chatting now.")
            
        except Exception as e:
            frappe.log_error(f"Error in chat room after_insert_hook: {str(e)}")

    def on_update_hook(self, method=None):
        """Hook method called when chat room is updated"""
        try:
            # Check if room name changed
            if self.has_value_changed("room_name"):
                old_name = self.get_db_value("room_name")
                if old_name and old_name != self.room_name:
                    self.create_system_message(f"Room name changed from '{old_name}' to '{self.room_name}'")
                    
            # Check if new members were added
            if self.has_value_changed("members"):
                self.handle_member_changes()
                
        except Exception as e:
            frappe.log_error(f"Error in chat room on_update_hook: {str(e)}")

    def on_trash(self):
        """Handle room deletion"""
        try:
            # Archive all messages in the room instead of deleting
            frappe.db.sql("""
                UPDATE `tabChat Message` 
                SET is_deleted = 1, delete_timestamp = %s, message_content = 'Room was deleted'
                WHERE chat_room = %s AND is_deleted = 0
            """, [now_datetime(), self.name])
            
            # Create final system message
            self.create_system_message("This room has been deleted")
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error in chat room on_trash: {str(e)}")

    def notify_team_members_of_new_room(self):
        """Notify team members about new team chat room"""
        try:
            if not self.team_master:
                return
                
            # Get team members
            team_members = frappe.get_all(
                "Employee",
                filters={"team": self.team_master, "status": "Active"},
                fields=["user_id", "full_name"]
            )
            
            # Send email notification
            for member in team_members:
                if member.user_id:
                    frappe.sendmail(
                        recipients=[member.user_id],
                        subject=f"New Team Chat Room: {self.room_name}",
                        message=f"""
                            <p>Hello {member.full_name},</p>
                            <p>A new team chat room has been created: <strong>{self.room_name}</strong></p>
                            <p>Description: {self.description or 'No description provided'}</p>
                            <p>You can access the chat room from the chat application.</p>
                            <p>Best regards,<br>VMS Team</p>
                        """,
                        now=True
                    )
                    
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error notifying team members: {str(e)}")

    def handle_member_changes(self):
        """Handle member addition/removal changes"""
        try:
            # Get previous members from database
            old_members = set()
            if self.name:
                old_member_records = frappe.get_all(
                    "Chat Room Member",
                    filters={"parent": self.name},
                    fields=["user"]
                )
                old_members = {member.user for member in old_member_records}
            
            # Get current members
            current_members = {member.user for member in self.members}
            
            # Find added and removed members
            added_members = current_members - old_members
            removed_members = old_members - current_members
            
            # Create system messages for changes
            for user in added_members:
                user_name = frappe.get_value("User", user, "full_name") or user
                self.create_system_message(f"{user_name} joined the chat")
                
            for user in removed_members:
                user_name = frappe.get_value("User", user, "full_name") or user
                self.create_system_message(f"{user_name} left the chat")
                
        except Exception as e:
            frappe.log_error(f"Error handling member changes: {str(e)}")

    @staticmethod
    def get_permission_query_conditions(user=None):
        """Permission query conditions for Chat Room"""
        if not user:
            user = frappe.session.user
            
        if user == "Administrator":
            return ""
            
        # Users can only see rooms they are members of
        return f"""
            `tabChat Room`.name IN (
                SELECT parent FROM `tabChat Room Member` 
                WHERE user = '{user}'
            )
        """

    @staticmethod
    def has_permission(doc, ptype, user=None):
        """Check if user has permission for this chat room"""
        if not user:
            user = frappe.session.user
            
        if user == "Administrator":
            return True
            
        # Check if user is a member of this room
        if doc.get("name"):
            is_member = frappe.db.exists(
                "Chat Room Member",
                {"parent": doc.name, "user": user}
            )
            return bool(is_member)
        
        # For new rooms, allow creation
        if ptype == "create":
            return True
            
        return False