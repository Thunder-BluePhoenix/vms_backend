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
    




@frappe.whitelist()
def validate_single_po(po_name):
    """
    Validate vendor code for a single Purchase Order
    
    Args:
        po_name: Name of the Purchase Order document
    
    Returns:
        Validation result with status and details
    """
    try:
        if not po_name:
            return {
                "status": "error",
                "message": "Purchase Order name is required"
            }
        
        # Check if PO exists
        if not frappe.db.exists("Purchase Order", po_name):
            return {
                "status": "error",
                "message": f"Purchase Order {po_name} does not exist"
            }
        
        # Get validation result using SQL with proper subquery
        validation_result = frappe.db.sql("""
            SELECT 
                po.name,
                po.vendor_code,
                po.company_code,
                po.vendor_code_invalid as current_status,
                (
                    SELECT cvc.name 
                    FROM `tabCompany Vendor Code` cvc
                    INNER JOIN `tabVendor Code` vc ON vc.parent = cvc.name
                    WHERE cvc.company_code = po.company_code 
                    AND vc.vendor_code = po.vendor_code
                    LIMIT 1
                ) as cvc_name,
                (
                    SELECT cvc.vendor_ref_no 
                    FROM `tabCompany Vendor Code` cvc
                    INNER JOIN `tabVendor Code` vc ON vc.parent = cvc.name
                    WHERE cvc.company_code = po.company_code 
                    AND vc.vendor_code = po.vendor_code
                    LIMIT 1
                ) as vendor_ref_no,
                (
                    SELECT vm.name
                    FROM `tabCompany Vendor Code` cvc
                    INNER JOIN `tabVendor Code` vc ON vc.parent = cvc.name
                    INNER JOIN `tabVendor Master` vm ON vm.name = cvc.vendor_ref_no
                    WHERE cvc.company_code = po.company_code 
                    AND vc.vendor_code = po.vendor_code
                    LIMIT 1
                ) as vm_name,
                (
                    SELECT vm.validity_status
                    FROM `tabCompany Vendor Code` cvc
                    INNER JOIN `tabVendor Code` vc ON vc.parent = cvc.name
                    INNER JOIN `tabVendor Master` vm ON vm.name = cvc.vendor_ref_no
                    WHERE cvc.company_code = po.company_code 
                    AND vc.vendor_code = po.vendor_code
                    LIMIT 1
                ) as validity_status,
                (
                    SELECT vm.is_blocked
                    FROM `tabCompany Vendor Code` cvc
                    INNER JOIN `tabVendor Code` vc ON vc.parent = cvc.name
                    INNER JOIN `tabVendor Master` vm ON vm.name = cvc.vendor_ref_no
                    WHERE cvc.company_code = po.company_code 
                    AND vc.vendor_code = po.vendor_code
                    LIMIT 1
                ) as is_blocked,
                (
                    SELECT vm.office_email_primary
                    FROM `tabCompany Vendor Code` cvc
                    INNER JOIN `tabVendor Code` vc ON vc.parent = cvc.name
                    INNER JOIN `tabVendor Master` vm ON vm.name = cvc.vendor_ref_no
                    WHERE cvc.company_code = po.company_code 
                    AND vc.vendor_code = po.vendor_code
                    LIMIT 1
                ) as office_email_primary
            FROM `tabPurchase Order` po
            WHERE po.name = %s
        """, (po_name,), as_dict=True)
        
        if not validation_result:
            return {
                "status": "error",
                "message": f"Could not retrieve validation data for {po_name}"
            }
        
        result = validation_result[0]
        
        # Calculate the validation status
        calculated_status = 0
        
        if not result.vendor_code or result.vendor_code == '':
            calculated_status = 1
        elif not result.company_code or result.company_code == '':
            calculated_status = 1
        elif not result.cvc_name:
            calculated_status = 1
        elif not result.vm_name:
            calculated_status = 1
        elif result.is_blocked == 1:
            calculated_status = 1
        elif result.validity_status != 'Valid':
            calculated_status = 1
        
        # Determine validation status
        is_valid = calculated_status == 0
        
        # Build detailed message
        issues = []
        if not result.vendor_code or result.vendor_code == '':
            issues.append("Vendor Code is missing")
        if not result.company_code or result.company_code == '':
            issues.append("Company Code is missing")
        if result.vendor_code and result.company_code and not result.cvc_name:
            issues.append(f"Vendor Code '{result.vendor_code}' not found in Company Vendor Code for Company '{result.company_code}'")
        if result.cvc_name and not result.vm_name:
            issues.append("Vendor Master not found for the matched Company Vendor Code")
        if result.is_blocked == 1:
            issues.append("Vendor is blocked")
        if result.validity_status and result.validity_status != 'Valid':
            issues.append(f"Vendor validity status is '{result.validity_status}' (not Valid)")
        
        # Update the field if status changed
        status_updated = False
        if result.current_status != calculated_status:
            frappe.db.set_value(
                "Purchase Order",
                po_name,
                "vendor_code_invalid",
                calculated_status,
                update_modified=True
            )
            frappe.db.commit()
            status_updated = True
        
        return {
            "status": "success",
            "is_valid": is_valid,
            "vendor_code_invalid": calculated_status,
            "status_updated": status_updated,
            "message": "Vendor code is valid" if is_valid else "Vendor code validation failed",
            "issues": issues,
            "details": {
                "vendor_code": result.vendor_code or 'N/A',
                "company_code": result.company_code or 'N/A',
                "company_vendor_code": result.cvc_name or 'Not Found',
                "vendor_master": result.vm_name or 'Not Found',
                "vendor_email": result.office_email_primary or 'N/A',
                "validity_status": result.validity_status or 'N/A',
                "is_blocked": 'Yes' if result.is_blocked == 1 else 'No',
                "previous_status": result.current_status,
                "current_status": calculated_status
            }
        }
        
    except Exception as e:
        frappe.log_error(
            f"Error validating PO {po_name}: {str(e)}\n{frappe.get_traceback()}",
            "Single PO Validation Error"
        )
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }