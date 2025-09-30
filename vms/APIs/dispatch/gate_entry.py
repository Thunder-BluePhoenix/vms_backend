import frappe
from frappe import _
import json
import base64

@frappe.whitelist(allow_guest=False)
def create_gate_entry():
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
            return update_gate_entry(name, data)
        else:
            return create_new_gate_entry(data)
            
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Gate Entry API Error")
        return {"error": True, "message": str(e)}

def create_new_gate_entry(data):
    doc = frappe.new_doc("Gate Entry")
    

    set_gate_entry_data_without_files(doc, data)
    doc.is_submitted = 1
    doc.status = "Gate Received"
    doc.insert()  
    
   
    handle_file_attachments(doc, data)
    doc.save()  
    frappe.db.commit()
    
    return {
        "success": True,
        "message": "Gate Entry created successfully",
        "name": doc.name,
        "date": doc.gate_entry_date
    }

def update_gate_entry(name, data):
    if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Gate Entry name is required"}
        
    if not frappe.db.exists("Gate Entry", name):
        frappe.response.http_status_code = 404
        return {"message": "Failed", "error": f"Gate Entry '{name}' not found"}
    
    doc = frappe.get_doc("Gate Entry", name)
    
    
    set_gate_entry_data(doc, data)

    is_store_user = check_if_store_user()
    if is_store_user:
        doc.status = "Received At Store"

    doc.save()
    frappe.db.commit()
    
    return {
        "success": True,
        "message": "Gate Entry updated successfully",
        "name": doc.name,
        "status": doc.status,
    }

def set_gate_entry_data_without_files(doc, data):
    
    for field, value in data.items():
        if field == "items":
            handle_child_items(doc, value)
        elif field in ["attachment", "image", "attach"]:
            
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

def set_gate_entry_data(doc, data):
    for field, value in data.items():
        if field == "items":
            handle_child_items(doc, value)
        elif field in ["attachment", "image", "attach"]:
            print("Processing attachment field:", field)
            handle_attachment(doc, field, value)
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
            "attached_to_doctype": "Gate Entry",
            "attached_to_name": doc.name
        })
        file_doc.insert(ignore_permissions=True)
        
       
        doc.set(field, file_doc.file_url)
        
        print(f"File uploaded successfully: {file_obj.filename} -> {file_doc.file_url}")
        
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        frappe.log_error(f"File upload error: {str(e)}", "Gate Entry File Upload")

def save_base64_file(doc, field, data_url):
    try:
        header, data_part = data_url.split(",", 1)
        file_type = header.split(";")[0].split(":")[1]
        extension = file_type.split('/')[-1]
        
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"gate_entry_{field}.{extension}",
            "content": data_part,
            "decode": True,
            "attached_to_doctype": "Gate Entry",
            "attached_to_name": doc.name,
            "is_private": 0
        })
        file_doc.insert(ignore_permissions=True)
        doc.set(field, file_doc.file_url)
        
    except Exception as e:
        print(f"Error saving base64 file: {str(e)}")
        frappe.log_error(f"Base64 file error: {str(e)}", "Gate Entry File Upload")



@frappe.whitelist(allow_guest=False)
def get_inward_location():
    locations = frappe.get_all(
        "Inward Location",
        fields=["name","inward_location"]
    )
    return locations


@frappe.whitelist(allow_guest=False)
def get_handover_person():
    employees = frappe.get_all(
        "Employee",
        filters={"designation": "Handover Person"},
        fields=["name","designation","full_name","user_id"]
    )
    return employees


def check_if_store_user():
   
    try:
        current_user = frappe.session.user
        
        if current_user == "Administrator":
            return False
        
       
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": current_user},
            ["designation", "name"],
            as_dict=True
        )
        
        if employee:
            if employee.get("designation") and "store" in str(employee.get("designation")).lower():
                return True
            
    
    
        user_roles = frappe.get_roles(current_user)
        if "Store" in user_roles:
            return True
        
        return False
        
    except Exception as e:
        frappe.log_error(
            f"Error checking store user: {str(e)}",
            "Check Store User Error"
        )
        return False


#vms.APIs.dispatch.gate_entry.handover_gate_entry
@frappe.whitelist()
def handover_gate_entry():
    try:
        if not check_if_store_user():
            frappe.response.http_status_code = 403
            return {
                "message": "Failed", 
                "error": "Only Store users are allowed to perform handover"
            }

        if frappe.request.data:
            try:
                form_data = json.loads(frappe.request.data)
            except:
                form_data = frappe.form_dict.copy()
        else:
            form_data = frappe.form_dict.copy()

        name = form_data.get("name")
        handover_person = form_data.get("handover_person")
        handover_remarks = form_data.get("handover_remarks")

       
        if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Gate Entry name is required"}
        
        if not handover_person:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Handover person is required"}

   
        if not frappe.db.exists("Gate Entry", name):
            frappe.response.http_status_code = 404
            return {"message": "Failed", "error": f"Gate Entry '{name}' not found"}

        
        doc = frappe.get_doc("Gate Entry", name)

   
        if doc.status != "Received At Store":
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": f"Cannot handover. Current status is '{doc.status}'. Must be 'Received At Store'"}


        doc.handover_to_person = handover_person
       
        
        if handover_remarks:
            doc.handover_remark = handover_remarks


        doc.status = "HandedOver"

       
        doc.save(ignore_permissions=True)
        frappe.db.commit()


        return {
            "message": "Success",
            "data": {
                "name": doc.name,
                "status": doc.status,
                "handover_person": handover_person,
            }
        }

    except frappe.ValidationError as e:
        frappe.db.rollback()
        frappe.response.http_status_code = 400
        frappe.log_error(frappe.get_traceback(), "Gate Entry Handover Validation Error")
        return {"message": "Failed", "error": str(e)}
    
    except frappe.PermissionError:
        frappe.db.rollback()
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.db.rollback()
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Gate Entry Handover Error")
        return {"message": "Failed", "error": str(e)}