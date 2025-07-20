import frappe
from frappe import _
from frappe.utils import nowdate, now
import json

@frappe.whitelist(allow_guest=True, methods=["POST"])
def save_qms_assessment_smart():

    try:
        # Get the request data
        data = frappe.local.form_dict
        
        
        vendor_onboarding_input = data.get('vendor_onboarding')
        ref_no_input = data.get('ref_no')
        
        
        form_data = data.get('form_data', {})
        

        if not vendor_onboarding_input or not ref_no_input:
            return {
                "status": "error",
                "message": "vendor_onboarding and ref_no are required"
            }
        
        
        vendor_onboarding_input = str(vendor_onboarding_input).strip()
        ref_no_input = str(ref_no_input).strip()
        
        
        vendor_onboarding_doc = find_vendor_onboarding_document(vendor_onboarding_input)
        ref_no_doc = find_ref_no_document(ref_no_input)
        
        
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
            
            if form_data:

                for field_name, field_value in form_data.items():
                    
                    regular_fields = [
                        'vendor_name1', 'supplier_company_name', 'name_of_manufacturer_of_supplied_material',
                        'name_of_parent_company', 'name_of_person', 'designation_of_person', 
                        'mobile_number', 'title', 'valid_license', 'license_registrations_attach',
                        'others_certificates', 'area_of_facility', 'no_of_employees', 'defined_areas',
                        'clean_rooms', 'humidity', 'air_handling_unit', 'pest_control',
                        'quality_manual', 'organizational_chart', 'qc_independent_of_production',
                        'regular_review_of_quality_system', 'review_frequency', 'manufacturing',
                        'manufactruing_process_validate', 'handling_of_start_materials',
                        'prevent_cross_contamination', 'product_identifiable', 'traceability',
                        'batch_record', 'duration_of_batch_records', 'quarantined_finish_products',
                        'storage_of_approved_finished_products', 'nonconforming_materials_removed',
                        'testing_laboratories', 'analytical_methods_validated', 'testing_or_inspection',
                        'technical_agreement_labs', 'procedure_for_training', 'maintain_training_records',
                        'effectiveness_of_training', 'customer_complaints', 'reviews_customer_complaints',
                        'retain_complaints_records', 'any_recalls', 'calibrations_performed',
                        'control_and_inspection', 'identification_number', 'water_disposal',
                        'reporting_environmental_accident', 'safety_committee', 'approved_supplierlist',
                        'amendent_existing_supplier', 'new_supplier', 'sites_inspected_by',
                        'inspected_by_others', 'assessment_outcome', 'failure_investigation',
                        'agreements', 'prior_notification', 'written_authority', 'adequate_sizes',
                        'person_signature', 'vendor_signature', 'signature', 'ssignature',
                        'additional_or_supplement_information', 'tissue_supplier'
                    ]
                    
                    if field_name in regular_fields:
                        frappe.db.set_value("Supplier QMS Assessment Form", existing_doc, field_name, field_value)
                

                frappe.db.set_value("Supplier QMS Assessment Form", existing_doc, "modified", now())
                frappe.db.commit()
                action = "updated"
            else:
                action = "loaded"
            
            
            doc = frappe.get_doc("Supplier QMS Assessment Form", existing_doc)
            
        else:

            doc = frappe.new_doc("Supplier QMS Assessment Form")
            
            
            doc.vendor_onboarding = vendor_onboarding_doc or vendor_onboarding_input
            doc.ref_no = ref_no_doc or ref_no_input
            doc.date1 = nowdate()
            
            
            set_default_values(doc)
            
            
            if form_data:
                update_document_fields(doc, form_data)
            
            
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
        
        error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        frappe.log_error(f"QMS API Error: {error_msg}")
        return {
            "status": "error",
            "message": str(e)
        }

def find_vendor_onboarding_document(input_value):
   
    try:

        if frappe.db.exists("Vendor Onboarding", input_value):
            return input_value
        
        
        possible_fields = ['vendor_onboarding_id', 'reference_no', 'onboarding_id', 'vendor_id']
        
        for field in possible_fields:
            try:

                if frappe.db.has_column("Vendor Onboarding", field):
                    doc_name = frappe.db.get_value("Vendor Onboarding", {field: input_value}, "name")
                    if doc_name:
                        return doc_name
            except:
                continue
        
        
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
    """
    Find the actual document name for ref_no from various possible doctypes
    """
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
  
    try:
        
        if vendor_onboarding_doc and ref_no_doc:
            existing = frappe.db.get_value("Supplier QMS Assessment Form", {
                "vendor_onboarding": vendor_onboarding_doc,
                "ref_no": ref_no_doc
            }, "name")
            if existing:
                return existing
        
        
        existing = frappe.db.get_value("Supplier QMS Assessment Form", {
            "vendor_onboarding": vendor_onboarding_input,
            "ref_no": ref_no_input
        }, "name")
        if existing:
            return existing
        
        
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
        
        
        if vendor_onboarding_doc and ref_no_doc:
            try:
                sql_result = frappe.db.sql("""
                    SELECT name FROM `tabSupplier QMS Assessment Form` 
                    WHERE vendor_onboarding LIKE %s AND ref_no LIKE %s
                    LIMIT 1
                """, (f"%{vendor_onboarding_doc}%", f"%{ref_no_doc}%"))
                
                if sql_result:
                    return sql_result[0][0]
            except:
                pass
        
      
        try:
            vendor_matches = frappe.db.sql("""
                SELECT name, ref_no FROM `tabSupplier QMS Assessment Form` 
                WHERE vendor_onboarding = %s
            """, (vendor_onboarding_input,), as_dict=True)
            
            
            if len(vendor_matches) == 1:
                return vendor_matches[0].name
            
        except:
            pass
        

        try:
            ref_matches = frappe.db.sql("""
                SELECT name, vendor_onboarding FROM `tabSupplier QMS Assessment Form` 
                WHERE ref_no = %s
            """, (ref_no_input,), as_dict=True)
            
            
            if len(ref_matches) == 1:
                return ref_matches[0].name
                
        except:
            pass
        
        
        try:
            advanced_match = frappe.db.sql("""
                SELECT name, vendor_onboarding, ref_no 
                FROM `tabSupplier QMS Assessment Form` 
                WHERE (vendor_onboarding LIKE %s OR vendor_onboarding LIKE %s)
                AND (ref_no LIKE %s OR ref_no LIKE %s)
                LIMIT 1
            """, (
                f"%{vendor_onboarding_input}%", 
                f"%{vendor_onboarding_doc}%" if vendor_onboarding_doc else "%none%",
                f"%{ref_no_input}%", 
                f"%{ref_no_doc}%" if ref_no_doc else "%none%"
            ))
            
            if advanced_match:
                return advanced_match[0][0]
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

def update_document_fields(doc, form_data):
   
    

    regular_fields = [
        'vendor_name1', 'supplier_company_name', 'name_of_manufacturer_of_supplied_material',
        'name_of_parent_company', 'name_of_person', 'designation_of_person', 
        'mobile_number', 'title', 'valid_license', 'license_registrations_attach',
        'others_certificates', 'area_of_facility', 'no_of_employees', 'defined_areas',
        'clean_rooms', 'humidity', 'air_handling_unit', 'pest_control',
        'quality_manual', 'organizational_chart', 'qc_independent_of_production',
        'regular_review_of_quality_system', 'review_frequency', 'manufacturing',
        'manufactruing_process_validate', 'handling_of_start_materials',
        'prevent_cross_contamination', 'product_identifiable', 'traceability',
        'batch_record', 'duration_of_batch_records', 'quarantined_finish_products',
        'storage_of_approved_finished_products', 'nonconforming_materials_removed',
        'testing_laboratories', 'analytical_methods_validated', 'testing_or_inspection',
        'technical_agreement_labs', 'procedure_for_training', 'maintain_training_records',
        'effectiveness_of_training', 'customer_complaints', 'reviews_customer_complaints',
        'retain_complaints_records', 'any_recalls', 'calibrations_performed',
        'control_and_inspection', 'identification_number', 'water_disposal',
        'reporting_environmental_accident', 'safety_committee', 'approved_supplierlist',
        'amendent_existing_supplier', 'new_supplier', 'sites_inspected_by',
        'inspected_by_others', 'assessment_outcome', 'failure_investigation',
        'agreements', 'prior_notification', 'written_authority', 'adequate_sizes',
        'person_signature', 'vendor_signature', 'signature', 'ssignature',
        'additional_or_supplement_information', 'tissue_supplier'
    ]
    

    for field_name in regular_fields:
        if field_name in form_data:
            
            field_value = form_data[field_name]
            setattr(doc, field_name, field_value)
    

    child_tables = {
        'details_of_batch_records': 'details_of_batch_records',
        'quality_control_system': 'quality_control_system',
        'have_documentsprocedure': 'have_documentsprocedure',
        'inspection_reports': 'inspection_reports',
        'products_in_qa': 'products_in_qa',
        'if_yes_for_prior_notification': 'if_yes_for_prior_notification',
        'mlspl_qa_list': 'mlspl_qa_list'
    }
    
    for table_field, table_name in child_tables.items():
        if table_field in form_data:
            
            doc.set(table_field, [])
            
            
            table_data = form_data.get(table_field, [])
            if isinstance(table_data, list):
                for row_data in table_data:
                    if isinstance(row_data, dict):
                        doc.append(table_field, row_data)

def get_formatted_data(doc):
    """
    Return document data in a format suitable for frontend
    """
    doc_dict = doc.as_dict()
    

    system_fields = [
        'docstatus', 'idx', 'owner', 'creation', 'modified', 'modified_by',
        '__last_sync_on', 'doctype', 'for_company_2000', 'for_company_7000',
        'mail_sent_to_qa_team'
    ]
    
    for field in system_fields:
        doc_dict.pop(field, None)
    
    return doc_dict

def get_search_strategies_debug(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc):
  
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