import frappe
import json
from frappe.model.document import Document

class Quotation(Document):
	
	def on_update(self):
		set_quotation_id_in_rfq(self)
		if self.rfq_number:
			self.update_quotation_rankings()
	
	def update_quotation_rankings(self):
		try:
			quotations = frappe.get_all(
				"Quotation",
				filters={
					"rfq_number": self.rfq_number,
				},
				fields=["name", "quote_amount"]
			)
			
			if not quotations:
				return
			
			valid_quotations = []
			invalid_quotations = []
			
			for q in quotations:
				try:
					if q.quote_amount and str(q.quote_amount).strip():
						quote_amount_float = float(str(q.quote_amount).replace(',', ''))
						if quote_amount_float > 0:
							q.quote_amount_float = quote_amount_float
							valid_quotations.append(q)
						else:
							invalid_quotations.append(q)
					else:
						invalid_quotations.append(q)
				except (ValueError, TypeError):
					invalid_quotations.append(q)
			
			if not valid_quotations:
				return
			
			valid_quotations.sort(key=lambda x: x.quote_amount_float)
			
			for index, quotation in enumerate(valid_quotations):
				rank = index + 1
				
				frappe.db.set_value("Quotation", quotation.name, "rank", str(rank))
				
				frappe.logger().info(f"Updated Quotation {quotation.name} rank to {rank} for RFQ {self.rfq_number}")
			
			for quotation in invalid_quotations:
				frappe.db.set_value("Quotation", quotation.name, "rank", "")
			
			frappe.db.commit()
			
		except Exception as e:
			frappe.log_error(f"Error updating quotation rankings for RFQ {self.rfq_number}: {str(e)}", "Quotation Ranking Error")
			frappe.throw(f"Failed to update quotation rankings: {str(e)}")
	

# set quotation id in rfq for those vendor who fill the quotation already
def set_quotation_id_in_rfq(doc):
	if not doc.rfq_number:
		return

	rfq = frappe.get_doc("Request For Quotation", doc.rfq_number)

	# Onboarded vendors
	if doc.ref_no and rfq.vendor_details:
		for row in rfq.vendor_details:
			if row.ref_no == doc.ref_no and not row.quotation:
				frappe.db.set_value("Vendor Details", row.name, "quotation", doc.name)

	# Non-onboarded vendors
	if doc.office_email_primary and rfq.non_onboarded_vendor_details:
		for row in rfq.non_onboarded_vendor_details:
			if row.office_email_primary == doc.office_email_primary and not row.quotation:
				frappe.db.set_value("Non Onboarded Vendor Details", row.name, "quotation", doc.name)

