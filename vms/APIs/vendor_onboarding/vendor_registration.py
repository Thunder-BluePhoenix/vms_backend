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
            "check_double_invoice", "order_currency", "incoterms",
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

        vendor_master = None

        # Check if vendor with the given email already exists
        if data.get("office_email_primary"):
            exists = frappe.get_all(
                "Vendor Master",
                filters={"office_email_primary": data["office_email_primary"]},
                fields=["name"],
                limit=1
            )

            if exists:
                vendor_master = frappe.get_doc("Vendor Master", exists[0]["name"])
            else:
                vendor_master = frappe.new_doc("Vendor Master")
        else:
            vendor_master = frappe.new_doc("Vendor Master")

        # vendor master fields
        for field in [
            "vendor_title", "vendor_name", "office_email_primary", "search_term",
            "country", "mobile_number", "registered_date", "qa_required"
        ]:
            if field in data:
                vendor_master.set(field, data[field])

        vendor_master.payee_in_document = 1
        vendor_master.gr_based_inv_ver = 1
        vendor_master.service_based_inv_ver = 1
        vendor_master.check_double_invoice = 1

        # Update child tables
        if "multiple_company_data" in data:
            for row in data["multiple_company_data"]:
                is_duplicate = False
                for existing in vendor_master.multiple_company_data:
                    if (
                        (existing.company_name or "").lower().strip() == (row.get("company_name") or "").lower().strip() and
                        (existing.purchase_organization or "").lower().strip() == (row.get("purchase_organization") or "").lower().strip() and
                        (existing.account_group or "").lower().strip() == (row.get("account_group") or "").lower().strip() and
                        (existing.purchase_group or "").lower().strip() == (row.get("purchase_group") or "").lower().strip()
                    ):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    vendor_master.append("multiple_company_data", row)


        if "vendor_types" in data:
            for row in data["vendor_types"]:
                is_duplicate = False
                for existing in vendor_master.vendor_types:
                    if (existing.vendor_type or "").lower().strip() == (row.get("vendor_type") or "").lower().strip():
                        is_duplicate = True
                        break

                if not is_duplicate:
                    vendor_master.append("vendor_types", row)

        vendor_master.save(ignore_permissions=True)
        frappe.db.commit()
            
        # Create Vendor Onboarding
        vendor_onboarding = frappe.new_doc("Vendor Onboarding")
        vendor_onboarding.ref_no = vendor_master.name

        for field in [
            "qms_required","company_name", "purchase_organization", "account_group",
            "purchase_group", "terms_of_payment", "order_currency", "incoterms"
        ]:
            if field in data:
                vendor_onboarding.set(field, data[field])

        vendor_onboarding.payee_in_document = 1
        vendor_onboarding.gr_based_inv_ver = 1
        vendor_onboarding.service_based_inv_ver = 1
        vendor_onboarding.check_double_invoice = 1

        # if "multiple_company" in data:
        #     for row in data["multiple_company"]:
        #         vendor_onboarding.append("multiple_company", row)

        if "vendor_types" in data:
            for row in data["vendor_types"]:
                is_duplicate = False
                for existing in vendor_master.vendor_types:
                    if (existing.vendor_type or "").lower().strip() == (row.get("vendor_type") or "").lower().strip():
                        is_duplicate = True
                        break

                if not is_duplicate:
                    vendor_master.append("vendor_types", row)

        vendor_onboarding.save()
        frappe.db.commit()

        # Create and link additional onboarding documents
        def create_related_doc(doctype):
            doc = frappe.new_doc(doctype)
            doc.vendor_onboarding = vendor_onboarding.name
            doc.ref_no = vendor_master.name
            doc.save()
            frappe.db.commit()
            return doc.name

        payment_detail = create_related_doc("Vendor Onboarding Payment Details")
        document_details = create_related_doc("Legal Documents")
        certificate_details = create_related_doc("Vendor Onboarding Certificates")
        manufacturing_details = create_related_doc("Vendor Onboarding Manufacturing Details")
        company_details = create_related_doc("Vendor Onboarding Company Details")

        # Add vendor_company_details in child table
        vendor_onboarding.append("vendor_company_details", {
            "vendor_company_details": company_details 
        })

        # Update vendor onboarding with doc names
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
            "manufacturing_details": manufacturing_details,
            "company_details": company_details
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Registration Full Flow Error")
        return {
            "status": "error",
            "message": "Vendor registration failed",
            "error": str(e)
        }




@frappe.whitelist(allow_guest=True)
def onboarding_form_submit(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        onb_ref = data.get('onb_id')
        onb = frappe.get_doc("Vendor Onboarding", onb_ref)
        onb.form_fully_submitted_by_vendor = data.get("completed")
        onb.save()
        frappe.db.commit()
        return {
            "status": "Success",
            "message": "Successfully Submitted Vendor onboarding data",
            
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Onboarding Registration from Submit by vendor error")
        return {
            "status": "error",
            "message": "Failed to update Vendor onboarding data",
            "error": str(e)
        }
    
# send registration email link
@frappe.whitelist(allow_guest=True)
def send_registration_email_link(vendor_onboarding):
    try:
        if not vendor_onboarding:
            return {
                "status": "error",
                "message": "Missing 'vendor_onboarding' parameter."
            }

        # get Vendor Onboarding document
        onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Proceed only if email hasn't been sent
        if not onboarding_doc.sent_registration_email_link:
            vendor_master = frappe.get_doc("Vendor Master", onboarding_doc.ref_no)

            recipient_email = vendor_master.office_email_primary or vendor_master.office_email_secondary
            if not recipient_email:
                return {
                    "status": "error",
                    "message": "No recipient email found for the vendor."
                }

            registration_link = f"{frappe.utils.get_url()}/register?vendor={vendor_master.name}"

            frappe.sendmail(
                recipients=[recipient_email],
                subject="Welcome to VMS",
                message=f"""
                    <p>Hello {vendor_master.vendor_name},</p>
                    <p>Click on the link below to complete your registration:</p>
                    <p style="margin: 15px 0px;">
                        <a href="{registration_link}" rel="nofollow" class="btn btn-primary">Complete Registration</a>
                    </p>
                    <p style="margin-top: 15px">Thanks,<br>VMS Team</p>
                    <br>
                    <p>You can also copy-paste the following link into your browser:<br>
                    <a href="{registration_link}">{registration_link}</a></p>
                """,
                delayed=False
            )

            onboarding_doc.sent_registration_email_link = 1
            onboarding_doc.save(ignore_permissions=True)
            frappe.db.commit()

            return {
                "status": "success",
                "message": "Registration email sent successfully."
            }

        else:
            return {
                "status": "info",
                "message": "Registration email has already been sent."
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Onboarding Registration Email Error")
        return {
            "status": "error",
            "message": "Failed to send registration email.",
            "error": str(e)
        }
