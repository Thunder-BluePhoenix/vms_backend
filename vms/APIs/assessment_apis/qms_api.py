import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_qms_details(vendor_onboarding):
    try:
        # Get Vendor Onboarding document
        vn_onb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get the linked QMS Assessment Form document
        qms_doc = frappe.get_doc("Supplier QMS Assessment Form", {"unique_name":vn_onb.qms_form_link})

        # Get meta for field labels
        meta = frappe.get_meta("Supplier QMS Assessment Form")
        qms_data = []

        for field in meta.fields:
            fieldname = field.fieldname
            fieldlabel = field.label
            if fieldname:
                value = qms_doc.get(fieldname)
                qms_data.append({
                    "fieldname": fieldname,
                    "fieldlabel": fieldlabel,
                    "value": value
                })

        return {
            "qms_details": qms_data,
            "qms_doc_name": qms_doc.name
        }

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_qms_details Error")
        frappe.throw(_("An unexpected error occurred while fetching QMS details."))
