import frappe
import json
from frappe.utils.file_manager import save_file

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_manufacturing_details(data):
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

        doc_name = frappe.db.get_value(
            "Vendor Onboarding Manufacturing Details",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            return {
                "status": "error",
                "message": "Vendor Onboarding Manufacturing Record not found."
            }

        doc = frappe.get_doc("Vendor Onboarding Manufacturing Details", doc_name)

        # Updatable fields
        fields_to_update = [
            "details_of_product_manufactured", "total_godown", "storage_capacity", "spare_capacity",
            "type_of_premises", "working_hours", "weekly_holidays", "number_of_manpower",
            "annual_revenue", "google_address_pin", "cold_storage"
        ]

        for field in fields_to_update:
            if field in data and data[field] is not None:
                doc.set(field, data[field])

        # Update brochure attachment
        if 'brochure_proof' in frappe.request.files:
            file = frappe.request.files['brochure_proof']
            saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
            doc.brochure_proof = saved.file_url

        # Update org structure attachment
        if 'organisation_structure_document' in frappe.request.files:
            file = frappe.request.files['organisation_structure_document']
            saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
            doc.organisation_structure_document = saved.file_url

        # update child table
        if "materials_supplied" in data:
            index = 0
            for row in data["materials_supplied"]:
                material_row = doc.append("materials_supplied", row)

                file_key = f"material_images_{index}"
                if file_key in frappe.request.files:
                    file = frappe.request.files[file_key]
                    saved = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
                    material_row.material_images = saved.file_url

                index += 1

        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Manufacturing details updated successfully.",
            "docname": doc.name,
            "brochure_proof": doc.brochure_proof if hasattr(doc, "brochure_proof") else None,
            "organisation_structure_document": doc.organisation_structure_document if hasattr(doc, "organisation_structure_document") else None
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Manufacturing Details Update Error")
        return {
            "status": "error",
            "message": "Failed to update manufacturing details.",
            "error": str(e)
        }
