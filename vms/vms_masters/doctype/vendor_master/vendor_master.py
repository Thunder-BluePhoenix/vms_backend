# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import json


class VendorMaster(Document):
    pass
# 	def on_update(self):
          
		
# 		# exist_onb = frappe.db.exist("Vendor Onboarding", {"ref_no": self.name})  
		
# 		if self.created_from_registration ==1 and frappe.db.exists("Vendor Onboarding", {"ref_no": self.name}):
# 			# print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ data exist")
# 			pass
# 		else:
# 			data = self.as_dict()
# 	# print("*********************************************", data)

# 			vendor_registration(data)
            










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




