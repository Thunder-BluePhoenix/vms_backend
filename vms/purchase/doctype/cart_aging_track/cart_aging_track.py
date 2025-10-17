# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, time_diff_in_seconds, add_to_date
from datetime import datetime, timedelta


class CartAgingTrack(Document):
	"""
	Cart Aging Track - Tracks aging metrics for Cart -> PR (ERP) -> SAP PR workflow
	"""

	def validate(self):
		"""Validate and calculate all aging metrics"""
		self.calculate_days_since_creation()
		self.set_aging_status()
		self.calculate_all_durations()

	def before_save(self):
		"""Calculate metrics before saving"""
		self.update_approval_datetime()

	# ============================================================================
	# BUTTON METHODS - View Linked Documents
	# ============================================================================

	def view_cart_details(self):
		"""
		Button method to view linked Cart Details document
		This creates a button in the form that redirects to Cart Details
		"""
		if not self.cart_id:
			frappe.throw("No Cart Details linked to this aging track")
		
		return {
			"type": "redirect",
			"route": ["Form", "Cart Details", self.cart_id]
		}

	def view_pr_erp(self):
		"""
		Button method to view linked Purchase Requisition Webform (ERP PR)
		This creates a button in the form that redirects to PR Webform
		"""
		if not self.pr_erp_link:
			frappe.throw("No Purchase Requisition (ERP) linked to this aging track")
		
		return {
			"type": "redirect",
			"route": ["Form", "Purchase Requisition Webform", self.pr_erp_link]
		}

	def view_pr_sap(self):
		"""
		Button method to view linked Purchase Requisition Form (SAP PR)
		This creates a button in the form that redirects to SAP PR
		"""
		if not self.pr_sap_link:
			frappe.throw("No SAP Purchase Requisition linked to this aging track")
		
		return {
			"type": "redirect",
			"route": ["Form", "Purchase Requisition Form", self.pr_sap_link]
		}

	def calculate_days_since_creation(self):
		"""Calculate days since cart creation"""
		if self.cart_creation_datetime:
			try:
				creation_dt = get_datetime(self.cart_creation_datetime)
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

	def update_approval_datetime(self):
		"""
		Update cart approval datetime based on Cart Details approval logic:
		- If hod_approved == 1 and is_requested_second_stage_approval != 1: Cart is approved
		- If hod_approved == 1 and is_requested_second_stage_approval == 1: Check second_stage_approved == 1
		"""
		if not self.cart_id:
			return

		try:
			# Fetch Cart Details document
			cart_doc = frappe.get_doc("Cart Details", self.cart_id)
			
			# Check if cart is approved based on the approval logic
			is_cart_approved = self.check_cart_approval_status(cart_doc)
			
			# If cart is approved and approval datetime is not set, set it now
			if is_cart_approved and not self.cart_approval_datetime:
				self.cart_approval_datetime = now_datetime()
				
		except Exception as e:
			frappe.log_error(
				title=f"Error updating approval datetime for {self.name}",
				message=f"Cart ID: {self.cart_id}\nError: {str(e)}\n{frappe.get_traceback()}"
			)

	def check_cart_approval_status(self, cart_doc):
		"""
		Check if cart is approved based on complex approval logic:
		1. If hod_approved == 1 and is_requested_second_stage_approval != 1 -> Approved
		2. If hod_approved == 1 and is_requested_second_stage_approval == 1 -> Check second_stage_approved == 1
		
		Returns:
			bool: True if cart is approved, False otherwise
		"""
		hod_approved = getattr(cart_doc, 'hod_approved', 0)
		is_requested_second_stage = getattr(cart_doc, 'is_requested_second_stage_approval', 0)
		second_stage_approved = getattr(cart_doc, 'second_stage_approved', 0)
		
		# Case 1: HOD approved and no second stage requested
		if hod_approved == 1 and is_requested_second_stage != 1:
			return True
		
		# Case 2: HOD approved, second stage requested, and second stage approved
		if hod_approved == 1 and is_requested_second_stage == 1 and second_stage_approved == 1:
			return True
		
		return False

	def calculate_all_durations(self):
		"""Calculate all duration fields"""
		self.calculate_cart_approval_duration()
		self.calculate_cart_to_pr_duration()
		self.calculate_erp_to_sap_duration()
		self.calculate_cart_to_sap_duration()
		self.calculate_approved_cart_to_sap_duration()

	def calculate_cart_approval_duration(self):
		"""Calculate duration from cart creation to cart approval"""
		if self.cart_creation_datetime and self.cart_approval_datetime:
			try:
				creation_dt = get_datetime(self.cart_creation_datetime)
				approval_dt = get_datetime(self.cart_approval_datetime)
				
				# Calculate duration in seconds
				duration_seconds = time_diff_in_seconds(approval_dt, creation_dt)
				self.cart_approval_duration = duration_seconds if duration_seconds > 0 else 0
			except Exception as e:
				frappe.log_error(f"Error calculating cart approval duration: {str(e)}")
				self.cart_approval_duration = 0

	def calculate_cart_to_pr_duration(self):
		"""Calculate duration from cart creation to ERP PR creation"""
		if self.cart_creation_datetime and self.pr_creation_datetime:
			try:
				creation_dt = get_datetime(self.cart_creation_datetime)
				pr_dt = get_datetime(self.pr_creation_datetime)
				
				duration_seconds = time_diff_in_seconds(pr_dt, creation_dt)
				self.cart_to_pr_creation = duration_seconds if duration_seconds > 0 else 0
			except Exception as e:
				frappe.log_error(f"Error calculating cart to PR duration: {str(e)}")
				self.cart_to_pr_creation = 0

	def calculate_erp_to_sap_duration(self):
		"""Calculate duration from ERP PR creation to SAP PR creation"""
		if self.pr_creation_datetime and self.sap_pr_creation_datetime:
			try:
				erp_pr_dt = get_datetime(self.pr_creation_datetime)
				sap_pr_dt = get_datetime(self.sap_pr_creation_datetime)
				
				duration_seconds = time_diff_in_seconds(sap_pr_dt, erp_pr_dt)
				self.erp_to_sap_pr_creation = duration_seconds if duration_seconds > 0 else 0
			except Exception as e:
				frappe.log_error(f"Error calculating ERP to SAP duration: {str(e)}")
				self.erp_to_sap_pr_creation = 0

	def calculate_cart_to_sap_duration(self):
		"""Calculate total duration from cart creation to SAP PR creation"""
		if self.cart_creation_datetime and self.sap_pr_creation_datetime:
			try:
				cart_dt = get_datetime(self.cart_creation_datetime)
				sap_pr_dt = get_datetime(self.sap_pr_creation_datetime)
				
				duration_seconds = time_diff_in_seconds(sap_pr_dt, cart_dt)
				self.cart_creation_to_sap_pr_creation = duration_seconds if duration_seconds > 0 else 0
			except Exception as e:
				frappe.log_error(f"Error calculating cart to SAP duration: {str(e)}")
				self.cart_creation_to_sap_pr_creation = 0

	def calculate_approved_cart_to_sap_duration(self):
		"""Calculate duration from cart approval to SAP PR creation"""
		if self.cart_approval_datetime and self.sap_pr_creation_datetime:
			try:
				approval_dt = get_datetime(self.cart_approval_datetime)
				sap_pr_dt = get_datetime(self.sap_pr_creation_datetime)
				
				duration_seconds = time_diff_in_seconds(sap_pr_dt, approval_dt)
				self.approved_cart_to_sap_creation = duration_seconds if duration_seconds > 0 else 0
			except Exception as e:
				frappe.log_error(f"Error calculating approved cart to SAP duration: {str(e)}")
				self.approved_cart_to_sap_creation = 0


# ============================================================================
# HELPER FUNCTIONS FOR CART AGING TRACKING
# ============================================================================

@frappe.whitelist()
def create_or_update_cart_aging_track(cart_id):
	"""
	Create or update Cart Aging Track record for a given cart
	
	Args:
		cart_id (str): Cart Details ID
	
	Returns:
		dict: Status and message
	"""
	try:
		# Check if Cart Aging Track already exists
		existing_track = frappe.db.get_value("Cart Aging Track", {"cart_id": cart_id}, "name")
		
		if existing_track:
			# Update existing record
			track_doc = frappe.get_doc("Cart Aging Track", existing_track)
			update_cart_aging_track_from_cart(track_doc, cart_id)
			track_doc.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"status": "success",
				"message": f"Cart Aging Track {existing_track} updated successfully",
				"track_id": existing_track
			}
		else:
			# Create new record
			track_doc = frappe.new_doc("Cart Aging Track")
			track_doc.cart_id = cart_id
			track_doc.cat_id =  cart_id
			update_cart_aging_track_from_cart(track_doc, cart_id)
			track_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"status": "success",
				"message": f"Cart Aging Track {track_doc.name} created successfully",
				"track_id": track_doc.name
			}
			
	except Exception as e:
		frappe.log_error(
			title=f"Error creating/updating Cart Aging Track for {cart_id}",
			message=frappe.get_traceback()
		)
		return {
			"status": "error",
			"message": str(e)
		}


def update_cart_aging_track_from_cart(track_doc, cart_id):
	"""
	Update Cart Aging Track document with data from Cart Details
	
	Args:
		track_doc: Cart Aging Track document
		cart_id (str): Cart Details ID
	"""
	try:
		# Get Cart Details document
		cart_doc = frappe.get_doc("Cart Details", cart_id)
		
		# Set cart creation datetime
		if hasattr(cart_doc, 'creation') and cart_doc.creation:
			track_doc.cart_creation_datetime = cart_doc.creation
		
		# Get PR links from Cart Details
		if hasattr(cart_doc, 'purchase_requisition_form') and cart_doc.purchase_requisition_form:
			track_doc.pr_erp_link = cart_doc.purchase_requisition_form
			
			# Get PR creation datetime
			pr_erp_doc = frappe.get_doc("Purchase Requisition Webform", cart_doc.purchase_requisition_form)
			if hasattr(pr_erp_doc, 'creation') and pr_erp_doc.creation:
				track_doc.pr_creation_datetime = pr_erp_doc.creation
			
			# Get SAP PR link from Purchase Requisition Webform
			if pr_erp_doc.form_status == "PR Created" and hasattr(pr_erp_doc, 'purchase_requisition_form_link') and pr_erp_doc.purchase_requisition_form_link:
				track_doc.pr_sap_link = pr_erp_doc.purchase_requisition_form_link
				
				# Get SAP PR creation datetime
				pr_sap_doc = frappe.get_doc("Purchase Requisition Form", pr_erp_doc.purchase_requisition_form_link)
				if hasattr(pr_sap_doc, 'creation') and pr_sap_doc.creation:
					track_doc.sap_pr_creation_datetime = pr_sap_doc.creation
		
	except Exception as e:
		frappe.log_error(
			title=f"Error updating Cart Aging Track from Cart {cart_id}",
			message=frappe.get_traceback()
		)


@frappe.whitelist()
def update_aging_track_on_pr_creation(pr_webform_id, cart_details_id):
	"""
	Update Cart Aging Track when Purchase Requisition Webform (ERP PR) is created
	
	Args:
		pr_webform_id (str): Purchase Requisition Webform ID
		cart_details_id (str): Cart Details ID
	
	Returns:
		dict: Status and message
	"""
	try:
		# Find or create Cart Aging Track
		result = create_or_update_cart_aging_track(cart_details_id)
		
		if result.get("status") == "success":
			track_doc = frappe.get_doc("Cart Aging Track", result.get("track_id"))
			track_doc.pr_erp_link = pr_webform_id
			
			# Set PR creation datetime
			pr_doc = frappe.get_doc("Purchase Requisition Webform", pr_webform_id)
			if hasattr(pr_doc, 'creation') and pr_doc.creation:
				track_doc.pr_creation_datetime = pr_doc.creation
			
			track_doc.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"status": "success",
				"message": f"Cart Aging Track updated with PR creation for {cart_details_id}"
			}
		else:
			return result
			
	except Exception as e:
		frappe.log_error(
			title=f"Error updating aging track on PR creation",
			message=f"PR: {pr_webform_id}, Cart: {cart_details_id}\n{frappe.get_traceback()}"
		)
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def update_aging_track_on_sap_pr_creation(pr_webform_id, pr_sap_id):
	"""
	Update Cart Aging Track when SAP Purchase Requisition is created
	
	Args:
		pr_webform_id (str): Purchase Requisition Webform ID
		pr_sap_id (str): Purchase Requisition Form (SAP) ID
	
	Returns:
		dict: Status and message
	"""
	try:
		# Find Cart Aging Track by PR ERP link
		track_name = frappe.db.get_value("Cart Aging Track", {"pr_erp_link": pr_webform_id}, "name")
		
		if not track_name:
			# Try to find by cart_id from PR Webform
			pr_doc = frappe.get_doc("Purchase Requisition Webform", pr_webform_id)
			if hasattr(pr_doc, 'cart_details_id') and pr_doc.cart_details_id:
				result = create_or_update_cart_aging_track(pr_doc.cart_details_id)
				if result.get("status") == "success":
					track_name = result.get("track_id")
		
		if track_name:
			track_doc = frappe.get_doc("Cart Aging Track", track_name)
			track_doc.pr_sap_link = pr_sap_id
			
			# Set SAP PR creation datetime
			pr_sap_doc = frappe.get_doc("Purchase Requisition Form", pr_sap_id)
			if hasattr(pr_sap_doc, 'creation') and pr_sap_doc.creation:
				track_doc.sap_pr_creation_datetime = pr_sap_doc.creation
			
			track_doc.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"status": "success",
				"message": f"Cart Aging Track updated with SAP PR creation"
			}
		else:
			return {
				"status": "warning",
				"message": f"No Cart Aging Track found for PR {pr_webform_id}"
			}
			
	except Exception as e:
		frappe.log_error(
			title=f"Error updating aging track on SAP PR creation",
			message=f"PR Webform: {pr_webform_id}, SAP PR: {pr_sap_id}\n{frappe.get_traceback()}"
		)
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def update_aging_track_on_cart_approval(cart_id):
	"""
	Update Cart Aging Track when cart is approved
	This should be called from Cart Details after approval
	
	Args:
		cart_id (str): Cart Details ID
	
	Returns:
		dict: Status and message
	"""
	try:
		# Find or create Cart Aging Track
		result = create_or_update_cart_aging_track(cart_id)
		
		if result.get("status") == "success":
			track_doc = frappe.get_doc("Cart Aging Track", result.get("track_id"))
			
			# Cart approval datetime will be set in validate() method
			# by checking the approval status
			track_doc.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"status": "success",
				"message": f"Cart Aging Track updated with approval for {cart_id}"
			}
		else:
			return result
			
	except Exception as e:
		frappe.log_error(
			title=f"Error updating aging track on cart approval",
			message=f"Cart: {cart_id}\n{frappe.get_traceback()}"
		)
		return {
			"status": "error",
			"message": str(e)
		}


# ============================================================================
# SCHEDULED JOBS / BULK UPDATE FUNCTIONS
# ============================================================================

# def update_all_cart_aging_tracks():
# 	"""
# 	Scheduled job to update all Cart Aging Track records
# 	Run this daily to keep aging metrics up to date
# 	"""
# 	try:
# 		all_tracks = frappe.get_all("Cart Aging Track", fields=["name", "cart_id"])
		
# 		updated_count = 0
# 		error_count = 0
		
# 		for track in all_tracks:
# 			try:
# 				track_doc = frappe.get_doc("Cart Aging Track", track.name)
				
# 				# Update from cart if cart_id exists
# 				if track.cart_id:
# 					update_cart_aging_track_from_cart(track_doc, track.cart_id)
				
# 				track_doc.save(ignore_permissions=True)
# 				updated_count += 1
				
# 			except Exception as e:
# 				error_count += 1
# 				frappe.log_error(
# 					title=f"Error updating Cart Aging Track {track.name}",
# 					message=frappe.get_traceback()
# 				)
		
# 		frappe.db.commit()
		
# 		return {
# 			"status": "success",
# 			"message": f"Updated {updated_count} records, {error_count} errors",
# 			"updated": updated_count,
# 			"errors": error_count
# 		}
		
# 	except Exception as e:
# 		frappe.log_error(
# 			title="Error in bulk Cart Aging Track update",
# 			message=frappe.get_traceback()
# 		)
# 		return {
# 			"status": "error",
# 			"message": str(e)
# 		}


def create_missing_cart_aging_tracks():
	"""
	Create Cart Aging Track records for all carts that don't have one
	Run this to backfill missing records
	"""
	try:
		# Get all Cart Details
		all_carts = frappe.get_all("Cart Details", fields=["name"])
		
		created_count = 0
		skipped_count = 0
		error_count = 0
		
		for cart in all_carts:
			try:
				# Check if Cart Aging Track exists
				existing = frappe.db.exists("Cart Aging Track", {"cart_id": cart.name})
				
				if not existing:
					result = create_or_update_cart_aging_track(cart.name)
					if result.get("status") == "success":
						created_count += 1
					else:
						error_count += 1
				else:
					skipped_count += 1
					
			except Exception as e:
				error_count += 1
				frappe.log_error(
					title=f"Error creating Cart Aging Track for {cart.name}",
					message=frappe.get_traceback()
				)
		
		frappe.db.commit()
		
		return {
			"status": "success",
			"message": f"Created {created_count} new records, skipped {skipped_count}, {error_count} errors",
			"created": created_count,
			"skipped": skipped_count,
			"errors": error_count
		}
		
	except Exception as e:
		frappe.log_error(
			title="Error creating missing Cart Aging Tracks",
			message=frappe.get_traceback()
		)
		return {
			"status": "error",
			"message": str(e)
		}
	


def update_all_cart_aging_tracks():
	"""
	Main scheduler function - enqueues background job
	"""
	frappe.enqueue(
		"vms.purchase.doctype.cart_aging_track.cart_aging_track.process_cart_aging_tracks_background",
		queue="long",  # Use 'long' queue for long-running jobs
		timeout=3600,  # 1 hour timeout
		is_async=True,
		job_name="update_cart_aging_tracks"
	)
	
	return {
		"status": "queued",
		"message": "Cart Aging Track update job has been queued"
	}


def process_cart_aging_tracks_background():
	"""
	Background job to process all records in batches
	"""
	batch_size = 1000
	offset = 0
	total_updated = 0
	total_errors = 0
	
	total_records = frappe.db.count("Cart Aging Track")
	
	frappe.publish_realtime(
		"cart_aging_update_progress",
		{"progress": 0, "total": total_records, "status": "started"},
		user=frappe.session.user
	)
	
	while offset < total_records:
		try:
			tracks = frappe.get_all(
				"Cart Aging Track",
				fields=["name", "cart_id"],
				limit_start=offset,
				limit_page_length=batch_size
			)
			
			if not tracks:
				break
			
			for track in tracks:
				try:
					track_doc = frappe.get_doc("Cart Aging Track", track.name)
					
					if track.cart_id:
						update_cart_aging_track_from_cart(track_doc, track.cart_id)
					
					track_doc.save(ignore_permissions=True)
					total_updated += 1
					
				except Exception as e:
					total_errors += 1
					frappe.log_error(
						title=f"Error updating Cart Aging Track {track.name}",
						message=frappe.get_traceback()
					)
			
			frappe.db.commit()
			offset += batch_size
			
			# Publish progress
			progress = (offset / total_records) * 100
			frappe.publish_realtime(
				"cart_aging_update_progress",
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
		"cart_aging_update_progress",
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