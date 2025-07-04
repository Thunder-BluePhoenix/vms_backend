import frappe
from frappe import _



@frappe.whitelist(allow_guest=True)
def get_asa_details(asa):
    try:
        # Get Vendor Onboarding document
        # vn_onb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get the linked QMS Assessment Form document
        asa_doc = frappe.get_doc("Annual Supplier Assessment Questionnaire",asa)

        # Get meta for field labels
        meta = frappe.get_meta("Annual Supplier Assessment Questionnaire")
        asa_data = []

        for field in meta.fields:
            fieldname = field.fieldname
            fieldlabel = field.label
            if fieldname:
                value = asa_doc.get(fieldname)
                asa_data.append({
                    "fieldname": fieldname,
                    "fieldlabel": fieldlabel,
                    "value": value
                })

        return {
            "asa_details": asa_data,
            "asa_doc_name": asa_doc.name
        }

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_asa_details Error")
        frappe.throw(_("An unexpected error occurred while fetching ASA details."))



@frappe.whitelist(allow_guest=True)
def get_asa_details_without_label(asa):
    try:
        # Get Vendor Onboarding document
        # vn_onb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get the linked QMS Assessment Form document
        asa_doc = frappe.get_doc("Annual Supplier Assessment Questionnaire",asa)

        # Get meta for field labels
        # meta = frappe.get_meta("Annual Supplier Assessment Questionnaire")
        # asa_data = []

        # for field in meta.fields:
        #     fieldname = field.fieldname
        #     fieldlabel = field.label
        #     if fieldname:
        #         value = asa_doc.get(fieldname)
        #         asa_data.append({
        #             "fieldname": fieldname,
        #             "fieldlabel": fieldlabel,
        #             "value": value
        #         })

        return {
            "asa_details": asa_doc.as_dict(),
            "asa_doc_name": asa_doc.name
        }

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_asa_details Error")
        frappe.throw(_("An unexpected error occurred while fetching ASA details."))


@frappe.whitelist(allow_guest=True)
def get_asa_list():
    # user = frappe.session.user
    # # emp = frappe.get_doc("Employee",{"user_id": user})
    # team = frappe.db.get_value("Employee", {"user_id": user}, "team")
    # user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
    # conditions = []
    # values = {}

    # conditions.append("vo.registered_by IN %(user_ids)s")
    # values["user_ids"] = user_ids


    all_asa = frappe.get_all("Annual Supplier Assessment Questionnaire", fields ="*", order_by = "modified desc")
    return all_asa

