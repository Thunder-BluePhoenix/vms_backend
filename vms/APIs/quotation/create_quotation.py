import frappe
import json
from frappe.utils.file_manager import save_file
from frappe.utils import nowdate, now
from frappe import _
import base64

@frappe.whitelist(allow_guest=True)
def fetch_rfq_data(name, ref_no):
	try:
		if not name:
			return {
				"status": "error",
				"message": "Request for Quotation docname is required"
			}
		
		rfq = frappe.get_doc("Request For Quotation", name)
		vendor_master = frappe.get_doc("Vendor Master", ref_no)

		company_vendor_code = frappe.get_all(
			"Company Vendor Code",
			filters={"vendor_ref_no": ref_no},
			fields=["name"]
		)

		vendor_code_list = []
		for row in company_vendor_code:
			doc = frappe.get_doc("Company Vendor Code", row.name)
			for code_row in doc.vendor_code:
				vendor_code_list.append(code_row.vendor_code)

		vendor_details = {
			"vendor_name": vendor_master.vendor_name,
			"office_email_primary": vendor_master.office_email_primary,
			"mobile_number": vendor_master.mobile_number,
			"country": vendor_master.country,
			"vendor_code": vendor_code_list
		}

		if rfq.rfq_type == "Logistic Vendor":
			attachments = []
			for row in rfq.multiple_attachments:
				file_url = row.get("attachment_name")
				if file_url:
					file_doc = frappe.get_doc("File", {"file_url": file_url})
					attachments.append({
						"url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
						"name": file_doc.name,
						"file_name": file_doc.file_name
					})
				else:
					attachments.append({
						"url": "",
						"name": "",
						"file_name": ""
					})
					
			return {
				"status": "success",
				"vendor_details": vendor_details,
				"company_name_logistic": rfq.company_name_logistic,
				"rfq_cutoff_date_logistic": rfq.rfq_cutoff_date_logistic,
				"mode_of_shipment": rfq.mode_of_shipment,
				"destination_port": rfq.destination_port,
				"port_of_loading": rfq.port_of_loading,
				"ship_to_address": rfq.ship_to_address,
				"no_of_pkg_units": rfq.no_of_pkg_units,
				"vol_weight": rfq.vol_weight,
				"invoice_date": rfq.invoice_date,
				"shipment_date": rfq.shipment_date,
				"remarks": rfq.remarks,
				"expected_date_of_arrival": rfq.expected_date_of_arrival,
				"consignee_name": rfq.consignee_name,
				"sr_no": rfq.sr_no,
				"rfq_date_logistic": rfq.rfq_date_logistic,
				"country": rfq.country,
				"port_code": rfq.port_code,
				"inco_terms": rfq.inco_terms,
				"package_type": rfq.package_type,
				"product_category": rfq.product_category,
				"actual_weight": rfq.actual_weight,
				"invoice_no": rfq.invoice_no,
				"invoice_value": rfq.invoice_value,
				"shipment_type": rfq.shipment_type,
				"shipper_name": rfq.shipper_name,
				"attachments": attachments

			}

		elif rfq.rfq_type == "Material Vendor":
			pr_items = []
			for row in rfq.rfq_items:
				pr_items.append({
					"row_id": row.name,
					"head_unique_field": row.head_unique_field,
					"purchase_requisition_number": row.purchase_requisition_number,
					"material_code_head": row.material_code_head,
					"delivery_date_head": row.delivery_date_head,
					"plant_head": row.plant_head,
					"material_name_head": row.material_name_head,
					"quantity_head": row.quantity_head,
					"uom_head": row.uom_head,
					"price_head": row.price_head
				})

			attachments = []
			for row in rfq.multiple_attachments:
				file_url = row.get("attachment_name")
				if file_url:
					file_doc = frappe.get_doc("File", {"file_url": file_url})
					attachments.append({
						"url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
						"name": file_doc.name,
						"file_name": file_doc.file_name
					})
				else:
					attachments.append({
						"url": "",
						"name": "",
						"file_name": ""
					})

			return {
				"status": "success",
				"vendor_details": vendor_details,
				"rfq_date": rfq.rfq_date,
				"company_name": rfq.company_name,
				"purchase_organization": rfq.purchase_organization,
				"purchase_group": rfq.purchase_group,
				"currency": rfq.currency,
				"collection_number": rfq.collection_number,
				"quotation_deadline": rfq.quotation_deadline,
				"validity_start_date": rfq.validity_start_date,
				"validity_end_date": rfq.validity_end_date,
				"bidding_person": rfq.bidding_person,
				"storage_location": rfq.storage_location,
				"service_code": rfq.service_code,
				"service_category": rfq.service_category,
				"service_location": rfq.service_location,
				"rfq_quantity": rfq.rfq_quantity,
				"quantity_unit": rfq.quantity_unit,
				"delivery_date": rfq.delivery_date,
				"estimated_price": rfq.estimated_price,
				"pr_items": pr_items,
				"attachments": attachments
			}

		elif rfq.rfq_type == "Service Vendor":
			pr_items = []
			for row in rfq.rfq_items:
				pr_items.append({
					"row_id": row.name,
					"head_unique_field": row.head_unique_field,
					"purchase_requisition_number": row.purchase_requisition_number,
					"material_code_head": row.material_code_head,
					"delivery_date_head": row.delivery_date_head,
					"plant_head": row.plant_head,
					"material_name_head": row.material_name_head,
					"quantity_head": row.quantity_head,
					"uom_head": row.uom_head,
					"price_head": row.price_head,
					"subhead_unique_field": row.subhead_unique_field,
					"material_code_subhead": row.material_code_subhead,
					"material_name_subhead": row.material_name_subhead,
					"quantity_subhead": row.quantity_subhead,
					"uom_subhead": row.uom_subhead,
					"price_subhead": row.price_subhead,
					"delivery_date_subhead": row.delivery_date_subhead
				})

			attachments = []
			for row in rfq.multiple_attachments:
				file_url = row.get("attachment_name")
				if file_url:
					file_doc = frappe.get_doc("File", {"file_url": file_url})
					attachments.append({
						"url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
						"name": file_doc.name,
						"file_name": file_doc.file_name
					})
				else:
					attachments.append({
						"url": "",
						"name": "",
						"file_name": ""
					})

			return {
				"status": "success",
				"vendor_details": vendor_details,
				"rfq_date": rfq.rfq_date,
				"company_name": rfq.company_name,
				"purchase_organization": rfq.purchase_organization,
				"purchase_group": rfq.purchase_group,
				"currency": rfq.currency,
				"collection_number": rfq.collection_number,
				"quotation_deadline": rfq.quotation_deadline,
				"validity_start_date": rfq.validity_start_date,
				"validity_end_date": rfq.validity_end_date,
				"bidding_person": rfq.bidding_person,
				"storage_location": rfq.storage_location,
				"service_code": rfq.service_code,
				"service_category": rfq.service_category,
				"service_location": rfq.service_location,
				"rfq_quantity": rfq.rfq_quantity,
				"quantity_unit": rfq.quantity_unit,
				"delivery_date": rfq.delivery_date,
				"estimated_price": rfq.estimated_price,
				"pr_items": pr_items,
				"attachments": attachments
			}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create Quotation API Error")
		return {
			"status": "error",
			"message": str(e)
		}

# if quotation deadline or rfqcutoff date > today datetime then i will throw a message that quotation cannot be create as time pass
# do in above code (discussion pending with neel)



@frappe.whitelist(allow_guest=True)
def create_or_update_quotation():
    try:
        form_data = frappe.local.form_dict
        
        files = []
        
        if hasattr(frappe, 'request') and hasattr(frappe.request, 'files'):
            request_files = frappe.request.files
            if 'file' in request_files:
                file_list = request_files.getlist('file')
                files.extend(file_list)
        
      
        if hasattr(frappe.local, 'uploaded_files') and frappe.local.uploaded_files:
            uploaded_files = frappe.local.uploaded_files
            if isinstance(uploaded_files, list):
                files.extend(uploaded_files)
            else:
                files.append(uploaded_files)
        
      
        if 'file' in form_data:
            file_data = form_data.get('file')
            if hasattr(file_data, 'filename'): 
                files.append(file_data)
            elif isinstance(file_data, list):
                files.extend([f for f in file_data if hasattr(f, 'filename')])
        
       
        frappe.log_error(f"Found {len(files)} files", "file_debug")
        
       
        data = {}
        for key, value in form_data.items():
            if key != 'file':  
                data[key] = value
        
      
        if isinstance(data.get('data'), str):
            try:
                json_data = json.loads(data.get('data'))
                data.update(json_data)
                data.pop('data', None)  
            except json.JSONDecodeError:
                pass
        
        quotation_name = data.get('name')
        
       
        if quotation_name and frappe.db.exists('Quotation', quotation_name):
            quotation = frappe.get_doc('Quotation', quotation_name)
            
            
            for key, value in data.items():
                if hasattr(quotation, key) and key != 'name':
                    setattr(quotation, key, value)
            
            quotation.asked_to_revise = 0
            quotation.save()
            
           
            handle_quotation_files(quotation, files)
            
            quotation.save()
            frappe.db.commit()
            
            return {
                "status": "success",
                "message": "Quotation updated successfully",
                "data": {
                    "name": quotation.name,
                    "action": "updated",
                    "attachments_count": len(quotation.attachments) if quotation.attachments else 0
                }
            }
        
        
        else:
            data.pop('name', None)  
            
            quotation = frappe.new_doc('Quotation')
            
            
            if not data.get('rfq_date'):
                data['rfq_date'] = nowdate()
            if not data.get('rfq_date_logistic'):
                data['rfq_date_logistic'] = nowdate()
            
           
            for key, value in data.items():
                if hasattr(quotation, key):
                    setattr(quotation, key, value)
            
            quotation.asked_to_revise = 0
            quotation.insert()
            
        
            handle_quotation_files(quotation, files)
            
            quotation.save()
            frappe.db.commit()
            
            return {
                "status": "success",
                "message": "Quotation created successfully",
                "data": {
                    "name": quotation.name,
                    "action": "created",
                    "attachments_count": len(quotation.attachments) if quotation.attachments else 0
                }
            }
        
    except frappe.ValidationError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": f"Validation Error: {str(e)}",
            "error_type": "validation"
        }
    
    except frappe.DuplicateEntryError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": f"Duplicate Entry: {str(e)}",
            "error_type": "duplicate"
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Quotation API Error: {str(e)}", "quotation_api_error")
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "error_type": "general"
        }


def handle_quotation_files(quotation, files):
    
    if not files:
        frappe.log_error("No files to process", "file_debug")
        return
    
    frappe.log_error(f"Processing {len(files)} files", "file_debug")
    
    
    if quotation.get('attachments'):
        quotation.set('attachments', [])
    
    for i, file_obj in enumerate(files):
        try:
            frappe.log_error(f"Processing file {i}: {type(file_obj)}", "file_debug")
            
            file_name = None
            file_content = None
            
          
            if hasattr(file_obj, 'filename') and hasattr(file_obj, 'stream'):
                file_name = file_obj.filename
                file_obj.stream.seek(0)  
                file_content = file_obj.stream.read()
                frappe.log_error(f"FileStorage: {file_name}, size: {len(file_content) if file_content else 0}", "file_debug")
                
           
            elif hasattr(file_obj, 'filename') and hasattr(file_obj, 'read'):
                file_name = file_obj.filename
                file_content = file_obj.read()
                frappe.log_error(f"File with read: {file_name}, size: {len(file_content) if file_content else 0}", "file_debug")
                
           
            elif hasattr(file_obj, 'filename') and hasattr(file_obj, 'file'):
                file_name = file_obj.filename
                file_content = file_obj.file.read()
                frappe.log_error(f"File with file attr: {file_name}, size: {len(file_content) if file_content else 0}", "file_debug")
                
            
            elif isinstance(file_obj, dict):
                file_name = file_obj.get('filename')
                file_content = file_obj.get('content')
                
                
                if isinstance(file_content, str):
                    try:
                        file_content = base64.b64decode(file_content)
                    except:
                        pass
                        
            else:
                frappe.log_error(f"Unknown file object type: {type(file_obj)}, attributes: {dir(file_obj)}", "file_debug")
                continue
            
            if not file_name or not file_content:
                frappe.log_error(f"Missing file name or content: name={file_name}, content_size={len(file_content) if file_content else 0}", "file_debug")
                continue
            
            
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "content": file_content,
                "decode": False,
                "is_private": 0,
                "attached_to_doctype": "Quotation",
                "attached_to_name": quotation.name
            })
            file_doc.insert(ignore_permissions=True)
            
            
            attachment_row = quotation.append('attachments', {})
            attachment_row.attachment_name = file_doc.file_url
            attachment_row.name1 = file_name  
            
            frappe.log_error(f"Successfully attached file: {file_name} -> {file_doc.file_url}", "file_debug")
            
        except Exception as e:
            frappe.log_error(f"Error handling file attachment {i}: {str(e)}", "file_attachment_error")
            import traceback
            frappe.log_error(traceback.format_exc(), "file_attachment_traceback")
            continue


def handle_quotation_files_alternative(quotation, form_data):
  
    if not form_data:
        return
    
    
    if quotation.get('attachments'):
        quotation.set('attachments', [])
    
   
    file_keys = [key for key in form_data.keys() if key.startswith('file')]
    
    for file_key in file_keys:
        files = form_data.getlist(file_key) 
        
        for file_obj in files:
            try:
                if hasattr(file_obj, 'filename') and hasattr(file_obj, 'read'):
                    file_name = file_obj.filename
                    file_content = file_obj.read()
                    
                    
                    file_doc = frappe.get_doc({
                        "doctype": "File",
                        "file_name": file_name,
                        "content": file_content,
                        "decode": False,
                        "is_private": 0,
                        "attached_to_doctype": "Quotation",
                        "attached_to_name": quotation.name
                    })
                    file_doc.insert()
                    
                    
                    attachment_row = quotation.append('attachments', {})
                    attachment_row.attachment_name = file_doc.file_url
                    attachment_row.name1 = file_name
                    
            except Exception as e:
                frappe.log_error(f"Error handling file {file_key}: {str(e)}", "file_handling_error")
                continue