import frappe
import json

@frappe.whitelist(allow_guest=True)
def get_grn_field_mappings():
    doctype_name = frappe.db.get_value("SAP Mapper PR", {'doctype_name': 'GRN'}, "name")
    mappings = frappe.get_all('SAP Mapper PR Item', filters={'parent': doctype_name}, fields=['sap_field', 'erp_field'])
    return {mapping['sap_field']: mapping['erp_field'] for mapping in mappings}


@frappe.whitelist(allow_guest=True)
def get_grn():
    try:
        data = frappe.request.get_json()

        if not data or "items" not in data:
            return {"status": "error", "message": "No valid data received or 'items' key not found."}

        grn_no = data.get("Grn", "")
        field_mappings = get_grn_field_mappings()

        if not field_mappings:
            return {"status": "error", "message": "No field mappings found for 'SAP Mapper GRN."}

        grn_doc = (frappe.get_doc("GRN", {"grn_no_t": grn_no})
                  if frappe.db.exists("GRN", {"grn_no_t": grn_no})
                  else frappe.new_doc("GRN"))


        meta = frappe.get_meta("GRN")
        grn_doc.grn_no_t = grn_no
        grn_doc.set("grn_items_table", [])
        print("Field Mappings:", field_mappings)
        print("Meta Fields:", meta.fields)

        for item in data["items"]:
            grn_item_data = {}
            for sap_field, erp_field in field_mappings.items():
                value = item.get(sap_field, "")
                field = next((f for f in meta.fields if f.fieldname == erp_field), None)
                grn_item_data[erp_field] = parse_date(value) if field and field.fieldtype == 'Date' else value

            
            for field in meta.fields:
                if field.fieldname in grn_item_data:
                    grn_doc.set(field.fieldname, grn_item_data[field.fieldname])

            grn_doc.append("grn_items_table", grn_item_data)

        grn_doc.save()
        frappe.db.commit()

        if grn_doc.is_new():
            grn_doc.insert()

            # grn_id = grn_doc.name
            # po_creation_send_mail(po_id)

            return {"status": "success", "message": "GRN Created Successfully.", "GRN": grn_doc.name}
        else:
            grn_doc.save()

            grn_id = grn_doc.name
            # po_update_send_mail(po_id)

            return {"status": "success", "message": "GRN Updated Successfully.", "GRN": grn_doc.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_po Error")
        return {"status": "error", "message": str(e)}



def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None
