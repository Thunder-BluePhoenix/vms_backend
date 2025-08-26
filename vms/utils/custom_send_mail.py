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


def _get_email_account_settings(email_id="noreply@merillife.com"):
    try:
        email_account = frappe.get_doc("Email Account", {"email_id": email_id})
        
        settings = {
            'email_id': email_account.email_id,
            'smtp_server': email_account.smtp_server or "smtp.zeptomail.in",
            'smtp_port': email_account.smtp_port or 465,
            'use_ssl': getattr(email_account, 'use_ssl', True),
            'use_tls': getattr(email_account, 'use_tls', False),
            'password': email_account.get_password(),
            'sender_name': getattr(email_account, 'sender_name', 'VMS'),
            'always_bcc': getattr(email_account, 'always_bcc', None)
        }
        
        frappe.logger("debug").info(f"Email account settings retrieved for {email_id}")
        return settings
        
    except Exception as e:
        frappe.logger("debug").error(f"Failed to get email account settings for {email_id}: {str(e)}")
        return {
            'email_id': email_id,
            'smtp_server': "smtp.zeptomail.in",
            'smtp_port': 465,
            'use_ssl': True,
            'use_tls': False,
            'password': None,
            'sender_name': 'VMS',
            'always_bcc': None
        }


def _send_email_with_cc_bcc_attachments(subject, body, to_emails, cc_emails=None, bcc_emails=None, attachments=None):
   
    cc_emails = cc_emails or []
    bcc_emails = bcc_emails or []
    
    email_settings = _get_email_account_settings()
    
    # Handle always_bcc
    if not bcc_emails and email_settings['always_bcc']:
        if isinstance(email_settings['always_bcc'], str):
            bcc_emails = [email.strip() for email in email_settings['always_bcc'].split(',') if email.strip()]
        else:
            bcc_emails = email_settings['always_bcc']
        frappe.logger("debug").info(f"Using always_bcc from Email Account: {bcc_emails}")
   
    
    if attachments:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = formataddr((email_settings['sender_name'], email_settings['email_id']))
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
        msg["From"] = formataddr((email_settings['sender_name'], email_settings['email_id']))
        msg["To"] = ", ".join(to_emails)
       
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
       
        msg.add_alternative(body, subtype="html")
   
    all_recipients = to_emails + cc_emails + bcc_emails
    
    frappe.logger("debug").info(f"Sending email to: TO={to_emails}, CC={cc_emails}, BCC={bcc_emails}, Attachments={len(attachments) if attachments else 0}")

    # First, always create Email Queue record (before attempting to send)
    email_queue_name = _create_email_queue_record(
        subject=subject,
        body=body,
        all_recipients=all_recipients,
        cc_emails=cc_emails,
        sender_email=email_settings['email_id'],
        sender_name=email_settings['sender_name'],
        attachments=attachments,
        status="Not Sent"
    )

    # Attempt to send email
    email_sent_successfully = False
    
    try:
        # Check if we have password
        if not email_settings['password']:
            raise Exception("Email password not found in Email Account settings")
        
        # Determine connection type
        if email_settings['use_ssl']:
            server = smtplib.SMTP_SSL(email_settings['smtp_server'], email_settings['smtp_port'])
        else:
            server = smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port'])
            if email_settings['use_tls']:
                server.starttls()
        
        with server:
            server.login(email_settings['email_id'], email_settings['password'])
            server.send_message(msg, to_addrs=all_recipients)
            email_sent_successfully = True
            
        frappe.logger("debug").info(f"Email sent successfully to {len(all_recipients)} recipients")
            
    except Exception as e:
        frappe.logger("debug").error(f"Failed to send email: {str(e)}")
        frappe.log_error(frappe.get_traceback(), f"Error sending email: {str(e)}")
        
        # Email sending failed, but we still have the record in Email Queue
        frappe.logger("debug").info(f"Email could not be sent, but Email Queue record created: {email_queue_name}")
    
    # Update Email Queue status if email was sent successfully
    if email_sent_successfully and email_queue_name:
        try:
            _update_email_queue_status(email_queue_name, "Sent")
        except Exception as eq_error:
            frappe.logger("debug").error(f"Failed to update Email Queue status: {str(eq_error)}")


def _create_email_queue_record(subject, body, all_recipients, cc_emails, sender_email, sender_name, attachments=None, status="Not Sent"):
    """Create Email Queue record with system permissions"""
    email_queue_name = None
    
    try:
        frappe.flags.ignore_permissions = True
        
        email_queue = frappe.get_doc({
            "doctype": "Email Queue",
            "subject": subject,
            "message": body,
            "status": status,
            "show_as_cc": ",".join(cc_emails) if cc_emails else "",
            "sender": sender_email,
            "sender_full_name": sender_name,
        })
        
        # Add all recipients to the queue record
        for recipient in all_recipients:
            email_queue.append("recipients", {
                "recipient": recipient, 
                "status": "Not Sent" if status == "Not Sent" else "Sent"
            })
        
        # Add attachments to Email Queue record if any
        if attachments:
            _add_attachments_to_email_queue(email_queue, attachments)
        
        email_queue.insert(ignore_permissions=True)
        email_queue_name = email_queue.name
        
        frappe.logger("debug").info(f"Email Queue record created: {email_queue_name}")
        
    except Exception as eq_error:
        # Fallback method with Administrator user
        try:
            original_user = frappe.session.user
            frappe.set_user("Administrator")
            
            email_queue = frappe.get_doc({
                "doctype": "Email Queue",
                "subject": subject,
                "message": body,
                "status": status,
                "show_as_cc": ",".join(cc_emails) if cc_emails else "",
                "sender": sender_email,
                "sender_full_name": sender_name,
            })
            
            for recipient in all_recipients:
                email_queue.append("recipients", {
                    "recipient": recipient, 
                    "status": "Not Sent" if status == "Not Sent" else "Sent"
                })
            
            if attachments:
                _add_attachments_to_email_queue(email_queue, attachments)
            
            email_queue.insert()
            email_queue_name = email_queue.name
            
            frappe.logger("debug").info(f"Email Queue record created with Administrator: {email_queue_name}")
            
        except Exception as admin_error:
            frappe.logger("debug").error(f"Failed to create Email Queue record even with Administrator: {str(admin_error)}")
        finally:
            frappe.set_user(original_user)
    finally:
        frappe.flags.ignore_permissions = False
    
    return email_queue_name


def _update_email_queue_status(email_queue_name, status):
    """Update Email Queue record status"""
    try:
        frappe.flags.ignore_permissions = True
        
        email_queue = frappe.get_doc("Email Queue", email_queue_name)
        email_queue.status = status
        
        # Update recipient status as well
        for recipient in email_queue.recipients:
            recipient.status = status
            
        email_queue.save(ignore_permissions=True)
        
        frappe.logger("debug").info(f"Email Queue {email_queue_name} status updated to {status}")
        
    except Exception as e:
        frappe.logger("debug").error(f"Failed to update Email Queue status: {str(e)}")
    finally:
        frappe.flags.ignore_permissions = False


def _add_attachments_to_message(msg, attachments):
    """Add attachments to the email message"""
    if not attachments:
        return
   
    processed_attachments = _process_attachments(attachments)
   
    for attachment in processed_attachments:
        try:
            file_content = attachment.get('fcontent') or attachment.get('content')
            filename = attachment.get('fname') or attachment.get('filename', 'attachment')
           
            if file_content:
                content_type, encoding = mimetypes.guess_type(filename)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
               
                main_type, sub_type = content_type.split('/', 1)
                part = MIMEBase(main_type, sub_type)
                part.set_payload(file_content)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                msg.attach(part)
               
        except Exception as e:
            frappe.logger("debug").error(f"Failed to attach file {filename}: {str(e)}")


def _add_attachments_to_email_queue(email_queue, attachments):
    """Add attachments to Email Queue record"""
    if not attachments:
        return
   
    try:
        processed_attachments = _process_attachments(attachments)
        attachment_names = []
        
        for attachment in processed_attachments:
            filename = attachment.get('fname') or attachment.get('filename', 'attachment')
            if filename:
                attachment_names.append(filename)
       
        if attachment_names:
            email_queue.attachments = ", ".join(attachment_names)
           
    except Exception as e:
        frappe.logger("debug").error(f"Failed to add attachments to Email Queue: {str(e)}")


def _process_attachments(attachments):
    """Process attachments into a consistent format"""
    if not attachments:
        return []
   
    processed = []
   
    if isinstance(attachments, dict):
        processed.append(attachments)
    elif isinstance(attachments, list):
        for attachment in attachments:
            if isinstance(attachment, dict):
                processed.append(attachment)
            elif isinstance(attachment, str):
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
                processed.append({
                    'fname': attachment.file_name,
                    'fcontent': attachment.content
                })
   
    return processed


def _normalize_recipients(recipients):
    if not recipients:
        return []

    if isinstance(recipients, str):
        recipients = [recipients]

    return [str(r).strip() for r in recipients if r]


frappe.custom_sendmail = custom_sendmail