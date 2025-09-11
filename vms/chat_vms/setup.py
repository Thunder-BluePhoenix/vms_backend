# vms/APIs/notification_chatroom/setup.py
# Setup functions for chat application

import frappe
from frappe import _
from frappe.utils import now_datetime

def setup_chat_application():
    """Setup chat application after installation"""
    try:
        # Create default chat roles
        create_chat_roles()
        
        # Create default chat settings
        create_chat_settings()
        
        # Setup default permissions
        setup_chat_permissions()
        
        # Create sample data (optional)
        create_sample_data()
        
        print("Chat application setup completed successfully")
        
    except Exception as e:
        frappe.log_error(f"Error setting up chat application: {str(e)}")

def create_chat_roles():
    """Create default chat roles"""
    roles = [
        {
            "name": "Chat Admin",
            "description": "Can manage all chat rooms and moderate messages"
        },
        {
            "name": "Chat Moderator", 
            "description": "Can moderate messages in assigned chat rooms"
        },
        {
            "name": "Chat User",
            "description": "Can participate in chat rooms"
        }
    ]
    
    for role_data in roles:
        if not frappe.db.exists("Role", role_data["name"]):
            try:
                role = frappe.new_doc("Role")
                role.role_name = role_data["name"]
                role.description = role_data["description"]
                role.insert(ignore_permissions=True)
                print(f"Created role: {role_data['name']}")
            except Exception as e:
                frappe.log_error(f"Error creating role {role_data['name']}: {str(e)}")

def create_chat_settings():
    """Create default chat settings"""
    settings = {
        "max_file_size": 10485760,  # 10MB
        "allowed_file_types": "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx",
        "enable_message_editing": 1,
        "message_edit_time_limit": 24,  # 24 hours
        "enable_message_reactions": 1,
        "enable_typing_indicators": 1,
        "enable_desktop_notifications": 1,
        "auto_delete_old_messages": 0,
        "default_room_max_members": 50
    }
    
    # Create Chat Settings DocType if it doesn't exist
    if not frappe.db.exists("DocType", "Chat Settings"):
        try:
            create_chat_settings_doctype()
        except Exception as e:
            frappe.log_error(f"Error creating Chat Settings DocType: {str(e)}")
    
    # Create or update chat settings record
    if not frappe.db.exists("Chat Settings", "Chat Settings"):
        try:
            chat_settings = frappe.new_doc("Chat Settings")
            chat_settings.name = "Chat Settings"
            for key, value in settings.items():
                if hasattr(chat_settings, key):
                    setattr(chat_settings, key, value)
            chat_settings.insert(ignore_permissions=True)
            print("Created Chat Settings record")
        except Exception as e:
            frappe.log_error(f"Error creating Chat Settings record: {str(e)}")

def create_chat_settings_doctype():
    """Create Chat Settings DocType"""
    doctype_dict = {
        "doctype": "DocType",
        "name": "Chat Settings",
        "module": "Chat VMS",
        "issingle": 1,
        "fields": [
            {
                "fieldname": "general_settings",
                "fieldtype": "Section Break",
                "label": "General Settings"
            },
            {
                "fieldname": "max_file_size",
                "fieldtype": "Int",
                "label": "Max File Size (bytes)",
                "default": 10485760
            },
            {
                "fieldname": "allowed_file_types",
                "fieldtype": "Data",
                "label": "Allowed File Types",
                "default": "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx"
            },
            {
                "fieldname": "default_room_max_members",
                "fieldtype": "Int",
                "label": "Default Room Max Members",
                "default": 50
            },
            {
                "fieldname": "message_settings",
                "fieldtype": "Section Break",
                "label": "Message Settings"
            },
            {
                "fieldname": "enable_message_editing",
                "fieldtype": "Check",
                "label": "Enable Message Editing",
                "default": 1
            },
            {
                "fieldname": "message_edit_time_limit",
                "fieldtype": "Int",
                "label": "Message Edit Time Limit (hours)",
                "default": 24
            },
            {
                "fieldname": "enable_message_reactions",
                "fieldtype": "Check",
                "label": "Enable Message Reactions",
                "default": 1
            },
            {
                "fieldname": "notification_settings",
                "fieldtype": "Section Break",
                "label": "Notification Settings"
            },
            {
                "fieldname": "enable_desktop_notifications",
                "fieldtype": "Check",
                "label": "Enable Desktop Notifications",
                "default": 1
            },
            {
                "fieldname": "enable_typing_indicators",
                "fieldtype": "Check",
                "label": "Enable Typing Indicators",
                "default": 1
            },
            {
                "fieldname": "cleanup_settings",
                "fieldtype": "Section Break",
                "label": "Cleanup Settings"
            },
            {
                "fieldname": "auto_delete_old_messages",
                "fieldtype": "Check",
                "label": "Auto Delete Old Messages",
                "default": 0
            },
            {
                "fieldname": "auto_delete_after_days",
                "fieldtype": "Int",
                "label": "Auto Delete After (Days)",
                "default": 365,
                "depends_on": "auto_delete_old_messages"
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1,
                "write": 1
            },
            {
                "role": "Chat Admin",
                "read": 1,
                "write": 1
            }
        ]
    }
    
    doc = frappe.get_doc(doctype_dict)
    doc.insert(ignore_permissions=True)

def setup_chat_permissions():
    """Setup default chat permissions"""
    try:
        # Chat Room permissions
        chat_room_perms = [
            {"role": "System Manager", "perms": {"read": 1, "write": 1, "create": 1, "delete": 1, "share": 1, "report": 1}},
            {"role": "Chat Admin", "perms": {"read": 1, "write": 1, "create": 1, "delete": 1, "share": 1, "report": 1}},
            {"role": "Chat Moderator", "perms": {"read": 1, "write": 1, "create": 1}},
            {"role": "Chat User", "perms": {"read": 1, "write": 1, "create": 1}},
            {"role": "Employee", "perms": {"read": 1, "write": 1, "create": 1}}
        ]
        
        for perm in chat_room_perms:
            if frappe.db.exists("Role", perm["role"]):
                # Check if permission already exists
                existing = frappe.db.exists("DocPerm", {
                    "parent": "Chat Room",
                    "role": perm["role"]
                })
                
                if not existing:
                    try:
                        doc_perm = frappe.new_doc("DocPerm")
                        doc_perm.parent = "Chat Room"
                        doc_perm.parenttype = "DocType"
                        doc_perm.parentfield = "permissions"
                        doc_perm.role = perm["role"]
                        for perm_type, value in perm["perms"].items():
                            setattr(doc_perm, perm_type, value)
                        doc_perm.insert(ignore_permissions=True)
                        print(f"Created Chat Room permission for {perm['role']}")
                    except Exception as e:
                        frappe.log_error(f"Error creating Chat Room permission for {perm['role']}: {str(e)}")
        
        # Chat Message permissions
        chat_message_perms = [
            {"role": "System Manager", "perms": {"read": 1, "write": 1, "create": 1, "delete": 1, "share": 1, "report": 1}},
            {"role": "Chat Admin", "perms": {"read": 1, "write": 1, "create": 1, "delete": 1, "share": 1, "report": 1}},
            {"role": "Chat Moderator", "perms": {"read": 1, "write": 1, "create": 1, "delete": 1}},
            {"role": "Chat User", "perms": {"read": 1, "write": 1, "create": 1}},
            {"role": "Employee", "perms": {"read": 1, "write": 1, "create": 1}}
        ]
        
        for perm in chat_message_perms:
            if frappe.db.exists("Role", perm["role"]):
                existing = frappe.db.exists("DocPerm", {
                    "parent": "Chat Message",
                    "role": perm["role"]
                })
                
                if not existing:
                    try:
                        doc_perm = frappe.new_doc("DocPerm")
                        doc_perm.parent = "Chat Message"
                        doc_perm.parenttype = "DocType"
                        doc_perm.parentfield = "permissions"
                        doc_perm.role = perm["role"]
                        for perm_type, value in perm["perms"].items():
                            setattr(doc_perm, perm_type, value)
                        doc_perm.insert(ignore_permissions=True)
                        print(f"Created Chat Message permission for {perm['role']}")
                    except Exception as e:
                        frappe.log_error(f"Error creating Chat Message permission for {perm['role']}: {str(e)}")
                        
        frappe.db.commit()
        print("Chat permissions setup completed")
        
    except Exception as e:
        frappe.log_error(f"Error setting up chat permissions: {str(e)}")

def create_sample_data():
    """Create sample chat data for testing (optional)"""
    try:
        # Only create sample data in development mode
        if frappe.conf.get("developer_mode"):
            create_sample_chat_room()
            print("Sample chat data created")
        
    except Exception as e:
        frappe.log_error(f"Error creating sample data: {str(e)}")

def create_sample_chat_room():
    """Create a sample chat room"""
    try:
        # Check if sample room already exists
        if frappe.db.exists("Chat Room", "General Discussion"):
            return
            
        # Create sample room
        room = frappe.new_doc("Chat Room")
        room.room_name = "General Discussion"
        room.room_type = "Group Chat"
        room.description = "A general discussion room for all team members"
        room.created_by = "Administrator"
        room.max_members = 100
        room.allow_file_sharing = 1
        
        # Add Administrator as admin
        room.append("members", {
            "user": "Administrator",
            "role": "Admin",
            "is_admin": 1,
            "joined_date": now_datetime()
        })
        
        room.insert(ignore_permissions=True)
        
        # Create welcome message
        message = frappe.new_doc("Chat Message")
        message.chat_room = room.name
        message.sender = "Administrator"
        message.message_type = "System"
        message.message_content = "Welcome to the General Discussion room! This is a sample room to get you started with the chat application."
        message.timestamp = now_datetime()
        message.insert(ignore_permissions=True)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating sample chat room: {str(e)}")

def update_chat_permissions():
    """Update chat permissions after migration"""
    try:
        # Add any new permissions or update existing ones
        setup_chat_permissions()
        
        # Update existing chat rooms and messages permissions
        frappe.db.sql("""
            UPDATE `tabChat Room` 
            SET modified = %s 
            WHERE modified < '2025-01-01'
        """, [now_datetime()])
        
        frappe.db.commit()
        
        print("Chat permissions updated successfully")
        
    except Exception as e:
        frappe.log_error(f"Error updating chat permissions: {str(e)}")

def create_chat_custom_fields():
    """Create custom fields for chat integration"""
    try:
        # Add chat status field to User
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_status"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_chat_status"
            custom_field.label = "Chat Status"
            custom_field.fieldtype = "Select"
            custom_field.options = "online\naway\noffline"
            custom_field.default = "offline"
            custom_field.insert_after = "user_image"
            custom_field.insert(ignore_permissions=True)
            print("Created custom_chat_status field for User")
        
        # Add last chat activity field to User
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_last_chat_activity"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_last_chat_activity"
            custom_field.label = "Last Chat Activity"
            custom_field.fieldtype = "Datetime"
            custom_field.read_only = 1
            custom_field.insert_after = "custom_chat_status"
            custom_field.insert(ignore_permissions=True)
            print("Created custom_last_chat_activity field for User")
        
        # Add chat preferences to User
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_notifications_enabled"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_chat_notifications_enabled"
            custom_field.label = "Enable Chat Notifications"
            custom_field.fieldtype = "Check"
            custom_field.default = 1
            custom_field.insert_after = "custom_last_chat_activity"
            custom_field.insert(ignore_permissions=True)
            print("Created custom_chat_notifications_enabled field for User")
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating chat custom fields: {str(e)}")

def setup_chat_workspace():
    """Create Chat workspace"""
    try:
        # Check if Chat workspace already exists
        if frappe.db.exists("Workspace", "Chat"):
            return
            
        workspace = frappe.new_doc("Workspace")
        workspace.title = "Chat"
        workspace.name = "Chat"
        workspace.module = "Chat VMS"
        workspace.icon = "chat"
        workspace.is_standard = 1
        workspace.public = 1
        
        # Add shortcuts
        shortcuts = [
            {
                "type": "DocType",
                "label": "Chat Rooms",
                "doc_view": "List",
                "link_to": "Chat Room",
                "stats_filter": '{"room_status": "Active"}'
            },
            {
                "type": "DocType",
                "label": "Chat Messages",
                "doc_view": "List",
                "link_to": "Chat Message",
                "stats_filter": '{"is_deleted": 0}'
            },
            {
                "type": "Page",
                "label": "Chat Application",
                "link_to": "/chat"
            }
        ]
        
        for shortcut in shortcuts:
            workspace.append("shortcuts", shortcut)
        
        # Add cards for quick access
        cards = [
            {
                "card_name": "Active Rooms",
                "card_type": "Number Card"
            },
            {
                "card_name": "Messages Today",
                "card_type": "Number Card"
            },
            {
                "card_name": "online Users",
                "card_type": "Number Card"
            }
        ]
        
        for card in cards:
            workspace.append("cards", card)
        
        workspace.insert(ignore_permissions=True)
        print("Created Chat workspace")
        
    except Exception as e:
        frappe.log_error(f"Error creating Chat workspace: {str(e)}")

def create_chat_dashboard():
    """Create Chat analytics dashboard"""
    try:
        # Create dashboard
        if not frappe.db.exists("Dashboard", "Chat Analytics"):
            dashboard = frappe.new_doc("Dashboard")
            dashboard.dashboard_name = "Chat Analytics"
            dashboard.module = "Chat VMS"
            dashboard.is_standard = 1
            
            # Add charts
            charts = [
                {
                    "chart": "Messages Per Day",
                    "width": "Half"
                },
                {
                    "chart": "Active Users",
                    "width": "Half"
                },
                {
                    "chart": "Room Activity",
                    "width": "Full"
                }
            ]
            
            for chart in charts:
                dashboard.append("charts", chart)
            
            dashboard.insert(ignore_permissions=True)
            print("Created Chat Analytics dashboard")
        
    except Exception as e:
        frappe.log_error(f"Error creating Chat dashboard: {str(e)}")

def setup_chat_notifications():
    """Setup notification settings for chat"""
    try:
        # Create notification for new chat messages
        if not frappe.db.exists("Notification", "New Chat Message"):
            notification = frappe.new_doc("Notification")
            notification.name = "New Chat Message"
            notification.subject = "New message in {room_name}"
            notification.document_type = "Chat Message"
            notification.event = "New"
            notification.enabled = 1
            notification.channel = "Email"
            notification.recipients = [
                {
                    "receiver_by_document_field": "chat_room.members.user"
                }
            ]
            notification.message = """
                <p>Hello,</p>
                <p>You have a new message in the chat room <strong>{{ doc.chat_room }}</strong></p>
                <p><strong>From:</strong> {{ doc.sender }}</p>
                <p><strong>Message:</strong> {{ doc.message_content }}</p>
                <p><a href="/chat/room/{{ doc.chat_room }}">View Message</a></p>
            """
            notification.insert(ignore_permissions=True)
            print("Created New Chat Message notification")
        
    except Exception as e:
        frappe.log_error(f"Error setting up chat notifications: {str(e)}")

def cleanup_chat_installation():
    """Clean up any existing chat data during reinstallation"""
    try:
        # This function can be called during app uninstall/reinstall
        # Be careful with this in production!
        
        if frappe.conf.get("developer_mode"):
            # Only in development mode
            frappe.db.sql("DELETE FROM `tabChat Message` WHERE message_type = 'System'")
            frappe.db.sql("DELETE FROM `tabChat Room` WHERE room_name LIKE 'Test%' OR room_name = 'General Discussion'")
            frappe.db.commit()
            print("Cleaned up test chat data")
        
    except Exception as e:
        frappe.log_error(f"Error cleaning up chat installation: {str(e)}")

def validate_chat_installation():
    """Validate that chat application is properly installed"""
    try:
        validation_results = []
        
        # Check if required DocTypes exist
        required_doctypes = ["Chat Room", "Chat Message", "Chat Room Member", 
                           "Chat Message Attachment", "Chat Message Reaction"]
        
        for doctype in required_doctypes:
            if frappe.db.exists("DocType", doctype):
                validation_results.append(f"✓ {doctype} DocType exists")
            else:
                validation_results.append(f"✗ {doctype} DocType missing")
        
        # Check if required roles exist
        required_roles = ["Chat Admin", "Chat User"]
        
        for role in required_roles:
            if frappe.db.exists("Role", role):
                validation_results.append(f"✓ {role} Role exists")
            else:
                validation_results.append(f"✗ {role} Role missing")
        
        # Check if API methods are accessible
        try:
            frappe.get_attr("vms.APIs.notification_chatroom.chat_apis.chat_api.get_user_chat_rooms")
            validation_results.append("✓ Chat APIs are accessible")
        except:
            validation_results.append("✗ Chat APIs not accessible")
        
        # Check database tables
        tables_to_check = ["tabChat Room", "tabChat Message"]
        for table in tables_to_check:
            try:
                frappe.db.sql(f"SELECT 1 FROM `{table}` LIMIT 1")
                validation_results.append(f"✓ {table} table accessible")
            except:
                validation_results.append(f"✗ {table} table not accessible")
        
        print("Chat Installation Validation Results:")
        for result in validation_results:
            print(result)
        
        return validation_results
        
    except Exception as e:
        frappe.log_error(f"Error validating chat installation: {str(e)}")
        return [f"✗ Validation failed: {str(e)}"]

# Main setup function that can be called from hooks
def install_chat_application():
    """Main installation function"""
    try:
        print("Starting Chat Application Installation...")
        
        # Step 1: Basic setup
        setup_chat_application()
        
        # Step 2: Create custom fields
        create_chat_custom_fields()
        
        # Step 3: Setup workspace
        setup_chat_workspace()
        
        # Step 4: Create dashboard
        create_chat_dashboard()
        
        # Step 5: Setup notifications
        setup_chat_notifications()
        
        # Step 6: Validate installation
        validation_results = validate_chat_installation()
        
        print("Chat Application Installation Completed!")
        print("Validation Results:", validation_results)
        
    except Exception as e:
        frappe.log_error(f"Error installing chat application: {str(e)}")
        print(f"Chat Application Installation Failed: {str(e)}")

# Uninstall function
def uninstall_chat_application():
    """Uninstall chat application"""
    try:
        print("Starting Chat Application Uninstallation...")
        
        # Clean up data if in development mode
        cleanup_chat_installation()
        
        print("Chat Application Uninstallation Completed!")
        
    except Exception as e:
        frappe.log_error(f"Error uninstalling chat application: {str(e)}")
        print(f"Chat Application Uninstallation Failed: {str(e)}")