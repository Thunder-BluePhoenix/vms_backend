import random
import string
import frappe
from frappe.exceptions import DoesNotExistError
from frappe import _

@frappe.whitelist(allow_guest=True)
def send_otp(**kwargs):
    reciever_email = kwargs.get('email')

    try:
        user = frappe.get_doc("User", reciever_email)
        
        otp = ''.join(random.choices(string.digits, k=6))
        
        
        subject = "One Time Password for Password Reset"
        message = f"""
        Dear,

        Your One-Time Password for the Vendor Management System (VMS) Portal is {otp}.

        Regards,
        VMS Team
        """

        frappe.sendmail(
            recipients=[reciever_email],
            subject=subject,
            message=message,
        )

        print(message)

        return {
            "status": "success",
            "message": f"OTP sent to {reciever_email}"
        }

    except DoesNotExistError:
        user_message = f"User {reciever_email} does not exist."
        frappe.log_error(user_message, _("User not found"))
        return {
            "status": "fail",
            "message": user_message
        }
