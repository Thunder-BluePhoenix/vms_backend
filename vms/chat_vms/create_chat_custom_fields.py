# vms/chat_vms/create_chat_custom_fields.py
# Script to create missing custom fields for chat integration

import frappe

def execute():
    """Create missing custom fields for chat functionality"""
    print("Creating missing custom fields for chat integration...")
    
    # Create chat status field for User
    create_user_chat_status_field()
    
    # Create last chat activity field for User
    create_user_last_activity_field()
    
    # Create chat notifications preference field for User
    create_user_notifications_field()
    
    print("Custom fields creation completed!")

def create_user_chat_status_field():
    """Create custom_chat_status field for User DocType"""
    if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_status"}):
        try:
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_chat_status"
            custom_field.label = "Chat Status"
            custom_field.fieldtype = "Select"
            custom_field.options = "online\naway\nbusy\noffline"
            custom_field.default = "offline"
            custom_field.insert_after = "desk_theme"
            custom_field.in_list_view = 0
            custom_field.read_only = 1
            custom_field.description = "Current chat status of the user"
            custom_field.insert(ignore_permissions=True)
            print("✓ Created custom_chat_status field for User")
        except Exception as e:
            print(f"❌ Failed to create custom_chat_status field: {str(e)}")
    else:
        print("✓ custom_chat_status field already exists")

def create_user_last_activity_field():
    """Create custom_last_chat_activity field for User DocType"""
    if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_last_chat_activity"}):
        try:
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_last_chat_activity"
            custom_field.label = "Last Chat Activity"
            custom_field.fieldtype = "Datetime"
            custom_field.insert_after = "custom_chat_status"
            custom_field.in_list_view = 0
            custom_field.read_only = 1
            custom_field.description = "Timestamp of last chat activity"
            custom_field.insert(ignore_permissions=True)
            print("✓ Created custom_last_chat_activity field for User")
        except Exception as e:
            print(f"❌ Failed to create custom_last_chat_activity field: {str(e)}")
    else:
        print("✓ custom_last_chat_activity field already exists")

def create_user_notifications_field():
    """Create custom_chat_notifications_enabled field for User DocType"""
    if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_notifications_enabled"}):
        try:
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_chat_notifications_enabled"
            custom_field.label = "Enable Chat Notifications"
            custom_field.fieldtype = "Check"
            custom_field.default = 1
            custom_field.insert_after = "custom_last_chat_activity"
            custom_field.in_list_view = 0
            custom_field.description = "Enable/disable chat notifications for this user"
            custom_field.insert(ignore_permissions=True)
            print("✓ Created custom_chat_notifications_enabled field for User")
        except Exception as e:
            print(f"❌ Failed to create custom_chat_notifications_enabled field: {str(e)}")
    else:
        print("✓ custom_chat_notifications_enabled field already exists")

if __name__ == '__main__':
    execute()