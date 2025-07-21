# import frappe
# from frappe import _
# from frappe.utils import nowdate, now
# import json

# @frappe.whitelist(allow_guest=True, methods=["POST"])
# def save_qms_assessment_smart():

#     try:
#         # Get the request data
#         data = frappe.local.form_dict
        
        
#         vendor_onboarding_input = data.get('vendor_onboarding')
#         ref_no_input = data.get('ref_no')
        
        
#         form_data = data.get('form_data', {})
        

#         if not vendor_onboarding_input or not ref_no_input:
#             return {
#                 "status": "error",
#                 "message": "vendor_onboarding and ref_no are required"
#             }
        
        
#         vendor_onboarding_input = str(vendor_onboarding_input).strip()
#         ref_no_input = str(ref_no_input).strip()
        
        
#         vendor_onboarding_doc = find_vendor_onboarding_document(vendor_onboarding_input)
#         ref_no_doc = find_ref_no_document(ref_no_input)
        
        
#         existing_doc = find_existing_qms_record(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc)
        

#         debug_info = {
#             "input_vendor_onboarding": vendor_onboarding_input,
#             "input_ref_no": ref_no_input,
#             "resolved_vendor_onboarding": vendor_onboarding_doc,
#             "resolved_ref_no": ref_no_doc,
#             "existing_record_found": existing_doc,
#             "search_strategies_used": get_search_strategies_debug(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc)
#         }
        
#         if existing_doc:
            
#             if form_data:

#                 for field_name, field_value in form_data.items():
                    
#                     regular_fields = [
#                         'vendor_name1', 'supplier_company_name', 'name_of_manufacturer_of_supplied_material',
#                         'name_of_parent_company', 'name_of_person', 'designation_of_person', 
#                         'mobile_number', 'title', 'valid_license', 'license_registrations_attach',
#                         'others_certificates', 'area_of_facility', 'no_of_employees', 'defined_areas',
#                         'clean_rooms', 'humidity', 'air_handling_unit', 'pest_control',
#                         'quality_manual', 'organizational_chart', 'qc_independent_of_production',
#                         'regular_review_of_quality_system', 'review_frequency', 'manufacturing',
#                         'manufactruing_process_validate', 'handling_of_start_materials',
#                         'prevent_cross_contamination', 'product_identifiable', 'traceability',
#                         'batch_record', 'duration_of_batch_records', 'quarantined_finish_products',
#                         'storage_of_approved_finished_products', 'nonconforming_materials_removed',
#                         'testing_laboratories', 'analytical_methods_validated', 'testing_or_inspection',
#                         'technical_agreement_labs', 'procedure_for_training', 'maintain_training_records',
#                         'effectiveness_of_training', 'customer_complaints', 'reviews_customer_complaints',
#                         'retain_complaints_records', 'any_recalls', 'calibrations_performed',
#                         'control_and_inspection', 'identification_number', 'water_disposal',
#                         'reporting_environmental_accident', 'safety_committee', 'approved_supplierlist',
#                         'amendent_existing_supplier', 'new_supplier', 'sites_inspected_by',
#                         'inspected_by_others', 'assessment_outcome', 'failure_investigation',
#                         'agreements', 'prior_notification', 'written_authority', 'adequate_sizes',
#                         'person_signature', 'vendor_signature', 'signature', 'ssignature',
#                         'additional_or_supplement_information', 'tissue_supplier'
#                     ]
                    
#                     if field_name in regular_fields:
#                         frappe.db.set_value("Supplier QMS Assessment Form", existing_doc, field_name, field_value)
                

#                 frappe.db.set_value("Supplier QMS Assessment Form", existing_doc, "modified", now())
#                 frappe.db.commit()
#                 action = "updated"
#             else:
#                 action = "loaded"
            
            
#             doc = frappe.get_doc("Supplier QMS Assessment Form", existing_doc)
            
#         else:

#             doc = frappe.new_doc("Supplier QMS Assessment Form")
            
            
#             doc.vendor_onboarding = vendor_onboarding_doc or vendor_onboarding_input
#             doc.ref_no = ref_no_doc or ref_no_input
#             doc.date1 = nowdate()
            
            
#             set_default_values(doc)
            
            
#             if form_data:
#                 update_document_fields(doc, form_data)
            
            
#             doc.insert()
#             frappe.db.commit()  
#             action = "created"
        
  
#         return {
#             "status": "success",
#             "message": f"Record {action} successfully",
#             "action": action,
#             "doc_name": doc.name,
#             "current_data": get_formatted_data(doc),
#             "debug_info": debug_info
#         }
        
#     except Exception as e:
        
#         error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
#         frappe.log_error(f"QMS API Error: {error_msg}")
#         return {
#             "status": "error",
#             "message": str(e)
#         }

# def find_vendor_onboarding_document(input_value):
   
#     try:

#         if frappe.db.exists("Vendor Onboarding", input_value):
#             return input_value
        
        
#         possible_fields = ['vendor_onboarding_id', 'reference_no', 'onboarding_id', 'vendor_id']
        
#         for field in possible_fields:
#             try:

#                 if frappe.db.has_column("Vendor Onboarding", field):
#                     doc_name = frappe.db.get_value("Vendor Onboarding", {field: input_value}, "name")
#                     if doc_name:
#                         return doc_name
#             except:
#                 continue
        
        
#         try:
#             sql_result = frappe.db.sql("""
#                 SELECT name FROM `tabVendor Onboarding` 
#                 WHERE name LIKE %s OR title LIKE %s
#                 LIMIT 1
#             """, (f"%{input_value}%", f"%{input_value}%"))
            
#             if sql_result:
#                 return sql_result[0][0]
#         except:
#             pass
        
   
#         return None
        
#     except Exception as e:
        
#         error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
#         frappe.log_error(f"Vendor onboarding search error: {error_msg}")
#         return None

# def find_ref_no_document(input_value):
#     """
#     Find the actual document name for ref_no from various possible doctypes
#     """
#     try:
        
#         possible_doctypes = ['Vendor Master', 'Supplier', 'Vendor', 'Customer']
        
#         for doctype in possible_doctypes:
#             try:
            
#                 if not frappe.db.exists("DocType", doctype):
#                     continue
                    
           
#                 if frappe.db.exists(doctype, input_value):
#                     return input_value
                
              
#                 possible_fields = ['vendor_id', 'supplier_id', 'reference_no', 'vendor_code', 'supplier_code']
                
#                 for field in possible_fields:
#                     try:
                  
#                         if frappe.db.has_column(doctype, field):
#                             doc_name = frappe.db.get_value(doctype, {field: input_value}, "name")
#                             if doc_name:
#                                 return doc_name
#                     except:
#                         continue
                
              
#                 try:
#                     sql_result = frappe.db.sql(f"""
#                         SELECT name FROM `tab{doctype}` 
#                         WHERE name LIKE %s 
#                         LIMIT 1
#                     """, (f"%{input_value}%",))
                    
#                     if sql_result:
#                         return sql_result[0][0]
#                 except:
#                     continue
                    
#             except:
#                 continue
        
       
#         return None
        
#     except Exception as e:
        
#         error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
#         frappe.log_error(f"Ref no search error: {error_msg}")
#         return None

# def find_existing_qms_record(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc):
  
#     try:
        
#         if vendor_onboarding_doc and ref_no_doc:
#             existing = frappe.db.get_value("Supplier QMS Assessment Form", {
#                 "vendor_onboarding": vendor_onboarding_doc,
#                 "ref_no": ref_no_doc
#             }, "name")
#             if existing:
#                 return existing
        
        
#         existing = frappe.db.get_value("Supplier QMS Assessment Form", {
#             "vendor_onboarding": vendor_onboarding_input,
#             "ref_no": ref_no_input
#         }, "name")
#         if existing:
#             return existing
        
        
#         combinations_to_try = [
#             (vendor_onboarding_doc, ref_no_input),
#             (vendor_onboarding_input, ref_no_doc),
#         ]
        
#         for vo, rn in combinations_to_try:
#             if vo and rn:
#                 existing = frappe.db.get_value("Supplier QMS Assessment Form", {
#                     "vendor_onboarding": vo,
#                     "ref_no": rn
#                 }, "name")
#                 if existing:
#                     return existing
    
#         try:
#             sql_result = frappe.db.sql("""
#                 SELECT name FROM `tabSupplier QMS Assessment Form` 
#                 WHERE vendor_onboarding LIKE %s AND ref_no LIKE %s
#                 LIMIT 1
#             """, (f"%{vendor_onboarding_input}%", f"%{ref_no_input}%"))
            
#             if sql_result:
#                 return sql_result[0][0]
#         except:
#             pass
        
        
#         if vendor_onboarding_doc and ref_no_doc:
#             try:
#                 sql_result = frappe.db.sql("""
#                     SELECT name FROM `tabSupplier QMS Assessment Form` 
#                     WHERE vendor_onboarding LIKE %s AND ref_no LIKE %s
#                     LIMIT 1
#                 """, (f"%{vendor_onboarding_doc}%", f"%{ref_no_doc}%"))
                
#                 if sql_result:
#                     return sql_result[0][0]
#             except:
#                 pass
        
      
#         try:
#             vendor_matches = frappe.db.sql("""
#                 SELECT name, ref_no FROM `tabSupplier QMS Assessment Form` 
#                 WHERE vendor_onboarding = %s
#             """, (vendor_onboarding_input,), as_dict=True)
            
            
#             if len(vendor_matches) == 1:
#                 return vendor_matches[0].name
            
#         except:
#             pass
        

#         try:
#             ref_matches = frappe.db.sql("""
#                 SELECT name, vendor_onboarding FROM `tabSupplier QMS Assessment Form` 
#                 WHERE ref_no = %s
#             """, (ref_no_input,), as_dict=True)
            
            
#             if len(ref_matches) == 1:
#                 return ref_matches[0].name
                
#         except:
#             pass
        
        
#         try:
#             advanced_match = frappe.db.sql("""
#                 SELECT name, vendor_onboarding, ref_no 
#                 FROM `tabSupplier QMS Assessment Form` 
#                 WHERE (vendor_onboarding LIKE %s OR vendor_onboarding LIKE %s)
#                 AND (ref_no LIKE %s OR ref_no LIKE %s)
#                 LIMIT 1
#             """, (
#                 f"%{vendor_onboarding_input}%", 
#                 f"%{vendor_onboarding_doc}%" if vendor_onboarding_doc else "%none%",
#                 f"%{ref_no_input}%", 
#                 f"%{ref_no_doc}%" if ref_no_doc else "%none%"
#             ))
            
#             if advanced_match:
#                 return advanced_match[0][0]
#         except:
#             pass
        

#         return None
        
#     except Exception as e:
        
#         error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
#         frappe.log_error(f"QMS record search error: {error_msg}")
#         return None

# def set_default_values(doc):
#     """Set default values for new documents"""
#     doc.docstatus = 0
#     doc.status = "Draft"
#     doc.company = "7000-Meril Diagnostics Private Limited"
#     doc.organization_name = "Meril"

# def update_document_fields(doc, form_data):
   
    

#     regular_fields = [
#         'vendor_name1', 'supplier_company_name', 'name_of_manufacturer_of_supplied_material',
#         'name_of_parent_company', 'name_of_person', 'designation_of_person', 
#         'mobile_number', 'title', 'valid_license', 'license_registrations_attach',
#         'others_certificates', 'area_of_facility', 'no_of_employees', 'defined_areas',
#         'clean_rooms', 'humidity', 'air_handling_unit', 'pest_control',
#         'quality_manual', 'organizational_chart', 'qc_independent_of_production',
#         'regular_review_of_quality_system', 'review_frequency', 'manufacturing',
#         'manufactruing_process_validate', 'handling_of_start_materials',
#         'prevent_cross_contamination', 'product_identifiable', 'traceability',
#         'batch_record', 'duration_of_batch_records', 'quarantined_finish_products',
#         'storage_of_approved_finished_products', 'nonconforming_materials_removed',
#         'testing_laboratories', 'analytical_methods_validated', 'testing_or_inspection',
#         'technical_agreement_labs', 'procedure_for_training', 'maintain_training_records',
#         'effectiveness_of_training', 'customer_complaints', 'reviews_customer_complaints',
#         'retain_complaints_records', 'any_recalls', 'calibrations_performed',
#         'control_and_inspection', 'identification_number', 'water_disposal',
#         'reporting_environmental_accident', 'safety_committee', 'approved_supplierlist',
#         'amendent_existing_supplier', 'new_supplier', 'sites_inspected_by',
#         'inspected_by_others', 'assessment_outcome', 'failure_investigation',
#         'agreements', 'prior_notification', 'written_authority', 'adequate_sizes',
#         'person_signature', 'vendor_signature', 'signature', 'ssignature',
#         'additional_or_supplement_information', 'tissue_supplier'
#     ]
    

#     for field_name in regular_fields:
#         if field_name in form_data:
            
#             field_value = form_data[field_name]
#             setattr(doc, field_name, field_value)
    

#     child_tables = {
#         'details_of_batch_records': 'details_of_batch_records',
#         'quality_control_system': 'quality_control_system',
#         'have_documentsprocedure': 'have_documentsprocedure',
#         'inspection_reports': 'inspection_reports',
#         'products_in_qa': 'products_in_qa',
#         'if_yes_for_prior_notification': 'if_yes_for_prior_notification',
#         'mlspl_qa_list': 'mlspl_qa_list'
#     }
    
#     for table_field, table_name in child_tables.items():
#         if table_field in form_data:
            
#             doc.set(table_field, [])
            
            
#             table_data = form_data.get(table_field, [])
#             if isinstance(table_data, list):
#                 for row_data in table_data:
#                     if isinstance(row_data, dict):
#                         doc.append(table_field, row_data)

# def get_formatted_data(doc):
#     """
#     Return document data in a format suitable for frontend
#     """
#     doc_dict = doc.as_dict()
    

#     system_fields = [
#         'docstatus', 'idx', 'owner', 'creation', 'modified', 'modified_by',
#         '__last_sync_on', 'doctype', 'for_company_2000', 'for_company_7000',
#         'mail_sent_to_qa_team'
#     ]
    
#     for field in system_fields:
#         doc_dict.pop(field, None)
    
#     return doc_dict

# def get_search_strategies_debug(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc):
  
#     debug_results = {}
    
#     try:

#         debug_results["exact_input_combination"] = frappe.db.exists("Supplier QMS Assessment Form", {
#             "vendor_onboarding": vendor_onboarding_input,
#             "ref_no": ref_no_input
#         })
        
#         if vendor_onboarding_doc and ref_no_doc:
#             debug_results["exact_resolved_combination"] = frappe.db.exists("Supplier QMS Assessment Form", {
#                 "vendor_onboarding": vendor_onboarding_doc,
#                 "ref_no": ref_no_doc
#             })
        

#         vendor_matches = frappe.db.sql("""
#             SELECT name, ref_no FROM `tabSupplier QMS Assessment Form` 
#             WHERE vendor_onboarding = %s
#         """, (vendor_onboarding_input,), as_dict=True)
        
#         ref_matches = frappe.db.sql("""
#             SELECT name, vendor_onboarding FROM `tabSupplier QMS Assessment Form` 
#             WHERE ref_no = %s
#         """, (ref_no_input,), as_dict=True)
        
#         debug_results["vendor_onboarding_matches"] = len(vendor_matches)
#         debug_results["ref_no_matches"] = len(ref_matches)
#         debug_results["vendor_match_details"] = vendor_matches[:3]  
#         debug_results["ref_match_details"] = ref_matches[:3]  
        
#     except Exception as e:
#         debug_results["debug_error"] = str(e)[:50]
    
#     return debug_results




import frappe
from frappe import _
from frappe.utils import nowdate, now
import json
import base64
import os

@frappe.whitelist(allow_guest=True, methods=["POST"])
def save_qms_assessment_complete():
    """
    Complete API to create or update QMS Assessment Form with support for:
    - Regular fields
    - Attachment fields
    - Table fields
    - Table MultiSelect fields
    - Signature fields
    
    UPDATE BEHAVIOR:
    - Only fields provided in the request will be updated
    - Fields not included in the request remain unchanged
    - Empty/null values will clear the field
    - For tables: entire table is replaced with new data
    - For attachments: only provided attachments are updated
    """
    try:
        # Get the request data
        data = frappe.local.form_dict
        
        vendor_onboarding_input = data.get('vendor_onboarding')
        ref_no_input = data.get('ref_no')
        form_data = data.get('data', {})
        attachments_data = data.get('attachments', {})
        signatures_data = data.get('signatures', {})
        
        # Validate required fields
        if not vendor_onboarding_input or not ref_no_input:
            return {
                "status": "error",
                "message": "vendor_onboarding and ref_no are required"
            }
        
        # Clean inputs
        vendor_onboarding_input = str(vendor_onboarding_input).strip()
        ref_no_input = str(ref_no_input).strip()
        
        # Find related documents
        vendor_onboarding_doc = find_vendor_onboarding_document(vendor_onboarding_input)
        ref_no_doc = find_ref_no_document(ref_no_input)
        
        # Check for existing record
        existing_doc = find_existing_qms_record(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc)
        
        debug_info = {
            "input_vendor_onboarding": vendor_onboarding_input,
            "input_ref_no": ref_no_input,
            "resolved_vendor_onboarding": vendor_onboarding_doc,
            "resolved_ref_no": ref_no_doc,
            "existing_record_found": existing_doc,
            "search_strategies_used": get_search_strategies_debug(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc)
        }
        
        if existing_doc:
            # Update existing document
            doc = frappe.get_doc("Supplier QMS Assessment Form", existing_doc)
            
            if form_data or attachments_data or signatures_data:
                # Update regular fields
                update_regular_fields(doc, form_data)
                
                # Handle attachment fields
                handle_attachment_fields(doc, attachments_data)
                
                # Handle signature fields
                handle_signature_fields(doc, signatures_data)
                
                # Handle table fields
                handle_table_fields(doc, form_data)
                
                # Handle table multiselect fields
                handle_table_multiselect_fields(doc, form_data)
                
                # Update multiselect_data_json for processing
                update_multiselect_json(doc, form_data)
                
                # Save the document
                doc.save()
                frappe.db.commit()
                action = "updated"
            else:
                action = "loaded"
                
        else:
            # Create new document
            doc = frappe.new_doc("Supplier QMS Assessment Form")
            
            # Set basic fields
            doc.vendor_onboarding = vendor_onboarding_doc or vendor_onboarding_input
            doc.ref_no = ref_no_doc or ref_no_input
            doc.date1 = nowdate()
            
            # Set default values
            set_default_values(doc)
            
            # Update with form data
            if form_data:
                update_regular_fields(doc, form_data)
                handle_table_fields(doc, form_data)
                handle_table_multiselect_fields(doc, form_data)
                update_multiselect_json(doc, form_data)
            
            # Handle attachments and signatures for new document
            if attachments_data:
                handle_attachment_fields(doc, attachments_data)
                
            if signatures_data:
                handle_signature_fields(doc, signatures_data)
            
            # Insert the document
            doc.insert()
            frappe.db.commit()
            action = "created"
        
        return {
            "status": "success",
            "message": f"Record {action} successfully",
            "action": action,
            "doc_name": doc.name,
            "current_data": get_formatted_data(doc),
            "debug_info": debug_info
        }
        
    except Exception as e:
        error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
        frappe.log_error(f"QMS API Error: {error_msg}")
        return {
            "status": "error",
            "message": str(e)
        }

def update_regular_fields(doc, form_data):
    """Update regular fields in the document"""
    regular_fields = [
        'vendor_name1', 'supplier_company_name', 'name_of_manufacturer_of_supplied_material',
        'name_of_parent_company', 'name_of_person', 'designation_of_person', 
        'mobile_number', 'title', 'valid_license', 'others_certificates', 
        'area_of_facility', 'no_of_employees', 'defined_areas', 'clean_rooms', 
        'humidity', 'air_handling_unit', 'pest_control', 'organizational_chart', 
        'qc_independent_of_production', 'regular_review_of_quality_system', 
        'review_frequency', 'manufacturing', 'manufactruing_process_validate', 
        'handling_of_start_materials', 'prevent_cross_contamination', 'product_identifiable', 
        'traceability', 'batch_record', 'duration_of_batch_records', 'quarantined_finish_products',
        'storage_of_approved_finished_products', 'nonconforming_materials_removed',
        'testing_laboratories', 'analytical_methods_validated', 'testing_or_inspection',
        'procedure_for_training', 'maintain_training_records', 'effectiveness_of_training', 
        'customer_complaints', 'reviews_customer_complaints', 'retain_complaints_records', 
        'any_recalls', 'calibrations_performed', 'control_and_inspection', 'identification_number', 
        'water_disposal', 'reporting_environmental_accident', 'safety_committee', 
        'approved_supplierlist', 'amendent_existing_supplier', 'new_supplier', 
        'sites_inspected_by', 'inspected_by_others', 'assessment_outcome', 
        'failure_investigation', 'agreements', 'prior_notification', 'written_authority', 
        'adequate_sizes', 'additional_or_supplement_information', 'conclusion_by_meril',
        'performer_name', 'performer_title', 'performent_date', 'mdpl_qa_date',
        'signed_date', 'name1', 'date', 'vendor_name', 'status', 'qms_form_status',
        'for_company_2000', 'for_company_7000', 'organization_name'
    ]
    
    for field_name in regular_fields:
        if field_name in form_data:
            field_value = form_data[field_name]
            setattr(doc, field_name, field_value)

def handle_attachment_fields(doc, attachments_data):
    """Handle attachment fields with base64 encoded files"""
    attachment_fields = [
        'license_registrations_attach', 'quality_manual', 'signature', 
        'performer_signature', 'tissue_supplier', 'new_supplier', 
        'technical_agreement_labs', 'amendent_existing_supplier'
    ]
    
    for field_name in attachment_fields:
        if field_name in attachments_data:
            attachment_info = attachments_data[field_name]
            
            if isinstance(attachment_info, dict):
                file_content = attachment_info.get('content')  # base64 encoded
                file_name = attachment_info.get('filename')
                file_type = attachment_info.get('content_type', 'application/octet-stream')
                
                if file_content and file_name:
                    try:
                        # Decode base64 content
                        file_data = base64.b64decode(file_content)
                        
                        # Create file document
                        file_doc = frappe.get_doc({
                            "doctype": "File",
                            "file_name": file_name,
                            "content": file_data,
                            "decode": False,
                            "is_private": 1,
                            "attached_to_doctype": "Supplier QMS Assessment Form",
                            "attached_to_name": doc.name if doc.name else None
                        })
                        file_doc.insert()
                        
                        # Set the file URL to the field
                        setattr(doc, field_name, file_doc.file_url)
                        
                    except Exception as e:
                        frappe.log_error(f"Error handling attachment {field_name}: {str(e)}")
            
            elif isinstance(attachment_info, str):
                # Direct file URL or path
                setattr(doc, field_name, attachment_info)

def handle_signature_fields(doc, signatures_data):
    """Handle signature fields (Signature fieldtype)"""
    signature_fields = [
        'vendor_signature', 'person_signature', 'performer_esignature', 'ssignature'
    ]
    
    for field_name in signature_fields:
        if field_name in signatures_data:
            signature_value = signatures_data[field_name]
            
            if isinstance(signature_value, dict):
                # Handle base64 signature data
                signature_data = signature_value.get('signature_data') or signature_value.get('content')
                if signature_data:
                    setattr(doc, field_name, signature_data)
            elif isinstance(signature_value, str):
                # Direct signature data string
                setattr(doc, field_name, signature_value)

def handle_table_fields(doc, form_data):
    """Handle regular table fields"""
    table_fields = {
        'products_in_qa': 'QA List of Products',
        'mlspl_qa_list': 'MLSPL QA Table'
    }
    
    for table_field, child_doctype in table_fields.items():
        if table_field in form_data:
            table_data = form_data.get(table_field, [])
            
            if isinstance(table_data, list):
                # Clear existing rows
                doc.set(table_field, [])
                
                # Add new rows
                for row_data in table_data:
                    if isinstance(row_data, dict):
                        child_doc = doc.append(table_field)
                        
                        # Handle QA List of Products fields
                        if child_doctype == 'QA List of Products':
                            child_doc.name_of_the_purchased_material__processes = row_data.get('name_of_the_purchased_material__processes', '')
                            child_doc.specifications = row_data.get('specifications', '')
                            
                            # Alternative field names for flexibility
                            if not child_doc.name_of_the_purchased_material__processes:
                                child_doc.name_of_the_purchased_material__processes = (
                                    row_data.get('product_name') or 
                                    row_data.get('material_name') or 
                                    row_data.get('name', '')
                                )
                        
                        # Handle MLSPL QA Table fields
                        elif child_doctype == 'MLSPL QA Table':
                            child_doc.document_type = row_data.get('document_type', '')
                            
                            # Handle qa_attachment if provided
                            if 'qa_attachment' in row_data:
                                attachment_data = row_data['qa_attachment']
                                if isinstance(attachment_data, dict):
                                    # Handle base64 attachment
                                    file_content = attachment_data.get('content')
                                    file_name = attachment_data.get('filename')
                                    if file_content and file_name:
                                        try:
                                            file_data = base64.b64decode(file_content)
                                            file_doc = frappe.get_doc({
                                                "doctype": "File",
                                                "file_name": file_name,
                                                "content": file_data,
                                                "decode": False,
                                                "is_private": 1
                                            })
                                            file_doc.insert()
                                            child_doc.qa_attachment = file_doc.file_url
                                        except Exception as e:
                                            frappe.log_error(f"Error handling table attachment: {str(e)}")
                                elif isinstance(attachment_data, str):
                                    # Direct file URL
                                    child_doc.qa_attachment = attachment_data

def handle_table_multiselect_fields(doc, form_data):
    """Handle table multiselect fields"""
    table_multiselect_fields = {
        'quality_control_system': 'QMS Quality Control',
        'have_documentsprocedure': 'QMS Procedure Doc',
        'if_yes_for_prior_notification': 'QMS Prior Notification Table',
        'inspection_reports': 'QMS Inspection Report Table',
        'details_of_batch_records': 'QMS Batch Record Table'
    }
    
    for table_field, child_doctype in table_multiselect_fields.items():
        if table_field in form_data:
            table_data = form_data.get(table_field, [])
            
            if isinstance(table_data, list):
                # Clear existing rows
                doc.set(table_field, [])
                
                # Add new rows
                for row_data in table_data:
                    child_doc = doc.append(table_field)
                    
                    if isinstance(row_data, dict):
                        # Handle specific field mappings for each table multiselect
                        if child_doctype == 'QMS Quality Control':
                            # Links to QMS Quality Control System
                            link_value = row_data.get('qms_quality_control') or row_data.get('name') or row_data.get('value')
                            if link_value:
                                # Ensure the linked document exists or create it
                                if not frappe.db.exists("QMS Quality Control System", link_value):
                                    create_quality_control_system(link_value)
                                child_doc.qms_quality_control = link_value
                        
                        elif child_doctype == 'QMS Procedure Doc':
                            # Links to QMS Procedure Doc Name
                            link_value = row_data.get('qms_procedure_doc') or row_data.get('name') or row_data.get('value')
                            if link_value:
                                if not frappe.db.exists("QMS Procedure Doc Name", link_value):
                                    create_procedure_doc_name(link_value)
                                child_doc.qms_procedure_doc = link_value
                        
                        elif child_doctype == 'QMS Prior Notification Table':
                            # Links to QMS Prior Notification
                            link_value = row_data.get('qms_prior_notification') or row_data.get('name') or row_data.get('value')
                            if link_value:
                                if not frappe.db.exists("QMS Prior Notification", link_value):
                                    create_prior_notification(link_value)
                                child_doc.qms_prior_notification = link_value
                        
                        elif child_doctype == 'QMS Inspection Report Table':
                            # Links to QMS Inspection Reports
                            link_value = row_data.get('qms_inspection_report') or row_data.get('name') or row_data.get('value')
                            if link_value:
                                if not frappe.db.exists("QMS Inspection Reports", link_value):
                                    create_inspection_report(link_value)
                                child_doc.qms_inspection_report = link_value
                        
                        elif child_doctype == 'QMS Batch Record Table':
                            # Links to QMS Batch Record Details
                            link_value = row_data.get('qms_batch_record') or row_data.get('name') or row_data.get('value')
                            if link_value:
                                if not frappe.db.exists("QMS Batch Record Details", link_value):
                                    create_batch_record_details(link_value)
                                child_doc.qms_batch_record = link_value
                    
                    elif isinstance(row_data, str):
                        # For simple string values - treat entire string as single document name
                        if child_doctype == 'QMS Quality Control':
                            if not frappe.db.exists("QMS Quality Control System", row_data):
                                create_quality_control_system(row_data)
                            child_doc.qms_quality_control = row_data
                        elif child_doctype == 'QMS Procedure Doc':
                            if not frappe.db.exists("QMS Procedure Doc Name", row_data):
                                create_procedure_doc_name(row_data)
                            child_doc.qms_procedure_doc = row_data
                        elif child_doctype == 'QMS Prior Notification Table':
                            if not frappe.db.exists("QMS Prior Notification", row_data):
                                create_prior_notification(row_data)
                            child_doc.qms_prior_notification = row_data
                        elif child_doctype == 'QMS Inspection Report Table':
                            if not frappe.db.exists("QMS Inspection Reports", row_data):
                                create_inspection_report(row_data)
                            child_doc.qms_inspection_report = row_data
                        elif child_doctype == 'QMS Batch Record Table':
                            if not frappe.db.exists("QMS Batch Record Details", row_data):
                                create_batch_record_details(row_data)
                            child_doc.qms_batch_record = row_data

def update_multiselect_json(doc, form_data):
    """Update the multiselect_data_json field for processing by document hooks"""
    multiselect_fields = [
        'quality_control_system', 'have_documentsprocedure', 
        'if_yes_for_prior_notification', 'inspection_reports', 
        'details_of_batch_records'
    ]
    
    json_data = {"data": {}}
    
    for field in multiselect_fields:
        if field in form_data:
            field_data = form_data[field]
            if isinstance(field_data, list):
                # Convert list to array format for proper processing
                values = []
                for item in field_data:
                    if isinstance(item, dict):
                        value = (item.get('qms_quality_control') or 
                                item.get('qms_procedure_doc') or 
                                item.get('qms_prior_notification') or 
                                item.get('qms_inspection_report') or 
                                item.get('qms_batch_record') or
                                item.get('value') or 
                                item.get('name'))
                        if value:
                            values.append({"name": str(value), "value": str(value)})
                    elif isinstance(item, str):
                        values.append({"name": item, "value": item})
                
                if values:
                    json_data["data"][field] = values
            
            elif isinstance(field_data, str):
                # Handle single string value
                json_data["data"][field] = [{"name": field_data, "value": field_data}]
    
    if json_data["data"]:
        doc.multiselect_data_json = json.dumps(json_data)

# Helper functions to create linked documents
def create_quality_control_system(name):
    """Create QMS Quality Control System document if it doesn't exist"""
    try:
        doc = frappe.get_doc({
            "doctype": "QMS Quality Control System",
            "quality_control_system": name
        })
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception as e:
        frappe.log_error(f"Error creating QMS Quality Control System: {str(e)}")
        return None

def create_procedure_doc_name(name):
    """Create QMS Procedure Doc Name document if it doesn't exist"""
    try:
        doc = frappe.get_doc({
            "doctype": "QMS Procedure Doc Name",
            "procedure_doc_name": name
        })
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception as e:
        frappe.log_error(f"Error creating QMS Procedure Doc Name: {str(e)}")
        return None

def create_prior_notification(name):
    """Create QMS Prior Notification document if it doesn't exist"""
    try:
        doc = frappe.get_doc({
            "doctype": "QMS Prior Notification",
            "prior_notification": name
        })
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception as e:
        frappe.log_error(f"Error creating QMS Prior Notification: {str(e)}")
        return None

def create_inspection_report(name):
    """Create QMS Inspection Reports document if it doesn't exist"""
    try:
        doc = frappe.get_doc({
            "doctype": "QMS Inspection Reports",
            "inspection_report": name
        })
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception as e:
        frappe.log_error(f"Error creating QMS Inspection Reports: {str(e)}")
        return None

def create_batch_record_details(name):
    """Create QMS Batch Record Details document if it doesn't exist"""
    try:
        doc = frappe.get_doc({
            "doctype": "QMS Batch Record Details",
            "details_of_batch_record": name
        })
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception as e:
        frappe.log_error(f"Error creating QMS Batch Record Details: {str(e)}")
        return None

def find_vendor_onboarding_document(input_value):
    """Find the actual document name for vendor_onboarding"""
    try:
        # Direct name match
        if frappe.db.exists("Vendor Onboarding", input_value):
            return input_value
        
        # Search by possible fields
        possible_fields = ['vendor_onboarding_id', 'reference_no', 'onboarding_id', 'vendor_id']
        
        for field in possible_fields:
            try:
                if frappe.db.has_column("Vendor Onboarding", field):
                    doc_name = frappe.db.get_value("Vendor Onboarding", {field: input_value}, "name")
                    if doc_name:
                        return doc_name
            except:
                continue
        
        # Fuzzy search
        try:
            sql_result = frappe.db.sql("""
                SELECT name FROM `tabVendor Onboarding` 
                WHERE name LIKE %s OR title LIKE %s
                LIMIT 1
            """, (f"%{input_value}%", f"%{input_value}%"))
            
            if sql_result:
                return sql_result[0][0]
        except:
            pass
        
        return None
        
    except Exception as e:
        error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        frappe.log_error(f"Vendor onboarding search error: {error_msg}")
        return None

def find_ref_no_document(input_value):
    """Find the actual document name for ref_no from various possible doctypes"""
    try:
        possible_doctypes = ['Vendor Master', 'Supplier', 'Vendor', 'Customer']
        
        for doctype in possible_doctypes:
            try:
                if not frappe.db.exists("DocType", doctype):
                    continue
                    
                if frappe.db.exists(doctype, input_value):
                    return input_value
                
                possible_fields = ['vendor_id', 'supplier_id', 'reference_no', 'vendor_code', 'supplier_code']
                
                for field in possible_fields:
                    try:
                        if frappe.db.has_column(doctype, field):
                            doc_name = frappe.db.get_value(doctype, {field: input_value}, "name")
                            if doc_name:
                                return doc_name
                    except:
                        continue
                
                try:
                    sql_result = frappe.db.sql(f"""
                        SELECT name FROM `tab{doctype}` 
                        WHERE name LIKE %s 
                        LIMIT 1
                    """, (f"%{input_value}%",))
                    
                    if sql_result:
                        return sql_result[0][0]
                except:
                    continue
                    
            except:
                continue
        
        return None
        
    except Exception as e:
        error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        frappe.log_error(f"Ref no search error: {error_msg}")
        return None

def find_existing_qms_record(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc):
    """Find existing QMS Assessment record with multiple strategies"""
    try:
        # Exact match with resolved documents
        if vendor_onboarding_doc and ref_no_doc:
            existing = frappe.db.get_value("Supplier QMS Assessment Form", {
                "vendor_onboarding": vendor_onboarding_doc,
                "ref_no": ref_no_doc
            }, "name")
            if existing:
                return existing
        
        # Exact match with input values
        existing = frappe.db.get_value("Supplier QMS Assessment Form", {
            "vendor_onboarding": vendor_onboarding_input,
            "ref_no": ref_no_input
        }, "name")
        if existing:
            return existing
        
        # Mixed combinations
        combinations_to_try = [
            (vendor_onboarding_doc, ref_no_input),
            (vendor_onboarding_input, ref_no_doc),
        ]
        
        for vo, rn in combinations_to_try:
            if vo and rn:
                existing = frappe.db.get_value("Supplier QMS Assessment Form", {
                    "vendor_onboarding": vo,
                    "ref_no": rn
                }, "name")
                if existing:
                    return existing
        
        # Fuzzy search
        try:
            sql_result = frappe.db.sql("""
                SELECT name FROM `tabSupplier QMS Assessment Form` 
                WHERE vendor_onboarding LIKE %s AND ref_no LIKE %s
                LIMIT 1
            """, (f"%{vendor_onboarding_input}%", f"%{ref_no_input}%"))
            
            if sql_result:
                return sql_result[0][0]
        except:
            pass
        
        return None
        
    except Exception as e:
        error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        frappe.log_error(f"QMS record search error: {error_msg}")
        return None

def set_default_values(doc):
    """Set default values for new documents"""
    doc.docstatus = 0
    doc.status = "Draft"
    doc.company = "7000-Meril Diagnostics Private Limited"
    doc.organization_name = "Meril"

def get_formatted_data(doc):
    """Return document data in a format suitable for frontend"""
    doc_dict = doc.as_dict()
    
    # Remove system fields
    system_fields = [
        'docstatus', 'idx', 'owner', 'creation', 'modified', 'modified_by',
        '__last_sync_on', 'doctype'
    ]
    
    for field in system_fields:
        doc_dict.pop(field, None)
    
    return doc_dict

def get_search_strategies_debug(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc):
    """Debug information for search strategies"""
    debug_results = {}
    
    try:
        debug_results["exact_input_combination"] = frappe.db.exists("Supplier QMS Assessment Form", {
            "vendor_onboarding": vendor_onboarding_input,
            "ref_no": ref_no_input
        })
        
        if vendor_onboarding_doc and ref_no_doc:
            debug_results["exact_resolved_combination"] = frappe.db.exists("Supplier QMS Assessment Form", {
                "vendor_onboarding": vendor_onboarding_doc,
                "ref_no": ref_no_doc
            })
        
        vendor_matches = frappe.db.sql("""
            SELECT name, ref_no FROM `tabSupplier QMS Assessment Form` 
            WHERE vendor_onboarding = %s
        """, (vendor_onboarding_input,), as_dict=True)
        
        ref_matches = frappe.db.sql("""
            SELECT name, vendor_onboarding FROM `tabSupplier QMS Assessment Form` 
            WHERE ref_no = %s
        """, (ref_no_input,), as_dict=True)
        
        debug_results["vendor_onboarding_matches"] = len(vendor_matches)
        debug_results["ref_no_matches"] = len(ref_matches)
        debug_results["vendor_match_details"] = vendor_matches[:3]
        debug_results["ref_match_details"] = ref_matches[:3]
        
    except Exception as e:
        debug_results["debug_error"] = str(e)[:50]
    
    return debug_results