import frappe
from frappe.utils.file_manager import save_file
import base64
import os




def get_context(context):
	# do your magic here
	pass




# @frappe.whitelist(allow_guest=True)
# def simple_file_upload():
#     """
#     Simple file upload for webforms
#     """
#     try:
#         files = frappe.request.files
#         if not files or 'file' not in files:
#             return {"success": False, "message": "No file uploaded"}
        
#         file_obj = files['file']
        
#         # Set permissions flags
#         frappe.flags.ignore_permissions = True
        
#         # Save file using Frappe's built-in method
#         # from frappe.utils.file_manager import save_file
        
#         file_doc = save_file(
#             file_obj.filename,
#             file_obj.read(),
#             dt="Supplier QMS Assessment Form",  # Your doctype
#             dn=None,
#             folder="Home/Attachments",
#             decode=False,
#             is_private=0
#         )
        
#         return {
#             "success": True,
#             "file_url": file_doc.file_url,
#             "file_name": file_doc.file_name,
#             "name": file_doc.name
#         }
        
#     except Exception as e:
#         frappe.log_error(str(e))
#         return {"success": False, "message": str(e)}
    





# import frappe
# from frappe.utils.file_manager import save_file
# import os

# @frappe.whitelist(allow_guest=True)
# def bypass_upload_file():
#     """
#     Completely bypass Frappe's permission system for file uploads
#     """
#     try:
#         # Force administrator privileges temporarily
#         original_user = frappe.session.user
#         frappe.set_user("Administrator")
#         frappe.flags.ignore_permissions = True
        
#         # Get uploaded file
#         files = frappe.request.files
#         if not files or 'file' not in files:
#             frappe.throw("No file uploaded")
        
#         file_obj = files['file']
#         content = file_obj.read()
#         filename = file_obj.filename
        
#         # Save file with full permissions
#         file_doc = save_file(
#             filename,
#             content,
#             dt=frappe.form_dict.get('doctype'),
#             dn=frappe.form_dict.get('docname'), 
#             folder=frappe.form_dict.get('folder', 'Home/Attachments'),
#             decode=False,
#             is_private=int(frappe.form_dict.get('is_private', 0)),
#             df=frappe.form_dict.get('docfield')
#         )
        
#         frappe.db.commit()
        
#         # Restore original user
#         frappe.set_user(original_user)
        
#         return {
#             "file_name": file_doc.file_name,
#             "file_url": file_doc.file_url,
#             "name": file_doc.name
#         }
        
#     except Exception as e:
#         # Restore original user in case of error
#         if 'original_user' in locals():
#             frappe.set_user(original_user)
        
#         frappe.log_error(f"File upload bypass error: {str(e)}")
#         frappe.throw(f"File upload failed: {str(e)}")






import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def check_supplier_qms_filled(vendor_onboarding):
    if not vendor_onboarding:
        frappe.throw(_("vendor_onboarding is required."))

    existing = frappe.get_all(
        'Supplier QMS Assessment Form',
        filters={'vendor_onboarding': vendor_onboarding},
        limit=1
    )

    return {
        'exists': len(existing) > 0
    }




