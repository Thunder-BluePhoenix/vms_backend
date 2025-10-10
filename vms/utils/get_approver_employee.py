import frappe

from vms.utils.get_employee_for_cur_user import get_employee_name_for_cur_user



def get_approval_employee(role_short, company_list, filters={}, fields=["*"], doc=None, stage=None):
    """
    Main entry point for getting approval employees based on doctype
    """
    if doc and doc.get("doctype") == "Vendor Onboarding":
        return get_vendor_onboarding_approval_employee(role_short, company_list, doc, filters, fields, stage)
    
    if doc and doc.get("doctype") == "Cart Details":
        return get_card_details_approval_employee(role_short, doc, filters, fields, stage)
    
    return get_standard_approval_employee(role_short, company_list, filters, fields)

def get_card_details_approval_employee(role_short, doc, filters={}, fields=["*"], stage=None):
   
    try:
        # Get category type and purchase group from the document
        category_type = doc.get("category_type")
        purchase_group = doc.get("purchase_group")
        
        if not category_type or not purchase_group:
            frappe.log_error(
                f"Missing category_type or purchase_group in Cart Details: {doc.name}",
                "Cart Details Approval Employee Error"
            )
            return None
        

        current_user = frappe.session.user
        
        
        # Step 1: Validate category type - Check if current user is authorized for this category
        category_type_doc = frappe.get_doc("Category Master", category_type)
        
        
        purchase_team_user = category_type_doc.get("purchase_team_user")
        alternative_purchase_team = category_type_doc.get("alternative_purchase_team")
        
        # Check if current user matches the category type's authorized users
        is_category_authorized = (
            current_user == purchase_team_user or 
            current_user == alternative_purchase_team
        )
        
        
        if not is_category_authorized:
            frappe.log_error(
                f"Current user {current_user} is not authorized for category_type: {category_type}. "
                f"Authorized users: {purchase_team_user}, {alternative_purchase_team}",
                "Cart Details Approval Employee Error"
            )
            return None
        
        
        purchase_group_doc = frappe.get_doc("Purchase Group Master", purchase_group)
        required_team = purchase_group_doc.get("team")
        
        
        if not required_team:
            frappe.log_error(
                f"No team found in Purchase Group Master: {purchase_group}",
                "Cart Details Approval Employee Error"
            )
            return None
        
        # Step 3: Get users who have the required role
        users_with_role = frappe.get_all(
            "Has Role",
            filters={"role": role_short},
            fields=["parent"]
        )
        
        if not users_with_role:
            frappe.log_error(
                f"No users found with role: {role_short}",
                "Cart Details Approval Employee Error"
            )
            return None
        
        user_ids_with_role = [user.parent for user in users_with_role]
        
        
        # Step 4: Build filters for employee search
        # Match: required role + matching team + active status
        final_filters = {
            **filters,
            "user_id": ("in", user_ids_with_role),
            "team": required_team,
            "status": "Active"
        }
        
        # Get matching employees
        employee_list = frappe.get_all(
            "Employee",
            filters=final_filters,
            fields=fields,
            limit=1
        )
        
        if not employee_list:
            frappe.log_error(
                f"No active employees found with role: {role_short} and team: {required_team}",
                "Cart Details Approval Employee Error"
            )
            return None
        
        
        return employee_list[0]
        
    except frappe.DoesNotExistError as e:
        frappe.log_error(
            f"Master not found - Category Type: {category_type} or Purchase Group: {purchase_group}. Error: {str(e)}",
            "Cart Details Approval Employee Error"
        )
        return None
        
    except Exception as e:
        frappe.log_error(
            f"Error in get_card_details_approval_employee: {str(e)}\n{frappe.get_traceback()}",
            "Cart Details Approval Employee Error"
        )
        return None

def get_vendor_onboarding_approval_employee(role_short, company_list, doc, filters={}, fields=["*"], stage=None):

    registered_by_accounts_team = doc.get("register_by_account_team", 0)
    
  
    team_wise = stage.get("team_wise", 0) if stage else 0
    company_wise = stage.get("company_wise", 0) if stage else 0
    
    if team_wise and company_wise:
        return get_team_and_company_wise_approval_employee(role_short, company_list, doc, filters, fields)
    
    elif team_wise:
        return get_team_wise_approval_employee_for_vendor_onboarding(role_short, doc, filters, fields)
    
    elif company_wise:
        
        return get_standard_approval_employee(role_short, company_list, filters, fields)
    
    # No approval matrix checkboxes checked - use existing logic
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


def get_team_and_company_wise_approval_employee(role_short, company_list, doc, filters={}, fields=["*"]):
   
    try:
       
        reference_user = doc.get("registered_by")
        
        if not reference_user:
            frappe.log_error("No registered_by user found for team and company-wise approval")
            return None
            
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
        frappe.log_error(f"Error in get_team_and_company_wise_approval_employee: {str(e)}")
        return None

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
   
    frappe.logger("get_user_for_role_short").debug([name, role_short, depth])
    
    
    if depth > 5 or not name:
        return None

    try:
        employee = frappe.get_doc("Employee", name)
        
        if not employee:
            return None
        
        
        user_id = employee.get("user_id")
        
        if not user_id:
            
            return get_user_for_role_short(
                employee.get("reports_to", None), 
                role_short, 
                depth + 1
            )
        
        
        if check_cur_user or depth > 0:
            
            user_roles = frappe.get_roles(user_id)
            
        
            if role_short in user_roles:
                return {
                    "name": employee.name,
                    "user_id": user_id,
                    "employee_name": employee.get("employee_name"),
                    "status": employee.get("status"),
                }
        
        
        return get_user_for_role_short(
            employee.get("reports_to", None), 
            role_short, 
            depth + 1
        )
        
    except Exception as e:
        frappe.log_error(
            f"Error in get_user_for_role_short: {str(e)}\n{frappe.get_traceback()}",
            "Get User For Role Short Error"
        )
        return None


def get_fd_for_cur_user():
    return get_user_for_role_short(get_employee_name_for_cur_user(), "FD")
