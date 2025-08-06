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
    



#----------------------------------------------------------------------------------------To call erp to vms api from another instance
import frappe
import requests
import json
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True)
def send_to_vms_api(doc, method=None):
    """Send Material Request data to VMS API"""
    try:
        
        doc_dict = clean_doc_for_json(doc)
        
        # Prepare request data
        payload = {
            "raw_data": doc_dict,
            "source_system": f"ERPNext - {frappe.local.site}",
            "reference_id": doc.name
        }
        
        # API call
        headers = {
            'Content-Type': 'application/json',
            # 'Authorization': f'token {api_key}:{api_secret}'
        }
        
        url = f"http://127.0.0.1:8013/api/method/vms.APIs.sap.erp_to_vms_pr.create_vms_purchase_requisition"
        
        requests.post(url, json=payload, headers=headers, timeout=30)
        
            
    except Exception as e:
        frappe.log_error(f"Failed to sync Material Request {doc.name} to VMS: {str(e)}", "VMS Sync Error")

def clean_doc_for_json(doc):
    """Convert document to JSON-serializable dictionary"""
    from datetime import datetime, date, time, timedelta
    import decimal
    
    def convert_value(value):
        """Convert non-JSON serializable values to strings"""
        if isinstance(value, (datetime, date, time)):
            return str(value)
        elif isinstance(value, timedelta):
            return str(value)
        elif isinstance(value, decimal.Decimal):
            return float(value)
        elif hasattr(value, '__dict__'):
            # Handle frappe objects
            return str(value)
        elif isinstance(value, (list, tuple)):
            return [convert_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        else:
            return value
    
    # Get document as dictionary
    doc_dict = doc.as_dict()
    
    # Clean all values
    cleaned_dict = {}
    for key, value in doc_dict.items():
        cleaned_dict[key] = convert_value(value)
    
    return cleaned_dict



