import frappe
import json
# from frappe.utils import parse_date
from vms.utils.custom_send_mail import custom_sendmail

@frappe.whitelist(allow_guest=True)
def get_field_mappings():
    doctype_name = frappe.db.get_value("SAP Mapper PR", filters={'doctype_name': 'Purchase Requisition'}, fieldname='name')
    mappings = frappe.get_all('SAP Mapper PR Item', filters={'parent': doctype_name}, fields=['sap_field', 'erp_field'])
    return {mapping['sap_field']: mapping['erp_field'] for mapping in mappings}


# @frappe.whitelist(allow_guest=True)
# def get_pr():
#     try:
#         data = frappe.request.get_json()
#         if not data or "items" not in data:
#             return {"status": "error", "message": "No valid data received or 'items' key not found."}

#         pr_no = data.get("pr_no", "")
#         field_mappings = get_field_mappings()

#         # Get or create PR doc
#         if frappe.db.exists("Purchase Requisition", {"purchase_requisition_number": pr_no}):
#             pr_doc = frappe.get_doc("Purchase Requisition", {"purchase_requisition_number": pr_no})
#             pr_doc.set("pr_items", [])
#         else:
#             pr_doc = frappe.new_doc("Purchase Requisition")

#         pr_doc.purchase_requisition_number = pr_no

#         meta = frappe.get_meta("Purchase Requisition")
#         pr_plant_value = None

#         for item in data["items"]:
#             pr_item_data = {}
#             for sap_field, erp_field in field_mappings.items():
#                 value = item.get(sap_field, "")
#                 field_meta = next((field for field in meta.fields if field.fieldname == erp_field), None)

#                 if field_meta and field_meta.fieldtype == 'Date':
#                     pr_item_data[erp_field] = parse_date(value)
#                 else:
#                     pr_item_data[erp_field] = value

#             pr_doc.append("pr_items", pr_item_data)

#             if not pr_plant_value and "plant" in item:
#                 pr_plant_value = item["plant"]

#         if pr_plant_value:
#             pr_doc.pr_plant = pr_plant_value

#         if pr_doc.is_new():
#             pr_doc.insert(ignore_permissions=True)
#             frappe.db.commit()
#             return {"status": "success", "message": "Purchase Requisition Created Successfully."}
#         else:
#             pr_doc.save(ignore_permissions=True)
#             frappe.db.commit()
#             return {"status": "success", "message": "Purchase Requisition Updated Successfully."}

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), "create_purchase_requisition Error")
#         return {"status": "error", "message": str(e)}


# create pr and purchase sap logs
# @frappe.whitelist(allow_guest=True)
# def get_pr():
#     try:
#         data = frappe.request.get_json()
#         if not data or "items" not in data:
#             return {"status": "error", "message": "No valid data received or 'items' key not found."}

#         pr_no = data.get("pr_no", "")
#         field_mappings = get_field_mappings()

#         # Get or create PR doc
#         if frappe.db.exists("Purchase Requisition", {"purchase_requisition_number": pr_no}):
#             pr_doc = frappe.get_doc("Purchase Requisition", {"purchase_requisition_number": pr_no})
#             pr_doc.set("pr_items", [])
#         else:
#             pr_doc = frappe.new_doc("Purchase Requisition")

#         pr_doc.purchase_requisition_number = pr_no

#         meta = frappe.get_meta("Purchase Requisition")
#         pr_plant_value = None

#         for item in data["items"]:
#             pr_item_data = {}
#             for sap_field, erp_field in field_mappings.items():
#                 value = item.get(sap_field, "")
#                 field_meta = next((field for field in meta.fields if field.fieldname == erp_field), None)

#                 if field_meta and field_meta.fieldtype == 'Date':
#                     pr_item_data[erp_field] = parse_date(value)
#                 else:
#                     pr_item_data[erp_field] = value

#             pr_doc.append("pr_items", pr_item_data)

#             if not pr_plant_value and "plant" in item:
#                 pr_plant_value = item["plant"]

#         if pr_plant_value:
#             pr_doc.pr_plant = pr_plant_value

#         if pr_doc.is_new():
#             pr_doc.insert(ignore_permissions=True)
#             frappe.db.commit()

#             response = {
#                 "status": "success",
#                 "message": "Purchase Requisition Created Successfully.",
#                 "pr": pr_doc.name
#             }

#             try:
#                 log_doc = frappe.new_doc("Purchase SAP Logs")
#                 log_doc.purchase_requisition_link = pr_doc.name
#                 log_doc.sap_to_erp_data = json.dumps(data, indent=2)
#                 log_doc.erp_response = json.dumps(response, indent=2)
#                 total_transaction_data = {
#                     "request_details": {
#                         "url": frappe.request.url,
#                         "headers": {k: v for k, v in frappe.request.headers.items() if k.lower() != 'authorization'},
#                         "auth_user": frappe.session.user,
#                         "payload": data
#                     },
#                     "response_details": {
#                         "status_code": 200,
#                         "headers": {},
#                         "body": response
#                     },
#                     "transaction_summary": {
#                         "status": response.get("status"),
#                         "pr_code": pr_no,
#                         "error_details": "",
#                         "timestamp": frappe.utils.now(),
#                         "sap_client_code": data.get("client_code", ""),
#                         "pr_doc_name": pr_doc.name,
#                         "pr_type": pr_doc.get("purchase_requisition_type"),
#                         "name_for_sap": pr_doc.get("company")
#                     }
#                 }
#                 log_doc.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)

#                 log_doc.insert(ignore_permissions=True)
#                 frappe.db.commit()
#             except Exception as log_err:
#                 frappe.log_error("Purchase Requisition SAP Log Creation Failed", frappe.get_traceback())

#             return response

#         else:
#             pr_doc.save(ignore_permissions=True)
#             frappe.db.commit()
#             return {"status": "success", "message": "Purchase Requisition Updated Successfully."}

#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), "create_purchase_requisition Error")
#         return {"status": "error", "message": str(e)}






@frappe.whitelist(allow_guest=True)
def get_pr():
    """
    Main API endpoint to receive PR data from SAP
    Ensures logging happens for EVERY request - success or failure
    """
    log_id = None
    data = None
    
    try:
        # Get request data
        data = frappe.request.get_json()
        
        # Create initial log entry IMMEDIATELY
        log_id = create_initial_sap_log(
            data=data,
            transaction_type="Purchase Requisition",
            sap_document_number=data.get("pr_no", "") if data else ""
        )
        
        # Validate data
        if not data or "items" not in data:
            error_msg = "No valid data received or 'items' key not found."
            update_sap_log_failure(log_id, error_msg, None)
            return {"status": "error", "message": error_msg}

        pr_no = data.get("pr_no", "")
        field_mappings = get_field_mappings()

        # Get or create PR doc
        if frappe.db.exists("Purchase Requisition", {"purchase_requisition_number": pr_no}):
            pr_doc = frappe.get_doc("Purchase Requisition", {"purchase_requisition_number": pr_no})
            pr_doc.set("pr_items", [])
        else:
            pr_doc = frappe.new_doc("Purchase Requisition")

        pr_doc.purchase_requisition_number = pr_no

        meta = frappe.get_meta("Purchase Requisition")
        pr_plant_value = None

        for item in data["items"]:
            pr_item_data = {}
            for sap_field, erp_field in field_mappings.items():
                value = item.get(sap_field, "")
                field_meta = next((field for field in meta.fields if field.fieldname == erp_field), None)

                if field_meta and field_meta.fieldtype == 'Date':
                    pr_item_data[erp_field] = parse_date(value)
                else:
                    pr_item_data[erp_field] = value

            pr_doc.append("pr_items", pr_item_data)

            if not pr_plant_value and "plant" in item:
                pr_plant_value = item["plant"]

        if pr_plant_value:
            pr_doc.pr_plant = pr_plant_value

        # Save or Update PR
        if pr_doc.is_new():
            pr_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            response = {
                "status": "success",
                "message": "Purchase Requisition Created Successfully.",
                "pr": pr_doc.name
            }
            
            # Update log with success
            update_sap_log_success(
                log_id=log_id,
                response=response,
                frappe_doc_type="Purchase Requisition",
                frappe_doc_name=pr_doc.name,
                data=data,
                po_doc=None
            )
            
            return response
            
        else:
            pr_doc.save(ignore_permissions=True)
            frappe.db.commit()

            response = {
                "status": "success",
                "message": "Purchase Requisition Updated Successfully.",
                "pr": pr_doc.name
            }
            
            # Update log with success
            update_sap_log_success(
                log_id=log_id,
                response=response,
                frappe_doc_type="Purchase Requisition",
                frappe_doc_name=pr_doc.name,
                data=data,
                po_doc=None
            )
            
            return response

    except Exception as e:
        # Capture full error traceback
        error_msg = frappe.get_traceback()
        
        # Update log with failure
        if log_id:
            update_sap_log_failure(log_id, str(e), error_msg)
        else:
            # If log creation failed, create a minimal log for the error
            try:
                create_error_only_log(
                    data=data,
                    transaction_type="Purchase Requisition",
                    error_message=str(e),
                    traceback=error_msg
                )
            except:
                frappe.log_error("Critical: Failed to create any SAP log", "SAP Log Creation Failed")
        
        # Also log to Frappe's error log
        frappe.log_error(
            title="get_pr Error",
            message=f"{error_msg}\n\nIncoming Data:\n{frappe.as_json(data) if data else 'No data'}"
        )
        
        frappe.db.rollback()
        return {"status": "error", "message": str(e)}
    



# ============= LOGGING HELPER FUNCTIONS =============
import frappe

from frappe import _
import json
from datetime import datetime


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


@frappe.whitelist(allow_guest=True)
def get_po_field_mappings():
    doctype_name = frappe.db.get_value("SAP Mapper PR", {'doctype_name': 'Purchase Order'}, "name")
    mappings = frappe.get_all('SAP Mapper PR Item', filters={'parent': doctype_name}, fields=['sap_field', 'erp_field'])
    return {mapping['sap_field']: mapping['erp_field'] for mapping in mappings}


# @frappe.whitelist(allow_guest=True)
# def get_po():
#     try:
#         data = frappe.request.get_json()

#         if not data or "items" not in data:
#             return {"status": "error", "message": "No valid data received or 'items' key not found."}

#         po_no = data.get("po_no", "")
#         field_mappings = get_po_field_mappings()

#         if not field_mappings:
#             return {"status": "error", "message": "No field mappings found for 'SAP Mapper PO'"}

#         po_doc = (frappe.get_doc("Purchase Order", {"po_number": po_no})
#                   if frappe.db.exists("Purchase Order", {"po_number": po_no})
#                   else frappe.new_doc("Purchase Order"))

#         meta = frappe.get_meta("Purchase Order")
#         po_doc.po_number = po_no
#         po_doc.set("po_items", [])

#         for item in data["items"]:
#             po_item_data = {}
#             for sap_field, erp_field in field_mappings.items():
#                 value = item.get(sap_field, "")
#                 field = next((f for f in meta.fields if f.fieldname == erp_field), None)
#                 po_item_data[erp_field] = parse_date(value) if field and field.fieldtype == 'Date' else value

#             # Map top-level fields
#             for field in meta.fields:
#                 if field.fieldname in po_item_data:
#                     po_doc.set(field.fieldname, po_item_data[field.fieldname])

#             po_doc.append("po_items", po_item_data)

#         sap_status = data.get("status", "")
#         po_doc.sap_status = sap_status
        
#         if po_doc.is_new():
            
#             po_doc.insert()

#             # po_id = po_doc.name
#             # po_creation_send_mail(po_id)

#             return {"status": "success", "message": "Purchase Order Created Successfully.", "po": po_doc.name}
#         else:
#             po_doc.save()

#             po_id = po_doc.name
#             # po_update_send_mail(po_id)
#             if sap_status == "REVOKED":
#                 po_doc.sent_to_vendor = 0
#                 revocked_po_details_mail(po_id)

#             return {"status": "success", "message": "Purchase Order Updated Successfully.", "po": po_doc.name}

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_po Error")
#         return {"status": "error", "message": str(e)}






# @frappe.whitelist(allow_guest=True)
# def get_po():
#     try:
#         data = frappe.request.get_json()

#         if not data or "items" not in data:
#             return {"status": "error", "message": "No valid data received or 'items' key not found."}

#         po_no = data.get("po_no", "")
#         field_mappings = get_po_field_mappings()

#         if not field_mappings:
#             return {"status": "error", "message": "No field mappings found for 'SAP Mapper PO'"}

#         po_doc = (frappe.get_doc("Purchase Order", {"po_number": po_no})
#                   if frappe.db.exists("Purchase Order", {"po_number": po_no})
#                   else frappe.new_doc("Purchase Order"))

#         meta = frappe.get_meta("Purchase Order")
#         po_doc.po_number = po_no
#         po_doc.set("po_items", [])

#         for item in data["items"]:
#             po_item_data = {}
#             for sap_field, erp_field in field_mappings.items():
#                 value = item.get(sap_field, "")
#                 field = next((f for f in meta.fields if f.fieldname == erp_field), None)
#                 po_item_data[erp_field] = parse_date(value) if field and field.fieldtype == 'Date' else value

#             for field in meta.fields:
#                 if field.fieldname in po_item_data:
#                     po_doc.set(field.fieldname, po_item_data[field.fieldname])

#             po_doc.append("po_items", po_item_data)

#         sap_status = data.get("status", "")
#         po_doc.sap_status = sap_status
#         po_doc.status = sap_status

#         if po_doc.is_new():
#             po_doc.insert()
#             frappe.db.commit() 

#             if not frappe.db.exists("Purchase Order", po_doc.name):
#                 frappe.throw(f"Purchase Order {po_doc.name} not found in DB after insert")

#             response = {
#                 "status": "success",
#                 "message": "Purchase Order Created Successfully.",
#                 "po": po_doc.name
#             }

#             try:
#                 log_doc = frappe.new_doc("Purchase SAP Logs")
#                 log_doc.purchase_order_link = po_doc.name
#                 frappe.log_error("SAP Log Link Debug", f"Link set to: {po_doc.name}")
#                 log_doc.sap_to_erp_data = json.dumps(data, indent=2)
#                 log_doc.erp_response = json.dumps(response, indent=2)
#                 total_transaction_data = {
#                     "request_details": {
#                         "url": frappe.request.url,
#                         "headers": {k: v for k, v in frappe.request.headers.items() if k.lower() != 'authorization'},
#                         "auth_user": frappe.session.user,
#                         "payload": data
#                     },
#                     "response_details": {
#                         "status_code": 200,
#                         "headers": {},
#                         "body": response
#                     },
#                     "transaction_summary": {
#                         "status": response.get("status"),
#                         "po_number": po_no,
#                         "error_details": "",
#                         "timestamp": frappe.utils.now(),
#                         "sap_client_code": data.get("client_code", ""),
#                         "po_doc_name": po_doc.name,
#                         "po_type": po_doc.get("purchase_order_type"),
#                         "name_for_sap": po_doc.get("supplier")
#                     }
#                 }
#                 log_doc.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)

#                 log_doc.insert(ignore_permissions=True)
#                 frappe.db.commit()
#             except Exception as log_err:
#                 frappe.log_error("Purchase SAP Log Creation Failed", frappe.get_traceback())

#             return response

#         else:
#             po_doc.save()
#             po_id = po_doc.name

#             if sap_status == "REVOKED":
#                 po_doc.sent_to_vendor = 0
#                 revocked_po_details_mail(po_id)

#             return {
#                 "status": "success",
#                 "message": "Purchase Order Updated Successfully.",
#                 "po": po_doc.name
#             }

#     except Exception as e:
#         frappe.log_error(
#             title="get_po Error",
#             message=f"{frappe.get_traceback()}\n\nIncoming Data:\n{frappe.as_json(frappe.request.get_json())}"
#         )
#         return {"status": "error", "message": str(e)}


# create po and puchase sap logs
@frappe.whitelist(allow_guest=True)
def get_po():
    """
    Main API endpoint to receive PO data from SAP
    Ensures logging happens for EVERY request - success or failure
    """
    log_id = None
    data = None
    
    try:
        # Get request data
        data = frappe.request.get_json()
        
        # Create initial log entry IMMEDIATELY - before any processing
        log_id = create_initial_sap_log(
            data=data,
            transaction_type="Purchase Order",
            sap_document_number=data.get("po_no", "") if data else ""
        )
        
        # Validate data
        if not data or "items" not in data:
            error_msg = "No valid data received or 'items' key not found."
            update_sap_log_failure(log_id, error_msg, None)
            return {"status": "error", "message": error_msg}

        po_no = data.get("po_no", "")
        field_mappings = get_po_field_mappings()

        if not field_mappings:
            error_msg = "No field mappings found for 'SAP Mapper PO'"
            update_sap_log_failure(log_id, error_msg, None)
            return {"status": "error", "message": error_msg}

        # Check if PO exists
        po_doc = (frappe.get_doc("Purchase Order", {"po_number": po_no})
                  if frappe.db.exists("Purchase Order", {"po_number": po_no})
                  else frappe.new_doc("Purchase Order"))

        meta = frappe.get_meta("Purchase Order")
        po_doc.po_number = po_no
        po_doc.set("po_items", [])

        # Process items
        for item in data["items"]:
            po_item_data = {}
            for sap_field, erp_field in field_mappings.items():
                value = item.get(sap_field, "")
                field = next((f for f in meta.fields if f.fieldname == erp_field), None)
                po_item_data[erp_field] = parse_date(value) if field and field.fieldtype == 'Date' else value

            for field in meta.fields:
                if field.fieldname in po_item_data:
                    po_doc.set(field.fieldname, po_item_data[field.fieldname])

            po_doc.append("po_items", po_item_data)

        sap_status = data.get("status", "")
        po_doc.sap_status = sap_status
        po_doc.status = sap_status

        # Save or Update PO
        if po_doc.is_new():
            po_doc.insert()
            frappe.db.commit()

            if not frappe.db.exists("Purchase Order", po_doc.name):
                error_msg = f"Purchase Order {po_doc.name} not found in DB after insert"
                update_sap_log_failure(log_id, error_msg, None)
                frappe.throw(error_msg)

            po_id = po_doc.name
            # po_creation_send_mail(po_id)
            po_creation_email_to_purchase(po_id)

            response = {
                "status": "success",
                "message": "Purchase Order Created Successfully.",
                "po": po_doc.name
            }
            
            # Update log with success
            update_sap_log_success(
                log_id=log_id,
                response=response,
                frappe_doc_type="Purchase Order",
                frappe_doc_name=po_doc.name,
                data=data,
                po_doc=po_doc
            )
            
            return response

        else:
            po_doc.save()
            po_id = po_doc.name
            # po_update_send_mail(po_id)
            po_updation_email_to_purchase(po_id)

            if sap_status == "REVOKED":
                po_doc.sent_to_vendor = 0
                revocked_po_details_mail(po_id)

            response = {
                "status": "success",
                "message": "Purchase Order Updated Successfully.",
                "po": po_doc.name
            }
            
            # Update log with success
            update_sap_log_success(
                log_id=log_id,
                response=response,
                frappe_doc_type="Purchase Order",
                frappe_doc_name=po_doc.name,
                data=data,
                po_doc=po_doc
            )
            
            return response

    except Exception as e:
        # Capture full error traceback
        error_msg = frappe.get_traceback()
        
        # Update log with failure
        if log_id:
            update_sap_log_failure(log_id, str(e), error_msg)
        else:
            # If log creation failed, create a minimal log for the error
            try:
                create_error_only_log(
                    data=data,
                    transaction_type="Purchase Order",
                    error_message=str(e),
                    traceback=error_msg
                )
            except:
                frappe.log_error("Critical: Failed to create any SAP log", "SAP Log Creation Failed")
        
        # Also log to Frappe's error log
        frappe.log_error(
            title="get_po Error",
            message=f"{error_msg}\n\nIncoming Data:\n{frappe.as_json(data) if data else 'No data'}"
        )
        
        return {"status": "error", "message": str(e)}

# send mail creation of po
@frappe.whitelist()
def po_creation_send_mail(po_id):
    try:
        po_doc = frappe.get_doc("Purchase Order", po_id)
        vendor_code_id = po_doc.vendor_code

        # Find parent Company Vendor Code where child Vendor Code table has a row with matching vendor_code
        com_vendor_code_name = frappe.db.get_value(
            "Vendor Code", {"vendor_code": vendor_code_id}, "parent"
        )

        if not com_vendor_code_name:
            return {"status": "error", "message": "No matching Company Vendor Code found for vendor_code."}

        com_vendor_doc = frappe.get_doc("Company Vendor Code", com_vendor_code_name)

        vendor_ref_no = com_vendor_doc.vendor_ref_no
        vendor_master_doc = frappe.get_doc("Vendor Master", vendor_ref_no)

        vendor_email = vendor_master_doc.office_email_primary or vendor_master_doc.office_email_secondary
        vendor_name = vendor_master_doc.vendor_name
        if not vendor_email:
            return {"status": "error", "message": "No email found for vendor."}

        print_format = frappe.db.get_single_value("Print Format Settings", "purchase_order_print_format")

        pdf_data = frappe.get_print(doctype="Purchase Order", name=po_id, print_format=print_format, as_pdf=True)
        file_name = f"{po_doc.name}.pdf"

        # Send email with attachment
        message = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #28a745;">New Purchase Order Created</h2>
                        
                        <p>Dear {vendor_name},</p>
                        
                        <p>We are pleased to inform you that a new Purchase Order has been created. Please find the attached document for your reference.</p>
                        
                        <div style="background-color: #e9f7ef; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                            <h3 style="margin-top: 0;">Purchase Order Details:</h3>
                            <p><strong>Purchase Order Number:</strong> {po_doc.name}</p>
                        </div>
                        
                        <p>Kindly review the attached Purchase Order and proceed with the necessary arrangements at your earliest convenience.</p>
                        
                        <p>For any queries or clarifications, please feel free to reach out to us.</p>
                        
                        <p>Thank you for your continued support.</p>
                        
                        <p>Best regards,<br>
                        VMS Team</p>
                    </div>
                    """

        frappe.custom_sendmail(
            recipients=[vendor_email],
            subject="New Purchase Order Created",
            message=message,
            attachments=[{
                "fname": file_name,
                "fcontent": pdf_data
            }]
        )

        return {
            "status": "success",
            "vendor_name": vendor_name,
            "message": "Email sent successfully to vendor.",
            "email": vendor_email,
            "file_name": file_name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO Creation Email Error")
        return {
            "status": "error",
            "message": "An error occurred.",
            "error": str(e)
        }



# send mail updation of po
@frappe.whitelist()
def po_update_send_mail(po_id):
    try:
        po_doc = frappe.get_doc("Purchase Order", po_id)
        vendor_code_id = po_doc.vendor_code

        # Find parent Company Vendor Code where child Vendor Code table has a row with matching vendor_code
        com_vendor_code_name = frappe.db.get_value(
            "Vendor Code", {"vendor_code": vendor_code_id}, "parent"
        )

        if not com_vendor_code_name:
            return {"status": "error", "message": "No matching Company Vendor Code found for vendor_code."}

        com_vendor_doc = frappe.get_doc("Company Vendor Code", com_vendor_code_name)

        vendor_ref_no = com_vendor_doc.vendor_ref_no
        vendor_master_doc = frappe.get_doc("Vendor Master", vendor_ref_no)

        vendor_email = vendor_master_doc.office_email_primary or vendor_master_doc.office_email_secondary
        vendor_name = vendor_master_doc.vendor_name
        if not vendor_email:
            return {"status": "error", "message": "No email found for vendor."}

        print_format = frappe.db.get_single_value("Print Format Settings", "purchase_order_print_format")

        pdf_data = frappe.get_print(doctype="Purchase Order", name=po_id, print_format=print_format, as_pdf=True)
        file_name = f"{po_doc.name}.pdf"

        # Send email with attachment
        frappe.custom_sendmail(
            recipients=[vendor_email],
            subject="New Purchase Order Created",
            message=f"Dear {vendor_name},<br><br>A Purchase Order <strong>{po_doc.name}</strong> has been Updated. Please find the attached document.",
            attachments=[{
                "fname": file_name,
                "fcontent": pdf_data
            }]
        )

        return {
            "status": "success",
            "vendor_name": vendor_name,
            "message": "Email sent successfully to vendor.",
            "email": vendor_email,
            "file_name": file_name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO Creation Email Error")
        return {
            "status": "error",
            "message": "An error occurred.",
            "error": str(e)
        }
    
# PO Creation Email to Purchase Team    
def po_creation_email_to_purchase(po_id):
    try:
        if not po_id:
            frappe.throw("Failed to send email: Purchase Order name is missing.")

        purchase_order = frappe.get_doc("Purchase Order", po_id)

        subject = f"A New Purchase Order has been created - {po_id}"

        message = f"""
            Dear Purchase Team,<br><br>
            A new Purchase Order <strong>{po_id}</strong> has been created.<br><br>
            Please review the details and take the necessary action.<br><br>
            Regards,<br>
            VMS Team
        """

        frappe.custom_sendmail(
            recipients=[purchase_order.email2],
            subject=subject,
            message=message,
            now=True
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in po_creation_email_to_purchase")


# PO Updation Email to Purchase Team    
def po_updation_email_to_purchase(po_id):
    try:
        if not po_id:
            frappe.throw("Failed to send email: Purchase Order name is missing.")

        purchase_order = frappe.get_doc("Purchase Order", po_id)

        subject = f"Purchase Order Updated - {po_id}"

        message = f"""
            Dear Purchase Team,<br><br>
            The Purchase Order <strong>{po_id}</strong> has been updated.<br><br>
            Kindly review the changes and take the necessary action as required.<br><br>
            Regards,<br>
            VMS Team
        """

        frappe.custom_sendmail(
            recipients=[purchase_order.email2],
            subject=subject,
            message=message,
            now=True
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in po_updation_email_to_purchase")



@frappe.whitelist()
def send_mail_for_po(data):
    try:
        po_id = data.get("po_id")
        po_doc = frappe.get_doc("Purchase Order", po_id)
        vendor_code_id = po_doc.vendor_code

        # Find parent Company Vendor Code where child Vendor Code table has a row with matching vendor_code
        com_vendor_code_name = frappe.db.get_value(
            "Vendor Code", {"vendor_code": vendor_code_id}, "parent"
        )

        if not com_vendor_code_name:
            return {"status": "error", "message": "No matching Company Vendor Code found for vendor_code."}

        com_vendor_doc = frappe.get_doc("Company Vendor Code", com_vendor_code_name)

        vendor_ref_no = com_vendor_doc.vendor_ref_no
        vendor_master_doc = frappe.get_doc("Vendor Master", vendor_ref_no)

        vendor_email = vendor_master_doc.office_email_primary or vendor_master_doc.office_email_secondary
        vendor_name = vendor_master_doc.vendor_name
        if not vendor_email:
            return {"status": "error", "message": "No email found for vendor."}

        print_format = frappe.db.get_single_value("Print Format Settings", "purchase_order_print_format")

        pdf_data = frappe.get_print(doctype="Purchase Order", name=po_id, print_format=print_format, as_pdf=True)
        file_name = f"{po_doc.name}.pdf"

        # Send email with attachment
        frappe.custom_sendmail(
            recipients=[vendor_email],
            subject="New Purchase Order Created",
            message=f"Dear {vendor_name}, Please find the attached document for the Purchase Order <strong>{po_doc.name}</strong>",
            attachments=[{
                "fname": file_name,
                "fcontent": pdf_data
            }]
        )

        return {
            "status": "success",
            "vendor_name": vendor_name,
            "message": "Email sent successfully to vendor.",
            "email": vendor_email,
            "file_name": file_name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "PO Creation Email Error")
        return {
            "status": "error",
            "message": "An error occurred.",
            "error": str(e)
        }





@frappe.whitelist(allow_guest=True)
def revocked_po_details_mail(po_id):
    try:
        if not po_id:
            return {
                "status": "error",
                "message": "Missing Purchase Order ID"
            }

        po = frappe.get_doc("Purchase Order", po_id)

        # Vendor's email and purchase team email
        vendor_email = po.get("email")
        purchase_team_email = po.get("email2")  # Ensure this field exists in your PO DocType

        if not vendor_email:
            return {
                "status": "error",
                "message": "No vendor email found in Purchase Order"
            }

        subject = f"Purchase Order {po.name} - Access Revoked"
        body = f"""
        Dear Vendor,<br><br>
        Please note that access to your Purchase Order <strong>{po.name}</strong> has been revoked.<br><br>
        If you have any questions or require clarification, please feel free to contact the Purchasing Team.<br><br>
        Best regards,<br>
        VMS Team
        """


        # Send email to vendor and CC purchase team (if provided)
        recipients = [vendor_email]
        cc_list = [purchase_team_email] if purchase_team_email else []

        frappe.custom_sendmail(
            recipients=recipients,
            cc=cc_list,
            subject=subject,
            message=body,
            now=True 
        )

        

        return {
            "status": "success",
            "message": f"Revocation email sent to vendor at {vendor_email}"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "po_details_mail")
        return {
            "status": "error",
            "message": str(e)
        }







# ============= LOGGING HELPER FUNCTIONS =============

def create_initial_sap_log(data, transaction_type, sap_document_number):
    """
    Create initial SAP log entry when API is hit
    This MUST succeed to ensure we always have a log
    """
    try:
        log_doc = frappe.new_doc("Purchase SAP Logs")
        log_doc.transaction_type = transaction_type
        log_doc.sap_document_number = sap_document_number
        log_doc.transaction_date = frappe.utils.now()
        log_doc.status = "In Progress"
        log_doc.sap_to_erp_data = json.dumps(data, indent=2, default=str)
        
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
            title=f"Failed to create initial SAP log for {transaction_type}",
            message=f"Error: {str(e)}\n\nData: {frappe.as_json(data)}"
        )
        # Re-raise to prevent silent failures
        raise


def update_sap_log_success(log_id, response, frappe_doc_type, frappe_doc_name, data, po_doc=None):
    """
    Update SAP log with success details
    """
    try:
        log_doc = frappe.get_doc("Purchase SAP Logs", log_id)
        log_doc.status = "Success"
        log_doc.processed_date = frappe.utils.now()
        log_doc.erp_response = json.dumps(response, indent=2, default=str)
        
        # Link to created/updated document
        if frappe_doc_type == "Purchase Order":
            log_doc.purchase_order_link = frappe_doc_name
        elif frappe_doc_type == "Purchase Requisition":
            log_doc.purchase_requisition_link = frappe_doc_name
        
        # Update total transaction with complete details
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
                "transaction_type": log_doc.transaction_type,
                "sap_document_number": log_doc.sap_document_number,
                "frappe_doc_type": frappe_doc_type,
                "frappe_doc_name": frappe_doc_name,
                "created_new": response.get("message", "").lower().find("created") != -1,
                "processing_time_seconds": (datetime.strptime(log_doc.processed_date, "%Y-%m-%d %H:%M:%S.%f") - 
                                          datetime.strptime(log_doc.transaction_date, "%Y-%m-%d %H:%M:%S.%f")).total_seconds() if log_doc.processed_date and log_doc.transaction_date else 0
            }
        }
        
        # Add PO-specific details if available
        if po_doc:
            total_transaction_data["transaction_summary"].update({
                "po_type": po_doc.get("purchase_order_type"),
                "supplier": po_doc.get("supplier_name"),
                "sap_status": po_doc.get("sap_status")
            })
        
        log_doc.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)
        
        log_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        # Log error but don't fail the main transaction
        frappe.log_error(
            title="Failed to update SAP log with success",
            message=f"Log ID: {log_id}\nError: {str(e)}\n{frappe.get_traceback()}"
        )


def update_sap_log_failure(log_id, error_message, traceback):
    """
    Update SAP log with failure details
    """
    try:
        log_doc = frappe.get_doc("Purchase SAP Logs", log_id)
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
            title="Critical: Failed to update SAP log with failure",
            message=f"Log ID: {log_id}\nOriginal Error: {error_message}\nLogging Error: {str(e)}"
        )


def create_error_only_log(data, transaction_type, error_message, traceback):
    """
    Create a minimal error log when initial log creation failed
    Last resort to ensure we capture the error
    """
    try:
        log_doc = frappe.new_doc("Purchase SAP Logs")
        log_doc.transaction_type = transaction_type
        log_doc.transaction_date = frappe.utils.now()
        log_doc.processed_date = frappe.utils.now()
        log_doc.status = "Failed"
        log_doc.error_message = f"Initial log creation failed. Error: {error_message}"
        log_doc.error_traceback = traceback
        log_doc.sap_to_erp_data = json.dumps(data, indent=2, default=str) if data else "{}"
        
        log_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        # Absolute last resort
        frappe.log_error(
            title="CRITICAL: All SAP logging failed",
            message=f"Transaction Type: {transaction_type}\nOriginal Error: {error_message}\nLogging Error: {str(e)}\nData: {frappe.as_json(data) if data else 'None'}"
        )