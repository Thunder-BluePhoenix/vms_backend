# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaterialAgingTrack(Document):
	pass




def create_or_update_aging_tracker_from_requestor(requestor_name):
	try:
		
		return {"status": "success", "message": "Aging tracker update completed"}
	except Exception as e:
		frappe.log_error(f"Aging tracker update error for {requestor_name}: {str(e)}")
		return {"status": "error", "message": str(e)}