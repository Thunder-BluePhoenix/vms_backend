# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PRSAPLogs(Document):
	def after_insert(self):
		try:
			pr_doc = frappe.get_doc(
				"Purchase Requisition Webform",
				{"purchase_requisition_form_link": self.purchase_requisition_link}
			)

			sap_response = frappe.parse_json(self.sap_response) if self.sap_response else {}
			total_transaction = frappe.parse_json(self.total_transaction) if self.total_transaction else {}

			sap_data = sap_response.get("d", {})
			ztype = sap_data.get("Ztype", "")
			ztext = sap_data.get("Ztext", "")
			banfn = sap_data.get("Banfn", "")

			transaction_summary = total_transaction.get("transaction_summary", {})

			# Build common fields to update
			if self.status != "Success":
				pr_doc.db_set({
					"form_is_submitted": 0,
					"purchase_team_approved": 0,
					# "form_status": "SAP Error",
					"sap_status": "Failed",
					"zmsg": ztext or transaction_summary.get("error_details", "Unknown Error"),
					"sap_summary": f"""Status: Failed
Error Type: {ztype}
Error Message: {ztext}
PR Code: {banfn}
Timestamp: {transaction_summary.get("timestamp")}
Failure Stage: {transaction_summary.get("failure_stage")}"""
				}, update_modified=True)

			else:  # Success case
				pr_doc.db_set({
					"form_status": "PR Created",
					"sap_status": "Success",
					"zmsg": f"PR Created Successfully - {banfn}" if banfn else "PR Created Successfully",
					"sap_summary": f"""Status: Success
PR Number: {banfn}
SAP Client: {transaction_summary.get("sap_client_code")}
Timestamp: {transaction_summary.get("timestamp")}
PR Type: {transaction_summary.get("pr_type")}"""
				}, update_modified=True)

			frappe.db.commit()

		except Exception:
			frappe.log_error(
				title=f"Error updating PR {self.purchase_requisition_link}",
				message=frappe.get_traceback()
			)
