import json

import frappe
from frappe.model.document import Document

# vms.APIs.gr_waiver.get_gr_waiver.get_gr_waiver_details
@frappe.whitelist(methods=["GET"])
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
        
        # Get all attach/image fields from the doctype
        meta = frappe.get_meta("GR Waiver")
        attach_fields = [df.fieldname for df in meta.fields if df.fieldtype in ['Attach', 'Attach Image']]
        
        # Replace file URLs with detailed file information
        for field in attach_fields:
            file_url = doc_dict.get(field)
            if file_url:
                try:
                    # Get file document details
                    file_doc = frappe.get_all(
                        "File",
                        filters={
                            "file_url": file_url,
                            "attached_to_doctype": "GR Waiver",
                            "attached_to_name": name
                        },
                        fields=["name", "file_name", "file_url", "file_size", "is_private", "creation"]
                    )
                    
                    if file_doc:
                        file_info = file_doc[0]
                        # Replace the file field with detailed information
                        doc_dict[field] = {
                            "file_url": file_info.get("file_url"),
                            "file_name": file_info.get("file_name"),
                            "file_size": file_info.get("file_size"),
                            "is_private": file_info.get("is_private"),
                            "uploaded_on": file_info.get("creation"),
                            "full_url": frappe.utils.get_url() + file_info.get("file_url") if file_info.get("file_url") else None
                        }
                    else:
                        # If file document not found, provide basic info
                        doc_dict[field] = {
                            "file_url": file_url,
                            "full_url": frappe.utils.get_url() + file_url if file_url else None
                        }
                except Exception as file_error:
                    frappe.log_error(
                        f"Error fetching file details for field {field}: {str(file_error)}",
                        "GR Waiver File Details Error"
                    )
                    # Keep basic URL if detailed fetch fails
                    doc_dict[field] = {
                        "file_url": file_url,
                        "full_url": frappe.utils.get_url() + file_url if file_url else None
                    }
        
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
        frappe.log_error(frappe.get_traceback(), "GR Waiver Get Details Error")
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