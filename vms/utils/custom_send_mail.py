import frappe
import smtplib
from email.message import EmailMessage


def custom_sendmail(recipients=None, subject=None, message=None, cc=None, bcc=None, **kwargs):
    """
    Enhanced sendmail function with CC/BCC support
    Drop-in replacement for frappe.sendmail with same parameters
    """
    
    # If no CC or BCC, use standard frappe.sendmail
    if not cc and not bcc:
        return frappe.sendmail(
            recipients=recipients,
            subject=subject, 
            message=message,
            **kwargs
        )
    
    
    if kwargs.get('now', False):
     
        _send_email_with_cc_bcc(
            subject=subject,
            body=message,
            to_emails=_normalize_recipients(recipients),
            cc_emails=_normalize_recipients(cc),
            bcc_emails=_normalize_recipients(bcc)
        )
    else:
    
        frappe.enqueue(
            method=_send_email_with_cc_bcc,
            subject=subject,
            body=message,
            to_emails=_normalize_recipients(recipients),
            cc_emails=_normalize_recipients(cc),
            bcc_emails=_normalize_recipients(bcc)
        )


def _send_email_with_cc_bcc(subject, body, to_emails, cc_emails=None, bcc_emails=None):
    
    cc_emails = cc_emails or []
    bcc_emails = bcc_emails or []
    

    if not bcc_emails:
        try:
            email_account = frappe.get_doc("Email Account", {"email_id": "noreply@merillife.com"})
            if email_account and hasattr(email_account, 'always_bcc') and email_account.always_bcc:
                if isinstance(email_account.always_bcc, str):
                    bcc_emails = [email.strip() for email in email_account.always_bcc.split(',') if email.strip()]
                else:
                    bcc_emails = email_account.always_bcc
                    
                frappe.logger("debug").info(f"Using always_bcc from Email Account: {bcc_emails}")
        except Exception as e:
        
            frappe.logger("debug").info(f"Could not get always_bcc from Email Account: {str(e)}")
    
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "noreply@merillife.com"
    msg["To"] = ", ".join(to_emails)
    
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
    
    # BCC is not added to headers (that's the point of BCC)
    msg.add_alternative(body, subtype="html")
    
    # All recipients for SMTP (TO + CC + BCC)
    all_recipients = to_emails + cc_emails + bcc_emails
    
    frappe.logger("debug").info(f"Sending email to: TO={to_emails}, CC={cc_emails}, BCC={bcc_emails}")

    try:
        with smtplib.SMTP_SSL("smtp.zeptomail.in", 465) as server:
            server.login("noreply@merillife.com", "4sxLpHrd3YNj__29edd5373fd7a")
            server.send_message(
                msg, from_addr="noreply@merillife.com", to_addrs=all_recipients
            )
            
            # Create Email Queue record with system permissions (bypass user permissions)
            try:
                # Method 1: Use ignore_permissions flag
                frappe.flags.ignore_permissions = True
                
                email_queue = frappe.get_doc(
                    {
                        "doctype": "Email Queue",
                        "subject": subject,
                        "message": body,
                        "status": "Sent",
                        "show_as_cc": ",".join(cc_emails) if cc_emails else "",
                        "sender": "noreply@merillife.com"
                    }
                )
                
                # Add all recipients to the queue record
                for recipient in all_recipients:
                    email_queue.append("recipients", {"recipient": recipient, "status": "Sent"})
                
                # Insert with ignore permissions
                email_queue.insert(ignore_permissions=True)
                
            except Exception as eq_error:
                # Method 2: Try with set_user context
                try:
                    original_user = frappe.session.user
                    frappe.set_user("Administrator")
                    
                    email_queue = frappe.get_doc(
                        {
                            "doctype": "Email Queue",
                            "subject": subject,
                            "message": body,
                            "status": "Sent",
                            "show_as_cc": ",".join(cc_emails) if cc_emails else "",
                            "sender": "noreply@merillife.com"
                        }
                    )
                    
                    for recipient in all_recipients:
                        email_queue.append("recipients", {"recipient": recipient, "status": "Sent"})
                    
                    email_queue.insert()
                    
                except Exception as admin_error:
                    # Method 3: Just log that email was sent without Email Queue
                    frappe.logger("debug").info(f"Email sent but couldn't create Email Queue record: {str(admin_error)}")
                finally:
                    # Reset user context
                    frappe.set_user(original_user)
                
            finally:
                # Reset permissions
                frappe.flags.ignore_permissions = False
            
            frappe.logger("debug").info(f"Email sent successfully to {len(all_recipients)} recipients (TO: {len(to_emails)}, CC: {len(cc_emails)}, BCC: {len(bcc_emails)})")
            
    except Exception as e:
        frappe.logger("debug").error(f"Failed to send email with CC/BCC: {e}")
        frappe.log_error(frappe.get_traceback(), f"Error sending email with CC/BCC: {str(e)}")


def _normalize_recipients(recipients):
    """Convert recipients to a list format"""
    if not recipients:
        return []
    if isinstance(recipients, str):
        return [recipients]
    return recipients if isinstance(recipients, list) else [recipients]


# Add this to frappe namespace so you can call frappe.custom_sendmail()
frappe.custom_sendmail = custom_sendmail