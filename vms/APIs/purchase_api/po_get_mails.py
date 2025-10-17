import frappe
import json
from frappe import _
from frappe.utils import nowdate, format_date
from datetime import datetime

@frappe.whitelist(allow_guest=True)
def get_vendor_mails_orm(po_number):
    try:
        # Get the Purchase Order document
        purchase_order = frappe.get_doc("Purchase Order", po_number)
        vendor_code = purchase_order.vendor_code
        company_code = purchase_order.company_code
        purchase_user_email = purchase_order.email2  # Purchase user's email

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
        
        # Get vendor email fields
        office_email_primary = vendor_master.office_email_primary or ""
        office_email_secondary = vendor_master.office_email_secondary or ""
        
        # Prepare result
        result = {
            "status": "success",
            "vendor_master": vendor_master_name,
            "vendor_emails": {
                "office_email_primary": office_email_primary,
                "office_email_secondary": office_email_secondary,
                "all_vendor_emails": []
            },
            "team_members": {
                "by_designation": {},
                "reporting_head": None,
                "all_team_user_ids": []
            }
        }
        
        # Add vendor emails to list (only if they exist)
        if office_email_primary:
            result["vendor_emails"]["all_vendor_emails"].append(office_email_primary)
        if office_email_secondary:
            result["vendor_emails"]["all_vendor_emails"].append(office_email_secondary)
        
        if not result["vendor_emails"]["all_vendor_emails"]:
            result["message"] = "Vendor Master found but no email addresses available"
        
        # Now fetch team information from purchase user email
        if purchase_user_email:
            # Get employee from user email
            employee = frappe.get_value(
                "Employee", 
                {"user_id": purchase_user_email}, 
                ["name", "team", "full_name"],
                as_dict=True
            )
            
            if employee and employee.team:
                team_name = employee.team
                result["team_members"]["team_name"] = team_name
                result["team_members"]["purchase_user"] = {
                    "name": employee.name,
                    "full_name": employee.full_name,
                    "user_id": purchase_user_email
                }
                
                # Get Team Master document to fetch reporting_head
                team_master = frappe.get_doc("Team Master", team_name)
                
                if team_master.reporting_head:
                    # Get reporting head's user_id
                    reporting_head_user_id = frappe.get_value(
                        "Employee",
                        team_master.reporting_head,
                        "user_id"
                    )
                    
                    result["team_members"]["reporting_head"] = {
                        "employee_name": team_master.reporting_head,
                        "user_id": reporting_head_user_id
                    }
                    
                    if reporting_head_user_id:
                        result["team_members"]["all_team_user_ids"].append(reporting_head_user_id)
                
                # Get all employees in the team
                team_employees = frappe.get_all(
                    "Employee",
                    filters={
                        "team": team_name,
                        "status": "Active"  # Only active employees
                    },
                    fields=["name", "full_name", "user_id", "designation"]
                )
                
                # Separate by designation
                for emp in team_employees:
                    if emp.user_id:
                        designation = emp.designation or "No Designation"
                        
                        if designation not in result["team_members"]["by_designation"]:
                            result["team_members"]["by_designation"][designation] = []
                        
                        result["team_members"]["by_designation"][designation].append({
                            "employee_name": emp.name,
                            "full_name": emp.full_name,
                            "user_id": emp.user_id
                        })
                        
                        # Add to all team user_ids list
                        if emp.user_id not in result["team_members"]["all_team_user_ids"]:
                            result["team_members"]["all_team_user_ids"].append(emp.user_id)
                
                result["team_members"]["total_team_members"] = len(team_employees)
                result["team_members"]["designation_count"] = {
                    designation: len(members) 
                    for designation, members in result["team_members"]["by_designation"].items()
                }
            else:
                result["team_members"]["message"] = "Employee or team not found for purchase user email"
        else:
            result["team_members"]["message"] = "No purchase user email (email2) found in PO"
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error fetching vendor email for PO {po_number}: {str(e)}", "Get Vendor Mails Error")
        return {"status": "error", "message": str(e)}
    




@frappe.whitelist(allow_guest=True)
def get_vendor_mails(po_number):
    try:
        # Get Purchase Order data using SQL - single query
        po_data = frappe.db.sql("""
            SELECT 
                vendor_code,
                company_code,
                email2 as purchase_user_email
            FROM `tabPurchase Order`
            WHERE name = %s
        """, (po_number,), as_dict=True)
        
        if not po_data:
            return {"status": "error", "message": f"Purchase Order {po_number} not found"}
        
        po = po_data[0]
        vendor_code = po.vendor_code
        company_code = po.company_code
        purchase_user_email = po.purchase_user_email

        if not vendor_code:
            return {"status": "error", "message": f"No Vendor Code found for PO {po_number}"}
        if not company_code:
            return {"status": "error", "message": f"No Company Code found for PO {po_number}"}
        
        # Get Company Master name from company_code using SQL
        company_master = frappe.db.sql("""
            SELECT name 
            FROM `tabCompany Master`
            WHERE company_code = %s
            LIMIT 1
        """, (company_code,), as_dict=True)

        if not company_master:
            return {"status": "error", "message": f"No Company Master found for Company Code {company_code}"}
        
        # Find matching vendor_code in Company Vendor Code and its child table using JOIN
        # This is the key optimization - using a single JOIN query instead of multiple queries
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
            return {
                "status": "error", 
                "message": f"No matching Vendor Code '{vendor_code}' found in Company Vendor Code records for Company Code {company_code}"
            }
        
        vendor_master_name = vendor_match[0].vendor_ref_no
        
        # Fetch Vendor Master emails using SQL
        vendor_emails = frappe.db.sql("""
            SELECT 
                office_email_primary,
                office_email_secondary
            FROM `tabVendor Master`
            WHERE name = %s
        """, (vendor_master_name,), as_dict=True)
        
        if not vendor_emails:
            return {"status": "error", "message": f"Vendor Master {vendor_master_name} not found"}
        
        vendor_email_data = vendor_emails[0]
        office_email_primary = vendor_email_data.office_email_primary or ""
        office_email_secondary = vendor_email_data.office_email_secondary or ""
        
        # Prepare result structure
        result = {
            "status": "success",
            "vendor_master": vendor_master_name,
            "vendor_emails": {
                "office_email_primary": office_email_primary,
                "office_email_secondary": office_email_secondary,
                "all_vendor_emails": []
            },
            "team_members": {
                "by_designation": {},
                "reporting_head": None,
                "all_team_user_ids": []
            }
        }
        
        # Add vendor emails to list
        if office_email_primary:
            result["vendor_emails"]["all_vendor_emails"].append(office_email_primary)
        if office_email_secondary:
            result["vendor_emails"]["all_vendor_emails"].append(office_email_secondary)
        
        if not result["vendor_emails"]["all_vendor_emails"]:
            result["message"] = "Vendor Master found but no email addresses available"
        
        # Fetch team information using SQL if purchase_user_email exists
        if purchase_user_email:
            # Get employee and team info in one query
            employee_data = frappe.db.sql("""
                SELECT 
                    name,
                    team,
                    full_name
                FROM `tabEmployee`
                WHERE user_id = %s
                LIMIT 1
            """, (purchase_user_email,), as_dict=True)
            
            if employee_data and employee_data[0].team:
                employee = employee_data[0]
                team_name = employee.team
                
                result["team_members"]["team_name"] = team_name
                result["team_members"]["purchase_user"] = {
                    "name": employee.name,
                    "full_name": employee.full_name,
                    "user_id": purchase_user_email
                }
                
                # Get Team Master reporting_head in one query
                team_master_data = frappe.db.sql("""
                    SELECT reporting_head
                    FROM `tabTeam Master`
                    WHERE name = %s
                """, (team_name,), as_dict=True)
                
                if team_master_data and team_master_data[0].reporting_head:
                    reporting_head_employee = team_master_data[0].reporting_head
                    
                    # Get reporting head's user_id
                    reporting_head_data = frappe.db.sql("""
                        SELECT user_id
                        FROM `tabEmployee`
                        WHERE name = %s
                    """, (reporting_head_employee,), as_dict=True)
                    
                    if reporting_head_data:
                        reporting_head_user_id = reporting_head_data[0].user_id
                        
                        result["team_members"]["reporting_head"] = {
                            "employee_name": reporting_head_employee,
                            "user_id": reporting_head_user_id
                        }
                        
                        if reporting_head_user_id:
                            result["team_members"]["all_team_user_ids"].append(reporting_head_user_id)
                
                # Get all team employees with designation in a single query
                team_employees = frappe.db.sql("""
                    SELECT 
                        name,
                        full_name,
                        user_id,
                        designation
                    FROM `tabEmployee`
                    WHERE team = %s
                    AND status = 'Active'
                    AND user_id IS NOT NULL
                    AND user_id != ''
                """, (team_name,), as_dict=True)
                
                # Group by designation
                designation_groups = {}
                all_user_ids = set(result["team_members"]["all_team_user_ids"])
                
                for emp in team_employees:
                    designation = emp.designation or "No Designation"
                    
                    if designation not in designation_groups:
                        designation_groups[designation] = []
                    
                    designation_groups[designation].append({
                        "employee_name": emp.name,
                        "full_name": emp.full_name,
                        "user_id": emp.user_id
                    })
                    
                    all_user_ids.add(emp.user_id)
                
                result["team_members"]["by_designation"] = designation_groups
                result["team_members"]["all_team_user_ids"] = list(all_user_ids)
                result["team_members"]["total_team_members"] = len(team_employees)
                result["team_members"]["designation_count"] = {
                    designation: len(members) 
                    for designation, members in designation_groups.items()
                }
            else:
                result["team_members"]["message"] = "Employee or team not found for purchase user email"
        else:
            result["team_members"]["message"] = "No purchase user email (email2) found in PO"
        
        return result
        
    except Exception as e:
        frappe.log_error(
            f"Error fetching vendor email for PO {po_number}: {str(e)}\n{frappe.get_traceback()}", 
            "Get Vendor Mails Error"
        )
        return {"status": "error", "message": str(e)}