import frappe
import json
from frappe import _
from frappe.utils import nowdate, format_date
from datetime import datetime




@frappe.whitelist(allow_guest=True)
def get_vendor_validation(doc):
    try:
        po_number = doc.name
        vendor_code = doc.vendor_code
        company_code = doc.company_code

        if not vendor_code:
            result = {"status": "error", "message": f"No Vendor Code found for PO {po_number}"}
        
        if not company_code:
            result =  {"status": "error", "message": f"No Company Code found for PO {po_number}"}
        
        if vendor_code and company_code:
            vendor_match = frappe.db.sql("""
                SELECT 
                    cvc.vendor_ref_no,
                    vc.vendor_code,
                    vc.state,
                    vc.gst_no
                FROM `tabCompany Vendor Code` cvc
                INNER JOIN `tabVendor Code` vc ON vc.parent = cvc.name
                WHERE cvc.company_code = %s
                AND vc.vendor_code = %s
                LIMIT 1
            """, (company_code, vendor_code), as_dict=True)
            
            if not vendor_match:
                result = {
                    "status": "error", 
                    "message": f"No matching Vendor Code '{vendor_code}' found in Company Vendor Code records for Company Code {company_code}"
                }
            
            else:
            
                vendor_master_name = vendor_match[0].vendor_ref_no
                
                # Fetch Vendo-date Master emails using SQL
                vendor_master_data = frappe.db.sql("""
                                        SELECT
                                            validity_status,
                                            is_blocked,
                                            office_email_primary                  
                                        FROM `tabVendor Master`
                                        WHERE name = %s
                                                """, (vendor_master_name,), as_dict=True)
            
                if not vendor_master_data:
                    result =  {"status": "error", "message": f"Vendor Master {vendor_master_name} not found"}

                else:
                
                    vendor_data = vendor_master_data[0]
                    validity_status = vendor_data.validity_status
                    is_blocked = vendor_data.is_blocked
                    office_email_primary = vendor_data.office_email_primary or ""
                    
                    # Prepare result structure
                    result = {
                        "status": "success",
                        "vendor_master": vendor_master_name,
                        "vendor_data": {
                            "office_email_primary": office_email_primary,
                            "validity_status": validity_status,
                            "is_blocked": is_blocked,
                            "vendor_code": vendor_code,
                            "company_code": company_code
                        }
                    }
        
        return result
        
        
    except Exception as e:
        frappe.log_error(
            f"Error fetching vendor email for PO {po_number}: {str(e)}\n{frappe.get_traceback()}", 
            "Get Vendor Mails Error"
        )
        return {"status": "error", "message": str(e)}
    




