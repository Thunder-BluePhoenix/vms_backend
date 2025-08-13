import frappe
import json
from frappe.utils.file_manager import save_file
from frappe.utils import nowdate, now
from frappe import _
import base64
import jwt
from frappe.utils import get_datetime, now_datetime
from datetime import datetime
from frappe import _
from datetime import datetime, timedelta

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





@frappe.whitelist()
def create_or_update_quotation():
    try:
        form_data = frappe.local.form_dict
        user = frappe.session.user

        rfq = form_data.get('rfq_number')
        if not rfq:
            return {
                "status": "error",
                "message": "RFQ Number is required",
                "error": "RFQ Number is required"
            }

        if not frappe.db.exists("Request For Quotation", rfq):
            return {
                "status": "error",
                "message": f"RFQ {rfq} does not exist",
                "error": "RFQ Not Found"
            }
        
        rfq_doc = frappe.get_doc("Request For Quotation", rfq)
        
    
        vendor_details = None
        user_authorized = False
        
        for vendor in rfq_doc.vendor_details:
            if vendor.get('office_email_primary') == user:
                user_authorized = True
                vendor_details = vendor
                break
        
        if not user_authorized:
            return {
                "status": "error",
                "message": "You are not allowed to fill this quotation",
                "error": "Unauthorized Access"
            }

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

        if vendor_details:
            data['ref_no'] = vendor_details.get('ref_no')
            data['vendor_name'] = vendor_details.get('vendor_name')
            data['vendor_code'] = vendor_details.get('vendor_code')

        quotation_name = data.get('name')
        action = "updated"
        email_sent = False

        if quotation_name and frappe.db.exists('Quotation', quotation_name):
            quotation = frappe.get_doc('Quotation', quotation_name)

            for key, value in data.items():
                if hasattr(quotation, key) and key != 'name':
                    setattr(quotation, key, value)

            quotation.asked_to_revise = 0
            quotation.flags.ignore_version = True
            quotation.flags.ignore_links = True
            quotation.save(ignore_version=True)

            handle_quotation_files(quotation, files)
            quotation.save(ignore_version=True)
            frappe.db.commit()

            action = "updated"

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
            quotation.flags.ignore_version = True
            quotation.flags.ignore_links = True
            quotation.insert(ignore_permissions=True)

            handle_quotation_files(quotation, files)
            quotation.save(ignore_version=True)
            frappe.db.commit()

            action = "created"

            if quotation.rfq_number:
                try:
                    frappe.enqueue(
                        'vms.APIs.quotation.create_quotation.send_quotation_notification_email',
                        quotation_name=quotation.name,
                        rfq_number=quotation.rfq_number,
                        action=action,
                        queue='short',
                        timeout=600,
                        is_async=True
                    )
                    email_sent = True
                    frappe.log_error(f"Email notification queued for NEW quotation {quotation.name}", "Email Queue Success")
                except Exception as email_error:
                    frappe.log_error(f"Failed to queue email for quotation {quotation.name}: {str(email_error)}", "Email Queue Error")

        return {
            "status": "success",
            "message": f"Quotation {action} successfully",
            "data": {
                "name": quotation.name,
                "action": action,
                "attachments_count": len(quotation.attachments) if quotation.attachments else 0,
                "email_sent": email_sent
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

SECRET_KEY = str(frappe.conf.get("secret_key", ""))

@frappe.whitelist(allow_guest=True)
def create_or_update_quotation_non_onboarded():
    try:
        form_data = frappe.local.form_dict
        token = form_data.get('token')
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        vendor_email = decoded.get("email")
        rfq_number = decoded.get("rfq")
        rfq_type = decoded.get("rfq_type")
        

        if rfq_number:
            rfq_doc = frappe.get_doc("Request For Quotation", rfq_number)
            cutoff = get_datetime(rfq_doc.rfq_cutoff_date_logistic)
            now = now_datetime()
            
            if now > cutoff:
                frappe.local.response["http_status_code"] = 410  
                frappe.throw(_("This secure link has expired due to cutoff date."))

        if not vendor_email:
            return {
                "status": "error",
                "message": "Email is required",
                "error": "Email is required"
            }

        if not rfq_number:
            return {
                "status": "error",
                "message": "RFQ Number is required",
                "error": "RFQ Number is required"
            }

        if not frappe.db.exists("Request For Quotation", rfq_number):
            return {
                "status": "error",
                "message": f"RFQ {rfq_number} does not exist",
                "error": "RFQ Not Found"
            }

        rfq_doc = frappe.get_doc("Request For Quotation", rfq_number)
        user_authorized = False
        vendor_details = None
        is_onboarded_vendor = False

       
        for vendor in rfq_doc.vendor_details:
            if vendor.get('office_email_primary') == vendor_email:
                user_authorized = True
                vendor_details = vendor
                is_onboarded_vendor = True
                break

      
        if not user_authorized:
            for vendor in rfq_doc.non_onboarded_vendor_details:
                if vendor.get('office_email_primary') == vendor_email:
                    user_authorized = True
                    break

        if not user_authorized:
            return {
                "status": "error",
                "message": "You are not allowed to fill this quotation",
                "error": "Unauthorized Access"
            }

        
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

        # Process form data
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

        if vendor_email:
            data['office_email_primary'] = vendor_email

        if rfq_number:
            data["rfq_number"] = rfq_number

        
       

        
    


       
        if vendor_details and is_onboarded_vendor:
            data['ref_no'] = vendor_details.get('ref_no')
            data['vendor_name'] = vendor_details.get('vendor_name')
            data['vendor_code'] = vendor_details.get('vendor_code')

        def find_quotation_child_table():
         
            try:
                quotation_meta = frappe.get_meta('Quotation')
                
                
                preferred_tables = ['rfq_item_list', 'items', 'quotation_items', 'rfq_items']
                
                for field in quotation_meta.fields:
                    if (field and hasattr(field, 'fieldtype') and 
                        field.fieldtype == 'Table' and 
                        field.fieldname in preferred_tables):
                        return field.fieldname, field.options
                
    
                for field in quotation_meta.fields:
                    if (field and hasattr(field, 'fieldtype') and 
                        field.fieldtype == 'Table' and 
                        field.fieldname not in ['attachments', 'version_history']):
                        return field.fieldname, field.options
                
                return None, None
                
            except Exception as e:
                frappe.log_error(f"Child table discovery failed: {str(e)[:80]}", "Child Table Error")
                return None, None

        def apply_rfq_logistic_logic(data_dict):
            rfq_type = data_dict.get('rfq_type', '').lower()
            logistic_type = data_dict.get('logistic_type', '').lower()
            
            if rfq_type == 'logistic vendor':
                if logistic_type == 'import':
                    total_landing_price = data_dict.get('total_landing_price')
                    if total_landing_price:
                        data_dict['quote_amount'] = total_landing_price
                        data_dict['total_landing_price'] = total_landing_price
                        
                elif logistic_type == 'export':
                    total_freightinr = data_dict.get('total_freightinr')
                    if total_freightinr:
                        data_dict['quote_amount'] = total_freightinr
                        data_dict['total_freightinr'] = total_freightinr
            
            elif rfq_type == 'material vendor':
                # Calculate total quote amount from items
                rfq_item_list = data_dict.get('rfq_item_list', [])
                total_amount = 0
                
                for item in rfq_item_list:
                    try:
                        price = float(item.get('price_head', 0) or 0)
                        total_amount += price
                    except (ValueError, TypeError):
                        continue
                        
                if total_amount > 0:
                    data_dict['quote_amount'] = total_amount
            
            return data_dict

        def apply_field_mapping_logic(data_dict):
            field_mapping = {
                'vendor_name':'final_ffn',
                'total_freight':'final_freight_fcr',
                'exchange_rate': 'final_xcr',
                'total_freightinr':'final_sum_freight_inr',
                'other_charges_in_total': 'final_others',
                'destination_charge':'final_dc',
                'remarks':'final_remarks',
                'ratekg': 'final_rate_kg',
                'fuel_surcharge':'final_fsc',
                'pickuporigin': 'final_pickup',
                'airlinevessel_name': 'final_airline',
                'transit_days': 'final_transit_days',
                'chargeable_weight': 'final_chargeable_weight',
                'sc': 'final_sc',
                'xray': 'final_xray',
                'total_landing_price': 'final_landing_price',
                'transit_days': 'final_transit_days',
                'total_freight': 'final_freight_fcr',
                'remarks': 'final_remarks',
                'vendor_name': 'final_ffn',
                'total_freightinr': 'final_sum_freight_inr',
                'destination_charge': 'final_dc',
                'fuel_surcharge': 'final_fsc',
                'cfs_charge': 'final_cfs_charge'
            }
            
            for original_field, final_field in field_mapping.items():
                if original_field in data_dict and data_dict[original_field] is not None:
                    data_dict[final_field] = data_dict[original_field]
            
            return data_dict

        def process_material_vendor_items(quotation, rfq_item_list, child_table_name):
            
            if not rfq_item_list or not child_table_name:
                return
            
            quotation.set(child_table_name, [])
            
            for i, item_data in enumerate(rfq_item_list):
                try:
                    quotation_item = quotation.append(child_table_name, item_data)
                    
                   
                    numeric_fields = ['rate_head', 'quantity_head', 'price_head', 'lead_time_head']
                    for field in numeric_fields:
                        if hasattr(quotation_item, field) and getattr(quotation_item, field):
                            try:
                                value = getattr(quotation_item, field)
                                setattr(quotation_item, field, float(value))
                            except (ValueError, TypeError):
                                setattr(quotation_item, field, 0)
                    
                    if hasattr(quotation_item, 'rfq_type'):
                        quotation_item.rfq_type = data.get('rfq_type', '')
                        
                except Exception as item_error:
                    frappe.log_error(f"Error processing item {i+1}: {str(item_error)[:80]}", "Item Error")
                    continue

        data = apply_field_mapping_logic(data)
        data = apply_rfq_logistic_logic(data)
        rfq_item_list = data.pop('rfq_item_list', [])

        quotation_name = data.get('name')
        action = "updated"
        email_sent = False

        
        child_table_name, child_doctype = find_quotation_child_table()
        
        if quotation_name and frappe.db.exists('Quotation', quotation_name):
            
            quotation = frappe.get_doc('Quotation', quotation_name)

            if 'rfq_type' in form_data:
                rfq_type_name = form_data.get('rfq_type')
                rfq_type_doc = frappe.get_doc("Vendor Type Master", {"vendor_type_name": rfq_type_name})
                quotation.rfq_type = rfq_type_doc.name
                print(f"Explicitly set rfq_type: {quotation.rfq_type}")

               

            
            for key, value in data.items():
                if hasattr(quotation, key) and key != 'name':
                    setattr(quotation, key, value)

         
            if data.get('rfq_type', '').lower() == 'material vendor' and rfq_item_list and child_table_name:
                process_material_vendor_items(quotation, rfq_item_list, child_table_name)

            quotation.asked_to_revise = 0
            quotation.flags.ignore_version = True
            quotation.flags.ignore_links = True
            quotation.save(ignore_version=True)
        
            handle_quotation_files(quotation, files)
            quotation.save(ignore_version=True)
            frappe.db.commit()
            send_quotation_access_email_simple(quotation, vendor_email, "updated", rfq_number)
            
            action = "updated"

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
            
            if 'rfq_type' in form_data:

                rfq_type_name = form_data.get('rfq_type')
                rfq_type_doc = frappe.get_doc("Vendor Type Master", {"vendor_type_name": rfq_type_name})
                quotation.rfq_type = rfq_type_doc.name
                print(f"Explicitly set rfq_type: {quotation.rfq_type}")

            quotation.asked_to_revise = 0
            quotation.flags.ignore_version = True
            quotation.flags.ignore_links = True
            
            if data.get('rfq_type', '').lower() == 'material vendor' and rfq_item_list and child_table_name:
                process_material_vendor_items(quotation, rfq_item_list, child_table_name)

          
            
            quotation.insert(ignore_permissions=True)

            handle_quotation_files(quotation, files)
            quotation.save(ignore_version=True)
            frappe.db.commit()
            send_quotation_access_email_simple(quotation, vendor_email, "created", rfq_number)

            action = "created"

            if quotation.rfq_number:
                try:
                    frappe.enqueue(
                        'vms.APIs.quotation.create_quotation.send_quotation_notification_email',
                        quotation_name=quotation.name,
                        rfq_number=quotation.rfq_number,
                        action=action,
                        queue='short',
                        timeout=600,
                        is_async=True
                    )
                    email_sent = True
                    
                except Exception as email_error:
                    frappe.log_error(f"Failed to queue email for quotation {quotation.name}: {str(email_error)[:80]}", "Email Queue Error")

        return {
            "status": "success",
            "message": f"Quotation {action} successfully",
            "data": {
                "name": quotation.name,
                "action": action,
                "attachments_count": len(quotation.attachments) if quotation.attachments else 0,
                "email_sent": email_sent,
                "vendor_type": "onboarded" if is_onboarded_vendor else "non_onboarded",
                "vendor_email": vendor_email,
                "items_processed": len(rfq_item_list) if rfq_item_list else 0,
                "child_table_found": child_table_name is not None,
                "child_table_name": child_table_name
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
        import traceback
        error_traceback = traceback.format_exc()
        frappe.log_error(f"Full error traceback:\n{error_traceback[:500]}", "Quotation Creation Error")
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "error_type": "general",
            "debug_info": "Check Error Log for full traceback"
        }


def send_quotation_notification_email(quotation_name, rfq_number, action):
    try:
        
        quotation = frappe.get_doc("Quotation", quotation_name)
        

        rfq = frappe.get_doc("Request For Quotation", rfq_number)
        
        if not rfq.raised_by:
            frappe.log_error(f"No raised_by user found for RFQ {rfq_number}", "Email Notification Error")
            return
        
        employee = frappe.db.get_value(
            "Employee", 
            {"user_id": rfq.raised_by}, 
            ["name", "team", "first_name"]
        )
        
        if not employee:
            frappe.log_error(f"No employee found for user {rfq.raised_by}", "Email Notification Error")
            return
        
        employee_name, team, employee_full_name = employee
        
        if not team:
            frappe.log_error(f"No team found for employee {employee_name} (user: {rfq.raised_by})", "Email Notification Error")
            return
        
        team_employees = frappe.get_all(
            "Employee",
            filters={
                "team": team,
                "status": "Active"
            },
            fields=["user_id", "first_name", "name"]
        )
        
        if not team_employees:
            frappe.log_error(f"No team members found for team {team}", "Email Notification Error")
            return
        
        
        recipients = []
        valid_team_members = []
        
        for emp in team_employees:
            if emp.user_id:  
                user_email = frappe.db.get_value("User", emp.user_id, "email")
                if user_email and frappe.db.get_value("User", emp.user_id, "enabled"):
                    recipients.append(user_email)
                    valid_team_members.append({
                        "name": emp.first_name,
                        "email": user_email,
                        "employee_id": emp.name
                    })
        
        if not recipients:
            frappe.log_error(f"No valid email addresses found for team {team} members", "Email Notification Error")
            return
        
        email_subject = f"New Quotation Created - RFQ: {rfq_number}"
        
        email_template = get_quotation_email_template(quotation, rfq, action, team, employee_full_name)
        
    
        frappe.sendmail(
            recipients=recipients,
            subject=email_subject,
            message=email_template,
            header="New Quotation Created",
            delayed=False  
        )
        
        
        frappe.log_error(
            f"Email sent successfully for quotation {quotation_name} to {len(recipients)} team members from team '{team}': {recipients}",
            "Email Notification Success"
        )
        
        
        frappe.log_error(
            f"Team members notified: {valid_team_members}",
            "Email Team Members Debug"
        )
        
    except Exception as e:
        frappe.log_error(
            f"Failed to send email notification for quotation {quotation_name}: {str(e)}",
            "Email Notification Error"
        )
        import traceback
        frappe.log_error(traceback.format_exc(), "Email Notification Traceback")


def get_quotation_email_template(quotation, rfq, action, team_name, raised_by_name):

    
    quotation_url = f"{frappe.utils.get_url()}/app/quotation/{quotation.name}"
    rfq_url = f"{frappe.utils.get_url()}/app/request-for-quotation/{rfq.name}"
    
    template = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2e7d32;">🎉 New Quotation Created</h2>
        
        <p>Dear {team_name} Team,</p>
        
        <p>A new quotation has been submitted for the RFQ raised by <strong>{raised_by_name}</strong>:</p>
        
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #1976d2;">📋 Quotation Details:</h3>
            <ul style="list-style-type: none; padding: 0;">
                <li><strong>Quotation ID:</strong> {quotation.name}</li>
                <li><strong>RFQ Number:</strong> {rfq.name}</li>
                <li><strong>Quote Amount:</strong> {quotation.get('quote_amount', 'N/A')}</li>
                <li><strong>Rank:</strong> {quotation.get('rank')}</li>
            </ul>
        </div>
        
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #1976d2;">📄 RFQ Details:</h3>
            <ul style="list-style-type: none; padding: 0;">
                <li><strong>RFQ Title:</strong> {rfq.get('title', 'N/A')}</li>
                <li><strong>Raised By:</strong> {raised_by_name} ({rfq.raised_by})</li>
              
            </ul>
        </div>
        
    
        
        
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated notification sent to the {team_name} team when new quotations are created. 
            Please do not reply to this email.
        </p>
    </div>
    """
    
    return template

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






def send_quotation_access_email_simple(quotation, vendor_email, action,rfq_number):
    try:
        site_url = frappe.get_site_config().get('frontend_http', 'https://saksham-v.merillife.com/')
        
        
        token = generate_secure_token(
            email=vendor_email,
            quotation_name=quotation.name,
            rfq_number=rfq_number
        )
        access_link = f"{site_url}/track-quotation?token={token}"
    
        
      
        subject = f"Quotation {action.title()} Successfully - {quotation.name}"
        message = f"""
        <p>Dear Vendor,</p>
        <p>Your quotation <strong>{quotation.name}</strong> has been {action} successfully!</p>
        <p><a href="{access_link}" target="_blank" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Click here to access your quotation or check your rank</a></p>
        <p>Thank you,<br>VMS Team</p>
        """
        
        frappe.sendmail(
            recipients=[vendor_email],
            subject=subject,
            message=message,
            now=True
        )
        
    except Exception as e:
        frappe.log_error(f"Failed to send access email: {str(e)}", "Simple Email Error")



def generate_secure_token(email=None, quotation_name=None,rfq_number=None):
    try:
       
        
        payload = {         
            "email": email,    
            "quotation": quotation_name,
            "rfq_number": rfq_number
        }
        
        
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
        
    except Exception as e:
        frappe.log_error(f"Token generation failed: {str(e)}", "Token Generation Error")
        return None



@frappe.whitelist(allow_guest=True)
def get_quotation_details_by_token():
    try:

        form_data = frappe.local.form_dict
        token = form_data.get('token')
        
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})

        quotation_name = decoded.get('quotation')
        vendor_email = decoded.get('email')
        
        if not quotation_name:
            frappe.throw("Quotation name not found in token", frappe.ValidationError)
        
        try:
            quotation = frappe.get_doc("Quotation", quotation_name)
            quotation_dict = quotation.as_dict()
            
            # Optionally, you can add the vendor email to the response
            quotation_dict['token_vendor_email'] = vendor_email
            
            return {
                "status": "success",
                "data": quotation_dict
            }
            
        except frappe.DoesNotExistError:
            frappe.throw(f"Quotation '{quotation_name}' not found", frappe.DoesNotExistError)
    except Exception as e:
        print(f"Unexpected error in get_quotation_details_by_token: {str(e)}")
        frappe.log_error(f"Error in get_quotation_details_by_token: {str(e)}")
        frappe.throw(f"An error occurred while fetching Quotation details: {str(e)}")