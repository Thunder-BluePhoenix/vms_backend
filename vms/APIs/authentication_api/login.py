import frappe

def generate_keys(user):
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)
    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key
    else:
        api_key = user_details.api_key  # Ensure api_key is fetched if already exists
    user_details.api_secret = api_secret
    user_details.save()

    return {
        "api_key": api_key,
        "api_secret": api_secret
    }

@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
    frappe.logger("login").error("Login Method----")
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Authentication Error!"
        }
        return
    # Generate API keys
    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)
    
    # Fetch additional details
    user_name = user.full_name or frappe.db.get_value("User", user.name, "full_name")
     
    # Get employee linked to user
    emp = frappe.get_value("Employee", {"user_id": user.name}, "name")
    
    emp_details = {}
    if emp:
        emp_details = frappe.get_value(
            "Employee",
            emp,
            ["designation", "company_email", "company"],
            as_dict=True
        )
    
    frappe.response["message"] = {
        "success_key": 1,
        "message": "Authentication success",
        "email": user.email,
        "sid": frappe.session.sid,
        "username": user.username,
        "full_name": user_name,
        "employee": emp,
        "designation": emp_details.get("designation") if emp_details else None,
        "company_email": emp_details.get("company_email") if emp_details else None,
        "company": emp_details.get("company") if emp_details else None
    }


