// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

// Copyright (c) 2025
// For license information, please see license.txt

frappe.query_reports["Product Inquiry Details"] = {
    "filters": [
        {
            "fieldname": "cart_id",
            "label": "Cart ID",
            "fieldtype": "Link",
            "options": "Cart Details",
            "reqd": 0
        },
        {
            "fieldname": "user",
            "label": "User",
            "fieldtype": "Data",
            "reqd": 0
        },
        {
            "fieldname": "cart_date",
            "label": "Cart Date",
            "fieldtype": "Date",
            "reqd": 0
        },
        {
            "fieldname": "product_name",
            "label": "Product Name",
            "fieldtype": "Link",
			"options": "VMS Product Master",
            "reqd": 0
        }
    ]
};

