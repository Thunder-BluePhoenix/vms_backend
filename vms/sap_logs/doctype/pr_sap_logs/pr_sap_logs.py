# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PRSAPLogs(Document):
	def after_insert(self):
		try:
			pr_doc = frappe.get_doc("Purchase Requisition Webform", self.purchase_requisition_link)

			sap_response = frappe.parse_json(self.sap_response) if self.sap_response else {}
			total_transaction = frappe.parse_json(self.total_transaction) if self.total_transaction else {}
			
			sap_data = sap_response.get("d", {})
			ztype = sap_data.get("Ztype", "")
			ztext = sap_data.get("Ztext", "")
			banfn = sap_data.get("Banfn", "")
			
			transaction_summary = total_transaction.get("transaction_summary", {})
			
			if self.status != "Success":
				pr_doc.form_is_submitted = 0
				pr_doc.purchase_team_approved = 0
				pr_doc.form_status = "SAP Error"
				pr_doc.sap_status = self.status
				pr_doc.zmsg = ztext or transaction_summary.get("error_details", "Unknown Error")
				pr_doc.sap_summary = f"""Status: {self.status}
Error Type: {ztype}
Error Message: {ztext}
PR Code: {banfn}
Timestamp: {transaction_summary.get("timestamp")}
Failure Stage: {transaction_summary.get("failure_stage")}"""

			if self.status == "Success":
				pr_doc.form_status = "PR Created"
				pr_doc.sap_status = self.status
				pr_doc.zmsg = f"PR Created Successfully - {banfn}" if banfn else "PR Created Successfully"
				pr_doc.sap_summary = f"""Status: {self.status}
PR Number: {banfn}
SAP Client: {transaction_summary.get("sap_client_code")}
Timestamp: {transaction_summary.get("timestamp")}
PR Type: {transaction_summary.get("pr_type")}"""
			
			pr_doc.save(ignore_permissions=True)
			frappe.db.commit()
			
		except Exception as e:
			frappe.log_error(
				title=f"Error updating PR {self.purchase_requisition_link}",
				message=frappe.get_traceback()
			)