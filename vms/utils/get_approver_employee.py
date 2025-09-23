import frappe

from vms.utils.get_employee_for_cur_user import get_employee_name_for_cur_user



def get_approval_employee(role_short, company_list, filters={}, fields=["*"], doc=None, stage=None):

    
    if doc and doc.get("doctype") == "Vendor Onboarding":
        return get_vendor_onboarding_approval_employee(role_short, company_list, doc, filters, fields, stage)
    
    return get_standard_approval_employee(role_short, company_list, filters, fields)


def get_vendor_onboarding_approval_employee(role_short, company_list, doc, filters={}, fields=["*"], stage=None):

    registered_by_accounts_team = doc.get("register_by_account_team", 0)
    
    if stage and stage.get("team_wise", 0):
        return get_team_wise_approval_employee_for_vendor_onboarding(role_short, doc, filters, fields)
    
    if registered_by_accounts_team:
        return get_standard_approval_employee(role_short, company_list, filters, fields)
    else:
        registered_by_user = doc.get("registered_by")
        
        if not registered_by_user:
            return get_standard_approval_employee(role_short, company_list, filters, fields)
        
        registered_employee = frappe.get_all(
            "Employee",
            filters={
                "user_id": registered_by_user,
                "status": "Active"
            },
            fields=["name", "multiple_purchase_heads", "team"],
            limit=1
        )
        
        if not registered_employee:
            return get_standard_approval_employee(role_short, company_list, filters, fields)
        
        registered_emp = registered_employee[0]
        team_checkbox_checked = registered_emp.get("multiple_purchase_heads", 0)
        employee_team = registered_emp.get("team")
        
        if team_checkbox_checked:
            return get_standard_approval_employee(role_short, company_list, filters, fields)
        else:
            return get_approval_employee_no_company(role_short, filters, fields, employee_team)


def get_team_wise_approval_employee_for_vendor_onboarding(role_short, doc, filters={}, fields=["*"]):
    """
    Get approval employee from the same team as the registered_by user (Vendor Onboarding only)
    """
    try:
        # Get the team of the registered_by user
        reference_user = doc.get("registered_by")
        
        if not reference_user:
            frappe.log_error("No registered_by user found for team-wise approval in Vendor Onboarding")
            return None
            
        # Get the team of the reference user
        reference_employee = frappe.get_all(
            "Employee",
            filters={"user_id": reference_user, "status": "Active"},
            fields=["team", "name"],
            limit=1
        )
        
        if not reference_employee:
            frappe.log_error(f"No active employee found for user: {reference_user}")
            return None
            
        team = reference_employee[0].get("team")
        if not team:
            frappe.log_error(f"No team assigned to employee of user: {reference_user}")
            return None
        
        # Get users with the required role
        users_with_role = frappe.get_all(
            "Has Role",
            filters={"role": role_short},
            fields=["parent"]
        )
        
        if not users_with_role:
            return None
        
        user_ids_with_role = [user.parent for user in users_with_role]
        
        # Build filters for team-based search
        final_filters = {
            **filters,
            "user_id": ("in", user_ids_with_role),
            "team": team,
            "status": "Active"
        }
        
        employee_list = frappe.get_all(
            "Employee", 
            filters=final_filters, 
            fields=fields, 
            limit=1
        )
        
        return employee_list[0] if employee_list else None
        
    except Exception as e:
        frappe.log_error(f"Error in get_team_wise_approval_employee_for_vendor_onboarding: {str(e)}")
        return None



def get_standard_approval_employee(role_short, company_list, filters={}, fields=["*"]):

    if isinstance(company_list, str):
        company_list = [company_list]


    employees_with_companies = frappe.get_all(
        "Multiple Company Name",  
        filters={"company_name": ("in", company_list)},  
        fields=["parent"],
        distinct=True
    )
    
    if not employees_with_companies:
        return None
    
    
    employee_names = [emp.parent for emp in employees_with_companies]
    
    # Get users who have the required role from Has Role child table
    users_with_role = frappe.get_all(
        "Has Role",
        filters={"role": role_short},
        fields=["parent"]
    )
    
    if not users_with_role:
        return None
    
    user_ids_with_role = [user.parent for user in users_with_role]
    
    final_filters = {
        **filters,
        "name": ("in", employee_names),
        "user_id": ("in", user_ids_with_role),  
        "status": "Active",  
    }
    
    employee_list = frappe.get_all(
        "Employee", 
        filters=final_filters, 
        fields=fields, 
        limit=1
    )
    
    return employee_list[0] if employee_list else None


def get_approval_employee_no_company(role_short, filters={}, fields=["*"],employee_team=None):
    
    users_with_role = frappe.get_all(
        "Has Role",
        filters={"role": role_short},
        fields=["parent"]
    )
    
    if not users_with_role:
        return None
    
    user_ids_with_role = [user.parent for user in users_with_role]
    
    
    final_filters = {
        **filters,
        "user_id": ("in", user_ids_with_role),  
        "team": employee_team,
        "status": "Active"
        
    }
    
    employee_list = frappe.get_all(
        "Employee", 
        filters=final_filters, 
        fields=fields, 
        limit=1
    )
    
    return employee_list[0] if employee_list else None

def get_approval_employee_by_state_for_rdm(
    state, role_short, company_list, filters={}, fields=["*"]
):
    emp_parent_dict = frappe.get_all(
        "Employee Select State",
        {"parenttype": "Employee", "state": state},
        "parent",
    )
    emp_parent = [item["parent"] for item in emp_parent_dict]
    filters = {
        **filters,
        "name": ("in", emp_parent),
        "is_active": 1,
    }
    employee_list = frappe.get_all(
        "Employee", filters=filters, fields=fields, limit=1
    )

    return employee_list[0] if employee_list else None


def get_user_for_role_short(name, role_short, depth=0, check_cur_user=False):
    frappe.logger("get_user_for_role_short").error([name, role_short, depth])
    # Check if maximum depth reached or employee not found
    if depth > 5 or not name:
        return None

    employee = frappe.get_doc("Employee", name)

    if (check_cur_user or depth > 0) and employee.get("role_short") == role_short:
        return employee

    return get_user_for_role_short(
        employee.get("reporting_head", None), role_short, depth + 1
    )


def get_fd_for_cur_user():
    return get_user_for_role_short(get_employee_name_for_cur_user(), "FD")
