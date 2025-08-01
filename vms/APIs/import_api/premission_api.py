# Role-Based Workflow State Filtering System
# File: vms/APIs/permission_api/workflow_permissions.py

import frappe
from frappe import _

def get_role_workflow_states():
    
    role_workflow_mapping = {
        'Earth': ['Pending'],  
        
        'Earth Upload': ['Pending', 'Approve By Earth Upload','Reject By Earth Upload'], 
        
        'Travel Desk': ['Approve By Earth Upload','Reject By Earth Upload', 'Approve By Travel Desk', 'Reject By Travel Desk'], 

        'Tyab' : ['Approve By Travel Desk', 'Reject By Travel Desk', 'Approve By Tyab Sir', 'Reject By Tyab Sir'],

        'Panjikar' : ['Approve By Tyab Sir', 'Reject By Tyab Sir', 'Approve By Panjikar Sir', 'Reject By Panjikar Sir'],

        'Accounts Team' : ['Approve By Panjikar Sir', 'Reject By Panjikar Sir', 'Approved', 'Rejected'],
    }
    
    return role_workflow_mapping

@frappe.whitelist()
def get_allowed_workflow_states_for_user():
    
    user_roles = frappe.get_roles()
    role_workflow_mapping = get_role_workflow_states()
    allowed_states = set()
    
    for role in user_roles:
        if role in role_workflow_mapping:
            allowed_states.update(role_workflow_mapping[role])
    

    if 'System Manager' in user_roles:
        allowed_states = ['Draft', 'Pending', 'Approve By Earth Upload','Reject By Earth Upload' 'Approved', 'Rejected']
    
    return list(allowed_states)

def get_permission_query_conditions(user=None):
    
    if not user:
        user = frappe.session.user
    

    if 'System Manager' in frappe.get_roles(user):
        return None
    

    user_roles = frappe.get_roles(user)
    role_workflow_mapping = get_role_workflow_states()
    allowed_states = set()
    
    for role in user_roles:
        if role in role_workflow_mapping:
            allowed_states.update(role_workflow_mapping[role])
    
    if allowed_states:
        states_condition = "', '".join(allowed_states)
        return f"`tabEarth Invoice`.workflow_state in ('{states_condition}')"
    else:

        return "`tabEarth Invoice`.workflow_state = 'NEVER_MATCH'"

def has_permission(doc, user=None, permission_type=None):

    
    if not user:
        user = frappe.session.user
    
    
    if 'System Manager' in frappe.get_roles(user):
        return True
    
   
    user_roles = frappe.get_roles(user)
    role_workflow_mapping = get_role_workflow_states()
    allowed_states = set()
    
    for role in user_roles:
        if role in role_workflow_mapping:
            allowed_states.update(role_workflow_mapping[role])
    
    
    if hasattr(doc, 'workflow_state') and doc.workflow_state:
        return doc.workflow_state in allowed_states
    
   
    return len(allowed_states) > 0