import frappe
import json
from frappe.utils.file_manager import save_file

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_payment_details(data):
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
            "Vendor Onboarding Payment Details",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            return {
                "status": "error",
                "message": "Vendor Onboarding Payment Details record not found."
            }

        doc = frappe.get_doc("Vendor Onboarding Payment Details", doc_name)

        # Update fields
        fields_to_update = [
            "bank_name", "ifsc_code", "account_number", "name_of_account_holder",
            "type_of_account", "currency", "rtgs", "neft"
        ]
        for field in fields_to_update:
            if field in data:
                doc.set(field, data[field])

        # Upload file to attach field
        if 'bank_proof' in frappe.request.files:
            file = frappe.request.files['bank_proof']
            saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
            doc.bank_proof = saved.file_url

        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Payment Details updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Payment Update Error")
        return {
            "status": "error",
            "message": "Failed to update payment details.",
            "error": str(e)
        }
