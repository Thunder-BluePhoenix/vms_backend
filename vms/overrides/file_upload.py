# Step 1: Create the override file
# File: apps/your_custom_app/your_custom_app/file_overrides.py

import frappe
from frappe.utils.file_manager import save_file
import os

@frappe.whitelist(allow_guest=True)
def custom_upload_file():
    """
    Custom upload file method that bypasses all permissions
    """
    try:
        # Store original user and set admin privileges
        original_user = frappe.session.user
        frappe.set_user("Administrator")
        frappe.flags.ignore_permissions = True
        
        # Get uploaded file from request
        files = frappe.request.files
        if not files or 'file' not in files:
            frappe.throw("No file uploaded")
        
        file_obj = files['file']
        content = file_obj.read()
        filename = file_obj.filename
        
        # Get form parameters
        doctype = frappe.form_dict.get('doctype')
        docname = frappe.form_dict.get('docname')
        folder = frappe.form_dict.get('folder', 'Home/Attachments')
        is_private = int(frappe.form_dict.get('is_private', 0))
        docfield = frappe.form_dict.get('docfield')
        
        # Save file with admin privileges
        file_doc = save_file(
            filename,
            content,
            dt=doctype,
            dn=docname,
            folder=folder,
            decode=False,
            is_private=is_private,
            df=docfield
        )
        
        # Commit the transaction
        frappe.db.commit()
        
        # Restore original user
        frappe.set_user(original_user)
        
        return {
            "file_name": file_doc.file_name,
            "file_url": file_doc.file_url,
            "name": file_doc.name,
            "is_private": file_doc.is_private
        }
        
    except Exception as e:
        # Restore original user in case of error
        if 'original_user' in locals():
            frappe.set_user(original_user)
        
        frappe.log_error(f"Custom upload file error: {str(e)}")
        frappe.throw(f"File upload failed: {str(e)}")

# Alternative method if the above doesn't work
@frappe.whitelist(allow_guest=True)
def bypass_upload_file():
    """
    Complete bypass of the original upload_file method
    """
    try:
        # Import the original upload_file function
        from frappe.handler import upload_file as original_upload_file
        
        # Temporarily elevate permissions
        frappe.flags.ignore_permissions = True
        original_user = frappe.session.user
        frappe.session.user = "Administrator"
        
        try:
            # Call the original upload_file with elevated permissions
            result = original_upload_file()
            return result
        finally:
            # Always restore the original user
            frappe.session.user = original_user
            
    except Exception as e:
        frappe.log_error(f"Bypass upload error: {str(e)}")
        frappe.throw(f"Upload failed: {str(e)}")

# Method for handling web form uploads specifically
@frappe.whitelist(allow_guest=True)
def webform_upload_file():
    """
    Specific method for webform file uploads
    """
    try:
        # Force admin session for uploads
        frappe.session.user = "Administrator"
        frappe.flags.ignore_permissions = True
        frappe.flags.ignore_user_permissions = True
        
        files = frappe.request.files
        if not files:
            return {"error": "No files uploaded"}
        
        uploaded_files = []
        
        for field_name, file_obj in files.items():
            if file_obj.filename:
                content = file_obj.read()
                
                # Save file
                file_doc = save_file(
                    file_obj.filename,
                    content,
                    dt=None,  # No specific doctype
                    dn=None,  # No specific document
                    folder="Home/Attachments",
                    decode=False,
                    is_private=0
                )
                
                uploaded_files.append({
                    "field_name": field_name,
                    "file_name": file_doc.file_name,
                    "file_url": file_doc.file_url,
                    "name": file_doc.name
                })
        
        frappe.db.commit()
        
        # Return first file if only one, otherwise return all
        if len(uploaded_files) == 1:
            return uploaded_files[0]
        else:
            return {"files": uploaded_files}
            
    except Exception as e:
        frappe.log_error(f"Webform upload error: {str(e)}")
        return {"error": str(e)}

# Step 2: Update your hooks.py file
# File: apps/your_custom_app/your_custom_app/hooks.py

app_name = "your_custom_app"
app_title = "Your Custom App"
app_publisher = "Your Company"
app_description = "Your app description"
app_email = "your.email@company.com"
app_license = "MIT"

# Override the upload_file method
override_whitelisted_methods = {
    "upload_file": "vms.overrides.file_upload.custom_upload_file",
    "frappe.handler.upload_file": "vms/overrides.file_upload.custom_upload_file"
}

# Alternative: You can also override multiple methods
# override_whitelisted_methods = {
#     "upload_file": "your_custom_app.file_overrides.custom_upload_file",
#     "frappe.handler.upload_file": "your_custom_app.file_overrides.bypass_upload_file",
#     "frappe.core.doctype.file.file.upload_file": "your_custom_app.file_overrides.webform_upload_file"
# }

# Optional: Additional document events for file handling
doc_events = {
    "File": {
        "before_insert": "vms.overrides.file_upload.before_file_insert"
    }
}

# Step 3: Additional helper functions for file handling
# Add these to the same file_overrides.py

def before_file_insert(doc, method):
    """
    Hook to bypass permissions for file insertion
    """
    if frappe.session.user == "Guest":
        doc.flags.ignore_permissions = True
        frappe.flags.ignore_permissions = True

@frappe.whitelist(allow_guest=True)
def get_upload_url():
    """
    Get the correct upload URL for the webform
    """
    return "/api/method/vms.overrides.file_upload.custom_upload_file"

# Step 4: Complete working example with error handling
@frappe.whitelist(allow_guest=True)
def robust_upload_file():
    """
    Most robust upload method with comprehensive error handling
    """
    response = {"success": False, "message": "", "file_url": "", "file_name": ""}
    
    try:
        # Check if files exist in request
        if not hasattr(frappe.local, 'request') or not frappe.request.files:
            response["message"] = "No files found in request"
            return response
        
        files = frappe.request.files
        if 'file' not in files:
            response["message"] = "No file field found"
            return response
        
        file_obj = files['file']
        if not file_obj or not file_obj.filename:
            response["message"] = "Empty file uploaded"
            return response
        
        # Set maximum file size (10MB)
        max_size = 25 * 1024 * 1024  # 10MB
        file_obj.seek(0, 2)  # Seek to end
        file_size = file_obj.tell()
        file_obj.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            response["message"] = "File too large. Maximum size is 25MB"
            return response
        
        # Read file content
        content = file_obj.read()
        filename = file_obj.filename
        
        # Force admin privileges
        original_user = frappe.session.user
        frappe.session.user = "Administrator"
        frappe.flags.ignore_permissions = True
        frappe.flags.ignore_user_permissions = True
        
        # Save file
        file_doc = save_file(
            filename,
            content,
            dt=None,
            dn=None,
            folder="Home/Attachments",
            decode=False,
            is_private=0
        )
        
        # Commit changes
        frappe.db.commit()
        
        # Restore original user
        frappe.session.user = original_user
        
        # Success response
        response.update({
            "success": True,
            "message": "File uploaded successfully",
            "file_url": file_doc.file_url,
            "file_name": file_doc.file_name,
            "name": file_doc.name
        })
        
        return response
        
    except Exception as e:
        # Restore user session if changed
        if 'original_user' in locals():
            frappe.session.user = original_user
        
        error_msg = str(e)
        frappe.log_error(f"Robust upload error: {error_msg}")
        
        response.update({
            "success": False,
            "message": f"Upload failed: {error_msg}"
        })
        
        return response