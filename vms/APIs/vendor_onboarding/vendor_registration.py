import frappe
from frappe import _
from frappe.model.document import Document
from urllib.parse import urlencode
import json
from datetime import datetime






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


@frappe.whitelist(allow_guest=True)
def vendor_registration(data):
    multi_companies = data.get("for_multiple_company")
    if multi_companies != 1:
        vendor_registration_single(data)

    else:
        vendor_registration_multi(data)



@frappe.whitelist(allow_guest=True)
def vendor_registration_multi(data):
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
        vendor_master.created_from_registration = 1

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

        usr = frappe.session.user
        vendor_master.registered_by = usr

        vendor_master.save(ignore_permissions=True)
        frappe.db.commit()



        now = datetime.now()
        year_month_prefix = f"MCD{now.strftime('%y')}{now.strftime('%m')}"  

        existing_max = frappe.db.sql(
            """
            SELECT MAX(CAST(SUBSTRING(unique_multi_comp_id, 8) AS UNSIGNED))
            FROM `Vendor Onboarding`
            WHERE unique_multi_comp_id LIKE %s
            """,
            (year_month_prefix + "%",),
            as_list=True
        )

        max_count = existing_max[0][0] or 0
        new_count = max_count + 1


        unique_multi_comp_id = f"{year_month_prefix}{str(new_count).zfill(5)}"

        
            
        # Create Vendor Onboarding
        vendor_onboarding_docs = []
        payment_detail_docs = []
        document_details_docs = []
        certificate_details_docs = []
        manufacturing_details_docs = []
        company_details_docs = []
        
        multi_companies = data.get("company_name")

        for comp in multi_companies:


            vendor_onboarding = frappe.new_doc("Vendor Onboarding")
            vendor_onboarding.ref_no = vendor_master.name
            vendor_onboarding.registered_for_multi_companies = 1
            vendor_onboarding.unique_multi_comp_id = unique_multi_comp_id

            for field in [
                "qms_required", "purchase_organization", "account_group",
                "purchase_group", "terms_of_payment", "order_currency", "incoterms", "reconciliation_account"
            ]:
                if field in data:
                    vendor_onboarding.set(field, data[field])

            vendor_onboarding.payee_in_document = 1
            vendor_onboarding.gr_based_inv_ver = 1
            vendor_onboarding.service_based_inv_ver = 1
            vendor_onboarding.check_double_invoice = 1
            vendor_onboarding.company_name = comp

            for company in multi_companies:
                vendor_onboarding.append("multiple_company", {
                    "company_name": company
                    })

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

            vendor_onboarding.registered_by = usr

            vendor_onboarding.save()
            frappe.db.commit()
            vendor_onboarding_docs.append(vendor_onboarding.name)

            # Create and link additional onboarding documents
            def create_related_doc(doctype):
                doc = frappe.new_doc(doctype)
                doc.vendor_onboarding = vendor_onboarding.name
                doc.ref_no = vendor_master.name
                doc.registered_for_multi_companies = 1
                doc.unique_multi_comp_id = unique_multi_comp_id
                doc.save()
                frappe.db.commit()
                return doc.name
            
            def create_related_doc_company(doctype):
                doc = frappe.new_doc(doctype)
                doc.vendor_onboarding = vendor_onboarding.name
                doc.ref_no = vendor_master.name
                doc.office_email_primary = vendor_master.office_email_primary
                doc.telephone_number = vendor_master.mobile_number
                doc.registered_for_multi_companies = 1
                doc.unique_multi_comp_id = unique_multi_comp_id
                doc.save()
                frappe.db.commit()
                return doc.name
            
            def create_related_doc_pd(doctype):
                doc = frappe.new_doc(doctype)
                doc.vendor_onboarding = vendor_onboarding.name
                doc.ref_no = vendor_master.name
                doc.country = data.get("country")
                doc.registered_for_multi_companies = 1
                doc.unique_multi_comp_id = unique_multi_comp_id
                doc.save()
                frappe.db.commit()
                return doc.name


            payment_detail = create_related_doc_pd("Vendor Onboarding Payment Details")
            payment_detail_docs.append(payment_detail)
            document_details = create_related_doc("Legal Documents")
            document_details_docs.append(document_details)
            certificate_details = create_related_doc("Vendor Onboarding Certificates")
            certificate_details_docs.append(certificate_details)
            manufacturing_details = create_related_doc("Vendor Onboarding Manufacturing Details")
            manufacturing_details_docs.append(manufacturing_details)
            company_details = create_related_doc_company("Vendor Onboarding Company Details")
            company_details_docs.append(company_details)

            if company_details:
                vendor_onb_company = frappe.get_doc("Vendor Onboarding Company Details", company_details)

                for field in ["vendor_title", "vendor_name",]:
                    if field in data:
                        vendor_onb_company.set(field, data[field])
                vendor_onb_company.company_name = comp

                vendor_onb_company.save()

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
            # send_registration_email_link(vendor_onboarding.name, vendor_master.name)
            frappe.db.commit()
        

        send_registration_email_link(vendor_onboarding_docs[0], vendor_master.name)
        return {
            "status": "success",
            "vendor_master": vendor_master.name,
            "vendor_onboarding": vendor_onboarding_docs,
            "payment_detail": payment_detail_docs,
            "document_details": document_details_docs,
            "certificate_details": certificate_details_docs,
            "manufacturing_details": manufacturing_details_docs,
            "company_details": company_details_docs
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Registration Full Flow Error")
        return {
            "status": "error",
            "message": "Vendor registration failed",
            "error": str(e)
        }








# check for existing vendor email and create vendor master, vendor onboarding & related link documents
@frappe.whitelist(allow_guest=True)
def vendor_registration_single(data):
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
        vendor_master.created_from_registration = 1

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

        usr = frappe.session.user
        vendor_master.registered_by = usr

        vendor_master.save(ignore_permissions=True)
        frappe.db.commit()
            
        # Create Vendor Onboarding
        vendor_onboarding = frappe.new_doc("Vendor Onboarding")
        vendor_onboarding.ref_no = vendor_master.name

        for field in [
            "qms_required","company_name", "purchase_organization", "account_group",
            "purchase_group", "terms_of_payment", "order_currency", "incoterms", "reconciliation_account"
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

        vendor_onboarding.registered_by = usr

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
        
        def create_related_doc_company(doctype):
            doc = frappe.new_doc(doctype)
            doc.vendor_onboarding = vendor_onboarding.name
            doc.ref_no = vendor_master.name
            doc.office_email_primary = vendor_master.office_email_primary
            doc.telephone_number = vendor_master.mobile_number
            doc.save()
            frappe.db.commit()
            return doc.name
        
        def create_related_doc_pd(doctype):
            doc = frappe.new_doc(doctype)
            doc.vendor_onboarding = vendor_onboarding.name
            doc.ref_no = vendor_master.name
            doc.country = data.get("country")
            doc.save()
            frappe.db.commit()
            return doc.name


        payment_detail = create_related_doc_pd("Vendor Onboarding Payment Details")
        document_details = create_related_doc("Legal Documents")
        certificate_details = create_related_doc("Vendor Onboarding Certificates")
        manufacturing_details = create_related_doc("Vendor Onboarding Manufacturing Details")
        company_details = create_related_doc_company("Vendor Onboarding Company Details")

        if company_details:
            vendor_onb_company = frappe.get_doc("Vendor Onboarding Company Details", company_details)

            for field in ["vendor_title", "vendor_name", "company_name"]:
                if field in data:
                    vendor_onb_company.set(field, data[field])

            vendor_onb_company.save()

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
        send_registration_email_link(vendor_onboarding.name, vendor_master.name)
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
def send_registration_email_link(vendor_onboarding, refno):
    try:
        if not vendor_onboarding:
            return {
                "status": "error",
                "message": "Missing 'vendor_onboarding' parameter."
            }

        onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Construct registration link
        http_server = frappe.conf.get("frontend_http")
        registration_link = (
            f"{http_server}/vendor-details-form"
            f"?tabtype=Company%20Detail"
            f"&refno={refno}"
            f"&vendor_onboarding={vendor_onboarding}"
        )

        # Construct QMS form link if required
        qms_section = ""
        if onboarding_doc.qms_required == "Yes":
            query_params = urlencode({
                "vendor_onboarding": onboarding_doc.name,
                "ref_no": onboarding_doc.ref_no
            })
            webform_link = f"{frappe.utils.get_url()}/qms-webform/new?{query_params}"
            qms_section = f"""
                <p>As part of your registration, please also complete the QMS Form at the link below:</p>
                <p style="margin: 15px 0px;">
                    <a href="{webform_link}" rel="nofollow" class="btn btn-secondary">Fill QMS Form</a>
                </p>
                <p>You may also copy and paste this link into your browser:<br>
                <a href="{webform_link}">{webform_link}</a></p>
            """

        # Send registration email only once
        if not onboarding_doc.sent_registration_email_link:
            vendor_master = frappe.get_doc("Vendor Master", refno)
            recipient_email = vendor_master.office_email_primary or vendor_master.office_email_secondary

            if not recipient_email:
                return {
                    "status": "error",
                    "message": "No recipient email found for the vendor."
                }

            frappe.sendmail(
                recipients=[recipient_email],
                subject="Welcome to VMS - Complete Your Registration",
                message=f"""
                    <p>Dear {vendor_master.vendor_name},</p>
                    <p>Your Vendor Onboardng process has Initiated.To complete your registration, please click the link below:</p>
                    <p style="margin: 15px 0px;">
                        <a href="{registration_link}" rel="nofollow" class="btn btn-primary">Complete Registration</a>
                    </p>
                    <p>You may also copy and paste this link into your browser:<br>
                    <a href="{registration_link}">{registration_link}</a></p>

                    {qms_section}

                    <p>Best regards,<br>VMS Team</p>
                """,
                delayed=False
            )

            onboarding_doc.sent_registration_email_link = 1
            onboarding_doc.sent_qms_form_link =1
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
    