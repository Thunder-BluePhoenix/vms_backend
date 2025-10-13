import frappe
import json
from frappe import _
from frappe.utils import nowdate, format_date
from datetime import datetime

@frappe.whitelist(allow_guest=True)
def get_vendor_mails(po_number):
    try:
        # Get the Purchase Order document
        purchase_order = frappe.get_doc("Purchase Order", po_number)
        vendor_code = purchase_order.vendor_code
        company_code = purchase_order.company_code

        if not vendor_code:
            return {"status": "error", "message": f"No Vendor Code found for PO {po_number}"}
        if not company_code:
            return {"status": "error", "message": f"No Company Code found for PO {po_number}"}
        
        # Get Company Master name from company_code
        company_master = frappe.get_value("Company Master", {"company_code": company_code}, "name")

        if not company_master:
            return {"status": "error", "message": f"No Company Master found for Company Code {company_code}"}
        
        # Find Company Vendor Code document with matching company_code
        company_vendor_codes = frappe.get_all(
            "Company Vendor Code",
            filters={"company_code": company_code},
            fields=["name", "vendor_ref_no"]
        )
        
        if not company_vendor_codes:
            return {"status": "error", "message": f"No Company Vendor Code found for Company Code {company_code}"}
        
        # Search through each Company Vendor Code to find matching vendor_code in child table
        vendor_master_name = None
        for cvc in company_vendor_codes:
            # Check the vendor_code child table for matching vendor_code
            vendor_code_entries = frappe.get_all(
                "Vendor Code",
                filters={
                    "parent": cvc.name,
                    "vendor_code": vendor_code
                },
                fields=["name", "vendor_code", "state", "gst_no"]
            )
            
            if vendor_code_entries:
                # Found a match, get the vendor_master reference
                vendor_master_name = cvc.vendor_ref_no
                break
        
        if not vendor_master_name:
            return {"status": "error", "message": f"No matching Vendor Code '{vendor_code}' found in Company Vendor Code records for Company Code {company_code}"}
        
        # Fetch the Vendor Master document
        vendor_master = frappe.get_doc("Vendor Master", vendor_master_name)
        
        # Get email fields
        office_email_primary = vendor_master.office_email_primary or ""
        office_email_secondary = vendor_master.office_email_secondary or ""
        
        # Prepare response
        result = {
            "status": "success",
            "vendor_master": vendor_master_name,
            "office_email_primary": office_email_primary,
            "office_email_secondary": office_email_secondary,
            "emails": []
        }
        
        # Add emails to list (only if they exist)
        if office_email_primary:
            result["emails"].append(office_email_primary)
        if office_email_secondary:
            result["emails"].append(office_email_secondary)
        
        if not result["emails"]:
            result["message"] = "Vendor Master found but no email addresses available"
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error fetching vendor email for PO {po_number}: {str(e)}", "Get Vendor Mails Error")
        return {"status": "error", "message": str(e)}