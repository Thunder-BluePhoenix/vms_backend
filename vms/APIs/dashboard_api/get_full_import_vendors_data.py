import frappe

@frappe.whitelist()
def get_full_data_of_import_vendors(refno=None, via_data_import=None, company=None):
    try:
        if not refno and not company:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Missing required parameter: 'refno' or 'company'."
            }

        docname = frappe.db.get_value("Vendor Master", {"name": refno, "via_data_import": via_data_import}, "name")

        if not docname:
            return {
                "status": "error",
                "message": f"No Vendor Master found for refno: {refno}"
            }

        vendor_master = frappe.get_doc("Vendor Master", docname)

        vendor_master_fields = [
            "vendor_title",
            "vendor_name",
            "office_email_primary",
            "search_term",
            "country",
            "mobile_number",
            "office_email_secondary",
            "registered_date",
            "service_provider_type",
            "registered_by",
            "via_data_import"
        ]

        vendor_details = {field: vendor_master.get(field) for field in vendor_master_fields}

        vendor_details["vendor_types"] = [
            row.as_dict() for row in vendor_master.vendor_types
        ] if vendor_master.vendor_types else []

        vendor_details["multiple_company_data"] = [
            row.as_dict() for row in vendor_master.multiple_company_data
        ] if vendor_master.multiple_company_data else []

        return {
            "status": "success",
            "data": vendor_details
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_full_data_of_import_vendors")
        return {
            "status": "error",
            "message": "An unexpected error occurred while fetching vendor data.",
            "error": str(e)
        }
