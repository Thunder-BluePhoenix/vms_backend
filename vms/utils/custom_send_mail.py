import frappe
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import mimetypes




def custom_sendmail(recipients=None, subject=None, message=None, cc=None, bcc=None, attachments=None, **kwargs):
   
   
  
    if not cc and not bcc and not attachments:
        
        try:
            email_account = frappe.get_doc("Email Account", {"email_id": "noreply@merillife.com"})
            has_always_bcc = email_account and hasattr(email_account, 'always_bcc') and email_account.always_bcc
        except:
            has_always_bcc = False
        
        # If no CC, no BCC, no attachments, and no always_bcc, use standard frappe.sendmail
        if not has_always_bcc:
            return frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=message,
                attachments=attachments,
                **kwargs
            )
   
   
    if kwargs.get('now', False):
        _send_email_with_cc_bcc_attachments(
            subject=subject,
            body=message,
            to_emails=_normalize_recipients(recipients),
            cc_emails=_normalize_recipients(cc),
            bcc_emails=_normalize_recipients(bcc),
            attachments=attachments
        )
    else:
        frappe.enqueue(
            method=_send_email_with_cc_bcc_attachments,
            subject=subject,
            body=message,
            to_emails=_normalize_recipients(recipients),
            cc_emails=_normalize_recipients(cc),
            bcc_emails=_normalize_recipients(bcc),
            attachments=attachments
        )


def _send_email_with_cc_bcc_attachments(subject, body, to_emails, cc_emails=None, bcc_emails=None, attachments=None):
   
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
   
    # Use MIMEMultipart for emails with attachments
    if attachments:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = formataddr(("VMS", "noreply@merillife.com"))
        msg["To"] = ", ".join(to_emails)
       
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
       
        # Add HTML body
        msg.attach(MIMEText(body, 'html'))
       
        # Process attachments
        _add_attachments_to_message(msg, attachments)
       
    else:
        # Use EmailMessage for simple emails without attachments
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = formataddr(("VMS", "noreply@merillife.com"))
        msg["To"] = ", ".join(to_emails)
       
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
       
        msg.add_alternative(body, subtype="html")
   
    # All recipients for SMTP (TO + CC + BCC)
    all_recipients = to_emails + cc_emails + bcc_emails
   
    frappe.logger("debug").info(f"Sending email to: TO={to_emails}, CC={cc_emails}, BCC={bcc_emails}, Attachments={len(attachments) if attachments else 0}")

    try:
        with smtplib.SMTP_SSL("smtp.zeptomail.in", 465) as server:
            server.login("noreply@merillife.com", "4sxLpHrd3YNj__29edd5373fd7a")
           
            # Send the message
            server.send_message(msg, to_addrs=all_recipients)
           
            # Create Email Queue record with system permissions
            try:
                frappe.flags.ignore_permissions = True
               
                email_queue = frappe.get_doc(
                    {
                        "doctype": "Email Queue",
                        "subject": subject,
                        "message": body,
                        "status": "Sent",
                        "show_as_cc": ",".join(cc_emails) if cc_emails else "",
                        "sender": "noreply@merillife.com",
                        "sender_full_name": "VMS",
                    }
                )
               
                # Add all recipients to the queue record
                for recipient in all_recipients:
                    email_queue.append("recipients", {"recipient": recipient, "status": "Sent"})
               
                # Add attachments to Email Queue record if any
                if attachments:
                    _add_attachments_to_email_queue(email_queue, attachments)
               
                # Insert with ignore permissions
                email_queue.insert(ignore_permissions=True)
               
            except Exception as eq_error:
                # Fallback methods for Email Queue creation
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
                            "sender": "noreply@merillife.com",
                            "sender_full_name": "VMS",
                        }
                    )
                   
                    for recipient in all_recipients:
                        email_queue.append("recipients", {"recipient": recipient, "status": "Sent"})
                   
                    if attachments:
                        _add_attachments_to_email_queue(email_queue, attachments)
                   
                    email_queue.insert()
                   
                except Exception as admin_error:
                    frappe.logger("debug").info(f"Email sent but couldn't create Email Queue record: {str(admin_error)}")
                finally:
                    frappe.set_user(original_user)
               
            finally:
                frappe.flags.ignore_permissions = False
           
            attachment_count = len(attachments) if attachments else 0
            frappe.logger("debug").info(f"Email sent successfully to {len(all_recipients)} recipients (TO: {len(to_emails)}, CC: {len(cc_emails)}, BCC: {len(bcc_emails)}) with {attachment_count} attachments")
           
    except Exception as e:
        frappe.logger("debug").error(f"Failed to send email with CC/BCC/attachments: {e}")
        frappe.log_error(frappe.get_traceback(), f"Error sending email with CC/BCC/attachments: {str(e)}")


def _add_attachments_to_message(msg, attachments):
    """Add attachments to the email message"""
    if not attachments:
        return
   
    # Handle different attachment formats
    processed_attachments = _process_attachments(attachments)
   
    for attachment in processed_attachments:
        try:
            # Get file content and info
            file_content = attachment.get('fcontent') or attachment.get('content')
            filename = attachment.get('fname') or attachment.get('filename', 'attachment')
           
            if file_content:
                # Guess the content type based on the filename
                content_type, encoding = mimetypes.guess_type(filename)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
               
                main_type, sub_type = content_type.split('/', 1)
               
                # Create MIMEBase object
                part = MIMEBase(main_type, sub_type)
                part.set_payload(file_content)
               
                # Encode file in ASCII characters to send by email
                encoders.encode_base64(part)
               
                # Add header as key/value pair to attachment part
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}',
                )
               
                # Attach the part to message
                msg.attach(part)
               
        except Exception as e:
            frappe.logger("debug").error(f"Failed to attach file {filename}: {str(e)}")


def _add_attachments_to_email_queue(email_queue, attachments):
    """Add attachments to Email Queue record"""
    if not attachments:
        return
   
    try:
        processed_attachments = _process_attachments(attachments)
       
        # Create a comma-separated string of filenames for Email Queue
        attachment_names = []
        for attachment in processed_attachments:
            filename = attachment.get('fname') or attachment.get('filename', 'attachment')
            if filename:
                attachment_names.append(filename)
       
        # Set attachments as a comma-separated string (not a list)
        if attachment_names:
            email_queue.attachments = ", ".join(attachment_names)
           
    except Exception as e:
        frappe.logger("debug").error(f"Failed to add attachments to Email Queue: {str(e)}")


def _process_attachments(attachments):
    """Process attachments into a consistent format"""
    if not attachments:
        return []
   
    processed = []
   
    # Handle different attachment formats that frappe.sendmail accepts
    if isinstance(attachments, dict):
        # Single attachment as dict
        processed.append(attachments)
    elif isinstance(attachments, list):
        for attachment in attachments:
            if isinstance(attachment, dict):
                processed.append(attachment)
            elif isinstance(attachment, str):
                # If it's a file path, read the file
                try:
                    if os.path.exists(attachment):
                        with open(attachment, 'rb') as f:
                            content = f.read()
                        processed.append({
                            'fname': os.path.basename(attachment),
                            'fcontent': content
                        })
                except Exception as e:
                    frappe.logger("debug").error(f"Failed to read attachment file {attachment}: {str(e)}")
            elif hasattr(attachment, 'file_name') and hasattr(attachment, 'content'):
                # Frappe File object
                processed.append({
                    'fname': attachment.file_name,
                    'fcontent': attachment.content
                })
   
    return processed


def _normalize_recipients(recipients):
    """Convert recipients to a list format"""
    if not recipients:
        return []
    if isinstance(recipients, str):
        return [recipients]
    return recipients if isinstance(recipients, list) else [recipients]



frappe.custom_sendmail = custom_sendmail