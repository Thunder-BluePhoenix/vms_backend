# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PurchaseRequisition(Document):
    def on_update(self):
        """Create or update Purchase Requisition Form document based on current Purchase Requisition."""

        if self.purchase_requisition_form_link:
            pur_req_form = frappe.get_doc("Purchase Requisition Form", self.purchase_requisition_form_link)
        else:
            pur_req_form = frappe.new_doc("Purchase Requisition Form")

        field_map = {
            "purchase_requisition_type": self.purchase_requisition_type,
            "plant": frappe.db.get_value("Plant Master", {"plant_code": self.pr_plant}, "name"),
            "company": frappe.db.get_value("Company Master", {"sap_client_code": self.company}, "name"),
            "purchase_requisition_date": self.purchase_requisition_date,
            "form_status": "PR Created from SAP"
        }

        for target_field, value in field_map.items():
            pur_req_form.set(target_field, value)

        pur_req_form.set("purchase_requisition_form_table", [])

        for item in self.get("pr_items"):
            new_row = pur_req_form.append("purchase_requisition_form_table", {})

            if self.purchase_requisition_type == "NB":
                item_category_head = item.item_category_head
            else:
                item_category_head = frappe.db.get_value("Item Category Master", {"sap_key": item.item_category_head}, "name")

            # Child Field Mapping
            child_field_map = {
                "head_unique_id": item.head_unique_id,
                "purchase_requisition_item_head": item.purchase_requisition_item_head,
                "item_number_of_purchase_requisition_head": item.item_number_of_purchase_requisition_head,
                "purchase_requisition_date_head": item.purchase_requisition_date_head,
                "purchase_requisition_type": self.purchase_requisition_type,
                "delivery_date_head": item.delivery_date_head,
                "store_location_head": frappe.db.get_value("Storage Location Master", {"storage_location": item.store_location_head}, "name"),
                "item_category_head": item_category_head,
                "material_group_head": frappe.db.get_value("Material Group Master", {"material_group_name": item.material_group_head}, "name"),
                "uom_head": item.uom_head,
                "cost_center_head": frappe.db.get_value("Cost Center", {"cost_center_code": item.cost_center_head}, "name"),
                "main_asset_no_head": item.main_asset_no_head,
                "asset_subnumber_head": item.asset_subnumber_head,
                "profit_ctr_head": frappe.db.get_value("Profit Center", {"profit_center_code": item.profit_ctr_head}, "name"),
                "short_text_head": item.short_text_head,
                "line_item_number_head": item.line_item_number_head,
                "company_code_area_head": frappe.db.get_value("Company Master", {"sap_client_code": self.company}, "name"),
                "c_delivery_date_head": item.c_delivery_date_head,
                "quantity_head": item.quantity_head,
                "price_of_purchase_requisition_head": item.price_of_purchase_requisition_head,
                "gl_account_number_head": frappe.db.get_value("GL Account", {"gl_account_code": item.gl_account_number_head}, "name"),
                "material_code_head": frappe.db.get_value("Material Code", {"material_code": item.material_code_head}, "name"),
                "account_assignment_category_head": item.account_assignment_category_head,
                "purchase_group_head": frappe.db.get_value("Purchase Group Master", {"purchase_group_code": item.purchase_group_head}, "name"),
                "product_name_head": item.product_name_head,
                "product_price_head": item.product_price_head,
                "final_price_by_purchase_team_head": item.final_price_by_purchase_team_head,
                "lead_time_head": item.lead_time_head,
                "plant_head": frappe.db.get_value("Plant Master", {"plant_code": self.pr_plant}, "name"),
                "requisitioner_name_head": item.requisitioner_name_head,
                "tracking_id_head": item.tracking_id_head,
                "desired_vendor_head": item.desired_vendor_head,
                "valuation_area_head": frappe.db.get_value("Valuation Class", {"valuation_class_code": item.valuation_area_head}, "name"),
                "fixed_value_head": item.fixed_value_head,
                "spit_head": item.spit_head,
                "purchase_organisation_head": frappe.db.get_value("Purchase Organization Master", {"purchase_organization_code": item.purchase_organisation_head}, "name"),
                "agreement_head": item.agreement_head,
                "item_of_head": item.item_of_head,
                "mpn_number_head": item.mpn_number_head,
                
                # Subhead Fields
				"sub_head_unique_id": item.sub_head_unique_id,
                "purchase_requisition_item_subhead": item.purchase_requisition_item_subhead,
                "item_number_of_purchase_requisition_subhead": item.item_number_of_purchase_requisition_subhead,
                "purchase_requisition_date_subhead": item.purchase_requisition_date_subhead,
                "delivery_date_subhead": item.delivery_date_subhead,
                "store_location_subhead": frappe.db.get_value("Storage Location Master", {"storage_location": item.store_location_subhead}, "name"),
                "item_category_subhead": frappe.db.get_value("Item Category Master", {"sap_key": item.item_category_subhead}, "name"),
                "material_group_subhead": frappe.db.get_value("Material Group Master", {"material_group_name": item.material_group_subhead}, "name"),
                "uom_subhead": item.uom_subhead,
                "cost_center_subhead": frappe.db.get_value("Cost Center", {"cost_center_code": item.cost_center_subhead}, "name"),
                "main_asset_no_subhead": item.main_asset_no_subhead,
                "asset_subnumber_subhead": item.asset_subnumber_subhead,
                "profit_ctr_subhead": frappe.db.get_value("Profit Center", {"profit_center_code": item.profit_ctr_subhead}, "name"),
                "short_text_subhead": item.short_text_subhead,
                "quantity_subhead": item.quantity_subhead,
                "price_of_purchase_requisition_subhead": item.price_of_purchase_requisition_subhead,
                "gl_account_number_subhead": frappe.db.get_value("GL Account", {"gl_account_code": item.gl_account_number_subhead}, "name"),
                "material_code_subhead": frappe.db.get_value("Material Code", {"material_code": item.material_code_subhead}, "name"),
                "account_assignment_category_subhead": item.account_assignment_category_subhead,
                "purchase_group_subhead": frappe.db.get_value("Purchase Group Master", {"purchase_group_code": item.purchase_group_subhead}, "name"),
                "line_item_number_subhead": item.line_item_number_subhead,
                "service_number_subhead": item.service_number_subhead,
                "gross_price_subhead": item.gross_price_subhead,
                "currency_subhead": item.currency_subhead,
                "service_type_subhead": item.service_type_subhead,
                "net_value_subhead": item.net_value_subhead,
                
				# Utility
                "is_created": 1
            }

            for fieldname, value in child_field_map.items():
                new_row.set(fieldname, value)

        pur_req_form.save(ignore_permissions=True)

        if not self.purchase_requisition_form_link:
            self.db_set("purchase_requisition_form_link", pur_req_form.name)
