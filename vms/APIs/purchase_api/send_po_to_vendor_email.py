import frappe
import json
from frappe import _
from vms.utils.custom_send_mail import custom_sendmail

@frappe.whitelist()
def send_po_to_pr(data=None, po_name=None):
    try:
        content_type = frappe.request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type or (data and isinstance(data, str)):

            if data and isinstance(data, str):
                data = json.loads(data)
            else:

                data = frappe.local.form_dict
            
            tomail = data.get("to")
            cc = data.get("cc")
            body = data.get("body")
            attach = data.get("attach")
            
        elif 'multipart/form-data' in content_type:

            tomail = frappe.form_dict.get("to")
            cc = frappe.form_dict.get("cc")
            body = frappe.form_dict.get("body")
            attach = None
            
            if frappe.request.files:
                attach = []
                for file_key, file_obj in frappe.request.files.items():
                    if file_obj and file_obj.filename:
                        file_content = file_obj.read()
                        attach.append({
                            "fname": file_obj.filename,
                            "fcontent": file_content
                        })
        else:
            if frappe.request.files:
                tomail = frappe.form_dict.get("to")
                cc = frappe.form_dict.get("cc")
                body = frappe.form_dict.get("body")
                attach = []
                for file_key, file_obj in frappe.request.files.items():
                    if file_obj and file_obj.filename:
                        file_content = file_obj.read()
                        attach.append({
                            "fname": file_obj.filename,
                            "fcontent": file_content
                        })
            else:
                data = frappe.local.form_dict if not data else json.loads(data) if isinstance(data, str) else data
                tomail = data.get("to")
                cc = data.get("cc")
                body = data.get("body")
                attach = data.get("attach")
        
        if not tomail:
            return {"status": "error", "message": "No email address found to send the email."}
        
        if not body:
            body = "Please find the attached Purchase Order document."
        
        to_emails = []
        if isinstance(tomail, str):
            to_emails = [email.strip() for email in tomail.split(",") if email.strip()]
        elif isinstance(tomail, list):
            to_emails = [email.strip() for email in tomail if email.strip()]
        else:
            return {"status": "error", "message": "Invalid 'to' email format."}
        
        for email in to_emails:
            if not frappe.utils.validate_email_address(email):
                return {"status": "error", "message": f"Invalid TO email address: {email}"}
        
        cc_list = []
        if cc:
            if isinstance(cc, str):
                cc_list = [email.strip() for email in cc.split(",") if email.strip()]
            elif isinstance(cc, list):
                cc_list = [email.strip() for email in cc if email.strip()]
            
            for email in cc_list:
                if not frappe.utils.validate_email_address(email):
                    return {"status": "error", "message": f"Invalid CC email address: {email}"}
        
        attachments = []
        if attach:
            if isinstance(attach, dict):
                if "data" in attach:
                    fname = attach.get("fname", "Purchase_Order.pdf")
                    if not fname.endswith(".pdf"):
                        fname += ".pdf"
                    
                    pdf_data = attach["data"]
                    
                    try:
                        import base64
                        binary_data = base64.b64decode(pdf_data)
                        
                        if not binary_data.startswith(b'%PDF'):
                            frappe.log_error(f"Invalid PDF header. First bytes: {binary_data[:10]}", "PDF Validation Error")
                            return {"status": "error", "message": "Invalid PDF format - missing PDF header"}
                        
                        attachments = [{
                            "fname": fname,
                            "fcontent": binary_data  
                        }]
                        
                    except Exception as decode_error:
                        frappe.log_error(f"Base64 decode error: {str(decode_error)}", "PDF Decode Error")
                        return {"status": "error", "message": "Failed to decode PDF data"}
                        
                elif "fcontent" in attach:
                    fname = attach.get("fname", "Purchase_Order.pdf")
                    if not fname.endswith(".pdf"):
                        fname += ".pdf"
                    
                    pdf_data = attach["fcontent"]
                    if isinstance(pdf_data, str):
                        try:
                            import base64
                            binary_data = base64.b64decode(pdf_data)
                            if not binary_data.startswith(b'%PDF'):
                                return {"status": "error", "message": "Invalid PDF format"}
                            pdf_data = binary_data
                        except:
                            pass  
                    
                    attachments = [{
                        "fname": fname,
                        "fcontent": pdf_data
                    }]

            elif isinstance(attach, list):
                for i, att in enumerate(attach):
                    if isinstance(att, dict):
                        fname = att.get("fname", f"Purchase_Order_{i+1}.pdf")
                        if not fname.endswith(".pdf"):
                            fname += ".pdf"
                        
                        
                        content = att.get("data") or att.get("fcontent")
                        if content:
                            
                            if isinstance(content, str):
                                try:
                                    import base64
                                    content = base64.b64decode(content)
                                    if not content.startswith(b'%PDF'):
                                        frappe.log_error(f"Invalid PDF in attachment {i+1}", "PDF Validation Error")
                                        continue
                                except:
                                    frappe.log_error(f"Failed to decode attachment {i+1}", "PDF Decode Error")
                                    continue
                            
                            attachments.append({
                                "fname": fname,
                                "fcontent": content
                            })
            
            elif isinstance(attach, str):
                try:
                    import base64
                    binary_data = base64.b64decode(attach)
                    if not binary_data.startswith(b'%PDF'):
                        return {"status": "error", "message": "Invalid PDF format"}
                    
                    attachments = [{
                        "fname": "Purchase_Order.pdf",
                        "fcontent": binary_data
                    }]
                except:
                    return {"status": "error", "message": "Failed to decode PDF data"}
        
        
        email_params = {
            "recipients": to_emails,
            "subject": "Purchase Order",
            "message": body
        }
        
        
        if attachments:
            email_params["attachments"] = attachments
        
        
        if cc_list:
            email_params["cc"] = cc_list
        
        frappe.custom_sendmail(**email_params)

        purchase_order = frappe.get_doc("Purchase Order", po_name)
        purchase_order.sent_to_vendor = 1
           
        frappe.logger().info(f"Purchase Order email sent successfully to {', '.join(to_emails)}")
        
        return {
            "status": "success",
            "message": f"Email sent successfully to {', '.join(to_emails)}" + (f" with CC to {', '.join(cc_list)}" if cc_list else "")
        }
        
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON data provided."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO Email Sending Error")
        return {
            "status": "error", 
            "message": "An error occurred while sending the email.",
            "error": str(e) if frappe.conf.get("developer_mode") else "Please contact administrator"
        }