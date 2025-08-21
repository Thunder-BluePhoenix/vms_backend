import frappe
import json
from frappe import _
from frappe.utils import nowdate, format_date
from datetime import datetime
from vms.utils.custom_send_mail import custom_sendmail

@frappe.whitelist(allow_guest=False)
def update_purchase_team_remarks(data, **kwargs):
    """
    Optimized API to update purchase team remarks and early delivery date for PO items
    and send email notification to vendor
    
    Expected data structure:
    {
        "po_name": "PO-XXXX",
        "items": [
            {
                "name": "row-id-12345",  # Child table row ID
                "purchase_team_remarks": "Remarks text",
                "early_delivery_date": "2024-01-15"
            }
        ]
    }
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        po_name = data.get("po_name")
        items_data = data.get("items", [])
        
        if not po_name or not items_data:
            return {
                "status": "error",
                "message": _("Purchase Order name and items data are required")
            }
        
        # Get only necessary PO fields for efficiency
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Create mapping for quick lookup
        update_items = {item.get("name"): item for item in items_data}
        
        # Track changes for email (only if email exists)
        has_email = bool(getattr(po, 'email', None))
        updated_items_details = [] if has_email else None
        updated_count = 0
        
        # Batch update child table items
        for po_item in po.po_items:
            if po_item.name in update_items:
                item_update = update_items[po_item.name]
                item_changed = False
                item_changes = {} if has_email else None
                
                # Update purchase team remarks
                if "purchase_team_remarks" in item_update:
                    old_value = po_item.purchase_team_remarks
                    new_value = item_update.get("purchase_team_remarks", "")
                    if old_value != new_value:
                        po_item.purchase_team_remarks = new_value
                        item_changed = True
                        if has_email:
                            item_changes["remarks"] = {"old": old_value or "", "new": new_value}
                
                # Update early delivery date
                if "early_delivery_date" in item_update:
                    old_value = po_item.early_delivery_date
                    new_value = item_update.get("early_delivery_date")
                    if old_value != new_value:
                        po_item.early_delivery_date = new_value
                        po_item.requested_for_earlydelivery = 1
                        item_changed = True
                        if has_email:
                            item_changes["early_delivery_date"] = {"old": old_value, "new": new_value}
                
                # Store minimal item details for email only if needed
                if item_changed:
                    updated_count += 1
                    if has_email and item_changes:
                        updated_items_details.append({
                            "item_code": po_item.product_code,
                            "item_name": po_item.product_name or po_item.material_code,
                            "qty": po_item.quantity,
                            "uom": po_item.uom,
                            "rate": po_item.rate,
                            "changes": item_changes
                        })
        
        # Save document only once
        if updated_count > 0:
            po.save(ignore_permissions=True)
            frappe.db.commit()
        
        # Send email asynchronously if needed
        email_sent = False
        email_error = None
        
        if updated_count > 0 and has_email:
            try:
                # Send email in background to avoid blocking API response
                frappe.enqueue(
                    send_po_update_notification,
                    queue='short',
                    timeout=60,
                    po_name=po_name,
                    vendor_name=getattr(po, 'supplier_name', ''),
                    po_email=po.email,
                    updated_items_details=updated_items_details,
                    po_data={
                        'name': po.name,
                        'po_date': po.po_date,
                        'vendor_code': getattr(po, 'vendor_code', 'N/A'),
                        'contact_person2': getattr(po, 'contact_person2', 'Purchase Team'),
                        'phone_no': getattr(po, 'phone_no', ''),
                        'purchase_group': getattr(po, 'purchase_group', 'N/A'),
                        'email2': getattr(po, 'email2', None)
                    }
                )
                email_sent = True
            except Exception as e:
                email_error = str(e)
                frappe.log_error(f"Email queue failed for PO {po_name}: {str(e)}", "PO Email Queue Error")
        elif updated_count > 0:
            email_error = "No email address found in PO"
        
        return {
            "status": "success",
            "message": _("Purchase team remarks updated successfully"),
            "po_name": po_name,
            "updated_items": updated_count,
            "email_queued": email_sent,
            "email_error": email_error
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Purchase Team Remarks Error")
        return {
            "status": "error",
            "message": _("Error updating purchase team remarks: {0}").format(str(e))
        }


def send_po_update_notification(po_name, vendor_name, po_email, updated_items_details, po_data):
    """
    Background task to send email notification to vendor about PO updates
    """
    try:
        # Generate email content
        subject = f"Purchase Order Early Delivery Request - {po_name}"
        message = generate_optimized_email_body(po_data, updated_items_details, vendor_name)
        
        # Prepare recipients
        recipients = [po_email]
        cc = [po_data.get('email2')] if po_data.get('email2') else None
        
        # Send email
        frappe.custom_sendmail(
            recipients=recipients,
            cc=cc,
            subject=subject,
            message=message,
            now=True,
            reference_doctype="Purchase Order",
            reference_name=po_name
        )
        
        # Log success
        frappe.logger().info(f"Email sent successfully for PO {po_name} to {po_email}")
        
    except Exception as e:
        frappe.log_error(f"Background email failed for PO {po_name}: {str(e)}", "PO Background Email Error")


def generate_optimized_email_body(po_data, updated_items, vendor_name):
    """
    Generate simplified and faster email body
    """
    current_date = format_date(nowdate())
    po_date = format_date(po_data.get('po_date')) if po_data.get('po_date') else 'N/A'
    
    # Build items section efficiently
    items_html = ""
    for idx, item in enumerate(updated_items, 1):
        # Calculate total safely
        try:
            total = float(item['qty']) * float(item['rate'])
            total_str = f"₹{total:,.2f}"
        except (ValueError, TypeError):
            total_str = "₹0.00"
            
        items_html += f"""
        <div style="border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">Item #{idx}: {item['item_name']}</h4>
            <p style="margin: 5px 0;"><strong>Code:</strong> {item['item_code']} | <strong>Qty:</strong> {item['qty']} {item['uom']} | <strong>Rate:</strong> ₹{item['rate']} | <strong>Total:</strong> {total_str}</p>
        """
        
        # Add changes
        if 'remarks' in item['changes']:
            old_remarks = item['changes']['remarks']['old'] or 'None'
            new_remarks = item['changes']['remarks']['new'] or 'None'
            items_html += f"""
            <div style="background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 3px;">
                <strong>Purchase Team Remarks:</strong><br>
                <span style="color: #888;">Previous:</span> {old_remarks}<br>
                <span style="color: #007bff;">Updated:</span> {new_remarks}
            </div>
            """
        
        if 'early_delivery_date' in item['changes']:
            old_date = format_date(item['changes']['early_delivery_date']['old']) if item['changes']['early_delivery_date']['old'] else 'Not set'
            new_date = format_date(item['changes']['early_delivery_date']['new']) if item['changes']['early_delivery_date']['new'] else 'Not set'
            items_html += f"""
            <div style="background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 3px;">
                <strong>Early Delivery Date:</strong><br>
                <span style="color: #888;">Previous:</span> {old_date}<br>
                <span style="color: #28a745;">Updated:</span> {new_date}
            </div>
            """
        
        items_html += "</div>"
    
    # Simplified email template
    email_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
        <div style="background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
            <h2 style="margin: 0;">Purchase Order Update Notification</h2>
        </div>
        
        <div style="background: white; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px;">
            <p>Dear {vendor_name or 'Valued Partner'},</p>
            <p>Our purchase team has updated the remarks and early delivery requirements for your Purchase Order.</p>
            
            <div style="background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h3 style="margin: 0 0 10px 0; color: #333;">PO Details</h3>
                <p style="margin: 5px 0;"><strong>PO Number:</strong> {po_data['name']}</p>
                <p style="margin: 5px 0;"><strong>PO Date:</strong> {po_date}</p>
                <p style="margin: 5px 0;"><strong>Vendor Code:</strong> {po_data.get('vendor_code', 'N/A')}</p>
                <p style="margin: 5px 0;"><strong>Update Date:</strong> {current_date}</p>
            </div>
            
            <h3 style="color: #333;">Updated Items</h3>
            {items_html}
            
            <div style="background: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #ffc107;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">Action Required</h4>
                <ul style="margin: 0; color: #856404;">
                    <li>Review the updated remarks and delivery requirements</li>
                    <li>Acknowledge receipt by replying to this email</li>
                    <li>Update your delivery schedule if needed</li>
                    <li>Contact our purchase team for any questions</li>
                </ul>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">Contact Information</h4>
                <p style="margin: 5px 0;"><strong>Contact Person:</strong> {po_data.get('contact_person2', 'Purchase Team')}</p>
                <p style="margin: 5px 0;"><strong>Phone:</strong> {po_data.get('phone_no', 'Contact via email')}</p>
                <p style="margin: 5px 0;"><strong>Purchase Group:</strong> {po_data.get('purchase_group', 'N/A')}</p>
            </div>
            
            <p>Thank you for your continued partnership.</p>
            <p><strong>Best regards,<br>Purchase Team</strong></p>
        </div>
        
        <div style="text-align: center; margin-top: 15px; color: #666; font-size: 12px;">
            <p>This is an automated notification. Please reply to this email for any queries.</p>
        </div>
    </div>
    """
    
    return email_body


@frappe.whitelist()
def debug_email_configuration(**kwargs):
    """
    Lightweight debug function to check email configuration
    """
    try:
        debug_info = {}
        
        # Quick email account check
        email_accounts = frappe.db.count("Email Account", {"enable_outgoing": 1})
        debug_info["outgoing_email_accounts"] = email_accounts
        
        # Check default email
        try:
            default_email = frappe.db.get_value("Email Account", {"default_outgoing": 1}, ["email_id", "smtp_server"])
            debug_info["default_email_configured"] = bool(default_email)
            if default_email:
                debug_info["default_email_id"] = default_email[0] if isinstance(default_email, tuple) else default_email
        except:
            debug_info["default_email_configured"] = False
        
        # Quick queue check
        pending_count = frappe.db.count("Email Queue", {"status": ["in", ["Not Sent", "Sending"]]})
        debug_info["pending_emails_count"] = pending_count
        
        return {
            "status": "success",
            "debug_info": debug_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@frappe.whitelist(allow_guest=False)
def update_vendor_approval_status(data):
    """
    API to update vendor approval status and remarks for PO items
    
    Expected data structure:
    {
        "po_name": "PO-XXXX",
        "items": [
            {
                "name": "row-id-12345",  # Child table row ID
                "approved_by_vendor": 1,
                "rejected_by_vendor": 0,
                "vendor_remarks": "Approved with conditions"
            }
        ]
    }
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        po_name = data.get("po_name")
        items_data = data.get("items", [])
        
        if not po_name:
            frappe.throw(_("Purchase Order name is required"))
        
        if not items_data:
            frappe.throw(_("Items data is required"))
        
        # Get the Purchase Order document
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Create a mapping of child row name (ID) to item data for quick lookup
        update_items = {item.get("name"): item for item in items_data}
        
        # Update the child table items
        updated_count = 0
        for po_item in po.po_items:
            if po_item.name in update_items:
                item_update = update_items[po_item.name]
                
                # Update vendor approval fields
                if "approved_by_vendor" in item_update:
                    po_item.approved_by_vendor = item_update.get("approved_by_vendor")
                
                if "rejected_by_vendor" in item_update:
                    po_item.rejected_by_vendor = item_update.get("rejected_by_vendor")
                
                if "vendor_remarks" in item_update:
                    po_item.vendor_remarks = item_update.get("vendor_remarks")
                
                updated_count += 1
        
        # Save the document
        po.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": _("Vendor approval status updated successfully"),
            "po_name": po_name,
            "updated_items": updated_count
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Vendor Approval Status Error")
        return {
            "status": "error",
            "message": _("Error updating vendor approval status: {0}").format(str(e))
        }


@frappe.whitelist(allow_guest=False)
def get_purchase_order_items(data):
    """
    API to get all child table data of a Purchase Order as complete dictionaries
    
    Expected data structure:
    {
        "po_name": "PO-XXXX"
    }
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        po_name = data.get("po_name")
        
        if not po_name:
            frappe.throw(_("Purchase Order name is required"))
        
        # Get the Purchase Order document
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Prepare items data - return complete item dictionaries
        items_data = []
        
        for item in po.po_items:
            # Get the complete item as dictionary
            item_dict = item.as_dict()
            items_data.append(item_dict)
        
        # Also get main PO data as dictionary
        po_dict = po.as_dict()
        
        return {
            "status": "success",
            # "po_data": po_dict,  # Complete PO document as dict
            "items": items_data,  # Complete items as dict array
            "total_items": len(items_data)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Purchase Order Items Error")
        return {
            "status": "error",
            "message": _("Error getting purchase order items: {0}").format(str(e))
        }

# Alternative method if you prefer to pass po_name as URL parameter
@frappe.whitelist(allow_guest=False)
def get_purchase_order_items_by_name(po_name):
    """
    Alternative API to get all child table data by passing po_name as parameter
    Usage: /api/method/your_app.purchase_order.get_purchase_order_items_by_name?po_name=PO-XXXX
    """
    return get_purchase_order_items({"po_name": po_name})


# Utility API to update single item by child row ID
@frappe.whitelist(allow_guest=False)
def update_single_po_item_by_id(data):
    """
    Utility API to update a single PO item by its child row ID
    
    Expected data structure:
    {
        "po_name": "PO-XXXX",
        "item_id": "row-id-12345",
        "fields": {
            "purchase_team_remarks": "New remarks",
            "early_delivery_date": "2024-01-15",
            "approved_by_vendor": 1,
            "vendor_remarks": "Approved"
        }
    }
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        po_name = data.get("po_name")
        item_id = data.get("item_id")
        fields_to_update = data.get("fields", {})
        
        if not po_name:
            frappe.throw(_("Purchase Order name is required"))
        
        if not item_id:
            frappe.throw(_("Item ID is required"))
            
        if not fields_to_update:
            frappe.throw(_("Fields to update are required"))
        
        # Get the Purchase Order document
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Find the specific item by ID
        item_found = False
        for po_item in po.po_items:
            if po_item.name == item_id:
                # Update only the provided fields
                for field_name, field_value in fields_to_update.items():
                    if hasattr(po_item, field_name):
                        setattr(po_item, field_name, field_value)
                
                item_found = True
                break
        
        if not item_found:
            frappe.throw(_("Item with ID {0} not found in Purchase Order {1}").format(item_id, po_name))
        
        # Save the document
        po.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": _("Purchase Order item updated successfully"),
            "po_name": po_name,
            "item_id": item_id,
            "updated_fields": list(fields_to_update.keys())
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Single PO Item Error")
        return {
            "status": "error",
            "message": _("Error updating purchase order item: {0}").format(str(e))
        }
    

# send mail to vendor for po details
@frappe.whitelist(allow_guest=True)
def po_details_mail(po_id):
    try:
        if not po_id:
            return {
                "status": "error",
                "message": "Missing Purchase Order ID"
            }

        po = frappe.get_doc("Purchase Order", po_id)

        if po.email:
            subject = "Here is your PO details"
            body = "Please check your PO details."
            frappe.custom_sendmail(
                recipients=[po.email],
                subject=subject,
                message=body
            )
            po.sent_to_vendor = 1
            po.save(ignore_permissions=True)
            return {
                "status": "success",
                "message": f"Email sent to {po.email}"
            }
        else:
            return {
                "status": "error",
                "message": "No email found in Purchase Order"
            }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "po_details_mail")
        return {
            "status": "error",
            "message": str(e)
        }