# vms/APIs/notification_chatroom/chat_apis/room_management.py
import frappe
from frappe import _
from frappe.utils import now_datetime, cint
import json

@frappe.whitelist()
def get_room_details(room_id):
    """
    Get detailed information about a chat room
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: Room details with members
    """
    try:
        current_user = frappe.session.user
        
        # Get room details
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Get member details with user info
        members = []
        for member in room.members:
            user_info = frappe.db.get_value(
                "User",
                member.user,
                ["full_name", "user_image", "email"],
                as_dict=True
            )
            
            # Get employee info if available
            employee_info = frappe.db.get_value(
                "Employee",
                {"user_id": member.user},
                ["designation", "department"],
                as_dict=True
            )
            
            members.append({
                "user": member.user,
                "role": member.role,
                "is_admin": member.is_admin,
                "is_muted": member.is_muted,
                "joined_date": str(member.joined_date) if member.joined_date else None,
                "last_read_timestamp": str(member.last_read_timestamp) if member.last_read_timestamp else None,
                "user_info": user_info or {},
                "employee_info": employee_info or {}
            })
            
        return {
            "success": True,
            "data": {
                "room_id": room.name,
                "room_name": room.room_name,
                "room_type": room.room_type,
                "description": room.description,
                "room_status": room.room_status,
                "is_private": room.is_private,
                "max_members": room.max_members,
                "allow_file_sharing": room.allow_file_sharing,
                "created_by": room.created_by,
                "creation_date": str(room.creation_date) if room.creation_date else None,
                "team_master": room.team_master,
                "members": members,
                "member_count": len(members),
                "user_permissions": permissions
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_room_details: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def add_room_member(room_id, user_id, role="Member"):
    """
    Add a member to a chat room
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User ID to add
        role (str): Role for the new member
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get room and check permissions
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        if not permissions["is_admin"]:
            frappe.throw("Only admins can add members")
            
        # Check if user exists
        if not frappe.db.exists("User", user_id):
            frappe.throw(f"User {user_id} does not exist")
            
        # Add member
        room.add_member(user_id, role)
        
        return {
            "success": True,
            "message": f"User {user_id} added to the room successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in add_room_member: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def remove_room_member(room_id, user_id):
    """
    Remove a member from a chat room
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User ID to remove
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get room and check permissions
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Users can remove themselves or admins can remove others
        if user_id != current_user and not permissions["is_admin"]:
            frappe.throw("Only admins can remove other members")
            
        # Remove member
        room.remove_member(user_id)
        
        return {
            "success": True,
            "message": f"User {user_id} removed from the room successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in remove_room_member: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def update_member_role(room_id, user_id, new_role):
    """
    Update a member's role in a chat room
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User ID
        new_role (str): New role (Member, Admin, Moderator)
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get room and check permissions
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_admin"]:
            frappe.throw("Only admins can update member roles")
            
        # Find and update member
        member_found = False
        for member in room.members:
            if member.user == user_id:
                member.role = new_role
                member.is_admin = 1 if new_role == "Admin" else 0
                member_found = True
                break
                
        if not member_found:
            frappe.throw(f"User {user_id} is not a member of this room")
            
        room.save(ignore_permissions=True)
        
        # Create system message
        room.create_system_message(f"{user_id} role updated to {new_role}")
        
        return {
            "success": True,
            "message": f"User {user_id} role updated to {new_role}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in update_member_role: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def mute_unmute_member(room_id, user_id, is_muted):
    """
    Mute or unmute a member in a chat room
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User ID to mute/unmute
        is_muted (int): 1 to mute, 0 to unmute
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        is_muted = cint(is_muted)
        
        # Get room and check permissions
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_admin"]:
            frappe.throw("Only admins can mute/unmute members")
            
        # Find and update member
        member_found = False
        for member in room.members:
            if member.user == user_id:
                member.is_muted = is_muted
                member_found = True
                break
                
        if not member_found:
            frappe.throw(f"User {user_id} is not a member of this room")
            
        room.save(ignore_permissions=True)
        
        # Create system message
        action = "muted" if is_muted else "unmuted"
        room.create_system_message(f"{user_id} has been {action}")
        
        return {
            "success": True,
            "message": f"User {user_id} has been {action}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in mute_unmute_member: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def update_room_settings(room_id, room_name=None, description=None, max_members=None, 
                        allow_file_sharing=None, auto_delete_messages_after_days=None):
    """
    Update room settings
    
    Args:
        room_id (str): Chat room ID
        room_name (str): New room name
        description (str): New description
        max_members (int): Maximum members allowed
        allow_file_sharing (int): Allow file sharing (1 or 0)
        auto_delete_messages_after_days (int): Auto delete messages after days
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get room and check permissions
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_admin"]:
            frappe.throw("Only admins can update room settings")
            
        # Update settings
        if room_name is not None:
            room.room_name = room_name
            
        if description is not None:
            room.description = description
            
        if max_members is not None:
            max_members = cint(max_members)
            if max_members < len(room.members):
                frappe.throw("Maximum members cannot be less than current member count")
            room.max_members = max_members
            
        if allow_file_sharing is not None:
            room.allow_file_sharing = cint(allow_file_sharing)
            
        if auto_delete_messages_after_days is not None:
            room.auto_delete_messages_after_days = cint(auto_delete_messages_after_days)
            
        room.save(ignore_permissions=True)
        
        # Create system message for significant changes
        if room_name is not None:
            room.create_system_message(f"Room name changed to '{room_name}'")
            
        return {
            "success": True,
            "message": "Room settings updated successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in update_room_settings: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def archive_room(room_id):
    """
    Archive a chat room
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get room and check permissions
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_admin"]:
            frappe.throw("Only admins can archive rooms")
            
        room.room_status = "Archived"
        room.save(ignore_permissions=True)
        
        # Create system message
        room.create_system_message("Room has been archived")
        
        return {
            "success": True,
            "message": "Room archived successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in archive_room: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def search_users_for_room(search_term, room_id=None, exclude_current_members=1):
    """
    Search users to add to a room
    
    Args:
        search_term (str): Search term for user names/emails
        room_id (str): Room ID to exclude current members
        exclude_current_members (int): Whether to exclude current room members
        
    Returns:
        dict: List of users
    """
    try:
        current_user = frappe.session.user
        exclude_current_members = cint(exclude_current_members)
        
        # Get current room members if excluding
        excluded_users = [current_user]  # Always exclude current user
        if room_id and exclude_current_members:
            room = frappe.get_doc("Chat Room", room_id)
            excluded_users.extend([member.user for member in room.members])
            
        # Search users
        conditions = ["enabled = 1", "name != 'Guest'"]
        values = []
        
        if search_term:
            conditions.append("(full_name LIKE %(search)s OR email LIKE %(search)s)")
            values.append(f"%{search_term}%")
            
        if excluded_users:
            placeholders = ", ".join(["%s"] * len(excluded_users))
            conditions.append(f"name NOT IN ({placeholders})")
            values.extend(excluded_users)
            
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT 
                name as user_id,
                full_name,
                email,
                user_image
            FROM `tabUser`
            WHERE {where_clause}
            ORDER BY full_name
            LIMIT 50
        """
        
        users = frappe.db.sql(query, values, as_dict=True)
        
        # Get employee info for each user
        for user in users:
            employee_info = frappe.db.get_value(
                "Employee",
                {"user_id": user.user_id},
                ["designation", "department", "team"],
                as_dict=True
            )
            user["employee_info"] = employee_info or {}
            
        return {
            "success": True,
            "data": {
                "users": users
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in search_users_for_room: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def get_team_chat_rooms():
    """
    Get available team chat rooms based on user's team
    
    Returns:
        dict: List of team chat rooms
    """
    try:
        current_user = frappe.session.user
        
        # Get user's employee record
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": current_user},
            ["team", "full_name"],
            as_dict=True
        )
        
        if not employee or not employee.team:
            return {
                "success": True,
                "data": {
                    "team_rooms": [],
                    "message": "No team assigned to current user"
                }
            }
            
        # Get team chat rooms for user's team
        team_rooms = frappe.get_all(
            "Chat Room",
            filters={
                "room_type": "Team Chat",
                "team_master": employee.team,
                "room_status": "Active"
            },
            fields=[
                "name", "room_name", "description", "creation",
                "created_by", "is_private"
            ]
        )
        
        # Check if user is member of each room
        for room in team_rooms:
            is_member = frappe.db.exists(
                "Chat Room Member",
                {"parent": room.name, "user": current_user}
            )
            room["is_member"] = bool(is_member)
            room["creation"] = str(room.creation)
            
        return {
            "success": True,
            "data": {
                "team_rooms": team_rooms,
                "user_team": employee.team
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_team_chat_rooms: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def join_team_room(room_id):
    """
    Join a team chat room
    
    Args:
        room_id (str): Team chat room ID
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get room and validate it's a team chat
        room = frappe.get_doc("Chat Room", room_id)
        
        if room.room_type != "Team Chat":
            frappe.throw("This function only works for team chat rooms")
            
        # Check if user belongs to the team
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": current_user},
            ["team"],
            as_dict=True
        )
        
        if not employee or employee.team != room.team_master:
            frappe.throw("You can only join team rooms for your assigned team")
            
        # Check if already a member
        permissions = room.get_member_permissions(current_user)
        if permissions["is_member"]:
            frappe.throw("You are already a member of this room")
            
        # Add user to room
        room.add_member(current_user, "Member")
        
        return {
            "success": True,
            "message": "Successfully joined the team room"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in join_team_room: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }