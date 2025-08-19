
import frappe
from frappe import _

class DynamicWorkflowPermissions:
    
    @staticmethod
    def get_workflow_role_mapping(doctype="Earth Invoice"):

        try:
            workflows = frappe.get_all(
                "Workflow",
                filters={
                    "document_type": doctype,
                    "is_active": 1
                },
                fields=["name"]
            )
            
            if not workflows:
                return {}
            
            
            all_transitions = []
            for workflow in workflows:
                transitions = frappe.get_all(
                    "Workflow Transition",
                    filters={"parent": workflow.name},
                    fields=["state", "next_state", "allowed", "action"]
                )
                all_transitions.extend(transitions)
            
           
            role_states_mapping = {}
            
            for transition in all_transitions:
                role = transition.get("allowed")
                current_state = transition.get("state")
                next_state = transition.get("next_state")
                
                if not role:
                    continue
                
              
                if role not in role_states_mapping:
                    role_states_mapping[role] = set()
                
                
                if current_state:
                    role_states_mapping[role].add(current_state)
                
                
                if next_state:
                    role_states_mapping[role].add(next_state)
            
            
            for role in role_states_mapping:
                role_states_mapping[role] = list(role_states_mapping[role])
            
            return role_states_mapping
            
        except Exception as e:
            frappe.log_error(f"Error building dynamic workflow mapping: {str(e)}")
            return {}

def get_enhanced_role_workflow_states(doctype="Earth Invoice"):
    
    
    dynamic_mapping = DynamicWorkflowPermissions.get_workflow_role_mapping(doctype)
    
  
    pre_workflow_roles = {
        
        'Earth': ['Pending'],  
        
      
        'Earth Upload': ['Pending'], 
        
       
        'System Manager': get_all_workflow_states(doctype) + ['Draft'],
        'Administrator': get_all_workflow_states(doctype) + ['Draft']
    }
    
    
    combined_mapping = {**dynamic_mapping, **pre_workflow_roles}
    
    return combined_mapping

def get_all_workflow_states(doctype="Earth Invoice"):
  
    try:
        workflows = frappe.get_all(
            "Workflow",
            filters={
                "document_type": doctype,
                "is_active": 1
            },
            fields=["name"]
        )
        
        all_states = set()
        for workflow in workflows:
            states = frappe.get_all(
                "Workflow Document State",
                filters={"parent": workflow.name},
                fields=["state"]
            )
            all_states.update([state.state for state in states])
        
        return list(all_states)
        
    except Exception as e:
        frappe.log_error(f"Error getting workflow states: {str(e)}")
        return []

@frappe.whitelist()
def get_allowed_workflow_states_for_user(doctype="Earth Invoice"):

    try:
        user_roles = frappe.get_roles()
        role_workflow_mapping = get_enhanced_role_workflow_states(doctype)
        allowed_states = set()
        
        for role in user_roles:
            if role in role_workflow_mapping:
                allowed_states.update(role_workflow_mapping[role])
        
       
        if 'System Manager' in user_roles or 'Administrator' in user_roles:
            all_states = get_all_workflow_states(doctype)
            allowed_states.update(all_states)
            allowed_states.add('Draft')
        
        return list(allowed_states)
        
    except Exception as e:
        frappe.log_error(f"Error in get_allowed_workflow_states_for_user: {str(e)}")
        return []

def get_permission_query_conditions(user=None, doctype="Earth Invoice"):
 
    if not user:
        user = frappe.session.user
    
    try:
   
        user_roles = frappe.get_roles(user)
        if 'System Manager' in user_roles or 'Administrator' in user_roles:
            return None
        
       
        role_workflow_mapping = get_enhanced_role_workflow_states(doctype)
        allowed_states = set()
        
        for role in user_roles:
            if role in role_workflow_mapping:
                allowed_states.update(role_workflow_mapping[role])
        
    
        additional_conditions = []
        
       
        if 'Earth' in user_roles:
            additional_conditions.append(
                f"(`tab{doctype}`.workflow_state = 'Pending' AND `tab{doctype}`.owner = '{user}')"
            )
        
       
        if 'Earth Upload' in user_roles:
            additional_conditions.append(
                f"`tab{doctype}`.workflow_state = 'Pending'"
            )
        
  
        workflow_condition = ""
        if allowed_states:
            
            filtered_states = allowed_states.copy()
            if 'Earth' in user_roles or 'Earth Upload' in user_roles:
                filtered_states.discard('Pending')
            
            if filtered_states:
                clean_states = [frappe.db.escape(state) for state in filtered_states]
                states_condition = ", ".join(clean_states)
                workflow_condition = f"`tab{doctype}`.workflow_state in ({states_condition})"
        
     
        all_conditions = []
        if workflow_condition:
            all_conditions.append(workflow_condition)
        if additional_conditions:
            all_conditions.extend(additional_conditions)
        
        if all_conditions:
            return " OR ".join([f"({condition})" for condition in all_conditions])
        else:
            return f"`tab{doctype}`.workflow_state = 'NEVER_MATCH'"
            
    except Exception as e:
        frappe.log_error(f"Error in get_permission_query_conditions: {str(e)}")
        return f"`tab{doctype}`.workflow_state = 'NEVER_MATCH'"

def has_permission(doc, user=None, permission_type=None):
   
    if not user:
        user = frappe.session.user
    
    try:
     
        user_roles = frappe.get_roles(user)
        if 'System Manager' in user_roles or 'Administrator' in user_roles:
            return True
        
        
        doctype = doc.doctype if hasattr(doc, 'doctype') else "Earth Invoice"
        role_workflow_mapping = get_enhanced_role_workflow_states(doctype)
        allowed_states = set()
        
        for role in user_roles:
            if role in role_workflow_mapping:
                allowed_states.update(role_workflow_mapping[role])
        
     
        if 'Earth' in user_roles and hasattr(doc, 'workflow_state'):
            if doc.workflow_state == 'Pending' and doc.owner == user:
                return True
          
            elif doc.workflow_state != 'Pending':
                return False
        
      
        if 'Earth Upload' in user_roles and hasattr(doc, 'workflow_state'):
            if doc.workflow_state == 'Pending':
                return True
        
        
        if hasattr(doc, 'workflow_state') and doc.workflow_state:
            return doc.workflow_state in allowed_states
        
     
        return len(allowed_states) > 0
        
    except Exception as e:
        frappe.log_error(f"Error in has_permission: {str(e)}")
        return False

@frappe.whitelist()
def get_current_workflow_mapping(doctype="Earth Invoice"):
   
    try:
        dynamic_mapping = DynamicWorkflowPermissions.get_workflow_role_mapping(doctype)
        enhanced_mapping = get_enhanced_role_workflow_states(doctype)
        user_states = get_allowed_workflow_states_for_user(doctype)
        
        return {
            "dynamic_from_workflow": dynamic_mapping,
            "enhanced_with_pre_workflow": enhanced_mapping,
            "current_user_states": user_states,
            "workflow_states": get_all_workflow_states(doctype)
        }
    except Exception as e:
        frappe.log_error(f"Error in get_current_workflow_mapping: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def test_permission_for_user(user_email, doctype="Earth Invoice"):
   
    try:
      
        original_user = frappe.session.user
        frappe.set_user(user_email)
        
        query = get_permission_query_conditions(user_email, doctype)
        allowed_states = get_allowed_workflow_states_for_user(doctype)
        user_roles = frappe.get_roles(user_email)
        
        
        frappe.set_user(original_user)
        
        return {
            "user": user_email,
            "roles": user_roles,
            "allowed_states": allowed_states,
            "permission_query": query
        }
        
    except Exception as e:
        frappe.log_error(f"Error testing permission for user {user_email}: {str(e)}")
        return {"error": str(e)}


def set_document_to_pending_workflow(doc):

    try:
        doc.db_set("workflow_state", "Pending")
        

        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Comment",
            "reference_doctype": doc.doctype,
            "reference_name": doc.name,
            "content": "Document moved to workflow. Ready for Travel Desk approval.",
            "comment_email": frappe.session.user,
            "comment_by": frappe.session.user_fullname or frappe.session.user
        }).insert(ignore_permissions=True)
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error setting document to pending workflow: {str(e)}")
        return False

