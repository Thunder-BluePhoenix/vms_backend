import frappe
from frappe import _
from frappe.utils import nowdate, now
import json

@frappe.whitelist(methods=["POST"])
def save_qms_assessment_smart():
    """
    One-shot API that handles everything automatically:
    - Finds linked documents by display values
    - Matches existing records intelligently
    - Creates or updates as needed
    - Returns complete current data
    """
    try:
        # Get the request data
        data = frappe.local.form_dict
        
        # Extract identification fields - REQUIRED
        vendor_onboarding_input = data.get('vendor_onboarding')
        ref_no_input = data.get('ref_no')
        
        # Extract form data to save - OPTIONAL
        form_data = data.get('form_data', {})
        
        # Validate required identification fields
        if not vendor_onboarding_input or not ref_no_input:
            return {
                "status": "error",
                "message": "vendor_onboarding and ref_no are required"
            }
        
        # Clean the input values
        vendor_onboarding_input = str(vendor_onboarding_input).strip()
        ref_no_input = str(ref_no_input).strip()
        
        # Step 1: Find the actual linked document names
        vendor_onboarding_doc = find_vendor_onboarding_document(vendor_onboarding_input)
        ref_no_doc = find_ref_no_document(ref_no_input)
        
        # Step 2: Find existing QMS Assessment record using multiple strategies
        existing_doc = find_existing_qms_record(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc)
        
        if existing_doc:
            # UPDATE existing record using direct database update to avoid version conflicts
            if form_data:
                # Use frappe.db.set_value for direct updates (bypasses version check)
                for field_name, field_value in form_data.items():
                    # Only update regular fields, skip child tables for now
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
                
                # Update modified timestamp
                frappe.db.set_value("Supplier QMS Assessment Form", existing_doc, "modified", now())
                frappe.db.commit()
                action = "updated"
            else:
                action = "loaded"
            
            # Get the updated document for response
            doc = frappe.get_doc("Supplier QMS Assessment Form", existing_doc)
            
        else:
            # CREATE new record
            doc = frappe.new_doc("Supplier QMS Assessment Form")
            
            # Use the resolved document names if found, otherwise use input values
            doc.vendor_onboarding = vendor_onboarding_doc or vendor_onboarding_input
            doc.ref_no = ref_no_doc or ref_no_input
            doc.date1 = nowdate()
            
            # Set default values
            set_default_values(doc)
            
            # Update fields if form_data is provided
            if form_data:
                update_document_fields(doc, form_data)
            
            # Insert new document
            doc.insert()
            frappe.db.commit()  # Commit the transaction
            action = "created"
        
        # Return success with current document data
        return {
            "status": "success",
            "message": f"Record {action} successfully",
            "action": action,
            "doc_name": doc.name,
            "current_data": get_formatted_data(doc),
            "debug_info": {
                "input_vendor_onboarding": vendor_onboarding_input,
                "input_ref_no": ref_no_input,
                "resolved_vendor_onboarding": vendor_onboarding_doc,
                "resolved_ref_no": ref_no_doc,
                "existing_record_found": existing_doc
            }
        }
        
    except Exception as e:
        # Use shorter error message to avoid title length issues
        error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        frappe.log_error(f"QMS API Error: {error_msg}")
        return {
            "status": "error",
            "message": str(e)
        }

def find_vendor_onboarding_document(input_value):
    """
    Find the actual Vendor Onboarding document name from various possible inputs
    """
    try:
        # Strategy 1: Direct match (if input is already the document name)
        if frappe.db.exists("Vendor Onboarding", input_value):
            return input_value
        
        # Strategy 2: Search by common fields in Vendor Onboarding
        possible_fields = ['vendor_onboarding_id', 'reference_no', 'onboarding_id', 'vendor_id']
        
        for field in possible_fields:
            try:
                # Check if field exists in doctype first
                if frappe.db.has_column("Vendor Onboarding", field):
                    doc_name = frappe.db.get_value("Vendor Onboarding", {field: input_value}, "name")
                    if doc_name:
                        return doc_name
            except:
                continue
        
        # Strategy 3: Search by partial match in name or title
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
        
        # Strategy 4: Return None if not found (will use input value as is)
        return None
        
    except Exception as e:
        # Use shorter error message
        error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        frappe.log_error(f"Vendor onboarding search error: {error_msg}")
        return None

def find_ref_no_document(input_value):
    """
    Find the actual document name for ref_no from various possible doctypes
    """
    try:
        # Possible doctypes that ref_no might link to
        possible_doctypes = ['Vendor Master', 'Supplier', 'Vendor', 'Customer']
        
        for doctype in possible_doctypes:
            try:
                # Check if doctype exists
                if not frappe.db.exists("DocType", doctype):
                    continue
                    
                # Strategy 1: Direct match
                if frappe.db.exists(doctype, input_value):
                    return input_value
                
                # Strategy 2: Search by common fields
                possible_fields = ['vendor_id', 'supplier_id', 'reference_no', 'vendor_code', 'supplier_code']
                
                for field in possible_fields:
                    try:
                        # Check if field exists in doctype first
                        if frappe.db.has_column(doctype, field):
                            doc_name = frappe.db.get_value(doctype, {field: input_value}, "name")
                            if doc_name:
                                return doc_name
                    except:
                        continue
                
                # Strategy 3: Search by partial match
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
        
        # Return None if not found (will use input value as is)
        return None
        
    except Exception as e:
        # Use shorter error message
        error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        frappe.log_error(f"Ref no search error: {error_msg}")
        return None

def find_existing_qms_record(vendor_onboarding_input, ref_no_input, vendor_onboarding_doc, ref_no_doc):
    """
    Find existing QMS Assessment record using multiple strategies
    """
    try:
        # Strategy 1: Direct match with resolved document names
        if vendor_onboarding_doc and ref_no_doc:
            existing = frappe.db.get_value("Supplier QMS Assessment Form", {
                "vendor_onboarding": vendor_onboarding_doc,
                "ref_no": ref_no_doc
            }, "name")
            if existing:
                return existing
        
        # Strategy 2: Direct match with input values
        existing = frappe.db.get_value("Supplier QMS Assessment Form", {
            "vendor_onboarding": vendor_onboarding_input,
            "ref_no": ref_no_input
        }, "name")
        if existing:
            return existing
        
        # Strategy 3: Match with any combination
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
        
        # Strategy 4: SQL search with LIKE for partial matches
        try:
            sql_result = frappe.db.sql("""
                SELECT name FROM `tabSupplier QMS Assessment Form` 
                WHERE vendor_onboarding LIKE %s OR ref_no LIKE %s
                LIMIT 1
            """, (f"%{vendor_onboarding_input}%", f"%{ref_no_input}%"))
            
            if sql_result:
                return sql_result[0][0]
        except:
            pass
        
        # No existing record found
        return None
        
    except Exception as e:
        # Use shorter error message
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
    """
    Update document fields from form_data
    All fields are optional - handles empty/null values gracefully
    """
    
    # Regular fields - all optional, no validation required
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
    
    # Update fields only if they exist in form_data (allows empty/null values)
    for field_name in regular_fields:
        if field_name in form_data:
            # Set field value even if it's empty string, null, or 0
            field_value = form_data[field_name]
            setattr(doc, field_name, field_value)
    
    # Handle child tables - also optional
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
            # Clear existing entries only if new data is provided
            doc.set(table_field, [])
            
            # Add new entries (can be empty array)
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
    
    # Remove system fields that frontend doesn't need
    system_fields = [
        'docstatus', 'idx', 'owner', 'creation', 'modified', 'modified_by',
        '__last_sync_on', 'doctype', 'for_company_2000', 'for_company_7000',
        'mail_sent_to_qa_team'
    ]
    
    for field in system_fields:
        doc_dict.pop(field, None)
    
    return doc_dict