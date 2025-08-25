# earth_invoice.py - Fixed controller with simplified permissions

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now
import json

class EarthInvoice(Document):

    def validate(self):
        self.update_upload_status()
    
    def update_upload_status(self):
        child_tables = {
            'confirmation_voucher': 'confirmation_voucher',  
            'invoice_attachment': 'invoice_attachment',   
            'debit_note_attachment': 'debit_note_attachment' 
        }
        
        uploaded_count = 0
        
        for table_field, attachment_field in child_tables.items():
            child_table = self.get(table_field) or []
            
            has_attachment = any(
                row.get(attachment_field) for row in child_table
            )
            
            if has_attachment:
                uploaded_count += 1
        
        if uploaded_count == 3:
            self.doc_upload_status = "Fully Uploaded"
        elif uploaded_count > 0:
            self.doc_upload_status = "Partially Uploaded"
        else:
            self.doc_upload_status = "Not Uploaded"
    
    def before_save(self):
        self.validate_workflow_state()
        
        
    
    def validate_workflow_state(self):
        if not self.workflow_state:
            self.workflow_state = "Pending"
    
  
def get_permission_query_conditions(user):
    """Simplified permission function for list filtering"""
    if not user:
        user = frappe.session.user
    
    user_roles = frappe.get_roles(user)
    
    # System Manager sees all
    if 'System Manager' in user_roles:
        return ""
    
    conditions = []
    
    # Earth role - can see all pending and rejected invoices (no owner restriction)
    if 'Earth' in user_roles:
        conditions.append("(`tabEarth Invoice`.workflow_state IN ('Pending', 'Rejected'))")
    
    # Earth Upload role - can see pending invoices  
    earth_upload_conditions = get_earth_upload_type_conditions(user_roles)
    if earth_upload_conditions:
        conditions.append(f"(`tabEarth Invoice`.workflow_state IN ('Pending', 'Rejected') AND ({earth_upload_conditions}))")

    if 'Nirav' in user_roles:
        conditions.append("(`tabEarth Invoice`.workflow_state IN ('Pending', 'Approve By Nirav Sir', 'Rejected'))")
    
    # Travel Desk role - can see pending, approved by travel desk, and rejected
    if 'Travel Desk' in user_roles:
        conditions.append("(`tabEarth Invoice`.workflow_state IN ('Approve By Nirav Sir', 'Approve By Travel Desk', 'Rejected'))")

    
    
    # Tyab role - can see approved by travel desk, approved by tyab sir, and rejected
    if 'Tyab' in user_roles:
        conditions.append("(`tabEarth Invoice`.workflow_state IN ('Approve By Travel Desk', 'Approve By Tyab Sir', 'Rejected'))")
    
    # Panjikar role - can see approved by tyab sir, approved by panjikar sir, and rejected
    if 'Panjikar' in user_roles:
        conditions.append("(`tabEarth Invoice`.workflow_state IN ('Approve By Tyab Sir', 'Approve By Panjikar Sir', 'Rejected'))")
    
    # Accounts Team - with company filtering, including rejected
    if 'Accounts Team' in user_roles:
        user_companies = get_user_assigned_companies(user)
        if user_companies:
            company_list = "', '".join(user_companies)
            conditions.append(f"(`tabEarth Invoice`.workflow_state IN ('Approve By Panjikar Sir', 'Approved', 'Rejected') AND `tabEarth Invoice`.billing_company IN ('{company_list}'))")
        else:
            # If no companies assigned, still allow to see but with no company match
            conditions.append("(`tabEarth Invoice`.workflow_state IN ('Approve By Panjikar Sir', 'Approved', 'Rejected'))")
    
    if conditions:
        return " OR ".join(conditions)
    else:
        return "`tabEarth Invoice`.name = 'NO_ACCESS'"

def has_permission(doc, user=None, permission_type=None):
    
    if not user:
        user = frappe.session.user
    
    user_roles = frappe.get_roles(user)
    
    # System Manager has full access
    if 'System Manager' in user_roles:
        return True
    
    state = doc.workflow_state or "Pending"
    
    # Earth role - can read/edit pending and rejected invoices (all, not just own)
    if 'Earth' in user_roles:
        if state in ['Pending', 'Rejected']:
            # Don't allow editing auto-rejected invoices
            if state == 'Rejected' and getattr(doc, 'is_auto_rejected', False):
                return permission_type == 'read'  # Read only for auto-rejected
            return True
        return False  # No access to other states
    
    # Earth Upload role - can read/edit pending and view rejected
   
   
    if has_earth_upload_role_for_type(user_roles, doc.type):
        if state == 'Rejected':
            return permission_type == 'read'
        return state == 'Pending'

    if 'Nirav' in user_roles:
        if state == 'Rejected':
            return permission_type == 'read'  # Read only for rejected
        return state in ['Pending', 'Approve By Nirav Sir']
    
    # Travel Desk role - can access pending, approve by travel desk, and view rejected
    if 'Travel Desk' in user_roles:
        if state == 'Rejected':
            return permission_type == 'read'  # Read only for rejected
        return state in ['Approve By Nirav Sir', 'Approve By Travel Desk']
    
    # Tyab role - can access approve by travel desk, approve by tyab sir, and view rejected
    if 'Tyab' in user_roles:
        if state == 'Rejected':
            return permission_type == 'read'  # Read only for rejected
        return state in ['Approve By Travel Desk', 'Approve By Tyab Sir','Pending']
    
    # Panjikar role - can access approve by tyab sir, approve by panjikar sir, and view rejected
    if 'Panjikar' in user_roles:
        if state == 'Rejected':
            return permission_type == 'read'  # Read only for rejected
        return state in ['Approve By Tyab Sir', 'Approve By Panjikar Sir', 'Pending']
    
    # Accounts Team with company check
    if state in ['Approve By Panjikar Sir', 'Approved', 'Rejected', 'Pending']:
        return user_has_company_access(user, doc.billing_company)
    
    return False

# Define mapping at module level
INVOICE_TYPE_ROLE_MAPPING = {
    'Hotel Booking': 'Earth Upload Hotel',
    'Bus Booking': 'Earth Upload Bus',
    'Domestic Air Booking': 'Earth Upload Domestic Air',
    'International Air Booking': 'Earth Upload International Air',
    'Railway Booking': 'Earth Upload Railway',
}

def has_earth_upload_role_for_type(user_roles, invoice_type_value):
    """Check if user has Earth Upload role for specific invoice type"""
    if not invoice_type_value:
        return False
    
    # Generic Earth Upload role has access to all types
    if 'Earth Upload' in user_roles:
        return True
    
    required_role = INVOICE_TYPE_ROLE_MAPPING.get(invoice_type_value)
    if required_role:
        return required_role in user_roles
    
    return False

def get_earth_upload_type_conditions(user_roles):
    """Generate SQL conditions for Earth Upload type-specific access"""
    type_conditions = []
    
    # Generic Earth Upload role sees all types
    if 'Earth Upload' in user_roles:
        return "1=1"  # No type restriction
    
    # Check each role-type pair
    for invoice_type_value, role in INVOICE_TYPE_ROLE_MAPPING.items():
        if role in user_roles:
            type_conditions.append(f"`tabEarth Invoice`.type = '{invoice_type_value}'")
    
    return " OR ".join(type_conditions) if type_conditions else "1=0"

@frappe.whitelist()
def get_user_assigned_companies(user):
    
    try:
        employee_name = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee_name:
            return []
        
        
        employee_doc = frappe.get_doc("Employee", employee_name)
        
        
        
        companies_child_table = employee_doc.get("company") or []
        
        
        if not companies_child_table:
        
            return []
        
        company_names = []
        
       
        for company_row in companies_child_table:
           
            
            
            company_link = company_row.get("company_name")  
            
            
            if company_link:
                try:
                  
                    company_doc = frappe.get_doc("Company Master", company_link)
                    company_display_name = company_doc.company_name 
                    company_names.append(company_display_name)
                   
                except Exception as company_error:
                   
                    company_names.append(company_link)
        
        print("Final company names:", company_names)
        return company_names
        
    except Exception as e:
        
        frappe.log_error(f"Error getting user companies: {str(e)}")
        return []

@frappe.whitelist()
def user_has_company_access(user, company):
    
    
    if not company:
        return True 
    
    user_companies = get_user_assigned_companies(user)
    if not user_companies:
        return True  

    print(company in user_companies," company in user_companies ")
    
    return company in user_companies

# Workflow Action Functions
@frappe.whitelist()
def approve_invoice(doc_name, next_state):
    
    try:
        doc = frappe.get_doc("Earth Invoice", doc_name)
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)
        

        current_state = doc.workflow_state
        
        
        approval_matrix = {
            'Pending': ['Nirav'], 
            'Approve By Nirav Sir': ['Travel Desk'],  
            'Approve By Travel Desk': ['Tyab'],
            'Approve By Tyab Sir': ['Panjikar'],
            'Approve By Panjikar Sir': ['Accounts Team']
        }
        
        allowed_roles = approval_matrix.get(current_state, [])
        if not any(role in user_roles for role in allowed_roles):
            frappe.throw(_("You are not authorized to approve this invoice at current state"))
        
        # Company access validation for accounts team
        if 'Accounts Team' in user_roles and current_state == 'Approve By Panjikar Sir':
            if not user_has_company_access(current_user, doc.billing_company):
                frappe.throw(_(f"No access to approve invoices for {doc.billing_company}"))
        
        # Update state based on current state
        state_transitions = {
            'Pending': 'Approve By Nirav Sir',  
            'Approve By Nirav Sir': 'Approve By Travel Desk',
            'Approve By Travel Desk': 'Approve By Tyab Sir',
            'Approve By Tyab Sir': 'Approve By Panjikar Sir',
            'Approve By Panjikar Sir': 'Approved'
        }
        
        doc.workflow_state = state_transitions.get(current_state, next_state)
        if doc.workflow_state == 'Approved':
            doc.docstatus = 1
        
        # Save the document
        doc.save()
        
        # Add audit comment
        add_workflow_comment(doc_name, f"Approved by {current_user}", "Workflow")
        
        return {"status": "success", "message": "Invoice approved successfully"}
        
    except Exception as e:
        frappe.log_error(f"Approval error: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def reject_invoice(doc_name, rejection_remark,next_state="Pending"):
    """Reject invoice with group rejection logic"""
    try:
        doc = frappe.get_doc("Earth Invoice", doc_name)
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)
        
      
        current_state = doc.workflow_state
        
        # Define who can reject from which state
        rejection_matrix = {
            'Pending': ['Nirav'], 
            'Approve By Nirav Sir': ['Travel Desk'],
            'Approve By Travel Desk': ['Tyab'],
            'Approve By Tyab Sir': ['Panjikar'],
            'Approve By Panjikar Sir': ['Accounts Team']
        }
        
        allowed_roles = rejection_matrix.get(current_state, [])
       
        if not any(role in user_roles for role in allowed_roles):
            frappe.throw(_("You are not authorized to reject this invoice at current state"))
        
       
        if 'Accounts Team' in user_roles and current_state == 'Approve By Panjikar Sir':
            if not user_has_company_access(current_user, doc.billing_company):
                frappe.throw(_(f"No access to reject invoices for {doc.billing_company}"))

        state_transitions = {
            'Pending': 'Pending',  
            'Approve By Nirav Sir': 'Pending',
            'Approve By Travel Desk': 'Pending',
            'Approve By Tyab Sir': 'Pending',
            'Approve By Panjikar Sir': 'Pending'
        }
        
        doc.workflow_state = state_transitions.get(current_state, next_state)
        
        # Update state and remark
        doc.workflow_state = "Pending"  # Always go to rejected state
        doc.rejection_remark = rejection_remark
        doc.rejected_by = current_user
        doc.rejection_date = today()
        doc.save()
        
        # Add audit comment
        add_workflow_comment(doc_name, f"Rejected by {current_user}: {rejection_remark}", "Workflow")
        
        return {"status": "success", "message": "Invoice rejected successfully"}
        
    except Exception as e:
        frappe.log_error(f"Rejection error: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def handle_group_rejection(rejecting_doc_name, booking_date, current_workflow_state, rejection_remark, rejected_by):
    try:
        if not booking_date or not current_workflow_state:
            return {"status": "error", "message": "Missing required parameters"}
        
        # Find all invoices from the same date with the same workflow state
        filters = {
            "booking_date": booking_date,
            "workflow_state": current_workflow_state,  
            "name": ["!=", rejecting_doc_name],
            "docstatus": ["!=", 2]
        }
        
        same_date_same_state_invoices = frappe.get_all(
            "Earth Invoice",
            filters=filters,
            fields=["name", "workflow_state"]
        )
        
        affected_invoices = 0
        affected_names = []
        
    
        for invoice in same_date_same_state_invoices:
            try:
                invoice_doc = frappe.get_doc("Earth Invoice", invoice.name)
                
               
                # invoice_doc._skip_rejection_flow = True
                
                # Set to Pending state with auto-rejection flags
                invoice_doc.workflow_state = "Pending"
                invoice_doc.rejection_remark = f"Auto-rejected due to {rejecting_doc_name}: {rejection_remark}"
                invoice_doc.is_auto_rejected = 1
                invoice_doc.rejected_by = rejected_by
                invoice_doc.rejection_date = today()
                
                # Save with ignore permissions
                invoice_doc.flags.ignore_permissions = True
                invoice_doc.save()
                
                affected_invoices += 1
                affected_names.append(invoice.name)
                
                # Add audit comment for auto-rejected invoice
                add_workflow_comment(
                    invoice.name, 
                    f"Auto-rejected due to rejection of {rejecting_doc_name} by {rejected_by}: {rejection_remark}", 
                    "Workflow"
                )
                
            except Exception as e:
                frappe.log_error(f"Error auto-rejecting invoice {invoice.name}: {str(e)}")
        
        return {
            "status": "success", 
            "message": f"Group rejection completed. {affected_invoices} invoices auto-rejected.",
            "affected_invoices": affected_invoices,
            "affected_invoice_names": affected_names
        }
        
    except Exception as e:
        frappe.log_error(f"Group rejection error: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def send_group_rejection_email(original_invoice, booking_date, billing_company, rejection_remark, affected_invoices, rejected_by):
    """Send group rejection notification email"""
    try:
        if not affected_invoices or len(affected_invoices) == 0:
            return {"status": "success", "message": "No group notification needed"}
        
        recipients = get_notification_recipients()
        if not recipients:
            return {"status": "error", "message": "No recipients found for notification"}
        
        total_affected = len(affected_invoices) + 1  
        subject = f"Group Rejection Alert - {total_affected} invoices affected"
        
        Build email content
        invoice_list = f"<li>{original_invoice} (Original - Can be edited)</li>"
        for inv_name in affected_invoices:
            invoice_list += f"<li>{inv_name} (Auto-rejected - Read only)</li>"
        
        message = f"""
        <h3 style="color: #d73527;">Group Invoice Rejection</h3>
        <p><strong>Date:</strong> {booking_date}</p>
        <p><strong>Company:</strong> {billing_company}</p>
        <p><strong>Rejected By:</strong> {rejected_by}</p>
        <p><strong>Reason:</strong> {rejection_remark}</p>
        
        <h4>Affected Invoice:</h4>
        <ul>{invoice_list}</ul>
        
        <div style="background: #fff3cd; padding: 10px; margin: 10px 0;">
            <strong>Action Required:</strong>
            <ol>
                <li>Only the original rejected invoice can be edited</li>
                <li>Fix the issue and resubmit for approval</li>
                
            </ol>
        </div>
        """
        
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message
        )
        
        return {"status": "success", "message": "Group rejection notification sent"}
        
    except Exception as e:
        frappe.log_error(f"Error sending group rejection email: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_notification_recipients():
    """Get email recipients for group rejection notifications"""
    try:
        recipients = []
        roles_to_notify = ["Earth"]
        
        for role in roles_to_notify:
            role_users = frappe.get_all(
                "Has Role",
                filters={"role": role},
                fields=["parent"]
            )
            
            for user in role_users:
                email = frappe.db.get_value("User", user.parent, "email")
                if email and email not in recipients:
                    recipients.append(email)
        
        return recipients
        
    except Exception as e:
        frappe.log_error(f"Error getting notification recipients: {str(e)}")
        return []

@frappe.whitelist()
def resubmit_invoice(doc_name):
    """Resubmit rejected invoice"""
    try:
        doc = frappe.get_doc("Earth Invoice", doc_name)
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)
        
        # Only Earth users can resubmit
        if 'Earth' not in user_roles:
            frappe.throw(_("Only Earth users can resubmit invoices"))
        
        if doc.workflow_state != "Rejected":
            frappe.throw(_("Only rejected invoices can be resubmitted"))
        
        # Cannot resubmit auto-rejected invoices
        if getattr(doc, 'is_auto_rejected', False):
            frappe.throw(_("Auto-rejected invoices cannot be resubmitted"))
        
        # Reset to pending
        doc.workflow_state = "Pending"
        doc.rejection_remark = ""
        doc.rejected_by = ""
        doc.rejection_date = None
        doc.save()
        
        # Add audit comment
        add_workflow_comment(doc_name, f"Resubmitted by {current_user}", "Workflow")
        
        return {"status": "success", "message": "Invoice resubmitted successfully"}
        
    except Exception as e:
        frappe.log_error(f"Resubmit error: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_user_workflow_info():
    """Get current user's workflow permissions and assigned companies"""
    try:
        user = frappe.session.user
        roles = frappe.get_roles(user)
        companies = get_user_assigned_companies(user) if 'Accounts Team' in roles else []
        
        return {
            "user": user,
            "roles": roles,
            "companies": companies,
            "can_approve_accounts": 'Accounts Team' in roles
        }
        
    except Exception as e:
        return {"error": str(e)}

def add_workflow_comment(doc_name, content, comment_type="Comment"):
    """Add workflow comment for audit trail"""
    try:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": comment_type,
            "reference_doctype": "Earth Invoice",
            "reference_name": doc_name,
            "content": content,
            "comment_email": frappe.session.user,
            "comment_by": frappe.session.user_fullname or frappe.session.user
        }).insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Error adding comment: {str(e)}")

# Utility Functions
@frappe.whitelist()
def get_workflow_stats():
    """Get workflow statistics for dashboard"""
    try:
        user_roles = frappe.get_roles()
        stats = {}
        
        if 'Earth' in user_roles:
            stats['my_pending'] = frappe.db.count("Earth Invoice", {
                "workflow_state": "Pending"
            })
            stats['my_rejected'] = frappe.db.count("Earth Invoice", {
                "workflow_state": "Rejected",
                "is_auto_rejected": 0
            })
        
        if 'Accounts Team' in user_roles:
            user_companies = get_user_assigned_companies(frappe.session.user)
            if user_companies:
                stats['accounts_pending'] = frappe.db.count("Earth Invoice", {
                    "workflow_state": "Approve By Panjikar Sir",
                    "billing_company": ["in", user_companies]
                })
            else:
                stats['accounts_pending'] = frappe.db.count("Earth Invoice", {
                    "workflow_state": "Approve By Panjikar Sir"
                })
        
        return stats
        
    except Exception as e:
        frappe.log_error(f"Error getting workflow stats: {str(e)}")
        return {}