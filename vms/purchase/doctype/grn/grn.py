import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now_datetime, format_datetime
from vms.utils.custom_send_mail import custom_sendmail


class GRN(Document):

    # def after_insert(self):
    #     self.send_grn_notification(action="created")
        
    #     self._notification_sent = True

    def on_update(self):

        self.set_sap_status()
      
        # if hasattr(self, '_notification_sent') and self._notification_sent:
        #     self._notification_sent = False  
        #     return
            
        # if not self.is_new():
        #     self.send_grn_notification(action="updated")


    def send_grn_notification(self, action="updated"):
        try:
            recipients = self.get_team_recipients()
            

            if not recipients:
                frappe.log_error("No recipients found for GRN notification", "GRN Notification")
                return

            subject = f"GRN {action.title()}: {self.name} - Please Review"
            message = self.prepare_notification_message(action)

            
            frappe.custom_sendmail(
                recipients=recipients,
                subject=subject,
                message=message,
                now=True
            )

            frappe.logger().info(
                f"GRN notification sent to {len(recipients)} recipients for {action} of {self.name}"
            )

        except Exception as e:
            frappe.log_error(f"Error sending GRN notification: {str(e)}", "GRN Notification Error")

    def get_team_recipients(self):
        recipients = []
        target_role_profiles = ["Purchase Team", "Accounts Team"]

        try:
            employees_with_role_profiles = frappe.get_all(
                "Employee",
                filters={
                    "designation": ["in", target_role_profiles],
                    "status": "Active",
                    "user_id": ["is", "set"]
                },
                fields=["name", "first_name", "user_id", "designation"]
            )

            for employee in employees_with_role_profiles:
                if employee.user_id:
                    user_email = frappe.db.get_value("User", employee.user_id, "email")
                    if user_email and user_email not in recipients:
                        recipients.append(user_email)

            return recipients

        except Exception as e:
            frappe.log_error(f"Error getting team recipients: {str(e)}")
            return []

    def prepare_notification_message(self, action):
        """Prepare the email notification message"""
        action_text = "created" if action == "created" else "updated"
        
        message = f"""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: #2c3e50; margin-top: 0;">
                GRN List {action_text.title()} Notification
            </h2>
            <p style="color: #7f8c8d; margin-bottom: 0;">
                The GRN list has been {action_text}. Please review the updated information.
            </p>
        </div>
        
        <div style="background: #ffffff; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                GRN Information
            </h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #2c3e50; width: 30%;">GRN Number:</td>
                    <td style="padding: 8px 0; color: #34495e;">{self.name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #2c3e50; width: 30%;">Status:</td>
                    <td style="padding: 8px 0; color: #34495e;">{action_text.title()}</td>
                </tr>
            </table>
        </div>
        
        <div style="background: #e8f6ff; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db;">
            <p style="margin: 0; color: #2c3e50;">
                <strong>Action Required:</strong><br>
                Please review the GRN list and take necessary actions as per your department responsibilities.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
            <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                This is an automated notification from the ERP System.<br>
                Please do not reply to this email.
            </p>
        </div>
    </div>"""
        
        return message

    def set_sap_status(self):
        if self.sap_booking_id and self.miro_no:
            self.db_set("sap_status", "Closed")
        else:
            self.db_set("sap_status", "Open")