# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LegalDocuments(Document):
	def on_update(self):
		"""Sync legal document data to Vendor Onboarding Company Details"""
		try:
			# Get the vendor onboarding company details document
			vonb_comp_doc = self._get_vendor_onboarding_company()
			
			if not vonb_comp_doc:
				return
			
			# Update company PAN number
			vonb_comp_doc.company_pan_number = self.company_pan_number
			
			# Process and update GST records
			self._update_gst_records(vonb_comp_doc)
			
			# Save the document (handles transaction automatically)
			vonb_comp_doc.save(ignore_permissions=True)
			
			frappe.logger().info(
				f"Successfully synced Legal Document {self.name} to "
				f"Vendor Onboarding Company Details {vonb_comp_doc.name}"
			)
			
		except Exception as e:
			frappe.log_error(
				title="LegalDocuments Sync Error",
				message=f"Error syncing Legal Document {self.name}: {str(e)}\n"
						f"Ref No: {self.ref_no}, Vendor Onboarding: {self.vendor_onboarding}"
			)
			raise
	
	def _get_vendor_onboarding_company(self):
		"""Get the related Vendor Onboarding Company Details document"""
		filters = {
			"ref_no": self.ref_no,
			"vendor_onboarding": self.vendor_onboarding
		}
		
		vonb_comp_name = frappe.db.get_value(
			"Vendor Onboarding Company Details",
			filters,
			"name"
		)
		
		if not vonb_comp_name:
			frappe.log_error(
				title="Vendor Onboarding Company Not Found",
				message=f"No Vendor Onboarding Company Details found for:\n"
						f"Ref No: {self.ref_no}\n"
						f"Vendor Onboarding: {self.vendor_onboarding}\n"
						f"Legal Document: {self.name}"
			)
			return None
		
		return frappe.get_doc("Vendor Onboarding Company Details", vonb_comp_name)
	
	def _update_gst_records(self, vonb_comp_doc):
		"""Update GST records in the vendor onboarding company document"""
		# Clear existing GST child table records
		vonb_comp_doc.comp_gst_table = []
		
		if self.gst_table and len(self.gst_table) > 0:
			# Set primary GST number from first record
			vonb_comp_doc.gst = self.gst_table[0].gst_number
			
			# Add all GST records to child table
			for gst_entry in self.gst_table:
				vonb_comp_doc.append("comp_gst_table", {
					"gst_state": gst_entry.gst_state,
					"gst_number": gst_entry.gst_number,
					"gst_registration_date": gst_entry.gst_registration_date,
					"gst_ven_type": gst_entry.gst_ven_type,
					"gst_document": gst_entry.gst_document,
					"pincode": gst_entry.pincode
				})
		else:
			# Clear GST field if no records
			vonb_comp_doc.gst = None
			frappe.logger().warning(
				f"GST table is empty for Legal Document: {self.name}"
			)

# class LegalDocuments(Document):
# 	def on_update(self):
# 		try:
# 			# Get the vendor onboarding company details name
# 			vonb_comp_name = frappe.db.get_value(
# 				"Vendor Onboarding Company Details",
# 				{"ref_no": self.ref_no, "vendor_onboarding": self.vendor_onboarding},
# 				"name"
# 			)

# 			if not vonb_comp_name:
# 				frappe.log_error(
# 					f"Vendor Onboarding Company Details not found for ref_no: {self.ref_no}, vendor_onboarding: {self.vendor_onboarding}", 
# 					"LegalDocuments.on_update"
# 				)
# 				return

# 			# Update company PAN number using set_value
# 			frappe.db.set_value(
# 				"Vendor Onboarding Company Details", 
# 				vonb_comp_name, 
# 				"company_pan_number", 
# 				self.company_pan_number
# 			)

# 			# Clear existing GST records
# 			frappe.db.delete("Vendor Company GST Table", {"parent": vonb_comp_name})

# 			# Process GST table
# 			if self.gst_table and len(self.gst_table) > 0:
# 				# Set primary GST number (first record)
# 				frappe.db.set_value(
# 					"Vendor Onboarding Company Details",
# 					vonb_comp_name,
# 					"gst",
# 					self.gst_table[0].gst_number
# 				)

# 				# Insert new GST records
# 				for idx, gst_d in enumerate(self.gst_table):
# 					gst_doc = frappe.get_doc({
# 						"doctype": "Vendor Company GST Table",  # Replace with actual child table doctype
# 						"parent": vonb_comp_name,
# 						"parenttype": "Vendor Onboarding Company Details",
# 						"parentfield": "comp_gst_table",
# 						"idx": idx + 1,
# 						"gst_state": gst_d.gst_state,
# 						"gst_number": gst_d.gst_number,
# 						"gst_registration_date": gst_d.gst_registration_date,
# 						"gst_ven_type": gst_d.gst_ven_type,
# 						"gst_document": gst_d.gst_document,
# 						"pincode": gst_d.pincode
# 					})
# 					gst_doc.insert(ignore_permissions=True)

# 			else:
# 				# Clear GST field if no GST records
# 				frappe.db.set_value(
# 					"Vendor Onboarding Company Details",
# 					vonb_comp_name,
# 					"gst",
# 					None
# 				)
# 				frappe.log_error(
# 					f"GST table is empty for Legal Document: {self.name}", 
# 					"LegalDocuments.on_update"
# 				)

# 			# Commit the transaction
# 			frappe.db.commit()
			
# 			frappe.logger().info(f"Successfully updated Vendor Onboarding Company Details: {vonb_comp_name}")

# 		except Exception as e:
# 			frappe.log_error(
# 				f"Error in LegalDocuments.on_update for {self.name}: {str(e)}", 
# 				"LegalDocuments.on_update"
# 			)
# 			frappe.db.rollback()
# 			raise