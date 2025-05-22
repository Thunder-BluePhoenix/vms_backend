import frappe
import json

# update number of employee table
@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_production_facility_details(data):
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


        new_row = {
            "qaqc": str(data.get("qaqc") or "").strip(),
            "logistics": str(data.get("logistics") or "").strip(),
            "marketing": str(data.get("marketing") or "").strip(),
            "r_d": str(data.get("r_d") or "").strip(),
            "hse": str(data.get("hse") or "").strip(),
            "other": str(data.get("other") or "").strip(),
            "production": str(data.get("production") or "").strip()
        }

        is_duplicate = False
        for row in doc.number_of_employee:
            if (
                str(row.qaqc).strip() == new_row["qaqc"] and
                str(row.logistics).strip() == new_row["logistics"] and
                str(row.marketing).strip() == new_row["marketing"] and
                str(row.r_d).strip() == new_row["r_d"] and
                str(row.hse).strip() == new_row["hse"] and
                str(row.other).strip() == new_row["other"] and
                str(row.production).strip() == new_row["production"]
            ):
                is_duplicate = True
                break

        if not is_duplicate:
            doc.append("number_of_employee", new_row)

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Number of employee updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Number of emplloyee Update Error")
        return {
            "status": "error",
            "message": "Failed to update Vendor Onboarding Number of employee details.",
            "error": str(e)
        }


# update Machinery details table
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
                "message": "Missing required fields: 'ref_no' and 'vendor_onboarding'."
            }

        doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        if "machinery_detail" not in data:
            return {
                "status": "error",
                "message": "Missing required field: 'machinery_detail'."
            }

        for row in data["machinery_detail"]:
            duplicate = any(
                existing.equipment_name == row.get("equipment_name") and
                existing.equipment_qty == row.get("equipment_qty") and
                existing.capacity == row.get("capacity")
                for existing in doc.machinery_detail
            )

            if not duplicate:
                doc.append("machinery_detail", {
                    "equipment_name": row.get("equipment_name"),
                    "equipment_qty": row.get("equipment_qty"),
                    "capacity": row.get("capacity"),
                    "remarks": row.get("remarks")
                })

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Machinery Detail updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Machinery Detail Update Error")
        return {
            "status": "error",
            "message": "Failed to update Vendor Onboarding machinery detail.",
            "error": str(e)
        }
