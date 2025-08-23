import frappe
from frappe import _
import json
import base64

@frappe.whitelist(allow_guest=True)
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
    doc.insert()  
    
   
    handle_file_attachments(doc, data)
    doc.save()  
    frappe.db.commit()
    
    return {
        "success": True,
        "message": "Gate Entry created successfully",
        "name": doc.name
    }

def update_gate_entry(name, data):
    if not frappe.db.exists("Gate Entry", name):
        return {"error": True, "message": f"Gate Entry '{name}' does not exist"}
    
    doc = frappe.get_doc("Gate Entry", name)
    
    
    set_gate_entry_data(doc, data)
    doc.save()
    frappe.db.commit()
    
    return {
        "success": True,
        "message": "Gate Entry updated successfully",
        "name": doc.name
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

@frappe.whitelist(allow_guest=True)
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
        
        if field.fieldtype == "Table" and value:
            child_data = []
            for child in value:
                child_dict = child.as_dict()
                child_data.append(child_dict)
            data[field_name] = child_data
        else:
            data[field_name] = value
    
    return data