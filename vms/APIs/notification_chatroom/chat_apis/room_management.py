# vms/APIs/notification_chatroom/chat_apis/room_management.py
import frappe
from frappe import _
from frappe.utils import now_datetime, cint
import json

@frappe.whitelist()
def check_room_permissions(room_id, user_id=None):
    """
    Check user permissions for a chat room based on member role
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User ID (defaults to current user)
        
    Returns:
        dict: Permission details
    """
    try:
        if not user_id:
            user_id = frappe.session.user
            
        # Check if room exists
        if not frappe.db.exists("Chat Room", room_id):
            return {
                "success": False,
                "error": "Room not found"
            }
            
        # Get member role
        member_data = frappe.db.get_value(
            "Chat Room Member",
            {"parent": room_id, "user": user_id},
            ["role", "is_muted", "joined_date"],
            as_dict=True
        )
        
        if not member_data:
            return {
                "success": True,
                "permissions": {
                    "is_member": False,
                    "role": None,
                    "can_send_messages": False,
                    "can_edit_messages": False,
                    "can_delete_messages": False,
                    "can_add_members": False,
                    "can_remove_members": False,
                    "can_update_roles": False,
                    "can_mute_members": False,
                    "can_update_room_settings": False,
                    "can_archive_room": False,
                    "can_delete_room": False,
                    "is_muted": False
                }
            }
            
        role = member_data.role
        is_muted = member_data.get("is_muted", 0)
        
        # Define permissions based on role
        permissions = {
            "is_member": True,
            "role": role,
            "can_send_messages": not is_muted,
            "can_edit_messages": not is_muted,  # Can edit own messages
            "can_delete_messages": not is_muted,  # Can delete own messages
            "is_muted": bool(is_muted),
            "joined_date": str(member_data.joined_date) if member_data.joined_date else None
        }
        
        # Role-based permissions
        if role == "Admin":
            permissions.update({
                "can_add_members": True,
                "can_remove_members": True,
                "can_update_roles": True,
                "can_mute_members": True,
                "can_update_room_settings": True,
                "can_archive_room": True,
                "can_delete_room": True,
                "can_delete_any_message": True,
                "can_edit_any_message": False  # Usually not allowed even for admins
            })
        elif role == "Moderator":
            permissions.update({
                "can_add_members": True,
                "can_remove_members": True,  # Can remove regular members only
                "can_update_roles": False,   # Cannot change roles
                "can_mute_members": True,
                "can_update_room_settings": False,
                "can_archive_room": False,
                "can_delete_room": False,
                "can_delete_any_message": True,  # Can delete others' messages
                "can_edit_any_message": False
            })
        else:  # Member
            permissions.update({
                "can_add_members": False,
                "can_remove_members": False,
                "can_update_roles": False,
                "can_mute_members": False,
                "can_update_room_settings": False,
                "can_archive_room": False,
                "can_delete_room": False,
                "can_delete_any_message": False,
                "can_edit_any_message": False
            })
            
        return {
            "success": True,
            "permissions": permissions
        }
        
    except Exception as e:
        frappe.log_error(f"Error in check_room_permissions: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_room_details(room_id):
    """
    Get detailed information about a chat room
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: Room details with members and permissions
    """
    try:
        current_user = frappe.session.user
        
        # Check permissions first
        perm_check = check_room_permissions(room_id, current_user)
        if not perm_check["success"]:
            return perm_check
            
        permissions = perm_check["permissions"]
        
        if not permissions["is_member"]:
            return {
                "success": False,
                "error": "You are not a member of this chat room"
            }
            
        # Get room details
        room = frappe.get_doc("Chat Room", room_id)
        
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
                "is_muted": member.is_muted,
                "joined_date": str(member.joined_date) if member.joined_date else None,
                "last_read_timestamp": str(member.last_read_timestamp) if member.last_read_timestamp else None,
                "user_full_name": user_info.get("full_name") if user_info else member.user,
                "user_image": user_info.get("user_image") if user_info else None,
                "user_email": user_info.get("email") if user_info else None,
                "employee_info": employee_info or {}
            })
            
        return {
            "success": True,
            "data": {
                "room": {
                    "name": room.name,
                    "room_name": room.room_name,
                    "room_type": room.room_type,
                    "description": room.description,
                    "room_status": room.room_status,
                    "is_private": room.is_private,
                    "max_members": room.max_members,
                    "allow_file_sharing": room.allow_file_sharing,
                    "auto_delete_messages_after_days": room.auto_delete_messages_after_days,
                    "created_by": room.created_by,
                    "creation_date": str(room.creation_date) if room.creation_date else None,
                    "team_master": room.team_master,
                    "members": members,
                    "member_count": len(members)
                },
                "user_permissions": permissions
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_room_details: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def add_room_member(room_id, user_id, role="Member"):
    """
    Add a member to a chat room
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User ID to add
        role (str): Role for the new member (Member, Moderator, Admin)
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Check permissions
        perm_check = check_room_permissions(room_id, current_user)
        if not perm_check["success"]:
            return perm_check
            
        permissions = perm_check["permissions"]
        
        if not permissions["can_add_members"]:
            return {
                "success": False,
                "error": "You don't have permission to add members to this room"
            }
            
        # Validate role
        valid_roles = ["Member", "Moderator", "Admin"]
        if role not in valid_roles:
            return {
                "success": False,
                "error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            }
            
        # Only admins can assign Admin or Moderator roles
        if role in ["Admin", "Moderator"] and permissions["role"] != "Admin":
            return {
                "success": False,
                "error": "Only admins can assign Admin or Moderator roles"
            }
            
        # Check if user exists and is enabled
        user_exists = frappe.db.get_value("User", user_id, ["enabled"], as_dict=True)
        if not user_exists:
            return {
                "success": False,
                "error": f"User {user_id} does not exist"
            }
            
        if not user_exists.enabled:
            return {
                "success": False,
                "error": f"User {user_id} is disabled"
            }
            
        # Check if user is already a member
        existing_member = frappe.db.exists("Chat Room Member", {
            "parent": room_id,
            "user": user_id
        })
        
        if existing_member:
            return {
                "success": False,
                "error": f"User {user_id} is already a member of this room"
            }
            
        # Get room and check capacity
        room = frappe.get_doc("Chat Room", room_id)
        if len(room.members) >= room.max_members:
            return {
                "success": False,
                "error": f"Room has reached maximum capacity of {room.max_members} members"
            }
            
        # Add member
        room.append('members', {
            'user': user_id,
            'role': role,
            'joined_date': now_datetime(),
            'is_muted': 0
        })
        
        room.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Get user's display name for response
        user_name = frappe.db.get_value("User", user_id, "full_name") or user_id
        
        return {
            "success": True,
            "message": f"{user_name} added to room as {role}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in add_room_member: {str(e)}")
        return {
            "success": False,
            "error": str(e)
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
        
        # Check permissions
        perm_check = check_room_permissions(room_id, current_user)
        if not perm_check["success"]:
            return perm_check
            
        permissions = perm_check["permissions"]
        
        # Users can remove themselves, or those with remove permissions can remove others
        if user_id == current_user:
            # Users can always leave a room
            pass
        elif not permissions["can_remove_members"]:
            return {
                "success": False,
                "error": "You don't have permission to remove members from this room"
            }
        else:
            # Check target user's role - moderators cannot remove admins
            target_perm_check = check_room_permissions(room_id, user_id)
            if target_perm_check["success"]:
                target_permissions = target_perm_check["permissions"]
                if (permissions["role"] == "Moderator" and 
                    target_permissions["role"] in ["Admin", "Moderator"]):
                    return {
                        "success": False,
                        "error": "Moderators cannot remove Admins or other Moderators"
                    }
                    
        # Get room and remove member
        room = frappe.get_doc("Chat Room", room_id)
        
        member_found = False
        for i, member in enumerate(room.members):
            if member.user == user_id:
                room.members.pop(i)
                member_found = True
                break
                
        if not member_found:
            return {
                "success": False,
                "error": f"User {user_id} is not a member of this room"
            }
            
        room.save(ignore_permissions=True)
        frappe.db.commit()
        
        user_name = frappe.db.get_value("User", user_id, "full_name") or user_id
        action = "left" if user_id == current_user else "removed from"
        
        return {
            "success": True,
            "message": f"{user_name} {action} the room"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in remove_room_member: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def update_member_role(room_id, user_id, new_role):
    """
    Update a member's role in a chat room
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User ID
        new_role (str): New role (Member, Moderator, Admin)
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Check permissions
        perm_check = check_room_permissions(room_id, current_user)
        if not perm_check["success"]:
            return perm_check
            
        permissions = perm_check["permissions"]
        
        if not permissions["can_update_roles"]:
            return {
                "success": False,
                "error": "You don't have permission to update member roles"
            }
            
        # Validate role
        valid_roles = ["Member", "Moderator", "Admin"]
        if new_role not in valid_roles:
            return {
                "success": False,
                "error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            }
            
        # Users cannot change their own role
        if user_id == current_user:
            return {
                "success": False,
                "error": "You cannot change your own role"
            }
            
        # Get room and find member
        room = frappe.get_doc("Chat Room", room_id)
        
        member_found = False
        for member in room.members:
            if member.user == user_id:
                old_role = member.role
                member.role = new_role
                member_found = True
                break
                
        if not member_found:
            return {
                "success": False,
                "error": f"User {user_id} is not a member of this room"
            }
            
        room.save(ignore_permissions=True)
        frappe.db.commit()
        
        user_name = frappe.db.get_value("User", user_id, "full_name") or user_id
        
        return {
            "success": True,
            "message": f"{user_name} role updated from {old_role} to {new_role}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in update_member_role: {str(e)}")
        return {
            "success": False,
            "error": str(e)
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
        
        # Check permissions
        perm_check = check_room_permissions(room_id, current_user)
        if not perm_check["success"]:
            return perm_check
            
        permissions = perm_check["permissions"]
        
        if not permissions["can_mute_members"]:
            return {
                "success": False,
                "error": "You don't have permission to mute/unmute members"
            }
            
        # Cannot mute yourself
        if user_id == current_user:
            return {
                "success": False,
                "error": "You cannot mute/unmute yourself"
            }
            
        # Check target user's role - moderators cannot mute admins
        target_perm_check = check_room_permissions(room_id, user_id)
        if target_perm_check["success"]:
            target_permissions = target_perm_check["permissions"]
            if (permissions["role"] == "Moderator" and 
                target_permissions["role"] in ["Admin", "Moderator"]):
                return {
                    "success": False,
                    "error": "Moderators cannot mute Admins or other Moderators"
                }
                
        # Get room and find member
        room = frappe.get_doc("Chat Room", room_id)
        
        member_found = False
        for member in room.members:
            if member.user == user_id:
                member.is_muted = is_muted
                member_found = True
                break
                
        if not member_found:
            return {
                "success": False,
                "error": f"User {user_id} is not a member of this room"
            }
            
        room.save(ignore_permissions=True)
        frappe.db.commit()
        
        user_name = frappe.db.get_value("User", user_id, "full_name") or user_id
        action = "muted" if is_muted else "unmuted"
        
        return {
            "success": True,
            "message": f"{user_name} has been {action}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in mute_unmute_member: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def update_room_settings(room_id, settings):
    """
    Update room settings
    
    Args:
        room_id (str): Chat room ID
        settings (dict): Settings to update
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Parse settings if it's a JSON string
        if isinstance(settings, str):
            settings = json.loads(settings)
            
        # Check permissions
        perm_check = check_room_permissions(room_id, current_user)
        if not perm_check["success"]:
            return perm_check
            
        permissions = perm_check["permissions"]
        
        if not permissions["can_update_room_settings"]:
            return {
                "success": False,
                "error": "Only admins can update room settings"
            }
            
        # Get room
        room = frappe.get_doc("Chat Room", room_id)
        
        # Update allowed settings
        allowed_settings = [
            'room_name', 'description', 'max_members', 'allow_file_sharing', 
            'auto_delete_messages_after_days', 'is_private', 'room_type'
        ]
        
        changes_made = []
        
        for setting, value in settings.items():
            if setting not in allowed_settings:
                continue
                
            if setting == 'max_members':
                value = cint(value)
                if value < len(room.members):
                    return {
                        "success": False,
                        "error": "Maximum members cannot be less than current member count"
                    }
                    
            old_value = getattr(room, setting)
            if old_value != value:
                setattr(room, setting, value)
                changes_made.append(f"{setting}: {old_value} → {value}")
                
        if not changes_made:
            return {
                "success": True,
                "message": "No changes were made"
            }
            
        room.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Room settings updated successfully",
            "changes": changes_made
        }
        
    except Exception as e:
        frappe.log_error(f"Error in update_room_settings: {str(e)}")
        return {
            "success": False,
            "error": str(e)
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
        
        # Check permissions
        perm_check = check_room_permissions(room_id, current_user)
        if not perm_check["success"]:
            return perm_check
            
        permissions = perm_check["permissions"]
        
        if not permissions["can_archive_room"]:
            return {
                "success": False,
                "error": "Only admins can archive rooms"
            }
            
        room = frappe.get_doc("Chat Room", room_id)
        room.room_status = "Archived"
        room.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Room archived successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in archive_room: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_user_room_role(room_id, user_id=None):
    """
    Get user's role in a specific room
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User ID (defaults to current user)
        
    Returns:
        dict: User's role and basic permissions
    """
    try:
        if not user_id:
            user_id = frappe.session.user
            
        perm_check = check_room_permissions(room_id, user_id)
        
        if not perm_check["success"]:
            return perm_check
            
        permissions = perm_check["permissions"]
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "room_id": room_id,
                "is_member": permissions["is_member"],
                "role": permissions["role"],
                "is_muted": permissions["is_muted"],
                "key_permissions": {
                    "can_send_messages": permissions["can_send_messages"],
                    "can_add_members": permissions["can_add_members"],
                    "can_update_room_settings": permissions["can_update_room_settings"]
                }
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_user_room_role: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }