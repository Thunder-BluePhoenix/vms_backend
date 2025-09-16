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
            dispatch_data = doc.as_dict()
            
            vendor_code = doc.get('vendor_code')  
            
            
            if vendor_code:
                try:
                    vendor_doc = frappe.get_doc("Company Vendor Code", vendor_code)
                    company_name = vendor_doc.company_name
                    vendor_name = vendor_doc.vendor_name
                    
                    
                    supplier_gst = None
                    if hasattr(vendor_doc, 'vendor_code') and vendor_doc.vendor_code:
                     
                        for row in vendor_doc.vendor_code:
                            if hasattr(row, 'gst_no') and row.gst_no:
                                supplier_gst = row.gst_no
                                break  
                    
                    
                    dispatch_data["company_name"] = company_name
                    dispatch_data["vendor_name"] = vendor_name
                    dispatch_data["supplier_gst"] = supplier_gst
                    
                except frappe.DoesNotExistError:
                    dispatch_data["company_name"] = None
                    dispatch_data["vendor_name"] = None
                    dispatch_data["supplier_gst"] = None
                    dispatch_data["vendor_error"] = "Vendor not found"
                except Exception as vendor_error:
                    dispatch_data["company_name"] = None
                    dispatch_data["vendor_name"] = None
                    dispatch_data["supplier_gst"] = None
                    dispatch_data["vendor_error"] = str(vendor_error)
            else:
                dispatch_data["company_name"] = None
                dispatch_data["vendor_name"] = None
                dispatch_data["supplier_gst"] = None
            
          
            vehicle_details = []
            if hasattr(doc, 'vehicle_details_item') and doc.vehicle_details_item:  
                for vehicle_row in doc.vehicle_details_item:
                    vehicle_link = vehicle_row.get('vehicle_details') 
                    
                    if vehicle_link:
                        try:
                            vehicle_doc = frappe.get_doc("Vehicle Details", vehicle_link) 
                            vehicle_info = {
                                "vehicle_no": vehicle_doc.get('vehicle_no'),
                                "driver_name": vehicle_doc.get('driver_name'),
                                "driver_phone": vehicle_doc.get('driver_phone')
                                
                            }
                            vehicle_details.append(vehicle_info)
                        except frappe.DoesNotExistError:
                            vehicle_details.append({"error": f"Vehicle {vehicle_link} not found"})
                        except Exception as vehicle_error:
                            vehicle_details.append({"error": str(vehicle_error)})
            
           
            dispatch_data["vehicle_details"] = vehicle_details
            
            return {
                "name": name,
                "data": dispatch_data
            }
            
    except Exception as e:
        return {"error": True, "message": str(e)}