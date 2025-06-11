import frappe
from frappe import _





@frappe.whitelist(allow_guest = True)
def collect_vendor_code_data(vendor_ref_no):
		"""Collect all vendor code data from multiple company data"""
		vendor_doc = frappe.get_doc("Vendor Master", vendor_ref_no)

		all_vendor_data = []
		
		
		try:
			# Check if multiple_company_data exists and has data
			if not hasattr(vendor_doc, 'multiple_company_data') or not vendor_doc.multiple_company_data:
				frappe.logger().info("No multiple_company_data found in vendor document")
				return all_vendor_data
			
			# Iterate through multiple_company_data table
			for company_data_row in vendor_doc.multiple_company_data:
				if hasattr(company_data_row, 'company_vendor_code') and company_data_row.company_vendor_code:
					try:
						# Fetch Company Vendor Code document
						company_vendor_code_doc = frappe.get_doc("Company Vendor Code", company_data_row.company_vendor_code)
						
						# Check if vendor_code table exists and has data
						if hasattr(company_vendor_code_doc, 'vendor_code') and company_vendor_code_doc.vendor_code:
							# Iterate through vendor_code table in Company Vendor Code doc
							for vendor_code_row in company_vendor_code_doc.vendor_code:
								vendor_info = {
									'company_name': getattr(company_vendor_code_doc, 'company_name', ''),
									'state': getattr(vendor_code_row, 'state', ''),
									'gst_no': getattr(vendor_code_row, 'gst_no', ''),
									'vendor_code': getattr(vendor_code_row, 'vendor_code', '')
								}
								all_vendor_data.append(vendor_info)
						else:
							frappe.logger().info(f"No vendor_code data found in Company Vendor Code {company_data_row.company_vendor_code}")
							
					except Exception as e:
						frappe.logger().error(f"Error fetching Company Vendor Code {company_data_row.company_vendor_code}: {str(e)}")
						continue
						
		except Exception as e:
			frappe.logger().error(f"Error in collect_vendor_code_data: {str(e)}")
		
		print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22",all_vendor_data)		
		
		return all_vendor_data