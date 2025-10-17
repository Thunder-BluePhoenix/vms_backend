import json

import frappe
from frappe.model.document import Document

# vms.APIs.gr_waiver.get_gr_waiver.get_gr_waiver_details
@frappe.whitelist()
def get_gr_waiver_details(name):
    try:
        # Check if name parameter is provided
        if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Document name is required"}

        # Get the document
        gr_waiver = frappe.get_doc("GR Waiver", name)
        
        # Convert to dictionary and include all fields
        doc_dict = gr_waiver.as_dict()
        
        return {
            "message": "Success",
            "data": doc_dict
        }

    except frappe.DoesNotExistError:
        frappe.response.http_status_code = 404
        return {"message": "Failed", "error": "Document not found"}
    
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}



# vms.APIs.gr_waiver.get_gr_waiver.get_gr_waiver_list
@frappe.whitelist()
def get_gr_waiver_list(filters=None, fields=None, limit=20, offset=0, order_by=None):
    try:
        # Parse filters if they're passed as JSON string
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Parse fields if they're passed as JSON string
        if isinstance(fields, str):
            fields = json.loads(fields) if fields else ["*"]
        elif fields is None:
            fields = ["*"]

        # Convert limit and offset to integers
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        # Set default order_by if not provided
        if not order_by:
            order_by = "creation desc"

        # Get list of documents with filters
        documents = frappe.get_list(
            "GR Waiver",
            filters=filters,
            fields=fields,
            limit=limit,
            start=offset,
            order_by=order_by,
            ignore_permissions=False 
        )

        # Get total count for pagination
        total_count = frappe.db.count("GR Waiver", filters)

        return {
            "message": "Success",
            "data": documents,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count,
                "has_previous": offset > 0
            }
        }

    except json.JSONDecodeError:
        frappe.response.http_status_code = 400
        return {"message": "Failed", "error": "Invalid JSON in filters or fields"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}


# vms.APIs.gr_waiver.get_gr_waiver.get_gr_waiver_statistics
@frappe.whitelist()
def get_gr_waiver_statistics(filters=None):
    try:
        # Check permission
        if not frappe.has_permission("GR Waiver", "read"):
            frappe.response.http_status_code = 403
            return {"message": "Failed", "error": "You don't have permission to view GR Waiver statistics"}

        # Parse filters if JSON string
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Build WHERE clause from filters
        where_conditions = []
        sql_params = {}
        
        if filters:
            for key, value in filters.items():
                where_conditions.append(f"`{key}` = %({key})s")
                sql_params[key] = value
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # Initialize response data
        data = {}

        # Get total count
        total_count = frappe.db.count("GR Waiver", filters)
        data["total_count"] = total_count

        # Get all companies from Company Master
        all_companies = frappe.get_all(
            "Company Master",
            fields=["name", "company_code", "company_name","company_short_form"],
            order_by="company_code"
        )

        # Get company-wise counts
        company_counts_sql = f"""
            SELECT 
                division as company,
                COUNT(*) as count
            FROM 
                `tabGR Waiver`
            {where_clause}
            GROUP BY 
                company
        """
        
        company_counts = frappe.db.sql(
            company_counts_sql,
            sql_params,
            as_dict=True
        )
        
        # Convert to dictionary for easy lookup
        company_count_dict = {item["company"]: item["count"] for item in company_counts}

        # Add count object for each company
        for company in all_companies:
            company_code = company.get("company_code") or company.get("name")
            company_name = company.get("company_name") or ""
            company_id = company.get("name")
            short_name = company.get("company_short_form") or ""
            count = company_count_dict.get(company_id, 0)
            
            # Create key from company_code
            if company_code:
                key = f"{company_id.lower().replace(' ', '_').replace('-', '_')}_count"
            else:
                key = f"{company_code.lower().replace(' ', '_').replace('-', '_')}_count"
            
            # Store as object with details
            data[key] = {
                "name": company_id,
                "company_code": company_code,
                "company_name": company_name,
                "short_name": short_name,
                "count": count
                
            }

        return {
            "message": "Success",
            "data": data
        }

    except json.JSONDecodeError:
        frappe.response.http_status_code = 400
        return {"message": "Failed", "error": "Invalid JSON in filters"}
    
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "GR Waiver Statistics Error")
        return {"message": "Failed", "error": str(e)}