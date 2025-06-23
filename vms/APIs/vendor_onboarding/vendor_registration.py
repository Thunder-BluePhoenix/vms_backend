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



# @frappe.whitelist(allow_guest=True)
# def vendor_registration_multi(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)

#         vendor_master = None

#         # Check if vendor with the given email already exists
#         if data.get("office_email_primary"):
#             exists = frappe.get_all(
#                 "Vendor Master",
#                 filters={"office_email_primary": data["office_email_primary"]},
#                 fields=["name"],
#                 limit=1
#             )

#             if exists:
#                 vendor_master = frappe.get_doc("Vendor Master", exists[0]["name"])
#             else:
#                 vendor_master = frappe.new_doc("Vendor Master")
#         else:
#             vendor_master = frappe.new_doc("Vendor Master")

#         # vendor master fields
#         for field in [
#             "vendor_title", "vendor_name", "office_email_primary", "search_term",
#             "country", "mobile_number", "registered_date", "qa_required"
#         ]:
#             if field in data:
#                 vendor_master.set(field, data[field])

#         vendor_master.payee_in_document = 1
#         vendor_master.gr_based_inv_ver = 1
#         vendor_master.service_based_inv_ver = 1
#         vendor_master.check_double_invoice = 1
#         vendor_master.created_from_registration = 1

#         # Update child tables
#         if "multiple_company_data" in data:
#             for row in data["multiple_company_data"]:
#                 is_duplicate = False
#                 for existing in vendor_master.multiple_company_data:
#                     if (
#                         (existing.company_name or "").lower().strip() == (row.get("company_name") or "").lower().strip() and
#                         (existing.purchase_organization or "").lower().strip() == (row.get("purchase_organization") or "").lower().strip() and
#                         (existing.account_group or "").lower().strip() == (row.get("account_group") or "").lower().strip() and
#                         (existing.purchase_group or "").lower().strip() == (row.get("purchase_group") or "").lower().strip()
#                     ):
#                         is_duplicate = True
#                         break

#                 if not is_duplicate:
#                     vendor_master.append("multiple_company_data", row)


#         if "vendor_types" in data:
#             for row in data["vendor_types"]:
#                 is_duplicate = False
#                 for existing in vendor_master.vendor_types:
#                     if (existing.vendor_type or "").lower().strip() == (row.get("vendor_type") or "").lower().strip():
#                         is_duplicate = True
#                         break

#                 if not is_duplicate:
#                     vendor_master.append("vendor_types", row)

#         usr = frappe.session.user
#         vendor_master.registered_by = usr

#         vendor_master.save(ignore_permissions=True)
#         frappe.db.commit()



#         now = datetime.now()
#         year_month_prefix = f"MCD{now.strftime('%y')}{now.strftime('%m')}"  

#         existing_max = frappe.db.sql(
#             """
#             SELECT MAX(CAST(SUBSTRING(unique_multi_comp_id, 8) AS UNSIGNED))
#             FROM `tabVendor Onboarding`
#             WHERE unique_multi_comp_id LIKE %s
#             """,
#             (year_month_prefix + "%",),
#             as_list=True
#         )

#         max_count = existing_max[0][0] or 0
#         new_count = max_count + 1


#         unique_multi_comp_id = f"{year_month_prefix}{str(new_count).zfill(5)}"

        
            
#         # Create Vendor Onboarding
#         vendor_onboarding_docs = []
#         payment_detail_docs = []
#         document_details_docs = []
#         certificate_details_docs = []
#         manufacturing_details_docs = []
#         company_details_docs = []
        
#         multi_companies = data.get("purchase_details")

#         for mc in multi_companies:


#             vendor_onboarding = frappe.new_doc("Vendor Onboarding")
#             vendor_onboarding.ref_no = vendor_master.name
#             vendor_onboarding.registered_for_multi_companies = 1
#             vendor_onboarding.unique_multi_comp_id = unique_multi_comp_id

#             for field in [
#                 "qms_required", "incoterms"
#             ]:
#                 if field in data:
#                     vendor_onboarding.set(field, data[field])

#             vendor_onboarding.payee_in_document = 1
#             vendor_onboarding.gr_based_inv_ver = 1
#             vendor_onboarding.service_based_inv_ver = 1
#             vendor_onboarding.check_double_invoice = 1
#             vendor_onboarding.company_name = mc.company_name
#             vendor_onboarding.purchase_organization = mc.purchase_organization
#             vendor_onboarding.account_group = mc.account_group
#             vendor_onboarding.purchase_group = mc.purchase_group
#             vendor_onboarding.terms_of_payment = mc.terms_of_payment
#             vendor_onboarding.order_currency = mc.order_currency
#             vendor_onboarding.reconciliation_account = mc.reconciliation_account


#             for company in multi_companies:
#                 vendor_onboarding.append("multiple_company", {
#                     "company_name": company
#                     })

#             # if "multiple_company" in data:
#             #     for row in data["multiple_company"]:
#             #         vendor_onboarding.append("multiple_company", row)

#             if "vendor_types" in data:
#                 for row in data["vendor_types"]:
#                     is_duplicate = False
#                     for existing in vendor_master.vendor_types:
#                         if (existing.vendor_type or "").lower().strip() == (row.get("vendor_type") or "").lower().strip():
#                             is_duplicate = True
#                             break

#                     if not is_duplicate:
#                         vendor_master.append("vendor_types", row)

#             vendor_onboarding.registered_by = usr

#             vendor_onboarding.save()
#             frappe.db.commit()
#             vendor_onboarding_docs.append(vendor_onboarding.name)

#             # Create and link additional onboarding documents
#             def create_related_doc(doctype):
#                 doc = frappe.new_doc(doctype)
#                 doc.vendor_onboarding = vendor_onboarding.name
#                 doc.ref_no = vendor_master.name
#                 doc.registered_for_multi_companies = 1
#                 doc.unique_multi_comp_id = unique_multi_comp_id
#                 doc.save()
#                 frappe.db.commit()
#                 return doc.name
            
#             def create_related_doc_company(doctype):
#                 doc = frappe.new_doc(doctype)
#                 doc.vendor_onboarding = vendor_onboarding.name
#                 doc.ref_no = vendor_master.name
#                 doc.office_email_primary = vendor_master.office_email_primary
#                 doc.telephone_number = vendor_master.mobile_number
#                 doc.registered_for_multi_companies = 1
#                 doc.unique_multi_comp_id = unique_multi_comp_id
#                 doc.save()
#                 frappe.db.commit()
#                 return doc.name
            
#             def create_related_doc_pd(doctype):
#                 doc = frappe.new_doc(doctype)
#                 doc.vendor_onboarding = vendor_onboarding.name
#                 doc.ref_no = vendor_master.name
#                 doc.country = data.get("country")
#                 doc.registered_for_multi_companies = 1
#                 doc.unique_multi_comp_id = unique_multi_comp_id
#                 doc.save()
#                 frappe.db.commit()
#                 return doc.name


#             payment_detail = create_related_doc_pd("Vendor Onboarding Payment Details")
#             payment_detail_docs.append(payment_detail)
#             document_details = create_related_doc("Legal Documents")
#             document_details_docs.append(document_details)
#             certificate_details = create_related_doc("Vendor Onboarding Certificates")
#             certificate_details_docs.append(certificate_details)
#             manufacturing_details = create_related_doc("Vendor Onboarding Manufacturing Details")
#             manufacturing_details_docs.append(manufacturing_details)
#             company_details = create_related_doc_company("Vendor Onboarding Company Details")
#             company_details_docs.append(company_details)

#             if company_details:
#                 vendor_onb_company = frappe.get_doc("Vendor Onboarding Company Details", company_details)

#                 for field in ["vendor_title", "vendor_name",]:
#                     if field in data:
#                         vendor_onb_company.set(field, data[field])
#                 vendor_onb_company.company_name = mc.company_name

#                 vendor_onb_company.save()

#             # Add vendor_company_details in child table
#             vendor_onboarding.append("vendor_company_details", {
#                 "vendor_company_details": company_details 
#             })

#             # Update vendor onboarding with doc names
#             vendor_onboarding.payment_detail = payment_detail
#             vendor_onboarding.document_details = document_details
#             vendor_onboarding.certificate_details = certificate_details
#             vendor_onboarding.manufacturing_details = manufacturing_details
            
#             vendor_onboarding.save()
#             # send_registration_email_link(vendor_onboarding.name, vendor_master.name)
#             frappe.db.commit()
        

#         send_registration_email_link(vendor_onboarding_docs[0], vendor_master.name)
#         return {
#             "status": "success",
#             "vendor_master": vendor_master.name,
#             "vendor_onboarding": vendor_onboarding_docs,
#             "payment_detail": payment_detail_docs,
#             "document_details": document_details_docs,
#             "certificate_details": certificate_details_docs,
#             "manufacturing_details": manufacturing_details_docs,
#             "company_details": company_details_docs
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Vendor Registration Full Flow Error")
#         return {
#             "status": "error",
#             "message": "Vendor registration failed",
#             "error": str(e)
#         }








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
                for existing in vendor_onboarding.vendor_types:
                    if (existing.vendor_type or "").lower().strip() == (row.get("vendor_type") or "").lower().strip():
                        is_duplicate = True
                        break

                if not is_duplicate:
                    vendor_onboarding.append("vendor_types", row)

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
                subject=f"""New Vendor Appointment for {onboarding_doc.company_name}-{vendor_master.vendor_name}-VMS Ref {vendor_master.name}""",
                message=f"""
                    <p>Dear Sir/Madam,</p>
                    <p>Greetings for the Day!</p>
                    <p>You have been added by {frappe.db.get_value("User", onboarding_doc.registered_by, "full_name")} to Onboard as a Vendor/Supplier for {onboarding_doc.company_name}.</p>
                    <p> Founded in 2006, Meril Life Sciences Pvt. Ltd. is a global medtech company based in India, dedicated to designing and manufacturing innovative, 
                    patient-centric medical devices. We focus on advancing healthcare through cutting-edge R&D, quality manufacturing, and clinical excellence 
                    to help people live longer, healthier lives. We are a family of 3000+ Vendors/Sub – Vendors across India. </p>
                    <p>Please click here to fill details!</p>
                    <p style="margin: 15px 0px;">
                        <a href="{registration_link}" rel="nofollow" class="btn btn-primary">Complete Registration</a>
                    </p>
                    <p>You may also copy and paste this link into your browser:<br>
                    <a href="{registration_link}">{registration_link}</a></p>

                    {qms_section}

                    <p>Thanking you,<br>VMS Team</p>
                """,
                delayed=False
            )

            onboarding_doc.sent_registration_email_link = 1
            onboarding_doc.sent_qms_form_link =1
            if onboarding_doc.registered_for_multi_companies == 1:
                onboarding_doc.head_target = 1
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
    




import json
import frappe
from datetime import datetime
from frappe import _

@frappe.whitelist(allow_guest=True)
def vendor_registration_multi(data):
    """
    Enhanced vendor registration API with comprehensive error handling
    """
    vendor_master = None
    vendor_onboarding_docs = []
    
    try:
        # Input validation and parsing
        if not data:
            return {
                "status": "error",
                "message": _("No data provided"),
                "error_code": "NO_DATA"
            }
            
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "message": _("Invalid JSON format"),
                    "error": str(e),
                    "error_code": "INVALID_JSON"
                }
        
        # Validate required fields
        required_fields = ["vendor_name", "office_email_primary"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return {
                "status": "error",
                "message": _("Missing required fields: {0}").format(", ".join(missing_fields)),
                "error_code": "MISSING_FIELDS"
            }
        
        # Validate email format
        if not frappe.utils.validate_email_address(data.get("office_email_primary")):
            return {
                "status": "error",
                "message": _("Invalid email format"),
                "error_code": "INVALID_EMAIL"
            }
        
        # Validate purchase_details
        if not data.get("purchase_details") or not isinstance(data["purchase_details"], list):
            return {
                "status": "error",
                "message": _("Purchase details are required and must be a list"),
                "error_code": "INVALID_PURCHASE_DETAILS"
            }

        # Check if vendor with the given email already exists
        vendor_master = None
        if data.get("office_email_primary"):
            try:
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
            except frappe.DoesNotExistError:
                vendor_master = frappe.new_doc("Vendor Master")
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Error checking existing vendor")
                return {
                    "status": "error",
                    "message": _("Error checking existing vendor data"),
                    "error": str(e),
                    "error_code": "VENDOR_CHECK_ERROR"
                }
        else:
            vendor_master = frappe.new_doc("Vendor Master")

        # Set vendor master fields with validation
        vendor_fields = [
            "vendor_title", "vendor_name", "office_email_primary", "search_term",
            "country", "mobile_number", "registered_date", "qa_required"
        ]
        
        for field in vendor_fields:
            if field in data and data[field] is not None:
                vendor_master.set(field, data[field])

        # Set default values
        vendor_master.payee_in_document = 1
        vendor_master.gr_based_inv_ver = 1
        vendor_master.service_based_inv_ver = 1
        vendor_master.check_double_invoice = 1
        vendor_master.created_from_registration = 1
        vendor_master.registered_by = frappe.session.user

        # Update child tables with duplicate checking
        if "multiple_company_data" in data and isinstance(data["multiple_company_data"], list):
            for row in data["multiple_company_data"]:
                if not isinstance(row, dict):
                    continue
                    
                is_duplicate = any(
                    (existing.company_name or "").lower().strip() == (row.get("company_name") or "").lower().strip() and
                    (existing.purchase_organization or "").lower().strip() == (row.get("purchase_organization") or "").lower().strip() and
                    (existing.account_group or "").lower().strip() == (row.get("account_group") or "").lower().strip() and
                    (existing.purchase_group or "").lower().strip() == (row.get("purchase_group") or "").lower().strip()
                    for existing in vendor_master.multiple_company_data
                )
                
                if not is_duplicate:
                    vendor_master.append("multiple_company_data", row)

        if "vendor_types" in data and isinstance(data["vendor_types"], list):
            for row in data["vendor_types"]:
                if not isinstance(row, dict):
                    continue
                    
                is_duplicate = any(
                    (existing.vendor_type or "").lower().strip() == (row.get("vendor_type") or "").lower().strip()
                    for existing in vendor_master.vendor_types
                )
                
                if not is_duplicate:
                    vendor_master.append("vendor_types", row)

        # Save vendor master
        try:
            vendor_master.save(ignore_permissions=True)
            frappe.db.commit()
        except frappe.ValidationError as e:
            frappe.db.rollback()
            return {
                "status": "error",
                "message": _("Vendor master validation failed: {0}").format(str(e)),
                "error_code": "VENDOR_VALIDATION_ERROR"
            }
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), "Error saving vendor master")
            return {
                "status": "error",
                "message": _("Failed to save vendor master"),
                "error": str(e),
                "error_code": "VENDOR_SAVE_ERROR"
            }

        # Generate unique ID
        try:
            now = datetime.now()
            year_month_prefix = f"MCD{now.strftime('%y')}{now.strftime('%m')}"
            
            existing_max = frappe.db.sql(
                """
                SELECT MAX(CAST(SUBSTRING(unique_multi_comp_id, 8) AS UNSIGNED))
                FROM `tabVendor Onboarding`
                WHERE unique_multi_comp_id LIKE %s
                """,
                (year_month_prefix + "%",),
                as_list=True
            )
            
            max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
            new_count = max_count + 1
            unique_multi_comp_id = f"{year_month_prefix}{str(new_count).zfill(5)}"
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error generating unique ID")
            return {
                "status": "error",
                "message": _("Failed to generate unique ID"),
                "error": str(e),
                "error_code": "ID_GENERATION_ERROR"
            }

        # Create vendor onboarding documents
        payment_detail_docs = []
        document_details_docs = []
        certificate_details_docs = []
        manufacturing_details_docs = []
        company_details_docs = []
        
        multi_companies = data.get("purchase_details", [])
        
        for mc in multi_companies:
            if not isinstance(mc, dict):
                continue
                
            try:
                # Create vendor onboarding
                vendor_onboarding = frappe.new_doc("Vendor Onboarding")
                vendor_onboarding.ref_no = vendor_master.name
                vendor_onboarding.registered_for_multi_companies = 1
                vendor_onboarding.unique_multi_comp_id = unique_multi_comp_id
                vendor_onboarding.registered_by = frappe.session.user

                # Set optional fields
                for field in ["qms_required", "incoterms"]:
                    if field in data and data[field] is not None:
                        vendor_onboarding.set(field, data[field])

                # Set default values
                vendor_onboarding.payee_in_document = 1
                vendor_onboarding.gr_based_inv_ver = 1
                vendor_onboarding.service_based_inv_ver = 1
                vendor_onboarding.check_double_invoice = 1
                
                # Set company-specific fields with validation
                company_fields = [
                    "company_name", "purchase_organization", "account_group", 
                    "purchase_group", "terms_of_payment", "order_currency", "reconciliation_account"
                ]
                
                for field in company_fields:
                    if hasattr(mc, field):
                        vendor_onboarding.set(field, getattr(mc, field))
                    elif isinstance(mc, dict) and field in mc:
                        vendor_onboarding.set(field, mc[field])

                # Add multiple company data
                for company in multi_companies:
                    if isinstance(company, dict) and company.get("company_name"):
                        vendor_onboarding.append("multiple_company", {
                            "company": company.get("company_name")
                        })
                    elif hasattr(company, 'company_name'):
                        vendor_onboarding.append("multiple_company", {
                            "company": company.company_name
                        })

                # Add vendor types (avoiding duplicates)
                if "vendor_types" in data and isinstance(data["vendor_types"], list):
                    for row in data["vendor_types"]:
                        if not isinstance(row, dict):
                            continue
                            
                        is_duplicate = any(
                            (existing.vendor_type or "").lower().strip() == (row.get("vendor_type") or "").lower().strip()
                            for existing in vendor_onboarding.get("vendor_types", [])
                        )
                        
                        if not is_duplicate:
                            vendor_onboarding.append("vendor_types", row)

                vendor_onboarding.save()
                frappe.db.commit()
                vendor_onboarding_docs.append(vendor_onboarding.name)

                # Helper functions for creating related documents
                def create_related_doc(doctype, additional_fields=None):
                    try:
                        doc = frappe.new_doc(doctype)
                        doc.vendor_onboarding = vendor_onboarding.name
                        doc.ref_no = vendor_master.name
                        doc.registered_for_multi_companies = 1
                        doc.unique_multi_comp_id = unique_multi_comp_id
                        
                        if additional_fields:
                            for field, value in additional_fields.items():
                                if value is not None:
                                    doc.set(field, value)
                        
                        doc.save()
                        frappe.db.commit()
                        return doc.name
                    except Exception as e:
                        frappe.log_error(frappe.get_traceback(), f"Error creating {doctype}")
                        raise e

                # Create related documents
                payment_detail = create_related_doc(
                    "Vendor Onboarding Payment Details",
                    {"country": data.get("country")}
                )
                payment_detail_docs.append(payment_detail)
                
                document_details = create_related_doc("Legal Documents")
                document_details_docs.append(document_details)
                
                certificate_details = create_related_doc("Vendor Onboarding Certificates")
                certificate_details_docs.append(certificate_details)
                
                manufacturing_details = create_related_doc("Vendor Onboarding Manufacturing Details")
                manufacturing_details_docs.append(manufacturing_details)
                
                company_details = create_related_doc(
                    "Vendor Onboarding Company Details",
                    {
                        "office_email_primary": vendor_master.office_email_primary,
                        "telephone_number": vendor_master.mobile_number
                    }
                )
                company_details_docs.append(company_details)

                # Update company details with vendor info
                if company_details:
                    try:
                        vendor_onb_company = frappe.get_doc("Vendor Onboarding Company Details", company_details)
                        
                        for field in ["vendor_title", "vendor_name"]:
                            if field in data and data[field] is not None:
                                vendor_onb_company.set(field, data[field])
                        
                        if hasattr(mc, 'company_name'):
                            vendor_onb_company.company_name = mc.company_name
                        elif isinstance(mc, dict) and mc.get("company_name"):
                            vendor_onb_company.company_name = mc["company_name"]
                        
                        vendor_onb_company.save()
                        frappe.db.commit()
                    except Exception as e:
                        frappe.log_error(frappe.get_traceback(), "Error updating company details")

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
                
            except Exception as e:
                frappe.db.rollback()
                frappe.log_error(frappe.get_traceback(), f"Error creating vendor onboarding for company {mc}")
                return {
                    "status": "error",
                    "message": _("Failed to create vendor onboarding"),
                    "error": str(e),
                    "error_code": "ONBOARDING_CREATION_ERROR"
                }

        # Send registration email (only if we have onboarding docs)
        if vendor_onboarding_docs:
            try:
                send_registration_email_link(vendor_onboarding_docs[0], vendor_master.name)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Error sending registration email")
                # Don't fail the entire process for email errors
                pass

        return {
            "status": "success",
            "message": _("Vendor registration completed successfully"),
            "vendor_master": vendor_master.name,
            "vendor_onboarding": vendor_onboarding_docs,
            "payment_detail": payment_detail_docs,
            "document_details": document_details_docs,
            "certificate_details": certificate_details_docs,
            "manufacturing_details": manufacturing_details_docs,
            "company_details": company_details_docs
        }

    except frappe.ValidationError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": _("Validation error: {0}").format(str(e)),
            "error_code": "VALIDATION_ERROR"
        }
    except frappe.DuplicateEntryError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": _("Duplicate entry error: {0}").format(str(e)),
            "error_code": "DUPLICATE_ERROR"
        }
    except frappe.PermissionError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": _("Permission denied: {0}").format(str(e)),
            "error_code": "PERMISSION_ERROR"
        }
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vendor Registration Full Flow Error")
        return {
            "status": "error",
            "message": _("Vendor registration failed"),
            "error": str(e),
            "error_code": "GENERAL_ERROR"
        }

