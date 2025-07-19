import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def send_po_user_confirmation(po_id):
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
        
        po_doc.user_confirmation = 0
        po_doc.save(ignore_permissions=True)
        frappe.db.commit()

        pr_no = po_doc.get("ref_pr_no")
        if not pr_no:
            return {
                "status": "error",
                "message": "Purchase Requisition Number (ref_pr_no) not found in the PO."
            }
        
        if not frappe.db.exists("Purchase Requisition Form", pr_no):
            return {
                "status": "error",
                "message": f"Purchase Requisition Form '{pr_no}' not found."
            }
        
        pr_doc = frappe.get_doc("Purchase Requisition Form", pr_no) 
        purchase_requisitioner = pr_doc.get("requisitioner")

        if not purchase_requisitioner:
            return {
                "status": "error",
                "message": "Purchase requisitioner not found in the PR."
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
        
        # Email message with JavaScript to hide buttons on click
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
            "message": f"Confirmation email sent to {requisitioner_name} ({requisitioner_email})"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO User Confirmation API Error")
        return {
            "status": "error",
            "message": "Failed to send confirmation email.",
            "error": str(e)
        }


import frappe
from frappe import _

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
            po_doc.save(ignore_permissions=True)
            frappe.db.commit()

           
            vendor_code = po_doc.get("vendor_code")
            vendor_email = None
            vendor_name = None

            if vendor_code:
                try:
                    company_vendor_docs = frappe.get_all("Company Vendor Code", fields=["name", "vendor_ref_no"])
                    for doc in company_vendor_docs:
                        full_doc = frappe.get_doc("Company Vendor Code", doc.name)
                        if hasattr(full_doc, 'vendor_code') and full_doc.vendor_code:
                            for row in full_doc.vendor_code:
                                if hasattr(row, 'vendor_code') and row.vendor_code == vendor_code:
                                    vendor_ref_no = full_doc.vendor_ref_no
                                    if vendor_ref_no:
                                        vendor_email = frappe.db.get_value("Vendor Master", vendor_ref_no, "office_email_primary")
                                        vendor_name = frappe.db.get_value("Vendor Master", vendor_ref_no, "vendor_name") or "Vendor"
                                        if vendor_email:
                                            break
                        if vendor_email:
                            break
                except Exception as vendor_error:
                    frappe.log_error(f"Error finding vendor email: {str(vendor_error)}", "Vendor Email Lookup Error")

            if vendor_email:
                try:
                    vendor_subject = f"Delivery Issue - PO: {po_doc.name}"
                    vendor_message = f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #dc3545;">Delivery Issue Notification</h2>
                            <p>Dear {vendor_name},</p>
                            <p>We have received feedback that goods have <strong>NOT been delivered</strong> for the following purchase order:</p>
                            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <strong>PO Number:</strong> {po_doc.name}<br>
                                <strong>Delivery Date:</strong> {frappe.utils.format_date(po_doc.delivery_date) if po_doc.delivery_date else 'Not specified'}<br>
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
                except Exception as email_error:
                    frappe.log_error(f"Error sending vendor email: {str(email_error)}", "Vendor Email Send Error")

            return frappe.respond_as_web_page(
                title="Issue Reported",
                html=html_response(f"Issue reported by {requisitioner_name} for PO: {po_doc.name}. {'Vendor notified.' if vendor_email else 'Issue logged.'}"),
                indicator_color='orange'
            )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO Confirmation Handler API Error")
        return frappe.respond_as_web_page(
            title="Error",
            html=html_response("An error occurred while processing your confirmation. Please try again later."),
            indicator_color='red'
        )
