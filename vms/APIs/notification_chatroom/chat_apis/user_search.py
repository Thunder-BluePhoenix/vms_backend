# NEW API: User Search for Chat Room Members
# File: vms/APIs/notification_chatroom/chat_apis/user_search.py

import frappe
from frappe import _
import json

@frappe.whitelist()
def search_users_for_chat_room(search_term="", room_id=None, exclude_existing=True):
    """
    Search users that can be added to chat rooms
    
    Args:
        search_term (str): Search term to filter users
        room_id (str): Room ID to exclude existing members
        exclude_existing (bool): Whether to exclude existing room members
    
    Returns:
        dict: Success status and user data
    """
    try:
        # Build search conditions
        conditions = []
        values = []
        
        # Only include enabled users who allow guest access
        conditions.append("enabled = 1")
        
        # Add custom field check if exists
        if frappe.db.has_column("User", "allow_guest"):
            conditions.append("allow_guest = 1")
        
        # Search filter
        if search_term:
            search_condition = """(
                LOWER(full_name) LIKE LOWER(%s) OR 
                LOWER(first_name) LIKE LOWER(%s) OR 
                LOWER(last_name) LIKE LOWER(%s) OR 
                LOWER(email) LIKE LOWER(%s) OR
                LOWER(name) LIKE LOWER(%s)
            )"""
            conditions.append(search_condition)
            search_pattern = f"%{search_term}%"
            values.extend([search_pattern] * 5)
        
        # Exclude system users
        conditions.append("name NOT IN ('Administrator', 'Guest')")
        
        # Get existing room members to exclude
        existing_members = []
        if room_id and exclude_existing:
            try:
                existing_members_data = frappe.db.sql("""
                    SELECT user 
                    FROM `tabChat Room Member` 
                    WHERE parent = %s
                """, [room_id], as_dict=True)
                existing_members = [member.user for member in existing_members_data]
            except Exception as e:
                frappe.log_error(f"Error getting existing members: {str(e)}")
        
        # Exclude existing members
        if existing_members:
            placeholders = ",".join(["%s"] * len(existing_members))
            conditions.append(f"name NOT IN ({placeholders})")
            values.extend(existing_members)
        
        # Build final query
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT 
                name,
                email,
                full_name,
                first_name,
                last_name,
                user_image,
                enabled,
                creation
            FROM `tabUser`
            WHERE {where_clause}
            ORDER BY 
                CASE 
                    WHEN full_name IS NOT NULL AND full_name != '' THEN full_name
                    WHEN first_name IS NOT NULL AND first_name != '' THEN first_name
                    ELSE name
                END
            LIMIT 50
        """
        
        users = frappe.db.sql(query, values, as_dict=True)
        
        # Format user data
        formatted_users = []
        for user in users:
            display_name = user.full_name or f"{user.first_name or ''} {user.last_name or ''}".strip() or user.name
            
            formatted_users.append({
                'name': user.name,
                'email': user.email,
                'full_name': display_name,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_image': user.user_image,
                'display_text': f"{display_name} ({user.email})"
            })
        
        return {
            'success': True,
            'data': formatted_users,
            'total_count': len(formatted_users),
            'search_term': search_term,
            'excluded_members': len(existing_members) if existing_members else 0
        }
        
    except Exception as e:
        frappe.log_error(f"Error in search_users_for_chat_room: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'data': []
        }

@frappe.whitelist()
def add_member_to_room(room_id, user_id, role="Member"):
    """
    Add a single member to chat room
    
    Args:
        room_id (str): Chat room ID
        user_id (str): User to add
        role (str): Member role (Member, Moderator, Admin)
    
    Returns:
        dict: Success status and message
    """
    try:
        # Validate inputs
        if not room_id or not user_id:
            return {
                'success': False,
                'error': 'Room ID and User ID are required'
            }
        
        # Check if room exists
        if not frappe.db.exists("Chat Room", room_id):
            return {
                'success': False,
                'error': 'Chat room not found'
            }
        
        # Check if user exists and is enabled
        user_doc = frappe.get_doc("User", user_id)
        if not user_doc.enabled:
            return {
                'success': False,
                'error': 'User is disabled and cannot be added'
            }
        
        # Check if user is already a member
        existing_member = frappe.db.exists("Chat Room Member", {
            'parent': room_id,
            'user': user_id
        })
        
        if existing_member:
            return {
                'success': False,
                'error': f'User {user_id} is already a member of this room'
            }
        
        # Get room document
        room_doc = frappe.get_doc("Chat Room", room_id)
        
        # Check room capacity
        current_member_count = len(room_doc.members)
        max_members = room_doc.max_members or 50
        
        if current_member_count >= max_members:
            return {
                'success': False,
                'error': f'Room has reached maximum capacity of {max_members} members'
            }
        
        # Add member to room
        room_doc.append('members', {
            'user': user_id,
            'role': role,
            'joined_on': frappe.utils.now()
        })
        
        room_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Get user's display name
        user_display_name = user_doc.full_name or user_doc.first_name or user_id
        
        return {
            'success': True,
            'message': f'{user_display_name} added to room successfully',
            'member_count': len(room_doc.members),
            'user_display_name': user_display_name
        }
        
    except Exception as e:
        frappe.log_error(f"Error in add_member_to_room: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def add_multiple_members_to_room(room_id, user_list, role="Member"):
    """
    Add multiple members to chat room in batch
    
    Args:
        room_id (str): Chat room ID
        user_list (str): JSON string of user IDs list
        role (str): Default role for all members
    
    Returns:
        dict: Success status with detailed results
    """
    try:
        # Parse user list
        if isinstance(user_list, str):
            users = json.loads(user_list)
        else:
            users = user_list
        
        if not users:
            return {
                'success': False,
                'error': 'No users provided'
            }
        
        # Validate room exists
        if not frappe.db.exists("Chat Room", room_id):
            return {
                'success': False,
                'error': 'Chat room not found'
            }
        
        room_doc = frappe.get_doc("Chat Room", room_id)
        
        results = {
            'success': True,
            'added_users': [],
            'failed_users': [],
            'already_members': [],
            'total_requested': len(users),
            'total_added': 0,
            'total_failed': 0
        }
        
        for user_id in users:
            try:
                # Check if user exists and is enabled
                if not frappe.db.exists("User", {"name": user_id, "enabled": 1}):
                    results['failed_users'].append({
                        'user_id': user_id,
                        'reason': 'User not found or disabled'
                    })
                    continue
                
                # Check if already a member
                existing_member = frappe.db.exists("Chat Room Member", {
                    'parent': room_id,
                    'user': user_id
                })
                
                if existing_member:
                    results['already_members'].append(user_id)
                    continue
                
                # Check room capacity
                current_member_count = len(room_doc.members)
                max_members = room_doc.max_members or 50
                
                if current_member_count >= max_members:
                    results['failed_users'].append({
                        'user_id': user_id,
                        'reason': f'Room capacity full ({max_members} members)'
                    })
                    continue
                
                # Add member
                room_doc.append('members', {
                    'user': user_id,
                    'role': role,
                    'joined_on': frappe.utils.now()
                })
                
                results['added_users'].append(user_id)
                results['total_added'] += 1
                
            except Exception as e:
                results['failed_users'].append({
                    'user_id': user_id,
                    'reason': str(e)
                })
        
        # Save room document if any members were added
        if results['total_added'] > 0:
            room_doc.save(ignore_permissions=True)
            frappe.db.commit()
        
        results['total_failed'] = len(results['failed_users'])
        results['final_member_count'] = len(room_doc.members)
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Error in add_multiple_members_to_room: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }