import frappe
import json

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_testing_details(data):
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

        # Update testing details
        if "testing_detail" in data:
            contact = data["testing_detail"]
            doc.append("testing_detail", {
                "equipment_name": contact.get("equipment_name"),
                "equipment_qty": contact.get("equipment_qty"),
                "capacity": contact.get("capacity"),
                "email": contact.get("email"),
                "remarks": contact.get("remarks")
            })
        else:
            return {
                "status": "error",
                "message": "Missing required field: 'testing_detail table'."
            }

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Testing Details updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error("Vendor Onboarding Testing Details Update Error")
        return {
            "status": "error",
            "message": "Failed to update Vendor Onboarding Testing details.",
            "error": str(e)
        }
