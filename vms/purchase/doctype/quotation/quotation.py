import frappe
import json
from frappe.model.document import Document

class Quotation(Document):
	def before_save(self):
		"""Store the old state of child table items before saving"""
		if not self.is_new():
			
			old_doc = frappe.get_doc("Quotation", self.name)
			
			
			self._old_items = {}
			for item in old_doc.get("rfq_item_list", []):  
				self._old_items[item.name] = item.as_dict()
	
	def on_update(self):
		if hasattr(self, '_old_items'):
			self.track_child_table_changes()
	
	def track_child_table_changes(self):
		current_items = {}
		for item in self.get("rfq_item_list", []):  
			current_items[item.name] = item.as_dict()
		
		
		for item_name, old_data in self._old_items.items():
			if item_name in current_items:
				new_data = current_items[item_name]
				
				
				if self.has_any_field_changed(old_data, new_data):
					self.log_complete_change(item_name, old_data, new_data)
		
		for item_name, new_data in current_items.items():
			if item_name not in self._old_items:
				self.log_complete_change(item_name, {}, new_data)
	
	def has_any_field_changed(self, old_data, new_data):
		ignore_fields = ['modified', 'modified_by', 'creation', 'owner', 'docstatus', 'idx']
		
		for key in new_data:
			if key not in ignore_fields:
				if old_data.get(key) != new_data.get(key):
					return True
		return False
	
	def log_complete_change(self, item_name, old_data, new_data):
		try:
			change_log = {
				"old": self.clean_data_for_json(old_data),
				"new": self.clean_data_for_json(new_data)
			}
			
			# Create new record in table_tbvu child table
			self.append("table_tbvu", {  
				"field_json": json.dumps(change_log, default=str, indent=2),  
				"date_and_time": frappe.utils.now_datetime(), 
			})
			
			
			# self.save(ignore_permissions=True)
			
		except Exception as e:
			frappe.log_error(f"Error logging change: {str(e)}", "Quotation Change Tracking")
	
	def clean_data_for_json(self, data):
	
		cleaned_data = {}
		
		# Fields to exclude from logging (system/internal fields)
		exclude_fields = [
			'doctype', 'name', 'owner', 'creation', 'modified', 'modified_by',
			'docstatus', 'parent', 'parentfield', 'parenttype', 'idx'
		]
		
		for key, value in data.items():
			if key not in exclude_fields:

				if hasattr(value, 'strftime'):
					cleaned_data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
				else:
					cleaned_data[key] = value
		
		return cleaned_data
