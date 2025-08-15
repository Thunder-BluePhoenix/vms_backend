# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now, getdate, get_fullname
import json


@frappe.whitelist()
def create_vendor_onboarding_amendment(data):
    """
    Robust API to create vendor onboarding amendment
    
    Args:
        data: JSON string or dict containing:
            - vendor_onboarding: Vendor Onboarding document name (required)
            - remarks: Amendment remarks (required)
            - amended_by: User who is making the amendment (optional, defaults to current user)
    
    Returns:
        dict: Status and details of the amendment creation
    """
    try:
        # Parse data if it's a JSON string
        if isinstance(data, str):
            data = json.loads(data)
        
        # Validate required fields
        vendor_onboarding_name = data.get("vendor_onboarding")
        remarks = data.get("remarks")
        amended_by = data.get("amended_by") or frappe.session.user
        
        if not vendor_onboarding_name:
            return {
                "status": "error",
                "message": "Missing required field: 'vendor_onboarding'"
            }
        
        if not remarks:
            return {
                "status": "error", 
                "message": "Missing required field: 'remarks'"
            }
        
        # Validate vendor onboarding document exists
        if not frappe.db.exists("Vendor Onboarding", vendor_onboarding_name):
            return {
                "status": "error",
                "message": f"Vendor Onboarding '{vendor_onboarding_name}' does not exist"
            }
        
        # Validate amended_by user exists
        if not frappe.db.exists("User", amended_by):
            return {
                "status": "error",
                "message": f"User '{amended_by}' does not exist"
            }
        
        # Get the vendor onboarding document
        vendor_onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding_name)
        
        # Check permissions
        if not vendor_onboarding_doc.has_permission("write"):
            return {
                "status": "error",
                "message": "You don't have permission to amend this vendor onboarding"
            }
        
        # Begin database transaction
        frappe.db.begin()
        
        # Reset rejection fields as required
        vendor_onboarding_doc.rejected = 0
        vendor_onboarding_doc.rejected_by = None
        vendor_onboarding_doc.rejected_by_designation = None
        vendor_onboarding_doc.reason_for_rejection = None
        
        # Add new amendment entry to the amendment_details table
        amendment_row = vendor_onboarding_doc.append("amendment_details", {})
        amendment_row.datetime = now()
        amendment_row.amended_by = amended_by
        amendment_row.remarks = remarks
        
        # Save the document
        vendor_onboarding_doc.save(ignore_permissions=True)
        
        # Commit the transaction
        frappe.db.commit()
        
        # Get amended by user details for response
        amended_by_details = frappe.get_value("User", amended_by, 
                                            ["full_name", "email"], as_dict=True)
        
        return {
            "status": "success",
            "message": "Vendor onboarding amendment created successfully",
            "data": {
                "vendor_onboarding": vendor_onboarding_name,
                "amendment_id": amendment_row.name,
                "datetime": amendment_row.datetime,
                "amended_by": amended_by,
                "amended_by_name": amended_by_details.get("full_name") if amended_by_details else amended_by,
                "amended_by_email": amended_by_details.get("email") if amended_by_details else None,
                "remarks": remarks,
                "rejected": vendor_onboarding_doc.rejected,
                "rejected_by": vendor_onboarding_doc.rejected_by,
                "rejected_by_designation": vendor_onboarding_doc.rejected_by_designation
            }
        }
        
    except frappe.ValidationError as ve:
        frappe.db.rollback()
        frappe.log_error(f"Validation error in amendment creation: {str(ve)}", 
                         "Vendor Amendment Validation Error")
        return {
            "status": "error",
            "message": f"Validation error: {str(ve)}"
        }
        
    except frappe.PermissionError as pe:
        frappe.db.rollback()
        frappe.log_error(f"Permission error in amendment creation: {str(pe)}", 
                         "Vendor Amendment Permission Error")
        return {
            "status": "error",
            "message": "You don't have sufficient permissions to perform this action"
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error creating vendor onboarding amendment: {str(e)}\n\n{frappe.get_traceback()}", 
                         "Vendor Amendment Creation Error")
        return {
            "status": "error",
            "message": "Failed to create vendor onboarding amendment",
            "error": str(e)
        }
