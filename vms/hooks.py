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
# app_include_css = "/assets/vms/css/vms.css"
# app_include_js = "/assets/vms/js/vms.js"
app_include_js = [
    "assets/vms/js/earth_invoice_list.js"  
]

# include js, css files in header of web template
# web_include_css = "/assets/vms/css/vms.css"
# web_include_js = "/assets/vms/js/vms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

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
    {"dt": "Role", "filters": {"name": ["in", ["Purchase Team", "Accounts Team", "Purchase Head", "QA Team", "QA Head", "Vendor", "Panjikar","Tyab", "Super Head", "Accounts Head", "ASA", "IT Head","International Air Accounts","Domestic Air Accounts","Hotel Accounts","Bus Accounts","Railway Accounts"]]}},
    {"dt": "Role Profile", "filters": {"name" :["in", ["Accounts Head", "Super Head", "Accounts Team", "Enquirer", "Purchase Head", "Purchase Team", "Vendor", "QA Team", "QA Head"]]}},
    {"dt": "Module Profile", "filters": {"name": ["in", ["Vendor"]]}},
    {"dt": "QMS Quality Control System"},
    {"dt": "QMS Procedure Doc Name"},
    {"dt": "QMS Prior Notification"},
    {"dt": "QMS Batch Record Details"},
    {"dt": "QMS Inspection Reports"},
    {"dt": "Workflow","filters": {"name": ["in", ["Earth Invoice Workflow"]]}},
    {"dt": "Workflow State","filters": {"name": ["in", ["Approve By Travel Desk","Reject By Travel Desk","Reject By Tyab Sir","Reject By Panjikar Sir","Approve By Panjikar Sir","Approve By Tyab Sir", "Approve By Earth Upload", "Reject By Earth Upload"]]}},
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
    "Earth Invoice": "vms.APIs.import_api.premission_api.get_permission_query_conditions"
}

has_permission = {
    "Earth Invoice": "vms.APIs.import_api.premission_api.has_permission"
}


doc_events = {
    "Vendor Master": {
        "on_update": "vms.vendor_onboarding.vendor_document_management.vendor_master_on_update"
    },
    "Vendor Onboarding":{"on_update": ["vms.APIs.sap.sap.update_sap_vonb",
                                       "vms.vendor_onboarding.vendor_document_management.on_vendor_onboarding_submit"],
                         "before_save": "vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding.set_vendor_onboarding_status"},
    "Purchase Requisition Form":{"on_update":"vms.APIs.sap.erp_to_sap_pr.onupdate_pr"},
    "Version":{"after_insert":"vms.overrides.versions.get_version_data_universal"},
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

scheduler_events = {
	"all": [
		"vms.cron_jobs.sent_asa_form_link.sent_asa_form_link"
	],
	"daily": [
        "vms.APIs.req_for_quotation.rfq_reminder.send_reminder_notification"
	    # "vms.cron_jobs.sent_asa_form_link.sent_asa_form_link"
	],
	"cron": {
        "*/10 * * * *": [
            "vms.APIs.req_for_quotation.rfq_reminder.block_quotation_link"
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
    "vms.restore_vendor_docs": "vms.vendor_onboarding.vendor_document_management.restore_from_onboarding"
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

