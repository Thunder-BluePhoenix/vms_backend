# vms/APIs/notification_chatroom/chat_apis/chat_api.py
import frappe
from frappe import _
from frappe.utils import now_datetime, cint, get_datetime
import json

@frappe.whitelist()
def get_user_chat_rooms(page=1, page_size=20, room_type=None, search=None):
    """
    Get chat rooms for current user with pagination
    
    Args:
        page (int): Page number
        page_size (int): Records per page
        room_type (str): Filter by room type
        search (str): Search in room names
        
    Returns:
        dict: Chat rooms with pagination info
    """
    try:
        current_user = frappe.session.user
        page = cint(page) or 1
        page_size = min(cint(page_size) or 20, 100)
        offset = (page - 1) * page_size
        
        # Build conditions
        conditions = ["crm.user = %(user)s"]
        values = {"user": current_user}
        
        if room_type:
            conditions.append("cr.room_type = %(room_type)s")
            values["room_type"] = room_type
            
        if search:
            conditions.append("cr.room_name LIKE %(search)s")
            values["search"] = f"%{search}%"
            
        # Add active room filter
        conditions.append("cr.room_status = 'Active'")
        
        where_clause = " AND ".join(conditions)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT cr.name) as total
            FROM `tabChat Room` cr
            INNER JOIN `tabChat Room Member` crm ON cr.name = crm.parent
            WHERE {where_clause}
        """
        
        total_count = frappe.db.sql(count_query, values, as_dict=True)[0].total
        
        # Get chat rooms with last message info
        query = f"""
            SELECT DISTINCT 
                cr.name,
                cr.room_name,
                cr.room_type,
                cr.description,
                cr.is_private,
                cr.creation,
                crm.role as user_role,
                crm.is_admin,
                crm.last_read_timestamp,
                (SELECT COUNT(*) FROM `tabChat Room Member` crm2 WHERE crm2.parent = cr.name) as member_count,
                (SELECT message_content FROM `tabChat Message` cm 
                 WHERE cm.chat_room = cr.name AND cm.is_deleted = 0 
                 ORDER BY cm.timestamp DESC LIMIT 1) as last_message,
                (SELECT timestamp FROM `tabChat Message` cm 
                 WHERE cm.chat_room = cr.name AND cm.is_deleted = 0 
                 ORDER BY cm.timestamp DESC LIMIT 1) as last_message_time,
                (SELECT sender FROM `tabChat Message` cm 
                 WHERE cm.chat_room = cr.name AND cm.is_deleted = 0 
                 ORDER BY cm.timestamp DESC LIMIT 1) as last_message_sender
            FROM `tabChat Room` cr
            INNER JOIN `tabChat Room Member` crm ON cr.name = crm.parent
            WHERE {where_clause}
            ORDER BY last_message_time DESC, cr.creation DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        values.update({"limit": page_size, "offset": offset})
        rooms = frappe.db.sql(query, values, as_dict=True)
        
        # Calculate unread count for each room
        for room in rooms:
            unread_count = 0
            if room.last_read_timestamp:
                unread_count = frappe.db.count(
                    "Chat Message",
                    filters={
                        "chat_room": room.name,
                        "timestamp": [">=", room.last_read_timestamp],
                        "sender": ["!=", current_user],
                        "is_deleted": 0
                    }
                )
            else:
                unread_count = frappe.db.count(
                    "Chat Message",
                    filters={
                        "chat_room": room.name,
                        "sender": ["!=", current_user],
                        "is_deleted": 0
                    }
                )
            
            room["unread_count"] = unread_count
            
            # Format timestamps
            if room.last_message_time:
                room["last_message_time"] = str(room.last_message_time)
            if room.creation:
                room["creation"] = str(room.creation)
            if room.last_read_timestamp:
                room["last_read_timestamp"] = str(room.last_read_timestamp)
        
        # Pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": {
                "rooms": rooms,
                "pagination": {
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_user_chat_rooms: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def create_chat_room(room_name, room_type, description=None, members=None, team_master=None, is_private=0):
    """
    Create a new chat room
    
    Args:
        room_name (str): Name of the room
        room_type (str): Type of room (Direct Message, Team Chat, Group Chat, Announcement)
        description (str): Room description
        members (list): List of user IDs to add as members
        team_master (str): Team Master for team chats
        is_private (int): Whether room is private
        
    Returns:
        dict: Created room info
    """
    try:
        current_user = frappe.session.user
        
        # Parse members if string
        if isinstance(members, str):
            members = json.loads(members) if members else []
            
        # Validate room type
        valid_room_types = ["Direct Message", "Team Chat", "Group Chat", "Announcement"]
        if room_type not in valid_room_types:
            frappe.throw(f"Invalid room type. Must be one of: {', '.join(valid_room_types)}")
            
        # Create room
        room = frappe.new_doc("Chat Room")
        room.room_name = room_name
        room.room_type = room_type
        room.description = description
        room.is_private = cint(is_private)
        room.created_by = current_user
        room.creation_date = now_datetime()
        
        if room_type == "Team Chat" and team_master:
            room.team_master = team_master
            
        # Add creator as admin
        room.append("members", {
            "user": current_user,
            "role": "Admin",
            "is_admin": 1,
            "joined_date": now_datetime()
        })
        
        # Add other members
        if members:
            for user_id in members:
                if user_id != current_user:  # Don't add creator twice
                    room.append("members", {
                        "user": user_id,
                        "role": "Member",
                        "is_admin": 0,
                        "joined_date": now_datetime()
                    })
        
        room.insert(ignore_permissions=True)
        
        # Create welcome message
        welcome_msg = frappe.new_doc("Chat Message")
        welcome_msg.chat_room = room.name
        welcome_msg.sender = current_user
        welcome_msg.message_type = "System"
        welcome_msg.message_content = f"Chat room '{room_name}' created"
        welcome_msg.timestamp = now_datetime()
        welcome_msg.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "data": {
                "room_id": room.name,
                "room_name": room.room_name,
                "room_type": room.room_type,
                "creation": str(room.creation)
            },
            "message": "Chat room created successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in create_chat_room: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def get_chat_messages(room_id, page=1, page_size=10, before_timestamp=None):
    """
    Get messages for a chat room with pagination
    
    Args:
        room_id (str): Chat room ID
        page (int): Page number
        page_size (int): Messages per page
        before_timestamp (str): Get messages before this timestamp
        
    Returns:
        dict: Messages with pagination info
    """
    try:
        current_user = frappe.session.user
        page = cint(page) or 1
        page_size = min(cint(page_size) or 50, 100)
        offset = (page - 1) * page_size
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Build conditions
        conditions = ["chat_room = %(room_id)s", "is_deleted = 0"]
        values = {"room_id": room_id}
        
        if before_timestamp:
            conditions.append("timestamp < %(before_timestamp)s")
            values["before_timestamp"] = get_datetime(before_timestamp)
            
        where_clause = " AND ".join(conditions)
        
        # Get messages with attachments and reactions
        query = f"""
            SELECT 
                name,
                sender,
                message_type,
                message_content,
                timestamp,
                reply_to_message,
                is_edited,
                edit_timestamp
            FROM `tabChat Message`
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        values.update({"limit": page_size, "offset": offset})
        messages = frappe.db.sql(query, values, as_dict=True)
        
        # Get attachments and reactions for each message
        for message in messages:
            # Attachments
            message["attachments"] = frappe.get_all(
                "Chat Message Attachment",
                filters={"parent": message.name},
                fields=["file_name", "file_url", "file_type", "file_size"]
            )

            # Reactions
            reactions = frappe.get_all(
                "Chat Message Reaction",
                filters={"parent": message.name},
                fields=["reaction_emoji", "user", "timestamp"]
            )
            reaction_summary = {}
            for reaction in reactions:
                emoji = reaction.reaction_emoji
                if emoji not in reaction_summary:
                    reaction_summary[emoji] = {"count": 0, "users": []}
                reaction_summary[emoji]["count"] += 1
                reaction_summary[emoji]["users"].append({
                    "user": reaction.user,
                    "timestamp": str(reaction.timestamp)
                })
            message["reactions"] = reaction_summary

            # ✅ Reply-to details
            if message.reply_to_message:
                reply = frappe.db.get_value(
                    "Chat Message",
                    message.reply_to_message,
                    ["name", "sender", "message_content"],
                    as_dict=True
                )
                if reply:
                    sender_info = frappe.db.get_value(
                        "User",
                        reply.sender,
                        ["full_name"],
                        as_dict=True
                    )
                    message["reply_to_content"] = reply.message_content
                    message["reply_to_sender"] = sender_info.full_name if sender_info else reply.sender
                else:
                    message["reply_to_content"] = "[Message not found]"
                    message["reply_to_sender"] = "Unknown"

            # Format timestamps
            message["timestamp"] = str(message.timestamp)
            if message.edit_timestamp:
                message["edit_timestamp"] = str(message.edit_timestamp)

            # Sender info
            sender_info = frappe.db.get_value(
                "User", 
                message.sender, 
                ["full_name", "user_image"], 
                as_dict=True
            )
            message["sender_info"] = sender_info or {"full_name": message.sender}

        
        # Update user's last read timestamp
        room.update_last_read(current_user)
        
        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabChat Message`
            WHERE {where_clause}
        """
        
        total_count = frappe.db.sql(count_query, values, as_dict=True)[0].total
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": {
                "messages": messages,
                "pagination": {
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }
        
    except Exception as e:
        # frappe.log_error(f"Error in get_chat_messages: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def send_message(room_id, message_content, message_type="Text", reply_to=None, attachments=None):
    """
    Send a message to a chat room
    
    Args:
        room_id (str): Chat room ID
        message_content (str): Message content
        message_type (str): Type of message
        reply_to (str): Message ID being replied to
        attachments (list): File attachments
        
    Returns:
        dict: Sent message info
    """
    try:
        current_user = frappe.session.user
        
        # Parse attachments if string
        if isinstance(attachments, str):
            attachments = json.loads(attachments) if attachments else []
            
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        if permissions.get("is_muted"):
            frappe.throw("You are muted in this chat room")
            
        # Create message
        message = frappe.new_doc("Chat Message")
        message.chat_room = room_id
        message.sender = current_user
        message.message_type = message_type
        message.message_content = message_content
        message.timestamp = now_datetime()
        
        if reply_to:
            message.reply_to_message = reply_to
            
        # Add attachments
        if attachments:
            for attachment in attachments:
                message.append("file_attachments", {
                    "file_name": attachment.get("file_name"),
                    "file_url": attachment.get("file_url"),
                    "file_type": attachment.get("file_type"),
                    "file_size": attachment.get("file_size", 0),
                    "uploaded_timestamp": now_datetime()
                })
        
        message.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "data": {
                "message_id": message.name,
                "timestamp": str(message.timestamp)
            },
            "message": "Message sent successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in send_message: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def add_reaction(message_id, emoji):
    """
    Add or remove reaction to a message
    
    Args:
        message_id (str): Message ID
        emoji (str): Reaction emoji
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get message and verify permissions
        message = frappe.get_doc("Chat Message", message_id)
        room = frappe.get_doc("Chat Room", message.chat_room)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Add/remove reaction
        message.add_reaction(current_user, emoji)
        
        return {
            "success": True,
            "message": "Reaction updated successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in add_reaction: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def edit_message(message_id, new_content):
    """
    Edit a message
    
    Args:
        message_id (str): Message ID
        new_content (str): New message content
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get message and edit it
        message = frappe.get_doc("Chat Message", message_id)
        message.edit_message(new_content, current_user)
        
        return {
            "success": True,
            "message": "Message edited successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in edit_message: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def delete_message(message_id):
    """
    Delete a message
    
    Args:
        message_id (str): Message ID
        
    Returns:
        dict: Success response
    """
    try:
        current_user = frappe.session.user
        
        # Get message and delete it
        message = frappe.get_doc("Chat Message", message_id)
        message.delete_message(current_user)
        
        return {
            "success": True,
            "message": "Message deleted successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in delete_message: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }