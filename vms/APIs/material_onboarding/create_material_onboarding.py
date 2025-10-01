import json
import frappe
from frappe import _
from frappe.utils import today
from vms.utils.custom_send_mail import custom_sendmail


#vms.APIs.material_onboarding.create_material_onboarding.create_material_onboarding
@frappe.whitelist()
def create_material_onboarding():
    try:
        # Check permissions
        if not frappe.has_permission("Material Onboarding", "create"):
            frappe.response.http_status_code = 403
            return {"message": "Failed", "error": "You don't have permission to create Material Onboarding"}

        # Get form data
        form_data = dict(frappe.form_dict)
        files = frappe.request.files
        
        # Handle file upload for material_information
        if files and "material_information" in files:
            file = files["material_information"]
            if file and getattr(file, "filename", None) and file.filename != "undefined":
                try:
                    file_doc = frappe.get_doc({
                        "doctype": "File",
                        "file_name": file.filename,
                        "content": file.read(),
                        "is_private": 1
                    })
                    file_doc.save()
                    form_data["material_information"] = file_doc.file_url
                except Exception as file_error:
                    frappe.log_error(
                        f"File upload failed: {str(file_error)}",
                        "Material Onboarding File Upload Error"
                    )

        # Get requestor reference
        req_name = form_data.get("requestor_ref_no") or form_data.get("requestor_name")
        if not req_name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Requestor reference (requestor_ref_no or requestor_name) is required"}

        # Check if requestor exists
        if not frappe.db.exists("Requestor Master", req_name):
            frappe.response.http_status_code = 404
            return {"message": "Failed", "error": f"Requestor Master '{req_name}' not found"}

        # Get requestor document
        requestor = frappe.get_doc("Requestor Master", req_name)

        # Check if this is a draft save
        save_as_draft = form_data.get("save_as_draft")
        if isinstance(save_as_draft, str):
            save_as_draft = save_as_draft.lower() in ['true', '1', 'yes']

        # Process Material Master and Material Onboarding
        material, onboarding = process_material_onboarding(
            form_data=form_data,
            requestor=requestor,
            save_as_draft=save_as_draft
        )

        # Update requestor with references
        requestor.material_master_ref_no = material.name
        requestor.material_onboarding_ref_no = onboarding.name
        
        # Set approval status based on draft flag
        if save_as_draft:
            requestor.approval_status = "Draft"
        else:
            if requestor.material_master_ref_no and requestor.material_onboarding_ref_no:
                # This is an update
                requestor.approval_status = "Updated by CP"
            else:
                # This is new
                requestor.approval_status = "Sent to SAP"
        
        requestor.save(ignore_permissions=True)
        frappe.db.commit()

        # Send email only if not draft
        if not save_as_draft:
            try:
                send_material_onboarding_email(onboarding.name)
            except Exception as email_error:
                frappe.log_error(
                    f"Email sending failed: {str(email_error)}",
                    "Material Onboarding Email Error"
                )
                

        return {
            "message": "Success",
            "data": {
                "material_master": material.name,
                "material_onboarding": onboarding.name,
                "requestor": requestor.name,
                "approval_status": requestor.approval_status,
                "is_draft": save_as_draft
            }
        }

    except frappe.ValidationError as e:
        frappe.db.rollback()
        frappe.response.http_status_code = 400
        frappe.log_error(frappe.get_traceback(), "Material Onboarding Validation Error")
        return {"message": "Failed", "error": str(e)}
    
    except frappe.PermissionError:
        frappe.db.rollback()
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.db.rollback()
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Material Onboarding Creation Error")
        return {"message": "Failed", "error": str(e)}


def process_material_onboarding(form_data, requestor, save_as_draft=False):
    # Add requestor reference to form data
    form_data["requestor_ref_no"] = requestor.name
    form_data["basic_data_ref_no"] = requestor.name

    # Check if Material Master exists
    if requestor.material_master_ref_no:
        # Update existing Material Master
        material = frappe.get_doc("Material Master", requestor.material_master_ref_no)
        set_doc_fields(material, form_data)
        material.save(ignore_permissions=True)
    else:
        # Create new Material Master
        material = frappe.new_doc("Material Master")
        set_doc_fields(material, form_data)
        material.insert(ignore_permissions=True)

    # Prepare onboarding data
    onboarding_data = form_data.copy()
    onboarding_data["material_master_ref_no"] = material.name
    onboarding_data["material_code_latest"] = form_data.get("material_code")
    
    # Set approval status
    if save_as_draft:
        onboarding_data["approval_status"] = "Draft"
    else:
        onboarding_data["approval_status"] = "Sent to SAP"

    # Check if Material Onboarding exists
    if requestor.material_onboarding_ref_no:
        # Update existing Material Onboarding
        onboarding = frappe.get_doc("Material Onboarding", requestor.material_onboarding_ref_no)
        set_doc_fields(onboarding, onboarding_data)
        onboarding.save(ignore_permissions=True)
    else:
        # Create new Material Onboarding
        onboarding = frappe.new_doc("Material Onboarding")
        set_doc_fields(onboarding, onboarding_data)
        onboarding.insert(ignore_permissions=True)

    # Link Material Master to Onboarding
    material.material_onboarding_ref_no = onboarding.name
    material.save(ignore_permissions=True)

    return material, onboarding


def set_doc_fields(doc, form_data):
    # Get document meta
    meta = frappe.get_meta(doc.doctype)
    
    # Special checkbox fields that need boolean conversion
    checkbox_fields = ["incoming_inspection_01", "incoming_inspection_09"]
    
    # Iterate through all fields in the doctype
    for field in meta.fields:
        field_name = field.fieldname
        
        # Skip if field not in form_data
        if field_name not in form_data:
            continue
        
        value = form_data.get(field_name)
        
        # Skip None values
        if value is None:
            continue
        
        # Handle checkbox fields
        if field_name in checkbox_fields:
            value = 1 if value in ["on", "1", 1, True, "true", "True"] else 0
        
        # Set the field value
        doc.set(field_name, value)


def send_material_onboarding_email(onboarding_name):
    try:
        # Get Material Onboarding document
        onboarding_doc = frappe.get_doc("Material Onboarding", onboarding_name)
        
        if not onboarding_doc.requestor_ref_no:
            frappe.log_error(
                "Requestor Reference Number is missing from Material Onboarding",
                "Material Onboarding Email Error"
            )
            return

        # Get requestor email
        requestor_email = frappe.db.get_value(
            "Requestor Master",
            onboarding_doc.requestor_ref_no,
            "contact_information_email"
        )
        
        if not requestor_email:
            frappe.log_error(
                "Requestor email not found",
                "Material Onboarding Email Error"
            )
            return

        # Get requestor details
        requestor_details = frappe.db.get_value(
            "Employee",
            {"user_id": requestor_email},
            ["full_name", "reports_to"],
            as_dict=True
        )
        
        if not requestor_details:
            frappe.log_error(
                f"Employee with email {requestor_email} not found",
                "Material Onboarding Email Error"
            )
            return

        # Get reporting manager details
        reporting_manager_details = None
        if requestor_details.get("reports_to"):
            reporting_manager_details = frappe.db.get_value(
                "Employee",
                requestor_details["reports_to"],
                ["user_id", "full_name"],
                as_dict=True
            )

        # Get CP employees
        cp_employees = frappe.get_all(
            "Employee",
            filters={"designation": "CP"},
            fields=["user_id"],
            pluck="user_id"
        )
        cp_emails = [user_id for user_id in cp_employees if user_id]

        # Prepare email recipients
        recipients = cp_emails if cp_emails else []
        cc_recipients = []
        
        if reporting_manager_details and reporting_manager_details.get("user_id"):
            cc_recipients.append(reporting_manager_details["user_id"])

        # Prepare email content
        manager_name = reporting_manager_details.get("full_name") if reporting_manager_details else "Team"
        requestor_name = requestor_details.get("full_name", "User")
        
        subject = "New Material Onboarding Request Submitted"
        message = f"""
            <p>Dear {manager_name},</p>
            <p>
                A new material onboarding request "<strong>{onboarding_name}</strong>" has been submitted 
                by <strong>{requestor_name}</strong> ({requestor_email}).
            </p>
            <p>Please review the request at your earliest convenience.</p>
            <p>Regards,<br>Meril VMS Team</p>
        """

        frappe.custom_sendmail(
            recipients=recipients,
            cc=cc_recipients,
            subject=subject,
            message=message,
            now=True
        )



    except Exception as e:
        frappe.log_error(
            f"Email notification error: {str(e)}\n{frappe.get_traceback()}",
            f"Material Onboarding Email Error - {onboarding_name}"
        )
        
     
       


