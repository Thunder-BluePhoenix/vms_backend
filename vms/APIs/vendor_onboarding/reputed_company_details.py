import frappe
import json

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_reputed_company_details(data):
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

        # Update reputed partner details
        if "reputed_partners" in data:
            contact = data["reputed_partners"]
            doc.append("reputed_partners", {
                "company_name": contact.get("company_name"),
                "supplied_qtyyear": contact.get("supplied_qtyyear"),
                "remark": contact.get("remark")
            })
        else:
            return {
                "status": "error",
                "message": "Missing required field: 'reputed_partners table'."
            }

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding reputed partner details updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error("Vendor Onboarding reputed partner details Update Error")
        return {
            "status": "error",
            "message": "Failed to update reputed partner details.",
            "error": str(e)
        }
