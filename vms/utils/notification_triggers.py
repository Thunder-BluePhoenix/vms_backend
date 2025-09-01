import frappe
from vms.utils.custom_send_mail import custom_sendmail
from vms.utils.verify_user import get_current_user_document


class NotificationTrigger:
    def __init__(self, context):
        self.context = context

    def send_email(self, recipients, template, cc_recepients=None):
        custom_send_mail(template, recipients, self.context, cc_recepients)


    def create_push_notification(self, redirect_url=None):
        frappe.enqueue(
            self.create_push_notification_in_background, redirect_url=redirect_url
        )

    def create_push_notification_in_background(self, redirect_url=None):

        # "from_user": frappe.session.user,
        # "for_user": recepient,
        # "doctype": self.doctype,
        # "document_name": self.name,
        # "user_document": self.distributor,
        # "subject": "Distrubutor Invoice Created",
        for_user = self.context.get("for_user")
        for_users = for_user if isinstance(for_user, list) else [for_user]
        for user in for_users:
            if frappe.db.exists("User", user):
                user_document, mobile_number = get_current_user_document(user)
                notification = frappe.get_doc(
                    {
                        "doctype": "Notification Log",
                        "subject": self.context.get("subject"),
                        "for_user": user,
                        "from_user": self.context.get("from_user"),
                        "type": "Alert",
                        "document_type": self.context.get("doctype"),
                        "email_content": self.context.get("subject"),
                        "read": 0,
                        "document_name": self.context.get("document_name"),
                        "link": redirect_url,
                        "custom_user_document": (
                            self.context.get("user_document")
                            if self.context.get("user_document")
                            else user_document or ""
                        ),
                    }
                )
                notification.save(ignore_permissions=True)
