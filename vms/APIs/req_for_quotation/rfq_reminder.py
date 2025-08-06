import frappe
from frappe.utils import getdate, today
from frappe.utils import now_datetime

# send reminder notification to vendor
def send_reminder_notification():
    today_date = getdate(today())

    req_quotations = frappe.get_all(
        "Request For Quotation",
        fields=["name", "first_reminder", "second_reminder", "third_reminder"]
    )

    for rfq_data in req_quotations:
        rfq = frappe.get_doc("Request For Quotation", rfq_data.name)

        reminder_type = None
        if rfq.first_reminder == today_date:
            reminder_type = "First"
        elif rfq.second_reminder == today_date:
            reminder_type = "Second"
        elif rfq.third_reminder == today_date:
            reminder_type = "Final"

        # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", reminder_type)

        if not reminder_type:
            continue

        subject = f"{reminder_type} Reminder: Please Submit Quotation for {rfq.name}"
        body = f"""
            <p>Dear Vendor,</p>
            <p>This is a gentle reminder to fill in the quotation details for RFQ <b>{rfq.name}</b>.</p>
            <p>Please complete it as soon as possible. If you have already submitted, please ignore this email.</p>
            <p>Thank you.</p>
        """

        sent = False

        for row in rfq.vendor_details:
            if row.office_email_primary and row.mail_sent:
                frappe.sendmail(
                    recipients=row.office_email_primary,
                    subject=subject,
                    message=body,
                    now=True
                )
                frappe.logger().info(f"Sent {reminder_type} reminder to {row.office_email_primary}")
                sent = True

        for row in rfq.non_onboarded_vendor_details:
            if row.office_email_primary and row.mail_sent:
                frappe.sendmail(
                    recipients=row.office_email_primary,
                    subject=subject,
                    message=body,
                    now=True
                )
                frappe.logger().info(f"Sent {reminder_type} reminder to {row.office_email_primary}")
                sent = True

        if not sent:
            frappe.logger().info(f"No eligible vendors for {rfq.name}")


# block the quotation link after passing rfq cut off date or quotation deadline
def block_quotation_link():
    current_time = now_datetime()

    req_quotations = frappe.get_all(
        "Request For Quotation",
        fields=["name", "rfq_cutoff_date_logistic"]
    )
    for rfq_data in req_quotations:
        deadline = rfq_data.rfq_cutoff_date_logistic 


        if deadline and deadline < current_time:
            frappe.db.set_value(
                "Request For Quotation",
                rfq_data.name,
                "quotation_rfq_deadline_pass",
                1
            )

        return {
            "status": "Success",
            "message": f"RFQ Cutoff Date or Quotation Deadline has passed. Now Quotation won't be create for {rfq_data.name}."
        }
