import frappe
import json
import uuid
import base64
from frappe import _

# @frappe.whitelist(allow_guest=True)
# def get_qms_details(vendor_onboarding):
#     try:
#         # Get Vendor Onboarding document
#         vn_onb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

#         # Get the linked QMS Assessment Form document
#         qms_doc = frappe.get_doc("Supplier QMS Assessment Form", {"unique_name":vn_onb.qms_form_link})

#         # Get meta for field labels
#         meta = frappe.get_meta("Supplier QMS Assessment Form")
#         qms_data = []

#         for field in meta.fields:
#             fieldname = field.fieldname
#             fieldlabel = field.label
#             if fieldname:
#                 value = qms_doc.get(fieldname)
#                 qms_data.append({
#                     "fieldname": fieldname,
#                     "fieldlabel": fieldlabel,
#                     "value": value
#                 })

#         return {
#             "qms_details": qms_data,
#             "qms_doc_name": qms_doc.name
#         }

#     except frappe.DoesNotExistError as e:
#         frappe.throw(_("Document not found: {0}").format(str(e)))
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_qms_details Error")
#         frappe.throw(_("An unexpected error occurred while fetching QMS details."))


@frappe.whitelist(allow_guest=True)
def get_qms_details(vendor_onboarding):
    try:
        # Get Vendor Onboarding document
        vn_onb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get the linked QMS Assessment Form document
        qms_doc = frappe.get_doc("Supplier QMS Assessment Form", {"unique_name": vn_onb.qms_form_link})

        # Get meta for field labels
        meta = frappe.get_meta("Supplier QMS Assessment Form")
        qms_data = []
        
        # Define table multiselect fields
        table_multiselect_fields = {
            "quality_control_system": {
                "child_doctype": "QMS Quality Control",
                "child_field": "qms_quality_control"
            },
            "details_of_batch_records": {
                "child_doctype": "QMS Batch Record Table",
                "child_field": "qms_batch_record"
            },
            "have_documentsprocedure": {
                "child_doctype": "QMS Procedure Doc",
                "child_field": "qms_procedure_doc"
            },
            "if_yes_for_prior_notification": {
                "child_doctype": "QMS Prior Notification Table",
                "child_field": "qms_prior_notification"
            }
        }

        for field in meta.fields:
            fieldname = field.fieldname
            fieldlabel = field.label
            fieldtype = field.fieldtype
            
            if fieldname:
                value = qms_doc.get(fieldname)
                
                # Handle table multiselect fields
                if fieldname in table_multiselect_fields and fieldtype == "Table":
                    child_config = table_multiselect_fields[fieldname]
                    child_records = []
                    
                    if value:  # value is a list of child documents
                        for child_doc in value:
                            child_field_name = child_config["child_field"]
                            child_value = child_doc.get(child_field_name)
                            if child_value:
                                child_records.append(child_value)
                    
                    qms_data.append({
                        "fieldname": fieldname,
                        "fieldlabel": fieldlabel,
                        "fieldtype": fieldtype,
                        "value": child_records,  # Array of values
                        "value_display": ", ".join(child_records) if child_records else "",  # Comma-separated display
                        "is_table_multiselect": True,
                        "child_doctype": child_config["child_doctype"],
                        "child_field": child_config["child_field"]
                    })
                else:
                    # Handle regular fields
                    qms_data.append({
                        "fieldname": fieldname,
                        "fieldlabel": fieldlabel,
                        "fieldtype": fieldtype,
                        "value": value,
                        "value_display": str(value) if value is not None else "",
                        "is_table_multiselect": False
                    })

        return {
            "qms_details": qms_data,
            "qms_doc_name": qms_doc.name,
            "table_multiselect_summary": get_table_multiselect_summary(qms_doc, table_multiselect_fields)
        }

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_qms_details Error")
        frappe.throw(_("An unexpected error occurred while fetching QMS details."))


def get_table_multiselect_summary(qms_doc, table_multiselect_fields):
    """
    Get a summary of table multiselect fields for easier access
    """
    summary = {}
    
    for field_name, config in table_multiselect_fields.items():
        child_records = qms_doc.get(field_name, [])
        child_field_name = config["child_field"]
        
        values = []
        for child_doc in child_records:
            child_value = child_doc.get(child_field_name)
            if child_value:
                values.append(child_value)
        
        summary[field_name] = {
            "values": values,
            "count": len(values),
            "display": ", ".join(values) if values else "No data",
            "child_doctype": config["child_doctype"]
        }
    
    return summary





@frappe.whitelist(allow_guest=True)
def get_qms_details_without_label(vendor_onboarding):
    try:
        # Get Vendor Onboarding document
        vn_onb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get the linked QMS Assessment Form document
        qms_doc = frappe.get_doc("Supplier QMS Assessment Form", {"unique_name":vn_onb.qms_form_link})
        vn_comp = frappe.get_doc("Company Master", vn_onb.company_name)
        comp_code = vn_comp.company_code

        

        return {
            "qms_details": qms_doc.as_dict(),
            "qms_doc_name": qms_doc.name,
            "onboarding_company_code": comp_code
        }

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_qms_details Error")
        frappe.throw(_("An unexpected error occurred while fetching QMS details."))


# QMS form Approval
@frappe.whitelist(allow_guest=True)
def approve_qms_form(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        if not data.get("name"):
            return {
                "status": "error",
                "message": "Missing QMS form name."
            }

        qms_form = frappe.get_doc("Supplier QMS Assessment Form", data.get("name"))

        qms_form.qms_form_status = data.get("qms_form_status") or ""
        qms_form.conclusion_by_meril = data.get("conclusion_by_meril") or ""
        qms_form.assessment_outcome = data.get("assessment_outcome") or ""
        qms_form.performer_name = data.get("performer_name") or ""
        qms_form.performer_title = data.get("performer_title") or ""
        qms_form.performent_date = data.get("performent_date") or ""
        
        qa_head_approved = data.get("qa_head_approved") or ""
        if qa_head_approved == 1:
            qms_form.qa_head_approved = 1

        qa_team_approved = data.get("qa_team_approved") or ""
        if qa_team_approved == 1:
            qms_form.qa_team_approved = 1

        purchase_team_approved = data.get("purchase_team_approved") or ""
        if purchase_team_approved == 1:
            qms_form.purchase_team_approved = 1

        base64_signature = data.get("performer_esignature")
        if base64_signature:
            file_name = f"{uuid.uuid4()}.png"
            file_content = base64.b64decode(base64_signature.split(",")[-1])
            _file = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "content": file_content,
                "is_private": 0
            })
            _file.save(ignore_permissions=True)
            qms_form.performer_esignature = base64_signature
            qms_form.performer_signature = _file.file_url

        qms_form.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "QMS form approved successfully."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "QMS Approval Error")
        return {
            "status": "error",
            "message": "Failed to approve QMS form.",
            "error": str(e)
        }


# Verify the Employee and Send the Encrypted Signature Image
from cryptography.fernet import Fernet
import base64
import hashlib

def encrypt_with_temp_key(data: bytes):
    """
    Generate a one-time temporary Fernet key (valid for only 1 API response)
    and encrypt the image bytes with it.
    """
    temp_key = Fernet.generate_key()
    f = Fernet(temp_key)

    encrypted = f.encrypt(data)

    return encrypted.decode(), temp_key.decode()


def err(code, msg):
    frappe.local.response["http_status_code"] = code
    return {"status": "error", "message": msg}


@frappe.whitelist(allow_guest=False, methods='GET')
def send_signature_image(user_id=None, esign_passkey=None):
    try:
        if not user_id or not esign_passkey:
            return err(400, "user_id or esign_passkey is missing")

        employee = frappe.db.get_value(
            "Employee",
            {"user_id": user_id},
            ["name", "full_name", "esign_passkey", "sign_attach"],
            as_dict=True
        )

        if not employee:
            return err(404, "Employee not found for this User ID")
        

        if not employee.esign_passkey:
            return err(400, f"esign_passkey is not set for Employee {employee.full_name}")
        

        if esign_passkey != employee.esign_passkey:
            return err(400, "Incorrect esign_passkey")


        if not employee.sign_attach:
            return err(404, "No signature image uploaded")


        file_path = frappe.get_site_path("public", employee.sign_attach.lstrip("/"))

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        encrypted_image, temp_key = encrypt_with_temp_key(file_bytes)

        return {
            "status": "success",
            "message": "Signature retrieved successfully",
            "employee_name": employee.full_name,
            "encrypted_image": encrypted_image,
            "token_key": temp_key
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Signature API Error")
        return err(500, str(e))



# @frappe.whitelist(allow_guest=False, methods='GET')
# def send_signature_image(user_id=None, esign_passkey=None):
#     try:
#         if not user_id:
#             frappe.local.response["http_status_code"] = 404
#             return {"status": "error", "message": "user_id not provided"}

#         employee = frappe.db.get_value(
#             "Employee",
#             {"user_id": user_id},
#             ["name", "full_name", "esign_passkey", "sign_attach"],
#             as_dict=True
#         )

#         if not employee:
#             frappe.local.response["http_status_code"] = 404
#             return {"status": "error", "message": "Employee not found"}

#         if not esign_passkey:
#             frappe.local.response["http_status_code"] = 400
#             return {"status": "error", "message": "esign_passkey not provided"}

#         if esign_passkey != employee.esign_passkey:
#             frappe.local.response["http_status_code"] = 400
#             return {"status": "error", "message": "Incorrect esign_passkey"}

#         if not employee.sign_attach:
#             frappe.local.response["http_status_code"] = 404
#             return {"status": "error", "message": "No signature image uploaded"}

#         # Get file
#         file_path = frappe.get_site_path("public", employee.sign_attach.lstrip("/"))
#         with open(file_path, "rb") as f:
#             file_bytes = f.read()

#         # NEW: Encrypt using temporary 1-time key
#         encrypted_image, temp_key = encrypt_with_temp_key(file_bytes)

#         return {
#             "status": "success",
#             "message": "Signature retrieved successfully",
#             "employee_name": employee.full_name,

#             # Encrypted image
#             "encrypted_image": encrypted_image,

#             # Send temporary Fernet key to frontend for decryption
#             "token_key": temp_key,

#             # Optional — for security monitoring
#             "expires_in": 60
#         }

#     except Exception as e:
#         frappe.local.response["http_status_code"] = 500
#         frappe.log_error(frappe.get_traceback(), "Signature API Error")
#         return {"status": "error", "message": str(e)}
