# vms/APIs/notification_chatroom/chat_apis/file_upload.py
import frappe
from frappe import _
from frappe.utils import now_datetime, get_files_path
from frappe.core.doctype.file.file import save_file
import os
import mimetypes

@frappe.whitelist()
def upload_chat_file(room_id):
    """
    Upload file for chat message
    
    Args:
        room_id (str): Chat room ID
        
    Returns:
        dict: File upload response
    """
    try:
        current_user = frappe.session.user
        
        # Verify user is member of the room
        room = frappe.get_doc("Chat Room", room_id)
        permissions = room.get_member_permissions(current_user)
        
        if not permissions["is_member"]:
            frappe.throw("You are not a member of this chat room")
            
        if not room.allow_file_sharing:
            frappe.throw("File sharing is not allowed in this room")
            
        # Get uploaded file
        files = frappe.request.files
        if not files:
            frappe.throw("No file uploaded")
            
        uploaded_files = []
        
        for fieldname, file_obj in files.items():
            if not file_obj.filename:
                continue
                
            # Validate file size (10MB limit)
            file_obj.seek(0, os.SEEK_END)
            file_size = file_obj.tell()
            file_obj.seek(0)
            
            if file_size > 25 * 1024 * 1024:  # 10MB
                frappe.throw(f"File {file_obj.filename} is too large. Maximum size is 10MB")
                
            # Get file content
            content = file_obj.read()
            
            # Determine file type
            file_type = mimetypes.guess_type(file_obj.filename)[0] or "application/octet-stream"
            
            # Create unique filename to prevent conflicts
            timestamp = now_datetime().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(file_obj.filename)[1]
            unique_filename = f"chat_{room_id}_{timestamp}_{file_obj.filename}"
            
            # Save file
            file_doc = save_file(
                unique_filename,
                content,
                dt="Chat Message",
                dn=None,
                folder="Home/Chat_Files",
                decode=False,
                is_private=1 if room.is_private else 0
            )
            
            uploaded_files.append({
                "file_name": file_obj.filename,
                "file_url": file_doc.file_url,
                "file_type": file_type,
                "file_size": file_size,
                "unique_filename": unique_filename,
                "file_doc_name": file_doc.name
            })
            
        return {
            "success": True,
            "data": {
                "files": uploaded_files
            },
            "message": f"Uploaded {len(uploaded_files)} file(s) successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in upload_chat_file: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }

@frappe.whitelist()
def get_chat_file_preview(file_url):
    """
    Get file preview/metadata
    
    Args:
        file_url (str): File URL
        
    Returns:
        dict: File preview data
    """
    try:
        # Get file document
        file_doc = frappe.get_all(
            "File",
            filters={"file_url": file_url},
            fields=["name", "file_name", "file_size", "file_type", "creation"],
            limit=1
        )
        
        if not file_doc:
            frappe.throw("File not found")
            
        file_info = file_doc[0]
        
        # Determine if file is image for preview
        is_image = file_info.file_type and file_info.file_type.startswith("image/")
        
        # Get file size in human readable format
        def format_file_size(size_bytes):
            if size_bytes == 0:
                return "0B"
            size_name = ["B", "KB", "MB", "GB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_name) - 1:
                size_bytes /= 1024.0
                i += 1
            return f"{size_bytes:.1f}{size_name[i]}"
            
        return {
            "success": True,
            "data": {
                "file_name": file_info.file_name,
                "file_size": file_info.file_size,
                "file_size_formatted": format_file_size(file_info.file_size or 0),
                "file_type": file_info.file_type,
                "is_image": is_image,
                "can_preview": is_image,
                "upload_date": str(file_info.creation),
                "preview_url": file_url if is_image else None
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_chat_file_preview: {str(e)}")
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }