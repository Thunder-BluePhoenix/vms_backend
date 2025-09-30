import frappe
import json
from frappe import _
from frappe.utils import now_datetime
from vms.utils.custom_send_mail import custom_sendmail



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
        
        
        frappe.custom_sendmail(
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
        
        # quotation.final_ffn = data.get("final_ffn") or ""
        # quotation.final_rate_kg = data.get("final_rate_kg") or ""
        # quotation.final_chargeable_weight = data.get("final_chargeable_weight") or ""
        # quotation.final_freight_fcr = data.get("final_freight_fcr") or ""
        # quotation.final_fsc = data.get("final_fsc") or ""
        # quotation.final_sc = data.get("final_sc") or ""
        # quotation.final_xcr = data.get("final_xcr") or ""
        # quotation.final_pickup = data.get("final_pickup") or ""
        # quotation.final_xray = data.get("final_xray") or ""
        # quotation.final_sum_freight_inr = data.get("final_sum_freight_inr") or ""
        # quotation.final_gst_amount = data.get("final_gst_amount") or ""
        # quotation.final_total = data.get("final_total") or ""
        # quotation.final_others = data.get("final_others") or ""
        # quotation.final_airline = data.get("final_airline") or ""
        # quotation.final_landing_price = data.get("final_landing_price") or ""
        # quotation.final_dc = data.get("final_dc") or ""
        # quotation.final_transit_days = data.get("final_transit_days") or ""
        # quotation.final_freight_total = data.get("final_freight_total") or ""
        # quotation.final_remarks = data.get("final_remarks") or ""
        # quotation.final_tat = data.get("final_tat") or ""
        
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
                        # set quotation win ID
                        frappe.db.set_value(
                            "Vendor Details",
                            row.name, 
                            "quotation",
                            quotation.name
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
                         # set quotation win ID
                        frappe.db.set_value(
                            "Non Onboarded Vendor Details",
                            row.name, 
                            "quotation",
                            quotation.name
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
        
        
        frappe.custom_sendmail(
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
        
    
        frappe.custom_sendmail(
            recipients=[vendor_email],
            subject=subject,
            message=message,
            now=True
        )
        
        
        frappe.logger().info(f"Thank you email sent to {vendor_email} for quotation {quotation.name}")
        
    except Exception as e:
        frappe.log_error(f"Error sending thank you email for quotation {quotation.name}: {str(e)}")
        raise e


# Return the Prev Quotation data based on prev Quotation ID

@frappe.whitelist(allow_guest=True)
def get_quotation_details(quotation_name):
    try:
        if not quotation_name:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Quotation ID is required."
            }

        quotation = frappe.get_doc("Quotation", quotation_name)

        quotation_data = {
            "quotation_name": quotation.name,
            "rfq_number": quotation.rfq_number,
            "ref_no": quotation.ref_no,
            "vendor_name": quotation.vendor_name,
            "vendor_code": quotation.vendor_code,
            "rfq_type": quotation.rfq_type,
            "office_email_primary": quotation.office_email_primary,
            "vendor_contact": quotation.vendor_contact,

            "logistic_type": quotation.logistic_type,
            "company_name_logistic": quotation.company_name_logistic,
            "mode_of_shipment": quotation.mode_of_shipment,
            "sr_no": quotation.sr_no,
            "airlinevessel_name": quotation.airlinevessel_name,
            "chargeable_weight": quotation.chargeable_weight,
            "rfq_cutoff_date": quotation.rfq_cutoff_date,
            "ratekg": quotation.ratekg,
            "fuel_surcharge": quotation.fuel_surcharge,
            "surcharge": quotation.surcharge,
            "sc": quotation.sc,
            "xray": quotation.xray,
            "pickuporigin": quotation.pickuporigin,
            "transit_days": quotation.transit_days,
            "total_freight": quotation.total_freight,
            "from_currency": quotation.from_currency,
            "exchange_rate": quotation.exchange_rate,
            "total_freightinr": quotation.total_freightinr,
            "destination_charge": quotation.destination_charge,
            "shipping_line_charge": quotation.shipping_line_charge,
            "cfs_charge": quotation.cfs_charge,
            "total_landing_price": quotation.total_landing_price,
            "remarks": quotation.remarks,

            "destination_port": quotation.destination_port,
            "port_code": quotation.port_code,
            "port_of_loading": quotation.port_of_loading,
            "inco_terms": quotation.inco_terms,
            "shipper_name": quotation.shipper_name,
            "package_type": quotation.package_type,
            "no_of_pkg_units": quotation.no_of_pkg_units,
            "product_category_logistic": quotation.product_category_logistic,
            "vol_weight": quotation.vol_weight,
            "actual_weight": quotation.actual_weight,
            "invoice_date": quotation.invoice_date,
            "invoice_no": quotation.invoice_no,
            "invoice_value": quotation.invoice_value,
            "expected_date_of_arrival": quotation.expected_date_of_arrival,
            "consignee_name": quotation.consignee_name,
            "shipment_date": quotation.shipment_date,
            "shipment_type": quotation.shipment_type,
            "quantity": quotation.quantity,
            "ship_to_address": quotation.ship_to_address,
        }

        return {
            "status": "success",
            "data": quotation_data
        }

    except frappe.DoesNotExistError:
        frappe.local.response["http_status_code"] = 404
        return {
            "status": "error",
            "message": f"Quotation '{quotation_name}' not found"
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        frappe.log_error(frappe.get_traceback(), "Error in get_quotation_details")
        return {
            "status": "error",
            "message": "An unexpected error occurred while fetching Quotation details."
        }



@frappe.whitelist(allow_guest=True)
def get_quotations_by_rfq(rfq_number, page_no=1, page_length=5, vendor_name=None):
    try:
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length

        if not rfq_number:
            frappe.throw(_("RFQ Number is required"))

        if not frappe.db.exists("Request For Quotation", rfq_number):
            frappe.throw(_("RFQ Number {0} does not exist").format(rfq_number))

        rfq = frappe.get_doc("Request For Quotation", rfq_number)

        current_time = now_datetime()
        deadline = rfq.rfq_cutoff_date_logistic or rfq.quotation_deadline

        if deadline and deadline < current_time:
            # Build filters
            filters = {"rfq_number": rfq_number}
            if vendor_name:
                # LIKE filter for vendor_name
                filters["vendor_name"] = ["like", f"%{vendor_name}%"]

            # Get total count for pagination info
            total_count = frappe.db.count("Quotation", filters=filters)

            quotations = frappe.get_all(
                "Quotation",
                filters=filters,
                fields=['*'],
                limit_start=offset,
                limit_page_length=page_length
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

                # Fetch quotation's item list
                # rfq_item_lists = frappe.get_all(
                #     "RFQ Items",
                #     filters={
                #         "parent": quotation.get('name'),
                #         "parenttype": "Quotation"
                #     },
                #     fields=[
                #        "name", "head_unique_field", "purchase_requisition_number", "material_code_head", "delivery_date_head", "material_name_head",
                #        "quantity_head", "uom_head", "price_head", "rate_with_tax", "rate_without_tax", "moq_head", "lead_time_head", "tax",
                #        "remarks"
                #     ]
                # )

                # pr_items = []
                # for item in rfq_item_lists:
                #     pr_items.append(item)

                rfq_item_lists = frappe.get_all(
                    "RFQ Items",
                    filters={
                        "parent": quotation.get('name'),
                        "parenttype": "Quotation"
                    },
                    fields=[
                    "name", "head_unique_field", "purchase_requisition_number", "material_code_head", "delivery_date_head", "material_name_head",
                    "quantity_head", "uom_head", "price_head", "rate_with_tax", "rate_without_tax", "moq_head", "lead_time_head", "tax",
                    "remarks",
                    # subhead fields
                    "subhead_unique_field", "material_code_subhead", "material_name_subhead",
                    "quantity_subhead", "uom_subhead", "price_subhead", "delivery_date_subhead", "rate_subhead"
                    ]
                )

                grouped_data = {}

                for row in sorted(rfq_item_lists, key=lambda x: x.name):
                    head_id = row.head_unique_field
                    if not head_id:
                        continue

                    if head_id not in grouped_data:
                        grouped_data[head_id] = {
                            "row_id": row.name,
                            "head_unique_field": row.head_unique_field,
                            "purchase_requisition_number": row.purchase_requisition_number,
                            "material_code_head": row.material_code_head,
                            "delivery_date_head": row.delivery_date_head,
                            "material_name_head": row.material_name_head,
                            "quantity_head": row.quantity_head,
                            "uom_head": row.uom_head,
                            "price_head": row.price_head,
                            "rate_with_tax": row.rate_with_tax,
                            "rate_without_tax": row.rate_without_tax,
                            "moq_head": row.moq_head,
                            "lead_time_head": row.lead_time_head,
                            "tax": row.tax,
                            "remarks": row.remarks,
                            "subhead_fields": []
                        }

                    subhead_data = {
                        "subhead_unique_field": row.subhead_unique_field,
                        "material_code_subhead": row.material_code_subhead,
                        "material_name_subhead": row.material_name_subhead,
                        "quantity_subhead": row.quantity_subhead,
                        "uom_subhead": row.uom_subhead,
                        "price_subhead": row.price_subhead,
                        "delivery_date_subhead": row.delivery_date_subhead
                    }

                    grouped_data[head_id]["subhead_fields"].append(subhead_data)

                pr_items = list(grouped_data.values())

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
                    "approved": quotation.get('approved'),

                    # material vendor fields
                    "rfq_date": quotation.get('rfq_date') or "",
                    "contact_person": quotation.get('contact_person') or "",
                    "validity_start_date": quotation.get('validity_start_date') or "",
                    "validity_end_date": quotation.get('validity_end_date') or "",
                    "currency": quotation.get('currency') or "",
                    "negotiation": quotation.get('negotiation') or "",
                    "payment_terms": quotation.get('payment_terms') or "",

                    # table
                    "attachments": formatted_attachments,
                    "quotation_item_list": pr_items

                }
                formatted_quotations.append(formatted_quotation)

            rfq_doc = frappe.get_doc("Request For Quotation", rfq_number)

            return {
                "success": True,
                "message": _("Quotations retrieved successfully"),
                "data": formatted_quotations,
                "total_count": total_count,
                "page_no": page_no,
                "page_length": page_length,
                "rfq_details": {
                    "name": rfq_doc.name
                }
            }

        else:
            return {
                "mesaage": "Cut off datetime is not Pass thats why Bidding details wont be visible.",
                "data": [],
            }

    except frappe.DoesNotExistError:
        frappe.throw(_("RFQ Number {0} does not exist").format(rfq_number))
    except Exception as e:
        frappe.log_error(f"Error in get_quotations_by_rfq API: {str(e)}", "Quotation API Error")
        frappe.throw(_("An error occurred while fetching quotations: {0}").format(str(e)))


# update the final negotiated rate of quotation
@frappe.whitelist(allow_guest=True)
def update_final_negotiated_rate(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)

        quotation_name = data.get("final_quotation_id")
        if not quotation_name:
            frappe.throw(_("Missing Quotation name"))

        quotation = frappe.get_doc("Quotation", quotation_name)

        quotation.is_negotiated = 1
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
        quotation.final_cfs_charge = data.get("final_cfs_charge") or ""

        # Save document
        quotation.save(ignore_permissions=True)
        frappe.db.commit()

        prev_values = [
            quotation.total_freight or "",
            quotation.ratekg or "",
            quotation.chargeable_weight or "",
            quotation.total_freight or "",
            quotation.fuel_surcharge or "",
            quotation.sc or "",
            quotation.xray or "",
            quotation.pickuporigin or "",
            quotation.xray or "",
            quotation.total_freightinr or "",
            quotation.total_landing_price or "",
            quotation.remarks or "",
            quotation.airlinevessel_name or "",
            quotation.destination_charge or "",
            quotation.transit_days or "",
            quotation.total_freight or "",
            quotation.remarks or "",
            quotation.total_landing_price or "",
            quotation.cfs_charge or "",

            quotation.mode_of_shipment or "",
            quotation.vendor_name or "",
            quotation.exchange_rate or ""
        ]

        final_negotiated_values = [
            quotation.final_ffn,
            quotation.final_rate_kg,
            quotation.final_chargeable_weight,
            quotation.final_freight_fcr,
            quotation.final_fsc,
            quotation.final_sc,
            quotation.final_xcr,
            quotation.final_pickup,
            quotation.final_xray,
            quotation.final_sum_freight_inr,
            quotation.final_gst_amount,
            quotation.final_total,
            quotation.final_others,
            quotation.final_airline,
            quotation.final_landing_price,
            quotation.final_dc,
            quotation.final_transit_days,
            quotation.final_freight_total,
            quotation.final_remarks,
            quotation.final_tat,
            quotation.final_cfs_charge
        ]

        table_html = """
            <h3>Final Negotiated Rate Details</h3>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; font-family: Arial; font-size: 13px;">
                <tr style="background-color: #f2f2f2;">
                    <th>Field</th>
                    <th>Previous Value</th>
                    <th>Final Negotiated Value</th>
                </tr>
        """

        field_labels = [
            "FFN", "Rate/KG", "Chargeable Weight", "Freight FCR", "FSC", "SC", "XCR",
            "Pickup", "X-Ray", "Sum Freight INR", "GST Amount", "Total", "Others",
            "Airline", "Landing Price", "DC", "Transit Days", "Freight Total", "Remarks", "TAT", "CFS Charge"
        ]

        for label, prev, updated in zip(field_labels, prev_values, final_negotiated_values):
            table_html += f"""
                <tr>
                    <td>{label}</td>
                    <td>{prev or '-'}</td>
                    <td>{updated or '-'}</td>
                </tr>
            """

        table_html += "</table>"

        subject = f"Final Negotiated Rate for Quotation {quotation.name}"
        message = f"""
        <p>Dear {quotation.vendor_name},</p>

        <p>The final negotiated rates for your quotation <b>{quotation.name}</b> have been finalized. Please find the comparison below:</p>

        {table_html}

        <p>Best regards,<br>
        VMS Team</p>
        """

       

        if not quotation.office_email_primary:
            frappe.throw(_("Vendor email is missing. Cannot send email."))

        frappe.custom_sendmail(
            recipients=[quotation.office_email_primary],
            subject=subject,
            message=message,
            now=True
        )

        return {
            "status": "success",
            "message": _("Final negotiated rate updated and email queued successfully."),
            "quotation": quotation.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in update_final_negotiated_rate API")
        frappe.local.response["http_status_code"] = 500
        frappe.throw(_("An error occurred while updating the final negotiated rate: {0}").format(str(e)))

