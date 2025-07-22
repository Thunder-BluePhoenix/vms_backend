import frappe
from frappe import _
from frappe.utils import nowdate, now_datetime
import json


@frappe.whitelist(allow_guest=False)
def update_purchase_team_remarks(data):
    """
    API to update purchase team remarks and early delivery date for PO items
    
    Expected data structure:
    {
        "po_name": "PO-XXXX",
        "items": [
            {
                "name": "row-id-12345",  # Child table row ID
                "purchase_team_remarks": "Remarks text",
                "early_delivery_date": "2024-01-15"
            }
        ]
    }
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        po_name = data.get("po_name")
        items_data = data.get("items", [])
        
        if not po_name:
            frappe.throw(_("Purchase Order name is required"))
        
        if not items_data:
            frappe.throw(_("Items data is required"))
        
        # Get the Purchase Order document
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Create a mapping of child row name (ID) to item data for quick lookup
        update_items = {item.get("name"): item for item in items_data}
        
        # Update the child table items
        updated_count = 0
        for po_item in po.po_items:
            if po_item.name in update_items:
                item_update = update_items[po_item.name]
                
                # Update purchase team remarks
                if "purchase_team_remarks" in item_update:
                    po_item.purchase_team_remarks = item_update.get("purchase_team_remarks")
                
                # Update early delivery date
                if "early_delivery_date" in item_update:
                    po_item.early_delivery_date = item_update.get("early_delivery_date")
                
                updated_count += 1
        
        # Save the document
        po.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": _("Purchase team remarks updated successfully"),
            "po_name": po_name,
            "updated_items": updated_count
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Purchase Team Remarks Error")
        return {
            "status": "error",
            "message": _("Error updating purchase team remarks: {0}").format(str(e))
        }


@frappe.whitelist(allow_guest=False)
def update_vendor_approval_status(data):
    """
    API to update vendor approval status and remarks for PO items
    
    Expected data structure:
    {
        "po_name": "PO-XXXX",
        "items": [
            {
                "name": "row-id-12345",  # Child table row ID
                "approved_by_vendor": 1,
                "rejected_by_vendor": 0,
                "vendor_remarks": "Approved with conditions"
            }
        ]
    }
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        po_name = data.get("po_name")
        items_data = data.get("items", [])
        
        if not po_name:
            frappe.throw(_("Purchase Order name is required"))
        
        if not items_data:
            frappe.throw(_("Items data is required"))
        
        # Get the Purchase Order document
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Create a mapping of child row name (ID) to item data for quick lookup
        update_items = {item.get("name"): item for item in items_data}
        
        # Update the child table items
        updated_count = 0
        for po_item in po.po_items:
            if po_item.name in update_items:
                item_update = update_items[po_item.name]
                
                # Update vendor approval fields
                if "approved_by_vendor" in item_update:
                    po_item.approved_by_vendor = item_update.get("approved_by_vendor")
                
                if "rejected_by_vendor" in item_update:
                    po_item.rejected_by_vendor = item_update.get("rejected_by_vendor")
                
                if "vendor_remarks" in item_update:
                    po_item.vendor_remarks = item_update.get("vendor_remarks")
                
                updated_count += 1
        
        # Save the document
        po.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": _("Vendor approval status updated successfully"),
            "po_name": po_name,
            "updated_items": updated_count
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Vendor Approval Status Error")
        return {
            "status": "error",
            "message": _("Error updating vendor approval status: {0}").format(str(e))
        }


@frappe.whitelist(allow_guest=False)
def get_purchase_order_items(data):
    """
    API to get all child table data of a Purchase Order as complete dictionaries
    
    Expected data structure:
    {
        "po_name": "PO-XXXX"
    }
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        po_name = data.get("po_name")
        
        if not po_name:
            frappe.throw(_("Purchase Order name is required"))
        
        # Get the Purchase Order document
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Prepare items data - return complete item dictionaries
        items_data = []
        
        for item in po.po_items:
            # Get the complete item as dictionary
            item_dict = item.as_dict()
            items_data.append(item_dict)
        
        # Also get main PO data as dictionary
        po_dict = po.as_dict()
        
        return {
            "status": "success",
            # "po_data": po_dict,  # Complete PO document as dict
            "items": items_data,  # Complete items as dict array
            "total_items": len(items_data)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Purchase Order Items Error")
        return {
            "status": "error",
            "message": _("Error getting purchase order items: {0}").format(str(e))
        }

# Alternative method if you prefer to pass po_name as URL parameter
@frappe.whitelist(allow_guest=False)
def get_purchase_order_items_by_name(po_name):
    """
    Alternative API to get all child table data by passing po_name as parameter
    Usage: /api/method/your_app.purchase_order.get_purchase_order_items_by_name?po_name=PO-XXXX
    """
    return get_purchase_order_items({"po_name": po_name})


# Utility API to update single item by child row ID
@frappe.whitelist(allow_guest=False)
def update_single_po_item_by_id(data):
    """
    Utility API to update a single PO item by its child row ID
    
    Expected data structure:
    {
        "po_name": "PO-XXXX",
        "item_id": "row-id-12345",
        "fields": {
            "purchase_team_remarks": "New remarks",
            "early_delivery_date": "2024-01-15",
            "approved_by_vendor": 1,
            "vendor_remarks": "Approved"
        }
    }
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
            
        po_name = data.get("po_name")
        item_id = data.get("item_id")
        fields_to_update = data.get("fields", {})
        
        if not po_name:
            frappe.throw(_("Purchase Order name is required"))
        
        if not item_id:
            frappe.throw(_("Item ID is required"))
            
        if not fields_to_update:
            frappe.throw(_("Fields to update are required"))
        
        # Get the Purchase Order document
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Find the specific item by ID
        item_found = False
        for po_item in po.po_items:
            if po_item.name == item_id:
                # Update only the provided fields
                for field_name, field_value in fields_to_update.items():
                    if hasattr(po_item, field_name):
                        setattr(po_item, field_name, field_value)
                
                item_found = True
                break
        
        if not item_found:
            frappe.throw(_("Item with ID {0} not found in Purchase Order {1}").format(item_id, po_name))
        
        # Save the document
        po.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": _("Purchase Order item updated successfully"),
            "po_name": po_name,
            "item_id": item_id,
            "updated_fields": list(fields_to_update.keys())
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Single PO Item Error")
        return {
            "status": "error",
            "message": _("Error updating purchase order item: {0}").format(str(e))
        }