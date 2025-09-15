import frappe
from frappe import _
import json
import base64

@frappe.whitelist(allow_guest=True)
def get_dispatch_data(data):
    try:
        data = json.loads(data) if isinstance(data, str) else data
        if not data:
            return {"error": True, "message": "No data provided"}

        name = data.get('doc_id')
        if name:
            doc = frappe.get_doc("Dispatch Item", name)
            return {
                "name": name,
                "data": doc.as_dict()
            }
            
    except Exception as e:
        return {"error": True, "message": str(e)}