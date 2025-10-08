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
            frappe.local.response['http_status_code'] = 400
            return {
                'status': 'error',
                'message': _('Vendor Onboarding and Change Request Description are required.'),
                'code': 400
            }
        
        # Check if vendor onboarding document exists
        if not frappe.db.exists('Vendor Onboarding', vend_onb):
            frappe.local.response['http_status_code'] = 404
            return {
                'status': 'error',
                'message': _('Vendor Onboarding document not found.'),
                'code': 404
            }
        
        # Get the vendor onboarding document
        vend_onb_doc = frappe.get_doc('Vendor Onboarding', vend_onb)
        employee_designation = frappe.db.get_value('Employee', {"user_id": frappe.session.user}, 'designation')

        if employee_designation not in ("Purchase Head", "Accounts Team"):
            frappe.local.response['http_status_code'] = 403
            return {
                'status': 'error',
                'message': _('Only Purchase Head and Accounts Team can create change requests.'),
                'code': 403
            }
        
        # Check permissions
        if not frappe.has_permission('Vendor Onboarding', 'write', vend_onb_doc):
            frappe.local.response['http_status_code'] = 403
            return {
                'status': 'error',
                'message': _('Insufficient permissions to modify this document.'),
                'code': 403
            }
        
        
        vend_onb_doc.change_request_by_at = 1
        vend_onb_doc.cr_description = cr_description
        vend_onb_doc.change_requested_by = frappe.session.user
        vend_onb_doc.made_changes_by_pt = 0
        vend_onb_doc.change_requested_by_designation = employee_designation
        
        # Send change request email (before saving)
        mail_response = send_cr_email(vend_onb_doc)
        
        if mail_response.get('status') == 'error':
            frappe.local.response['http_status_code'] = 500
            return {
                'status': 'error',
                'message': mail_response.get('message', _('Failed to send change request email.')),
                'code': 500
            }
        
        # If email sent successfully, mark it and save everything in one go
        vend_onb_doc.mail_sent_for_cr = 1
        vend_onb_doc.save(ignore_permissions=True)
        
        # Commit the transaction
        frappe.db.commit()
        
        frappe.local.response['http_status_code'] = 200
        return {
            'status': 'success',
            'message': _('Change request created and notification sent successfully.'),
            'data': {
                'vendor_onboarding': vend_onb_doc.name,
                'change_requested_by': vend_onb_doc.change_requested_by,
                'cr_description': vend_onb_doc.cr_description
            },
            'code': 200
        }
        
    except frappe.DoesNotExistError:
        frappe.db.rollback()
        frappe.local.response['http_status_code'] = 404
        frappe.log_error(
            title='Change Request by AT - Document Not Found',
            message=f"Vendor Onboarding {vend_onb} not found:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('Vendor Onboarding document not found.'),
            'code': 404
        }
    
    except frappe.PermissionError:
        frappe.db.rollback()
        frappe.local.response['http_status_code'] = 403
        frappe.log_error(
            title='Change Request by AT - Permission Denied',
            message=f"Permission denied for {vend_onb}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('You do not have permission to perform this action.'),
            'code': 403
        }
    
    except frappe.ValidationError as e:
        frappe.db.rollback()
        frappe.local.response['http_status_code'] = 422
        frappe.log_error(
            title='Change Request by AT - Validation Error',
            message=f"Validation error for {vend_onb}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('Validation failed: {0}').format(str(e)),
            'code': 422
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.local.response['http_status_code'] = 500
        frappe.log_error(
            title='Change Request by AT - Internal Error',
            message=f"Error creating change request for {vend_onb}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('An unexpected error occurred. Please try again or contact support.'),
            'code': 500
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
   
    try:
        
        if not vend_onb:
            frappe.local.response['http_status_code'] = 400
            return {
                'status': 'error',
                'message': _('Vendor Onboarding is required.'),
                'code': 400
            }
        
        
        if not frappe.db.exists('Vendor Onboarding', vend_onb):
            frappe.local.response['http_status_code'] = 404
            return {
                'status': 'error',
                'message': _('Vendor Onboarding document not found.'),
                'code': 404
            }
        
        
        employee = frappe.db.get_value('Employee', {'user_id': frappe.session.user}, ['name', 'designation'], as_dict=True)
        
        if not employee:
            frappe.local.response['http_status_code'] = 401
            return {
                'status': 'error',
                'message': _('No employee record found for current user.'),
                'code': 401
            }
        
        allowed_designations = ['Purchase Team']
        
        if employee.designation not in allowed_designations:
            frappe.local.response['http_status_code'] = 403
            return {
                'status': 'error',
                'message': _('Only Purchase Team members can complete change requests. Your designation: {0}').format(employee.designation),
                'code': 403
            }
        
        
        vend_onb_doc = frappe.get_doc('Vendor Onboarding', vend_onb)
        

        if not frappe.has_permission('Vendor Onboarding', 'write', vend_onb_doc):
            frappe.local.response['http_status_code'] = 403
            return {
                'status': 'error',
                'message': _('Insufficient permissions to modify this document.'),
                'code': 403
            }
        
        if not vend_onb_doc.change_request_by_at:
            frappe.local.response['http_status_code'] = 422
            return {
                'status': 'error',
                'message': _('No active change request found for this vendor onboarding.'),
                'code': 422
            }
        
       
        vend_onb_doc.made_changes_by_pt = 1
        vend_onb_doc.change_request_by_at = 0
        vend_onb_doc.mail_sent_for_cr = 0
        
       
        mail_response = send_cr_completion_email(vend_onb_doc)
        

        
        if mail_response.get('status') == 'error':
            frappe.local.response['http_status_code'] = 500
            return {
                'status': 'error',
                'message': mail_response.get('message', _('Failed to send completion notification email.')),
                'code': 500
            }
        
        
        vend_onb_doc.save(ignore_permissions=True)
        
        
        frappe.db.commit()
        
       
        frappe.local.response['http_status_code'] = 200
        return {
            'status': 'success',
            'message': _('Change request completed by Purchase Team and notification sent successfully.'),
            'data': {
                'vendor_onboarding': vend_onb_doc.name,
                'change_requested_by': vend_onb_doc.change_requested_by,
                'change_requested_by_designation': vend_onb_doc.change_requested_by_designation
            },
            'code': 200
        }
        
    except frappe.DoesNotExistError:
        frappe.db.rollback()
        frappe.local.response['http_status_code'] = 404
        frappe.log_error(
            title='CR Completion - Document Not Found',
            message=f"Vendor Onboarding {vend_onb} not found:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('Vendor Onboarding document not found.'),
            'code': 404
        }
    
    except frappe.PermissionError:
        frappe.db.rollback()
        frappe.local.response['http_status_code'] = 403
        frappe.log_error(
            title='CR Completion - Permission Denied',
            message=f"Permission denied for {vend_onb}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('You do not have permission to perform this action.'),
            'code': 403
        }
    
    except frappe.ValidationError as e:
        frappe.db.rollback()
        frappe.local.response['http_status_code'] = 422
        frappe.log_error(
            title='CR Completion - Validation Error',
            message=f"Validation error for {vend_onb}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('Validation failed: {0}').format(str(e)),
            'code': 422
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.local.response['http_status_code'] = 500
        frappe.log_error(
            title='CR Completion - Internal Error',
            message=f"Error completing change request for {vend_onb}:\n{frappe.get_traceback()}"
        )
        return {
            'status': 'error',
            'message': _('An unexpected error occurred while completing the change request.'),
            'code': 500
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
                'message': _('Change request recipient email not configured.')
            }
        
        # Prepare email content
        recipients = [vend_onb_doc.change_requested_by]
        cc = [vend_onb_doc.purchase_h_approval] if vend_onb_doc.purchase_h_approval else []
        
        message = f"""
        <p>Dear Requestor,</p>
        
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