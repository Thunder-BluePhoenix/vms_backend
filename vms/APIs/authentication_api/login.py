import frappe
from frappe import _

def generate_api_keys(user):
    
    user_doc = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=32) 
    if not user_doc.api_key:
        api_key = frappe.generate_hash(length=32)  
        user_doc.api_key = api_key
    else:
        api_key = user_doc.api_key
    
    # Save the updated secret
    user_doc.api_secret = api_secret
    user_doc.save(ignore_permissions=True)
    
    return {
        "api_key": api_key,
        "api_secret": api_secret
    }

@frappe.whitelist(allow_guest=True)
def login(data):
    try:
        if not data or not isinstance(data, dict):
            frappe.throw(_("Invalid request format"))

        usr = data.get("usr")
        pwd = data.get("pwd")

        if not usr or not pwd:
            frappe.throw(_("Username and password are required"))

        # Authenticate user
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

        api_credentials = generate_api_keys(frappe.session.user)

        # Build user response
        user_response = build_user_response(frappe.session.user, api_credentials)

        # --- Set Cookies in Response ---
        frappe.local.response["type"] = "json"
        frappe.local.response["message"] = {"success": True, "message": _("Authentication successful")}

        # Set cookies - you can customize secure and httpOnly flags as needed
        frappe.local.response["cookies"] = {
            "sid": {
                "value": frappe.session.sid,
                "httponly": True,
                "secure": 1,  # set to 1 if using HTTPS
                "path": "/",
                "samesite": "Lax"
            },
            "api_key": {
                "value": api_credentials.get("api_key"),
                "httponly": False,
                "secure": 1,
                "path": "/",
                "samesite": "Lax"
            },
            "api_secret": {
                "value": api_credentials.get("api_secret"),
                "httponly": False,
                "secure": 1,
                "path": "/",
                "samesite": "Lax"
            }
        }

        return  user_response# No need to explicitly return the response body
                

    except frappe.exceptions.AuthenticationError:
        frappe.local.response["message"] = {
            "success": False,
            "message": _("Invalid username or password")
        }
        frappe.local.response.http_status_code = 401
        return

    except Exception as e:
        frappe.logger().error(f"Login error: {str(e)}")
        frappe.local.response["message"] = {
            "success": False,
            "message": _("An error occurred during authentication")
        }
        frappe.local.response.http_status_code = 500
        return





def build_user_response(user, api_credentials):
    """
    Build comprehensive user response with relevant details.
    
    Args:
        user (str): User ID
        api_credentials (dict): API key and secret
        
    Returns:
        dict: User details and credentials
    """
    user_doc = frappe.get_doc('User', user)
    user_name = user_doc.full_name or frappe.db.get_value("User", user, "full_name")
    
    # Get employee details if linked
    employee_id = frappe.get_value("Employee", {"user_id": user}, "name")
    employee_details = {}
    
    if employee_id:
        employee_details = frappe.get_value(
            "Employee",
            employee_id,
            ["designation", "company_email", "company"],
            as_dict=True
        ) or {}
    
    # Get vendor details if applicable
    vendor_id = frappe.get_value("Vendor Master", {"office_email_primary": user}, "name")
    
    # Get company details if available
    company_details = {}
    if employee_details.get("company"):
        company_details = frappe.get_value(
            "Company Master",
            employee_details.get("company"),
            ["company_code", "company_short_form"],
            as_dict=True
        ) or {}
    
    # Construct response
    response = {
        "success": True,
        "message": _("Authentication successful"),
        "user": {
            "email": user_doc.email,
            "username": user_doc.username,
            "full_name": user_name,
            "sid": frappe.session.sid,
        },
        "api_credentials": {
            "api_key": api_credentials.get("api_key"),
            "api_secret": api_credentials.get("api_secret")
        },
        "employee": {
            "id": employee_id,
            "designation": employee_details.get("designation"),
            "company_email": employee_details.get("company_email"),
        },
        "company": {
            "id": employee_details.get("company"),
            "code": company_details.get("company_code"),
            "short_form": company_details.get("company_short_form")
        },
        "vendor": {
            "id": vendor_id
        }
    }
    
    frappe.response["message"] = response
    return response




#  "designation_name": user_designation_name, --
#         "username": user.username,  --
#         "email": user.email,  --
#         "refno": refno,  --
#         "vendor_code": vendor_code, -- 
#         "full_name": user_name,  --
#         "company_code": company_code, --
#         "user_company": company_name,   --
#         "company_short_form": company_short =--


# @frappe.whitelist(allow_guest=True)
# def reset_pwd(data):
#     usr = data.get("usr")
#     new_pwd = data.get("new_pwd")
#     user = frappe.get_doc("User", usr)

#     user.new_password = new_pwd

#     user.save()
#     frappe.db.commit()



@frappe.whitelist(allow_guest=True)
def reset_pwd(data):
    try:
        if not isinstance(data, dict):
            return {"status": "error", "message": "Invalid data format"}
            
        usr = data.get("usr")
        new_pwd = data.get("new_pwd")
        
        if not usr or not new_pwd:
            return {"status": "error", "message": "Missing required fields: 'usr' and 'new_pwd'"}
        
        if not frappe.db.exists("User", usr):
            frappe.log_error(f"Password reset attempted for non-existent user: {usr}", "Security")
            return {"status": "error", "message": "Password reset failed"}
        
        if len(new_pwd) < 8:
            return {"status": "error", "message": "Password must be at least 8 characters long"}
            
        user = frappe.get_doc("User", usr)
        
        if user.enabled == 0:
            frappe.log_error(f"Password reset attempted for disabled user: {usr}", "Security")
            return {"status": "error", "message": "Password reset failed"}
        
        user.new_password = new_pwd
        
        user.save(ignore_permissions=False)
        frappe.db.commit()
        
        frappe.log_error(f"Password reset successful for user: {usr}", "Security Info")
        
        return {
            "status": "success",
            "message": "Password has been reset successfully"
        }
        
    except frappe.PermissionError:
        frappe.db.rollback()
        frappe.log_error(f"Permission error during password reset for user: {usr}", "Security")
        return {"status": "error", "message": "You don't have permission to perform this action"}
        
    except frappe.ValidationError as e:
        frappe.db.rollback()
        return {"status": "error", "message": str(e)}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error resetting password: {str(e)}", "Password Reset Error")
        return {"status": "error", "message": "An unexpected error occurred during password reset"}

