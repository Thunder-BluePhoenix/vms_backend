# File Location: frappe-bench/apps/vms/vms/vendor_onboarding/vendor_document_management.py
# This is the main document management module

import frappe
from frappe import _
from frappe.model.document import Document
import json

class VendorDocumentManager:
    """Manages the synchronization and maintenance of vendor documents"""
    
    @staticmethod
    def create_or_update_vendor_master_docs(vendor_onboarding_name):
        """
        Creates or updates vendor master documents from onboarding documents
        Called after vendor onboarding approval
        """
        try:
            # Get vendor onboarding document
            onboarding = frappe.get_doc("Vendor Onboarding", vendor_onboarding_name)
            vendor_master = frappe.get_doc("Vendor Master", onboarding.ref_no)
            
            # 1. Handle Bank Details
            bank_details_name = VendorDocumentManager.sync_bank_details(
                onboarding, vendor_master
            )
            
            # 2. Handle Document Details (combines Legal Documents + Certificates)
            document_details_name = VendorDocumentManager.sync_document_details(
                onboarding, vendor_master
            )
            
            # 3. Handle Manufacturing Details
            manufacturing_details_name = VendorDocumentManager.sync_manufacturing_details(
                onboarding, vendor_master
            )
            
            # Update vendor master with document links
            vendor_master.bank_details = bank_details_name
            vendor_master.document_details = document_details_name
            vendor_master.manufacturing_details = manufacturing_details_name
            
            # Add onboarding record to vendor master's table
            VendorDocumentManager.add_onboarding_record(vendor_master, onboarding)
            
            vendor_master.flags.ignore_validate_update_after_submit = True
            vendor_master.save(ignore_permissions=True)
            frappe.db.commit()
            
            return {
                "status": "success",
                "message": "Vendor master documents updated successfully",
                "bank_details": bank_details_name,
                "document_details": document_details_name,
                "manufacturing_details": manufacturing_details_name
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Vendor Document Sync Error")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def sync_bank_details(onboarding, vendor_master):
        """Sync bank details from onboarding to vendor master"""
        
        if not onboarding.payment_detail:
            return None
            
        # Get onboarding payment details
        onb_payment = frappe.get_doc("Vendor Onboarding Payment Details", onboarding.payment_detail)
        
        # Check if vendor bank details already exists
        if vendor_master.bank_details:
            vendor_bank = frappe.get_doc("Vendor Bank Details", vendor_master.bank_details)
        else:
            vendor_bank = frappe.new_doc("Vendor Bank Details")
            vendor_bank.ref_no = vendor_master.name
        
        # Copy fields from onboarding to vendor master document
        fields_to_copy = [
            "country", "bank_name", "ifsc_code", "account_number",
            "name_of_account_holder", "type_of_account", "currency",
            "currency_code", "bank_proof", "bank_proof_by_purchase_team",
            "rtgs", "neft", "ift", "add_intermediate_bank_details"
        ]
        
        for field in fields_to_copy:
            if hasattr(onb_payment, field):
                setattr(vendor_bank, field, getattr(onb_payment, field))
        
        # Copy child tables
        # Banker Details
        vendor_bank.banker_details = []
        for row in onb_payment.banker_details:
            vendor_bank.append("banker_details", row.as_dict())
        
        # International Bank Details
        vendor_bank.international_bank_details = []
        for row in onb_payment.international_bank_details:
            vendor_bank.append("international_bank_details", row.as_dict())
        
        # Intermediate Bank Details
        if onb_payment.add_intermediate_bank_details:
            vendor_bank.intermediate_bank_details = []
            for row in onb_payment.intermediate_bank_details:
                vendor_bank.append("intermediate_bank_details", row.as_dict())
        
        vendor_bank.flags.ignore_validate_update_after_submit = True
        vendor_bank.save(ignore_permissions=True)
        return vendor_bank.name
    
    @staticmethod
    def sync_document_details(onboarding, vendor_master):
        """
        Sync document details from onboarding to vendor master
        This combines both Legal Documents AND Vendor Onboarding Certificates
        """
        
        # Check if vendor document details already exists
        if vendor_master.document_details:
            vendor_docs = frappe.get_doc("Vendor Document Details", vendor_master.document_details)
        else:
            vendor_docs = frappe.new_doc("Vendor Document Details")
            vendor_docs.ref_no = vendor_master.name
        
        # Part 1: Sync from Legal Documents
        if onboarding.document_details:
            onb_legal_docs = frappe.get_doc("Legal Documents", onboarding.document_details)
            
            # Copy legal document fields
            legal_fields = [
                "company_pan_number", "name_on_company_pan", "pan_proof",
                "enterprise_registration_number", "entity_proof",
                "iec", "iec_proof", "msme_registered", "msme_enterprise_type",
                "udyam_number", "name_on_udyam_certificate", "msme_proof",
                "form_10f_proof", "trc_certificate_no", "trc_certificate",
                "pe_certificate"
            ]
            
            for field in legal_fields:
                if hasattr(onb_legal_docs, field):
                    setattr(vendor_docs, field, getattr(onb_legal_docs, field))
            
            # Copy GST table
            vendor_docs.gst_table = []
            for row in onb_legal_docs.gst_table:
                vendor_docs.append("gst_table", row.as_dict())
        
        # Part 2: Sync from Vendor Onboarding Certificates
        if onboarding.certificate_details:
            onb_certificates = frappe.get_doc("Vendor Onboarding Certificates", onboarding.certificate_details)
            
            # Copy certificate fields (these should be in the certificates child table)
            if hasattr(vendor_docs, "certificates"):
                vendor_docs.certificates = []
                
                # Map common certificate types
                certificate_mappings = [
                    ("iso_9001_2015", "ISO 9001:2015"),
                    ("iso_14001_2015", "ISO 14001:2015"),
                    ("iso_45001_2018", "ISO 45001:2018"),
                    ("iso_50001_2018", "ISO 50001:2018"),
                    ("iatf_16949_2016", "IATF 16949:2016"),
                    ("as9100d", "AS9100D"),
                    ("fsms_22000_2018", "FSMS 22000:2018"),
                    ("haccp", "HACCP"),
                    ("kosher", "KOSHER"),
                    ("halal", "HALAL"),
                    ("sa_8000_2014", "SA 8000:2014"),
                    ("iso_27001_2013", "ISO 27001:2013"),
                    ("iso_13485_2016", "ISO 13485:2016"),
                    ("bis", "BIS"),
                    ("isi", "ISI"),
                    ("aeo", "AEO"),
                    ("fda", "FDA"),
                    ("ce", "CE"),
                    ("ul", "UL"),
                    ("zed_bronze", "ZED Bronze"),
                    ("zed_silver", "ZED Silver"),
                    ("zed_gold", "ZED Gold"),
                    ("zed_diamond", "ZED Diamond"),
                    ("zed_platinum", "ZED Platinum")
                ]
                
                for field_name, cert_type in certificate_mappings:
                    if hasattr(onb_certificates, field_name) and getattr(onb_certificates, field_name):
                        # Add to certificates child table
                        vendor_docs.append("certificates", {
                            "certificate_type": cert_type,
                            "certificate_file": getattr(onb_certificates, field_name),
                            "is_available": 1
                        })
                
                # Handle any additional certificates from child table if exists
                if hasattr(onb_certificates, "additional_certificates"):
                    for cert in onb_certificates.additional_certificates:
                        vendor_docs.append("certificates", cert.as_dict())
        
        vendor_docs.flags.ignore_validate_update_after_submit = True
        vendor_docs.save(ignore_permissions=True)
        return vendor_docs.name
    
    @staticmethod
    def sync_manufacturing_details(onboarding, vendor_master):
        """Sync manufacturing details from onboarding to vendor master"""
        
        if not onboarding.manufacturing_details:
            return None
            
        # Get onboarding manufacturing details
        onb_manuf = frappe.get_doc("Vendor Onboarding Manufacturing Details", 
                                   onboarding.manufacturing_details)
        
        # Check if vendor manufacturing details already exists
        if vendor_master.manufacturing_details:
            vendor_manuf = frappe.get_doc("Vendor Manufacturing Details", 
                                         vendor_master.manufacturing_details)
        else:
            vendor_manuf = frappe.new_doc("Vendor Manufacturing Details")
            vendor_manuf.ref_no = vendor_master.name
        
        # Copy fields
        fields_to_copy = [
            "details_of_product_manufactured", "total_godown", "storage_capacity",
            "spare_capacity", "type_of_premises", "working_hours", "weekly_holidays",
            "number_of_manpower", "annual_revenue", "google_address_pin",
            "cold_storage", "brochure_proof", "organisation_structure_document"
        ]
        
        for field in fields_to_copy:
            if hasattr(onb_manuf, field):
                setattr(vendor_manuf, field, getattr(onb_manuf, field))
        
        # Copy materials supplied table
        if hasattr(onb_manuf, "materials_supplied"):
            vendor_manuf.materials_supplied = []
            for row in onb_manuf.materials_supplied:
                vendor_manuf.append("materials_supplied", row.as_dict())
        
        vendor_manuf.flags.ignore_validate_update_after_submit = True
        vendor_manuf.save(ignore_permissions=True)
        return vendor_manuf.name
    
    @staticmethod
    def add_onboarding_record(vendor_master, onboarding):
        """Add onboarding record to vendor master's tracking table"""
        
        # Check if record already exists
        existing = False
        for record in vendor_master.vendor_onb_records:
            if record.vendor_onboarding_no == onboarding.name:
                existing = True
                # Update existing record
                record.onboarding_date = onboarding.creation
                record.onboarding_status = onboarding.onboarding_form_status
                record.onboarding_form_status = onboarding.onboarding_form_status
                record.payment_details = onboarding.payment_detail
                record.document_details = onboarding.document_details
                record.certificate_details = onboarding.certificate_details
                record.manufacturing_details = onboarding.manufacturing_details
                record.is_current = 1
                record.registered_by = onboarding.registered_by
                record.purchase_team_approval = onboarding.purchase_t_approval
                record.purchase_head_approval = onboarding.purchase_h_approval
                record.accounts_team_approval = onboarding.accounts_t_approval
                record.accounts_head_approval = onboarding.accounts_h_approval
                record.created_by_accounts_team = onboarding.register_by_account_team
                record.synced_date = frappe.utils.now()
                record.synced_by = frappe.session.user
                break
        
        if not existing:
            # Mark all existing records as not current
            for record in vendor_master.vendor_onb_records:
                record.is_current = 0
            
            # Add new record
            vendor_master.append("vendor_onb_records", {
                "vendor_onboarding_no": onboarding.name,
                "onboarding_date": onboarding.creation,
                "onboarding_form_status": onboarding.onboarding_form_status,
                "onboarding_status": onboarding.onboarding_form_status,
                "payment_details": onboarding.payment_detail,
                "document_details": onboarding.document_details,
                "certificate_details": onboarding.certificate_details,
                "manufacturing_details": onboarding.manufacturing_details,
                "is_current": 1,
                "registered_by" : onboarding.registered_by,
                "purchase_team_approval" : onboarding.purchase_t_approval,
                "purchase_head_approval" : onboarding.purchase_h_approval,
                "accounts_team_approval" : onboarding.accounts_t_approval,
                "accounts_head_approval" : onboarding.accounts_h_approval,
                "created_by_accounts_team": onboarding.register_by_account_team,
                "synced_date": frappe.utils.now(),
                "synced_by": frappe.session.user
            })


# Hook Functions
@frappe.whitelist()
def sync_vendor_documents_on_approval(vendor_onboarding_name):
    """
    Call this function when vendor onboarding is approved
    Can be triggered from workflow or button click
    """
    return VendorDocumentManager.create_or_update_vendor_master_docs(vendor_onboarding_name)


@frappe.whitelist()
def on_vendor_onboarding_submit(doc, method):
    """
    Hook method called when Vendor Onboarding is submitted
    """
    if doc.onboarding_form_status == "Approved":
        sync_vendor_documents_on_approval(doc.name)


def vendor_master_on_update(doc, method):
    """
    Hook to track manual updates to vendor documents
    """
    # Check if documents were manually updated (not from onboarding sync)
    if frappe.flags.in_import or frappe.flags.in_migrate:
        return
    
    # Log manual updates
    if doc.has_value_changed("bank_details") or \
       doc.has_value_changed("document_details") or \
       doc.has_value_changed("manufacturing_details"):
        
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Vendor Master",
            "reference_name": doc.name,
            "content": f"Vendor documents manually updated by {frappe.session.user}"
        }).insert(ignore_permissions=True)


@frappe.whitelist()
def get_vendor_document_history(vendor_master_name):
    """Get complete document history for a vendor"""
    
    vendor = frappe.get_doc("Vendor Master", vendor_master_name)
    
    history = []
    for record in vendor.vendor_onb_records:
        history.append({
            "onboarding_id": record.vendor_onboarding_no,
            "date": record.onboarding_date,
            "status": record.onboarding_status,
            "payment_details": record.payment_details,
            "document_details": record.document_details,
            "certificate_details": record.certificate_details,
            "manufacturing_details": record.manufacturing_details,
            "is_current": record.is_current,
            "synced_date": record.synced_date,
            "synced_by": record.synced_by
        })
    
    current_docs = {
        "bank_details": vendor.bank_details,
        "document_details": vendor.document_details,
        "manufacturing_details": vendor.manufacturing_details
    }
    
    return {
        "current_documents": current_docs,
        "onboarding_history": history
    }


@frappe.whitelist()
def restore_from_onboarding(vendor_master_name, onboarding_name):
    """
    Restore vendor master documents from a specific onboarding record
    Useful for reverting to previous version
    """
    vendor = frappe.get_doc("Vendor Master", vendor_master_name)
    
    # Verify the onboarding belongs to this vendor
    onboarding = frappe.get_doc("Vendor Onboarding", onboarding_name)
    if onboarding.ref_no != vendor_master_name:
        frappe.throw(_("This onboarding does not belong to the specified vendor"))
    
    # Restore documents
    result = VendorDocumentManager.create_or_update_vendor_master_docs(onboarding_name)
    
    return result