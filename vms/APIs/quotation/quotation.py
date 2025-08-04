import frappe
import json
from frappe import _
from frappe.utils import now_datetime



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
def approve_quotation(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        quotation_name = data.get("name")
        
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
        
        quotation.final_ffn = data.get("final_ffn") or ""
        quotation.final_rate_kg = data.get("final_rate_kg") or ""
        quotation.final_chargeable_weight = data.get("final_chargeable_weight") or ""
        quotation.final_freight_fcr = data.get("final_freight_fcr") or ""
        quotation.final_fsc = data.get("final_fsc") or ""
        quotation.final_sc = data.get("final_sc") or ""
        quotation.final_xcr = data.get("final_xcr") or ""
        quotation.final_pickup = data.get("final_pickup") or ""
        quotation.final_xray = data.get("final_xray") or ""
        quotation.final_sum_freight_inr = data.get("final_sum_freight_inr") or ""
        quotation.final_gst_amount = data.get("final_gst_amount") or ""
        quotation.final_total = data.get("final_total") or ""
        quotation.final_others = data.get("final_others") or ""
        quotation.final_airline = data.get("final_airline") or ""
        quotation.final_landing_price = data.get("final_landing_price") or ""
        quotation.final_dc = data.get("final_dc") or ""
        quotation.final_transit_days = data.get("final_transit_days") or ""
        quotation.final_freight_total = data.get("final_freight_total") or ""
        quotation.final_remarks = data.get("final_remarks") or ""
        quotation.final_tat = data.get("final_tat") or ""
        
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

                rfq = frappe.get_doc("Request For Quotation", rfq_number)
                frappe.db.set_value("Request For Quotation", rfq.name, "status", "Approved")
                frappe.db.set_value("Request For Quotation", rfq.name, "is_approved", 1)

                 # Mark 'Won' in Vendor Details table if ref_no or email matches
                for row in rfq.vendor_details:
                    if (quotation.ref_no and quotation.ref_no == row.ref_no) or \
                    (quotation.office_email_primary and quotation.office_email_primary == row.office_email_primary):
                        frappe.db.set_value(
                            "Vendor Details",
                            row.name, 
                            "bid_status",
                            "Won"
                        )

                        frappe.db.set_value(
                            "Vendor Details",
                            row.name, 
                            "bid_won",
                            1
                        )

                # Mark 'Won' in Non-Onboarded Vendor Details table if email matches
                for row in rfq.non_onboarded_vendor_details:
                    if quotation.office_email_primary and quotation.office_email_primary == row.office_email_primary:
                        frappe.db.set_value(
                            "Non Onboarded Vendor Details",
                            row.name, 
                            "bid_status",
                            "Won"
                        )

                        frappe.db.set_value(
                            "Non Onboarded Vendor Details",
                            row.name, 
                            "bid_won",
                            1
                        )


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

@frappe.whitelist(allow_guest=True)
def get_quotations_by_rfq(rfq_number):
    try:
        
        if not rfq_number:
            frappe.throw(_("RFQ Number is required"))
        
       
        if not frappe.db.exists("Request For Quotation", rfq_number):
            frappe.throw(_("RFQ Number {0} does not exist").format(rfq_number))
        
        rfq = frappe.get_doc("Request For Quotation", rfq_number)

        current_time = now_datetime()

        deadline = rfq.rfq_cutoff_date_logistic or rfq.quotation_deadline

        if deadline and deadline < current_time:

            quotations = frappe.get_all(
                "Quotation",
                filters={
                    "rfq_number": rfq_number,
                },
                fields=['*']
            )
            
            if not quotations:
                return {
                    "success": True,
                    "message": _("No quotations found for RFQ {0}").format(rfq_number),
                    "data": [],
                    "total_count": 0
                }
            
            def get_sort_key(quotation):
                try:
                    rank = quotation.get('rank')
                    if rank and str(rank).strip():
                        return int(str(rank).strip())
                    else:
                        return 999999
                except (ValueError, TypeError):
                    return 999999
            
            quotations.sort(key=get_sort_key)

            formatted_quotations = []
            for quotation in quotations:
                quote_amount_display = None
                if quotation.get('quote_amount'):
                    try:
                        quote_amount_display = float(str(quotation['quote_amount']).replace(',', ''))
                    except (ValueError, TypeError):
                        quote_amount_display = quotation['quote_amount']
                
            
                attachments = frappe.get_all(
                    "Multiple Attachment",  
                    filters={
                        "parent": quotation.get('name'),
                        "parenttype": "Quotation"
                    },
                    fields=['name1', 'attachment_name']
                )
                
            
                formatted_attachments = []
                for attachment in attachments:
                    attachment_data = {
                        "document_name": attachment.get('name1'),
                        "attach": attachment.get('attachment_name'),
                        "file_url": frappe.utils.get_url() + attachment.get('attachment_name') if attachment.get('attachment_name') else None
                    }
                    formatted_attachments.append(attachment_data)
                
                formatted_quotation = {
                    "name": quotation.get('name'),
                    "rfq_number": quotation.get('rfq_number'),
                    "vendor_name": quotation.get('vendor_name'),
                    "vendor_code": quotation.get('vendor_code'),
                    "quote_amount": quote_amount_display,
                    # "quote_amount_formatted": quotation.get('quote_amount'), 
                    "rank": quotation.get('rank'),
                    "mode_of_shipment": quotation.get('mode_of_shipment'),
                    "office_email_primary": quotation.get('office_email_primary'),
                    "airlinevessel_name": quotation.get('airlinevessel_name'),
                    "chargeable_weight": quotation.get('chargeable_weight'),
                    "ratekg": quotation.get('ratekg'),
                    "fuel_surcharge": quotation.get('fuel_surcharge'),
                    "destination_port": quotation.get('destination_port'),
                    "actual_weight": quotation.get('actual_weight'),
                    "sc": quotation.get('sc'),
                    "xray": quotation.get('xray'),
                    "pickuporigin": quotation.get('pickuporigin'),
                    "ex_works": quotation.get('ex_works'),
                    "total_freight": quotation.get('total_freight'),
                    "from_currency": quotation.get('from_currency'),
                    "to_currency": quotation.get('to_currency'),
                    "exchange_rate": quotation.get('exchange_rate'),
                    "total_freightinr": quotation.get('total_freightinr'),
                    "destination_charge": quotation.get('destination_charge'),
                    "shipping_line_charge": quotation.get('shipping_line_charge'),
                    "cfs_charge": quotation.get('cfs_charge'),
                    "total_landing_price": quotation.get('total_landing_price'),
                    "invoice_no": quotation.get('invoice_no'),
                    "transit_days": quotation.get('transit_days'),
                    "remarks": quotation.get('remarks'),
                    "logistic_type": quotation.get('logistic_type'),
                    "bidding_status": quotation.get('bidding_status'),
                    "status": quotation.get('status'),
                    "attachments": formatted_attachments
                }
                formatted_quotations.append(formatted_quotation)
            
            rfq_doc = frappe.get_doc("Request For Quotation", rfq_number)
            
            return {
                "success": True,
                "message": _("Quotations retrieved successfully"),
                "data": formatted_quotations,
                "total_count": len(formatted_quotations),
                "rfq_details": {
                    "name": rfq_doc.name
                }
            }
        
        else:
            return{
                "mesaage": "Cut off datetime is not Pass thats why Bidding details wont be visible."
            }
        
    except frappe.DoesNotExistError:
        frappe.throw(_("RFQ Number {0} does not exist").format(rfq_number))
    except Exception as e:
        frappe.log_error(f"Error in get_quotations_by_rfq API: {str(e)}", "Quotation API Error")
        frappe.throw(_("An error occurred while fetching quotations: {0}").format(str(e)))

