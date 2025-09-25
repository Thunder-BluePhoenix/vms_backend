import frappe
from frappe.utils import getdate, today
from frappe.utils import now_datetime
from vms.utils.custom_send_mail import custom_sendmail

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

        <p>This is a gentle reminder to complete the quotation details for RFQ <b>{rfq.name}</b>.</p>

        <p>We request you to submit the details at the earliest. If you have already submitted, please disregard this message.</p>

        <p>Thank you.<br>
        Best regards,<br>
        VMS Team</p>
        """


        sent = False

        for row in rfq.vendor_details:
            if row.office_email_primary and row.mail_sent:
                frappe.custom_sendmail(
                    recipients=row.office_email_primary,
                    subject=subject,
                    message=body,
                    now=True
                )
                frappe.logger().info(f"Sent {reminder_type} reminder to {row.office_email_primary}")
                sent = True

        for row in rfq.non_onboarded_vendor_details:
            if row.office_email_primary and row.mail_sent:
                frappe.custom_sendmail(
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
        fields=["name", "rfq_cutoff_date_logistic", "raised_by", "quotation_rfq_deadline_pass"]
    )

    updated_rfqs = []

    for rfq in req_quotations:
        if rfq.quotation_rfq_deadline_pass:
            continue

        if rfq.rfq_cutoff_date_logistic and rfq.rfq_cutoff_date_logistic < current_time:
            frappe.db.set_value(
                "Request For Quotation",
                rfq.name,
                "quotation_rfq_deadline_pass",
                1
            )

            subject = f"RFQ Deadline Passed: {rfq.name}"

            message = f"""
                <p>Dear Purchase Team,</p>

                <p>The Request for Quotation <strong>{rfq.name}</strong> has passed its submission deadline 
                (<strong>{rfq.rfq_cutoff_date_logistic.strftime('%d %B %Y, %I:%M %p')}</strong>).</p>

                <p>Please review the received quotations and take the necessary actions. 
                The system has automatically marked this RFQ as expired.</p>

                <p>Regards,<br>VMS Team</p>
            """

            frappe.custom_sendmail(
                recipients=rfq.raised_by,
                subject=subject,
                message=message,
                now=True
            )

            updated_rfqs.append(rfq.name)

    return {
        "status": "Success",
        "message": f"Processed {len(updated_rfqs)} expired RFQs: {', '.join(updated_rfqs)}"
    }
