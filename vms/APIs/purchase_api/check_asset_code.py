import frappe
from frappe import _

@frappe.whitelist(allow_guest=False, methods=['GET'])
def check_asset_code_availability(asset_code=None):
    try:
        
        if not asset_code:
            frappe.local.response['http_status_code'] = 400
            return {
                "status": "error",
                "message": _("Asset code parameter is required"),
                "asset_code": None
            }
        

        existing_asset = frappe.db.exists({
            "doctype": "Purchase Requisition Webform Table",  
            "main_asset_no_head": asset_code
        })
        
        if existing_asset:
            
            frappe.local.response['http_status_code'] = 400
            return {
                "status": "error",
                "message": _("Asset code already exists in Purchase Requisition"),
                "asset_code": asset_code,
                "exists": True
            }
        else:
            
            frappe.local.response['http_status_code'] = 200
            return {
                "status": "success",
                "message": _("Asset code is available"),
                "asset_code": asset_code,
                "exists": False
            }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Asset Code Check API Error"))
        frappe.local.response['http_status_code'] = 500
        return {
            "status": "error",
            "message": _("Internal server error: {0}").format(str(e)),
            "asset_code": asset_code
        }

