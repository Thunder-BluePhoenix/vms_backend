import frappe
from frappe import _
from frappe.model.document import Document
from urllib.parse import urlencode
import json
from datetime import datetime
from vms.utils.custom_send_mail import custom_sendmail
import time

from vms.APIs.vendor_onboarding.vendor_registration_helper import populate_vendor_data_from_existing_onboarding
from vms.APIs.vendor_onboarding.vendor_reg_mail import send_registration_email_link_v2






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
            "incoterms2", "qms_required", "registered_by", "purchase_team_approval",
            "purchase_team_second", "purchase_head_approval", "purchase_head_second_approval",
            "qa_team_approval", "qa_head_approval", "accounts_team_approval",
            "accounts_team_second_approval", "status", "onboarding_form_status",
            "onboarding_ref_no"
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
        frappe.local.response["http_status_code"] = 500
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
        result = vendor_registration_single(data)

    else:
        result = vendor_registration_multi(data)

    return result


@frappe.whitelist(allow_guest=True)
def extended_vendor_registration(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        # Check if vendor already exists and has onboarding records
        email = data.get("office_email_primary")
        if email:
            # Check if vendor master exists
            vendor_master = frappe.get_all(
                "Vendor Master",
                filters={"office_email_primary": email},
                fields=["name", "vendor_name", "vendor_title"],
                limit=1
            )
            
            if vendor_master:
                vendor_master_doc = vendor_master[0]
                vendor_name = vendor_master_doc.get("vendor_name") or vendor_master_doc.get("vendor_title")
                
                # Get onboarding records for this vendor
                onboarding_records = frappe.get_all(
                    "Vendor Onboarding",
                    filters={"ref_no": vendor_master_doc["name"]},
                    fields=[
                        "name", "company_name", "onboarding_form_status", "docstatus", 
                        "registered_by", "owner", "creation"
                    ],
                    order_by="creation desc"
                )
                
                if onboarding_records:
                    # Check for company-specific conflicts
                    company_name = data.get("company_name")
                    purchase_details = data.get("purchase_details", [])
                    
                    # Get requested companies
                    requested_companies = []
                    if company_name:
                        requested_companies.append(company_name)
                    
                    for detail in purchase_details:
                        comp_name = None
                        if isinstance(detail, dict):
                            comp_name = detail.get("company_name")
                        elif hasattr(detail, 'company_name'):
                            comp_name = detail.company_name
                        
                        if comp_name and comp_name not in requested_companies:
                            requested_companies.append(comp_name)
                    
                    # Check for existing onboarding for requested companies
                    conflicting_records = []
                    for record in onboarding_records:
                        if record.get("company_name") in requested_companies:
                            onboarding_status = record.get("onboarding_form_status", "").lower()
                            
                            # Only consider active/approved records as conflicts
                            if onboarding_status in ["approved"] :
                                status = "already_onboarded"
                            elif onboarding_status in ["pending",]:
                                status = "in_process"
                            else:
                                continue  
                            
                            # Get raised by name
                            raised_by = record.get("registered_by") or record.get("owner")
                            raised_by_name = raised_by
                            if raised_by:
                                user_doc = frappe.get_value("User", raised_by, ["full_name", "first_name"], as_dict=True)
                                if user_doc:
                                    raised_by_name = user_doc.get("full_name") or user_doc.get("first_name") or raised_by
                            
                            conflicting_records.append({
                                "company_name": record.get("company_name"),
                                "status": status,
                                "onboarding_id": record.get("name"),
                                "raised_by_name": raised_by_name
                            })
                    
                    # If conflicts found, return appropriate response
                    if conflicting_records:
                        if len(conflicting_records) == 1:
                            record = conflicting_records[0]
                            if record["status"] == "already_onboarded":
                                message = f"Vendor '{vendor_name}' is already onboarded for company '{record['company_name']}'. The onboarding was completed by {record['raised_by_name']}."
                            else:
                                message = f"Vendor '{vendor_name}' onboarding for company '{record['company_name']}' is currently in process. The registration was initiated by {record['raised_by_name']}."
                        else:
                            onboarded_companies = [r["company_name"] for r in conflicting_records if r["status"] == "already_onboarded"]
                            in_process_companies = [r["company_name"] for r in conflicting_records if r["status"] == "in_process"]
                            
                            message_parts = [f"Vendor '{vendor_name}' has existing onboarding records:"]
                            if onboarded_companies:
                                message_parts.append(f"Already onboarded: {', '.join(onboarded_companies)}")
                            if in_process_companies:
                                message_parts.append(f"In process: {', '.join(in_process_companies)}")
                            
                            message = " ".join(message_parts)
                        
                        return {
                            "status": "duplicate",
                            "message": message,
                            "vendor_details": {
                                "vendor_master_id": vendor_master_doc["name"],
                                "vendor_name": vendor_name,
                                "office_email_primary": email
                            },
                            "conflicting_records": conflicting_records
                        }
        
        # No conflicts found, proceed with normal registration
        multi_companies = data.get("for_multiple_company")
        if multi_companies != 1:
            result = vendor_registration_single(data)
        else:
            result = vendor_registration_multi(data)
        
        return result
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Extended Vendor Registration Error")
        return {
            "status": "error",
            "message": "Extended vendor registration failed",
            "error": str(e)
        }





# check for existing vendor email and create vendor master, vendor onboarding & related link documents
@frappe.whitelist(allow_guest=True)
def vendor_registration_single(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)


        # Validate QMS requirement
        if data.get("qms_required") == "Yes":
            company_name = data.get("company_name")
            if company_name:
                # Check if company exists and has qms_required enabled
                company_qms = frappe.db.get_value("Company Master", company_name, "qms_required")
                
                if company_qms != 1:
                    return {
                                "status": "error",
                                "message": _(f"QMS is required for this vendor but Company '{company_name}' does not have QMS enabled. Please enable QMS in Company Master or change the QMS requirement."),
                                "error_code": "QMS_VALIDATION_ERROR"
                            }

        vendor_master = None

        # Check if vendor with the given email already exists
        # if data.get("office_email_primary"):
        #     exists = frappe.get_all(
        #         "Vendor Master",
        #         filters={"office_email_primary": data["office_email_primary"]},
        #         fields=["name"],
        #         limit=1
        #     )

        #     if exists:
        #         vendor_master = frappe.get_doc("Vendor Master", exists[0]["name"])
        #     else:
        #         vendor_master = frappe.new_doc("Vendor Master")
        # else:
        #     vendor_master = frappe.new_doc("Vendor Master")
        if data.get("office_email_primary"):
            exists = frappe.get_all(
                "Vendor Master",
                filters={"office_email_primary": data["office_email_primary"]},
                fields=["name"],
                limit=1
            )

            if exists:
                vendor_master = frappe.get_doc("Vendor Master", exists[0]["name"])
                
                # NEW: Check for existing vendor onboarding with same vendor master and company name
                if data.get("company_name"):
                    existing_onboarding = frappe.get_all(
                        "Vendor Onboarding",
                        filters={
                            "ref_no": vendor_master.name,
                            "company_name": data["company_name"]
                        },
                        fields=["name", "owner", "creation"],
                        order_by="creation desc",
                        limit=1
                    )
                    
                    if existing_onboarding:
                        onboarding_doc = existing_onboarding[0]
                        return {
                            "status": "duplicate",
                            "message": f"A vendor onboarding record already exists for this vendor ({vendor_master.vendor_name}) with company '{data['company_name']}'. Please use the existing record or contact the administrator if you need to create a new one.",
                            "existing_onboarding": {
                                "onboarding_id": onboarding_doc["name"],
                                "owner": onboarding_doc["owner"],
                                "office_email_primary": vendor_master.office_email_primary,
                                "created_on": onboarding_doc["creation"]
                            }
                        }
            else:
                vendor_master = frappe.new_doc("Vendor Master")
        else:
            vendor_master = frappe.new_doc("Vendor Master")

        # vendor master fields
        for field in [
            "vendor_title", "vendor_name", "office_email_primary", "search_term",
            "country", "mobile_number", "registered_date", "qms_required"
        ]:
            if field in data:
                vendor_master.set(field, data[field])
        vendor_master.via_data_import = 0
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
        
        # check for session user is belongs to the accounts team
        usr = frappe.session.user
        employee = frappe.get_value(
            "Employee",
            {"user_id": usr},
            ["name", "designation"],
            as_dict=True
        )
        if employee and employee.designation == "Accounts Team":
            vendor_onboarding.register_by_account_team = 1

        vendor_onboarding.ref_no = vendor_master.name

        for field in [
            "qms_required", "company_name", "purchase_organization", "account_group",
            "purchase_group", "terms_of_payment", "order_currency", "incoterms", "reconciliation_account"
        ]:
            if field in data:
                vendor_onboarding.set(field, data[field])

        # # Validate QMS requirement
        # if data.get("qms_required") == "Yes":
        #     company_name = data.get("company_name")
        #     if company_name:
        #         # Check if company exists and has qms_required enabled
        #         company_qms = frappe.db.get_value("Company Master", company_name, "qms_required")
                
        #         if company_qms != 1:
        #             frappe.throw(
        #                 f"QMS is required for this vendor but Company '{company_name}' does not have QMS enabled. "
        #                 "Please enable QMS in Company Master or change the QMS requirement.",
        #                 title="QMS Validation Error"
        #             )

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

        # vendor_master.onboarding_ref_no = vendor_onboarding.name
        # vendor_master.save()
        # frappe.db.commit
        vendor_master.db_set('onboarding_ref_no', vendor_onboarding.name, update_modified=False)

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
        # send_registration_email_link(vendor_onboarding.name, vendor_master.name)
        send_registration_email_link_v2(vendor_onboarding.name, vendor_master.name)
        frappe.db.commit()


        population_result = populate_vendor_data_from_existing_onboarding(
            vendor_master.name, 
            vendor_master.office_email_primary,
            vendor_onboarding.name
        )
        # vendor_master.onboarding_ref_no = vendor_onboarding.name
        # vendor_master.save()
        # frappe.db.commit

        return {
            "status": "success",
            "vendor_master": vendor_master.name,
            "vendor_onboarding": vendor_onboarding.name,
            "payment_detail": payment_detail,
            "document_details": document_details,
            "certificate_details": certificate_details,
            "manufacturing_details": manufacturing_details,
            "company_details": company_details,
            "population_result": population_result
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Registration Full Flow Error")
        return {
            "status": "error",
            "message": "Vendor registration failed",
            "error": str(e)
        }

# @frappe.whitelist(allow_guest = True)
# def update_vendor_master_doc(vendor_master):
#     frappe.enqueue(
#             method=vendor_master.populate_onboard_doc,
#             queue='default',
#             timeout=exp_d_sec,
#             now=False,
#             job_name=f'vendor_master_doc_update_{vendor_master.name}',
#             # enqueue_after_commit = False
#         )
        
        


# def populate_onboard_doc(vendor_master):
    

#     exp_t_sec = 5
#     time.sleep(exp_t_sec)
#     if vendor_master.form_fully_submitted_by_vendor == 0:
#         vendor_master.db_set('expired', 1, update_modified=False)
#         vendor_master.db_set('onboarding_form_status', "Expired", update_modified=False)

#     else:
#         pass

#     # exp_d_sec = exp_t_sec + 300
#     frappe.db.commit()



@frappe.whitelist(allow_guest=True)
def onboarding_form_submit(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        onb_ref = data.get('onb_id')

        onb = frappe.get_doc("Vendor Onboarding", onb_ref)

        if onb.registered_for_multi_companies == 1:
            linked_docs = frappe.get_all(
                "Vendor Onboarding",
                filters={
                    "registered_for_multi_companies": 1,
                    "unique_multi_comp_id": onb.unique_multi_comp_id
                },
                fields=["name"]
            )
        else:
            linked_docs = [{"name": onb.name}]

        for entry in linked_docs:
            doc = frappe.get_doc("Vendor Onboarding", entry["name"])
            doc.form_fully_submitted_by_vendor = data.get("completed")
            doc.save(ignore_permissions=True) 

        # onb.save()
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

        # Validate QMS requirement for each purchase detail
        for purchase_detail in data.get("purchase_details", []):
            if purchase_detail.get("qms_required") == "Yes":
                company_name = purchase_detail.get("company_name")
                
                if not company_name:
                    return {
                        "status": "error",
                        "message": _("Company name is required when QMS is enabled"),
                        "error_code": "MISSING_COMPANY_NAME"
                    }
                
                # Check if company exists and has qms_required enabled
                company_qms = frappe.db.get_value("Company Master", company_name, "qms_required")
                
                if not company_qms:
                    return {
                        "status": "error",
                        "message": _(f"Company '{company_name}' not found in Company Master"),
                        "error_code": "COMPANY_NOT_FOUND"
                    }
                
                if company_qms != 1:
                    return {
                        "status": "error",
                        "message": _(f"QMS is required for this vendor but Company '{company_name}' does not have QMS enabled. Please enable QMS in Company Master or change the QMS requirement."),
                        "error_code": "QMS_VALIDATION_ERROR"
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
                    
                    # NEW: Check for existing vendor onboarding with same vendor master and companies
                    duplicate_companies = []
                    
                    for purchase_detail in data.get("purchase_details", []):
                        company_name = None
                        
                        # Handle different company name structures
                        if isinstance(purchase_detail, dict):
                            company_name = purchase_detail.get("company_name")
                        elif hasattr(purchase_detail, 'company_name'):
                            company_name = purchase_detail.company_name
                            
                        if company_name:
                            existing_onboarding = frappe.get_all(
                                "Vendor Onboarding",
                                filters={
                                    "ref_no": vendor_master.name,
                                    "company_name": company_name
                                },
                                fields=["name", "owner", "creation", "company_name"],
                                order_by="creation desc",
                                limit=1
                            )
                            
                            if existing_onboarding:
                                duplicate_companies.append({
                                    "company_name": company_name,
                                    "onboarding_id": existing_onboarding[0]["name"],
                                    "owner": existing_onboarding[0]["owner"],
                                    "created_on": existing_onboarding[0]["creation"]
                                })
                    
                    # If duplicates found, return early with detailed information
                    if duplicate_companies:
                        company_names = [comp["company_name"] for comp in duplicate_companies]
                        
                        return {
                            "status": "duplicate",
                            "message": f"Vendor onboarding records already exist for vendor '{vendor_master.vendor_name or vendor_master.vendor_title}' with the following companies: {', '.join(company_names)}. Please use the existing records or contact the administrator if you need to create new ones.",
                            "existing_onboardings": duplicate_companies,
                            "vendor_details": {
                                "vendor_master_id": vendor_master.name,
                                "office_email_primary": vendor_master.office_email_primary,
                                "vendor_name": vendor_master.vendor_name or vendor_master.vendor_title
                            }
                        }
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
        vendor_master.via_data_import = 0
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

        # Update vendor_types in Vendor Master (across all purchase_details entries)
        all_vendor_types = set()

        for row in data.get("purchase_details", []):
            for vendor_type_entry in row.get("vendor_types", []):
                vt = (vendor_type_entry.get("vendor_type") or "").strip().lower()
                if vt:
                    all_vendor_types.add(vt)

        for vt in all_vendor_types:
            is_duplicate = any(
                (existing.vendor_type or "").strip().lower() == vt
                for existing in vendor_master.vendor_types
            )
            if not is_duplicate:
                vendor_master.append("vendor_types", {
                    "vendor_type": vt
                })

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

                # check for session user is belongs to the accounts team
                usr = frappe.session.user
                employee = frappe.get_value(
                    "Employee",
                    {"user_id": usr},
                    ["name", "designation"],
                    as_dict=True
                )
                if employee and employee.designation == "Accounts Team":
                    vendor_onboarding.register_by_account_team = 1

                vendor_onboarding.ref_no = vendor_master.name
                vendor_onboarding.registered_for_multi_companies = 1
                vendor_onboarding.unique_multi_comp_id = unique_multi_comp_id
                vendor_onboarding.registered_by = frappe.session.user

                # Set optional fields
                # for field in ["qms_required"]:
                #     if field in data and data[field] is not None:
                #         vendor_onboarding.set(field, data[field])

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
                    vendor_onboarding.incoterms = company.get("incoterms")
                    if isinstance(company, dict) and company.get("company_name"):
                        vendor_onboarding.append("multiple_company", {
                            "company": company.get("company_name"),
                            "qms_required": company.get("qms_required")
                        })
                    elif hasattr(company, 'company_name'):
                        vendor_onboarding.append("multiple_company", {
                            "company": company.company_name,
                            "qms_required": company.get("qms_required")
                        })

                # Add vendor types (avoiding duplicates)
                for vendor_type_entry in mc.get("vendor_types", []):
                    vt = (vendor_type_entry.get("vendor_type") or "").strip().lower()
                    if not vt:
                        continue

                    is_duplicate = any(
                        (existing.vendor_type or "").strip().lower() == vt
                        for existing in vendor_onboarding.vendor_types
                    )

                    if not is_duplicate:
                        vendor_onboarding.append("vendor_types", {
                            "vendor_type": vendor_type_entry.get("vendor_type")
                        })

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
                # frappe.db.commit()
                # vendor_master.db_set('onboarding_ref_no', vendor_onboarding.name, update_modified=False)
                
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
                # send_registration_email_link(vendor_onboarding_docs[0], vendor_master.name)
                send_registration_email_link_v2(vendor_onboarding_docs[0], vendor_master.name)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Error sending registration email")
                # Don't fail the entire process for email errors
                pass

            for vend_onb_doc in vendor_onboarding_docs:
                population_result = populate_vendor_data_from_existing_onboarding(
                    vendor_master.name, 
                    vendor_master.office_email_primary,
                    vend_onb_doc
                )

        return {
            "status": "success",
            "message": _("Vendor registration completed successfully"),
            "vendor_master": vendor_master.name,
            "vendor_onboarding": vendor_onboarding_docs,
            "payment_detail": payment_detail_docs,
            "document_details": document_details_docs,
            "certificate_details": certificate_details_docs,
            "manufacturing_details": manufacturing_details_docs,
            "company_details": company_details_docs,
            "population_result":population_result
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
    



# send registration email link
from urllib.parse import urlencode

@frappe.whitelist(allow_guest=True)
def send_registration_email_link(vendor_onboarding, refno):
    try:
        if not vendor_onboarding:
            return {
                "status": "error",
                "message": "Missing 'vendor_onboarding' parameter."
            }

        onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)
        vendor_master = frappe.get_doc("Vendor Master", onboarding_doc.ref_no)

        company_codes = []
        mul_docs = [] 

        if onboarding_doc.registered_for_multi_companies == 1:
            mul_docs = frappe.get_all(
                "Vendor Onboarding",
                filters={
                    "unique_multi_comp_id": onboarding_doc.unique_multi_comp_id,
                    "registered_for_multi_companies": 1
                },
                fields=["company_name", "qms_required"]
            )
            mul_company_names = [d["company_name"] for d in mul_docs if d.get("company_name")]

            company_names = []
            for name in mul_company_names:
                if frappe.db.exists("Company Master", name):
                    comp = frappe.db.get_value("Company Master", name, ["company_name", "company_code"], as_dict=True)
                    if comp:
                        company_names.append(comp.company_name)
                        company_codes.append(comp.company_code)

            company_names = ", ".join(company_names)
        else:
            comp = frappe.db.get_value("Company Master", onboarding_doc.company_name, ["company_name", "company_code"], as_dict=True)
            company_names = comp.company_name if comp else ""
            company_codes = [comp.company_code] if comp else []

        # Construct registration link
        http_server = frappe.conf.get("frontend_http")
        registration_link = (
            f"{http_server}/vendor-details-form"
            f"?tabtype=Company%20Detail"
            f"&refno={refno}"
            f"&vendor_onboarding={vendor_onboarding}"
        )

        # Construct QMS form link if required
        # qms_section = ""
        # qms_mul_company_code = []

        # qms_mul_company_names = [d["company_name"] for d in mul_docs if d.get("company_name") and d.get("qms_required") == "Yes"]

        # for name in qms_mul_company_names:
        #     if frappe.db.exists("Company Master", name):
        #         comp = frappe.db.get_value("Company Master", name, ["company_code"], as_dict=True)
        #         if comp:
        #             qms_mul_company_code.append(comp.company_code)

        # if qms_mul_company_code:
        #     qms_company_code = qms_mul_company_code
        # else:
        #     comp = frappe.db.get_value("Company Master", onboarding_doc.company_name, ["company_code"], as_dict=True)
        #     qms_company_code = [comp.company_code] if comp else []

        qms_company_codes = []
        qms_section = ""

        if onboarding_doc.registered_for_multi_companies == 1:
            qms_mul_docs = frappe.get_all(
                "Vendor Onboarding",
                filters={
                    "unique_multi_comp_id": onboarding_doc.unique_multi_comp_id,
                    "registered_for_multi_companies": 1
                },
                fields=["company_name", "qms_required"]
            )

            # Collect only companies where QMS is required
            qms_company_names = [
                d["company_name"] for d in qms_mul_docs
                if d.get("company_name") and d.get("qms_required") == "Yes"
            ]

            for name in qms_company_names:
                if frappe.db.exists("Company Master", name):
                    comp = frappe.db.get_value(
                        "Company Master", name, ["company_name", "company_code"], as_dict=True
                    )
                    if comp:
                        qms_company_codes.append(comp.company_code)

            # Build QMS link only if some codes exist
            if qms_company_codes:
                query_params = urlencode({
                    "vendor_onboarding": onboarding_doc.name,
                    "ref_no": onboarding_doc.ref_no,
                    "company_code": ",".join(qms_company_codes)
                })

                webform_link = f"{http_server}/qms-form?tabtype=vendor_information&{query_params}"

                qms_section = f"""
                    <p>As part of your registration, please also complete the QMS Form at the link below:</p>
                    <p style="margin: 15px 0px;">
                        <a href="{webform_link}" 
                            rel="nofollow" 
                            style="display: inline-block; 
                                    padding: 8px 16px; 
                                    background-color: #6c757d; 
                                    color: white; 
                                    text-decoration: none; 
                                    border-radius: 4px; 
                                    border: none; 
                                    cursor: pointer;">
                                Fill QMS Form
                        </a>
                    </p>
                    <p>You may also copy and paste this link into your browser:<br>
                    <a href="{webform_link}">{webform_link}</a></p>
                """

        else:
            # Single company onboarding
            if onboarding_doc.qms_required == "Yes":
                comp = frappe.db.get_value(
                    "Company Master", onboarding_doc.company_name, ["company_name", "company_code"], as_dict=True
                )
                if comp:
                    qms_company_codes = [comp.company_code]

                    query_params = urlencode({
                        "vendor_onboarding": onboarding_doc.name,
                        "ref_no": onboarding_doc.ref_no,
                        "company_code": ",".join(qms_company_codes)
                    })

                    webform_link = f"{http_server}/qms-form?tabtype=vendor_information&{query_params}"

                    qms_section = f"""
                        <p>As part of your registration, please also complete the QMS Form at the link below:</p>
                        <p style="margin: 15px 0px;">
                             <a href="{webform_link}" 
                                rel="nofollow" 
                                style="display: inline-block; 
                                        padding: 8px 16px; 
                                        background-color: #6c757d; 
                                        color: white; 
                                        text-decoration: none; 
                                        border-radius: 4px; 
                                        border: none; 
                                        cursor: pointer;">
                                    Fill QMS Form
                            </a>
                        </p>
                        <p>You may also copy and paste this link into your browser:<br>
                        <a href="{webform_link}">{webform_link}</a></p>
                    """

        # if onboarding_doc.qms_required == "Yes":
        # query_params = urlencode({
        #     "vendor_onboarding": onboarding_doc.name,
        #     "ref_no": onboarding_doc.ref_no,
        #     # "mobile_number": vendor_master.mobile_number,
        #     "company_code": ",".join(qms_company_codes) 
        # })

        # http_backend_server = frappe.conf.get("backend_http")
        # # webform_link = f"{http_backend_server}/qms-webform/new?{query_params}"

        # webform_link = f"{http_server}/qms-form?tabtype=vendor_information&{query_params}"

        # qms_section = f"""
        #     <p>As part of your registration, please also complete the QMS Form at the link below:</p>
        #     <p style="margin: 15px 0px;">
        #         <a href="{webform_link}" rel="nofollow" class="btn btn-secondary">Fill QMS Form</a>
        #     </p>
        #     <p>You may also copy and paste this link into your browser:<br>
        #     <a href="{webform_link}">{webform_link}</a></p>
        # """

        # Send registration email only once
        if not onboarding_doc.sent_registration_email_link:
            vendor_master = frappe.get_doc("Vendor Master", refno)
            recipient_email = vendor_master.office_email_primary or vendor_master.office_email_secondary

            if not recipient_email:
                return {
                    "status": "error",
                    "message": "No recipient email found for the vendor."
                }

            frappe.custom_sendmail(
                recipients=[recipient_email], 
                cc=[onboarding_doc.registered_by],
                subject=f"""New Vendor Appointment for Meril Group -{vendor_master.vendor_name}-VMS Ref {vendor_master.name}""",
                message=f"""
                    <p>Dear Vendor,</p>
                    <p>Greetings for the Day!</p>
                    <p>You have been added by <strong>{frappe.db.get_value("User", onboarding_doc.registered_by, "full_name")}</strong> to Onboard as a Vendor/Supplier for <strong> {company_names}.</strong></p>
                    <p> Founded in 2006, Meril Group of Companies is a global MEDTECH company based in India, dedicated to designing and manufacturing innovative, 
                    patient-centric medical devices. We focus on advancing healthcare through cutting-edge R&D, quality manufacturing, and clinical excellence 
                    to help people live longer, healthier lives. We are a family of 3000+ Vendors/Sub – Vendors across India. </p>
                    <p>Please click here to fill details!</p>
                    <p style="margin: 15px 0px;">
                        <a href="{registration_link}" 
                        style="display: inline-block; 
                                padding: 10px 20px; 
                                background-color: #007bff; 
                                color: white; 
                                text-decoration: none; 
                                border-radius: 4px; 
                                font-weight: bold;
                                border: 1px solid #007bff;"
                        rel="nofollow">Complete Registration</a>
                    </p>
                    <p>You may also copy and paste this link into your browser:<br>
                    <a href="{registration_link}">{registration_link}</a></p>

                    {qms_section}

                    <p>Thanking you,<br>VMS Team</p>
                """,
                now=True
            )

            # handle for to mark the registration email link sent to vendor for single and multi doc

            # onboarding_doc.sent_registration_email_link = 1
            # if onboarding_doc.qms_required == "Yes":
            #     onboarding_doc.sent_qms_form_link = 1

            if onboarding_doc.registered_for_multi_companies == 1:
                linked_docs = frappe.get_all(
                    "Vendor Onboarding",
                    filters={
                        "registered_for_multi_companies": 1,
                        "unique_multi_comp_id": onboarding_doc.unique_multi_comp_id
                    },
                    fields=["name"]
                )
            else:
                linked_docs = [{"name": onboarding_doc.name}]

            for entry in linked_docs:
                doc = frappe.get_doc("Vendor Onboarding", entry["name"])
                # doc.sent_registration_email_link = 1
                doc.db_set('sent_registration_email_link', 1, update_modified=False)

                if doc.qms_required == "Yes":
                    # doc.sent_qms_form_link = 1
                    doc.db_set('sent_qms_form_link', 1, update_modified=False)

                doc.save(ignore_permissions=True)


            if onboarding_doc.registered_for_multi_companies == 1:
                onboarding_doc.db_set('head_target', 1, update_modified=False)
                # onboarding_doc.head_target = 1
                
                vendor_master.db_set('onboarding_ref_no', onboarding_doc.name, update_modified=False)

            # onboarding_doc.save(ignore_permissions=True)
            # frappe.db.commit()

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
#             "country", "mobile_number", "registered_date", "qms_required"
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



