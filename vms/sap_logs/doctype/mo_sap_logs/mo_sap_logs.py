# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MOSAPLogs(Document):
	def after_insert(self):
		try:
			from vms.material.doctype.material_aging_track.material_aging_track import update_aging_tracker_on_sap_sync
			update_aging_tracker_on_sap_sync(self.name)
			return {"status": "success", "message": "Aging tracker update completed"}
		except Exception as e:
			frappe.log_error(f"Aging tracker update error for {self.name}: {str(e)}")
			return {"status": "error", "message": str(e)}
