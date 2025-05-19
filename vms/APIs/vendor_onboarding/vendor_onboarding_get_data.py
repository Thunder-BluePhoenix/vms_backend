import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_vendor_onboarding_data(vendor_onboarding):
    try:
        if not vendor_onboarding:
            return {
                "status": "error",
                "message": "Missing required field: vendor_onboarding"
            }

        # Fetch vendor onboarding document
        onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        if not onboarding_doc:
            return {
                "status": "error",
                "message": "Vendor onboarding document not found."
            }
        
        # company name from Company Master
        full_company_name = frappe.db.get_value("Company Master", onboarding_doc.company_name, "company_name")

        onboarding_data = onboarding_doc.as_dict()
        onboarding_data["full_company_name"] = full_company_name

        # Fetch child documents
        linked_docs = {}

        if onboarding_doc.ref_no:
            linked_docs["vendor_master"] = frappe.get_doc("Vendor Master", onboarding_doc.ref_no).as_dict()
        
        company_details_list = []
        if onboarding_doc.vendor_company_details:
            for row in onboarding_doc.vendor_company_details:
                if row.vendor_company_details:
                    detail_doc = frappe.get_doc("Vendor Onboarding Company Details", row.vendor_company_details)
                    company_details_list.append(detail_doc.as_dict())

        linked_docs["vendor_company_details"] = company_details_list

        if onboarding_doc.payment_detail:
            linked_docs["payment_detail"] = frappe.get_doc("Vendor Onboarding Payment Details", onboarding_doc.payment_detail).as_dict()
                                                                                              
        if onboarding_doc.document_details:
            linked_docs["document_details"] = frappe.get_doc("Legal Documents", onboarding_doc.document_details).as_dict()

        if onboarding_doc.certificate_details:
            linked_docs["certificate_details"] = frappe.get_doc("Vendor Onboarding Certificates", onboarding_doc.certificate_details).as_dict()

        if onboarding_doc.manufacturing_details:
            linked_docs["manufacturing_details"] = frappe.get_doc("Vendor Onboarding Manufacturing Details", onboarding_doc.manufacturing_details).as_dict()

        return {
            "status": "success",
            "message": "Vendor onboarding data with related documents fetched successfully.",
            "data": {
                "vendor_onboarding": onboarding_data,
                **linked_docs
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vendor onboarding data with related documents fetching Error.")
        return {
            "status": "error",
            "message": "Failed to fetch Vendor onboarding data with related documents.",
            "error": str(e)
        }