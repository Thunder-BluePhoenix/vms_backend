import frappe
from frappe.utils import now_datetime, get_datetime

def sent_asa_form_link():
    try:
        ass_form_settings = frappe.get_single("Assessment Form Settings")
        asa_duration_sec = int(ass_form_settings.asa_form_period or 0)  # already in seconds

        if not asa_duration_sec:
            print("ASA form period not set.")
            return

        vendor_masters = frappe.get_all(
            "Vendor Master",
            fields=["name", "vendor_name", "office_email_primary", "office_email_secondary"]
        )

        for vendor in vendor_masters:
            vm_doc = frappe.get_doc("Vendor Master", vendor.name)

            if not vm_doc.form_records:
                continue  # No ASA submissions yet

            # Get the latest row based on date_time
            latest_row = max(vm_doc.form_records, key=lambda row: row.date_time)
            prev_datetime = get_datetime(latest_row.date_time)

            # Calculate time diff in seconds
            time_since_last = (now_datetime() - prev_datetime).total_seconds()

            if time_since_last >= asa_duration_sec:
                http_server = frappe.conf.get("backend_http")
                subject = "ASA Form Reminder"
                link = f"{http_server}/annual-supplier-assessment-questionnaire/new?vendor_ref_no={vm_doc.name}"

                message = f"""
                    Hello {vm_doc.vendor_name},<br><br>
                    Our records show your ASA form has not been updated in the required time.<br>
                    Please fill out the form using the link below:<br>
                    <a href="{link}">{link}</a><br><br>
                    Thank you.<br><br>
                    Regards,<br>
                    Team VMS
                """

                recipients = vm_doc.office_email_primary or vm_doc.office_email_secondary
                if recipients:
                    frappe.sendmail(
                        recipients=recipients,
                        subject=subject,
                        message=message
                    )
                    print(f"Reminder sent to {vm_doc.name}")
                else:
                    print(f"No recipient found for {vm_doc.name}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "ASA Reminder Cron Job Failed")
