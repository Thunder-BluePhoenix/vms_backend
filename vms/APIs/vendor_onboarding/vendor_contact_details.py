import frappe
import json

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_contact_details(data):
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

        doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Update contact details table
        if "contact_details" in data:
            contact = data["contact_details"]
            is_duplicate = False

            for row in doc.contact_details:
                if (
                    (row.email or "").strip().lower() == (contact.get("email") or "").strip().lower() and
                    (row.contact_number or "").strip() == (contact.get("contact_number") or "").strip()
                ):
                    is_duplicate = True
                    break

            if not is_duplicate:
                doc.append("contact_details", {
                    "first_name": contact.get("first_name"),
                    "last_name": contact.get("last_name"),
                    "designation": contact.get("designation"),
                    "email": contact.get("email"),
                    "contact_number": contact.get("contact_number"),
                    "department_name": contact.get("department_name")
                })
        else:
            return {
                "status": "error",
                "message": "Missing required field: 'contact_details table'."
            }

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Contact Details updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error("Contact Details Update Error")
        return {
            "status": "error",
            "message": "Failed to update contact details.",
            "error": str(e)
        }
