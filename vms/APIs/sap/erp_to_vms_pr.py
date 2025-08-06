import frappe
import json
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_vms_purchase_requisition():
    try:
        data = frappe.local.form_dict
        
        if not data.get('raw_data'):
            frappe.throw(_("raw_data is required"))
        
        raw_data_content = data.get('raw_data')
        
        if isinstance(raw_data_content, dict):
            raw_data_json = json.dumps(raw_data_content, indent=2, default=str)
        else:
            raw_data_json = str(raw_data_content)
        
        if isinstance(raw_data_content, dict):
            raw_data_content['_sync_metadata'] = {
                'received_at': str(now_datetime()),
                'source_system': data.get('source_system', 'Unknown'),
                'reference_id': data.get('reference_id', ''),
                'api_version': '1.0'
            }
            raw_data_json = json.dumps(raw_data_content, indent=2, default=str)
        
        vms_pr = frappe.get_doc({
            "doctype": "ERP To VMS Purchase Requisition",
            "raw_data": raw_data_json
        })
        
        vms_pr.insert(ignore_permissions=True)
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "ERP To VMS Purchase Requisition created successfully",
            "data": {
                "name": vms_pr.name,
                "creation": str(vms_pr.creation),
                "source_system": data.get('source_system', 'Unknown'),
                "reference_id": data.get('reference_id', '')
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "VMS Purchase Requisition Creation Error")
        frappe.db.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    
