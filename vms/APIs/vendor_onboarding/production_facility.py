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

        # Create a single row with multiple division fields
        doc.append("number_of_employee", {
            "qaqc": data.get("qaqc"),
            "logistics": data.get("logistics"),
            "marketing": data.get("marketing"),
            "r_d": data.get("r_d"),
            "hse": data.get("hse"),
            "other": data.get("other"),
            "production": data.get("production")
        })

        # Append to machinery_detail table
        if "machinery_detail" in data:
            for row in data["machinery_detail"]:
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
