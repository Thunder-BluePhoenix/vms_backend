# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, date_diff


def execute(filters=None):
    """
    Vendor Aging Detail Report with Purchase Order breakdown
    """
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    
    return columns, data, None, chart


def get_columns():
    """Define report columns"""
    return [
        {
            "label": _("Vendor Code"),
            "fieldname": "vendor_code",
            "fieldtype": "Link",
            "options": "Vendor Aging Tracker",
            "width": 120
        },
        {
            "label": _("Vendor Name"),
            "fieldname": "vendor_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Company"),
            "fieldname": "company_code",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Vendor Age (Days)"),
            "fieldname": "days_since_creation",
            "fieldtype": "Int",
            "width": 130
        },
        {
            "label": _("Aging Status"),
            "fieldname": "vendor_aging_status",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Status"),
            "fieldname": "vendor_status",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("PO Number"),
            "fieldname": "po_number",
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 130
        },
        {
            "label": _("PO Date"),
            "fieldname": "po_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("PO Age (Days)"),
            "fieldname": "days_since_po",
            "fieldtype": "Int",
            "width": 110
        },
        {
            "label": _("PO Status"),
            "fieldname": "po_status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("PO Value"),
            "fieldname": "po_value",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Delivery Date"),
            "fieldname": "delivery_date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": _("Days to Delivery"),
            "fieldname": "days_to_delivery",
            "fieldtype": "Int",
            "width": 120
        }
    ]


def get_data(filters):
    """Get report data with filters"""
    conditions = get_conditions(filters)
    
    data = []
    
    # Get all vendor aging trackers
    aging_trackers = frappe.db.sql(f"""
        SELECT 
            name,
            vendor_code,
            vendor_name,
            company_code,
            days_since_creation,
            vendor_aging_status,
            vendor_status,
            total_purchase_orders,
            total_po_value
        FROM `tabVendor Aging Tracker`
        WHERE 1=1 {conditions}
        ORDER BY days_since_creation DESC
    """, filters, as_dict=1)
    
    for tracker in aging_trackers:
        # Get PO details for this vendor
        po_details = frappe.db.sql("""
            SELECT 
                purchase_order,
                po_number,
                po_date,
                po_status,
                po_value,
                delivery_date,
                days_since_po,
                po_aging_status
            FROM `tabVendor Aging PO Details`
            WHERE parent = %(parent)s
            ORDER BY po_date DESC
        """, {"parent": tracker.name}, as_dict=1)
        
        if po_details:
            # Add rows for each PO
            for idx, po in enumerate(po_details):
                row = {
                    "vendor_code": tracker.vendor_code if idx == 0 else "",
                    "vendor_name": tracker.vendor_name if idx == 0 else "",
                    "company_code": tracker.company_code if idx == 0 else "",
                    "days_since_creation": tracker.days_since_creation if idx == 0 else "",
                    "vendor_aging_status": tracker.vendor_aging_status if idx == 0 else "",
                    "vendor_status": tracker.vendor_status if idx == 0 else "",
                    "po_number": po.purchase_order,
                    "po_date": po.po_date,
                    "days_since_po": po.days_since_po,
                    "po_status": po.po_status,
                    "po_value": po.po_value,
                    "delivery_date": po.delivery_date,
                    "days_to_delivery": calculate_days_to_delivery(po.delivery_date) if po.delivery_date else None,
                    "indent": 0 if idx == 0 else 1
                }
                data.append(row)
        else:
            # Vendor with no POs
            row = {
                "vendor_code": tracker.vendor_code,
                "vendor_name": tracker.vendor_name,
                "company_code": tracker.company_code,
                "days_since_creation": tracker.days_since_creation,
                "vendor_aging_status": tracker.vendor_aging_status,
                "vendor_status": tracker.vendor_status,
                "po_number": "-",
                "po_date": None,
                "days_since_po": None,
                "po_status": "No PO",
                "po_value": 0,
                "delivery_date": None,
                "days_to_delivery": None,
                "indent": 0
            }
            data.append(row)
    
    return data


def get_conditions(filters):
    """Build SQL conditions from filters"""
    conditions = ""
    
    if filters.get("company_code"):
        conditions += " AND company_code = %(company_code)s"
    
    if filters.get("vendor_status"):
        conditions += " AND vendor_status = %(vendor_status)s"
    
    if filters.get("vendor_aging_status"):
        conditions += " AND vendor_aging_status = %(vendor_aging_status)s"
    
    if filters.get("from_date"):
        conditions += " AND DATE(vendor_creation_date) >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND DATE(vendor_creation_date) <= %(to_date)s"
    
    if not filters.get("include_inactive"):
        conditions += " AND vendor_status != 'Inactive'"
    
    if filters.get("min_po_value"):
        conditions += " AND total_po_value >= %(min_po_value)s"
    
    return conditions


def calculate_days_to_delivery(delivery_date):
    """Calculate days remaining until delivery"""
    if not delivery_date:
        return None
    
    today = getdate()
    delivery = getdate(delivery_date)
    
    return date_diff(delivery, today)


def get_chart_data(data):
    """Generate chart data for aging distribution"""
    
    # Count vendors by aging status
    aging_distribution = {}
    for row in data:
        if row.get("vendor_aging_status") and row.get("vendor_code"):  # Only count vendor rows
            status = row["vendor_aging_status"]
            aging_distribution[status] = aging_distribution.get(status, 0) + 1
    
    return {
        "data": {
            "labels": list(aging_distribution.keys()),
            "datasets": [
                {
                    "name": "Vendor Count",
                    "values": list(aging_distribution.values())
                }
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#28a745", "#17a2b8", "#ffc107", "#dc3545"]
    }