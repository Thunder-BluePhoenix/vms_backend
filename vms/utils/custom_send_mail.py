import frappe
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, make_msgid, formatdate
import mimetypes
import os
from vms.utils.notification import create_notification_log


def is_email_sending_suspended():
    """Return True if email sending is suspended in system defaults"""
    try:
        return bool(int(frappe.db.get_default("suspend_email_queue") or 0))
    except Exception:
        return False


def custom_sendmail(recipients=None, subject=None, message=None, cc=None, bcc=None, 
                   attachments=None, template=None, args=None, **kwargs):
    """Enhanced sendmail with template support and suspension handling"""
    
    try:
        # Handle Email Template if provided
        if template:
            subject, message = _render_email_template(template, args or {})
        elif args and (subject or message):
            if subject:
                subject = frappe.render_template(subject, args)
            if message:
                message = frappe.render_template(message, args)
        
        # Validate subject
        if not subject or not str(subject).strip():
            frappe.log_error(
                title="Custom Sendmail - Missing Subject",
                message=f"Recipients: {recipients}, Template: {template}"
            )
            subject = "No Subject"
        
        # Create notification log
        create_notification_log(recipients=recipients, subject=subject, message=message, **kwargs)

        # Get email account settings
        email_settings = _get_email_account_settings()
        
        # Handle always_bcc
        always_bcc = []
        if email_settings.get('always_bcc'):
            if isinstance(email_settings['always_bcc'], str):
                always_bcc = [email.strip() for email in email_settings['always_bcc'].split(',') if email.strip()]
            elif isinstance(email_settings['always_bcc'], list):
                always_bcc = email_settings['always_bcc']
        
        # Merge provided bcc with always_bcc
        if bcc:
            if isinstance(bcc, str):
                bcc = [bcc]
            all_bcc = list(set(bcc + always_bcc))
        else:
            all_bcc = always_bcc if always_bcc else []
        
        # Normalize cc
        if cc and isinstance(cc, str):
            cc = [cc]
        elif not cc:
            cc = []
        
        # Check if suspended
        is_suspended = is_email_sending_suspended()
        
        if is_suspended:
            # When suspended, create MIME message in Email Queue
            result = _create_email_queue_with_mime(
                recipients=recipients,
                subject=subject,
                message=message,
                cc=cc,
                bcc=all_bcc,
                attachments=attachments,
                sender=email_settings.get('email_id'),
                sender_name=email_settings.get('sender_name')
            )
            
            if result:
                frappe.logger("debug").info(f"✅ Email queued successfully: {result}")
            else:
                frappe.logger("debug").error("❌ Failed to create email queue")
                
        else:
            # ✅ When not suspended, use custom method to ensure CC/BCC are tracked
            send_now = kwargs.pop('now', False)
            
            _send_with_tracking(
                recipients=recipients,
                cc=cc,
                bcc=all_bcc,
                subject=subject,
                message=message,
                attachments=attachments,
                sender_email=email_settings.get('email_id'),
                sender_name=email_settings.get('sender_name'),
                send_now=send_now
            )
        
        status = "queued (suspended)" if is_suspended else "sent"
        frappe.logger("debug").info(f"Email {status}: '{subject}' to {recipients}")
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error in custom_sendmail")
        frappe.logger("debug").error(f"❌ custom_sendmail failed: {str(e)}")
        raise


def _send_with_tracking(recipients, subject, message, cc=None, bcc=None, 
                        attachments=None, sender_email=None, sender_name=None, send_now=True):
    """
    Send email with proper CC/BCC tracking in Email Queue
    This creates an Email Queue record that shows CC and BCC, then sends the email
    """
    try:
        # Normalize recipients
        if isinstance(recipients, str):
            recipients = [recipients]
        if isinstance(cc, str):
            cc = [cc] if cc else []
        elif not cc:
            cc = []
        if isinstance(bcc, str):
            bcc = [bcc] if bcc else []
        elif not bcc:
            bcc = []
        
        sender_email = sender_email or "noreply@merillife.com"
        sender_full = formataddr((sender_name or "VMS", sender_email))
        
        # Build MIME message
        mime_message = _build_mime_message(
            subject=subject,
            body=message,
            sender=sender_full,
            sender_email=sender_email,
            recipients=recipients,
            cc=cc,
            attachments=attachments
        )
        
        # ✅ Create Email Queue record WITH CC and BCC visible
        frappe.flags.ignore_permissions = True
        
        email_queue = frappe.get_doc({
            "doctype": "Email Queue",
            "message": mime_message,
            "status": "Sending" if send_now else "Not Sent",
            "sender": sender_full,
            "show_as_cc": ",".join(cc) if cc else "",  # ✅ Shows CC
            "priority": 1,
            "retry": 0,
        })
        
        # ✅ Add all recipients including BCC
        all_recipients = recipients + cc + bcc
        for recipient in all_recipients:
            if recipient:
                email_queue.append("recipients", {
                    "recipient": recipient,
                    "status": "Not Sent"
                })
        
        email_queue.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.flags.ignore_permissions = False
        
        # ✅ Now send the email immediately if send_now is True
        if send_now:
            _send_via_smtp(
                recipients=recipients,
                cc=cc,
                bcc=bcc,
                mime_message=mime_message,
                sender_email=sender_email,
                email_queue_name=email_queue.name
            )
        
        frappe.logger("debug").info(f"✅ Email {'sent' if send_now else 'queued'}: {email_queue.name}")
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in _send_with_tracking")
        frappe.logger("debug").error(f"❌ _send_with_tracking failed: {str(e)}")
        raise


def _send_via_smtp(recipients, cc, bcc, mime_message, sender_email, email_queue_name):
    """Send email via SMTP and update Email Queue status"""
    try:
        # Get email account
        email_account = frappe.get_doc("Email Account", {"email_id": sender_email})
        
        all_recipients = recipients + cc + bcc
        
        # Connect to SMTP
        if email_account.use_ssl:
            server = smtplib.SMTP_SSL(email_account.smtp_server, email_account.smtp_port)
        else:
            server = smtplib.SMTP(email_account.smtp_server, email_account.smtp_port)
            if email_account.use_tls:
                server.starttls()
        
        with server:
            server.login(email_account.email_id, email_account.get_password())
            
            # Send to all recipients
            server.sendmail(
                from_addr=sender_email,
                to_addrs=all_recipients,
                msg=mime_message
            )
        
        # ✅ Update Email Queue status to Sent
        frappe.flags.ignore_permissions = True
        email_queue = frappe.get_doc("Email Queue", email_queue_name)
        email_queue.status = "Sent"
        
        # Update all recipient statuses
        for recipient in email_queue.recipients:
            recipient.status = "Sent"
        
        email_queue.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.flags.ignore_permissions = False
        
        frappe.logger("debug").info(f"✅ Email sent and Email Queue updated: {email_queue_name}")
        
    except Exception as e:
        # ✅ Update Email Queue status to Error
        try:
            frappe.flags.ignore_permissions = True
            email_queue = frappe.get_doc("Email Queue", email_queue_name)
            email_queue.status = "Error"
            email_queue.error = str(e)
            email_queue.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.flags.ignore_permissions = False
        except:
            pass
        
        frappe.log_error(frappe.get_traceback(), "Error sending via SMTP")
        frappe.logger("debug").error(f"❌ SMTP send failed: {str(e)}")
        raise


def _create_email_queue_with_mime(recipients, subject, message, cc=None, bcc=None, 
                                   attachments=None, sender=None, sender_name=None):
    """Create Email Queue with proper MIME message format (without Communication)"""
    try:
        frappe.flags.ignore_permissions = True
        
        # Normalize recipients
        if isinstance(recipients, str):
            recipients = [recipients]
        if isinstance(cc, str):
            cc = [cc] if cc else []
        elif not cc:
            cc = []
        if isinstance(bcc, str):
            bcc = [bcc] if bcc else []
        elif not bcc:
            bcc = []
        
        # Filter out None values from cc and bcc
        cc = [email for email in cc if email]
        bcc = [email for email in bcc if email]
        
        sender_email = sender or "noreply@merillife.com"
        sender_full = formataddr((sender_name or "VMS", sender_email))
        
        # Build MIME message with attachments
        mime_message = _build_mime_message(
            subject=subject,
            body=message,
            sender=sender_full,
            sender_email=sender_email,
            recipients=recipients,
            cc=cc,
            attachments=attachments
        )
        
        if not mime_message:
            frappe.logger("debug").error("❌ MIME message is empty")
            return None
        
        # ✅ Create Email Queue WITHOUT Communication
        # Since we have a complete MIME message with Subject header, we don't need Communication
        email_queue = frappe.get_doc({
            "doctype": "Email Queue",
            "message": mime_message,  # Complete MIME message with all headers
            "status": "Not Sent",
            "sender": sender_full,
            "show_as_cc": ",".join(cc) if cc else "",
            "priority": 1,
            "retry": 0,
        })
        
        # Add all recipients
        all_recipients = recipients + cc + bcc
        for recipient in all_recipients:
            if recipient:  # Skip None/empty recipients
                email_queue.append("recipients", {
                    "recipient": recipient,
                    "status": "Not Sent"
                })
        
        email_queue.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.logger("debug").info(f"✅ Email Queue created: {email_queue.name}")
        
        return email_queue.name
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating Email Queue with MIME")
        frappe.logger("debug").error(f"❌ Failed: {str(e)}")
        return None
        
    finally:
        frappe.flags.ignore_permissions = False



def _build_mime_message(subject, body, sender, sender_email, recipients, cc=None, attachments=None):
    """Build a proper MIME message with headers and attachments"""
    try:
        import time
        
        # Create the outer multipart message
        msg = MIMEMultipart('mixed')
        
        # Add all required headers
        msg['Subject'] = str(subject)
        msg['From'] = str(sender)
        msg['To'] = ", ".join(recipients)
        if cc:
            msg['Cc'] = ", ".join(cc)
        msg['Reply-To'] = str(sender_email)
        msg['Message-Id'] = make_msgid()
        msg['Date'] = formatdate(time.time(), localtime=True)
        msg['MIME-Version'] = '1.0'
        msg['X-Frappe-Site'] = frappe.utils.get_url()
        
        # Create alternative part for text and HTML
        msg_alternative = MIMEMultipart('alternative')
        
        # Convert HTML to plain text
        try:
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            text_content = h.handle(body)
        except (ImportError, Exception):
            import re
            text_content = re.sub('<[^<]+?>', '', body)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Add plain text version
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg_alternative.attach(text_part)
        
        # Add HTML version
        html_part = MIMEText(body, 'html', 'utf-8')
        msg_alternative.attach(html_part)
        
        # Attach the alternative part to the main message
        msg.attach(msg_alternative)
        
        # ✅ Add attachments if provided
        if attachments:
            _add_attachments_to_mime(msg, attachments)
        
        # Convert to string
        mime_string = msg.as_string()
        
        frappe.logger("debug").info(f"✅ MIME built: {len(mime_string)} bytes with {len(attachments) if attachments else 0} attachments")
        
        return mime_string
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error building MIME message")
        frappe.logger("debug").error(f"❌ _build_mime_message failed: {str(e)}")
        return None


def _add_attachments_to_mime(msg, attachments):
    """Add attachments to MIME message"""
    if not attachments:
        return
    
    # Normalize attachments to list
    if not isinstance(attachments, list):
        attachments = [attachments]
    
    for attachment in attachments:
        try:
            # Handle different attachment formats
            if isinstance(attachment, dict):
                filename = attachment.get('fname') or attachment.get('filename', 'attachment')
                file_content = attachment.get('fcontent') or attachment.get('content')
            elif isinstance(attachment, str):
                # If it's a file path
                if os.path.exists(attachment):
                    filename = os.path.basename(attachment)
                    with open(attachment, 'rb') as f:
                        file_content = f.read()
                else:
                    continue
            else:
                continue
            
            # Guess MIME type
            content_type, encoding = mimetypes.guess_type(filename)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            
            main_type, sub_type = content_type.split('/', 1)
            
            # Create MIME part
            part = MIMEBase(main_type, sub_type)
            part.set_payload(file_content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            
            msg.attach(part)
            
            frappe.logger("debug").info(f"✅ Attached file: {filename}")
            
        except Exception as e:
            frappe.logger("debug").error(f"❌ Failed to attach file: {str(e)}")


def _add_attachments_to_communication(communication, attachments):
    """Add attachments to Communication document"""
    if not attachments:
        return
    
    if not isinstance(attachments, list):
        attachments = [attachments]
    
    for attachment in attachments:
        try:
            if isinstance(attachment, dict):
                filename = attachment.get('fname') or attachment.get('filename', 'attachment')
                file_content = attachment.get('fcontent') or attachment.get('content')
                
                # Create File document
                file_doc = frappe.get_doc({
                    "doctype": "File",
                    "file_name": filename,
                    "attached_to_doctype": "Communication",
                    "attached_to_name": communication.name,
                    "content": file_content,
                    "is_private": 1
                })
                file_doc.insert(ignore_permissions=True)
                
                # Link to communication
                communication.append("attachments", {
                    "file_url": file_doc.file_url
                })
                
        except Exception as e:
            frappe.logger("debug").error(f"Failed to add attachment to Communication: {str(e)}")


def custom_send_mail(mail_template, recipient, email_context=None, cc_recepients=None, **kwargs):
    """Convenience wrapper for template-based emails"""
    return custom_sendmail(
        recipients=recipient,
        cc=cc_recepients,
        template=mail_template,
        args=email_context,
        **kwargs
    )


def _render_email_template(template_name, context):
    """Render Email Template with context"""
    try:
        subject = frappe.db.get_value("Email Template", template_name, "subject")
        response = frappe.db.get_value("Email Template", template_name, "response_html")
        
        if not subject:
            frappe.log_error(
                title="Email Template Missing Subject",
                message=f"Template '{template_name}' has no subject"
            )
            subject = f"Notification from {template_name}"
        
        # Handle empty rich text
        if response == '<div class="ql-editor read-mode"><p><br></p></div>':
            response = ""
        
        # Render with context
        rendered_subject = frappe.render_template(subject, context) if subject else "No Subject"
        rendered_message = frappe.render_template(response, context) if response else ""
        
        if not rendered_subject.strip():
            rendered_subject = "No Subject"
        
        return rendered_subject, rendered_message
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error rendering template {template_name}")
        return "Email Template Error", "Failed to render email template"


def _get_email_account_settings(email_id="noreply@merillife.com"):
    try:
        email_account = frappe.get_doc("Email Account", {"email_id": email_id})
        return {
            'email_id': email_account.email_id,
            'sender_name': getattr(email_account, 'sender_name', 'VMS'),
            'always_bcc': getattr(email_account, 'always_bcc', None)
        }
    except Exception as e:
        frappe.logger("debug").error(f"Failed to get email account: {str(e)}")
        return {
            'email_id': email_id,
            'sender_name': 'VMS',
            'always_bcc': None
        }


@frappe.whitelist()
def toggle_sending(enable):
    frappe.only_for("System Manager")
    frappe.db.set_default("suspend_email_queue", 0 if frappe.utils.cint(enable) else 1)


# Expose as global function
frappe.custom_sendmail = custom_sendmail
