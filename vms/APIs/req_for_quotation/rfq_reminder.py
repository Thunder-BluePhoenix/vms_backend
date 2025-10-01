import frappe
from frappe.utils import getdate, today
from frappe.utils import now_datetime
from vms.utils.custom_send_mail import custom_sendmail

# send reminder notification to vendor
def send_reminder_notification():
    today_date = getdate(today())

    req_quotations = frappe.get_all(
        "Request For Quotation",
        filters = {"quotation_rfq_deadline_pass" : 0, "revised_rfq": 0},
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

        <p>We request you to submit the details at the earliest. If you have already submitted, please ignore this message.</p>

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
        filters = {"revised_rfq": 0},
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


# Send a reminder email to the vendor one hour before the deadline to check how much of the quotation they have submitted

from datetime import datetime
import frappe

def quotation_count_reminder_mail():
    try:
        rfq_settings = frappe.get_doc("RFQ Settings")
        reminder_seconds = int(rfq_settings.vendor_filled_quotations_count or 3600)

        req_quotations = frappe.get_all(
            "Request For Quotation",
            filters={
                "quotation_rfq_deadline_pass": 0,
                "revised_rfq": 0,
            },
            fields=["name", "rfq_cutoff_date_logistic"]
        )

        now = datetime.now()
        now_seconds = now.hour * 3600 + now.minute * 60 + now.second

        for rfq_data in req_quotations:
            rfq_cutoff = rfq_data.get("rfq_cutoff_date_logistic")

            if rfq_cutoff:
                if isinstance(rfq_cutoff, str):
                    cutoff_dt = datetime.strptime(rfq_cutoff, "%Y-%m-%d %H:%M:%S")
                else:
                    cutoff_dt = rfq_cutoff 

                cutoff_seconds = cutoff_dt.hour * 3600 + cutoff_dt.minute * 60 + cutoff_dt.second
               
                diff = cutoff_seconds - now_seconds
                print(f"Now seconds: {now_seconds}, Cutoff seconds: {cutoff_seconds}, Diff: {diff}, name: {rfq_data.get("name")}")

                # Now you can compare diff with reminder_seconds (or any logic you want)
                if reminder_seconds > diff:
                    subject = f"RFQ Deadline Passed:"

                    message = f"""
                        <p>Dear Purchase Team,</p>

                        <p>Heelooooooo abhishek</p>

                        <p>Regards,<br>VMS Team</p>
                    """

                    frappe.custom_sendmail(
                        recipients="rishi.hingad@merillife.com",
                        subject=subject,
                        message=message,
                        now=True
                    )

    except Exception as e:
        frappe.log_error(f"Error in quotation_count_reminder_mail: {str(e)}")
        print(f"Error: {e}")




# apps/vms/vms/APIs/req_for_quotation/rfq_reminder.py

# vms.APIs.req_for_quotation.rfq_reminder.quotation_count_reminder_mail