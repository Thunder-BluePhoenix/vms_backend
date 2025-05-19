import frappe
import json
from frappe.utils.file_manager import save_file

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
            "vendor_title","vendor_name", "company_name", "type_of_business", "website", "office_email_primary",
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

# update vendor onboarding company address
@frappe.whitelist(allow_guest=True)
def update_vendor_onboarding_company_address(data):
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

        doc_name = frappe.db.get_value(
            "Vendor Onboarding Company Details",
            {"ref_no": ref_no, "vendor_onboarding": vendor_onboarding},
            "name"
        )

        if not doc_name:
            return {
                "status": "error",
                "message": "Vendor Onboarding Company Details record not found."
            }

        doc = frappe.get_doc("Vendor Onboarding Company Details", doc_name)

        fields_to_update = [
            "address_line_1", "address_line_2", "city", "district", "state", "country", "pincode",
            "same_as_above", "street_1", "street_2", "manufacturing_city", "manufacturing_district",
            "manufacturing_state", "manufacturing_country", "manufacturing_pincode",
            "multiple_locations", "gst"
        ]

        for field in fields_to_update:
            if field in data:
                doc.set(field, data[field])

        # upload and set address_proofattachment if file provided
        if 'file' in frappe.request.files:
            file = frappe.request.files['file']
            saved_file = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, is_private=1)
            doc.address_proofattachment = saved_file.file_url

        # update child table
        if "multiple_location_table" in data:
            for row in data["multiple_location_table"]:
                doc.append("multiple_location_table", row)

        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Company address and locations updated successfully.",
            "docname": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Company Address Update Error")
        return {
            "status": "error",
            "message": "Failed to update company address.",
            "error": str(e)
        }
