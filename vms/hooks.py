app_name = "vms"
app_title = "Vms"
app_publisher = "Blue Phoenix"
app_description = "Vendor Management System"
app_email = "bluephoenix00995@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "vms",
# 		"logo": "/assets/vms/logo.png",
# 		"title": "Vms",
# 		"route": "/vms",
# 		"has_permission": "vms.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "assets/vms/css/chat_styles.css",
    "assets/vms/css/chat_enhanced.css"
]
# app_include_js = "/assets/vms/js/vms.js"
app_include_js = [
    "assets/vms/js/earth_invoice_list.js" ,
    # "https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js",
    # "assets/vms/js/chat_integratioonn.js",
    # "assets/vms/js/chat_realtimee.js" 
    # "assets/vms/js/nav_chat27.js",
    # "assets/vms/js/nav_chat_enhanced3.js"  
]

# include js, css files in header of web template
# web_include_css = "/assets/vms/css/vms.css"
# web_include_js = "/assets/vms/js/vms.js"
website_context = {
    "chat_enabled": True,
    "max_file_size": 10485760,  # 10MB
    "supported_file_types": ["image/*", "application/pdf", "text/*", ".doc", ".docx", ".xls", ".xlsx"]
}
# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vms/public/scss/website"
websocket_events = {
    "chat_message": "vms.chat_vms.doctype.chat_message.chat_message.handle_websocket_message",
    "chat_room_join": "vms.chat_vms.doctype.chat_message.chat_message.handle_user_join_room",
    "chat_room_leave": "vms.chat_vms.doctype.chat_message.chat_message.handle_user_leave_room",
    "typing_indicator": "vms.chat_vms.doctype.chat_message.chat_message.handle_typing_indicator"
}
# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}


# boot_session = [
#     "vms.chat_vms.doctype.chat_message.chat_message.get_user_chat_status"
# ]
# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "vms/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"QMS Inspection Reports
# }
fixtures = [
    # {"dt": "SAP Mapper PR"},
    {"dt": "Role", "filters": {"name": ["in", ["Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head", "Vendor", "Panjikar","Tyab", "Super Head", "Accounts Head", "ASA", "IT Head","Nirav","Earth Upload Railway","Earth Upload International Air","Earth Upload Domestic Air","Earth Upload Bus","Earth Upload Hotel"]]}},
    {"dt": "Role Profile", "filters": {"name" :["in", ["Accounts Head", "Super Head", "Accounts Team", "Enquirer", "Purchase Head", "Purchase Team", "Vendor", "QA Team", "QA Head"]]}},
    {"dt": "Module Profile", "filters": {"name": ["in", ["Vendor"]]}},
    {"dt": "QMS Quality Control System"},
    {"dt": "QMS Procedure Doc Name"},
    {"dt": "QMS Prior Notification"},
    {"dt": "QMS Batch Record Details"},
    {"dt": "QMS Inspection Reports"},
    {"dt": "Workflow","filters": {"name": ["in", ["Earth Invoice Workflow"]]}},
    {"dt": "Workflow State","filters": {"name": ["in", ["Approve By Travel Desk","Reject By Travel Desk","Reject By Tyab Sir","Reject By Panjikar Sir","Approve By Panjikar Sir","Approve By Tyab Sir", "Approve By Earth Upload", "Reject By Earth Upload","Approve By Nirav Sir"]]}},
]
# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "vms.utils.jinja_methods",
# 	"filters": "vms.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "vms.install.before_install"
# after_install = "vms.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "vms.uninstall.before_uninstall"
# after_uninstall = "vms.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "vms.utils.before_app_install"
# after_app_install = "vms.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "vms.utils.before_app_uninstall"
# after_app_uninstall = "vms.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events


permission_query_conditions = {
    "Earth Invoice": "vms.vms.doctype.earth_invoice.earth_invoice.get_permission_query_conditions",
    # "Chat Room": "vms.chat_vms.doctype.chat_room.chat_room.get_permission_query_conditions",
    # "Chat Message": "vms.chat_vms.doctype.chat_message.chat_message.get_permission_query_conditions"
}

has_permission = {
    "Earth Invoice": "vms.vms.doctype.earth_invoice.earth_invoice.has_permission",
    # "Chat Room": "vms.chat_vms.doctype.chat_room.chat_room.has_permission",
    # "Chat Message": "vms.chat_vms.doctype.chat_message.chat_message.has_permission"
}


doc_events = {
    "Vendor Master": {
        "on_update": "vms.vendor_onboarding.vendor_document_management.vendor_master_on_update"
    },
    # "Vendor Onboarding":{
    #                      "before_save": "vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.set_vendor_onboarding_status"},
    "Purchase Requisition Form":{"on_update":"vms.APIs.sap.erp_to_sap_pr.onupdate_pr"},
    "Version":{"after_insert":"vms.overrides.versions.get_version_data_universal"},


    "Chat Message": {
        "after_insert": "vms.APIs.notification_chatroom.chat_apis.realtime_enhanced.handle_new_message_notification",
        "before_save": "vms.chat_vms.doctype.chat_message.chat_message.before_save_hook",
        "on_update": "vms.APIs.notification_chatroom.chat_apis.realtime_enhanced.handle_message_update_notification"
    },
    "Chat Room": {
        "after_insert": "vms.APIs.notification_chatroom.chat_apis.realtime_enhanced.handle_new_room_notification",
        "on_update": "vms.APIs.notification_chatroom.chat_apis.realtime_enhanced.handle_room_update_notification"
    },
    "Chat Room Member": {
        "after_insert": "vms.APIs.notification_chatroom.chat_apis.realtime_enhanced.handle_member_added_notification",
        "on_trash": "vms.APIs.notification_chatroom.chat_apis.realtime_enhanced.handle_member_removed_notification"
    },
    "User": {
        "on_update": "vms.chat_vms.maintenance.update_user_chat_permissions"
    }
}
# doc_events = {
# 	"*": {
# 		"on_update": "method",.py
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }


# Scheduled Tasks
# ---------------

scheduler_events_enhanced = {
    "all": [
        "vms.cron_jobs.sent_asa_form_link.sent_asa_form_link"
    ],
    "daily": [
        "vms.APIs.req_for_quotation.rfq_reminder.send_reminder_notification",
        "vms.chat_vms.maintenance.cleanup_old_messages",
        "vms.chat_vms.maintenance.update_room_statistics",
        "vms.APIs.notification_chatroom.chat_apis.realtime_enhanced.cleanup_user_status_cache"  # New
    ],
    "cron": {
        "*/10 * * * *": [
            "vms.APIs.req_for_quotation.rfq_reminder.block_quotation_link",
            "vms.APIs.sap.send_sap_error_email.uncheck_sap_error_email"  
        ],
        "0 2 * * *": [  # Run at 2 AM daily
            "vms.chat_vms.maintenance.cleanup_deleted_files"
        ],
        "*/15 * * * *": [  # Every 15 minutes
            "vms.chat_vms.maintenance.update_user_online_status"
        ],
        "*/1 * * * *": [  # Every minute - for real-time status updates
            "vms.APIs.notification_chatroom.chat_apis.realtime_enhanced.update_user_activity_status"
        ]
    }    
	# "hourly": [
	# 	"vms.tasks.hourly"
	# ],
	# "weekly": [
	# 	"vms.tasks.weekly"
	# ],
	# "monthly": [
	# 	"vms.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "vms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "vms.event.get_events"
# }

override_whitelisted_methods = {
    "vms.sync_vendor_documents": "vms.vendor_onboarding.vendor_document_management.sync_vendor_documents_on_approval",
    "vms.get_vendor_history": "vms.vendor_onboarding.vendor_document_management.get_vendor_document_history",
    "vms.restore_vendor_docs": "vms.vendor_onboarding.vendor_document_management.restore_from_onboarding",

    # Core Chat Room APIs (from APIs/notification_chatroom/chat_apis/)
    "vms.get_user_chat_rooms": "vms.APIs.notification_chatroom.chat_apis.chat_api.get_user_chat_rooms",
    "vms.create_chat_room": "vms.APIs.notification_chatroom.chat_apis.chat_api.create_chat_room",
    "vms.get_chat_messages": "vms.APIs.notification_chatroom.chat_apis.chat_api.get_chat_messages",
    "vms.send_message": "vms.APIs.notification_chatroom.chat_apis.chat_api.send_message",
    "vms.add_reaction": "vms.APIs.notification_chatroom.chat_apis.chat_api.add_reaction",
    "vms.edit_message": "vms.APIs.notification_chatroom.chat_apis.chat_api.edit_message",
    "vms.delete_message": "vms.APIs.notification_chatroom.chat_apis.chat_api.delete_message",
    
    # Room Management APIs
    "vms.get_room_details": "vms.APIs.notification_chatroom.chat_apis.room_management.get_room_details",
    "vms.add_room_member": "vms.APIs.notification_chatroom.chat_apis.room_management.add_room_member",
    "vms.remove_room_member": "vms.APIs.notification_chatroom.chat_apis.room_management.remove_room_member",
    "vms.update_member_role": "vms.APIs.notification_chatroom.chat_apis.room_management.update_member_role",
    "vms.mute_unmute_member": "vms.APIs.notification_chatroom.chat_apis.room_management.mute_unmute_member",
    "vms.update_room_settings": "vms.APIs.notification_chatroom.chat_apis.room_management.update_room_settings",
    "vms.archive_room": "vms.APIs.notification_chatroom.chat_apis.room_management.archive_room",
    "vms.search_users_for_room": "vms.APIs.notification_chatroom.chat_apis.room_management.search_users_for_room",
    "vms.get_team_chat_rooms": "vms.APIs.notification_chatroom.chat_apis.room_management.get_team_chat_rooms",
    "vms.join_team_room": "vms.APIs.notification_chatroom.chat_apis.room_management.join_team_room",
    
    # File Upload APIs
    "vms.upload_chat_file": "vms.APIs.notification_chatroom.chat_apis.file_upload.upload_chat_file",
    "vms.get_chat_file_preview": "vms.APIs.notification_chatroom.chat_apis.file_upload.get_chat_file_preview",
    
    # Real-time Event APIs
    "vms.join_chat_room": "vms.APIs.notification_chatroom.chat_apis.realtime_events.join_chat_room",
    "vms.leave_chat_room": "vms.APIs.notification_chatroom.chat_apis.realtime_events.leave_chat_room",
    "vms.send_typing_indicator": "vms.APIs.notification_chatroom.chat_apis.realtime_events.send_typing_indicator",
    "vms.get_online_users": "vms.APIs.notification_chatroom.chat_apis.realtime_events.get_online_users",
    
    # Search and Analytics APIs
    "vms.search_messages": "vms.APIs.notification_chatroom.chat_apis.search_analytics.search_messages",
    "vms.get_chat_analytics": "vms.APIs.notification_chatroom.chat_apis.search_analytics.get_chat_analytics",
    "vms.get_global_chat_search": "vms.APIs.notification_chatroom.chat_apis.search_analytics.get_global_chat_search",
    "vms.export_chat_messages": "vms.APIs.notification_chatroom.chat_apis.search_analytics.export_chat_messages",
    
    # Maintenance APIs (from chat_vms/maintenance.py)
    "vms.manual_cleanup_room": "vms.chat_vms.maintenance.manual_cleanup_room",
    "vms.get_room_storage_usage": "vms.chat_vms.maintenance.get_room_storage_usage",
    "vms.get_chat_system_stats": "vms.chat_vms.maintenance.get_chat_system_stats",
    "vms.optimize_chat_database": "vms.chat_vms.maintenance.optimize_chat_database",
    
    # Chat Utility APIs (from chat_vms DocType controllers)
    "vms.get_user_chat_status": "vms.chat_vms.doctype.chat_message.chat_message.get_user_chat_status",
    "vms.mark_room_as_read": "vms.chat_vms.doctype.chat_message.chat_message.mark_room_as_read",
    "vms.get_recent_chat_activity": "vms.chat_vms.doctype.chat_message.chat_message.get_recent_chat_activity"

}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["vms.utils.before_request"]
# after_request = ["vms.utils.after_request"]

# Job Events
# ----------
# before_job = ["vms.utils.before_job"]
# after_job = ["vms.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"vms.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

