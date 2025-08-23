import frappe
import json
from frappe.utils.file_manager import save_file
import os
import shutil
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

class VendorDataPopulator:
    def __init__(self):
        """Initialize with Frappe database context"""
        self.db = frappe.db
    
    def populate_vendor_data_from_existing_onboarding(self, vendor_master_name, office_email_primary, 
                                                    new_onboarding_record_given=None, source_onb_doc=None):
        """
        Main function to populate vendor data from existing approved onboarding records
        Uses direct SQL queries for better performance
        """
        try:
            # Step 1: Check if any vendor master already exists with the same office_email_primary
            existing_vendor_master = self.db.sql("""
                SELECT name, onboarding_form_status 
                FROM `tabVendor Master` 
                WHERE office_email_primary = %s
            """, (office_email_primary,), as_dict=True)
            
            if not existing_vendor_master:
                return {"status": "info", "message": "No existing vendor master found with this email"}
            
            existing_vendor = existing_vendor_master[0]
            
            # Step 2: Find vendor onboarding records for the existing vendor master
            onboarding_records = self.db.sql("""
                SELECT name, onboarding_form_status, creation 
                FROM `tabVendor Onboarding` 
                WHERE ref_no = %s 
                ORDER BY creation DESC
            """, (existing_vendor['name'],), as_dict=True)
            
            if not onboarding_records:
                return {"status": "info", "message": "No onboarding records found for existing vendor"}
            
            # Step 3: Determine which onboarding record to use
            selected_onboarding = None
            
            if source_onb_doc is None:
                # First try to find approved records, get the latest one
                approved_records = [r for r in onboarding_records if r['onboarding_form_status'] == "Approved"]
                if approved_records:
                    selected_onboarding = approved_records[0]
                else:
                    selected_onboarding = onboarding_records[0]
            else:
                selected_onboarding = {'name': source_onb_doc if isinstance(source_onb_doc, str) else source_onb_doc.name}
            
            if not selected_onboarding:
                return {"status": "info", "message": "No suitable onboarding record found"}
            
            # Step 4: Get the new vendor master document
            new_vendor_data = self.db.sql("""
                SELECT name, onboarding_ref_no 
                FROM `tabVendor Master` 
                WHERE name = %s
            """, (vendor_master_name,), as_dict=True)
            
            if not new_vendor_data:
                return {"status": "error", "message": "New vendor master not found"}
            
            new_vendor_master = new_vendor_data[0]
            
            # Step 5: Get onboarding record names
            source_onboarding_name = selected_onboarding['name']
            new_onboarding_name = new_onboarding_record_given if new_onboarding_record_given else new_vendor_master['onboarding_ref_no']
            
            # Step 6: Get source and target onboarding details
            source_onboarding_data = self.db.sql("""
                SELECT document_details, payment_detail, manufacturing_details, certificate_details 
                FROM `tabVendor Onboarding` 
                WHERE name = %s
            """, (source_onboarding_name,), as_dict=True)
            
            if not source_onboarding_data:
                return {"status": "error", "message": "Source onboarding data not found"}
            
            source_onboarding = source_onboarding_data[0]
            
            new_onboarding_data = self.db.sql("""
                SELECT document_details, payment_detail, manufacturing_details, certificate_details 
                FROM `tabVendor Onboarding` 
                WHERE name = %s
            """, (new_onboarding_name,), as_dict=True)
            
            if not new_onboarding_data:
                return {"status": "error", "message": "New onboarding data not found"}
            
            new_onboarding = new_onboarding_data[0]
            
            # Step 7: Populate data for all related documents
            populated_docs = []
            
            # Populate Legal Documents
            if source_onboarding['document_details'] and new_onboarding['document_details']:
                result = self.populate_legal_documents(
                    source_onboarding['document_details'], 
                    new_onboarding['document_details'],
                    vendor_master_name
                )
                populated_docs.append(f"Legal Documents: {result}")
            
            # Populate Payment Details
            if source_onboarding['payment_detail'] and new_onboarding['payment_detail']:
                result = self.populate_payment_details(
                    source_onboarding['payment_detail'], 
                    new_onboarding['payment_detail'],
                    vendor_master_name
                )
                populated_docs.append(f"Payment Details: {result}")
            
            # Populate Manufacturing Details
            if source_onboarding['manufacturing_details'] and new_onboarding['manufacturing_details']:
                result = self.populate_manufacturing_details(
                    source_onboarding['manufacturing_details'], 
                    new_onboarding['manufacturing_details'],
                    vendor_master_name
                )
                populated_docs.append(f"Manufacturing Details: {result}")
            
            # Populate Certificate Details
            if source_onboarding['certificate_details'] and new_onboarding['certificate_details']:
                result = self.populate_certificate_details(
                    source_onboarding['certificate_details'], 
                    new_onboarding['certificate_details'],
                    vendor_master_name
                )
                populated_docs.append(f"Certificate Details: {result}")
            
            # Populate Company Details
            result = self.populate_company_details(
                source_onboarding_name,
                new_onboarding_name,
                vendor_master_name
            )
            populated_docs.append(f"Company Details: {result}")
            
            # Commit all changes
            frappe.db.commit()
            
            return {
                "status": "success", 
                "message": f"Data populated from onboarding record: {source_onboarding_name}",
                "source_onboarding": source_onboarding_name,
                "populated_documents": populated_docs
            }
            
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Vendor data population error: {frappe.get_traceback()}", "Vendor Data Population Error")
            return {
                "status": "error", 
                "message": f"Failed to populate vendor data: {str(e)}"
            }
    
    def duplicate_attachment_file(self, source_file_url, target_doctype, target_docname):
        """
        Duplicate an attachment file for a new document using Frappe's file system
        """
        try:
            if not source_file_url:
                return None
                
            # Get the source file document
            source_file_data = self.db.sql("""
                SELECT name, file_name, is_private, file_url 
                FROM `tabFile` 
                WHERE file_url = %s
            """, (source_file_url,), as_dict=True)
            
            if not source_file_data:
                return None
                
            source_file_doc = source_file_data[0]
            
            # Get file path using Frappe's methods
            if source_file_doc['is_private']:
                source_file_path = frappe.get_site_path("private", "files", source_file_doc['file_name'])
            else:
                source_file_path = frappe.get_site_path("public", "files", source_file_doc['file_name'])
            
            if not os.path.exists(source_file_path):
                logger.warning(f"Source file not found: {source_file_path}")
                return None
            
            # Read file content
            with open(source_file_path, 'rb') as file:
                file_content = file.read()
            
            # Save the duplicated file using Frappe's save_file function
            new_file_doc = save_file(
                source_file_doc['file_name'],
                file_content,
                target_doctype,
                target_docname,
                is_private=source_file_doc['is_private']
            )
            
            return new_file_doc.file_url
            
        except Exception as e:
            logger.error(f"File duplication failed for {source_file_url}: {str(e)}")
            return None
    
    def populate_legal_documents(self, source_doc_name, target_doc_name, new_vendor_master_name):
        """Populate Legal Documents data using direct SQL"""
        try:
            # Get source document data
            source_data = self.db.sql("""
                SELECT company_pan_number, name_on_company_pan, enterprise_registration_number,
                       iec, msme_registered, msme_enterprise_type, udyam_number, 
                       name_on_udyam_certificate, trc_certificate_no, pan_proof, entity_proof, 
                       iec_proof, msme_proof, form_10f_proof, trc_certificate, pe_certificate
                FROM `tabLegal Documents` 
                WHERE name = %s
            """, (source_doc_name,), as_dict=True)
            
            if not source_data:
                return "Source document not found"
            
            source_doc = source_data[0]
            
            # Update target document with basic fields
            self.db.sql("""
                UPDATE `tabLegal Documents` 
                SET company_pan_number = %s, name_on_company_pan = %s, 
                    enterprise_registration_number = %s, iec = %s, msme_registered = %s,
                    msme_enterprise_type = %s, udyam_number = %s, 
                    name_on_udyam_certificate = %s, trc_certificate_no = %s,
                    modified = %s, modified_by = %s
                WHERE name = %s
            """, (
                source_doc['company_pan_number'], source_doc['name_on_company_pan'],
                source_doc['enterprise_registration_number'], source_doc['iec'], 
                source_doc['msme_registered'], source_doc['msme_enterprise_type'],
                source_doc['udyam_number'], source_doc['name_on_udyam_certificate'],
                source_doc['trc_certificate_no'], frappe.utils.now(), frappe.session.user,
                target_doc_name
            ))
            
            # Handle attachment fields
            attachment_fields = [
                'pan_proof', 'entity_proof', 'iec_proof', 'msme_proof', 
                'form_10f_proof', 'trc_certificate', 'pe_certificate'
            ]
            
            for field in attachment_fields:
                source_url = source_doc.get(field)
                if source_url:
                    new_url = self.duplicate_attachment_file(source_url, "Legal Documents", target_doc_name)
                    if new_url:
                        self.db.sql(f"""
                            UPDATE `tabLegal Documents` 
                            SET {field} = %s, modified = %s 
                            WHERE name = %s
                        """, (new_url, frappe.utils.now(), target_doc_name))
            
            # Copy GST table
            self.copy_gst_table(source_doc_name, target_doc_name)
            
            return "Success"
            
        except Exception as e:
            logger.error(f"Legal Documents population failed: {str(e)}")
            return f"Failed: {str(e)}"
    
    def copy_gst_table(self, source_doc_name, target_doc_name):
        """Copy GST table data using direct SQL"""
        try:
            # Get source GST data
            gst_data = self.db.sql("""
                SELECT gst_state, gst_number, gst_registration_date, gst_ven_type, 
                       pincode, company, gst_document
                FROM `tabGST Table` 
                WHERE parent = %s
            """, (source_doc_name,), as_dict=True)
            
            # Delete existing GST records for target
            self.db.sql("DELETE FROM `tabGST Table` WHERE parent = %s", (target_doc_name,))
            
            # Insert new GST records
            for idx, row in enumerate(gst_data, 1):
                new_row_id = frappe.generate_hash("", 10)  # Generate unique ID
                
                # Duplicate GST document if exists
                gst_doc_url = row['gst_document']
                if gst_doc_url:
                    gst_doc_url = self.duplicate_attachment_file(gst_doc_url, "Legal Documents", target_doc_name)
                
                self.db.sql("""
                    INSERT INTO `tabGST Table` (name, parent, parenttype, parentfield,
                                              gst_state, gst_number, gst_registration_date, 
                                              gst_ven_type, pincode, company, gst_document,
                                              creation, modified, owner, modified_by, idx)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_row_id, target_doc_name, 'Legal Documents', 'gst_table',
                    row['gst_state'], row['gst_number'], row['gst_registration_date'],
                    row['gst_ven_type'], row['pincode'], row['company'], gst_doc_url,
                    frappe.utils.now(), frappe.utils.now(), frappe.session.user, frappe.session.user, idx
                ))
                
        except Exception as e:
            logger.error(f"GST table copy failed: {str(e)}")
            raise
    
    def populate_payment_details(self, source_doc_name, target_doc_name, new_vendor_master_name):
        """Populate Payment Details data"""
        try:
            # Get source document data
            source_data = self.db.sql("""
                SELECT bank_name, ifsc_code, account_number, name_of_account_holder,
                       type_of_account, currency, rtgs, neft, ift, bank_proof,
                       bank_proof_for_beneficiary_bank, bank_proof_for_intermediate_bank
                FROM `tabVendor Onboarding Payment Details` 
                WHERE name = %s
            """, (source_doc_name,), as_dict=True)
            
            if not source_data:
                return "Source document not found"
            
            source_doc = source_data[0]
            
            # Update target document
            self.db.sql("""
                UPDATE `tabVendor Onboarding Payment Details` 
                SET bank_name = %s, ifsc_code = %s, account_number = %s, 
                    name_of_account_holder = %s, type_of_account = %s, currency = %s,
                    rtgs = %s, neft = %s, ift = %s, modified = %s, modified_by = %s
                WHERE name = %s
            """, (
                source_doc['bank_name'], source_doc['ifsc_code'], source_doc['account_number'],
                source_doc['name_of_account_holder'], source_doc['type_of_account'], 
                source_doc['currency'], source_doc['rtgs'], source_doc['neft'], 
                source_doc['ift'], frappe.utils.now(), frappe.session.user, target_doc_name
            ))
            
            # Handle attachment fields
            attachment_fields = ['bank_proof', 'bank_proof_for_beneficiary_bank', 'bank_proof_for_intermediate_bank']
            for field in attachment_fields:
                source_url = source_doc.get(field)
                if source_url:
                    new_url = self.duplicate_attachment_file(source_url, "Vendor Onboarding Payment Details", target_doc_name)
                    if new_url:
                        self.db.sql(f"""
                            UPDATE `tabVendor Onboarding Payment Details` 
                            SET {field} = %s, modified = %s 
                            WHERE name = %s
                        """, (new_url, frappe.utils.now(), target_doc_name))
            
            # Copy child tables
            self.copy_child_table("Banker Details", source_doc_name, target_doc_name, "banker_details")
            self.copy_child_table("International Bank Details", source_doc_name, target_doc_name, "international_bank_details")
            self.copy_child_table("Intermediate Bank Details", source_doc_name, target_doc_name, "intermediate_bank_details")
            
            return "Success"
            
        except Exception as e:
            logger.error(f"Payment Details population failed: {str(e)}")
            return f"Failed: {str(e)}"
    
    def copy_child_table(self, table_name, source_parent, target_parent, parentfield):
        """Generic function to copy child table data"""
        try:
            # Get source data
            data = self.db.sql(f"SELECT * FROM `tab{table_name}` WHERE parent = %s", (source_parent,), as_dict=True)
            
            # Delete existing records
            self.db.sql(f"DELETE FROM `tab{table_name}` WHERE parent = %s", (target_parent,))
            
            # Insert new records
            for idx, row in enumerate(data, 1):
                # Remove system fields
                row.pop('name', None)
                row.pop('creation', None)
                row.pop('modified', None)
                row.pop('owner', None)
                row.pop('modified_by', None)
                row.pop('parent', None)
                row.pop('idx', None)
                
                # Set new values
                row['name'] = frappe.generate_hash("", 10)
                row['parent'] = target_parent
                row['parentfield'] = parentfield
                row['creation'] = frappe.utils.now()
                row['modified'] = frappe.utils.now()
                row['owner'] = frappe.session.user
                row['modified_by'] = frappe.session.user
                row['idx'] = idx
                
                # Insert record
                columns = list(row.keys())
                values = [row[col] for col in columns]
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join([f'`{col}`' for col in columns])
                
                self.db.sql(f"""
                    INSERT INTO `tab{table_name}` ({columns_str}) 
                    VALUES ({placeholders})
                """, values)
                
        except Exception as e:
            logger.error(f"{table_name} copy failed: {str(e)}")
            raise
    
    def populate_manufacturing_details(self, source_doc_name, target_doc_name, new_vendor_master_name):
        """Populate Manufacturing Details data"""
        try:
            # Get source document data
            source_data = self.db.sql("""
                SELECT details_of_product_manufactured, total_godown, storage_capacity, 
                       spare_capacity, type_of_premises, working_hours, weekly_holidays, 
                       number_of_manpower, annual_revenue, google_address_pin, cold_storage,
                       brochure_proof, organisation_structure_document
                FROM `tabVendor Onboarding Manufacturing Details` 
                WHERE name = %s
            """, (source_doc_name,), as_dict=True)
            
            if not source_data:
                return "Source document not found"
            
            source_doc = source_data[0]
            
            # Update target document
            self.db.sql("""
                UPDATE `tabVendor Onboarding Manufacturing Details` 
                SET details_of_product_manufactured = %s, total_godown = %s, 
                    storage_capacity = %s, spare_capacity = %s, type_of_premises = %s,
                    working_hours = %s, weekly_holidays = %s, number_of_manpower = %s,
                    annual_revenue = %s, google_address_pin = %s, cold_storage = %s,
                    modified = %s, modified_by = %s
                WHERE name = %s
            """, (
                source_doc['details_of_product_manufactured'], source_doc['total_godown'],
                source_doc['storage_capacity'], source_doc['spare_capacity'], 
                source_doc['type_of_premises'], source_doc['working_hours'],
                source_doc['weekly_holidays'], source_doc['number_of_manpower'],
                source_doc['annual_revenue'], source_doc['google_address_pin'],
                source_doc['cold_storage'], frappe.utils.now(), frappe.session.user, target_doc_name
            ))
            
            # Handle attachment fields
            attachment_fields = ['brochure_proof', 'organisation_structure_document']
            for field in attachment_fields:
                source_url = source_doc.get(field)
                if source_url:
                    new_url = self.duplicate_attachment_file(source_url, "Vendor Onboarding Manufacturing Details", target_doc_name)
                    if new_url:
                        self.db.sql(f"""
                            UPDATE `tabVendor Onboarding Manufacturing Details` 
                            SET {field} = %s, modified = %s 
                            WHERE name = %s
                        """, (new_url, frappe.utils.now(), target_doc_name))
            
            # Copy materials supplied table
            self.copy_materials_supplied_table(source_doc_name, target_doc_name)
            
            return "Success"
            
        except Exception as e:
            logger.error(f"Manufacturing Details population failed: {str(e)}")
            return f"Failed: {str(e)}"
    
    def copy_materials_supplied_table(self, source_doc_name, target_doc_name):
        """Copy materials supplied table with image handling"""
        try:
            # Get source data
            data = self.db.sql("""
                SELECT material_description, annual_capacity, hsnsac_code, material_images
                FROM `tabMaterials Supplied` 
                WHERE parent = %s
            """, (source_doc_name,), as_dict=True)
            
            # Delete existing records
            self.db.sql("DELETE FROM `tabMaterials Supplied` WHERE parent = %s", (target_doc_name,))
            
            # Insert new records
            for idx, row in enumerate(data, 1):
                new_row_id = frappe.generate_hash("", 10)
                
                # Duplicate material images if exists
                material_images_url = row['material_images']
                if material_images_url:
                    material_images_url = self.duplicate_attachment_file(
                        material_images_url, 
                        "Vendor Onboarding Manufacturing Details", 
                        target_doc_name
                    )
                
                self.db.sql("""
                    INSERT INTO `tabMaterials Supplied` (name, parent, parenttype, parentfield,
                                                       material_description, annual_capacity, 
                                                       hsnsac_code, material_images,
                                                       creation, modified, owner, modified_by, idx)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_row_id, target_doc_name, 'Vendor Onboarding Manufacturing Details', 'materials_supplied',
                    row['material_description'], row['annual_capacity'], 
                    row['hsnsac_code'], material_images_url,
                    frappe.utils.now(), frappe.utils.now(), frappe.session.user, frappe.session.user, idx
                ))
                
        except Exception as e:
            logger.error(f"Materials supplied copy failed: {str(e)}")
            raise
    
    def populate_certificate_details(self, source_doc_name, target_doc_name, new_vendor_master_name):
        """Populate Certificate Details data"""
        try:
            # Copy certificates table
            self.copy_certificates_table(source_doc_name, target_doc_name)
            return "Success"
            
        except Exception as e:
            logger.error(f"Certificate Details population failed: {str(e)}")
            return f"Failed: {str(e)}"
    
    def copy_certificates_table(self, source_doc_name, target_doc_name):
        """Copy certificates table with attachment handling"""
        try:
            # Get source data
            data = self.db.sql("""
                SELECT certificate_code, certificate_name, other_certificate_name, 
                       valid_till, other, certificate_attach
                FROM `tabCertificates` 
                WHERE parent = %s
            """, (source_doc_name,), as_dict=True)
            
            # Delete existing records
            self.db.sql("DELETE FROM `tabCertificates` WHERE parent = %s", (target_doc_name,))
            
            # Insert new records
            for idx, row in enumerate(data, 1):
                new_row_id = frappe.generate_hash("", 10)
                
                # Duplicate certificate attachment if exists
                cert_attach_url = row['certificate_attach']
                if cert_attach_url:
                    cert_attach_url = self.duplicate_attachment_file(
                        cert_attach_url, 
                        "Vendor Onboarding Certificates", 
                        target_doc_name
                    )
                
                self.db.sql("""
                    INSERT INTO `tabCertificates` (name, parent, parenttype, parentfield,
                                                 certificate_code, certificate_name, 
                                                 other_certificate_name, valid_till, 
                                                 other, certificate_attach,
                                                 creation, modified, owner, modified_by, idx)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_row_id, target_doc_name, 'Vendor Onboarding Certificates', 'certificates',
                    row['certificate_code'], row['certificate_name'], 
                    row['other_certificate_name'], row['valid_till'],
                    row['other'], cert_attach_url,
                    frappe.utils.now(), frappe.utils.now(), frappe.session.user, frappe.session.user, idx
                ))
                
        except Exception as e:
            logger.error(f"Certificates copy failed: {str(e)}")
            raise
    
    def populate_company_details(self, source_onboarding_name, target_onboarding_name, new_vendor_master_name):
        """Populate Company Details from vendor_company_details table"""
        try:
            # Find company details document for source onboarding
            company_details_data = self.db.sql("""
                SELECT name 
                FROM `tabVendor Onboarding Company Details` 
                WHERE vendor_onboarding = %s
            """, (source_onboarding_name,), as_dict=True)
            
            if company_details_data:
                self.populate_vendor_onboarding_company_details(
                    company_details_data[0]['name'],
                    target_onboarding_name,
                    new_vendor_master_name
                )
            
            return "Success"
            
        except Exception as e:
            logger.error(f"Company Details population failed: {str(e)}")
            return f"Failed: {str(e)}"
    
    def populate_vendor_onboarding_company_details(self, source_doc_name, target_vendor_onboarding, target_ref_no):
        """Populate Vendor Onboarding Company Details"""
        try:
            # Get source document data
            source_data = self.db.sql("""
                SELECT vendor_name, office_email_primary, telephone_number, established_year,
                       nature_of_business, corporate_identification_number, address_line_1,
                       address_line_2, city, district, state, country, pincode,
                       same_as_above, manufacturing_address_line_1, manufacturing_address_line_2,
                       manufacturing_city, manufacturing_district, manufacturing_state,
                       manufacturing_country, manufacturing_pincode, multiple_location
                FROM `tabVendor Onboarding Company Details` 
                WHERE name = %s
            """, (source_doc_name,), as_dict=True)
            
            if not source_data:
                return "Source document not found"
            
            source_doc = source_data[0]
            
            # Check if target company details document already exists
            existing_target = self.db.sql("""
                SELECT name 
                FROM `tabVendor Onboarding Company Details` 
                WHERE vendor_onboarding = %s
            """, (target_vendor_onboarding,), as_dict=True)
            
            if existing_target:
                # Update existing document
                self.db.sql("""
                    UPDATE `tabVendor Onboarding Company Details` 
                    SET vendor_name = %s, office_email_primary = %s, telephone_number = %s,
                        established_year = %s, nature_of_business = %s, 
                        corporate_identification_number = %s, address_line_1 = %s,
                        address_line_2 = %s, city = %s, district = %s, state = %s,
                        country = %s, pincode = %s, same_as_above = %s,
                        manufacturing_address_line_1 = %s, manufacturing_address_line_2 = %s,
                        manufacturing_city = %s, manufacturing_district = %s,
                        manufacturing_state = %s, manufacturing_country = %s,
                        manufacturing_pincode = %s, multiple_location = %s,
                        modified = %s, modified_by = %s
                    WHERE vendor_onboarding = %s
                """, (
                    source_doc['vendor_name'], source_doc['office_email_primary'],
                    source_doc['telephone_number'], source_doc['established_year'],
                    source_doc['nature_of_business'], source_doc['corporate_identification_number'],
                    source_doc['address_line_1'], source_doc['address_line_2'],
                    source_doc['city'], source_doc['district'], source_doc['state'],
                    source_doc['country'], source_doc['pincode'], source_doc['same_as_above'],
                    source_doc['manufacturing_address_line_1'], source_doc['manufacturing_address_line_2'],
                    source_doc['manufacturing_city'], source_doc['manufacturing_district'],
                    source_doc['manufacturing_state'], source_doc['manufacturing_country'],
                    source_doc['manufacturing_pincode'], source_doc['multiple_location'],
                    frappe.utils.now(), frappe.session.user, target_vendor_onboarding
                ))
                
                target_doc_name = existing_target[0]['name']
            else:
                # Create new document
                new_doc_id = frappe.generate_hash("", 10)
                
                self.db.sql("""
                    INSERT INTO `tabVendor Onboarding Company Details` 
                    (name, vendor_onboarding, ref_no, vendor_name, office_email_primary,
                     telephone_number, established_year, nature_of_business, 
                     corporate_identification_number, address_line_1, address_line_2,
                     city, district, state, country, pincode, same_as_above,
                     manufacturing_address_line_1, manufacturing_address_line_2,
                     manufacturing_city, manufacturing_district, manufacturing_state,
                     manufacturing_country, manufacturing_pincode, multiple_location,
                     creation, modified, owner, modified_by, docstatus)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_doc_id, target_vendor_onboarding, target_ref_no,
                    source_doc['vendor_name'], source_doc['office_email_primary'],
                    source_doc['telephone_number'], source_doc['established_year'],
                    source_doc['nature_of_business'], source_doc['corporate_identification_number'],
                    source_doc['address_line_1'], source_doc['address_line_2'],
                    source_doc['city'], source_doc['district'], source_doc['state'],
                    source_doc['country'], source_doc['pincode'], source_doc['same_as_above'],
                    source_doc['manufacturing_address_line_1'], source_doc['manufacturing_address_line_2'],
                    source_doc['manufacturing_city'], source_doc['manufacturing_district'],
                    source_doc['manufacturing_state'], source_doc['manufacturing_country'],
                    source_doc['manufacturing_pincode'], source_doc['multiple_location'],
                    frappe.utils.now(), frappe.utils.now(), frappe.session.user, frappe.session.user, 0
                ))
                
                target_doc_name = new_doc_id
            
            # Copy multiple location table
            self.copy_multiple_location_table(source_doc_name, target_doc_name)
            
            return "Success"
            
        except Exception as e:
            logger.error(f"Vendor Onboarding Company Details population failed: {str(e)}")
            return f"Failed: {str(e)}"
    
    def copy_multiple_location_table(self, source_doc_name, target_doc_name):
        """Copy multiple location table"""
        try:
            # Get source data
            data = self.db.sql("""
                SELECT ma_address_line_1, ma_address_line_2, ma_city, ma_district, 
                       ma_state, ma_country, ma_pincode
                FROM `tabMultiple Location Table` 
                WHERE parent = %s
            """, (source_doc_name,), as_dict=True)
            
            # Delete existing records
            self.db.sql("DELETE FROM `tabMultiple Location Table` WHERE parent = %s", (target_doc_name,))
            
            # Insert new records
            for idx, row in enumerate(data, 1):
                new_row_id = frappe.generate_hash("", 10)
                
                self.db.sql("""
                    INSERT INTO `tabMultiple Location Table` (name, parent, parenttype, parentfield,
                                                            ma_address_line_1, ma_address_line_2, 
                                                            ma_city, ma_district, ma_state, 
                                                            ma_country, ma_pincode,
                                                            creation, modified, owner, modified_by, idx)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_row_id, target_doc_name, 'Vendor Onboarding Company Details', 'multiple_location_table',
                    row['ma_address_line_1'], row['ma_address_line_2'],
                    row['ma_city'], row['ma_district'], row['ma_state'],
                    row['ma_country'], row['ma_pincode'],
                    frappe.utils.now(), frappe.utils.now(), frappe.session.user, frappe.session.user, idx
                ))
                
        except Exception as e:
            logger.error(f"Multiple location table copy failed: {str(e)}")
            raise


# Wrapper function for backward compatibility
def populate_vendor_data_from_existing_onboarding(vendor_master_name, office_email_primary, 
                                                new_onboarding_record_given=None, source_onb_doc=None):
    """
    Backward compatible wrapper function
    """
    populator = VendorDataPopulator()
    return populator.populate_vendor_data_from_existing_onboarding(
        vendor_master_name, office_email_primary, new_onboarding_record_given, source_onb_doc
    )


# Additional utility functions for your specific use case
@frappe.whitelist()
def bulk_populate_multi_company_records(unique_multi_comp_id):
    """
    Bulk populate records for multi-company scenario
    """
    try:
        # Get head record
        head_record = frappe.db.sql("""
            SELECT name, ref_no, office_email_primary, form_fully_submitted_by_vendor 
            FROM `tabVendor Onboarding` 
            WHERE unique_multi_comp_id = %s AND head_target = 1
        """, (unique_multi_comp_id,), as_dict=True)
        
        if not head_record or not head_record[0]['form_fully_submitted_by_vendor']:
            return {"status": "error", "message": "Head record not found or not fully submitted"}
        
        head = head_record[0]
        
        # Get all child records
        child_records = frappe.db.sql("""
            SELECT name 
            FROM `tabVendor Onboarding` 
            WHERE unique_multi_comp_id = %s AND head_target = 0
        """, (unique_multi_comp_id,), as_dict=True)
        
        if not child_records:
            return {"status": "info", "message": "No child records found"}
        
        # Get vendor master
        vendor_master = frappe.get_doc("Vendor Master", head['ref_no'])
        
        populator = VendorDataPopulator()
        results = []
        
        for child in child_records:
            result = populator.populate_vendor_data_from_existing_onboarding(
                vendor_master.name,
                vendor_master.office_email_primary,
                child['name'],
                head['name']
            )
            results.append({
                'child_record': child['name'],
                'result': result
            })
        
        # Mark head record as populated
        frappe.db.set_value("Vendor Onboarding", head['name'], "multi_records_populated", 1)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": f"Populated {len(child_records)} child records",
            "results": results
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Bulk populate error: {frappe.get_traceback()}", "Bulk Populate Error")
        return {"status": "error", "message": f"Bulk populate failed: {str(e)}"}


@frappe.whitelist()
def validate_population_requirements(vendor_master_name, office_email_primary):
    """
    Validate if data population can be performed
    """
    try:
        populator = VendorDataPopulator()
        
        # Check existing vendor
        existing_vendor = frappe.db.sql("""
            SELECT name, onboarding_form_status 
            FROM `tabVendor Master` 
            WHERE office_email_primary = %s
        """, (office_email_primary,), as_dict=True)
        
        if not existing_vendor:
            return {"status": "error", "message": "No existing vendor found with this email"}
        
        # Check approved onboarding records
        approved_records = frappe.db.sql("""
            SELECT name, creation 
            FROM `tabVendor Onboarding` 
            WHERE ref_no = %s AND onboarding_form_status = 'Approved'
            ORDER BY creation DESC
        """, (existing_vendor[0]['name'],), as_dict=True)
        
        # Check new vendor master
        new_vendor = frappe.db.sql("""
            SELECT name, onboarding_ref_no 
            FROM `tabVendor Master` 
            WHERE name = %s
        """, (vendor_master_name,), as_dict=True)
        
        if not new_vendor:
            return {"status": "error", "message": "New vendor master not found"}
        
        return {
            "status": "success",
            "message": "Validation passed",
            "existing_vendor": existing_vendor[0]['name'],
            "approved_records_count": len(approved_records),
            "latest_approved": approved_records[0]['name'] if approved_records else None,
            "new_vendor": new_vendor[0]['name'],
            "new_onboarding": new_vendor[0]['onboarding_ref_no']
        }
        
    except Exception as e:
        frappe.log_error(f"Validation error: {frappe.get_traceback()}", "Validation Error")
        return {"status": "error", "message": f"Validation failed: {str(e)}"}


# Performance optimized version for your update_van_core_docs_multi_case function
def optimized_update_van_core_docs_multi_case(doc, method=None):
    """
    Optimized version of your multi-company update function
    """
    if not (doc.head_target == 1 and doc.registered_for_multi_companies == 1 and 
            doc.form_fully_submitted_by_vendor == 1):
        return
    
    if doc.multi_records_populated == 1:
        return  # Already populated
    
    try:
        # Get all core documents in one query
        core_docs = frappe.db.sql("""
            SELECT name 
            FROM `tabVendor Onboarding` 
            WHERE unique_multi_comp_id = %s AND head_target = 0
        """, (doc.unique_multi_comp_id,), as_dict=True)
        
        if not core_docs:
            return
        
        # Get vendor master
        vendor_master = frappe.get_doc("Vendor Master", doc.ref_no)
        
        # Use optimized populator
        populator = VendorDataPopulator()
        
        for vend_onb_doc in core_docs:
            result = populator.populate_vendor_data_from_existing_onboarding(
                vendor_master.name, 
                vendor_master.office_email_primary,
                vend_onb_doc['name'],
                doc.name
            )
            
            if result['status'] != 'success':
                frappe.log_error(f"Population failed for {vend_onb_doc['name']}: {result['message']}", 
                               "Multi Company Population Error")
        
        # Mark as populated
        frappe.db.set_value("Vendor Onboarding", doc.name, "multi_records_populated", 1)
        frappe.db.commit()
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Multi company update error: {frappe.get_traceback()}", 
                        "Multi Company Update Error")


# Monitoring and debugging functions
@frappe.whitelist()
def get_population_status(vendor_onboarding_name):
    """
    Get status of data population for a vendor onboarding record
    """
    try:
        # Get basic info
        basic_info = frappe.db.sql("""
            SELECT name, ref_no, onboarding_form_status, multi_records_populated,
                   document_details, payment_detail, manufacturing_details, certificate_details
            FROM `tabVendor Onboarding` 
            WHERE name = %s
        """, (vendor_onboarding_name,), as_dict=True)
        
        if not basic_info:
            return {"status": "error", "message": "Vendor onboarding record not found"}
        
        info = basic_info[0]
        
        # Check if related documents have data
        status = {
            "vendor_onboarding": info['name'],
            "vendor_master": info['ref_no'],
            "form_status": info['onboarding_form_status'],
            "multi_records_populated": info['multi_records_populated'],
            "documents": {}
        }
        
        # Check each document type
        if info['document_details']:
            legal_data = frappe.db.sql("SELECT COUNT(*) as count FROM `tabGST Table` WHERE parent = %s", 
                                     (info['document_details'],), as_dict=True)
            status["documents"]["legal_documents"] = {
                "name": info['document_details'],
                "gst_records": legal_data[0]['count'] if legal_data else 0
            }
        
        if info['payment_detail']:
            banker_data = frappe.db.sql("SELECT COUNT(*) as count FROM `tabBanker Details` WHERE parent = %s", 
                                      (info['payment_detail'],), as_dict=True)
            status["documents"]["payment_details"] = {
                "name": info['payment_detail'],
                "banker_records": banker_data[0]['count'] if banker_data else 0
            }
        
        if info['manufacturing_details']:
            material_data = frappe.db.sql("SELECT COUNT(*) as count FROM `tabMaterials Supplied` WHERE parent = %s", 
                                        (info['manufacturing_details'],), as_dict=True)
            status["documents"]["manufacturing_details"] = {
                "name": info['manufacturing_details'],
                "material_records": material_data[0]['count'] if material_data else 0
            }
        
        if info['certificate_details']:
            cert_data = frappe.db.sql("SELECT COUNT(*) as count FROM `tabCertificates` WHERE parent = %s", 
                                    (info['certificate_details'],), as_dict=True)
            status["documents"]["certificate_details"] = {
                "name": info['certificate_details'],
                "certificate_records": cert_data[0]['count'] if cert_data else 0
            }
        
        return {"status": "success", "data": status}
        
    except Exception as e:
        return {"status": "error", "message": f"Status check failed: {str(e)}"}


# Integration with your existing code
def enhanced_update_van_core_docs_multi_case(doc, method=None):
    """
    Enhanced version that can replace your existing function
    """
    if not (doc.head_target == 1 and doc.registered_for_multi_companies == 1 and 
            doc.form_fully_submitted_by_vendor == 1):
        return
    
    if doc.multi_records_populated == 1:
        return
    
    # Use the optimized function
    optimized_update_van_core_docs_multi_case(doc, method)
    
    # Log the operation
    frappe.log_error(f"Multi-company records populated for {doc.name}", "Multi Company Population Success")