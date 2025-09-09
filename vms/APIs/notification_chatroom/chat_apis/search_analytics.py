# vms/APIs/notification_chatroom/chat_apis/search_analytics.py
import frappe
from frappe import _
from frappe.utils import now_datetime, cint, get_datetime, add_days
import json

@frappe.whitelist()
def search_messages(room_id, search_term, page=1, page_size=20, message_type=None, 
                   from_date=None, to_date=None, sender=None):
    """
    Search messages in a chat room
    
    Args:
        room_id (str): Chat room ID
        search_term (str): Search term
        page (int): Page number
        page_size (int): Messages per page
        message_type (str): Filter by message type
        from_date (str): Start date for search
        to_date (str): End date for search
        sender (str): Filter by sender
        
    Returns:
        dict: Search results with pagination
    """
    try:
        current_user = frappe.session.user
        page = cint(page) or 1
        page_size = min(cint(page_size) or 20, 50)
        offset = (page - 1) * page_size
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Build search conditions
        conditions = [
            "chat_room = %(room_id)s",
            "is_deleted = 0"
        ]
        values = {"room_id": room_id}
        
        if search_term:
            conditions.append("message_content LIKE %(search_term)s")
            values["search_term"] = f"%{search_term}%"
            
        if message_type:
            conditions.append("message_type = %(message_type)s")
            values["message_type"] = message_type
            
        if from_date:
            conditions.append("timestamp >= %(from_date)s")
            values["from_date"] = get_datetime(from_date)
            
        if to_date:
            conditions.append("timestamp <= %(to_date)s")
            values["to_date"] = get_datetime(to_date)
            
        if sender:
            conditions.append("sender = %(sender)s")
            values["sender"] = sender
            
        where_clause = " AND ".join(conditions)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabChat Message`
            WHERE {where_clause}
        """
        
        total_count = frappe.db.sql(count_query, values, as_dict=True)[0].total
        
        # Get messages
        query = f"""
            SELECT 
                name,
                sender,
                message_type,
                message_content,
                timestamp,
                reply_to_message
            FROM `tabChat Message`
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        values.update({"limit": page_size, "offset": offset})
        messages = frappe.db.sql(query, values, as_dict=True)
        
        # Add sender info and attachments
        for message in messages:
            # Get sender info
            sender_info = frappe.db.get_value(
                "User",
                message.sender,
                ["full_name", "user_image"],
                as_dict=True
            )
            message["sender_info"] = sender_info or {"full_name": message.sender}
            
            # Get attachments
            message["attachments"] = frappe.get_all(
                "Chat Message Attachment",
                filters={"parent": message.name},
                fields=["file_name", "file_url", "file_type"]
            )
            
            message["timestamp"] = str(message.timestamp)
            
        # Pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": {
                "messages": messages,
                "search_term": search_term,
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
        frappe.log_error(f"Error in search_messages: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def get_chat_analytics(room_id, period="week"):
    """
    Get chat analytics for a room
    
    Args:
        room_id (str): Chat room ID
        period (str): Analysis period (day, week, month)
        
    Returns:
        dict: Analytics data
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        # Calculate date range
        end_date = now_datetime()
        if period == "day":
            start_date = add_days(end_date, -1)
        elif period == "week":
            start_date = add_days(end_date, -7)
        elif period == "month":
            start_date = add_days(end_date, -30)
        else:
            start_date = add_days(end_date, -7)  # Default to week
            
        # Get message statistics
        message_stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_messages,
                COUNT(DISTINCT sender) as active_users,
                AVG(CHAR_LENGTH(message_content)) as avg_message_length
            FROM `tabChat Message`
            WHERE chat_room = %(room_id)s 
                AND timestamp >= %(start_date)s 
                AND timestamp <= %(end_date)s
                AND is_deleted = 0
        """, {
            "room_id": room_id,
            "start_date": start_date,
            "end_date": end_date
        }, as_dict=True)[0]
        
        # Get message count by type
        message_by_type = frappe.db.sql("""
            SELECT 
                message_type,
                COUNT(*) as count
            FROM `tabChat Message`
            WHERE chat_room = %(room_id)s 
                AND timestamp >= %(start_date)s 
                AND timestamp <= %(end_date)s
                AND is_deleted = 0
            GROUP BY message_type
        """, {
            "room_id": room_id,
            "start_date": start_date,
            "end_date": end_date
        }, as_dict=True)
        
        # Get most active users
        most_active_users = frappe.db.sql("""
            SELECT 
                cm.sender,
                COUNT(*) as message_count,
                u.full_name
            FROM `tabChat Message` cm
            LEFT JOIN `tabUser` u ON cm.sender = u.name
            WHERE cm.chat_room = %(room_id)s 
                AND cm.timestamp >= %(start_date)s 
                AND cm.timestamp <= %(end_date)s
                AND cm.is_deleted = 0
            GROUP BY cm.sender
            ORDER BY message_count DESC
            LIMIT 10
        """, {
            "room_id": room_id,
            "start_date": start_date,
            "end_date": end_date
        }, as_dict=True)
        
        # Get daily message counts for chart
        daily_stats = frappe.db.sql("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as message_count,
                COUNT(DISTINCT sender) as unique_senders
            FROM `tabChat Message`
            WHERE chat_room = %(room_id)s 
                AND timestamp >= %(start_date)s 
                AND timestamp <= %(end_date)s
                AND is_deleted = 0
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, {
            "room_id": room_id,
            "start_date": start_date,
            "end_date": end_date
        }, as_dict=True)
        
        # Get file sharing stats
        file_stats = frappe.db.sql("""
            SELECT 
                COUNT(DISTINCT cm.name) as messages_with_files,
                COUNT(cma.name) as total_files,
                SUM(cma.file_size) as total_file_size
            FROM `tabChat Message` cm
            LEFT JOIN `tabChat Message Attachment` cma ON cm.name = cma.parent
            WHERE cm.chat_room = %(room_id)s 
                AND cm.timestamp >= %(start_date)s 
                AND cm.timestamp <= %(end_date)s
                AND cm.is_deleted = 0
                AND cma.name IS NOT NULL
        """, {
            "room_id": room_id,
            "start_date": start_date,
            "end_date": end_date
        }, as_dict=True)[0]
        
        return {
            "success": True,
            "data": {
                "period": period,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "message_stats": {
                    "total_messages": message_stats.total_messages or 0,
                    "active_users": message_stats.active_users or 0,
                    "avg_message_length": round(message_stats.avg_message_length or 0, 2)
                },
                "message_by_type": message_by_type,
                "most_active_users": most_active_users,
                "daily_stats": [
                    {
                        "date": str(stat.date),
                        "message_count": stat.message_count,
                        "unique_senders": stat.unique_senders
                    } for stat in daily_stats
                ],
                "file_stats": {
                    "messages_with_files": file_stats.messages_with_files or 0,
                    "total_files": file_stats.total_files or 0,
                    "total_file_size": file_stats.total_file_size or 0
                }
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_chat_analytics: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def get_global_chat_search(search_term, page=1, page_size=20):
    """
    Search across all accessible chat rooms
    
    Args:
        search_term (str): Search term
        page (int): Page number
        page_size (int): Results per page
        
    Returns:
        dict: Global search results
    """
    try:
        current_user = frappe.session.user
        page = cint(page) or 1
        page_size = min(cint(page_size) or 20, 50)
        offset = (page - 1) * page_size
        
        if not search_term:
            frappe.throw("Search term is required")
            
        # Get rooms user is member of
        user_rooms = frappe.db.sql("""
            SELECT DISTINCT parent as room_id
            FROM `tabChat Room Member`
            WHERE user = %(user)s
        """, {"user": current_user}, as_dict=True)
        
        if not user_rooms:
            return {
                "success": True,
                "data": {
                    "results": [],
                    "pagination": {
                        "total_count": 0,
                        "page": page,
                        "page_size": page_size,
                        "total_pages": 0,
                        "has_next": False,
                        "has_prev": False
                    }
                }
            }
            
        room_ids = [room.room_id for room in user_rooms]
        room_placeholders = ", ".join(["%s"] * len(room_ids))
        
        # Search messages across user's rooms
        query = f"""
            SELECT 
                cm.name,
                cm.chat_room,
                cm.sender,
                cm.message_type,
                cm.message_content,
                cm.timestamp,
                cr.room_name,
                cr.room_type,
                u.full_name as sender_name
            FROM `tabChat Message` cm
            LEFT JOIN `tabChat Room` cr ON cm.chat_room = cr.name
            LEFT JOIN `tabUser` u ON cm.sender = u.name
            WHERE cm.chat_room IN ({room_placeholders})
                AND cm.message_content LIKE %(search_term)s
                AND cm.is_deleted = 0
            ORDER BY cm.timestamp DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        values = room_ids + [f"%{search_term}%", page_size, offset]
        results = frappe.db.sql(query, values, as_dict=True)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabChat Message` cm
            WHERE cm.chat_room IN ({room_placeholders})
                AND cm.message_content LIKE %(search_term)s
                AND cm.is_deleted = 0
        """
        
        count_values = room_ids + [f"%{search_term}%"]
        total_count = frappe.db.sql(count_query, count_values, as_dict=True)[0].total
        
        # Format results
        for result in results:
            result["timestamp"] = str(result.timestamp)
            
            # Highlight search term in message content
            if result.message_content and search_term.lower() in result.message_content.lower():
                highlighted = result.message_content.replace(
                    search_term,
                    f"<mark>{search_term}</mark>"
                )
                result["highlighted_content"] = highlighted
            else:
                result["highlighted_content"] = result.message_content
                
        # Pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "success": True,
            "data": {
                "results": results,
                "search_term": search_term,
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
        frappe.log_error(f"Error in get_global_chat_search: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def export_chat_messages(room_id, from_date=None, to_date=None, format_type="json"):
    """
    Export chat messages for a room
    
    Args:
        room_id (str): Chat room ID
        from_date (str): Start date
        to_date (str): End date
        format_type (str): Export format (json, csv)
        
    Returns:
        dict: Export data or file
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is admin of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_admin"]:
            frappe.throw("Only admins can export chat messages")
            
        # Build conditions
        conditions = ["chat_room = %(room_id)s", "is_deleted = 0"]
        values = {"room_id": room_id}
        
        if from_date:
            conditions.append("timestamp >= %(from_date)s")
            values["from_date"] = get_datetime(from_date)
            
        if to_date:
            conditions.append("timestamp <= %(to_date)s")
            values["to_date"] = get_datetime(to_date)
            
        where_clause = " AND ".join(conditions)
        
        # Get messages
        query = f"""
            SELECT 
                cm.name,
                cm.sender,
                cm.message_type,
                cm.message_content,
                cm.timestamp,
                cm.is_edited,
                cm.edit_timestamp,
                u.full_name as sender_name
            FROM `tabChat Message` cm
            LEFT JOIN `tabUser` u ON cm.sender = u.name
            WHERE {where_clause}
            ORDER BY cm.timestamp ASC
        """
        
        messages = frappe.db.sql(query, values, as_dict=True)
        
        # Add attachments and reactions
        for message in messages:
            # Get attachments
            message["attachments"] = frappe.get_all(
                "Chat Message Attachment",
                filters={"parent": message.name},
                fields=["file_name", "file_url", "file_type", "file_size"]
            )
            
            # Get reactions
            message["reactions"] = frappe.get_all(
                "Chat Message Reaction",
                filters={"parent": message.name},
                fields=["user", "reaction_emoji", "timestamp"]
            )
            
            # Format timestamps
            message["timestamp"] = str(message.timestamp)
            if message.edit_timestamp:
                message["edit_timestamp"] = str(message.edit_timestamp)
                
        export_data = {
            "room_info": {
                "room_id": room.name,
                "room_name": room.room_name,
                "room_type": room.room_type,
                "export_date": str(now_datetime()),
                "exported_by": current_user,
                "message_count": len(messages)
            },
            "messages": messages
        }
        
        if format_type == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                "Timestamp", "Sender", "Sender Name", "Message Type", 
                "Message Content", "Is Edited", "Edit Timestamp", "Attachments", "Reactions"
            ])
            
            # Write data
            for message in messages:
                attachments_str = "; ".join([att["file_name"] for att in message["attachments"]])
                reactions_str = "; ".join([f"{r['user']}:{r['reaction_emoji']}" for r in message["reactions"]])
                
                writer.writerow([
                    message["timestamp"],
                    message["sender"],
                    message["sender_name"] or "",
                    message["message_type"],
                    message["message_content"] or "",
                    message["is_edited"],
                    message["edit_timestamp"] or "",
                    attachments_str,
                    reactions_str
                ])
                
            csv_content = output.getvalue()
            output.close()
            
            return {
                "success": True,
                "data": {
                    "format": "csv",
                    "content": csv_content,
                    "filename": f"chat_export_{room_id}_{now_datetime().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            }
        else:
            # Return JSON format
            return {
                "success": True,
                "data": {
                    "format": "json",
                    "content": export_data
                }
            }
            
    except Exception as e:
        frappe.log_error(f"Error in export_chat_messages: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }