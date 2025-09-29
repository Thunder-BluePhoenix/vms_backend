import frappe
from frappe import _


@frappe.whitelist()
def request_change_by_at(vend_onb, cr_description):
    """
    Create a change request for vendor onboarding initiated by AT team
    
    Parameters:
    - vend_onb: Vendor Onboarding document name
    - cr_description: Description of the change request
    """
    try:
        # Validate inputs
        if not vend_onb or not cr_description:
            return {
                'status': 'error',
                'message': _('Vendor Onboarding and Change Request Description are required.')
            }
        
        # Get the vendor onboarding document
        vend_onb_doc = frappe.get_doc('Vendor Onboarding', vend_onb)
        
        # Set change request fields
        vend_onb_doc.change_request_by_at = 1
        vend_onb_doc.cr_description = cr_description
        vend_onb_doc.change_requested_by = frappe.session.user
        
        # Send change request email (before saving)
        mail_response = send_cr_email(vend_onb_doc)
        
        if mail_response['status'] == 'error':
            return mail_response
        
        # If email sent successfully, mark it and save everything in one go
        vend_onb_doc.mail_sent_for_cr = 1
        vend_onb_doc.save(ignore_permissions=True)
        
        # Commit the transaction
        frappe.db.commit()
        
        return {
            'status': 'success',
            'message': _('Change request created and notification sent successfully.'),
            'vendor_onboarding': vend_onb_doc.name
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(
            title='Change Request by AT Error',
            message=f"Error creating change request for {vend_onb}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('Failed to create change request: {0}').format(str(e))
        }


def send_cr_email(vend_onb_doc):
    """
    Send change request notification email to Purchase Team
    
    Parameters:
    - vend_onb_doc: Vendor Onboarding document object (can be unsaved)
    """
    try:
        # Check if email should be sent
        if vend_onb_doc.change_request_by_at != 1:
            return {
                'status': 'error',
                'message': _('Change request not initiated by AT.')
            }
        
        # Check if email already sent (from database, not just the doc object)
        existing_mail_status = frappe.db.get_value(
            'Vendor Onboarding',
            vend_onb_doc.name,
            'mail_sent_for_cr'
        )
        
        if existing_mail_status == 1:
            return {
                'status': 'success',
                'message': _('Change request email already sent.')
            }
        
        # Validate email recipients
        if not vend_onb_doc.purchase_t_approval:
            return {
                'status': 'error',
                'message': _('Purchase Team approval email not configured.')
            }
        
        # Prepare email content
        recipients = [vend_onb_doc.purchase_t_approval]
        cc = [vend_onb_doc.purchase_h_approval] if vend_onb_doc.purchase_h_approval else []
        
        message = f"""
        <p>Dear Purchase Team,</p>
        
        <p>A change request has been initiated for <b>Vendor Onboarding {vend_onb_doc.name}</b>.</p>
        
        <p><b>Change Request Description:</b><br>
        {vend_onb_doc.cr_description or 'No description provided'}</p>
        
        <p>Please review the request and take the necessary action.</p>
        
       
        
        <p>Best regards,<br>
        Vendor Management System</p>
        """
        
        # Send email using custom sendmail
        frappe.custom_sendmail(
            recipients=recipients,
            cc=cc,
            subject='Change Request OnBoarding',
            message=message
        )
        
        frappe.logger().info(
            f"Change request email sent for Vendor Onboarding: {vend_onb_doc.name}"
        )
        
        return {
            'status': 'success',
            'message': _('Change request email sent to Purchase Team successfully.')
        }
        
    except Exception as e:
        frappe.log_error(
            title='Change Request Email Error',
            message=f"Error sending CR email for {vend_onb_doc.name}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('Failed to send change request email: {0}').format(str(e))
        }
    


@frappe.whitelist()
def completed_cr_by_pt(vend_onb):
    """
    Mark change request as completed by Purchase Team (PT)
    
    Parameters:
    - vend_onb: Vendor Onboarding document name
    """
    try:
        # Validate input
        if not vend_onb:
            return {
                'status': 'error',
                'message': _('Vendor Onboarding is required.')
            }
        
        # Get the vendor onboarding document
        vend_onb_doc = frappe.get_doc('Vendor Onboarding', vend_onb)
        
        # Set completion fields
        vend_onb_doc.made_changes_by_pt = 1
        vend_onb_doc.change_request_by_at = 0
        vend_onb_doc.mail_sent_for_cr = 0
        
        # Send completion notification email (before saving)
        mail_response = send_cr_completion_email(vend_onb_doc)
        
        if mail_response['status'] == 'error':
            return mail_response
        
        # Save all changes in one go
        vend_onb_doc.save(ignore_permissions=True)
        
        # Commit the transaction
        frappe.db.commit()
        
        return {
            'status': 'success',
            'message': _('Change request completed by Purchase Team and notification sent successfully.'),
            'vendor_onboarding': vend_onb_doc.name
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(
            title='Change Request Completion Error',
            message=f"Error completing change request for {vend_onb}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('Failed to complete change request: {0}').format(str(e))
        }


def send_cr_completion_email(vend_onb_doc):
    """
    Send change request completion notification email to Accounts Team
    
    Parameters:
    - vend_onb_doc: Vendor Onboarding document object (can be unsaved)
    """
    try:
        # Validate email recipients
        if not vend_onb_doc.change_requested_by:
            return {
                'status': 'error',
                'message': _('Accounts Team approval email not configured.')
            }
        
        # Prepare email content
        recipients = [vend_onb_doc.change_requested_by]
        cc = [vend_onb_doc.purchase_h_approval] if vend_onb_doc.purchase_h_approval else []
        
        message = f"""
        <p>Dear Accounts Team,</p>
        
        <p>The change request for <b>Vendor Onboarding {vend_onb_doc.name}</b> has been completed by the Purchase Team.</p>
        
        <p>The requested changes have been reviewed and implemented. Please proceed with the next steps in the vendor onboarding process.</p>
        
        
        
        <p>Best regards,<br>
        Vendor Management System</p>
        """
        
        # Send email using custom sendmail
        frappe.custom_sendmail(
            recipients=recipients,
            cc=cc,
            subject='Change Request Completed - OnBoarding',
            message=message
        )
        
        frappe.logger().info(
            f"Change request completion email sent for Vendor Onboarding: {vend_onb_doc.name}"
        )
        
        return {
            'status': 'success',
            'message': _('Change request completion email sent to Accounts Team successfully.')
        }
        
    except Exception as e:
        frappe.log_error(
            title='CR Completion Email Error',
            message=f"Error sending completion email for {vend_onb_doc.name}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('Failed to send completion email: {0}').format(str(e))
        }