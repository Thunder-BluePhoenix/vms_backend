# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, time_diff_in_seconds, add_to_date
from datetime import datetime, timedelta

class MaterialAgingTrack(Document):
	def validate(self):
		self.calculate_all_duration_fields()
		self.calculate_days_since_creation()
		self.set_aging_status()


	def calculate_all_duration_fields(self):
		"""Calculate all duration fields"""
		req_doc = frappe.get_doc("Requestor Master", self.requestor)
		mat_doc = frappe.get_doc("Material Master", self.material_master_id) if self.material_master_id else None
		log_erp_to_sap = frappe.get_doc("MO SAP Logs", self.erp_to_sap_mo_log) if self.erp_to_sap_mo_log else None
		log_sap_to_erp = frappe.get_doc("MO SAP Logs", self.sap_to_erp_mo_log) if self.sap_to_erp_mo_log else None

		if req_doc and mat_doc:
			creation_req = get_datetime(req_doc.creation)
			creation_mat = get_datetime(mat_doc.creation)
			duration_seconds = time_diff_in_seconds(creation_mat, creation_req)
			self.req_to_mat_duration = duration_seconds if duration_seconds > 0 else 0


		if req_doc and log_erp_to_sap:
			creation_req = get_datetime(req_doc.creation)
			creation_log_erp = get_datetime(log_erp_to_sap.creation)
			duration_seconds = time_diff_in_seconds(creation_log_erp, creation_req)
			self.mat_onboard_duration_e_s = duration_seconds if duration_seconds > 0 else 0

		if req_doc and log_sap_to_erp:
			creation_req = get_datetime(req_doc.creation)
			creation_log_sap = get_datetime(log_sap_to_erp.creation)
			duration_seconds = time_diff_in_seconds(creation_log_sap, creation_req)
			self.mat_onboard_duration = duration_seconds if duration_seconds > 0 else 0

		if log_erp_to_sap and log_sap_to_erp:
			creation_log_erp = get_datetime(log_erp_to_sap.creation)
			creation_log_sap = get_datetime(log_sap_to_erp.creation)
			duration_seconds = time_diff_in_seconds(creation_log_sap, creation_log_erp)
			self.mat_onboard_duration_s_e = duration_seconds if duration_seconds > 0 else 0

		


	def calculate_days_since_creation(self):
		"""Calculate days since cart creation"""
		if self.material_master_creation_dt:
			try:
				creation_dt = get_datetime(self.material_master_creation_dt)
				current_dt = now_datetime()
				days_diff = (current_dt - creation_dt).days
				self.days_since_creation = days_diff
			except Exception as e:
				frappe.log_error(f"Error calculating days since creation: {str(e)}")
				self.days_since_creation = 0


	def set_aging_status(self):
		"""Set aging status based on days since creation"""
		if not self.days_since_creation:
			self.aging_status = "New (0-30 days)"
			return

		if self.days_since_creation <= 30:
			self.aging_status = "New (0-30 days)"
		elif self.days_since_creation <= 90:
			self.aging_status = "Recent (31-90 days)"
		elif self.days_since_creation <= 180:
			self.aging_status = "Established (91-180 days)"
		else:
			self.aging_status = "Long Term (180+ days)"


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
	


def update_aging_tracker_on_sap_sync(sap_id):
	try:
		sap_log = frappe.get_doc("MO SAP Logs", sap_id)
		if not sap_log:
			return {"status": "error", "message": f"MO SAP Log {sap_id} not found"}
		requestor_doc = frappe.get_doc("Requestor Master", sap_log.requestor_ref)
		if not requestor_doc:
			return {"status": "error", "message": f"Requestor Master {sap_log.requestor_ref} not found"}
		mat_age_doc = frappe.get_doc("Material Aging Track", {"requestor": sap_log.requestor_ref})
		if not mat_age_doc:
			return {"status": "error", "message": f"Material Aging Track for {sap_log.requestor_ref} not found"}
		if sap_log.direction == "ERP to SAP":
			mat_age_doc.erp_to_sap_mo_log = sap_id
			mat_age_doc.sap_mo_log_creation_e_s = sap_log.creation
			mat_age_doc.save()
		else:
			mat_age_doc.sap_to_erp_mo_log = sap_id
			mat_age_doc.sap_mo_log_creation_s_e = sap_log.creation
			mat_age_doc.save()
		return {"status": "success", "message": "Aging tracker SAP sync update completed"}
	except Exception as e:
		frappe.log_error(f"Aging tracker SAP sync update error for {sap_id}: {str(e)}")
		return {"status": "error", "message": str(e)}

		

		

	





def update_all_mo_aging_tracks():
	"""
	Main scheduler function - enqueues background job
	"""
	frappe.enqueue(
		"vms.material.doctype.material_aging_track.material_aging_track.process_mo_aging_tracks_background",
		queue="long",  # Use 'long' queue for long-running jobs
		timeout=7200,  # 2 hour timeout
		is_async=True,
		job_name="update_mo_aging_tracks"
	)
	
	return {
		"status": "queued",
		"message": "Cart Aging Track update job has been queued"
	}


def process_mo_aging_tracks_background():
	"""
	Background job to process all records in batches
	"""
	batch_size = 1000
	offset = 0
	total_updated = 0
	total_errors = 0
	
	total_records = frappe.db.count("Material Aging Track")
	
	frappe.publish_realtime(
		"mo_aging_update_progress",
		{"progress": 0, "total": total_records, "status": "started"},
		user=frappe.session.user
	)
	
	while offset < total_records:
		try:
			tracks = frappe.get_all(
				"Material Aging Track",
				fields=["name", "requestor_id"],
				limit_start=offset,
				limit_page_length=batch_size
			)
			
			if not tracks:
				break
			
			for track in tracks:
				try:
					track_doc = frappe.get_doc("Material Aging Track", track.name)
					
					if track.requestor_id:
						create_or_update_aging_tracker_from_requestor(track.requestor_id)
					
					track_doc.save(ignore_permissions=True)
					total_updated += 1
					
				except Exception as e:
					total_errors += 1
					frappe.log_error(
						title=f"Error updating MO Aging Track {track.name}",
						message=frappe.get_traceback()
					)
			
			frappe.db.commit()
			offset += batch_size
			
			# Publish progress
			progress = (offset / total_records) * 100
			frappe.publish_realtime(
				"mo_aging_update_progress",
				{
					"progress": progress,
					"updated": total_updated,
					"errors": total_errors,
					"total": total_records
				},
				user=frappe.session.user
			)
			
		except Exception as batch_error:
			frappe.log_error(
				title=f"Error processing batch at offset {offset}",
				message=frappe.get_traceback()
			)
			offset += batch_size
	
	frappe.publish_realtime(
		"mo_aging_update_progress",
		{
			"progress": 100,
			"status": "completed",
			"updated": total_updated,
			"errors": total_errors,
			"total": total_records
		},
		user=frappe.session.user
	)
	
	return {
		"status": "success",
		"updated": total_updated,
		"errors": total_errors,
		"total": total_records
	}