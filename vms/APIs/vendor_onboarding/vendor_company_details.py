import frappe
import json

@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_company_details(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        ref_no = data.get("ref_no")
        vendor_onboarding = data.get("vendor_onboarding")

        if not ref_no or not vendor_onboarding:
            return {
                "status": "error",
                "message": "Both 'ref_no' and 'vendor_onboarding' are required."
            }

        # Get the existing document name
        doc_name = frappe.db.get_value(
            "Vendor Onboarding Company Details",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            return {
                "status": "error",
                "message": "Record not found."
            }

        doc = frappe.get_doc("Vendor Onboarding Company Details", doc_name)

        updatable_fields = [
            "vendor_name", "company_name", "type_of_business", "website", "office_email_primary",
            "office_email_secondary", "telephone_number", "whatsapp_number", "cin_date",
            "nature_of_company", "size_of_company", "registered_office_number", "established_year",
            "nature_of_business", "corporate_identification_number", "address_line_1", "address_line_2",
            "city", "district", "state", "country", "pincode", "same_as_above", "street_1", "street_2",
            "manufacturing_city", "manufacturing_district", "manufacturing_state",
            "manufacturing_country", "manufacturing_pincode", "multiple_locations"
        ]

        for field in updatable_fields:
            if field in data:
                doc.set(field, data[field])

        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Vendor Onboarding Company Details updated successfully.",
            "name": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor Onboarding Company Update Error")
        return {
            "status": "error",
            "message": "Update failed.",
            "error": str(e)
        }
