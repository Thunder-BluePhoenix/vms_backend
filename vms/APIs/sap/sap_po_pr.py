import frappe
import json
# from frappe.utils import parse_date

@frappe.whitelist(allow_guest=True)
def get_field_mappings():
    doctype_name = frappe.db.get_value("SAP Mapper PR", filters={'doctype_name': 'Purchase Requisition'}, fieldname='name')
    mappings = frappe.get_all('SAP Mapper PR Item', filters={'parent': doctype_name}, fields=['sap_field', 'erp_field'])
    return {mapping['sap_field']: mapping['erp_field'] for mapping in mappings}


@frappe.whitelist(allow_guest=True)
def get_pr():
    try:
        data = frappe.request.get_json()
        if not data or "items" not in data:
            return {"status": "error", "message": "No valid data received or 'items' key not found."}

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

        if pr_doc.is_new():
            pr_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return {"status": "success", "message": "Purchase Requisition Created Successfully."}
        else:
            pr_doc.save(ignore_permissions=True)
            frappe.db.commit()
            return {"status": "success", "message": "Purchase Requisition Updated Successfully."}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "create_purchase_requisition Error")
        return {"status": "error", "message": str(e)}



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


@frappe.whitelist(allow_guest=True)
def get_po():
    try:
        data = frappe.request.get_json()

        if not data or "items" not in data:
            return {"status": "error", "message": "No valid data received or 'items' key not found."}

        pr_no = data.get("po_no", "")
        field_mappings = get_po_field_mappings()

        if not field_mappings:
            return {"status": "error", "message": "No field mappings found for 'SAP Mapper PO'"}

        po_doc = (frappe.get_doc("Purchase Order", {"po_number": pr_no})
                  if frappe.db.exists("Purchase Order", {"po_number": pr_no})
                  else frappe.new_doc("Purchase Order"))

        meta = frappe.get_meta("Purchase Order")
        po_doc.po_number = pr_no
        po_doc.set("po_items", [])

        for item in data["items"]:
            po_item_data = {}
            for sap_field, erp_field in field_mappings.items():
                value = item.get(sap_field, "")
                field = next((f for f in meta.fields if f.fieldname == erp_field), None)
                po_item_data[erp_field] = parse_date(value) if field and field.fieldtype == 'Date' else value

            # Map top-level fields
            for field in meta.fields:
                if field.fieldname in po_item_data:
                    po_doc.set(field.fieldname, po_item_data[field.fieldname])

            po_doc.append("po_items", po_item_data)

        if po_doc.is_new():
            po_doc.status = "Pending"
            po_doc.insert()

            po_id = po_doc.name
            po_creation_send_mail(po_id)

            return {"status": "success", "message": "Purchase Order Created Successfully.", "po": po_doc.name}
        else:
            po_doc.save()

            po_id = po_doc.name
            po_update_send_mail(po_id)

            return {"status": "success", "message": "Purchase Order Updated Successfully.", "po": po_doc.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_po Error")
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
        frappe.sendmail(
            recipients=[vendor_email],
            subject="New Purchase Order Created",
            message=f"Dear {vendor_name},<br><br>A new Purchase Order <strong>{po_doc.name}</strong> has been created. Please find the attached document.",
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
        frappe.sendmail(
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
        frappe.sendmail(
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
