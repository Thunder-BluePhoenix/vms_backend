import frappe
from frappe import _
import json
import base64

@frappe.whitelist(allow_guest=True)
def create_vehicle_details():
    try:
        data = frappe.local.form_dict.copy() if frappe.local.form_dict else {}
        
        if hasattr(frappe.request, 'files') and frappe.request.files:
            for field_name, file_obj in frappe.request.files.items():
                if file_obj and getattr(file_obj, 'filename', None):
                    data[field_name] = file_obj
        
        if not data and frappe.request.data:
            try:
                data = json.loads(frappe.request.data)
            except json.JSONDecodeError:
                return {"error": True, "message": "Invalid JSON data"}
        
        if 'data' in data and isinstance(data['data'], dict):
            nested_data = data['data']
            files = {k: v for k, v in data.items() if hasattr(v, 'filename')}
            data = nested_data
            data.update(files)
        
        if not data:
            return {"error": True, "message": "No data provided"}

        name = data.get('name')
        if name:
            result = update_vehicle_details(name, data)
        else:
            result = create_new_vehicle_details(data)
        
        # Handle dispatch item mapping after vehicle creation/update
        if result.get('success') and data.get('dispatch_item_id'):
            map_vehicle_to_dispatch_item(result['name'], data['dispatch_item_id'])
            
        return result
            
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vehicle Details API Error")
        return {"error": True, "message": str(e)}

def create_new_vehicle_details(data):
    doc = frappe.new_doc("Vehicle Details")
    
    set_vehicle_details_data_without_files(doc, data)
    doc.insert()  
    
    handle_file_attachments(doc, data)
    doc.save()  
    frappe.db.commit()
    
    return {
        "success": True,
        "message": "Vehicle Details created successfully",
        "name": doc.name
    }

def update_vehicle_details(name, data):
    if not frappe.db.exists("Vehicle Details", name):
        return {"error": True, "message": f"Vehicle Details '{name}' does not exist"}
    
    doc = frappe.get_doc("Vehicle Details", name)
    
    set_vehicle_details_data(doc, data)
    doc.save()
    frappe.db.commit()
    
    return {
        "success": True,
        "message": "Vehicle Details updated successfully",
        "name": doc.name
    }

def map_vehicle_to_dispatch_item(vehicle_name, dispatch_item_id):
    try:
        if not frappe.db.exists("Dispatch Item", dispatch_item_id):
            frappe.log_error(f"Dispatch Item '{dispatch_item_id}' does not exist", "Vehicle Mapping Error")
            return
        
        dispatch_doc = frappe.get_doc("Dispatch Item", dispatch_item_id)
        
        existing_vehicle = None
        if hasattr(dispatch_doc, 'vehicle_details_item'):  
            for vehicle_row in dispatch_doc.vehicle_details_item:
                if vehicle_row.vehicle_details == vehicle_name:
                    existing_vehicle = vehicle_row
                    break
        
        if not existing_vehicle:
    
            dispatch_doc.append('vehicle_details_item', {
                'vehicle_details': vehicle_name,
               
            })
        else:
            existing_vehicle.vehicle = vehicle_name
        
        dispatch_doc.save()
        frappe.db.commit()
        
        frappe.msgprint(f"Vehicle {vehicle_name} mapped to Dispatch Item {dispatch_item_id}")
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vehicle Mapping Error")
        frappe.throw(f"Error mapping vehicle to dispatch item: {str(e)}")

def set_vehicle_details_data_without_files(doc, data):
   
    excluded_fields = ["items", "attachment", "image", "attach", "dispatch_item_id"]
    
    for field, value in data.items():
        if field == "items":
            handle_child_items(doc, value)
        elif field in excluded_fields:
            continue
        else:
            if hasattr(value, 'filename'):
                continue
            if hasattr(doc, field):
                doc.set(field, value)

def handle_file_attachments(doc, data):
    for field, value in data.items():
        if field in ["attachment", "image", "attach"]:
            print("Processing attachment field:", field)
            handle_attachment(doc, field, value)

def set_vehicle_details_data(doc, data):
   
    excluded_fields = ["items", "attachment", "image", "attach", "dispatch_item_id"]
    
    for field, value in data.items():
        if field == "items":
            handle_child_items(doc, value)
        elif field in ["attachment", "image", "attach"]:
            print("Processing attachment field:", field)
            handle_attachment(doc, field, value)
        elif field in excluded_fields:
            continue
        else:
           
            if hasattr(value, 'filename'):
                continue
            if hasattr(doc, field):
                doc.set(field, value)

def handle_child_items(doc, items_data):
    if not isinstance(items_data, list):
        return
    
    doc.set("items", [])
    for item in items_data:
        if isinstance(item, dict):
            doc.append("items", item)

def handle_attachment(doc, field, value):
    if not value:
        return
    
   
    if hasattr(value, 'filename'):
        save_uploaded_file(doc, field, value)
        return
    
  
    if isinstance(value, str) and value.startswith("data:"):
        save_base64_file(doc, field, value)
        return
    
  
    if isinstance(value, str):
        doc.set(field, value)

@frappe.whitelist()
def get_dispatch_item_vehicles(dispatch_item_id):
    try:
        if not frappe.db.exists("Dispatch Item", dispatch_item_id):
            return {"error": True, "message": f"Dispatch Item '{dispatch_item_id}' does not exist"}
        
        dispatch_doc = frappe.get_doc("Dispatch Item", dispatch_item_id)
        vehicles = []
        
        if hasattr(dispatch_doc, 'vehicle_details_item'):
            for vehicle_row in dispatch_doc.vehicle_details_item:
                if vehicle_row.vehicle_details:
                    vehicle_doc = frappe.get_doc("Vehicle Details", vehicle_row.vehicle)
                    vehicle_details_item.append({
                        "name": vehicle_doc.name,
                    })
        
        return {
            "success": True,
            "vehicles": vehicles
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Dispatch Vehicles Error")
        return {"error": True, "message": str(e)}

def save_uploaded_file(doc, field, file_obj):
    try:
      
        file_content = None
        if hasattr(file_obj, 'stream'):
            file_obj.stream.seek(0)
            file_content = file_obj.stream.read()
        elif hasattr(file_obj, 'read'):
            file_content = file_obj.read()
        elif hasattr(file_obj, 'file'):
            file_content = file_obj.file.read()
        
        if not file_content or not file_obj.filename:
            return
        
      
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_obj.filename,
            "content": file_content,
            "decode": False,
            "is_private": 0,
            "attached_to_doctype": "Vehicle Details",
            "attached_to_name": doc.name
        })
        file_doc.insert(ignore_permissions=True)
        
       
        doc.set(field, file_doc.file_url)
        
        print(f"File uploaded successfully: {file_obj.filename} -> {file_doc.file_url}")
        
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        frappe.log_error(f"File upload error: {str(e)}", "Vehicle Details File Upload")

def save_base64_file(doc, field, data_url):
    try:
        header, data_part = data_url.split(",", 1)
        file_type = header.split(";")[0].split(":")[1]
        extension = file_type.split('/')[-1]
        
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"vehicle_details_{field}.{extension}",
            "content": data_part,
            "decode": True,
            "attached_to_doctype": "Vehicle Details",
            "attached_to_name": doc.name,
            "is_private": 0
        })
        file_doc.insert(ignore_permissions=True)
        doc.set(field, file_doc.file_url)
        
    except Exception as e:
        print(f"Error saving base64 file: {str(e)}")
        frappe.log_error(f"Base64 file error: {str(e)}", "Vehicle Details File Upload")

@frappe.whitelist(allow_guest=True)
def vehicle_details_get(name=None, start=0, page_length=20):
    try:
        if name:
            doc = frappe.get_doc("Vehicle Details", name)
            print("doc",doc)
            return {
                "name": name,
                "data": get_vehicle_details_data(doc)
            }
        else:
            data = frappe.get_list(
                "Vehicle Details",
                fields=["*"],
                start=start,
                page_length=page_length,
                order_by="modified desc"
            )
            
            total_count = frappe.db.count("Vehicle Details")
            
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

def get_vehicle_details_data(doc):
    data = {}
    meta = frappe.get_meta("Vehicle Details")
    
    exclude_fieldtypes = [
        "Section Break", "Column Break", "Tab Break", 
        "HTML", "Heading", "Fold", "Button",
    ]
    
    for field in meta.fields:
        if field.fieldtype in exclude_fieldtypes:
            continue
            
        field_name = field.fieldname
        value = getattr(doc, field_name, None)
        print(value)
        
        if field.fieldtype == "Table" and value:
            child_data = []
            for child in value:
                child_dict = child.as_dict()
                child_data.append(child_dict)
            data[field_name] = child_data
        else:
            data[field_name] = value
    
    return data


@frappe.whitelist(allow_guest=True)  
def get_state_and_plant_data(search_term=None, page=1, page_size=50):
    try:
        page = max(1, int(page or 1))
        page_size = min(200, max(1, int(page_size or 50)))
        search_term = search_term.strip() if search_term else None
        
        response = {
            "success": True,
            "data": {}
        }
        
        states_data = get_state_master_list(search_term, page, page_size)
        print(states_data)
        plants_data = get_plant_master_list(search_term, page, page_size)
        
        response["data"]["states"] = states_data["records"]
        response["data"]["plants"] = plants_data["records"]
        
        response["pagination"] = {
            "page": page,
            "page_size": page_size,
            "search_term": search_term,
            "states": {
                "total_records": states_data["total_count"],
                "total_pages": states_data["total_pages"],
                "has_next": states_data["has_next"],
                "has_prev": states_data["has_prev"]
            },
            "plants": {
                "total_records": plants_data["total_count"], 
                "total_pages": plants_data["total_pages"],
                "has_next": plants_data["has_next"],
                "has_prev": plants_data["has_prev"]
            }
        }
        
        if not states_data["records"] and not plants_data["records"]:
            response = {
                "success": False,
                "message": "No master data found"
            }
        
        return response
        
    except Exception as e:
        frappe.log_error(f"Error in get_master_data: {str(e)}")
        return {
            "success": False,
            "message": "An error occurred while fetching master data",
            "error": str(e)
        }

def get_state_master_list(search_term=None, page=1, page_size=50):
    try:
    
        filters = {}
        or_filters = []
        
        if search_term:
            or_filters = [
                ['state_name', 'like', f'%{search_term}%'],
                ['state_code', 'like', f'%{search_term}%'],
                ['country', 'like', f'%{search_term}%']
            ]
        
       
        if or_filters:
            total_count = len(frappe.get_all(
                'State Master',
                fields=['name'],
                filters=filters,
                or_filters=or_filters
            ))
        else:
            total_count = frappe.db.count('State Master')
        
        
        total_pages = (total_count + page_size - 1) // page_size
        start = (page - 1) * page_size
        
        
        states = frappe.get_all(
            'State Master',
            fields=['name', 'state_name', 'state_code', 'country_name'],
            filters=filters,
            or_filters=or_filters if or_filters else None,
            order_by='state_name asc',
            start=start,
            page_length=page_size
        )
        
        return {
            "records": states,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching states: {str(e)}")
        return {
            "records": [],
            "total_count": 0,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False
        }

def get_plant_master_list(search_term=None, page=1, page_size=50):
    try:
        # Build search filters
        filters = {}
        or_filters = []
        
        if search_term:
            or_filters = [
                ['plant_name', 'like', f'%{search_term}%'],
                ['company', 'like', f'%{search_term}%'],
                ['name', 'like', f'%{search_term}%']
            ]
        
        # Get total count
        if or_filters:
            total_count = len(frappe.get_all(
                'Plant Master',
                fields=['name'],
                filters=filters,
                or_filters=or_filters
            ))
        else:
            total_count = frappe.db.count('Plant Master')
        
    
        total_pages = (total_count + page_size - 1) // page_size
        start = (page - 1) * page_size
        
        plants = frappe.get_all(
            'Plant Master',  
            fields=['name', 'plant_name', 'company'],
            filters=filters,
            or_filters=or_filters if or_filters else None,
            order_by='plant_name asc',
            start=start,
            page_length=page_size
        )
        
        return {
            "records": plants,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching plants: {str(e)}")
        return {
            "records": [],
            "total_count": 0,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False
        }