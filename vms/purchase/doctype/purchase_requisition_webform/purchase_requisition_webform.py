# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PurchaseRequisitionWebform(Document):
	def on_update(self):
		field_map = [
			"purchase_requisition_type",
			"plant",
			"company_code_area",
			"company",
			"requisitioner"
		]

		child_field_map = {
			"purchase_requisition_item": "purchase_requisition_item",
			"item_number_of_purchase_requisition": "item_number_of_purchase_requisition",
			"purchase_requisition_date": "purchase_requisition_date",
			"delivery_date": "delivery_date",
			"store_location": "store_location",
			"item_category": "item_category",
			"material_group": "material_group",
			"uom": "uom",
			"cost_center": "cost_center",
			"main_asset_no": "main_asset_no",
			"asset_subnumber": "asset_subnumber",
			"profit_ctr": "profit_ctr",
			"short_text": "short_text",
			"quantity": "quantity",
			"gl_account_number": "gl_account_number",
			"material_code": "material_code",
			"account_assignment_category": "account_assignment_category",
			"purchase_group": "purchase_group",
			"price_of_purchase_requisition": "price_in_purchase_requisition"
		}

		if not self.purchase_requisition_form_link:
			# Create new Purchase Requisition Form
			pur_req_form = frappe.new_doc("Purchase Requisition Form")

			for field in field_map:
				pur_req_form.set(field, self.get(field))

			for item in self.get("purchase_requisition_form_table"):
				new_row = pur_req_form.append("purchase_requisition_form_table", {})
				for src_field, target_field in child_field_map.items():
					new_row.set(target_field, item.get(src_field))

			pur_req_form.save()
			self.db_set("purchase_requisition_form_link", pur_req_form.name)

		else:
			# Update existing Purchase Requisition Form
			pur_req_form = frappe.get_doc("Purchase Requisition Form", self.purchase_requisition_form_link)

			for field in field_map:
				pur_req_form.set(field, self.get(field))

			# Clear existing child table to avoid mismatch
			pur_req_form.set("purchase_requisition_form_table", [])

			for item in self.get("purchase_requisition_form_table"):
				new_row = pur_req_form.append("purchase_requisition_form_table", {})
				for src_field, target_field in child_field_map.items():
					new_row.set(target_field, item.get(src_field))

			pur_req_form.save()