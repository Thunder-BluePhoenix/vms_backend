import frappe
import json
from frappe import _

# @frappe.whitelist(allow_guest=True)
# def update_vendor_onboarding_testing_details(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)

#         ref_no = data.get("ref_no")
#         vendor_onboarding = data.get("vendor_onboarding")

#         if not ref_no or not vendor_onboarding:
#             return {
#                 "status": "error",
#                 "message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
#             }

#         doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

#         doc.set("testing_detail", [])

#         # Update testing details table
#         if "testing_detail" in data and isinstance(data["testing_detail"], list):
#             for contact in data["testing_detail"]:
#                 # is_duplicate = False

#                 # for existing in doc.testing_detail:
#                 #     if (
#                 #         (existing.equipment_name or "").lower().strip() == (contact.get("equipment_name") or "").lower().strip() and
#                 #         (existing.equipment_qty or "").strip() == (contact.get("equipment_qty") or "").strip() and
#                 #         (existing.capacity or "").strip() == (contact.get("capacity") or "").strip()
#                 #     ):
#                 #         is_duplicate = True
#                 #         break

#                 # if not is_duplicate:
                    
#                 doc.append("testing_detail", {
#                     "equipment_name": contact.get("equipment_name"),
#                     "equipment_qty": contact.get("equipment_qty"),
#                     "capacity": contact.get("capacity"),
#                     "remarks": contact.get("remarks")
#                 })
#         else:
#             return {
#                 "status": "error",
#                 "message": "Missing required field: 'testing_detail table'."
#             }

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Vendor Onboarding Testing Details updated successfully.",
#             "docname": doc.name
#         }

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error("Vendor Onboarding Testing Details Update Error")
#         return {
#             "status": "error",
#             "message": "Failed to update Vendor Onboarding Testing details.",
#             "error": str(e)
#         }

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_testing_details(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        ref_no = data.get("ref_no")
        vendor_onboarding = data.get("vendor_onboarding")
        testing_data = data.get("testing_detail")

        if not ref_no or not vendor_onboarding:
            return {
                "status": "error",
                "message": _("Missing required fields: 'ref_no' and 'vendor_onboarding'.")
            }

        if not isinstance(testing_data, list):
            return {
                "status": "error",
                "message": _("Missing or invalid child table: 'testing_detail'.")
            }

        # Fetch main doc
        main_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get linked docs
        if main_doc.registered_for_multi_companies == 1:
            linked_docs = frappe.get_all(
                "Vendor Onboarding",
                filters={
                    "registered_for_multi_companies": 1,
                    "unique_multi_comp_id": main_doc.unique_multi_comp_id
                },
                fields=["name"]
            )
        else:
            linked_docs = [{"name": main_doc.name}]

        updated_docs = []

        for d in linked_docs:
            doc = frappe.get_doc("Vendor Onboarding", d.get("name"))
            doc.set("testing_detail", [])  # Clear  rows

            for row in testing_data:
                doc.append("testing_detail", {
                    "equipment_name": row.get("equipment_name"),
                    "equipment_qty": row.get("equipment_qty"),
                    "capacity": row.get("capacity"),
                    "remarks": row.get("remarks")
                })

            doc.save(ignore_permissions=True)
            updated_docs.append(doc.name)

        frappe.db.commit()

        return {
            "status": "success",
            "message": _("Vendor Onboarding Testing Details updated successfully."),
            "updated_docs": updated_docs
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Testing Details Update Error")
        return {
            "status": "error",
            "message": _("Failed to update Vendor Onboarding Testing details."),
            "error": str(e)
        }
