import frappe
import json
from datetime import datetime
from frappe import _
from vms.utils.custom_send_mail import custom_sendmail
from collections import defaultdict



def convert_and_validate_date(date_value):
    
    if not date_value or date_value == "0000-00-00" or date_value == "":
        return None
    
    try:
        date_obj = datetime.strptime(str(date_value), "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None
def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


@frappe.whitelist(allow_guest=True)
def get_grn_field_mappings():
    doctype_name = frappe.db.get_value("SAP Mapper PR", {'doctype_name': 'GRN'}, "name")
    mappings = frappe.get_all('SAP Mapper PR Item', filters={'parent': doctype_name}, fields=['sap_field', 'erp_field'])
    return {mapping['sap_field']: mapping['erp_field'] for mapping in mappings}


# ============= GRN API WITH GUARANTEED LOGGING =============
@frappe.whitelist(allow_guest=True)
def get_grn():
    """
    Main API endpoint to receive GRN data from SAP
    Ensures logging happens for EVERY request - success or failure
    """
    log_id = None
    data = None
    
    try:
        # Get request data
        data = frappe.request.get_json()
        
        # Create initial log entry IMMEDIATELY - before any processing
        log_id = create_initial_grn_log(
            data=data,
            sap_document_number=data.get("MBLNR", "") if data else ""
        )
        
        # Validate data
        if not data or "items" not in data:
            error_msg = "No valid data received or 'items' key not found."
            update_grn_log_failure(log_id, error_msg, None)
            return {"status": "error", "message": error_msg}
        
        grn_no = data.get("MBLNR", "")
        
        if not grn_no:
            error_msg = "MBLNR (GRN Number) not found in the data."
            update_grn_log_failure(log_id, error_msg, None)
            return {"status": "error", "message": error_msg}
        
        field_mappings = get_grn_field_mappings()
        
        if not field_mappings:
            error_msg = "No field mappings found for 'SAP Mapper GRN.'"
            update_grn_log_failure(log_id, error_msg, None)
            return {"status": "error", "message": error_msg}
        
        # Check if GRN exists
        is_existing_doc = frappe.db.exists("GRN", {"grn_number": grn_no})
        
        if is_existing_doc:
            grn_doc = frappe.get_doc("GRN", {"grn_number": grn_no})
        else:
            grn_doc = frappe.new_doc("GRN")
        
        meta = frappe.get_meta("GRN")
        grn_doc.grn_number = grn_no
        grn_doc.set("grn_items_table", [])
        
        # Process header data (non-table fields)
        header_data = {}
        for sap_field, erp_field in field_mappings.items():
            if sap_field in data:
                value = data.get(sap_field, "")
                field_meta = next((f for f in meta.fields if f.fieldname == erp_field), None)
                if field_meta and field_meta.fieldtype != "Table":
                    # Handle date fields
                    if field_meta.fieldtype == "Date":
                        value = convert_and_validate_date(value)
                    header_data[erp_field] = value
        
        # Set header fields on GRN doc
        for field_name, value in header_data.items():
            if value is not None:  # Only set non-None values
                grn_doc.set(field_name, value)
        
        # Process items (table rows)
        for idx, item in enumerate(data["items"]):
            grn_item_data = {}
            
            # Get child table meta
            child_meta = frappe.get_meta("GRN Items")  # Replace with your actual child table doctype name
            
            for sap_field, erp_field in field_mappings.items():
                if sap_field in item:
                    value = item.get(sap_field, "")
                    
                    # Get field metadata from child table
                    field_meta = next((f for f in child_meta.fields if f.fieldname == erp_field), None)
                    
                    # Handle date fields in child table
                    if field_meta and field_meta.fieldtype == "Date":
                        value = convert_and_validate_date(value)
                    
                    # Only add non-None values
                    if value is not None:
                        grn_item_data[erp_field] = value
            
            grn_doc.append("grn_items_table", grn_item_data)
        
        # Save or Update GRN
        if is_existing_doc:
            grn_doc.save()
            send_grn_emails_to_po_contacts(grn_doc)
            frappe.db.commit()
            
            response = {
                "status": "success",
                "message": "GRN Updated Successfully.",
                "GRN": grn_doc.name
            }
            
            # Update log with success
            update_grn_log_success(
                log_id=log_id,
                response=response,
                grn_doc_name=grn_doc.name,
                data=data,
                is_new=False
            )
            
            return response
            
        else:
            grn_doc.insert()
            send_grn_emails_to_po_contacts(grn_doc)
            frappe.db.commit()
            
            response = {
                "status": "success",
                "message": "GRN Created Successfully.",
                "GRN": grn_doc.name
            }
            
            # Update log with success
            update_grn_log_success(
                log_id=log_id,
                response=response,
                grn_doc_name=grn_doc.name,
                data=data,
                is_new=True
            )
            
            return response
    
    except Exception as e:
        # Capture full error traceback
        error_msg = frappe.get_traceback()
        
        # Update log with failure
        if log_id:
            update_grn_log_failure(log_id, str(e), error_msg)
        else:
            # If log creation failed, create a minimal log for the error
            try:
                create_error_only_grn_log(
                    data=data,
                    error_message=str(e),
                    traceback=error_msg
                )
            except:
                frappe.log_error("Critical: Failed to create any GRN SAP log", "GRN Log Creation Failed")
        
        # Also log to Frappe's error log
        frappe.log_error(
            title="get_grn Error",
            message=f"{error_msg}\n\nIncoming Data:\n{frappe.as_json(data) if data else 'No data'}"
        )
        
        return {"status": "error", "message": str(e)}


# ============= GRN LOGGING HELPER FUNCTIONS =============

def create_initial_grn_log(data, sap_document_number):
    """
    Create initial GRN SAP log entry when API is hit
    This MUST succeed to ensure we always have a log
    """
    try:
        log_doc = frappe.new_doc("GRN SAP Logs")
        log_doc.grn_number = sap_document_number
        log_doc.transaction_date = frappe.utils.now()
        log_doc.status = "In Progress"
        log_doc.sap_to_erp_data = json.dumps(data, indent=2, default=str)
        
        # Extract additional details from data
        if data:
            log_doc.grn_year = data.get("MJAHR", "")
            log_doc.company_code = data.get("BUKRS", "")
        
        # Store request details in total_transaction
        request_details = {
            "request_details": {
                "url": frappe.request.url,
                "method": frappe.request.method,
                "headers": {k: v for k, v in frappe.request.headers.items() if k.lower() != 'authorization'},
                "payload": data,
                "timestamp": frappe.utils.now()
            }
        }
        log_doc.total_transaction = json.dumps(request_details, indent=2, default=str)
        
        log_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return log_doc.name
        
    except Exception as e:
        # If we can't create a log, at least log the error
        frappe.log_error(
            title="Failed to create initial GRN SAP log",
            message=f"Error: {str(e)}\n\nData: {frappe.as_json(data)}"
        )
        # Re-raise to prevent silent failures
        raise


def update_grn_log_success(log_id, response, grn_doc_name, data, is_new=True):
    """
    Update GRN SAP log with success details
    """
    try:
        log_doc = frappe.get_doc("GRN SAP Logs", log_id)
        log_doc.status = "Success"
        log_doc.processed_date = frappe.utils.now()
        log_doc.erp_response = json.dumps(response, indent=2, default=str)
        
        # Link to created/updated GRN document
        log_doc.grn_link = grn_doc_name
        
        # Update total transaction with complete details
        processed_date = ensure_datetime(log_doc.processed_date)
        transaction_date = ensure_datetime(log_doc.transaction_date)
        total_transaction_data = {
            "request_details": {
                "url": frappe.request.url,
                "method": frappe.request.method,
                "headers": {k: v for k, v in frappe.request.headers.items() if k.lower() != 'authorization'},
                "payload": data,
                "timestamp": log_doc.transaction_date
            },
            "response_details": {
                "status_code": 200,
                "body": response,
                "timestamp": frappe.utils.now()
            },
            "transaction_summary": {
                "status": "Success",
                "grn_number": log_doc.grn_number,
                "grn_doc_name": grn_doc_name,
                "operation": "Created" if is_new else "Updated",
                "total_items": len(data.get("items", [])) if data else 0,
                "processing_time_seconds": (
                                                (processed_date - transaction_date).total_seconds()
                                                if processed_date and transaction_date
                                                else 0
                                            )

            }
        }
        
        # Add GRN-specific details from data
        if data:
            total_transaction_data["transaction_summary"].update({
                "grn_year": data.get("MJAHR", ""),
                "company_code": data.get("BUKRS", ""),
                "movement_type": data.get("BWART", ""),
                "posting_date": data.get("BUDAT", "")
            })
        
        log_doc.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)
        
        log_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        # Log error but don't fail the main transaction
        frappe.log_error(
            title="Failed to update GRN SAP log with success",
            message=f"Log ID: {log_id}\nError: {str(e)}\n{frappe.get_traceback()}"
        )

def ensure_datetime(value):
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            # fallback if microseconds are missing
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value



def update_grn_log_failure(log_id, error_message, traceback):
    """
    Update GRN SAP log with failure details
    """
    try:
        log_doc = frappe.get_doc("GRN SAP Logs", log_id)
        log_doc.status = "Failed"
        log_doc.processed_date = frappe.utils.now()
        log_doc.error_message = error_message
        log_doc.error_traceback = traceback or ""
        
        # Update response
        error_response = {
            "status": "error",
            "message": error_message,
            "timestamp": frappe.utils.now()
        }
        log_doc.erp_response = json.dumps(error_response, indent=2, default=str)
        
        # Update total transaction with error details
        try:
            total_transaction = json.loads(log_doc.total_transaction)
        except:
            total_transaction = {}
        
        total_transaction["response_details"] = {
            "status_code": 500,
            "body": error_response,
            "timestamp": frappe.utils.now()
        }
        
        total_transaction["error_details"] = {
            "error_message": error_message,
            "traceback": traceback,
            "timestamp": frappe.utils.now()
        }
        
        log_doc.total_transaction = json.dumps(total_transaction, indent=2, default=str)
        
        log_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        # Last resort - log to Frappe error log
        frappe.log_error(
            title="Critical: Failed to update GRN SAP log with failure",
            message=f"Log ID: {log_id}\nOriginal Error: {error_message}\nLogging Error: {str(e)}"
        )


def create_error_only_grn_log(data, error_message, traceback):
    """
    Create a minimal error log when initial log creation failed
    Last resort to ensure we capture the error
    """
    try:
        log_doc = frappe.new_doc("GRN SAP Logs")
        log_doc.grn_number = data.get("MBLNR", "") if data else ""
        log_doc.transaction_date = frappe.utils.now()
        log_doc.processed_date = frappe.utils.now()
        log_doc.status = "Failed"
        log_doc.error_message = f"Initial log creation failed. Error: {error_message}"
        log_doc.error_traceback = traceback
        log_doc.sap_to_erp_data = json.dumps(data, indent=2, default=str) if data else "{}"
        
        if data:
            log_doc.grn_year = data.get("MJAHR", "")
            log_doc.company_code = data.get("BUKRS", "")
        
        log_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        # Absolute last resort
        frappe.log_error(
            title="CRITICAL: All GRN SAP logging failed",
            message=f"Original Error: {error_message}\nLogging Error: {str(e)}\nData: {frappe.as_json(data) if data else 'None'}"
        )








def send_grn_emails_to_po_contacts(grn_doc):
    """
    Send emails to unique contacts from Purchase Orders referenced in GRN items.
    Groups GRN items by PO email2 field and sends one email per unique contact.
    
    Args:
        grn_doc: GRN document object or name
    """
    
    if isinstance(grn_doc, str):
        grn_doc = frappe.get_doc("GRN", grn_doc)
    
    email_groups = defaultdict(list)
    
    for grn_item in grn_doc.grn_items_table:
        po_no = grn_item.po_no
        
        if not po_no:
            continue
            
        try:
            po_doc = frappe.get_doc("Purchase Order", {"po_no": po_no})
            
            email2 = po_doc.email2
            
            if email2:
                email_groups[email2].append({
                    "grn_item": grn_item.grn_item,
                    "po_no": po_no,
                    "material": grn_item.material,
                    "material_description": grn_item.material_description,
                    "quantity": grn_item.quantity,
                    "uom": grn_item.uom,
                    "batch_no": grn_item.batch_no,
                    "vendor_name": grn_item.vendor_name,
                    "grn_number": grn_item.grn_number,
                    "grn_date": grn_item.grn_date
                })
        except Exception as e:
            frappe.log_error(
                message=f"Error fetching PO {po_no}: {str(e)}",
                title="GRN Email - PO Fetch Error"
            )
            continue
    
    # Send one email per unique contact
    for email, items in email_groups.items():
        try:
            send_grn_notification_email(grn_doc, email, items)
        except Exception as e:
            frappe.log_error(
                message=f"Error sending email to {email}: {str(e)}",
                title="GRN Email Sending Error"
            )

def send_grn_notification_email(grn_doc, recipient_email, grn_items):
    """
    Send email notification with GRN details
    
    Args:
        grn_doc: GRN document
        recipient_email: Email address to send to
        grn_items: List of GRN items for this recipient
    """
    
    # Build item details table for email
    items_html = """
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <thead>
            <tr style="background-color: #f2f2f2;">
                <th style="border: 1px solid #ddd; padding: 8px;">Item</th>
                <th style="border: 1px solid #ddd; padding: 8px;">PO No</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Material</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Description</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Quantity</th>
                <th style="border: 1px solid #ddd; padding: 8px;">UOM</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Batch No</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for item in grn_items:
        items_html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{item['grn_item']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item['po_no']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item['material']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item['material_description']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item['quantity']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item['uom']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{item['batch_no']}</td>
            </tr>
        """
    
    items_html += """
        </tbody>
    </table>
    """
    
    # Email subject
    subject = f"GRN Notification - {grn_doc.grn_number}"
    
    # Email message
    message = f"""
    <p>Dear User,</p>
    
    <p>Please find the details of Goods Receipt Note (GRN) below:</p>
    
    <p><strong>GRN Number:</strong> {grn_doc.grn_number}<br>
    <strong>GRN Date:</strong> {grn_doc.grn_date}<br>
    <strong>Company Code:</strong> {grn_doc.company_code}<br>
    <strong>Total Items:</strong> {len(grn_items)}</p>
    
    <h3>Item Details:</h3>
    {items_html}
    
    <p>This is an automated notification.</p>
    
    <p>Best regards,<br>
    VMS Team</p>
    """
    
    # Send email
    frappe.custom_sendmail(
        recipients=[recipient_email],
        subject=subject,
        message=message,
        now=True
    )
    
    frappe.msgprint(f"Email sent successfully to {recipient_email}")

# Example usage in a server script or button event
@frappe.whitelist()
def trigger_grn_emails(grn_name):
    """
    Whitelist function to trigger email sending from client side
    """
    grn_doc = frappe.get_doc("GRN", grn_name)
    send_grn_emails_to_po_contacts(grn_doc)
    return {"status": "success", "message": "Emails sent successfully"}
#############################old code - sap_to_grn.py@@@@@@@@@###############################


# import frappe
# import json
# from datetime import datetime

# @frappe.whitelist(allow_guest=True)
# def get_grn_field_mappings():
#     doctype_name = frappe.db.get_value("SAP Mapper PR", {'doctype_name': 'GRN'}, "name")
#     mappings = frappe.get_all('SAP Mapper PR Item', filters={'parent': doctype_name}, fields=['sap_field', 'erp_field'])
#     return {mapping['sap_field']: mapping['erp_field'] for mapping in mappings}

# @frappe.whitelist(allow_guest=True)
# def get_grn():
#     try:
#         data = frappe.request.get_json()
        
        
#         if not data or "items" not in data:
#             return {"status": "error", "message": "No valid data received or 'items' key not found."}
        
        
#         grn_no = data.get("MBLNR", "")
        
#         if not grn_no:
#             return {"status": "error", "message": "MBLNR (GRN Number) not found in the data."}
        
#         field_mappings = get_grn_field_mappings()
        
#         if not field_mappings:
#             return {"status": "error", "message": "No field mappings found for 'SAP Mapper GRN.'"}
        
#         is_existing_doc = frappe.db.exists("GRN", {"grn_number": grn_no})
        
        
#         if is_existing_doc:
#             grn_doc = frappe.get_doc("GRN", {"grn_number": grn_no})
#         else:
#             grn_doc = frappe.new_doc("GRN")
        
#         meta = frappe.get_meta("GRN")
#         grn_doc.grn_number = grn_no
#         grn_doc.set("grn_items_table", [])
        
        
       
#         header_data = {}
#         for sap_field, erp_field in field_mappings.items():
#             if sap_field in data:  
#                 value = data.get(sap_field, "")
#                 #
#                 field_meta = next((f for f in meta.fields if f.fieldname == erp_field), None)
#                 if field_meta and field_meta.fieldtype != "Table":
#                     header_data[erp_field] = value
                    
        
        
#         for field_name, value in header_data.items():
#             grn_doc.set(field_name, value)
        
        
#         for idx, item in enumerate(data["items"]):
#             grn_item_data = {}
            
            
#             for sap_field, erp_field in field_mappings.items():
#                 if sap_field in item:
#                     value = item.get(sap_field, "")
#                     grn_item_data[erp_field] = value
                    
            
            
#             grn_doc.append("grn_items_table", grn_item_data)
        
#         #
#         if is_existing_doc:
#             grn_doc.save()
#             frappe.db.commit()
#             return {"status": "success", "message": "GRN Updated Successfully.", "GRN": grn_doc.name}
#         else:
#             grn_doc.insert()
#             frappe.db.commit()
#             return {"status": "success", "message": "GRN Created Successfully.", "GRN": grn_doc.name}
    
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_grn Error")
#         return {"status": "error", "message": str(e)}

# def parse_date(value):
#     if not value:
#         return None
#     try:
#         return datetime.strptime(value, "%Y-%m-%d").date()
#     except Exception:
#         return None