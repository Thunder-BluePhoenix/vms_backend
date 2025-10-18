# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RequestorMaster(Document):
	def after_save(self):
		try:
			from vms.material.doctype.material_aging_track.material_aging_track import create_or_update_aging_tracker_from_requestor
			create_or_update_aging_tracker_from_requestor(self.name)
			return {"status": "success", "message": "Aging tracker update completed"}
		except Exception as e:
			frappe.log_error(f"Aging tracker update error for {self.name}: {str(e)}")
			return {"status": "error", "message": str(e)}	
    # pass
	# def validate(self):
	# 	try:
	# 		if self.request_id == "" or self.request_id is None:
	# 			self.request_id = frappe.generate_hash(length=7)
	# 		return {"status": "success", "message": "Request ID validated"}
	# 	except Exception as e:
	# 		frappe.log_error(f"Request ID validation error for {self.name}: {str(e)}")
	# 		return {"status": "error", "message": str(e)}