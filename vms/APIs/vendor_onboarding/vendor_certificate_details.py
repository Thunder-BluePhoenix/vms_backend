import frappe
import json
from frappe.utils.file_manager import save_file

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_certificate_details(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        ref_no = data.get("ref_no")
        vendor_onboarding = data.get("vendor_onboarding")

        if not ref_no or not vendor_onboarding:
            return {
                "status": "error",
                "message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
            }

        doc_name = frappe.db.get_value(
            "Vendor Onboarding Certificates",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            return {
                "status": "error",
                "message": "Vendor Onboarding Certificates Record not found."
            }

        doc = frappe.get_doc("Vendor Onboarding Certificates", doc_name)

        # update child table
        if "certificates" in data:
            index = 0
            for row in data["certificates"]:
                material_row = doc.append("certificates", row)

                file_key = f"certificate_attach{index}"
                if file_key in frappe.request.files:
                    file = frappe.request.files[file_key]
                    saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
                    material_row.material_images = saved.file_url

                index += 1
        else:
            return {
                "status": "error",
                "message": "Missing fields: 'certificates Table'."
            } 

        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Certificates updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Certificates Update Error")
        return {
            "status": "error",
            "message": "Failed to update Vendor Onboarding Certificates.",
            "error": str(e)
        }
