import frappe
import json

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

        #  Append number_of_employee table if not duplicate
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


        #  Append machinery_detail table if not duplicate
        if "machinery_detail" in data:
            for row in data["machinery_detail"]:
                duplicate = False
                for existing in doc.machinery_detail:
                    if (
                        existing.equipment_name == row.get("equipment_name") and
                        existing.equipment_qty == row.get("equipment_qty") and
                        existing.capacity == row.get("capacity")
                    ):
                        duplicate = True
                        break

                if not duplicate:
                    doc.append("machinery_detail", {
                        "equipment_name": row.get("equipment_name"),
                        "equipment_qty": row.get("equipment_qty"),
                        "capacity": row.get("capacity"),
                        "remarks": row.get("remarks")
                    })
        else:
            return {
                "status": "error",
                "message": "Missing required field: 'machinery_detail'."
            }

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Production Facility updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Production Facility Details Update Error")
        return {
            "status": "error",
            "message": "Failed to update Vendor Onboarding production facility details.",
            "error": str(e)
        }
