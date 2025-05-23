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
           
        if "reputed_partners" not in data:
            return {
                "status": "error",
                "message": "Missing child table field: 'reputed_partners'."
            }

        doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        doc.set("reputed_partners", [])

        # Update reputed partner table
        for partner in data["reputed_partners"]:
            doc.append("reputed_partners", {
                "company_name": str(partner.get("company_name") or "").strip(),
                "supplied_qtyyear": str(partner.get("supplied_qtyyear") or "").strip(),
                "remark": str(partner.get("remark") or "").strip()
            })

            # is_duplicate = False
            # for row in doc.reputed_partners:
            #     if (
            #         str(row.company_name).strip() == new_row["company_name"] and
            #         str(row.supplied_qtyyear).strip() == new_row["supplied_qtyyear"]
            #     ):
            #         is_duplicate = True
            #         break

            # if not is_duplicate:
                # doc.append("reputed_partners", new_row)

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
