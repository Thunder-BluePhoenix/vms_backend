import frappe

@frappe.whitelist()
def get_doc_fields_list(doctype):
    meta_data = frappe.get_meta(doctype)
    fields = meta_data.get("fields")

    options = [""]

    if fields:
        for field in fields:
            field_name = field.get("fieldname")
            field_type = field.get("fieldtype")

            if field_type not in ["Section Break", "Column Break", "Page Break"]:
                options.append(field_name)

    return options