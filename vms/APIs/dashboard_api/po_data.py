import frappe
import json


@frappe.whitelist(allow_guest = True)
def get_po():
    all_po = frappe.get_all("Purchase Order", fields ="*", order_by = "modified desc")
    return all_po



@frappe.whitelist(allow_guest = True)
def get_po_details(po_name):
    try:
        po = frappe.get_doc("Purchase Order", po_name)
        po_dict = po.as_dict()
        
      
        po_dict["requisitioner_email"] = None
        po_dict["requisitioner_name"] = None
        
        pr_no = po.get("ref_pr_no")
        
        if pr_no:
            
            pr_form_name = frappe.db.get_value("Purchase Requisition Form", {"sap_pr_code": pr_no}, "name")
            
            if pr_form_name:
                pr_doc = frappe.get_doc("Purchase Requisition Form", pr_form_name)
                purchase_requisitioner = pr_doc.get("requisitioner")
                
                if purchase_requisitioner:
                    
                    po_dict["requisitioner_email"] = purchase_requisitioner
                    
                    
                    requisitioner_name = frappe.get_value("User", purchase_requisitioner, "first_name") or frappe.get_value("User", purchase_requisitioner, "full_name")
                    po_dict["requisitioner_name"] = requisitioner_name

        return po_dict
        
    except frappe.DoesNotExistError:
        frappe.throw(f"Purchase Order '{po_name}' not found")
    except Exception as e:
        frappe.log_error(f"Error in get_po_details: {str(e)}")
        frappe.throw(f"An error occurred while fetching PO details: {str(e)}")


@frappe.whitelist(allow_guest = True)
def filtering_data(data):
    pass






# @frappe.whitelist(allow_guest=True)
# def get_po_details_withformat(po_name, po_format_name=None):
#     try:
#         # Check if PO exists
#         if not frappe.db.exists("Purchase Order", po_name):
#             raise frappe.DoesNotExistError(f"Purchase Order {po_name} not found")
        
#         # Validate permissions
#         if not frappe.has_permission("Purchase Order", "read"):
#             raise frappe.PermissionError("Insufficient permissions to read Purchase Order")
        
#         po = frappe.get_doc("Purchase Order", po_name)
        
#         # Update PO format if provided
#         if po_format_name:
#             # Validate write permission if updating
#             if not frappe.has_permission("Purchase Order", "write"):
#                 raise frappe.PermissionError("Insufficient permissions to update Purchase Order")
            
#             # Validate format exists
#             if not frappe.db.exists("PO PrintFormat Master", po_format_name):
#                 raise frappe.DoesNotExistError(f"Print Format {po_format_name} not found")
            
#             po.purchase_order_format = po_format_name
#             po.save()
#             frappe.db.commit()
        
#         po_dict = po.as_dict()
        
#         # Populate po_format_name from updated/existing field
#         po_dict["po_format_name"] = po.get("purchase_order_format")
        
#         # Initialize requisitioner fields
#         po_dict["requisitioner_email"] = None
#         po_dict["requisitioner_name"] = None
#         po_dict["sign_url1"] = None
#         po_dict["sign_url2"] = None
#         po_dict["sign_url3"] = None
        
#         pr_no = po.get("ref_pr_no")
        
#         if pr_no:
#             pr_form_name = frappe.db.get_value("Purchase Requisition Form", {"sap_pr_code": pr_no}, "name")
            
#             if pr_form_name:
#                 pr_doc = frappe.get_doc("Purchase Requisition Form", pr_form_name)
#                 purchase_requisitioner = pr_doc.get("requisitioner")
                
#                 if purchase_requisitioner:
#                     po_dict["requisitioner_email"] = purchase_requisitioner
#                     requisitioner_name = frappe.get_value("User", purchase_requisitioner, "first_name") or frappe.get_value("User", purchase_requisitioner, "full_name")
#                     po_dict["requisitioner_name"] = requisitioner_name


#         if po.sign_of_approval1:
#             file_doc = frappe.get_doc("File", {"file_url": po.sign_of_approval1})
#             po_dict["sign_url1"] = {
#                 "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
#                 "name": file_doc.name,
#                 "file_name": file_doc.file_name

#             }
#         if po.sign_of_approval2:
#             file_doc = frappe.get_doc("File", {"file_url": po.sign_of_approval2})
#             po_dict["sign_url2"] = {
#                 "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
#                 "name": file_doc.name,
#                 "file_name": file_doc.file_name

#             }
#         if po.sign_of_approval3:
#             file_doc = frappe.get_doc("File", {"file_url": po.sign_of_approval3})
#             po_dict["sign_url3"] = {
#                 "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
#                 "name": file_doc.name,
#                 "file_name": file_doc.file_name

#             }

        
#         # Success response
#         frappe.response["http_status_code"] = 200
#         return {
#             "success": True,
#             "message": f"PO details retrieved{' and format updated' if po_format_name else ''} successfully",
#             "data": po_dict
#         }
        
#     except Exception as e:
#         frappe.db.rollback()
#         return handle_api_exception(e, "PO Details API")
    






def handle_api_exception(e, operation_name="API Operation"):
    """Dynamic exception handler for Frappe APIs"""
    
    # Get exception type and name
    exc_type = type(e)
    exc_name = exc_type.__name__
    
    # Dynamic mapping based on exception name patterns
    status_code = 500
    error_type = "Internal server error"
    default_message = "An unexpected error occurred"
    
    # Check frappe exception types dynamically
    if hasattr(frappe, exc_name):
        if "NotFound" in exc_name or "DoesNotExist" in exc_name:
            status_code = 404
            error_type = "Resource not found"
            default_message = "The requested resource does not exist"
        elif "Permission" in exc_name:
            status_code = 403
            error_type = "Permission denied"
            default_message = "You don't have permission to access this resource"
        elif "Validation" in exc_name:
            status_code = 400
            error_type = "Validation error"
            default_message = "Invalid data provided"
        elif "Data" in exc_name:
            status_code = 400
            error_type = "Data error"
            default_message = "Invalid field or data structure"
        elif "Duplicate" in exc_name:
            status_code = 409
            error_type = "Duplicate entry"
            default_message = "Resource already exists"
        elif "Link" in exc_name:
            status_code = 400
            error_type = "Link validation error"
            default_message = "Invalid link reference"
    
    # Set HTTP status code
    frappe.response["http_status_code"] = status_code
    
    # Log error with operation context
    log_title = f"{operation_name} - {error_type}"
    frappe.log_error(frappe.get_traceback(), log_title)
    
    # Return structured error response
    return {
        "success": False,
        "error": error_type,
        "message": f"{default_message}: {str(e)}" if str(e) else default_message,
        "exception_type": exc_name
    }




import base64
import mimetypes
import os

@frappe.whitelist(allow_guest=True)
def get_po_details_withformat(po_name, po_format_name=None):
    try:
        # Check if PO exists
        if not frappe.db.exists("Purchase Order", po_name):
            raise frappe.DoesNotExistError(f"Purchase Order {po_name} not found")
        
        # Validate permissions
        if not frappe.has_permission("Purchase Order", "read"):
            raise frappe.PermissionError("Insufficient permissions to read Purchase Order")
        
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Update PO format if provided
        if po_format_name:
            # Validate write permission if updating
            if not frappe.has_permission("Purchase Order", "write"):
                raise frappe.PermissionError("Insufficient permissions to update Purchase Order")
            
            # Validate format exists
            if not frappe.db.exists("PO PrintFormat Master", po_format_name):
                raise frappe.DoesNotExistError(f"Print Format {po_format_name} not found")
            
            po.purchase_order_format = po_format_name
            po.save()
            frappe.db.commit()
        
        po_dict = po.as_dict()
        
        # Populate po_format_name from updated/existing field
        po_dict["po_format_name"] = po.get("purchase_order_format")
        
        # Initialize requisitioner fields
        po_dict["requisitioner_email"] = None
        po_dict["requisitioner_name"] = None
        po_dict["sign_url1"] = None
        po_dict["sign_url2"] = None
        po_dict["sign_url3"] = None
        
        pr_no = po.get("ref_pr_no")
        
        if pr_no:
            pr_form_name = frappe.db.get_value("Purchase Requisition Form", {"sap_pr_code": pr_no}, "name")
            
            if pr_form_name:
                pr_doc = frappe.get_doc("Purchase Requisition Form", pr_form_name)
                purchase_requisitioner = pr_doc.get("requisitioner")
                
                if purchase_requisitioner:
                    po_dict["requisitioner_email"] = purchase_requisitioner
                    requisitioner_name = frappe.get_value("User", purchase_requisitioner, "first_name") or frappe.get_value("User", purchase_requisitioner, "full_name")
                    po_dict["requisitioner_name"] = requisitioner_name

        # Helper function to get file data with base64
        def get_file_data_with_base64(file_url):
            try:
                file_doc = frappe.get_doc("File", {"file_url": file_url})
                
                # Get the full file path
                file_path = frappe.get_site_path() + file_doc.file_url
                
                # Initialize base64 data
                base64_data = None
                mime_type = None
                
                # Read file and convert to base64 if it exists
                if os.path.exists(file_path):
                    with open(file_path, "rb") as file:
                        file_content = file.read()
                        base64_data = base64.b64encode(file_content).decode('utf-8')
                        
                    # Get MIME type
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if not mime_type:
                        # Default to common image types if unable to detect
                        file_ext = os.path.splitext(file_doc.file_name)[1].lower()
                        mime_type_map = {
                            '.png': 'image/png',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.gif': 'image/gif',
                            '.pdf': 'application/pdf'
                        }
                        mime_type = mime_type_map.get(file_ext, 'application/octet-stream')
                
                return {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name,
                    "base64": base64_data,
                    "mime_type": mime_type,
                    "data_url": f"data:{mime_type};base64,{base64_data}" if base64_data and mime_type else None
                }
            except Exception as e:
                frappe.log_error(f"Error processing file {file_url}: {str(e)}", "File Base64 Conversion")
                return {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_url}",
                    "name": None,
                    "file_name": None,
                    "base64": None,
                    "mime_type": None,
                    "data_url": None,
                    "error": f"Failed to process file: {str(e)}"
                }

        # Process signature files with base64 conversion
        if po.sign_of_approval1:
            po_dict["sign_url1"] = get_file_data_with_base64(po.sign_of_approval1)
            
        if po.sign_of_approval2:
            po_dict["sign_url2"] = get_file_data_with_base64(po.sign_of_approval2)
            
        if po.sign_of_approval3:
            po_dict["sign_url3"] = get_file_data_with_base64(po.sign_of_approval3)
        
        # Success response
        frappe.response["http_status_code"] = 200
        return {
            "success": True,
            "message": f"PO details retrieved{' and format updated' if po_format_name else ''} successfully",
            "data": po_dict
        }
        
    except Exception as e:
        frappe.db.rollback()
        return handle_api_exception(e, "PO Details API")