# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime


class SupplierQMSAssessmentForm(Document):
	def on_update(self):

		# set_unique_data(self, method=None)
		# set_qms_form_link(self, method=None)
		set_qms_form_link_unique_data(self, method=None)
		update_multiselect_child_fields(self, method=None)

		set_unique_data(self, method=None)
		set_qms_form_link(self, method=None)
		send_mail_qa_team(self, method=None)
		





@frappe.whitelist(allow_guest=True)
def set_qms_form_link(doc, method=None):

	if doc.vendor_onboarding != None:
		ven_onb = frappe.get_doc("Vendor Onboarding", doc.vendor_onboarding)
		ven_onb.qms_form_link = doc.unique_name
		ven_onb.qms_form_filled = 1
		ven_onb.save()
		frappe.db.commit()



def set_unique_data(doc, method=None):
	if doc.unique_name == None or doc.unique_name == "":
		now = datetime.now()
		year_month_prefix = f"QMS{now.strftime('%y')}{now.strftime('%m')}"
		
		existing_max = frappe.db.sql(
			"""
			SELECT MAX(CAST(SUBSTRING(unique_name, 8) AS UNSIGNED))
			FROM `tabSupplier QMS Assessment Form`
			WHERE unique_name LIKE %s
			""",
			(year_month_prefix + "%",),
			as_list=True
		)
		
		max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
		new_count = max_count + 1

		unique_name = f"{year_month_prefix}{str(new_count).zfill(5)}"

		frappe.db.set_value("Supplier QMS Assessment Form", doc.name, "unique_name", unique_name)





@frappe.whitelist(allow_guest=True)
def set_qms_form_link_unique_data(doc, method=None):
	# unique_name = None
	if doc.unique_name == None or doc.unique_name == "":
		now = datetime.now()
		year_month_prefix = f"QMS{now.strftime('%y')}{now.strftime('%m')}"
		
		existing_max = frappe.db.sql(
			"""
			SELECT MAX(CAST(SUBSTRING(unique_name, 8) AS UNSIGNED))
			FROM `tabSupplier QMS Assessment Form`
			WHERE unique_name LIKE %s
			""",
			(year_month_prefix + "%",),
			as_list=True
		)
		
		max_count = existing_max[0][0] if existing_max and existing_max[0] and existing_max[0][0] else 0
		new_count = max_count + 1
		unique_name = f"{year_month_prefix}{str(new_count).zfill(5)}"

		frappe.db.set_value("Supplier QMS Assessment Form", doc.name, "unique_name", unique_name)
		if doc.vendor_onboarding != None:
			ven_onb = frappe.get_doc("Vendor Onboarding", doc.vendor_onboarding)
			frappe.db.set_value("Vendor Onboarding", ven_onb.name, "qms_form_link", unique_name)
			frappe.db.set_value("Vendor Onboarding", ven_onb.name, "qms_form_filled", 1)
			# ven_onb.qms_form_link = unique_name
			# ven_onb.qms_form_filled = 1
			# ven_onb.save()
			frappe.db.commit()

	

		doc.unique_name = f"{year_month_prefix}{str(new_count).zfill(5)}"


def send_mail_qa_team(doc, method=None):
	try:
		qa_users = frappe.get_all("Has Role", 
			filters={"role": "QA Team"},
			fields=["parent as user"])

		emails = []
		for u in qa_users:
			user_email = frappe.db.get_value("User", u.user, "email")
			if user_email:
				emails.append(user_email)
		
		if not emails:
			frappe.log_error("No QA users with email found", "send_mail_qa_team")
			return

		http_server = frappe.conf.get("frontend_http")
		
		form_link = f"{http_server}/qms-webform/{doc.name}"

		subject = "Vendor QMS Form Submitted"
		message = f"""
		Dear QA Team,<br><br>
		The vendor has submitted the Supplier QMS Assessment Form.<br>
		Please review it using the link below:<br><br>
		<a href="{form_link}">{form_link}</a><br><br>
		Regards,<br>
		VMS Team
		"""

		# Send the email
		if not doc.mail_sent_to_qa_team:
			frappe.sendmail(
				recipients=emails,
				subject=subject,
				message=message,
				now=True
			)
			frappe.db.set_value("Supplier QMS Assessment Form", doc.name, "mail_sent_to_qa_team", 1)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in send_mail_qa_team")




import json
import frappe

def update_multiselect_child_fields(self, method=None):
    """
    Update Table MultiSelect child fields from multiselect_data_json
    """
    if not self.multiselect_data_json:
        return
        
    try:
        # Parse JSON
        json_data = json.loads(self.multiselect_data_json)
        data = json_data.get("data", {})
        
        field_mappings = {
            "quality_control_system": ("QMS Quality Control", "qms_quality_control"),
            "details_of_batch_records": ("QMS Batch Record Table", "qms_batch_record"),
            "have_documentsprocedure": ("QMS Procedure Doc", "qms_procedure_doc"),
            "if_yes_for_prior_notification": ("QMS Prior Notification Table", "qms_prior_notification")
        }
        
        for json_field, (child_doctype, child_field) in field_mappings.items():
            if json_field in data and data[json_field]:
                field_data = data[json_field]
                
                # Handle array of objects format
                if isinstance(field_data, list):
                    values = []
                    for item in field_data:
                        if isinstance(item, dict):
                            # Use 'value' field if available, otherwise 'name'
                            value = item.get('value') or item.get('name')
                            if value:
                                values.append(str(value).strip())
                        elif isinstance(item, str):
                            # Handle case where it's just a string
                            values.append(str(item).strip())
                    
                    # Filter out empty values
                    values = [v for v in values if v]
                    
                elif isinstance(field_data, str):
                    # Handle legacy comma-separated string format
                    values = [v.strip() for v in field_data.split(",") if v.strip()]
                else:
                    continue
                
                if values:
                    # Clear existing records using db operations
                    frappe.db.delete(child_doctype, {
                        "parent": self.name,
                        "parenttype": self.doctype
                    })
                    
                    # Create new records
                    for idx, value in enumerate(values, 1):
                        doc = frappe.get_doc({
                            "doctype": child_doctype,
                            "parent": self.name,
                            "parenttype": self.doctype,
                            "parentfield": json_field,
                            "idx": idx,
                            child_field: value
                        })
                        doc.insert(ignore_permissions=True)
                        
                        # Use db.set_value to ensure the value is set
                        frappe.db.set_value(child_doctype, doc.name, child_field, value)
                    
                    frappe.logger().info(f"Updated {json_field} with {len(values)} records")
        
        # Commit and reload
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error in multiselect update: {str(e)}", "QMS Multiselect Update Error")
        frappe.db.rollback()
        raise

def update_qms_multiselect_db_only(docname, json_data_string):
    """
    Standalone function to update multiselect fields using only database operations
    """
    try:
        # Parse JSON
        json_data = json.loads(json_data_string)
        data = json_data.get("data", {})
        
        field_mappings = {
            "quality_control_system": ("QMS Quality Control", "qms_quality_control"),
            "details_of_batch_records": ("QMS Batch Record Table", "qms_batch_record"),
            "have_documentsprocedure": ("QMS Procedure Doc", "qms_procedure_doc"),
            "if_yes_for_prior_notification": ("QMS Prior Notification Table", "qms_prior_notification")
        }
        
        parent_doctype = "Supplier QMS Assessment Form"
        
        for json_field, (child_doctype, child_field) in field_mappings.items():
            # Delete existing records
            frappe.db.sql("""
                DELETE FROM `tab{child_doctype}` 
                WHERE parent = %s AND parenttype = %s AND parentfield = %s
            """.format(child_doctype=child_doctype), (docname, parent_doctype, json_field))
            
            # Insert new records if data exists
            if json_field in data and data[json_field]:
                field_value = str(data[json_field]).strip()
                
                if field_value:
                    values = [v.strip() for v in field_value.split(",") if v.strip()]
                    
                    for idx, value in enumerate(values, 1):
                        # Generate unique name
                        child_name = f"new-{child_doctype.lower().replace(' ', '-')}-{frappe.generate_hash(length=8)}"
                        
                        # Insert using db.set_value approach
                        frappe.db.sql("""
                            INSERT INTO `tab{child_doctype}` 
                            (name, parent, parenttype, parentfield, idx, {child_field}, 
                             creation, modified, owner, modified_by, docstatus)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                        """.format(child_doctype=child_doctype, child_field=child_field), 
                        (child_name, docname, parent_doctype, json_field, idx, value,
                         frappe.utils.now(), frappe.utils.now(), frappe.session.user, frappe.session.user))
        
        # Commit changes
        frappe.db.commit()
        
        return {"status": "success", "message": "Multiselect fields updated using db operations"}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error in db-only update: {str(e)}", "QMS DB Only Error")
        return {"status": "error", "message": str(e)}

