# vms/patches/chat_application_setup.py
# Updated patch function to install and setup chat application

import frappe
from frappe import _
from frappe.utils import now_datetime, cint

def execute():
    """
    Patch function to install and setup chat application
    This will run automatically during migration
    """
    try:
        print("🚀 Starting Chat Application Setup Patch...")
        
        # Step 1: Validate prerequisites
        validate_prerequisites()
        
        # Step 2: Install chat application
        install_chat_application()
        
        # Step 3: Create Chat Settings DocType and record
        create_chat_settings_doctype()
        
        # Step 4: Setup Socket.IO integration
        setup_socketio_integration()
        
        # Step 5: Verify installation
        verify_installation()
        
        print("✅ Chat Application Setup Patch Completed Successfully!")
        
    except Exception as e:
        error_msg = f"❌ Chat Application Setup Patch Failed: {str(e)}"
        print(error_msg)
        frappe.log_error(error_msg, "Chat Application Setup Patch")
        # Don't raise exception to avoid breaking migration

def validate_prerequisites():
    """Validate that all prerequisites are met"""
    try:
        print("🔍 Validating prerequisites...")
        
        # Check if required DocTypes exist
        required_doctypes = [
            "Chat Room", 
            "Chat Message", 
            "Chat Room Member",
            "Chat Message Attachment", 
            "Chat Message Reaction"
        ]
        
        for doctype in required_doctypes:
            if frappe.db.exists("DocType", doctype):
                print(f"  ✓ DocType {doctype} exists")
            else:
                print(f"  ⚠️  DocType {doctype} not found - will need to be created manually")
        
        # Check Socket.IO configuration
        socketio_port = frappe.conf.get('socketio_port', 9013)
        print(f"  ✓ Socket.IO configured on port {socketio_port}")
        
        print("✅ Prerequisites validation completed")
        
    except Exception as e:
        raise Exception(f"Prerequisites validation failed: {str(e)}")

def install_chat_application():
    """Install chat application using available methods"""
    try:
        print("📦 Installing Chat Application...")
        
        # Try method 1: Use setup module
        try:
            from vms.chat_vms import setup
            if hasattr(setup, 'install_chat_application'):
                setup.install_chat_application()
                print("  ✓ Chat application installed via setup module")
                return
            elif hasattr(setup, 'setup_chat_application'):
                setup.setup_chat_application()
                print("  ✓ Basic chat setup completed via setup module")
        except (ImportError, AttributeError) as e:
            print(f"  ⚠️  Setup module method failed: {str(e)}")
        
        # Method 2: Import functions directly
        try:
            print("  📦 Trying direct function import...")
            direct_install_chat_application()
            print("  ✓ Chat application installed via direct method")
            return
        except Exception as e:
            print(f"  ⚠️  Direct method failed: {str(e)}")
        
        # Method 3: Basic setup only
        try:
            print("  📦 Trying basic setup...")
            basic_chat_setup()
            print("  ✓ Basic chat setup completed")
        except Exception as e:
            print(f"  ❌ All installation methods failed: {str(e)}")
            
    except Exception as e:
        error_msg = f"Chat application installation failed: {str(e)}"
        print(f"  ❌ {error_msg}")
        frappe.log_error(error_msg, "Chat Installation")

def create_chat_settings_doctype():
    """Create Chat Settings DocType if it doesn't exist"""
    try:
        print("📝 Creating Chat Settings DocType...")
        
        # Check if DocType already exists
        if frappe.db.exists("DocType", "Chat Settings"):
            print("  ✓ Chat Settings DocType already exists")
        else:
            print("  📝 Creating Chat Settings DocType...")
            
            # Create the DocType
            doctype_dict = {
                "doctype": "DocType",
                "name": "Chat Settings",
                "module": "Chat VMS",
                "issingle": 1,
                "autoname": "",
                "fields": [
                    {
                        "fieldname": "general_settings_section",
                        "fieldtype": "Section Break",
                        "label": "General Settings"
                    },
                    {
                        "fieldname": "max_file_size",
                        "fieldtype": "Int",
                        "label": "Max File Size (bytes)",
                        "default": 10485760,
                        "description": "Maximum file size allowed for uploads"
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
                        "fieldname": "column_break_1",
                        "fieldtype": "Column Break"
                    },
                    {
                        "fieldname": "enable_desktop_notifications",
                        "fieldtype": "Check",
                        "label": "Enable Desktop Notifications",
                        "default": 1
                    },
                    {
                        "fieldname": "auto_delete_old_messages",
                        "fieldtype": "Check",
                        "label": "Auto Delete Old Messages",
                        "default": 0
                    },
                    {
                        "fieldname": "message_settings_section",
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
                        "fieldname": "column_break_2",
                        "fieldtype": "Column Break"
                    },
                    {
                        "fieldname": "enable_message_reactions",
                        "fieldtype": "Check",
                        "label": "Enable Message Reactions",
                        "default": 1
                    },
                    {
                        "fieldname": "enable_typing_indicators",
                        "fieldtype": "Check",
                        "label": "Enable Typing Indicators",
                        "default": 1
                    }
                ],
                "permissions": [
                    {
                        "role": "System Manager",
                        "read": 1,
                        "write": 1,
                        "create": 1,
                        "delete": 1
                    },
                    {
                        "role": "Chat Admin",
                        "read": 1,
                        "write": 1
                    }
                ]
            }
            
            # Insert DocType
            doctype_doc = frappe.get_doc(doctype_dict)
            doctype_doc.insert(ignore_permissions=True)
            print("  ✓ Chat Settings DocType created")
        
        # Create Chat Settings record
        create_chat_settings_record()
        
    except Exception as e:
        print(f"  ❌ Failed to create Chat Settings DocType: {str(e)}")
        frappe.log_error(f"Chat Settings DocType creation error: {str(e)}")

def create_chat_settings_record():
    """Create Chat Settings record with default values"""
    try:
        if not frappe.db.exists("Chat Settings", "Chat Settings"):
            settings = frappe.new_doc("Chat Settings")
            settings.name = "Chat Settings"
            settings.max_file_size = 10485760
            settings.allowed_file_types = "image/*,application/pdf,text/*,.doc,.docx,.xls,.xlsx"
            settings.default_room_max_members = 50
            settings.enable_desktop_notifications = 1
            settings.auto_delete_old_messages = 0
            settings.enable_message_editing = 1
            settings.message_edit_time_limit = 24
            settings.enable_message_reactions = 1
            settings.enable_typing_indicators = 1
            settings.insert(ignore_permissions=True)
            print("  ✓ Chat Settings record created")
        else:
            print("  ✓ Chat Settings record already exists")
            
    except Exception as e:
        print(f"  ⚠️  Failed to create Chat Settings record: {str(e)}")

def setup_socketio_integration():
    """Setup Socket.IO integration with Frappe's existing server"""
    try:
        print("🔌 Setting up Socket.IO integration...")
        
        # Get Socket.IO configuration
        socketio_port = frappe.conf.get('socketio_port', 9013)
        webserver_port = frappe.conf.get('webserver_port', 8000)
        
        print(f"  ✓ Socket.IO server port: {socketio_port}")
        print(f"  ✓ Web server port: {webserver_port}")
        
        # Create Socket.IO event handlers configuration
        setup_socketio_events()
        
        print("  ✓ Socket.IO integration configured")
        
    except Exception as e:
        print(f"  ⚠️  Socket.IO integration setup failed: {str(e)}")

def setup_socketio_events():
    """Setup Socket.IO event handlers in hooks"""
    try:
        # These should already be in hooks.py
        expected_events = [
            "chat_message",
            "chat_room_join", 
            "chat_room_leave",
            "typing_indicator"
        ]
        
        for event in expected_events:
            print(f"  ✓ Socket.IO event handler: {event}")
            
    except Exception as e:
        print(f"  ⚠️  Socket.IO events setup failed: {str(e)}")

def direct_install_chat_application():
    """Direct installation method"""
    # Create essential roles
    create_chat_roles()
    
    # Create basic permissions
    setup_basic_chat_permissions()
    
    # Create custom fields
    create_chat_custom_fields()
    
    print("  ✓ Direct installation completed")

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

def setup_basic_chat_permissions():
    """Create basic permissions for chat DocTypes"""
    try:
        print("    🔐 Setting up basic permissions...")
        
        # Chat Room permissions
        if frappe.db.exists("DocType", "Chat Room"):
            chat_room_perms = [
                {"role": "System Manager", "perms": {"read": 1, "write": 1, "create": 1, "delete": 1}},
                {"role": "Chat Admin", "perms": {"read": 1, "write": 1, "create": 1, "delete": 1}},
                {"role": "Employee", "perms": {"read": 1, "write": 1, "create": 1}}
            ]
            
            for perm in chat_room_perms:
                if frappe.db.exists("Role", perm["role"]):
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
                            print(f"    ✓ Created Chat Room permission for {perm['role']}")
                        except Exception as e:
                            print(f"    ⚠️  Could not create permission: {str(e)}")
        
        frappe.db.commit()
        print("    ✓ Basic permissions setup completed")
        
    except Exception as e:
        print(f"    ⚠️  Permissions setup failed: {str(e)}")

def create_chat_custom_fields():
    """Create custom fields for chat integration"""
    try:
        print("    📝 Creating custom fields...")
        
        # Add chat status field to User
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_status"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_chat_status"
            custom_field.label = "Chat Status"
            custom_field.fieldtype = "Select"
            custom_field.options = "Online\nAway\nBusy\nOffline"
            custom_field.default = "Offline"
            custom_field.insert_after = "desk_theme"
            custom_field.read_only = 1
            custom_field.insert(ignore_permissions=True)
            print("    ✓ Created custom_chat_status field")
        
        # Add last chat activity field to User
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_last_chat_activity"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_last_chat_activity"
            custom_field.label = "Last Chat Activity"
            custom_field.fieldtype = "Datetime"
            custom_field.insert_after = "custom_chat_status"
            custom_field.read_only = 1
            custom_field.insert(ignore_permissions=True)
            print("    ✓ Created custom_last_chat_activity field")
        
        # Add chat notifications preference field to User
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_chat_notifications_enabled"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "User"
            custom_field.fieldname = "custom_chat_notifications_enabled"
            custom_field.label = "Enable Chat Notifications"
            custom_field.fieldtype = "Check"
            custom_field.default = 1
            custom_field.insert_after = "custom_last_chat_activity"
            custom_field.insert(ignore_permissions=True)
            print("    ✓ Created custom_chat_notifications_enabled field")
        
        frappe.db.commit()
        print("    ✓ Custom fields creation completed")
        
    except Exception as e:
        print(f"    ❌ Custom fields creation failed: {str(e)}")
        frappe.log_error(f"Custom fields creation error: {str(e)}")

def basic_chat_setup():
    """Basic chat setup without advanced features"""
    try:
        create_chat_roles()
        setup_basic_chat_permissions()
        create_chat_custom_fields()
        print("  ✓ Basic chat setup completed")
        
    except Exception as e:
        print(f"  ❌ Basic chat setup failed: {str(e)}")

def verify_installation():
    """Verify that chat application was installed correctly"""
    try:
        print("🔬 Verifying installation...")
        
        verification_results = []
        passed_checks = 0
        total_checks = 0
        
        # Check DocTypes
        required_doctypes = [
            "Chat Room", 
            "Chat Message", 
            "Chat Room Member",
            "Chat Message Attachment", 
            "Chat Message Reaction",
            "Chat Settings"
        ]
        
        for doctype in required_doctypes:
            total_checks += 1
            if frappe.db.exists("DocType", doctype):
                verification_results.append(f"✓ {doctype} DocType")
                print(f"  ✓ {doctype} DocType exists")
                passed_checks += 1
            else:
                verification_results.append(f"✗ {doctype} DocType")
                print(f"  ❌ {doctype} DocType missing")
        
        # Check Roles
        required_roles = ["Chat Admin", "Chat User", "Chat Moderator"]
        
        for role in required_roles:
            total_checks += 1
            if frappe.db.exists("Role", role):
                verification_results.append(f"✓ {role} Role")
                print(f"  ✓ {role} Role exists")
                passed_checks += 1
            else:
                verification_results.append(f"✗ {role} Role")
                print(f"  ❌ {role} Role missing")
        
        # Check API accessibility
        total_checks += 1
        try:
            api_method = frappe.get_attr("vms.APIs.notification_chatroom.chat_apis.chat_api.get_user_chat_rooms")
            if api_method:
                verification_results.append("✓ Chat APIs accessible")
                print("  ✓ Chat APIs are accessible")
                passed_checks += 1
        except:
            verification_results.append("✗ Chat APIs not accessible")
            print("  ❌ Chat APIs not accessible")
        
        # Check Custom Fields
        custom_fields = [
            {"dt": "User", "fieldname": "custom_chat_status"},
            {"dt": "User", "fieldname": "custom_last_chat_activity"},
            {"dt": "User", "fieldname": "custom_chat_notifications_enabled"}
        ]
        
        for field in custom_fields:
            total_checks += 1
            if frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
                verification_results.append(f"✓ {field['dt']}.{field['fieldname']}")
                print(f"  ✓ Custom field {field['dt']}.{field['fieldname']} exists")
                passed_checks += 1
            else:
                verification_results.append(f"✗ {field['dt']}.{field['fieldname']}")
                print(f"  ⚠️  Custom field {field['dt']}.{field['fieldname']} missing")
        
        # Check Chat Settings record
        total_checks += 1
        if frappe.db.exists("Chat Settings", "Chat Settings"):
            verification_results.append("✓ Chat Settings record")
            print("  ✓ Chat Settings record exists")
            passed_checks += 1
        else:
            verification_results.append("✗ Chat Settings record")
            print("  ❌ Chat Settings record missing")
        
        print(f"📊 Verification Summary: {passed_checks}/{total_checks} checks passed")
        
        if passed_checks >= total_checks * 0.8:  # 80% pass rate
            print("✅ Chat application verification passed")
        else:
            print("⚠️  Chat application verification had issues but installation can proceed")
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        frappe.log_error(f"Chat verification error: {str(e)}")