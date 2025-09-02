import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_vendor_multi_company(v_primary_mail):
    try:
        vendor_master = frappe.get_doc("Vendor Master", {"office_email_primary": v_primary_mail})
        
        # Get all table data
        table_data = [row.as_dict() for row in vendor_master.multiple_company_data]
        
        # Get unique company names
        company_names = list(set([row.get('company_name') for row in table_data if row.get('company_name')]))
        
        # Bulk fetch company master data
        company_master_data = {}
        if company_names:
            companies = frappe.get_all(
                "Company Master",
                filters={"name": ["in", company_names]},
                fields="*"
            )
            company_master_data = {company['name']: company for company in companies}
        
        # Add company master data to each row
        for row in table_data:
            if row.get('company_name'):
                row['company_master_data'] = company_master_data.get(row['company_name'])
            else:
                row['company_master_data'] = None
        
        return {
            "success": True,
            "data": table_data,
            "vendor_master_id": vendor_master.name
        }
        
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": f"Vendor not found with email: {v_primary_mail}",
            "data": []
        }
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_multi_company: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=True)
def get_vendor_onb_via_company(v_id, company):
    try:
        onb = frappe.get_all(
            "Vendor Onboarding", 
            {"ref_no": v_id, "company_name": company},
            ["name", "onboarding_form_status"]
        )
        
        return {
            "success": True,
            "data": onb
        } if onb else {
            "success": False,
            "message": "No records found",
            "data": []
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_onb_via_company: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "data": []
        }