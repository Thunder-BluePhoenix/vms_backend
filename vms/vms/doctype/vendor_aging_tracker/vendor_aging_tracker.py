# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, get_datetime, date_diff, getdate, nowdate
import json



class VendorAgingTracker(Document):
	"""
	Vendor Aging Tracker DocType Controller
	Tracks aging for vendor onboarding and associated purchase orders
	"""

	def validate(self):
		"""Validate and calculate aging metrics"""
		self.calculate_vendor_aging()
		self.update_po_aging()
		self.calculate_summary_metrics()
		self.calculate_vendor_aging_duration()

	def before_save(self):
		"""Before save calculations"""
		self.update_vendor_status()
		


	

	def calculate_vendor_aging_duration(self):
		"""Calculate total vendor aging duration"""
		if self.vendor_creation_date and self.vendor_onboarding_date and self.vendor_creation_date_sap:
			try:
				# Convert string datetime to datetime objects
				creation_datetime = get_datetime(self.vendor_creation_date)
				onboarding_datetime = get_datetime(self.vendor_onboarding_date)
				sap_approval_datetime = get_datetime(self.vendor_creation_date_sap)
				
				# Calculate duration from onboarding to SAP approval
				time_diff = sap_approval_datetime - onboarding_datetime
				
				# Convert to seconds (Duration field stores value in seconds)
				self.vendor_onboard_to_approval_time = time_diff.total_seconds() if time_diff else 0
			except:
				self.vendor_onboard_to_approval_time = 0

		if self.oldest_po_creation_time:
			try:
				# Convert to datetime objects
				oldest_po_datetime = get_datetime(self.oldest_po_creation_time)
				onboarding_datetime = get_datetime(self.vendor_onboarding_date)
				sap_approval_datetime = get_datetime(self.vendor_creation_date_sap)
				
				# Calculate durations
				total_po_time_diff = oldest_po_datetime - onboarding_datetime
				approve_to_first_po_time = oldest_po_datetime - sap_approval_datetime

				self.vendor_creation_to_po_time = total_po_time_diff.total_seconds() if total_po_time_diff else 0
				self.vendor_approval_to__first_po_time = approve_to_first_po_time.total_seconds() if approve_to_first_po_time else 0
			except:
				self.vendor_creation_to_po_time = 0
				self.vendor_approval_to__first_po_time = 0


	def calculate_vendor_aging(self):
		"""Calculate days since vendor creation"""
		if self.vendor_creation_date:
			creation_datetime = get_datetime(self.vendor_creation_date)
			current_datetime = get_datetime(now())
			self.days_since_creation = (current_datetime - creation_datetime).days
			
			# Set aging status based on days
			self.vendor_aging_status = self.get_aging_status_category(self.days_since_creation)

	def get_aging_status_category(self, days):
		"""Determine aging status category"""
		if days <= 30:
			return "New (0-30 days)"
		elif days <= 90:
			return "Recent (31-90 days)"
		elif days <= 180:
			return "Established (91-180 days)"
		else:
			return "Long Term (180+ days)"

	def update_po_aging(self):
		"""Calculate aging for each purchase order"""
		if not self.purchase_order_details:
			return
		
		current_date = getdate(nowdate())
		
		for po in self.purchase_order_details:
			if po.po_date:
				po_date = getdate(po.po_date)
				po.days_since_po = date_diff(current_date, po_date)
				po.po_aging_status = self.get_po_aging_status(po.days_since_po)

		

	def get_po_aging_status(self, days):
		"""Determine PO aging status"""
		if days <= 7:
			return "Fresh (0-7 days)"
		elif days <= 15:
			return "Recent (8-15 days)"
		elif days <= 30:
			return "Moderate (16-30 days)"
		elif days <= 60:
			return "Old (31-60 days)"
		else:
			return "Very Old (60+ days)"

	def calculate_summary_metrics(self):
		"""Calculate summary metrics for aging"""
		self.total_aging_days = self.days_since_creation
		
		if self.purchase_order_details:
			# Count total POs
			self.total_purchase_orders = len(self.purchase_order_details)
			
			# Calculate average PO aging
			total_days = sum([po.days_since_po or 0 for po in self.purchase_order_details])
			self.average_po_aging = total_days / len(self.purchase_order_details) if self.purchase_order_details else 0
			
			# Calculate total PO value
			self.total_po_value = sum([po.po_value or 0 for po in self.purchase_order_details])
			
			# Find oldest pending PO and oldest PO
			oldest_pending_po = None
			max_days = 0
			max_pending_days = 0
			pending_count = 0
			
			for po in self.purchase_order_details:
				# Count pending POs (not completed/closed)
				if po.po_status not in ["Completed", "Closed", "Cancelled"]:
					pending_count += 1
					
					# Find oldest pending PO
					if po.days_since_po and po.days_since_po > max_pending_days:
						max_pending_days = po.days_since_po
						oldest_pending_po = po.purchase_order
				
				# Find oldest PO (regardless of status)
				# if po.days_since_po and po.days_since_po > max_days:
				# 	max_days = po.days_since_po
				# 	oldest_po = po.purchase_order
			oldest_po = None
			oldest_po_datetime = None

			for po in self.purchase_order_details:
				if po.po_creation_datetime:
					po_datetime = get_datetime(po.po_creation_datetime)
					
					# Check if this is the oldest PO so far
					if oldest_po_datetime is None or po_datetime < oldest_po_datetime:
						oldest_po_datetime = po_datetime
						oldest_po = po.purchase_order

			# Store the results
			self.oldest_po = oldest_po
			self.oldest_po_creation_time = oldest_po_datetime
			
			self.oldest_pending_po = oldest_pending_po
			# self.oldest_pending_po_creation_time = frappe.get_value("Purchase Order", oldest_pending_po, "creation") if oldest_pending_po else None
			self.pending_po_count = pending_count
			
			# Get newest PO date
			po_dates = [getdate(po.po_date) for po in self.purchase_order_details if po.po_date]
			if po_dates:
				self.newest_po_date = max(po_dates)

	def update_vendor_status(self):
		"""Update vendor status based on activity"""
		if self.purchase_order_details:
			self.vendor_status = "Active"
			self.last_activity_date = self.newest_po_date
		elif self.days_since_creation > 90 and not self.purchase_order_details:
			self.vendor_status = "Inactive"
		else:
			self.vendor_status = "Active"


# Hook functions to be called from other doctypes

@frappe.whitelist()
def create_or_update_aging_tracker_from_vendor_onboarding(vendor_onboarding_name):
	"""
	Create or update Vendor Aging Tracker when Vendor Onboarding is created/updated
	ONE tracker per vendor onboarding (not per vendor code)
	Called from Vendor Onboarding after_insert/on_update hook
	"""
	try:
		onboarding_doc = frappe.get_doc("Vendor Onboarding", vendor_onboarding_name)
		
		
		# Check if aging tracker already exists for this vendor onboarding
		existing = frappe.db.exists("Vendor Aging Tracker", {"vendor_onboarding_link": vendor_onboarding_name})
		
		if existing:
			# Update existing tracker
			aging_doc = frappe.get_doc("Vendor Aging Tracker", existing)
			# Clear existing vendor codes to refresh
			aging_doc.vendor_codes_by_company = []
		else:
			# Create new aging tracker
			aging_doc = frappe.new_doc("Vendor Aging Tracker")
			aging_doc.vendor_onboarding_link = vendor_onboarding_name
			aging_doc.ag_id = vendor_onboarding_name
		
		# Extract vendor information from onboarding document
		aging_doc.vendor_name = onboarding_doc.vendor_name or ""
		aging_doc.vendor_ref_no = onboarding_doc.ref_no or ""
		
		# Set creation dates
		if onboarding_doc.creation:
			aging_doc.vendor_creation_date = onboarding_doc.creation
			aging_doc.vendor_onboarding_date = onboarding_doc.creation
		
		# Set vendor status based on onboarding status
		if onboarding_doc.onboarding_form_status == "Approved":
			aging_doc.vendor_status = "Active"
		elif onboarding_doc.rejected:
			aging_doc.vendor_status = "Blocked"
		else:
			aging_doc.vendor_status = "Pending"
		
		# Process all company details and add to child table
		primary_code_set = False
		for idx, company_detail in enumerate(onboarding_doc.vendor_company_details):
			if not company_detail.vendor_company_details:
				continue
			
			# Set primary vendor code (first one)
			onb_com= frappe.get_doc("Vendor Onboarding Company Details", company_detail.vendor_company_details)
			sap_client_code = None
			if not primary_code_set:
				# aging_doc.primary_vendor_code = company_detail.vendor_code
				aging_doc.company_code = onb_com.company_name or ""
				aging_doc.gst_number = onb_com.gst or ""
				
				# Get SAP client code from company master
				if onb_com.company_name:
					try:
						company_master = frappe.get_doc("Company Master", onb_com.company_name)
						if hasattr(company_master, 'sap_client_code'):
							aging_doc.sap_client_code = company_master.sap_client_code
							sap_client_code = company_master.sap_client_code
					except:
						pass
				
				primary_code_set = True
			
			# Add to vendor codes child table
			for cgt in onb_com.comp_gst_table:
				aging_doc.append("vendor_codes_by_company", {
					"company": onb_com.company_name or "",
					"company_code": onb_com.company_name or "",
					"sap_client_code":sap_client_code or "",
					"gst_number": cgt.gst_number or "",
					"state": cgt.gst_state or ""
				})
		
		aging_doc.save(ignore_permissions=True)
		frappe.db.commit()
		
		frappe.msgprint(f"Vendor Aging Tracker created/updated for: {onboarding_doc.vendor_name}")
		
	except Exception as e:
		frappe.log_error(f"Error creating/updating Vendor Aging Tracker from Vendor Onboarding: {str(e)}", 
						"Vendor Aging Tracker Error")


@frappe.whitelist()
def create_or_update_aging_tracker_from_sap_log(sap_log_name):
	try:
		sap_log = frappe.get_doc("VMS SAP Logs", sap_log_name)
		
		# Early exit if not successful or no data
		if sap_log.status != "Success" or not sap_log.total_transaction:
			return
		
		transaction_data = json.loads(sap_log.total_transaction)
		vendor_code = (
			transaction_data.get("transaction_summary", {}).get("vendor_code")
			or transaction_data.get("response_details", {}).get("vendor_code")
		)
		
		if not vendor_code:
			frappe.log_error("No vendor code found in SAP log total_transaction", "Vendor Aging Tracker")
			return
		
		request_details = transaction_data.get("request_details", {})
		payload = request_details.get("payload", {})
		doc_name = sap_log.vendor_onboarding_link
		
		# ✅ Get or create document
		if frappe.db.exists("Vendor Aging Tracker", doc_name):
			doc = frappe.get_doc("Vendor Aging Tracker", doc_name)
		else:
			doc = frappe.get_doc({
				"doctype": "Vendor Aging Tracker",
				"ag_id": doc_name,
				"vendor_onboarding_link": doc_name
			})
		
		# ✅ Update parent fields
		doc.vendor_name = payload.get("Name1", "")
		doc.primary_vendor_code = vendor_code
		doc.company_code = request_details.get("company_name", "")
		doc.sap_client_code = request_details.get("sap_client_code", "")
		doc.gst_number = request_details.get("gst_number", "")
		doc.vendor_ref_no = request_details.get("vendor_ref_no", "")
		doc.vendor_status = "Active"
		doc.sap_log_reference = sap_log.name
		
		# Handle vendor_creation_date_sap if empty
		if not doc.vendor_creation_date_sap:
			doc.vendor_creation_date_sap = get_datetime(sap_log.creation)
		
		# ✅ Update or add child table row
		child_doctype = "Vendor Aging Company Codes"
		company_code = request_details.get("company_name", "")
		gst_number = request_details.get("gst_number", "")
		sap_client_code = request_details.get("sap_client_code", "")
		
		# Find existing child row
		existing_row = None
		for row in doc.get("vendor_codes_by_company", []):
			if (row.company_code == company_code and 
				row.gst_number == gst_number and 
				row.sap_client_code == sap_client_code):
				existing_row = row
				break
		
		if existing_row:
			# Update existing row
			existing_row.vendor_code = vendor_code
			existing_row.vendor_code_generation_time = get_datetime(sap_log.creation)
			existing_row.vms_sap_log = sap_log.name
		else:
			# Add new row
			doc.append("vendor_codes_by_company", {
				"company_code": company_code,
				"gst_number": gst_number,
				"sap_client_code": sap_client_code,
				"vendor_code": vendor_code,
				"vendor_code_generation_time": get_datetime(sap_log.creation),
				"vms_sap_log": sap_log.name
			})
		
		# ✅ Save document - this will trigger validate() and before_save()
		doc.flags.ignore_permissions = True
		doc.save()
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(
			f"Error creating/updating Vendor Aging Tracker from SAP log: {frappe.get_traceback()}",
			"Vendor Aging Tracker Error"
		)
		frappe.db.rollback()


@frappe.whitelist()
def update_aging_tracker_with_po(purchase_order_name):
	"""
	Update Vendor Aging Tracker when a Purchase Order is created
	Matches PO vendor_code with any vendor code in the tracker
	Called from Purchase Order after_insert/on_update hook
	"""
	try:
		po_doc = frappe.get_doc("Purchase Order", purchase_order_name)
		
		# Check if vendor_code exists
		if not po_doc.vendor_code:
			return
		
		# Find aging tracker that has this vendor code in its child table
		tracker_name = frappe.db.sql("""
			SELECT parent 
			FROM `tabVendor Aging Company Codes` 
			WHERE vendor_code = %s
			LIMIT 1
		""", po_doc.vendor_code)
		
		if not tracker_name or not tracker_name[0][0]:
			# No tracker found with this vendor code
			frappe.log_error(
				f"No Vendor Aging Tracker found for vendor code: {po_doc.vendor_code}",
				"Vendor Aging Tracker PO Link"
			)
			return
		
		aging_doc = frappe.get_doc("Vendor Aging Tracker", tracker_name[0][0])
		
		# Check if PO already exists in the tracker
		po_exists = False
		for existing_po in aging_doc.purchase_order_details:
			if existing_po.purchase_order == purchase_order_name:
				po_exists = True
				# Update existing PO details
				existing_po.po_number = po_doc.po_number
				existing_po.po_date = po_doc.po_date
				existing_po.po_status = po_doc.vendor_status
				existing_po.po_value = po_doc.total_value_of_po__so
				existing_po.delivery_date = po_doc.delivery_date
				existing_po.po_creation_datetime = get_datetime(po_doc.creation)
				break
		
		# Add PO to tracker if it doesn't exist
		if not po_exists:
			aging_doc.append("purchase_order_details", {
				"purchase_order": purchase_order_name,
				"po_number": po_doc.po_number,
				"po_date": po_doc.po_date,
				"po_status": po_doc.vendor_status,
				"po_value": po_doc.total_value_of_po__so,
				"delivery_date": po_doc.delivery_date,
				"po_creation_datetime": get_datetime(po_doc.creation)
			})
		
		aging_doc.save(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error updating Vendor Aging Tracker with PO: {str(e)}", 
						"Vendor Aging Tracker PO Update Error")


@frappe.whitelist()
def refresh_all_aging_trackers():
    """
    Refresh all vendor aging trackers
    Can be called from a scheduled job or manually
    """
    try:
        aging_trackers = frappe.get_all("Vendor Aging Tracker", fields=["name"])
        
        for tracker in aging_trackers:
            doc = frappe.get_doc("Vendor Aging Tracker", tracker.name)
            doc.save(ignore_permissions=True)
        
        frappe.msgprint(f"Successfully refreshed {len(aging_trackers)} aging trackers")
        
    except Exception as e:
        frappe.log_error(f"Error refreshing aging trackers: {str(e)}", 
                        "Vendor Aging Refresh Error")


@frappe.whitelist()
def get_vendor_aging_dashboard_data():
    """
    Get dashboard data for vendor aging analytics
    Returns summary statistics for aging analysis
    """
    try:
        data = {
            "total_vendors": frappe.db.count("Vendor Aging Tracker"),
            "active_vendors": frappe.db.count("Vendor Aging Tracker", {"vendor_status": "Active"}),
            "inactive_vendors": frappe.db.count("Vendor Aging Tracker", {"vendor_status": "Inactive"}),
            "total_purchase_orders": frappe.db.sql("""
                SELECT SUM(total_purchase_orders) 
                FROM `tabVendor Aging Tracker`
            """)[0][0] or 0,
            "aging_categories": {}
        }
        
        # Get count by aging categories
        aging_statuses = ["New (0-30 days)", "Recent (31-90 days)", 
                         "Established (91-180 days)", "Long Term (180+ days)"]
        
        for status in aging_statuses:
            count = frappe.db.count("Vendor Aging Tracker", {"vendor_aging_status": status})
            data["aging_categories"][status] = count
        
        return data
        
    except Exception as e:
        frappe.log_error(f"Error getting aging dashboard data: {str(e)}", 
                        "Vendor Aging Dashboard Error")
        return {}