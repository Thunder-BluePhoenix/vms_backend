import frappe
from frappe import _

def get_permission_query_conditions(user=None):
    if not user:
        user = frappe.session.user
    
  
    if 'System Manager' in frappe.get_roles(user):
        return None
    
    user_roles = frappe.get_roles(user)
    
    conditions = []
    
    if 'Earth' in user_roles:
        # conditions.append(f"`tabEarth Invoice`.owner = '{user}'")
        conditions.append("`tabEarth Invoice`.workflow_state = 'Pending'")
    
    approval_conditions = get_approval_matrix_conditions(user_roles)
    if approval_conditions:
        conditions.extend(approval_conditions)
    
    if conditions:
        return f"({' OR '.join(conditions)})"
    else:
        return "`tabEarth Invoice`.name = 'NEVER_MATCH'"

def get_approval_matrix_conditions(user_roles):
   
    conditions = []
    

    matrices = frappe.get_all("Approval Matrix", 
        filters={"document_type": "Earth Invoice", "is_active": 1})
    
    for matrix_info in matrices:
        matrix = frappe.get_doc("Approval Matrix", matrix_info.name)


        for level in matrix.approval_levels:
            if level.approver_type == "Role" and level.approver_value in user_roles:
                level_conditions = [
                    
                ]

                if level.status_when_approved:
                    level_conditions.append(
                        f"`tabEarth Invoice`.workflow_state = '{level.status_when_approved}'"
                    )
                if level.status_when_rejected:
                    level_conditions.append(
                        f"`tabEarth Invoice`.workflow_state = '{level.status_when_rejected}'"
                    )
                
                previous_level = None
                for check_level in matrix.approval_levels:
                    if check_level.sequence == level.sequence - 1: 
                        previous_level = check_level
                        break
                
              
                if previous_level:
                    print(f"Current level: {level.sequence}, Previous level: {previous_level.sequence}")
                    print(f"Status when approved: {previous_level.status_when_approved}, Status when rejected: {previous_level.status_when_rejected}")
                    if previous_level.status_when_approved:
                        level_conditions.append(
                            f"`tabEarth Invoice`.workflow_state = '{previous_level.status_when_approved}'"
                        )
                    if previous_level.status_when_rejected:
                        level_conditions.append(
                            f"`tabEarth Invoice`.workflow_state = '{previous_level.status_when_rejected}'"
                        )
                
                max_sequence = max(l.sequence for l in matrix.approval_levels)
                if level.sequence == max_sequence:
                    level_conditions.extend([
                        "`tabEarth Invoice`.workflow_state = 'Approved'",
                        "`tabEarth Invoice`.workflow_state = 'Rejected'"
                    ])
                
                if level_conditions:
                    conditions.append(f"({' OR '.join(level_conditions)})")
            
            elif level.approver_type == "User" and level.approver_value == frappe.session.user:
                level_conditions = []

                if level.status_when_approved:
                    level_conditions.append(
                        f"`tabEarth Invoice`.workflow_state = '{level.status_when_approved}'"
                    )
                if level.status_when_rejected:
                    level_conditions.append(
                        f"`tabEarth Invoice`.workflow_state = '{level.status_when_rejected}'"
                    )
                
              
                previous_level = None
                for check_level in matrix.approval_levels:
                    if check_level.sequence == level.sequence - 1:
                        previous_level = check_level
                        break
                
                if previous_level:
                    if previous_level.status_when_approved:
                        level_conditions.append(
                            f"`tabEarth Invoice`.workflow_state = '{previous_level.status_when_approved}'"
                        )
                    if previous_level.status_when_rejected:
                        level_conditions.append(
                            f"`tabEarth Invoice`.workflow_state = '{previous_level.status_when_rejected}'"
                        )
                
                
                max_sequence = max(l.sequence for l in matrix.approval_levels)
                if level.sequence == max_sequence:
                    level_conditions.extend([
                        "`tabEarth Invoice`.workflow_state = 'Approved'",
                        "`tabEarth Invoice`.workflow_state = 'Rejected'"
                    ])
                
                conditions.append(f"({' OR '.join(level_conditions)})")

        return conditions

       
def has_permission(doc, user=None, permission_type=None):
    if not user:
        user = frappe.session.user
    
    if 'System Manager' in frappe.get_roles(user):
        return True
    
    user_roles = frappe.get_roles(user)
    
    if 'Earth' in user_roles and doc.owner == user:
        return True
    
    
    return check_approval_matrix_permission(doc, user_roles)

def check_approval_matrix_permission(doc, user_roles):
    """Check if user can access document based on approval matrix"""
    if not hasattr(doc, 'approval_matrix') or not doc.approval_matrix:
        return False
    
    try:
        matrix = frappe.get_doc("Approval Matrix", doc.approval_matrix)
        current_workflow_state = getattr(doc, 'workflow_state', 'Pending')
        
        # Check if user can access document at current state
        for level in matrix.approval_levels:
            if level.approver_type == "Role" and level.approver_value in user_roles:
                # Check if this user can see document at current state
                allowed_states = ['Pending']
                
                for check_level in matrix.approval_levels:
                    if check_level.sequence <= level.sequence:
                        if check_level.status_when_approved:
                            allowed_states.append(check_level.status_when_approved)
                        if check_level.status_when_rejected:
                            allowed_states.append(check_level.status_when_rejected)
                
                # Final level users can see approved/rejected
                max_sequence = max(l.sequence for l in matrix.approval_levels)
                if level.sequence == max_sequence:
                    allowed_states.extend(['Approved', 'Rejected'])
                
                if current_workflow_state in allowed_states:
                    return True
    except:
        pass
    
    return False

@frappe.whitelist()
def get_user_access_summary():
    """Get summary of what current user can access"""
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    
    # Count documents based on permission query
    query_conditions = get_permission_query_conditions(user)
    
    if query_conditions:
        total_accessible = frappe.db.count("Earth Invoice", filters=query_conditions)
    else:
        total_accessible = frappe.db.count("Earth Invoice")  
    
    pending_for_user = len(get_pending_for_current_user())
    
    return {
        "total_accessible": total_accessible,
        "pending_for_user": pending_for_user,
        "user_roles": user_roles
    }

def get_pending_for_current_user():
    """Get documents pending for current user's approval"""
    user = frappe.session.user
    
    pending_docs = frappe.get_all("Earth Invoice", 
        filters={"approval_status": "Pending", "docstatus": 0},
        fields=["name", "approval_matrix", "current_approval_level"]
    )
    
    user_can_approve = []
    for doc_info in pending_docs:
        try:
            doc = frappe.get_doc("Earth Invoice", doc_info.name)
            if can_user_approve_document(doc, user):
                user_can_approve.append(doc_info.name)
        except:
            continue
    
    return user_can_approve

def can_user_approve_document(doc, user):
    """Check if specific user can approve specific document"""
    if not doc.approval_matrix or doc.approval_status != "Pending":
        return False
        
    try:
        matrix = frappe.get_doc("Approval Matrix", doc.approval_matrix)
        current_level = None
        
        for level in matrix.approval_levels:
            if level.sequence == doc.current_approval_level:
                current_level = level
                break
        
        if not current_level:
            return False
        
        user_roles = frappe.get_roles(user)
        
        if current_level.approver_type == "Role":
            return current_level.approver_value in user_roles
        elif current_level.approver_type == "User":
            return current_level.approver_value == user
            
    except:
        pass
    
    return False