import frappe
import json
from frappe import _

# update number of employee table
# @frappe.whitelist(allow_guest=True)
# def update_vendor_onboarding_production_facility_details(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)

#         ref_no = data.get("ref_no")
#         vendor_onboarding = data.get("vendor_onboarding")
#         employee_rows = data.get("number_of_employee", [])

#         if not ref_no or not vendor_onboarding:
#             return {
#                 "status": "error",
#                 "message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
#             }

#         doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

#         doc.set("number_of_employee", [])

#         for row in employee_rows:
#             doc.append("number_of_employee", {
#                 "qaqc": str(row.get("qaqc") or "").strip(),
#                 "logistics": str(row.get("logistics") or "").strip(),
#                 "marketing": str(row.get("marketing") or "").strip(),
#                 "r_d": str(row.get("r_d") or "").strip(),
#                 "hse": str(row.get("hse") or "").strip(),
#                 "other": str(row.get("other") or "").strip(),
#                 "production": str(row.get("production") or "").strip()
#             })

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Vendor Onboarding Number of employee updated successfully.",
#             "docname": doc.name
#         }

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Number of Employee Update Error")
#         return {
#             "status": "error",
#             "message": "Failed to update Vendor Onboarding Number of employee details.",
#             "error": str(e)
#         }


@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_production_facility_details(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        ref_no = data.get("ref_no")
        vendor_onboarding = data.get("vendor_onboarding")
        employee_rows = data.get("number_of_employee", [])

        if not ref_no or not vendor_onboarding:
            return {
                "status": "error",
                "message": _("Missing required fields: 'ref_no' and 'vendor_onboarding'.")
            }

        main_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

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

        # Loop over each linked document and update the child table
        for d in linked_docs:
            doc = frappe.get_doc("Vendor Onboarding", d.get("name"))
            doc.set("number_of_employee", [])  # Clear existing child table

            for row in employee_rows:
                doc.append("number_of_employee", {
                    "qaqc": str(row.get("qaqc") or "").strip(),
                    "logistics": str(row.get("logistics") or "").strip(),
                    "marketing": str(row.get("marketing") or "").strip(),
                    "r_d": str(row.get("r_d") or "").strip(),
                    "hse": str(row.get("hse") or "").strip(),
                    "other": str(row.get("other") or "").strip(),
                    "production": str(row.get("production") or "").strip()
                })

            doc.save(ignore_permissions=True)
            updated_docs.append(doc.name)

        frappe.db.commit()

        return {
            "status": "success",
            "message": _("Vendor Onboarding 'number_of_employee' updated successfully."),
            "updated_docs": updated_docs
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Number of Employee Update Error")
        return {
            "status": "error",
            "message": _("Failed to update Vendor Onboarding 'number_of_employee' details."),
            "error": str(e)
        }
    


# update Machinery details table

# @frappe.whitelist(allow_guest=True)
# def update_vendor_onboarding_machinery_detail(data):
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

#         if "machinery_detail" not in data:
#             return {
#                 "status": "error",
#                 "message": "Missing required field: 'machinery_detail'."
#             }
        
#         doc.set("machinery_detail", [])

#         for row in data["machinery_detail"]:
#             # duplicate = any(
#             #     existing.equipment_name == row.get("equipment_name") and
#             #     existing.equipment_qty == row.get("equipment_qty") and
#             #     existing.capacity == row.get("capacity")
#             #     for existing in doc.machinery_detail
#             # )

#             # if not duplicate:
            
#             doc.append("machinery_detail", {
#                 "equipment_name": row.get("equipment_name"),
#                 "equipment_qty": row.get("equipment_qty"),
#                 "capacity": row.get("capacity"),
#                 "remarks": row.get("remarks")
#             })

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Vendor Onboarding Machinery Detail updated successfully.",
#             "docname": doc.name
#         }

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Machinery Detail Update Error")
#         return {
#             "status": "error",
#             "message": "Failed to update Vendor Onboarding machinery detail.",
#             "error": str(e)
#         }

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_machinery_detail(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        ref_no = data.get("ref_no")
        vendor_onboarding = data.get("vendor_onboarding")

        if not ref_no or not vendor_onboarding:
            return {
                "status": "error",
                "message": _("Missing required fields: 'ref_no' and 'vendor_onboarding'.")
            }

        if "machinery_detail" not in data:
            return {
                "status": "error",
                "message": _("Missing required field: 'machinery_detail'.")
            }

        # Fetch main Vendor Onboarding doc
        main_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get linked docs based on multi company registration
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
            doc.set("machinery_detail", [])  # Clear existing rows

            for row in data["machinery_detail"]:
                doc.append("machinery_detail", {
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
            "message": _("Vendor Onboarding Machinery Detail updated successfully."),
            "updated_docs": updated_docs
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Machinery Detail Update Error")
        return {
            "status": "error",
            "message": _("Failed to update Vendor Onboarding machinery detail."),
            "error": str(e)
        }
