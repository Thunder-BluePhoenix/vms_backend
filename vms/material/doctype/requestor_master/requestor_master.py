# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RequestorMaster(Document):
	# def after_insert(self):
	# 	try:
	# 		from vms.vms.doctype.vendor_aging_tracker.vendor_aging_tracker import create_or_update_aging_tracker_from_requestor
	# 		create_or_update_aging_tracker_from_requestor(self.name)
	# 		return {"status": "success", "message": "Aging tracker update completed"}
	# 	except Exception as e:
	# 		frappe.log_error(f"Aging tracker update error for {self.name}: {str(e)}")
	# 		return {"status": "error", "message": str(e)}	
    pass
