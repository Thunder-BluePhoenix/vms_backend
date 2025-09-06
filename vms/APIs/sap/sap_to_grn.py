import frappe
import json
from datetime import datetime

@frappe.whitelist(allow_guest=True)
def get_grn_field_mappings():
    doctype_name = frappe.db.get_value("SAP Mapper PR", {'doctype_name': 'GRN'}, "name")
    mappings = frappe.get_all('SAP Mapper PR Item', filters={'parent': doctype_name}, fields=['sap_field', 'erp_field'])
    return {mapping['sap_field']: mapping['erp_field'] for mapping in mappings}

@frappe.whitelist(allow_guest=True)
def get_grn():
    try:
        data = frappe.request.get_json()
        
        
        if not data or "items" not in data:
            return {"status": "error", "message": "No valid data received or 'items' key not found."}
        
        
        grn_no = data.get("MBLNR", "")
        
        if not grn_no:
            return {"status": "error", "message": "MBLNR (GRN Number) not found in the data."}
        
        field_mappings = get_grn_field_mappings()
        
        if not field_mappings:
            return {"status": "error", "message": "No field mappings found for 'SAP Mapper GRN.'"}
        
        is_existing_doc = frappe.db.exists("GRN", {"grn_number": grn_no})
        
        
        if is_existing_doc:
            grn_doc = frappe.get_doc("GRN", {"grn_number": grn_no})
        else:
            grn_doc = frappe.new_doc("GRN")
        
        meta = frappe.get_meta("GRN")
        grn_doc.grn_number = grn_no
        grn_doc.set("grn_items_table", [])
        
        
       
        header_data = {}
        for sap_field, erp_field in field_mappings.items():
            if sap_field in data:  
                value = data.get(sap_field, "")
                #
                field_meta = next((f for f in meta.fields if f.fieldname == erp_field), None)
                if field_meta and field_meta.fieldtype != "Table":
                    header_data[erp_field] = value
                    
        
        
        for field_name, value in header_data.items():
            grn_doc.set(field_name, value)
        
        
        for idx, item in enumerate(data["items"]):
            grn_item_data = {}
            
            
            for sap_field, erp_field in field_mappings.items():
                if sap_field in item:
                    value = item.get(sap_field, "")
                    grn_item_data[erp_field] = value
                    
            
            
            grn_doc.append("grn_items_table", grn_item_data)
        
        #
        if is_existing_doc:
            grn_doc.save()
            frappe.db.commit()
            return {"status": "success", "message": "GRN Updated Successfully.", "GRN": grn_doc.name}
        else:
            grn_doc.insert()
            frappe.db.commit()
            return {"status": "success", "message": "GRN Created Successfully.", "GRN": grn_doc.name}
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_grn Error")
        return {"status": "error", "message": str(e)}

def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None