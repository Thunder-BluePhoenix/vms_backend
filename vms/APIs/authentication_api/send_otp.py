from datetime import datetime
import random
import string
import frappe
from frappe.exceptions import DoesNotExistError
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
def send_otp(data):
    reciever_email = data.get('email')

    try:
        user = frappe.get_doc("User", reciever_email) or None
        api_credentials = generate_api_keys(user)

        api_key = api_credentials.get("api_key")
        api_secret = api_credentials.get("api_secret")
        auth = f"token {api_key}:{api_secret}"
        if user == None:
            return {
                "status": "error",
                "message": "No User found for the Mail ID"
            }
        
        otp = ''.join(random.choices(string.digits, k=6))

        otp_var = frappe.get_doc({
                                    "doctype":"OTP Verification",
                                    "email":reciever_email,
                                    "otp": otp
                                })
        
        otp_var.insert(ignore_permissions=True)
        
        
        vendor_name = frappe.db.get_value(
            "User",
            filters={'email': reciever_email},
            fieldname='full_name'
        )

        subject = "One Time Password for Password Reset"
        message = f"""
        Dear {vendor_name},

        Your One-Time Password for the Vendor Management System (VMS) Portal is {otp}.

        Regards,
        VMS Team
        """

        frappe.sendmail(
            recipients=[reciever_email],
            subject=subject,
            message=message,
        )

        # print(message)
        frappe.db.commit()


        return {
            "status": "success",
            "message": f"OTP sent to {reciever_email}",
            "Authorization": f"token {api_key}:{api_secret}"
        }

    except DoesNotExistError:
        user_message = f"User {reciever_email} does not exist."
        frappe.log_error(user_message, _("User not found"))
        return {
            "status": "fail",
            "message": user_message
        }
