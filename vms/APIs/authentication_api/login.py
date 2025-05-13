import frappe

def generate_keys(user):
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)
    
    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key
    else:
        api_key = user_details.api_key
    
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

    # Full name
    user_name = user.full_name or frappe.db.get_value("User", user.name, "full_name")

    # Linked Employee
    emp = frappe.get_value("Employee", {"user_id": user.name}, "name")
    emp_details = {}

    if emp:
        emp_details = frappe.get_value(
            "Employee",
            emp,
            ["designation", "company_email", "company"],
            as_dict=True
        )

    # Vendor Master
    vendor_master_ref_no = frappe.get_value("Vendor Master", {"office_email_primary": user.name}, "name")
    vendor_code = None

    if vendor_master_ref_no:
        vendor_data = frappe.get_value(
            "Vendor Master",
            vendor_master_ref_no,
            ["vendor_code"],
            as_dict=True
        )
        vendor_code = vendor_data.vendor_code

    # Company Details
    company_details = {}
    if emp_details.get("company"):
        company_details = frappe.get_value(
            "Company Master",
            emp_details.company,
            ["company_code", "company_short_form"],
            as_dict=True
        )

    # Final response
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
        "company": emp_details.get("company") if emp_details else None,
        "vendor_master_ref_no": vendor_master_ref_no,
        "vendor_code": vendor_code,
        "company_code": company_details.get("company_code") if company_details else None,
        "company_short_form": company_details.get("company_short_form") if company_details else None,
        "api_key": api_generate.get("api_key"),
        "api_secret": api_generate.get("api_secret")
    }


#  "designation_name": user_designation_name, --
#         "username": user.username,  --
#         "email": user.email,  --
#         "refno": refno,  --
#         "vendor_code": vendor_code, -- 
#         "full_name": user_name,  --
#         "company_code": company_code, --
#         "user_company": company_name,   --
#         "company_short_form": company_short =--