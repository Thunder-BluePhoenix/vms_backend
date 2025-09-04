
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now
import json
from vms.utils.custom_send_mail import custom_sendmail

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
        if hasattr(self, '_doc_before_save'):
            self._old_workflow_state = self._doc_before_save.workflow_state
        else:
            self._old_workflow_state = self.get_doc_before_save().workflow_state if not self.is_new() else None


    def on_update(self):

        """Handle workflow state changes and group actions"""
        # Skip if this is a group action batch update to prevent recursion
        if getattr(self, '_skip_group_action', False):
            return
            
        # Skip if called from our own group action functions
        if hasattr(frappe.local, 'group_action_in_progress'):
            return
            
        # Check if workflow state actually changed
        old_state = getattr(self, '_old_workflow_state', None)
        current_state = self.workflow_state
        
        if old_state == current_state:
            return  # No state change, skip group actions
            
        # Handle group actions based on state transition
        self._handle_workflow_state_change(old_state, current_state)


    def _handle_workflow_state_change(self, old_state, new_state):
    
        try:
            frappe.local.group_action_in_progress = True
            
            if self._is_approval_transition(old_state, new_state):
                self._trigger_group_approval(old_state, new_state)
            elif self._is_rejection_transition(old_state, new_state):
                self._trigger_group_rejection(old_state)
                
        finally:
            if hasattr(frappe.local, 'group_action_in_progress'):
                delattr(frappe.local, 'group_action_in_progress')
        
    def _is_approval_transition(self, old_state, new_state):
        """Check if the state change represents an approval"""
        approval_transitions = {
            'Pending': 'Approve By Nirav Sir',
            'Approve By Nirav Sir': 'Approve By Travel Desk',
            'Approve By Travel Desk': 'Approve By Tyab Sir',
            'Approve By Tyab Sir': 'Approve By Panjikar Sir',
            'Approve By Panjikar Sir': 'Approved'
        }
        return approval_transitions.get(old_state) == new_state
    
    def _is_rejection_transition(self, old_state, new_state):
        """Check if the state change represents a rejection"""
        # Any transition to Rejected state or back to Pending from an approval state
        if new_state == 'Rejected':
            return True
        if new_state == 'Pending' and old_state in [
            'Approve By Nirav Sir', 'Approve By Travel Desk', 
            'Approve By Tyab Sir', 'Approve By Panjikar Sir'
        ]:
            return True
        return False
    
    def _trigger_group_approval(self, old_state, new_state):
       
        try:
            result = handle_group_approval_internal(
                approving_doc_name=self.name,
                inv_date=self.inv_date,
                current_workflow_state=old_state,
                approved_by=frappe.session.user,
                next_state=new_state
            )
            
            if result.get('status') == 'success' and result.get('affected_invoices', 0) > 0:
               
                send_group_approval_email_internal(
                    original_invoice=self.name,
                    inv_date=self.inv_date,
                    billing_company=self.billing_company or 'N/A',
                    affected_invoices=result.get('affected_invoice_names', []),
                    approved_by=frappe.session.user,
                    next_state=new_state
                )
                
        except Exception as e:
            frappe.log_error(f"Error in group approval trigger: {str(e)}")
    
    def _trigger_group_rejection(self, old_state):
        
        try:
            
            rejection_remark = getattr(self, 'rejection_remark', 'Bulk rejection from list view')
            
            result = handle_group_rejection_internal(
                rejecting_doc_name=self.name,
                inv_date=self.inv_date,
                current_workflow_state=old_state,
                rejection_remark=rejection_remark,
                rejected_by=frappe.session.user
            )
            
            if result.get('status') == 'success' and result.get('affected_invoices', 0) > 0:
                
                send_group_rejection_email_internal(
                    original_invoice=self.name,
                    inv_date=self.inv_date,
                    billing_company=self.billing_company or 'N/A',
                    rejection_remark=rejection_remark,
                    affected_invoices=result.get('affected_invoice_names', []),
                    rejected_by=frappe.session.user,
                    current_workflow_state=old_state
                )
                
        except Exception as e:
            frappe.log_error(f"Error in group rejection trigger: {str(e)}")
        
    
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
        return state in ['Approve By Nirav Sir', 'Approve By Travel Desk','Pending']
    
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
def handle_group_rejection(rejecting_doc_name, inv_date, current_workflow_state, rejection_remark, rejected_by):
    return handle_group_rejection_internal(
        rejecting_doc_name, inv_date, current_workflow_state, rejection_remark, rejected_by
    )
@frappe.whitelist()
def handle_group_approval(approving_doc_name, inv_date, current_workflow_state, approved_by, next_state):
    return handle_group_approval_internal(
        approving_doc_name, inv_date, current_workflow_state, approved_by, next_state
    )

def handle_group_approval_internal(approving_doc_name, inv_date, current_workflow_state, approved_by, next_state):
    
    try:
        if not inv_date or not current_workflow_state:
            return {"status": "error", "message": "Missing required parameters"}
        
        # Set flag to prevent triggering on_update during batch operations
        frappe.local.group_action_in_progress = True
        
        # Find all invoices from the same date with the same workflow state
        filters = {
            "inv_date": inv_date,
            "workflow_state": current_workflow_state,  
            "name": ["!=", approving_doc_name],
            "docstatus": ["!=", 2]
        }
        
        same_date_same_state_invoices = frappe.get_all(
            "Earth Invoice",
            filters=filters,
            fields=["name", "workflow_state", "billing_company"]
        )
        
        affected_invoices = 0
        affected_names = []
        
        user_roles = frappe.get_roles(approved_by)
        
        for invoice in same_date_same_state_invoices:
            try:
                # For Accounts Team, check company access
                if 'Accounts Team' in user_roles and current_workflow_state == 'Approve By Panjikar Sir':
                    if not user_has_company_access(approved_by, invoice.billing_company):
                        continue  # Skip this invoice if no company access
                
                invoice_doc = frappe.get_doc("Earth Invoice", invoice.name)
                
                # Set flag to skip group action on this document
                invoice_doc._skip_group_action = True
                
                # Update to next state
                invoice_doc.workflow_state = next_state
                if next_state == 'Approved':
                    invoice_doc.docstatus = 1
                
                # Save with ignore permissions
                invoice_doc.flags.ignore_permissions = True
                invoice_doc.save()
                
                affected_invoices += 1
                affected_names.append(invoice.name)
                
                # Add audit comment for auto-approved invoice
                add_workflow_comment(
                    invoice.name, 
                    f"Auto-approved due to approval of {approving_doc_name} by {approved_by}", 
                    "Workflow"
                )
                
            except Exception as e:
                frappe.log_error(f"Error auto-approving invoice {invoice.name}: {str(e)}")
        
        return {
            "status": "success", 
            "message": f"Group approval completed. {affected_invoices} invoices auto-approved.",
            "affected_invoices": affected_invoices,
            "affected_invoice_names": affected_names
        }
        
    except Exception as e:
        frappe.log_error(f"Group approval error: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        # Always clear the flag
        if hasattr(frappe.local, 'group_action_in_progress'):
            delattr(frappe.local, 'group_action_in_progress')

def handle_group_rejection_internal(rejecting_doc_name, inv_date, current_workflow_state, rejection_remark, rejected_by):
    try:
        if not inv_date or not current_workflow_state:
            return {"status": "error", "message": "Missing required parameters"}
        
        
        frappe.local.group_action_in_progress = True
        

        filters = {
            "inv_date": inv_date,
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
                
                # Set flag to skip group action on this document
                invoice_doc._skip_group_action = True
                
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
    finally:
        # Always clear the flag
        if hasattr(frappe.local, 'group_action_in_progress'):
            delattr(frappe.local, 'group_action_in_progress')


def send_group_approval_email_internal(original_invoice, inv_date, billing_company, affected_invoices, approved_by, next_state):
    
    try:
        if not affected_invoices or len(affected_invoices) == 0:
            return {"status": "success", "message": "No group notification needed"}

        recipients = get_next_approval_recipients(next_state)
        if not recipients:
            return {"status": "success", "message": "No next approval recipients found"}
        
        total_affected = len(affected_invoices) + 1  
        
        approval_step_names = {
            'Approve By Nirav Sir': 'Nirav Sir',
            'Approve By Travel Desk': 'Travel Desk',
            'Approve By Tyab Sir': 'Tyab Sir', 
            'Approve By Panjikar Sir': 'Panjikar Sir',
            'Approved': 'Final Approval'
        }
        
        step_name = approval_step_names.get(next_state, next_state)
        
        if next_state == 'Approved':
            subject = f"Group Final Approval - {total_affected} invoices approved for {inv_date}"
        else:
            subject = f"Group Approval - {total_affected} invoices ready for {step_name} approval"
        
        invoice_list = f"<li>{original_invoice} (Original)</li>"
        for inv_name in affected_invoices:
            invoice_list += f"<li>{inv_name} (Auto-approved)</li>"
        
        if next_state == 'Approved':
            message = f"""
            <h3 style="color: #28a745;">Group Invoice Final Approval</h3>
            <p><strong>Date:</strong> {inv_date}</p>
            <p><strong>Company:</strong> {billing_company}</p>
            <p><strong>Approved By:</strong> {approved_by}</p>
            
            <h4>Approved Invoices ({total_affected} total):</h4>
            <ul>{invoice_list}</ul>
            
            <div style="background: #d4edda; padding: 10px; margin: 10px 0;">
                <strong><i class="fa fa-check"></i> All invoices have been fully approved and are now finalized.</strong>
            </div>
            """
        else:
            message = f"""
            <h3 style="color: #007bff;">Group Invoice Approval - Ready for {step_name}</h3>
            <p><strong>Date:</strong> {inv_date}</p>
            <p><strong>Company:</strong> {billing_company}</p>
            <p><strong>Approved By:</strong> {approved_by}</p>
            
            <h4>Invoices Ready for Your Approval ({total_affected} total):</h4>
            <ul>{invoice_list}</ul>
            
            <div style="background: #cce5ff; padding: 10px; margin: 10px 0;">
                <strong>Action Required:</strong>
                <p>These invoices are now ready for your approval. Please review and approve/reject as appropriate.</p>
            </div>
            """
        
        frappe.custom_sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            now=True
        )
        
        return {"status": "success", "message": "Group approval notification sent"}
        
    except Exception as e:
        frappe.log_error(f"Error sending group approval email: {str(e)}")
        return {"status": "error", "message": str(e)}

def send_group_rejection_email_internal(original_invoice, inv_date, billing_company, rejection_remark, affected_invoices, rejected_by, current_workflow_state):
    
    try:
        if not affected_invoices or len(affected_invoices) == 0:
            return {"status": "success", "message": "No group notification needed"}
        
        recipients = get_previous_approval_recipients(current_workflow_state)
        if not recipients:
            return {"status": "success", "message": "No previous approval recipients found"}
        
        total_affected = len(affected_invoices) + 1  
        subject = f"Group Rejection Alert - {total_affected} invoices rejected for {inv_date}"
        
        invoice_list = f"<li>{original_invoice} (Original - Can be edited)</li>"
        for inv_name in affected_invoices:
            invoice_list += f"<li>{inv_name} (Auto-rejected - Read only)</li>"
        
        rejector_level = get_rejector_level_name(current_workflow_state)
        
        message = f"""
        <h3 style="color: #d73527;">Group Invoice Rejection Alert</h3>
        <p><strong>Date:</strong> {inv_date}</p>
        <p><strong>Company:</strong> {billing_company}</p>
        <p><strong>Rejected By:</strong> {rejected_by} ({rejector_level})</p>
        <p><strong>Reason:</strong> {rejection_remark}</p>
        
        <h4>Affected Invoices ({total_affected} total):</h4>
        <ul>{invoice_list}</ul>
        
        <div style="background: #fff3cd; padding: 10px; margin: 10px 0;">
            <strong>Action Required:</strong>
            <ol>
                <li>Only the original rejected invoice ({original_invoice}) can be edited</li>
                <li>Earth team should fix the issue and resubmit for approval</li>
                <li>Auto-rejected invoices will remain read-only until the original is resubmitted</li>
            </ol>
        </div>
        """
        
        frappe.custom_sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            now=True
        )
        
        return {"status": "success", "message": "Group rejection notification sent to previous approvers"}
        
    except Exception as e:
        frappe.log_error(f"Error sending group rejection email: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def send_group_rejection_email(original_invoice, inv_date, billing_company, rejection_remark, affected_invoices, rejected_by, current_workflow_state):
    try:
        if not affected_invoices or len(affected_invoices) == 0:
            return {"status": "success", "message": "No group notification needed"}

        if isinstance(affected_invoices, str):
            import json
            try:
                affected_invoices = json.loads(affected_invoices)
            except json.JSONDecodeError:
                affected_invoices = eval(affected_invoices)
        
        
        recipients = get_previous_approval_recipients(current_workflow_state)
        if not recipients:
            return {"status": "success", "message": "No previous approval recipients found"}
        
        total_affected = len(affected_invoices) + 1  
        subject = f"Group Rejection Alert - {total_affected} invoices rejected for {inv_date}"
        
        invoice_list = f"<li>{original_invoice} (Original - Can be edited)</li>"
        for inv_name in affected_invoices:
            invoice_list += f"<li>{inv_name} (Auto-rejected - Read only)</li>"
        
        # Get rejector level for display
        rejector_level = get_rejector_level_name(current_workflow_state)
        
        message = f"""
        <h3 style="color: #d73527;">Group Invoice Rejection Alert</h3>
        <p><strong>Date:</strong> {inv_date}</p>
        <p><strong>Company:</strong> {billing_company}</p>
        <p><strong>Rejected By:</strong> {rejected_by} ({rejector_level})</p>
        <p><strong>Reason:</strong> {rejection_remark}</p>
        
        <h4>Affected Invoices ({total_affected} total):</h4>
        <ul>{invoice_list}</ul>
        
        <div style="background: #fff3cd; padding: 10px; margin: 10px 0;">
            <strong>Action Required:</strong>
            <ol>
                <li>Only the original rejected invoice ({original_invoice}) can be edited</li>
                <li>Earth team should fix the issue and resubmit for approval</li>
                <li>Auto-rejected invoices will remain read-only until the original is resubmitted</li>
            </ol>
        </div>
        
        <div style="background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff;">
            <strong>Note:</strong> This notification was sent to all previous approval levels in the workflow chain.
        </div>
        """
        
        frappe.custom_sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            now=True
        )
        
        return {"status": "success", "message": "Group rejection notification sent to previous approvers"}
        
    except Exception as e:
        frappe.log_error(f"Error sending group rejection email: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def send_group_approval_email(original_invoice, inv_date, billing_company, affected_invoices, approved_by, next_state):
    """Send group approval notification email"""
    try:
        if not affected_invoices or len(affected_invoices) == 0:
            return {"status": "success", "message": "No group notification needed"}

        if isinstance(affected_invoices, str):
            import json
            try:
                affected_invoices = json.loads(affected_invoices)
            except json.JSONDecodeError:
                affected_invoices = eval(affected_invoices)
        
        # Get recipients - next approval step users
        recipients = get_next_approval_recipients(next_state)
        if not recipients:
            return {"status": "success", "message": "No next approval recipients found"}
        
        total_affected = len(affected_invoices) + 1  
        
        # Get approval step name for email
        approval_step_names = {
            'Approve By Nirav Sir': 'Nirav Sir',
            'Approve By Travel Desk': 'Travel Desk',
            'Approve By Tyab Sir': 'Tyab Sir', 
            'Approve By Panjikar Sir': 'Panjikar Sir',
            'Approved': 'Final Approval'
        }
        
        step_name = approval_step_names.get(next_state, next_state)
        
        if next_state == 'Approved':
            subject = f"Group Final Approval - {total_affected} invoices approved for {inv_date}"
        else:
            subject = f"Group Approval - {total_affected} invoices ready for {step_name} approval"
        
        invoice_list = f"<li>{original_invoice} (Original)</li>"
        for inv_name in affected_invoices:
            invoice_list += f"<li>{inv_name} (Auto-approved)</li>"
        
        if next_state == 'Approved':
            message = f"""
            <h3 style="color: #28a745;">Group Invoice Final Approval</h3>
            <p><strong>Date:</strong> {inv_date}</p>
            <p><strong>Company:</strong> {billing_company}</p>
            <p><strong>Approved By:</strong> {approved_by}</p>
            
            <h4>Approved Invoices ({total_affected} total):</h4>
            <ul>{invoice_list}</ul>
            
            <div style="background: #d4edda; padding: 10px; margin: 10px 0;">
                <strong><i class="fa fa-check"></i> All invoices have been fully approved and are now finalized.</strong>
            </div>
            """
        else:
            message = f"""
            <h3 style="color: #007bff;">Group Invoice Approval - Ready for {step_name}</h3>
            <p><strong>Date:</strong> {inv_date}</p>
            <p><strong>Company:</strong> {billing_company}</p>
            <p><strong>Approved By:</strong> {approved_by}</p>
            
            <h4>Invoices Ready for Your Approval ({total_affected} total):</h4>
            <ul>{invoice_list}</ul>
            
            <div style="background: #cce5ff; padding: 10px; margin: 10px 0;">
                <strong>Action Required:</strong>
                <p>These invoices are now ready for your approval. Please review and approve/reject as appropriate.</p>
            </div>
            """
        
        frappe.custom_sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            now=True
        )
        
        return {"status": "success", "message": "Group approval notification sent"}
        
    except Exception as e:
        frappe.log_error(f"Error sending group approval email: {str(e)}")
        return {"status": "error", "message": str(e)}




@frappe.whitelist()
def get_previous_approval_recipients(current_workflow_state):
    """Get email recipients for previous approval steps only"""
    try:
        recipients = []
        
        # Define the approval flow hierarchy
        approval_hierarchy = {
            'Pending': [],  
            'Approve By Nirav Sir': ['Earth'],  
            'Approve By Travel Desk': ['Earth', 'Nirav'],  
            'Approve By Tyab Sir': ['Earth', 'Nirav', 'Travel Desk'],  
            'Approve By Panjikar Sir': ['Earth', 'Nirav', 'Travel Desk', 'Tyab'],  
            'Approved': ['Earth', 'Nirav', 'Travel Desk', 'Tyab', 'Panjikar']  
        }
        
        roles_to_notify = approval_hierarchy.get(current_workflow_state, [])
        
       
        if 'Earth' in roles_to_notify:
            roles_to_notify.extend([
                'Earth Upload', 
                'Earth Upload Hotel', 
                'Earth Upload Bus', 
                'Earth Upload Domestic Air',
                'Earth Upload International Air', 
                'Earth Upload Railway'
            ])
        
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
        frappe.log_error(f"Error getting previous approval recipients: {str(e)}")
        return []

@frappe.whitelist()
def get_rejector_level_name(current_workflow_state):
    """Get the display name of the rejector level"""
    level_names = {
        'Pending': 'Earth Level',
        'Approve By Nirav Sir': 'Nirav Sir',
        'Approve By Travel Desk': 'Travel Desk',
        'Approve By Tyab Sir': 'Tyab Sir',
        'Approve By Panjikar Sir': 'Panjikar Sir',
        'Approved': 'Accounts Team'
    }
    return level_names.get(current_workflow_state, current_workflow_state)

@frappe.whitelist()
def get_next_approval_recipients(next_state):
    
    try:
        recipients = []
    
        state_role_mapping = {
            'Approve By Nirav Sir': 'Nirav',
            'Approve By Travel Desk': 'Travel Desk', 
            'Approve By Tyab Sir': 'Tyab',
            'Approve By Panjikar Sir': 'Panjikar',
        }
        
        role_to_notify = state_role_mapping.get(next_state)
        if not role_to_notify:
            return []
        
        role_users = frappe.get_all(
            "Has Role",
            filters={"role": role_to_notify},
            fields=["parent"]
        )
        
        for user in role_users:
            email = frappe.db.get_value("User", user.parent, "email")
            if email and email not in recipients:
                recipients.append(email)
        
        return recipients
        
    except Exception as e:
        frappe.log_error(f"Error getting next approval recipients: {str(e)}")
        return []

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