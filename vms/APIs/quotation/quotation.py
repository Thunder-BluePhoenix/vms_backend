import frappe
import json
from frappe import _



# API Function for the Revise of a quotation
@frappe.whitelist(allow_guest=False)
def update_asked_to_revise(name):
    try:
        
        quotation_name = name
        
        
        if not quotation_name:
            return {
                "status": "error",
                "message": "Quotation name is required",
                "error_type": "missing_parameter"
            }
        
        
        if not frappe.db.exists('Quotation', quotation_name):
            return {
                "status": "error",
                "message": f"Quotation '{quotation_name}' does not exist",
                "error_type": "not_found"
            }
        
        
        quotation = frappe.get_doc('Quotation', quotation_name)
        quotation.asked_to_revise = 1
        quotation.save()
        frappe.db.commit()
        
       
        try:
            send_revision_email_to_vendor(quotation)
        except Exception as email_error:
        
            frappe.log_error(f"Failed to send revision email for quotation {quotation_name}: {str(email_error)}")
        
        return {
            "status": "success",
            "message": "Quotation marked for revision and email sent to vendor",
            "data": {
                "name": quotation.name,
                "action": "Asked to revise checkbox checked"
            }
        }
        
    except frappe.ValidationError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": f"Validation Error: {str(e)}",
            "error_type": "validation"
        }
    
    except frappe.DuplicateEntryError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": f"Duplicate Entry: {str(e)}",
            "error_type": "duplicate"
        }
    
    except frappe.PermissionError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": f"Permission Error: {str(e)}",
            "error_type": "permission"
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error updating quotation {quotation_name}: {str(e)}")
        return {
            "status": "error",
            "message": "An unexpected error occurred",
            "error_type": "general"
        }


def send_revision_email_to_vendor(quotation):
    try:

        vendor_email = quotation.get('office_email_primary') 
        
        if not vendor_email:
            frappe.log_error(f"No vendor email found in quotation {quotation.name}")
            return
        
        
        subject = f"Quotation {quotation.name} - Revision Required"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ffc107;">Quotation Revision Required</h2>
            
            <p>Dear Vendor,</p>
            
            <p>We have reviewed your quotation and would like to request some revisions before we can proceed with the approval.</p>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h3 style="margin-top: 0;">Quotation Details:</h3>
                <p><strong>Quotation Number:</strong> {quotation.name}</p>
                <p><strong>Total Amount:</strong> {quotation.currency} {quotation.quote_amount}</p>
                <p><strong>Status:</strong> Revision Required</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #495057;">Next Steps:</h3>
                <ul style="margin-bottom: 0;">
                    <li>Please review the quotation details</li>
                    <li>Make the necessary revisions</li>
                    <li>Submit the updated quotation for our review</li>
                </ul>
            </div>
            
            <p>Please contact us if you need any clarification or have questions regarding the required revisions.</p>
            
            <p>Thank you for your cooperation.</p>
            
            <p>Best regards,<br>
            VMS Team</p>
        </div>
        """
        
        
        frappe.sendmail(
            recipients=[vendor_email],
            subject=subject,
            message=message,
            now=True
        )
        

        frappe.logger().info(f"Revision email sent to {vendor_email} for quotation {quotation.name}")
        
    except Exception as e:
        frappe.log_error(f"Error sending revision email for quotation {quotation.name}: {str(e)}")
        raise e





#API Function for the approval of quotation
@frappe.whitelist(allow_guest=True)
def approve_quotation(name):
    try:
        quotation_name = name
        
        if not quotation_name:
            return {
                "status": "error",
                "message": "Quotation name is required",
                "error_type": "missing_parameter"
            }
        
        if not frappe.db.exists('Quotation', quotation_name):
            return {
                "status": "error",
                "message": f"Quotation '{quotation_name}' does not exist",
                "error_type": "not_found"
            }
        
        
        quotation = frappe.get_doc('Quotation', quotation_name)
        
        
        rfq_number = quotation.get('rfq_number') 
        
       
        quotation.approved = 1
        quotation.status = 'Approved'
        quotation.bidding_status = 'Win'  
        quotation.save()
        frappe.db.commit()
        
       
        try:
            send_approval_email_to_vendor(quotation)
        except Exception as email_error:
            frappe.log_error(f"Failed to send approval email for quotation {quotation_name}: {str(email_error)}")
        
       
        if rfq_number:
            try:
                update_losing_quotations(rfq_number, quotation_name)
            except Exception as rfq_error:
                frappe.log_error(f"Failed to update other quotations for RFQ {rfq_number}: {str(rfq_error)}")
        
        return {
            "status": "success",
            "message": "Quotation approved successfully, other quotations marked as lose, and emails sent to all vendors",
            "data": {
                "name": quotation.name,
                "action": "Quotation approved",
                "rfq_number": rfq_number
            }
        }
        
    except frappe.ValidationError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": f"Validation Error: {str(e)}",
            "error_type": "validation"
        }
    
    except frappe.DuplicateEntryError as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": f"Duplicate Entry: {str(e)}",
            "error_type": "duplicate"
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error updating quotation {quotation_name}: {str(e)}")
        return {
            "status": "error",
            "message": "An unexpected error occurred",
            "error_type": "general"
        }


def update_losing_quotations(rfq_number, approved_quotation_name):
   
    try:
        
        other_quotations = frappe.get_all(
            'Quotation',
            filters={
                'rfq_number': rfq_number, 
                'name': ['!=', approved_quotation_name]
            },
            fields=['name']
        )
        
        
        if not other_quotations:
            for field_name in ['rfq_number']:
                other_quotations = frappe.get_all(
                    'Quotation',
                    filters={
                        field_name: rfq_number,
                        'name': ['!=', approved_quotation_name]
                    },
                    fields=['name']
                )
                if other_quotations:
                    break
        
        for quotation_record in other_quotations:
            try:
                losing_quotation = frappe.get_doc('Quotation', quotation_record.name)
                losing_quotation.bidding_status = 'Lose'
                losing_quotation.status = 'Lost'
                losing_quotation.save()
                
                send_thank_you_email_to_vendor(losing_quotation)
                
                frappe.logger().info(f"Updated quotation {quotation_record.name} to Lose status")
                
            except Exception as e:
                frappe.log_error(f"Error updating losing quotation {quotation_record.name}: {str(e)}")
                continue
        
        frappe.db.commit()
        frappe.logger().info(f"Updated {len(other_quotations)} quotations to Lose status for RFQ {rfq_number}")
        
    except Exception as e:
        frappe.log_error(f"Error in update_losing_quotations for RFQ {rfq_number}: {str(e)}")
        raise e


def send_approval_email_to_vendor(quotation):

    try:

        vendor_email = quotation.get('office_email_primary') 
        
        if not vendor_email:
            frappe.log_error(f"No vendor email found in quotation {quotation.name}")
            return
        

        subject = f"Quotation {quotation.name} - Approved"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #28a745;">Quotation Approved</h2>
            
            <p>Dear Vendor,</p>
            
            <p>We are pleased to inform you that your quotation has been approved.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Quotation Details:</h3>
                <p><strong>Quotation Number:</strong> {quotation.name}</p>
                <p><strong>Total Amount:</strong> {quotation.currency} {quotation.quote_amount}</p>
                <p><strong>Status:</strong> Approved</p>
            </div>
            
            <p>Please proceed with the next steps as per our agreement.</p>
            
            <p>Thank you for your business.</p>
            
            <p>Best regards,<br>
            VMS Team</p>
        </div>
        """
        
        
        frappe.sendmail(
            recipients=[vendor_email],
            subject=subject,
            message=message,
            now=True
        )
        
        
    
        frappe.logger().info(f"Approval email sent to {vendor_email} for quotation {quotation.name}")
        
    except Exception as e:
        frappe.log_error(f"Error sending approval email for quotation {quotation.name}: {str(e)}")
        raise e

def send_thank_you_email_to_vendor(quotation):
    try:
       
        vendor_email = quotation.get('office_email_primary') 
        
        if not vendor_email:
            frappe.log_error(f"No vendor email found in quotation {quotation.name}")
            return
        
       
        subject = f"Thank You for Your Participation - Quotation {quotation.name}"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #6c757d;">Thank You for Your Participation</h2>
            
            <p>Dear Vendor,</p>
            
            <p>Thank you for submitting your quotation for our recent Request for Quotation (RFQ). We appreciate the time and effort you invested in preparing your proposal.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #6c757d;">
                <h3 style="margin-top: 0;">Quotation Details:</h3>
                <p><strong>Quotation Number:</strong> {quotation.name}</p>
                <p><strong>Status:</strong> Bid Not Selected</p>
            </div>
            
            <p>While we have selected another vendor for this particular project, we were impressed with your submission and would like to keep you in our vendor database for future opportunities.</p>
            
            <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0;"><strong>We encourage you to participate in our future RFQs as we value your partnership and look forward to potential collaborations.</strong></p>
            </div>
            
            <p>Thank you once again for your interest in working with us.</p>
            
            <p>Best regards,<br>
            VMS Team</p>
        </div>
        """
        
    
        frappe.sendmail(
            recipients=[vendor_email],
            subject=subject,
            message=message,
            now=True
        )
        
        
        frappe.logger().info(f"Thank you email sent to {vendor_email} for quotation {quotation.name}")
        
    except Exception as e:
        frappe.log_error(f"Error sending thank you email for quotation {quotation.name}: {str(e)}")
        raise e



@frappe.whitelist(allow_guest=True)
def get_quotation_details(quotation_name):
    try:
        quotation = frappe.get_doc("Quotation", quotation_name)
        quotation_dict = quotation.as_dict()
        
        return quotation_dict
        
    except frappe.DoesNotExistError:
        frappe.throw(f"Quotation '{quotation_name}' not found")
    except Exception as e:
        frappe.log_error(f"Error in get_quotation_details: {str(e)}")
        frappe.throw(f"An error occurred while fetching Quotation details: {str(e)}")