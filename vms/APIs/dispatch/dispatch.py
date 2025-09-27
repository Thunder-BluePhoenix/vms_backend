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
            
            # Remove unwanted fields from dispatch_data
            fields_to_remove = [
                'vehicle_details_item','qr_code_generated','qr_generation_date','qr_code_image','qr_code_data'
            ]
            
            for field in fields_to_remove:
                dispatch_data.pop(field, None)  

            if "items" in dispatch_data:
                dispatch_data["gate_entry_details"] = dispatch_data.pop("items")
            
            vendor_code = doc.get('vendor_code')  
            
            if vendor_code:
                try:
                    vendor_doc = frappe.get_doc("Company Vendor Code", vendor_code)
                    company_name = vendor_doc.company_name
                    vendor_name = vendor_doc.vendor_name
                    ref_no = vendor_doc.vendor_ref_no
                    
                   
                    supplier_gst = None
                    if hasattr(vendor_doc, 'vendor_code') and vendor_doc.vendor_code:
                        for row in vendor_doc.vendor_code:
                            if hasattr(row, 'gst_no') and row.gst_no:
                                supplier_gst = row.gst_no
                                break  
                    
                
                    vendor_address = None
                    try:
                        company_details_doc = frappe.get_doc("Vendor Onboarding Company Details", {
                            "company_name": company_name,
                            "ref_no": ref_no
                        })

                        address_1 = company_details_doc.get('address_line_1') or ""
                        address_2 = company_details_doc.get('address_line_2') or ""
                        city = company_details_doc.get('city') or ""
                        state = company_details_doc.get('state') or ""
                        pincode = company_details_doc.get('pincode') or ""
                        country = company_details_doc.get('country') or ""
                        district = company_details_doc.get('district') or ""
                        
                    
                        address_parts = [addr for addr in [address_1, address_2, city, district, state, pincode, country] if addr]
                        vendor_address = ", ".join(address_parts) if address_parts else None
                        
                    except frappe.DoesNotExistError:
                        vendor_address = None
                    except Exception as addr_error:
                        vendor_address = None
                        print(f"Error getting company details: {str(addr_error)}")
                    
                    
                    dispatch_data["company_name"] = company_name
                    dispatch_data["vendor_name"] = vendor_name
                    dispatch_data["supplier_gst"] = supplier_gst
                    dispatch_data["vendor_address"] = vendor_address
                    
                except frappe.DoesNotExistError:
                    dispatch_data["company_name"] = None
                    dispatch_data["vendor_name"] = None
                    dispatch_data["supplier_gst"] = None
                    dispatch_data["vendor_address"] = None
                    dispatch_data["vendor_error"] = "Vendor not found"
                except Exception as vendor_error:
                    dispatch_data["company_name"] = None
                    dispatch_data["vendor_name"] = None
                    dispatch_data["supplier_gst"] = None
                    dispatch_data["vendor_address"] = None
                    dispatch_data["vendor_error"] = str(vendor_error)
            else:
                dispatch_data["company_name"] = None
                dispatch_data["vendor_name"] = None
                dispatch_data["supplier_gst"] = None
                dispatch_data["vendor_address"] = None
            
          
            vehicle_details = []
            if hasattr(doc, 'vehicle_details_item') and doc.vehicle_details_item:  
                for vehicle_row in doc.vehicle_details_item:
                    vehicle_link = vehicle_row.get('vehicle_details') 
                    
                    if vehicle_link:
                        try:
                            vehicle_doc = frappe.get_doc("Vehicle Details", vehicle_link) 
                            vehicle_info = {
                                "name": vehicle_doc.name,
                                "vehicle_no": vehicle_doc.get('vehicle_no'),
                                "driver_name": vehicle_doc.get('driver_name'),
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
            
           
            dispatch_data["vehicle_details_item"] = vehicle_details

           
            
            return {
                "name": name,
                "data": dispatch_data
            }
            
    except Exception as e:
        return {"error": True, "message": str(e)}