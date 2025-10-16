# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MaterialAgingTrack(Document):
	pass




def create_or_update_aging_tracker_from_requestor(requestor_name):
	try:
		requestor = frappe.get_doc("Requestor Master", requestor_name)
		if not requestor:
			return {"status": "error", "message": f"Requestor Master {requestor_name} not found"}
		material_aging_track = frappe.get_all(
			"Material Aging Track",
			filters={"requestor": requestor_name},
			fields=["name"],
			limit=1,
		)
		if material_aging_track:
			aging_doc = frappe.get_doc("Material Aging Track", material_aging_track[0].name)
		else:
			aging_doc = frappe.new_doc("Material Aging Track")
			aging_doc.mat_id = requestor_name
		aging_doc.requestor_id = requestor.requestor_name
		aging_doc.material_master_id = requestor.material_master_ref_no or ""
		aging_doc.requestor_creation_dt = requestor.creation
		aging_doc.material_master_creation_dt = frappe.get_value(
																	"Material Master", requestor.material_master_ref_no, "creation"
																) if requestor.material_master_ref_no else None
		aging_doc.save()
		
		return {"status": "success", "message": "Aging tracker update completed"}
	except Exception as e:
		frappe.log_error(f"Aging tracker update error for {requestor_name}: {str(e)}")
		return {"status": "error", "message": str(e)}