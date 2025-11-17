# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import json
from frappe.model.meta import get_meta
from vms.utils.custom_send_mail import custom_sendmail


class VendorMaster(Document):

    def on_update(self):
        sent_asa_form_link(self)
        
# 		# exist_onb = frappe.db.exist("Vendor Onboarding", {"ref_no": self.name})  
        
# 		if self.created_from_registration ==1 and frappe.db.exists("Vendor Onboarding", {"ref_no": self.name}):
# 			# print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ data exist")
# 			pass
# 		else:
# 			data = self.as_dict()
# 	# print("*********************************************", data)

# 			vendor_registration(data)
            

def sent_asa_form_link(doc, method=None):
    try:
        recipient = doc.office_email_primary or doc.office_email_secondary
        if not recipient:
            return

        frontend_http = frappe.get_site_config().get('frontend_http', 'https://saksham-v.merillife.com/')
        link = f"{frontend_http}/login"

        subject = "Fill ASA Form"
        message = f"""
            Dear {doc.vendor_name},<br><br>

            <p>Meril is strengthening its Responsible Sourcing and Sustainability Framework across the entire supply chain. 
            As part of this initiative, we are collecting ESG (Environment, Social & Governance) information from all our partners 
            to understand operational practices related to the environment, workforce management, safety, and governance. 
            This also aims to create greater awareness regarding sustainability and ESG practices within our supply chain.</p>

            <p>The information you provide will help us build a clear overview of sustainability practices across our supply chain, 
            identify potential risks, and understand where support or improvements may be required. This will also enable Meril to 
            meet evolving global expectations from healthcare customers, regulators, and international markets that increasingly 
            emphasize responsible and transparent supply chains.</p>

            <p>We request you to kindly submit your ESG information through the portal link given below:</p>

            <p>To fill the form, please log in to the portal:</p>

            <strong>Portal Link:</strong> 
            <a href="{link}" target="_blank">Click here to access the portal</a><br>

            <strong>The login credentials were already shared with you in a previous email.</strong><br><br>

            For any assistance or clarification, our team will be happy to support you.<br><br>

            Thank you.<br><br>

            Regards,<br>
            Team VMS
        """

        # VIA DATA IMPORT + MULTIPLE COMPANY DATA
    
        if doc.asa_required and doc.via_data_import and not doc.asa_form_link_sent:
            for row in doc.multiple_company_data or []:
                if row.company_vendor_code:
                    frappe.custom_sendmail(
                        recipients=recipient,
                        subject=subject,
                        message=message
                    )

                    frappe.db.set_value("Vendor Master", doc.name, "asa_form_link_sent", 1)

        # CREATED FROM REGISTRATION + ONBOARDING RECORDS

        if doc.asa_required and doc.created_from_registration and not doc.asa_form_link_sent:
            for row in doc.vendor_onb_records or []:
                if row.vendor_onboarding_no and row.onboarding_form_status == "Approved":
                    frappe.custom_sendmail(
                        recipients=recipient,
                        subject=subject,
                        message=message
                    )
                    
                    frappe.db.set_value("Vendor Master", doc.name, "asa_form_link_sent", 1)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error in send_asa_form_link")



@frappe.whitelist()
def danger_action(vendor_name):
    """
    Danger API: 
    1. Unlink Vendor Master from all linked doctypes
    2. Clear link fields in Vendor Master
    3. Delete docs that become empty
    4. Delete the Vendor Master itself
    """
    if not vendor_name:
        frappe.throw("Vendor name required")

    vendor_doc = frappe.get_doc("Vendor Master", vendor_name)

    # Step 1: Find all doctypes with Link field to Vendor Master
    linked_fields = frappe.get_all(
        "DocField",
        filters={"fieldtype": "Link", "options": "Vendor Master"},
        fields=["parent", "fieldname"]
    )

    # Step 2: For each linked doctype, clear the field
    for lf in linked_fields:
        linked_docs = frappe.get_all(
            lf.parent,
            filters={lf.fieldname: vendor_name},
            pluck="name"
        )

        for docname in linked_docs:
            # doc = frappe.get_doc(lf.parent, docname)
            # setattr(doc, lf.fieldname, None)
            # doc.save(ignore_permissions=True)
            frappe.db.set_value(lf.parent, docname, lf.fieldname, None, update_modified=True)


            # If doc becomes empty (all fields except name/doctype are blank) → delete
            # if is_doc_empty(doc):
            #     doc.delete(ignore_permissions=True)

    # Step 3: Clear link fields inside Vendor Master itself
        meta = get_meta("Vendor Master")
        for df in meta.fields:
            if df.fieldtype == "Link":
                setattr(vendor_doc, df.fieldname, None)
        vendor_doc.save(ignore_permissions=True)


        for docname in linked_docs:
            doc = frappe.get_doc(lf.parent, docname)
            doc.delete(ignore_permissions=True, force=True)

    # Step 4: Finally delete Vendor Master
    vendor_doc.delete(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "message": f"Vendor {vendor_name} and linked data deleted."}


def is_doc_empty(doc):
    """Helper: check if doc has no non-empty fields except metadata"""
    ignore_fields = {"name", "doctype", "owner", "creation", "modified", "modified_by", "docstatus"}
    for field in doc.meta.fields:
        if field.fieldname not in ignore_fields:
            value = doc.get(field.fieldname)
            if value not in (None, "", 0):
                return False
    return True






@frappe.whitelist()
def danger_action_bulk(vendor_name):
    """
    Danger API: Unlink + Delete vendor(s).
    vendor_name can be single or comma-separated list.
    """
    if not vendor_name:
        frappe.throw("Vendor name required")

    vendors = [v.strip() for v in vendor_name.split(",") if v.strip()]

    for vname in vendors:
        if not frappe.db.exists("Vendor Master", vname):
            continue
        vendor_doc = frappe.get_doc("Vendor Master", vname)

        # ... (your unlinking logic here)
        danger_action(vendor_doc.name)

        # finally delete
        # vendor_doc.delete(ignore_permissions=True, force=True)

    frappe.db.commit()
    return {"status": "success", "message": f"Deleted vendors: {', '.join(vendors)}"}




# @frappe.whitelist(allow_guest=True)
# def vendor_registration(data):
#     try:
#         if isinstance(data, str):
#             data = json.loads(data)

#         vendor_master = frappe.get_doc("Vendor Master", data.name)

        
            
#         # Create Vendor Onboarding
#         vendor_onboarding = frappe.new_doc("Vendor Onboarding")
#         vendor_onboarding.ref_no = vendor_master.name
#         vendor_onboarding.company_name = vendor_master.multiple_company_data[0].company_name
#         vendor_onboarding.purchase_t_approval = vendor_master.purchase_team_approval
#         vendor_onboarding.accounts_t_approval = vendor_master.accounts_team_approval
#         vendor_onboarding.purchase_h_approval = vendor_master.purchase_head_approval

#         for field in [
#             "qms_required","company_name", "purchase_organization", "account_group",
#             "purchase_group", "terms_of_payment", "order_currency", "incoterms"
#         ]:
#             if field in data:
#                 vendor_onboarding.set(field, data[field])

#         vendor_onboarding.payee_in_document = 1
#         vendor_onboarding.gr_based_inv_ver = 1
#         vendor_onboarding.service_based_inv_ver = 1
#         vendor_onboarding.check_double_invoice = 1

#         # if "multiple_company" in data:
#         #     for row in data["multiple_company"]:
#         #         vendor_onboarding.append("multiple_company", row)

#         if "vendor_types" in data:
#             for row in data["vendor_types"]:
#                 is_duplicate = False
#                 for existing in vendor_master.vendor_types:
#                     if (existing.vendor_type or "").lower().strip() == (row.get("vendor_type") or "").lower().strip():
#                         is_duplicate = True
#                         break

#                 if not is_duplicate:
#                     vendor_master.append("vendor_types", row)

#         vendor_onboarding.save()
#         frappe.db.commit()

#         # Create and link additional onboarding documents
#         def create_related_doc(doctype):
#             doc = frappe.new_doc(doctype)
#             doc.vendor_onboarding = vendor_onboarding.name
#             doc.ref_no = vendor_master.name
#             doc.save()
#             frappe.db.commit()
#             return doc.name

#         payment_detail = create_related_doc("Vendor Onboarding Payment Details")
#         document_details = create_related_doc("Legal Documents")
#         certificate_details = create_related_doc("Vendor Onboarding Certificates")
#         manufacturing_details = create_related_doc("Vendor Onboarding Manufacturing Details")
#         company_details = create_related_doc("Vendor Onboarding Company Details")

#         if company_details:
#             vendor_onb_company = frappe.get_doc("Vendor Onboarding Company Details", company_details)

#             for field in ["vendor_title", "vendor_name", "company_name"]:
#                 if field in data:
#                     vendor_onb_company.set(field, data[field])

#             vendor_onb_company.save()

#         # Add vendor_company_details in child table
#         vendor_onboarding.append("vendor_company_details", {
#             "vendor_company_details": company_details 
#         })

#         # Update vendor onboarding with doc names
#         vendor_onboarding.payment_detail = payment_detail
#         vendor_onboarding.document_details = document_details
#         vendor_onboarding.certificate_details = certificate_details
#         vendor_onboarding.manufacturing_details = manufacturing_details
        
#         vendor_onboarding.save()
#         # send_registration_email_link(vendor_onboarding.name, vendor_master.name)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "vendor_master": vendor_master.name,
#             "vendor_onboarding": vendor_onboarding.name,
#             "payment_detail": payment_detail,
#             "document_details": document_details,
#             "certificate_details": certificate_details,
#             "manufacturing_details": manufacturing_details,
#             "company_details": company_details
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Vendor Registration Full Flow Error")
#         return {
#             "status": "error",
#             "message": "Vendor registration failed",
#             "error": str(e)
#         }




