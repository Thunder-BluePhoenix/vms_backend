# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LegalDocuments(Document):
	def on_update(self):
		try:
			# Get the vendor onboarding company details name
			vonb_comp_name = frappe.db.get_value(
				"Vendor Onboarding Company Details",
				{"ref_no": self.ref_no, "vendor_onboarding": self.vendor_onboarding},
				"name"
			)

			if not vonb_comp_name:
				frappe.log_error(
					f"Vendor Onboarding Company Details not found for ref_no: {self.ref_no}, vendor_onboarding: {self.vendor_onboarding}", 
					"LegalDocuments.on_update"
				)
				return

			# Update company PAN number using set_value
			frappe.db.set_value(
				"Vendor Onboarding Company Details", 
				vonb_comp_name, 
				"company_pan_number", 
				self.company_pan_number
			)

			# Clear existing GST records
			frappe.db.delete("Vendor Company GST Table", {"parent": vonb_comp_name})

			# Process GST table
			if self.gst_table and len(self.gst_table) > 0:
				# Set primary GST number (first record)
				frappe.db.set_value(
					"Vendor Onboarding Company Details",
					vonb_comp_name,
					"gst",
					self.gst_table[0].gst_number
				)

				# Insert new GST records
				for idx, gst_d in enumerate(self.gst_table):
					gst_doc = frappe.get_doc({
						"doctype": "Vendor Company GST Table",  # Replace with actual child table doctype
						"parent": vonb_comp_name,
						"parenttype": "Vendor Onboarding Company Details",
						"parentfield": "comp_gst_table",
						"idx": idx + 1,
						"gst_state": gst_d.gst_state,
						"gst_number": gst_d.gst_number,
						"gst_registration_date": gst_d.gst_registration_date,
						"gst_ven_type": gst_d.gst_ven_type,
						"gst_document": gst_d.gst_document,
						"pincode": gst_d.pincode
					})
					gst_doc.insert(ignore_permissions=True)

			else:
				# Clear GST field if no GST records
				frappe.db.set_value(
					"Vendor Onboarding Company Details",
					vonb_comp_name,
					"gst",
					None
				)
				frappe.log_error(
					f"GST table is empty for Legal Document: {self.name}", 
					"LegalDocuments.on_update"
				)

			# Commit the transaction
			frappe.db.commit()
			
			frappe.logger().info(f"Successfully updated Vendor Onboarding Company Details: {vonb_comp_name}")

		except Exception as e:
			frappe.log_error(
				f"Error in LegalDocuments.on_update for {self.name}: {str(e)}", 
				"LegalDocuments.on_update"
			)
			frappe.db.rollback()
			raise