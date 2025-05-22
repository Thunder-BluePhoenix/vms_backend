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

        # Update testing details table
        if "testing_detail" in data:
            for contact in data["testing_detail"]:
                is_duplicate = False

                for existing in doc.testing_detail:
                    if (
                        (existing.equipment_name or "").lower().strip() == (contact.get("equipment_name") or "").lower().strip() and
                        (existing.equipment_qty or "").strip() == (contact.get("equipment_qty") or "").strip() and
                        (existing.capacity or "").strip() == (contact.get("capacity") or "").strip()
                    ):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    
                    doc.append("testing_detail", {
                        "equipment_name": contact.get("equipment_name"),
                        "equipment_qty": contact.get("equipment_qty"),
                        "capacity": contact.get("capacity"),
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
