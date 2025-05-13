import frappe
from frappe import _
from frappe.model.document import Document
import json

# will be used for vendor master updation
@frappe.whitelist(allow_guest=True)
def create_vendor_master(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        # Create new Vendor Master document
        doc = frappe.new_doc("Vendor Master")

        # Set parent fields
        for field in [
            "vendor_title", "vendor_name", "office_email_primary", "search_term",
            "purchase_organization", "terms_of_payment", "account_group",
            "payee_in_document", "gr_based_inv_ver", "service_based_inv_ver",
            "check_double_invoice", "vendor_code", "order_currency", "incoterms",
            "purchase_group", "country", "mobile_number", "registered_date",
            "incoterms2", "qa_required", "registered_by", "purchase_team_approval",
            "purchase_team_second", "purchase_head_approval", "purchase_head_second_approval",
            "qa_team_approval", "qa_head_approval", "accounts_team_approval",
            "accounts_team_second_approval", "status", "onboarding_form_status",
            "onboarding_ref_no", "rejection_comment"
        ]:
            if field in data:
                doc.set(field, data[field])

        # Add child table: Multiple Company Data
        if "multiple_company_data" in data:
            for row in data["multiple_company_data"]:
                doc.append("multiple_company_data", row)

        # Add child table: Vendor Types
        if "vendor_types" in data:
            for row in data["vendor_types"]:
                doc.append("vendor_types", row)

        # Save and commit
        doc.save()
        frappe.db.commit()

        return {"status": "success", "name": doc.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Master API Error")
        return {
            "status": "error",
            "message": "Failed to create Vendor Master",
            "error": str(e)
        }

# check for existing vendor email and create vendor master, vendor onboarding & related link documents
@frappe.whitelist(allow_guest=True)
def vendor_registration(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        if data.get("office_email_primary"):
            exists = frappe.get_all(
                "Vendor Master",
                filters={"office_email_primary": data["office_email_primary"]},
                limit=1
            )
            if exists:
                return {
                    "status": "error",
                    "message": "Email already exists"
                }

        # Create Vendor Master
        vendor_master = frappe.new_doc("Vendor Master")

        for field in [
            "vendor_title", 
            "vendor_name", 
            "office_email_primary", 
            "country", 
            "mobile_number", 
            "registered_date", 
            "qa_required"
        ]:
            if field in data:
                vendor_master.set(field, data[field])

        vendor_master.payee_in_document = 1
        vendor_master.gr_based_inv_ver = 1
        vendor_master.service_based_inv_ver = 1
        vendor_master.check_double_invoice = 1

        if "multiple_company_data" in data:
            for row in data["multiple_company_data"]:
                vendor_master.append("multiple_company_data", row)

        if "vendor_types" in data:
            for row in data["vendor_types"]:
                vendor_master.append("vendor_types", row)

        vendor_master.save()
        frappe.db.commit()

        # Create Vendor Onboarding
        vendor_onboarding = frappe.new_doc("Vendor Onboarding")
        vendor_onboarding.ref_no = vendor_master.name

        for field in [
            "qms_required", "purchase_organization", "account_group",
            "purchase_group", "terms_of_payment", "order_currency", "incoterms"
        ]:
            if field in data:
                vendor_onboarding.set(field, data[field])

        vendor_onboarding.payee_in_document = 1
        vendor_onboarding.gr_based_inv_ver = 1
        vendor_onboarding.service_based_inv_ver = 1
        vendor_onboarding.check_double_invoice = 1

        if "multiple_company" in data:
            for row in data["multiple_company"]:
                vendor_onboarding.append("multiple_company", row)

        if "vendor_types" in data:
            for row in data["vendor_types"]:
                vendor_onboarding.append("vendor_types", row)

        vendor_onboarding.save()
        frappe.db.commit()

        # Create and link additional onboarding documents
        def create_related_doc(doctype, link_field):
            doc = frappe.new_doc(doctype)
            doc.vendor_onboarding = vendor_onboarding.name
            doc.ref_no = vendor_master.name
            doc.save()
            frappe.db.commit()
            return doc.name

        payment_detail = create_related_doc("Vendor Onboarding Payment Details", "vendor_onboarding")
        document_details = create_related_doc("Legal Documents", "vendor_onboarding")
        certificate_details = create_related_doc("Vendor Onboarding Certificates", "vendor_onboarding")
        manufacturing_details = create_related_doc("Vendor Onboarding Manufacturing Details", "vendor_onboarding")

        # Update vendor onboarding doc with references
        vendor_onboarding.payment_detail = payment_detail
        vendor_onboarding.document_details = document_details
        vendor_onboarding.certificate_details = certificate_details
        vendor_onboarding.manufacturing_details = manufacturing_details
        vendor_onboarding.save()
        frappe.db.commit()

        return {
            "status": "success",
            "vendor_master": vendor_master.name,
            "vendor_onboarding": vendor_onboarding.name,
            "payment_detail": payment_detail,
            "document_details": document_details,
            "certificate_details": certificate_details,
            "manufacturing_details": manufacturing_details
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Registration Full Flow Error")
        return {
            "status": "error",
            "message": "Vendor registration failed",
            "error": str(e)
        }






