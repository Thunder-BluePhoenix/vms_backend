import frappe
import json
from frappe.utils.file_manager import save_file, get_file
import requests
import os
from urllib.parse import urlparse


def populate_vendor_data_from_existing_onboarding(vendor_master_name, office_email_primary):
    """
    Function to populate vendor data from existing approved onboarding records
    
    Args:
        vendor_master_name: Name of the newly created vendor master
        office_email_primary: Primary email to search for existing vendor master
    """
    try:
        # Step 1: Check if any vendor master already exists with the same office_email_primary
        existing_vendor_master = frappe.db.get_value(
            "Vendor Master", 
            {"office_email_primary": office_email_primary}, 
            ["name", "onboarding_form_status"],
            as_dict=True
        )
        
        if not existing_vendor_master:
            return {"status": "info", "message": "No existing vendor master found with this email"}
        
        # Step 2: Find vendor onboarding records for the existing vendor master
        onboarding_filters = {
            "ref_no": existing_vendor_master.name,
        }
        
        # Get all onboarding records for this vendor
        onboarding_records = frappe.get_all(
            "Vendor Onboarding",
            filters=onboarding_filters,
            fields=["name", "onboarding_form_status", "creation"],
            order_by="creation desc"
        )
        
        if not onboarding_records:
            return {"status": "info", "message": "No onboarding records found for existing vendor"}
        
        # Step 3: Determine which onboarding record to use
        selected_onboarding = None
        
        # First try to find approved records, get the latest one
        approved_records = [r for r in onboarding_records if r.onboarding_form_status == "Approved"]
        if approved_records:
            selected_onboarding = approved_records[0]  # Latest approved record
        else:
            # If no approved record, get the latest record
            selected_onboarding = onboarding_records[0]
        
        if not selected_onboarding:
            return {"status": "info", "message": "No suitable onboarding record found"}
        
        # Step 4: Get the complete onboarding data
        source_onboarding = frappe.get_doc("Vendor Onboarding", selected_onboarding.name)
        
        # Step 5: Get the new vendor master document
        new_vendor_master = frappe.get_doc("Vendor Master", vendor_master_name)
        
        # Step 6: Get all related documents created during new registration
        new_onboarding = frappe.get_doc("Vendor Onboarding", new_vendor_master.onboarding_ref_no)
        
        # Step 7: Populate data for all related documents
        populated_docs = []
        
        # Populate Legal Documents
        if source_onboarding.document_details and new_onboarding.document_details:
            result = populate_legal_documents(
                source_onboarding.document_details, 
                new_onboarding.document_details,
                new_vendor_master.name
            )
            populated_docs.append(f"Legal Documents: {result}")
        
        # Populate Payment Details
        if source_onboarding.payment_detail and new_onboarding.payment_detail:
            result = populate_payment_details(
                source_onboarding.payment_detail, 
                new_onboarding.payment_detail,
                new_vendor_master.name
            )
            populated_docs.append(f"Payment Details: {result}")
        
        # Populate Manufacturing Details
        if source_onboarding.manufacturing_details and new_onboarding.manufacturing_details:
            result = populate_manufacturing_details(
                source_onboarding.manufacturing_details, 
                new_onboarding.manufacturing_details,
                new_vendor_master.name
            )
            populated_docs.append(f"Manufacturing Details: {result}")
        
        # Populate Certificate Details
        if source_onboarding.certificate_details and new_onboarding.certificate_details:
            result = populate_certificate_details(
                source_onboarding.certificate_details, 
                new_onboarding.certificate_details,
                new_vendor_master.name
            )
            populated_docs.append(f"Certificate Details: {result}")
        
        # Populate Company Details (if exists in vendor_company_details table)
        if source_onboarding.vendor_company_details:
            result = populate_company_details(
                source_onboarding.name,
                new_onboarding.name,
                new_vendor_master.name
            )
            populated_docs.append(f"Company Details: {result}")
        
        frappe.db.commit()
        
        return {
            "status": "success", 
            "message": f"Data populated from onboarding record: {selected_onboarding.name}",
            "source_onboarding": selected_onboarding.name,
            "populated_documents": populated_docs
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Data Population Error")
        return {
            "status": "error", 
            "message": f"Failed to populate vendor data: {str(e)}"
        }


def duplicate_attachment_file(source_file_url, target_doctype, target_docname):
    """
    Duplicate an attachment file for a new document
    
    Args:
        source_file_url: URL of the source file
        target_doctype: DocType of the target document
        target_docname: Name of the target document
    
    Returns:
        str: URL of the duplicated file or None if failed
    """
    try:
        if not source_file_url:
            return None
            
        # Get the source file document
        source_file_doc = frappe.get_doc("File", {"file_url": source_file_url})
        
        # Read the file content
        file_content = None
        if source_file_doc.is_private:
            # For private files, read from the private files directory
            file_path = frappe.get_site_path("private", "files", source_file_doc.file_name)
        else:
            # For public files, read from the public files directory
            file_path = frappe.get_site_path("public", "files", source_file_doc.file_name)
        
        # Check if file exists
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                file_content = file.read()
        else:
            # Try to download from URL if local file not found
            try:
                response = requests.get(f"{frappe.utils.get_site_url()}{source_file_url}")
                if response.status_code == 200:
                    file_content = response.content
            except:
                pass
        
        if not file_content:
            return None
        
        # Save the duplicated file
        new_file_doc = save_file(
            source_file_doc.file_name,
            file_content,
            target_doctype,
            target_docname,
            is_private=source_file_doc.is_private
        )
        
        return new_file_doc.file_url
        
    except Exception as e:
        frappe.log_error(f"File duplication failed for {source_file_url}: {str(e)}", "File Duplication Error")
        return None


def populate_legal_documents(source_doc_name, target_doc_name, new_vendor_master_name):
    """Populate Legal Documents data"""
    try:
        source_doc = frappe.get_doc("Legal Documents", source_doc_name)
        target_doc = frappe.get_doc("Legal Documents", target_doc_name)
        
        # Fields to copy (excluding attachment fields for now)
        fields_to_copy = [
            "company_pan_number", "name_on_company_pan", "enterprise_registration_number",
            "iec", "msme_registered", "msme_enterprise_type", "udyam_number", 
            "name_on_udyam_certificate", "trc_certificate_no"
        ]
        
        # Copy basic fields
        for field in fields_to_copy:
            if hasattr(source_doc, field):
                target_doc.set(field, source_doc.get(field))
        
        # Duplicate and copy attachment fields
        attachment_fields = [
            "pan_proof", "entity_proof", "iec_proof", "msme_proof", 
            "form_10f_proof", "trc_certificate", "pe_certificate"
        ]
        
        for field in attachment_fields:
            source_url = source_doc.get(field)
            if source_url:
                new_url = duplicate_attachment_file(source_url, target_doc.doctype, target_doc.name)
                if new_url:
                    target_doc.set(field, new_url)
        
        # Copy GST table with file duplication
        target_doc.set("gst_table", [])
        for row in source_doc.gst_table:
            new_row_data = {
                "gst_state": row.gst_state,
                "gst_number": row.gst_number,
                "gst_registration_date": row.gst_registration_date,
                "gst_ven_type": row.gst_ven_type,
                "pincode": row.pincode,
                "company": row.company
            }
            
            new_row = target_doc.append("gst_table", new_row_data)
            
            # Duplicate GST document attachment
            if row.gst_document:
                new_gst_doc_url = duplicate_attachment_file(row.gst_document, target_doc.doctype, target_doc.name)
                if new_gst_doc_url:
                    new_row.gst_document = new_gst_doc_url
        
        target_doc.save(ignore_permissions=True)
        return "Success"
        
    except Exception as e:
        frappe.log_error(f"Legal Documents population failed: {str(e)}", "Legal Documents Population Error")
        return f"Failed: {str(e)}"


def populate_payment_details(source_doc_name, target_doc_name, new_vendor_master_name):
    """Populate Payment Details data"""
    try:
        source_doc = frappe.get_doc("Vendor Onboarding Payment Details", source_doc_name)
        target_doc = frappe.get_doc("Vendor Onboarding Payment Details", target_doc_name)
        
        # Fields to copy
        fields_to_copy = [
            "bank_name", "ifsc_code", "account_number", "name_of_account_holder",
            "type_of_account", "currency", "rtgs", "neft", "ift"
        ]
        
        # Copy basic fields
        for field in fields_to_copy:
            if hasattr(source_doc, field):
                target_doc.set(field, source_doc.get(field))
        
        # Duplicate and copy attachment fields
        attachment_fields = [
            "bank_proof", "bank_proof_for_beneficiary_bank", "bank_proof_for_intermediate_bank"
        ]
        
        for field in attachment_fields:
            source_url = source_doc.get(field)
            if source_url:
                new_url = duplicate_attachment_file(source_url, target_doc.doctype, target_doc.name)
                if new_url:
                    target_doc.set(field, new_url)
        
        # Copy child tables
        if hasattr(source_doc, 'banker_details'):
            target_doc.set("banker_details", [])
            for row in source_doc.banker_details:
                target_doc.append("banker_details", {
                    "bank_name": row.bank_name,
                    "branch_name": row.branch_name,
                    "account_number": row.account_number,
                    "ifsc_code": row.ifsc_code,
                    "account_holder_name": row.account_holder_name,
                    "account_type": row.account_type
                })
        
        if hasattr(source_doc, 'international_bank_details'):
            target_doc.set("international_bank_details", [])
            for row in source_doc.international_bank_details:
                target_doc.append("international_bank_details", {
                    "bank_name": row.bank_name,
                    "bank_address": row.bank_address,
                    "swift_code": row.swift_code,
                    "country": row.country,
                    "currency": row.currency
                })
        
        if hasattr(source_doc, 'intermediate_bank_details') and source_doc.add_intermediate_bank_details:
            target_doc.set("intermediate_bank_details", [])
            for row in source_doc.intermediate_bank_details:
                target_doc.append("intermediate_bank_details", {
                    "bank_name": row.bank_name,
                    "bank_address": row.bank_address,
                    "swift_code": row.swift_code,
                    "country": row.country
                })
        
        target_doc.save(ignore_permissions=True)
        return "Success"
        
    except Exception as e:
        frappe.log_error(f"Payment Details population failed: {str(e)}", "Payment Details Population Error")
        return f"Failed: {str(e)}"


def populate_manufacturing_details(source_doc_name, target_doc_name, new_vendor_master_name):
    """Populate Manufacturing Details data"""
    try:
        source_doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", source_doc_name)
        target_doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", target_doc_name)
        
        # Fields to copy
        fields_to_copy = [
            "details_of_product_manufactured", "total_godown", "storage_capacity", "spare_capacity",
            "type_of_premises", "working_hours", "weekly_holidays", "number_of_manpower",
            "annual_revenue", "google_address_pin", "cold_storage"
        ]
        
        # Copy basic fields
        for field in fields_to_copy:
            if hasattr(source_doc, field):
                target_doc.set(field, source_doc.get(field))
        
        # Duplicate and copy attachment fields
        attachment_fields = ["brochure_proof", "organisation_structure_document"]
        
        for field in attachment_fields:
            source_url = source_doc.get(field)
            if source_url:
                new_url = duplicate_attachment_file(source_url, target_doc.doctype, target_doc.name)
                if new_url:
                    target_doc.set(field, new_url)
        
        # Copy materials supplied table
        if hasattr(source_doc, 'materials_supplied'):
            target_doc.set("materials_supplied", [])
            for row in source_doc.materials_supplied:
                new_row_data = {
                    "material_description": row.material_description,
                    "annual_capacity": row.annual_capacity,
                    "hsnsac_code": row.hsnsac_code
                }
                
                new_row = target_doc.append("materials_supplied", new_row_data)
                
                # Duplicate material images if available
                if hasattr(row, 'material_images') and row.material_images:
                    new_img_url = duplicate_attachment_file(row.material_images, target_doc.doctype, target_doc.name)
                    if new_img_url:
                        new_row.material_images = new_img_url
        
        target_doc.save(ignore_permissions=True)
        return "Success"
        
    except Exception as e:
        frappe.log_error(f"Manufacturing Details population failed: {str(e)}", "Manufacturing Details Population Error")
        return f"Failed: {str(e)}"


def populate_certificate_details(source_doc_name, target_doc_name, new_vendor_master_name):
    """Populate Certificate Details data"""
    try:
        source_doc = frappe.get_doc("Vendor Onboarding Certificates", source_doc_name)
        target_doc = frappe.get_doc("Vendor Onboarding Certificates", target_doc_name)
        
        # Copy certificates table
        if hasattr(source_doc, 'certificates'):
            target_doc.set("certificates", [])
            for row in source_doc.certificates:
                new_row_data = {
                    "certificate_code": row.certificate_code,
                    "certificate_name": row.certificate_name,
                    "other_certificate_name": row.other_certificate_name,
                    "valid_till": row.valid_till,
                    "other": row.other
                }
                
                new_row = target_doc.append("certificates", new_row_data)
                
                # Duplicate certificate attachment
                if hasattr(row, 'certificate_attach') and row.certificate_attach:
                    new_cert_url = duplicate_attachment_file(row.certificate_attach, target_doc.doctype, target_doc.name)
                    if new_cert_url:
                        new_row.certificate_attach = new_cert_url
        
        target_doc.save(ignore_permissions=True)
        return "Success"
        
    except Exception as e:
        frappe.log_error(f"Certificate Details population failed: {str(e)}", "Certificate Details Population Error")
        return f"Failed: {str(e)}"


def populate_company_details(source_onboarding_name, target_onboarding_name, new_vendor_master_name):
    """Populate Company Details from vendor_company_details table"""
    try:
        source_onboarding = frappe.get_doc("Vendor Onboarding", source_onboarding_name)
        target_onboarding = frappe.get_doc("Vendor Onboarding", target_onboarding_name)
        
        # Copy vendor company details table
        if hasattr(source_onboarding, 'vendor_company_details'):
            target_onboarding.set("vendor_company_details", [])
            for row in source_onboarding.vendor_company_details:
                # Find the corresponding Company Details document
                company_details_doc = frappe.db.get_value(
                    "Vendor Onboarding Company Details",
                    {"vendor_onboarding": source_onboarding_name, "company_name": row.company_name},
                    "name"
                )
                
                if company_details_doc:
                    # Create new company details for target onboarding
                    result = populate_vendor_onboarding_company_details(
                        company_details_doc,
                        target_onboarding_name,
                        new_vendor_master_name,
                        row.company_name
                    )
                    
                    if result == "Success":
                        # Add to vendor_company_details table
                        target_onboarding.append("vendor_company_details", {
                            "company_name": row.company_name,
                            "qms_required": row.qms_required
                        })
        
        target_onboarding.save(ignore_permissions=True)
        return "Success"
        
    except Exception as e:
        frappe.log_error(f"Company Details population failed: {str(e)}", "Company Details Population Error")
        return f"Failed: {str(e)}"


def populate_vendor_onboarding_company_details(source_doc_name, target_vendor_onboarding, target_ref_no, company_name):
    """Populate Vendor Onboarding Company Details"""
    try:
        source_doc = frappe.get_doc("Vendor Onboarding Company Details", source_doc_name)
        
        # Create new company details document
        target_doc = frappe.new_doc("Vendor Onboarding Company Details")
        target_doc.vendor_onboarding = target_vendor_onboarding
        target_doc.ref_no = target_ref_no
        target_doc.company_name = company_name
        
        # Fields to copy
        fields_to_copy = [
            "vendor_name", "office_email_primary", "telephone_number", "established_year",
            "nature_of_business", "corporate_identification_number", "address_line_1",
            "address_line_2", "city", "district", "state", "country", "pincode",
            "same_as_above", "manufacturing_address_line_1", "manufacturing_address_line_2",
            "manufacturing_city", "manufacturing_district", "manufacturing_state",
            "manufacturing_country", "manufacturing_pincode", "multiple_location"
        ]
        
        # Copy basic fields
        for field in fields_to_copy:
            if hasattr(source_doc, field):
                target_doc.set(field, source_doc.get(field))
        
        # Copy multiple location table
        if hasattr(source_doc, 'multiple_location_table'):
            for row in source_doc.multiple_location_table:
                target_doc.append("multiple_location_table", {
                    "ma_address_line_1": row.ma_address_line_1,
                    "ma_address_line_2": row.ma_address_line_2,
                    "ma_city": row.ma_city,
                    "ma_district": row.ma_district,
                    "ma_state": row.ma_state,
                    "ma_country": row.ma_country,
                    "ma_pincode": row.ma_pincode
                })
        
        target_doc.save(ignore_permissions=True)
        return "Success"
        
    except Exception as e:
        frappe.log_error(f"Vendor Onboarding Company Details population failed: {str(e)}", "Company Details Population Error")
        return f"Failed: {str(e)}"


# Function to be called after vendor registration
@frappe.whitelist()
def trigger_vendor_data_population(vendor_master_name, office_email_primary):
    """
    Wrapper function to be called from vendor registration API
    """
    return populate_vendor_data_from_existing_onboarding(vendor_master_name, office_email_primary)