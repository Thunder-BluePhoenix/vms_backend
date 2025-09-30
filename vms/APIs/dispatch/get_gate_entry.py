import frappe
from frappe import _
import json
import base64


#vms.APIs.dispatch.get_gate_entry.gate_entry_get
@frappe.whitelist(allow_guest=False)
def gate_entry_get(name=None, start=0, page_length=20):
    try:
        if name:
            if not frappe.db.exists("Gate Entry", name):
                return {"error": True, "message": f"Gate Entry '{name}' does not exist"}
            
            doc = frappe.get_doc("Gate Entry", name)
            return {
                "name": name,
                "data": get_gate_entry_data(doc)
            }
        else:
            data = frappe.get_list(
                "Gate Entry",
                fields=["*"],
                start=start,
                page_length=page_length,
                order_by="modified desc"
            )
            
            total_count = frappe.db.count("Gate Entry")
            
            return {
                "data": data,
                "pagination": {
                    "start": start,
                    "page_length": page_length,
                    "total_count": total_count
                }
            }
            
    except Exception as e:
        return {"error": True, "message": str(e)}



def get_gate_entry_data(doc):
    data = {}
    meta = frappe.get_meta("Gate Entry")
    
    exclude_fieldtypes = [
        "Section Break", "Column Break", "Tab Break", 
        "HTML", "Heading", "Fold", "Button"
    ]
    
    for field in meta.fields:
        if field.fieldtype in exclude_fieldtypes:
            continue
            
        field_name = field.fieldname
        value = getattr(doc, field_name, None)

        vehicle_details = []
        if hasattr(doc, 'vehicle_details_item') and doc.vehicle_details_item:  
            for vehicle_row in doc.vehicle_details_item:
                vehicle_link = vehicle_row.get('vehicle_details') 
                driver_name = vehicle_row.get('driver_name')
                driver_info = {"driver_name": driver_name} if driver_name else {}

                
                if vehicle_link:
                    try:
                        vehicle_doc = frappe.get_doc("Vehicle Details", vehicle_link) 
                        vehicle_info = {
                            "name": vehicle_doc.name,
                            "vehicle_no": vehicle_doc.get('vehicle_no'),
                            "driver_name": driver_name or vehicle_doc.get('driver_name'),
                            "driver_phone": vehicle_doc.get('driver_phone'),
                            "driver_license": vehicle_doc.get('driver_license'),
                            "loading_state": vehicle_doc.get('loading_state'),
                            "loading_location": vehicle_doc.get('loading_location'),
                            "transporter_name": vehicle_doc.get('transporter_name'),
                            "destination_plant": vehicle_doc.get('destination_plant'),
                            "lr_number": vehicle_doc.get('lr_number'),
                            "lr_date": vehicle_doc.get('lr_date'),
                            "vehicle_type": vehicle_doc.get('vehicle_type'),
                            "attachment": vehicle_doc.get('attachment')
                        }
                        vehicle_details.append(vehicle_info)
                       
                    except frappe.DoesNotExistError:
                        vehicle_details.append({"error": f"Vehicle {vehicle_link} not found"})
                    except Exception as vehicle_error:
                        vehicle_details.append({"error": str(vehicle_error)})
        
        
        # data["vehicle_details_item"] = vehicle_details
        
        if field.fieldtype == "Table" and value:
            child_data = []
            for child in value:
                child_dict = child.as_dict()
                child_data.append(child_dict)
            data[field_name] = child_data
       
        else:
            data[field_name] = value
        data["vehicle_details_item"] = vehicle_details
    
    return data
