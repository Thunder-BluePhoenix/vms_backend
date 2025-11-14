# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
import datetime


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Cart ID", "fieldname": "cart_id", "fieldtype": "Link", "options": "Cart Details", "width": 120},
        {"label": "User", "fieldname": "user", "fieldtype": "Data", "width": 150},
        {"label": "Cart Date", "fieldname": "cart_date", "fieldtype": "Date", "width": 120},
        {"label": "PR Form Created", "fieldname": "pr_created", "fieldtype": "Check", "width": 120},
        {"label": "PR Form", "fieldname": "pr_form", "fieldtype": "Link", "options": "Purchase Requisition Webform", "width": 150},
        {"label": "Product Name", "fieldname": "product_name", "fieldtype": "Link", "options": "VMS Product Master", "width": 150},
        {"label": "Product Price", "fieldname": "product_price", "fieldtype": "Data", "width": 180},
        {"label": "Final Price by Purchase Team", "fieldname": "final_price", "fieldtype": "Currency", "width": 160},
        {"label": "Quantity", "fieldname": "quantity", "fieldtype": "Int", "width": 80},
    ]


def get_data(filters):
    data = []
    parent_filters = {}

    if filters.get("cart_id"):
        parent_filters["name"] = filters.get("cart_id")

    if filters.get("user"):
        parent_filters["user"] = ["like", f"%{filters.get('user')}%"]

    if filters.get("cart_date"):
        parent_filters["cart_date"] = filters.get("cart_date")

    cart_list = frappe.get_all(
        "Cart Details",
        fields=["name", "user", "cart_date", "purchase_requisition_form_created", "purchase_requisition_form"],
        filters=parent_filters
    )

    for cart in cart_list:

        child_filters = {"parent": cart.name}

        if filters.get("product_name"):
            child_filters["product_name"] = filters.get("product_name")

        products = frappe.get_all(
            "Cart Master",
            filters=child_filters,
            fields=[
                "product_name",
                "product_price",
                "final_price_by_purchase_team",
                "product_quantity"
            ]
        )

        if products:
            for item in products:
                data.append({
                    "cart_id": cart.name,
                    "user": cart.user,
                    "cart_date": cart.cart_date,
                    "pr_created": cart.purchase_requisition_form_created,
                    "pr_form": cart.purchase_requisition_form,

                    "product_name": item.product_name,
                    "product_price": item.product_price,
                    "final_price": item.final_price_by_purchase_team,
                    "quantity": item.product_quantity,
                })
        else:
            if filters.get("product_name"):
                continue

            data.append({
                "cart_id": cart.name,
                "user": cart.user,
                "cart_date": cart.cart_date,
                "pr_created": cart.purchase_requisition_form_created,
                "pr_form": cart.purchase_requisition_form,

                "product_name": "",
                "product_price": "",
                "final_price": "",
                "quantity": "",
            })

    return data
