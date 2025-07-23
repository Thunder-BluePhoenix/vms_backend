import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def send_po_user_confirmation():
    try:
        if frappe.request.method == "POST":
            if frappe.request.content_type and 'application/json' in frappe.request.content_type:
                data = frappe.request.get_json()
            else:
                data = frappe.form_dict
        else:
            data = frappe.form_dict
        
        po_id = data.get("po_id")
        remark = data.get("remark", "")  
        purchase_requisitioner = data.get("email")
        
        if not po_id:
            return {
                "status": "error",
                "message": "Missing required field: 'po_id'."
            }

        if not frappe.db.exists("Purchase Order", po_id):
            return {
                "status": "error",
                "message": f"Purchase Order '{po_id}' not found."
            }

        po_doc = frappe.get_doc("Purchase Order", po_id)
        
        
        if remark:
            current_remarks = po_doc.get("remarks") or ""
            new_remark = f"Remark: {remark} by purchase team - {frappe.utils.format_datetime(frappe.utils.now())}"
            
            if current_remarks:
                po_doc.remarks = f"{current_remarks}\n{new_remark}"
            else:
                po_doc.remarks = new_remark
        
        po_doc.user_confirmation = 0
        po_doc.save(ignore_permissions=True)
        frappe.db.commit()

        

        if not purchase_requisitioner:
            return {
                "status": "error",
                "message": "Purchase requisitioner is not in Data."
            }

        requisitioner_email = purchase_requisitioner  
        requisitioner_name = frappe.get_value("User", purchase_requisitioner, "first_name") or frappe.get_value("User", purchase_requisitioner, "full_name")
        
        if not requisitioner_email:
            return {
                "status": "error",
                "message": "Purchase requisitioner email not found."
            }

        if not requisitioner_name:
            requisitioner_name = "User" 

        subject = f"Goods Confirmation Required - PO: {po_doc.name}"
        
        base_url = frappe.utils.get_url()
        yes_url = f"{base_url}/api/method/vms.APIs.user_confirmation.user_confirmation.handle_po_confirmation?po_id={po_id}&response=yes"
        no_url = f"{base_url}/api/method/vms.APIs.user_confirmation.user_confirmation.handle_po_confirmation?po_id={po_id}&response=no"
        
        
        remark_section = ""
        if remark:
            remark_section = f"""
                <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007bff;">
                    <strong>Remark:</strong> {remark} by purchase team
                </div>
            """
        
        
        message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Goods Delivery Confirmation</h2>
                
                <p>Dear {requisitioner_name},</p>
                
                <p>This is a confirmation email regarding your Purchase Order.</p>
                
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Purchase Order Details:</strong><br>
                    <strong>PO Number:</strong> {po_doc.name}<br>
                    <strong>Delivery Date:</strong> {frappe.utils.format_date(po_doc.delivery_date) if po_doc.delivery_date else 'Not specified'}<br>
                </div>
                
                {remark_section}
                
                <h3 style="color: #333;">Question: Have you received your goods?</h3>
                
                <div id="button-container" style="text-align: center; margin: 30px 0;">
                    <a href="{yes_url}" onclick="handleButtonClick(this, 'yes')" style="background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 0 10px; display: inline-block; font-weight: bold;">YES</a>
                    <a href="{no_url}" onclick="handleButtonClick(this, 'no')" style="background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 0 10px; display: inline-block; font-weight: bold;">NO</a>
                </div>
                
                <div id="status-message" style="text-align: center; margin: 30px 0; display: none;">
                    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 20px; border-radius: 5px;">
                        <strong id="status-text">Processing your response...</strong>
                    </div>
                </div>
                
                <p style="font-size: 12px; color: #666; margin-top: 30px;">
                    Please click on the appropriate button above to confirm the status of your goods delivery.
                </p>
                
                <p>Regards,<br>VMS Team</p>
                
                <script>
                    function handleButtonClick(button, response) {{
                        // Hide the button container
                        document.getElementById('button-container').style.display = 'none';
                        
                        // Show status message
                        const statusMessage = document.getElementById('status-message');
                        const statusText = document.getElementById('status-text');
                        
                        if (response === 'yes') {{
                            statusText.innerHTML = '✓ Thank you! You have confirmed that goods have been received.';
                        }} else {{
                            statusText.innerHTML = '⚠ Thank you for reporting the issue. We will follow up on the delivery status.';
                        }}
                        
                        statusMessage.style.display = 'block';
                        
                        // Prevent the default link behavior
                        event.preventDefault();
                        
                        // Make the API call in the background
                        fetch(button.href)
                            .then(response => response.text())
                            .then(data => {{
                                console.log('Response processed successfully');
                            }})
                            .catch(error => {{
                                console.error('Error processing response:', error);
                                statusText.innerHTML = '❌ Error processing your response. Please try again or contact support.';
                            }});
                        
                        return false;
                    }}
                </script>
            </div>
        """
        
        frappe.sendmail(
            recipients=[requisitioner_email],
            subject=subject,
            message=message,
            now=True
        )
        
        return {
            "status": "success",
            "message": f"Confirmation email sent to {requisitioner_name} ({requisitioner_email})",
            "remark_saved": bool(remark)
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO User Confirmation API Error")
        return {
            "status": "error",
            "message": "Failed to send confirmation email.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def handle_po_confirmation(po_id, response):
    try:
        def html_response(message):
            return f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; margin-top: 100px;">
                <h2 style="color: #28a745;">Thank you!</h2>
                <p style="font-size: 18px; color: #555;">{message}</p>
            </div>
            """

        if not po_id or not response:
            return frappe.respond_as_web_page(
                title="Invalid Request",
                html=html_response("Missing required information in the request."),
                indicator_color='red'
            )

        if response.lower() not in ['yes', 'no']:
            return frappe.respond_as_web_page(
                title="Invalid Response",
                html=html_response("Invalid response received."),
                indicator_color='red'
            )

        if not frappe.db.exists("Purchase Order", po_id):
            return frappe.respond_as_web_page(
                title="PO Not Found",
                html=html_response(f"Purchase Order '{po_id}' not found."),
                indicator_color='red'
            )

        po_doc = frappe.get_doc("Purchase Order", po_id)

        pr_no = po_doc.get("ref_pr_no")
        requisitioner_name = "User"

        if pr_no and frappe.db.exists("Purchase Requisition Form", pr_no):
            pr_doc = frappe.get_doc("Purchase Requisition Form", pr_no)
            purchase_requisitioner = pr_doc.get("requisitioner")
            if purchase_requisitioner:
                requisitioner_name = (
                    frappe.get_value("User", purchase_requisitioner, "first_name")
                    or frappe.get_value("User", purchase_requisitioner, "full_name")
                    or "User"
                )

        if response.lower() == 'yes':
            po_doc.payment_release = 1
            po_doc.save(ignore_permissions=True)
            frappe.db.commit()

            return frappe.respond_as_web_page(
                title="Confirmation Received",
                html=html_response(f"Confirmation received from {requisitioner_name}. Payment release initiated for PO: {po_doc.name}"),
                indicator_color='green'
            )
        else:
            po_doc.user_confirmation = 1
            pd_doc.goods_not_received = 1
            po_doc.save(ignore_permissions=True)
            frappe.db.commit()

            return frappe.respond_as_web_page(
                title="Issue Reported",
                html=html_response(f"Issue reported by {requisitioner_name} for PO: {po_doc.name}. Issue logged."),
                indicator_color='orange'
            )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO Confirmation Handler API Error")
        return frappe.respond_as_web_page(
            title="Error",
            html=html_response("An error occurred while processing your confirmation. Please try again later."),
            indicator_color='red'
        )



@frappe.whitelist(allow_guest=True)
def send_payment_release_notification_api(po_id):
   
    try:
        if not po_id:
            return {
                "status": "error",
                "message": "Missing required field: 'po_id'."
            }

        if not frappe.db.exists("Purchase Order", po_id):
            return {
                "status": "error",
                "message": f"Purchase Order '{po_id}' not found."
            }

        
        po_doc = frappe.get_doc("Purchase Order", po_id)
        po_doc.payment_release = 0
        po_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        
        company_code = po_doc.get("company_code")
        if not company_code:
            return {
                "status": "error",
                "message": "Company code not found in Purchase Order."
            }

        
        accounts_team_emails = []
        
        
        employees = frappe.get_all("Employee", fields=["name", "user_id"])
        
        for employee in employees:
            if not employee.user_id:
                continue
                
            try:
                emp_doc = frappe.get_doc("Employee", employee.name)
            
            
                if hasattr(emp_doc, 'company') and emp_doc.company:
                    company_code_match = False
                    
                    
                    for company_row in emp_doc.company:
                        print(company_row.company_name)
                        if hasattr(company_row, 'company_name') and company_row.company_name == company_code:
                            company_code_match = True
                            break
                    
                    if company_code_match:
                        user_roles = frappe.get_all("Has Role", 
                                                  filters={"parent": employee.user_id, "role": "Accounts Team"}, 
                                                  fields=["role"])
                        
                        
                        if user_roles:
                            user_email = frappe.get_value("User", employee.user_id, "email")
                            user_name = frappe.get_value("User", employee.user_id, "first_name") or frappe.get_value("User", employee.user_id, "full_name") or "Team Member"
                            
                            if user_email:
                                accounts_team_emails.append({
                                    "email": user_email,
                                    "name": user_name
                                })
                                
            except Exception as emp_error:
                frappe.log_error(f"Error processing employee {employee.name}: {str(emp_error)}", "Employee Processing Error")
                continue
        
        
        if not accounts_team_emails:
            return {
                "status": "error",
                "message": f"No accounts team members found for company code: {company_code}"
            }
        
       
        successful_emails = 0
        failed_emails = 0
        
        for member in accounts_team_emails:
            try:
                subject = f"Payment Release Approved - PO: {po_doc.name}"
                
                message = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #28a745;">Payment Release Notification</h2>
                        
                        <p>Dear {member['name']},</p>
                        
                        <p>Good news! We have received confirmation that goods have been delivered for the following purchase order. You can now proceed with payment release.</p>
                        
                        
                        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>Purchase Order Details:</strong><br>
                            <strong>PO Number:</strong> {po_doc.name}<br>
                            <strong>Company Code:</strong> {company_code}<br>
                            <strong>Delivery Date:</strong> {frappe.utils.format_date(po_doc.delivery_date) if po_doc.delivery_date else 'Not specified'}<br>
                        </div>
                        
                        <div style="background-color: #cce5ff; border: 1px solid #99ccff; color: #004085; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>Action Required:</strong> Please proceed with payment release for this purchase order as goods delivery has been confirmed.
                        </div>
                        
                        <p>Please process the payment at your earliest convenience.</p>
                        
                        <p>Regards,<br>VMS Team</p>
                    </div>
                """
                
                frappe.sendmail(
                    recipients=[member['email']],
                    subject=subject,
                    message=message,
                    now=True
                )
                
                successful_emails += 1
                
            except Exception as email_error:
                frappe.log_error(f"Error sending email to {member['email']}: {str(email_error)}", "Accounts Team Email Error")
                failed_emails += 1
        
        
        if successful_emails > 0:
            return {
                "status": "success",
                "message": f"Payment release notification sent successfully to {successful_emails} accounts team member(s).",
                "details": {
                    "po_id": po_id,
                    "company_code": company_code,
                    "total_recipients": len(accounts_team_emails),
                    "successful_emails": successful_emails,
                    "failed_emails": failed_emails,
                    "recipients": [member['email'] for member in accounts_team_emails]
                }
            }
        else:
            return {
                "status": "error",
                "message": "Failed to send any notification emails.",
                "details": {
                    "po_id": po_id,
                    "company_code": company_code,
                    "total_recipients": len(accounts_team_emails),
                    "failed_emails": failed_emails
                }
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Release Notification API Error")
        return {
            "status": "error",
            "message": "Failed to send payment release notification.",
            "error": str(e)
        }



@frappe.whitelist(allow_guest=True)
def send_vendor_delivery_issue_email(po_id):
    try:
        if not frappe.db.exists("Purchase Order", po_id):
            return {"status": "error", "message": f"Purchase Order '{po_id}' not found."}

        po_doc = frappe.get_doc("Purchase Order", po_id)
        
        vendor_email = po_doc.get("email")
        

        if not vendor_email:
            return {"status": "error", "message": "No email found for vendor."}
        
        if vendor_email:
            try:
                vendor_subject = f"Delivery Issue - PO: {po_doc.name}"
                vendor_message = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #dc3545;">Delivery Issue Notification</h2>
                        <p>Dear Vendor,</p>
                        <p>We have received feedback that goods have <strong>NOT been delivered</strong> for the following purchase order:</p>
                        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>PO Number:</strong> {po_doc.name}<br>
                        </div>
                        <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>Action Required:</strong> Please check the delivery status and contact us immediately to resolve this issue.
                        </div>
                        <p>Regards,<br>VMS Team</p>
                    </div>
                """
                frappe.sendmail(
                    recipients=[vendor_email],
                    subject=vendor_subject,
                    message=vendor_message,
                    now=True
                )
                return {"status": "success", "message": "Vendor email sent successfully", "vendor_email": vendor_email}
            except Exception as email_error:
                frappe.log_error(f"Error sending vendor email: {str(email_error)}", "Vendor Email Send Error")
                return {"status": "error", "message": "Error sending vendor email"}
        else:
            return {"status": "warning", "message": "Vendor email not found"}
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Send Vendor Email API Error")
        return {"status": "error", "message": "An error occurred while sending vendor email"}

