# notification_log_api.py
# Add this to your custom app's api folder

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, strip_html_tags
import json
import re




def clean_html_content(html_content):
    """
    Clean HTML content by removing tags and formatting properly
    
    Args:
        html_content (str): HTML content to clean
        
    Returns:
        str: Clean text content
    """
    if not html_content:
        return ""
    
    # Remove HTML tags using frappe's built-in function
    clean_text = strip_html_tags(html_content)
    
    # Remove extra whitespaces and newlines
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Remove leading/trailing whitespace
    clean_text = clean_text.strip()
    
    return clean_text


@frappe.whitelist(allow_guest=True)
def get_notifications(page=1, page_size=20, read_status=None, search=None):
    """
    Fetch all notifications for the current user with pagination (HTML content stripped)
    
    Args:
        page (int): Page number (default: 1)
        page_size (int): Number of records per page (default: 20, max: 100)
        read_status (str): Filter by read status ('0' for unread, '1' for read, None for all)
        search (str): Search in subject field
    
    Returns:
        dict: Notifications with clean text content
    """
    try:
        # Input validation
        page = cint(page) if page else 1
        page_size = cint(page_size) if page_size else 20
        
        # Validate page number
        if page < 1:
            page = 1
            
        # Limit page size to prevent abuse
        if page_size < 1:
            page_size = 20
        elif page_size > 100:
            page_size = 100
            
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build filters
        filters = {
            'for_user': frappe.session.user
        }
        
        # Add read status filter if provided
        if read_status is not None:
            if read_status in ['0', '1']:
                filters['read'] = cint(read_status)
            else:
                frappe.throw(_("Invalid read_status. Use '0' for unread or '1' for read"))
        
        # Build query conditions
        conditions = []
        values = []
        
        for key, value in filters.items():
            conditions.append(f"`{key}` = %s")
            values.append(value)
            
        # Add search condition
        if search:
            conditions.append("(`subject` LIKE %s OR `email_content` LIKE %s)")
            search_term = f"%{search}%"
            values.extend([search_term, search_term])
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(*) as total 
            FROM `tabNotification Log` 
            WHERE {where_clause}
        """
        
        total_count = frappe.db.sql(count_query, values, as_dict=True)[0].total
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        # Main query to fetch notifications
        query = f"""
            SELECT 
                name,
                subject,
                email_content,
                `read`,
                creation,
                modified,
                for_user,
                from_user,
                type,
                document_type,
                document_name,
                attached_file
            FROM `tabNotification Log` 
            WHERE {where_clause}
            ORDER BY creation DESC
            LIMIT %s OFFSET %s
        """
        
        # Add limit and offset to values
        query_values = values + [page_size, offset]
        
        # Execute query
        notifications = frappe.db.sql(query, query_values, as_dict=True)
        
        # Format the response and clean HTML content
        for notification in notifications:
            # Convert datetime to string for JSON serialization
            if notification.get('creation'):
                notification['creation'] = str(notification['creation'])
            if notification.get('modified'):
                notification['modified'] = str(notification['modified'])
                
            # Convert read field to boolean
            notification['read'] = bool(notification.get('read'))
            
            # Clean HTML content
            if notification.get('email_content'):
                notification['content'] = clean_html_content(notification['email_content'])
                # Create preview (first 200 characters)
                notification['content_preview'] = notification['content'][:200] + '...' if len(notification['content']) > 200 else notification['content']
            else:
                notification['content'] = ''
                notification['content_preview'] = ''
            
            # Remove the original email_content field to avoid confusion
            notification.pop('email_content', None)
        
        return {
            'success': True,
            'data': {
                'notifications': notifications,
                'pagination': {
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                }
            }
        }
        
    except frappe.PermissionError:
        frappe.local.response['http_status_code'] = 403
        return {
            'success': False,
            'error': {
                'code': 'PERMISSION_DENIED',
                'message': _('You do not have permission to access notifications')
            }
        }
        
    except frappe.ValidationError as e:
        frappe.local.response['http_status_code'] = 400
        return {
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_notifications API: {str(e)}")
        frappe.local.response['http_status_code'] = 500
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': _('An internal error occurred while fetching notifications')
            }
        }


@frappe.whitelist()
def mark_notification_read(notification_id):
    """
    Mark a specific notification as read
    
    Args:
        notification_id (str): Name/ID of the notification log
        
    Returns:
        dict: Success/error response
    """
    try:
        if not notification_id:
            frappe.throw(_("Notification ID is required"))
            
        # Check if notification exists and belongs to current user
        notification = frappe.get_doc("Notification Log", notification_id)
        
        if notification.for_user != frappe.session.user:
            frappe.throw(_("You can only mark your own notifications as read"))
            
        # Update read status
        notification.read = 1
        notification.save(ignore_permissions=True)
        
        return {
            'success': True,
            'message': _('Notification marked as read')
        }
        
    except frappe.DoesNotExistError:
        frappe.local.response['http_status_code'] = 404
        return {
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': _('Notification not found')
            }
        }
        
    except frappe.PermissionError:
        frappe.local.response['http_status_code'] = 403
        return {
            'success': False,
            'error': {
                'code': 'PERMISSION_DENIED',
                'message': _('You do not have permission to modify this notification')
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in mark_notification_read API: {str(e)}")
        frappe.local.response['http_status_code'] = 500
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': _('An internal error occurred while updating notification')
            }
        }


@frappe.whitelist()
def mark_all_notifications_read():
    """
    Mark all notifications as read for the current user
    
    Returns:
        dict: Success/error response
    """
    try:
        # Update all unread notifications for current user
        frappe.db.sql("""
            UPDATE `tabNotification Log` 
            SET `read` = 1 
            WHERE for_user = %s AND `read` = 0
        """, (frappe.session.user,))
        
        frappe.db.commit()
        
        return {
            'success': True,
            'message': _('All notifications marked as read')
        }
        
    except Exception as e:
        frappe.log_error(f"Error in mark_all_notifications_read API: {str(e)}")
        frappe.local.response['http_status_code'] = 500
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': _('An internal error occurred while updating notifications')
            }
        }


@frappe.whitelist()
def get_notification_counts():
    """
    Get unread and total notification counts for the current user
    
    Returns:
        dict: {
            'unread_count': number of unread notifications,
            'total_count': total number of notifications
        }
    """
    try:
        user = frappe.session.user
        
        # Get counts
        counts = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN `read` = 0 THEN 1 ELSE 0 END) as unread_count
            FROM `tabNotification Log` 
            WHERE for_user = %s
        """, (user,), as_dict=True)[0]
        
        return {
            'success': True,
            'data': {
                'unread_count': int(counts.unread_count or 0),
                'total_count': int(counts.total_count or 0)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_notification_counts API: {str(e)}")
        frappe.local.response['http_status_code'] = 500
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': _('An internal error occurred while fetching notification counts')
            }
        }





@frappe.whitelist()
def get_notification_detail(notification_name):
    """
    Get notification detail by name and mark it as read (HTML content stripped)
    
    Args:
        notification_name (str): Name/ID of the notification log record
        
    Returns:
        dict: Notification record with clean text content
    """
    try:
        # Validate input
        if not notification_name:
            frappe.throw(_("Notification name is required"))
            
        # Check if notification exists
        if not frappe.db.exists("Notification Log", notification_name):
            frappe.local.response['http_status_code'] = 404
            return {
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': _('Notification not found')
                }
            }
            
        # Get the notification record
        notification = frappe.get_doc("Notification Log", notification_name)
        
        # Check if notification belongs to current user
        if notification.for_user != frappe.session.user:
            frappe.local.response['http_status_code'] = 403
            return {
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': _('You can only access your own notifications')
                }
            }
            
        # Mark notification as read if not already read
        was_unread = not notification.read
        if was_unread:
            frappe.db.set_value("Notification Log", notification_name, "read", 1)
            frappe.db.commit()
            
        # Prepare response data with cleaned HTML content
        notification_data = {
            'name': notification.name,
            'subject': notification.subject,
            'content': clean_html_content(notification.email_content),  # Cleaned content
            'read': True if was_unread else bool(notification.read),  # True if we just marked it read
            'creation': str(notification.creation),
            'modified': str(notification.modified),
            'for_user': notification.for_user,
            'from_user': notification.from_user,
            'type': notification.type,
            'document_type': notification.document_type,
            'document_name': notification.document_name,
            'attached_file': notification.attached_file,
            'link': notification.link if hasattr(notification, 'link') else None,
            'seen': notification.seen if hasattr(notification, 'seen') else None,
            'email_sent_to': notification.email_sent_to if hasattr(notification, 'email_sent_to') else None,
            'sent_email': notification.sent_email if hasattr(notification, 'sent_email') else None
        }
        
        return {
            'success': True,
            'data': notification_data,
            'message': _('Notification retrieved and marked as read')
        }
        
    except frappe.PermissionError:
        frappe.local.response['http_status_code'] = 403
        return {
            'success': False,
            'error': {
                'code': 'PERMISSION_DENIED',
                'message': _('You do not have permission to access this notification')
            }
        }
        
    except frappe.ValidationError as e:
        frappe.local.response['http_status_code'] = 400
        return {
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_notification_detail API: {str(e)}")
        frappe.local.response['http_status_code'] = 500
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': _('An internal error occurred while fetching notification details')
            }
        }
    



@frappe.whitelist()
def mark_all_notifications_read():
    """
    Mark all notifications as read for the current user
    
    Returns:
        dict: {
            'success': boolean,
            'message': success message,
            'data': {
                'updated_count': number of notifications marked as read
            },
            'error': error details if any
        }
    """
    try:
        current_user = frappe.session.user
        
        if not current_user:
            frappe.throw(_("User session not found"))
        
        # Get count of unread notifications before updating
        unread_count = frappe.db.count("Notification Log", {
            "for_user": current_user,
            "read": 0
        })
        
        if unread_count == 0:
            return {
                'success': True,
                'message': _('No unread notifications found'),
                'data': {
                    'updated_count': 0,
                    'total_notifications': frappe.db.count("Notification Log", {"for_user": current_user})
                }
            }
        
        # Update all unread notifications for current user
        frappe.db.sql("""
            UPDATE `tabNotification Log` 
            SET `read` = 1 
            WHERE for_user = %s AND `read` = 0
        """, (current_user,))
        
        # Commit the transaction
        frappe.db.commit()
        
        # Get total count after update
        total_count = frappe.db.count("Notification Log", {"for_user": current_user})
        
        return {
            'success': True,
            'message': _('All notifications marked as read successfully'),
            'data': {
                'updated_count': unread_count,
                'total_notifications': total_count
            }
        }
        
    except frappe.PermissionError:
        frappe.local.response['http_status_code'] = 403
        return {
            'success': False,
            'error': {
                'code': 'PERMISSION_DENIED',
                'message': _('You do not have permission to update notifications')
            }
        }
        
    except frappe.ValidationError as e:
        frappe.local.response['http_status_code'] = 400
        return {
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in mark_all_notifications_read API: {str(e)}")
        frappe.local.response['http_status_code'] = 500
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': _('An internal error occurred while updating notifications')
            }
        }
