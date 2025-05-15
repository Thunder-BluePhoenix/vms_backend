import frappe
import json
from frappe.utils.file_manager import save_file

# update vendor onboarding document details
@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_document_details(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        ref_no = data.get("ref_no")
        vendor_onboarding = data.get("vendor_onboarding")

        if not ref_no or not vendor_onboarding:
            return {
                "status": "error",
                "message": "Both 'ref_no' and 'vendor_onboarding' are required."
            }

        doc_name = frappe.db.get_value(
            "Legal Documents",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            return {
                "status": "error",
                "message": "Legal Documents record not found."
            }

        doc = frappe.get_doc("Legal Documents", doc_name)

        # Update fields
        fields_to_update = [
            "company_pan_number", "name_on_company_pan",
            "msme_registered", "enterprise_registration_number", "entity_proof",
            "msme_enterprise_type", "udyam_number", "name_on_udyam_certificate"
        ]

        for field in fields_to_update:
            if field in data and data[field] is not None:
                doc.set(field, data[field])

        # Upload and attach files
        if 'msme_proof' in frappe.request.files:
            file = frappe.request.files['msme_proof']
            saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
            doc.msme_proof = saved.file_url

        if 'pan_proof' in frappe.request.files:
            file = frappe.request.files['pan_proof']
            saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
            doc.pan_proof = saved.file_url

        if 'entity_proof' in frappe.request.files:
            file = frappe.request.files['entity_proof']
            saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
            doc.entity_proof = saved.file_url

        # update child table
        if "gst_table" in data:
            index = 0
            for row in data["gst_table"]:
                gst_row = doc.append("gst_table", row)

                # gst_document file upload
                file_key = f"gst_document_{index}"
                if file_key in frappe.request.files:
                    file = frappe.request.files[file_key]
                    saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
                    gst_row.gst_document = saved.file_url

                index += 1

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Legal Documents updated successfully.",
            "docname": doc.name,
            "msme_proof": doc.msme_proof if hasattr(doc, "msme_proof") else None,
            "pan_proof": doc.pan_proof if hasattr(doc, "pan_proof") else None,
            "entity_proof": doc.entity_proof if hasattr(doc, "entity_proof") else None,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Legal Document Update Error")
        return {
            "status": "error",
            "message": "Failed to update Legal Documents.",
            "error": str(e)
        }