import frappe

@frappe.whitelist(allow_guest=True)
def dispatch_dashboard(page_no=None, page_length=None, status=None):
    try:
        user = frappe.session.user
        roles = frappe.get_roles(user)

        filters = {}
        if status:
            filters["status"] = status

        if "Purchase Team" in roles:
            pass  # No filter, show all
        elif "Vendor" in roles:
            filters["owner"] = user
        else:
            return {
                "status": "error",
                "message": "User does not have access to view this data.",
                "dispatches": []
            }

        # Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length

        total_count = frappe.db.count("Dispatch Item", filters)

        dispatch_docs = frappe.get_all(
            "Dispatch Item",
            filters=filters,
            fields=["name", "invoice_number", "invoice_date", "invoice_amount", "status", "owner"],
            limit_start=offset,
            limit_page_length=page_length
        )

        dispatches = []
        for doc in dispatch_docs:
            dispatch_doc = frappe.get_doc("Dispatch Item", doc.name)
            purchase_numbers = [row.purchase_number for row in dispatch_doc.purchase_number or []]

            dispatches.append({
                "name": doc.name,
                "invoice_number": doc.invoice_number,
                "invoice_date": doc.invoice_date,
                "invoice_amount": doc.invoice_amount,
                "owner": doc.owner,
                "status": doc.status,
                "purchase_numbers": purchase_numbers
            })

        return {
            "status": "success",
            "message": "Dispatch data fetched successfully.",
            "dispatches": dispatches,
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dispatch Dashboard Error")
        return {
            "status": "error",
            "message": "Failed to fetch dispatch data.",
            "error": str(e)
        }
