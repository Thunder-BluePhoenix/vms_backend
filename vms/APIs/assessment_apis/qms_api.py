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

