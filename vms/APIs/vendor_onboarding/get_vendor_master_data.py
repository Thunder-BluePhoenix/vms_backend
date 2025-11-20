import frappe
from frappe import _
from vms.utils.validators import validate_string


#vms.APIs.vendor_onboarding.get_vendor_master_data.get_vendors_by_name
@frappe.whitelist(methods=["GET"])
def get_vendors_by_name(vendor_name):

    vendor_name = validate_string(vendor_name, field_name="Vendor name")

    
    try:
        
        # Fetch vendors matching the name pattern
        vendors = fetch_vendors_by_name_pattern(vendor_name)
        if not vendors:
            frappe.local.response["http_status_code"] = 404
            return {
                'status': 'error',
                'message': 'No vendors found matching the given name'
            }
        
        for vendor in vendors:
            if not frappe.has_permission('Vendor Master', 'read', vendor.get('name')):
                frappe.throw(_("Insufficient permissions"), frappe.PermissionError)
            vendor['gst_data'] = get_latest_gst_details(vendor.get('name'))
        
        return {
            'status': 'success',
            'data': vendors,
            'count': len(vendors)
        }
    
    except (frappe.ValidationError, frappe.PermissionError):
        raise
    
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title='Get Vendors API Error'
        )
        frappe.throw(
            _("An error occurred while fetching vendor data"),
            frappe.ValidationError
        )


def fetch_vendors_by_name_pattern(vendor_name):
    vendors = frappe.db.get_all(
        'Vendor Master',
        filters={
            'vendor_name': ['like', f'%{vendor_name}%']
        },
        fields=[
            'name', 
            'vendor_name', 
            'office_email_primary', 
            'country', 
            'first_name', 
            'mobile_number', 
            'search_term'
        ],
        order_by='vendor_name asc',
        limit_page_length=0
    )
    
    return vendors

def get_latest_gst_details(vendor_name):
    try:
       
        legal_doc = frappe.db.get_all(
            'Legal Documents',
            filters={'ref_no': vendor_name},
            fields=['name'],
            order_by='creation desc',
            limit=1
        )
        
        
        if not legal_doc:
            return []
        
        legal_doc_name = legal_doc[0].get('name')
        pan_number = legal_doc[0].get('pan_number')
        
        
       
        gst_details = frappe.db.get_all(
            'GST Details Table',  
            filters={'parent': legal_doc_name},
            fields=['gst_state', 'gst_number', 'pincode','company'],  
            order_by='idx asc'
        )
    
        
        return {
            'pan_number': pan_number,
            'gst_details': gst_details
        }
    
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f'Get GST Details Error for {vendor_name}'
        )
        return []