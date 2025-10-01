import frappe
from frappe import _
import json
import base64


#vms.APIs.dispatch.get_gate_entry.gate_entry_get
@frappe.whitelist()
def gate_entry_get(name=None, filters=None, fields=None, limit=20, offset=0, order_by=None, search_term=None, company=None, status=None, get_all=False):

    try:
        if not frappe.has_permission("Gate Entry", "read"):
            frappe.response.http_status_code = 403
            return {"message": "Failed", "error": "You don't have permission to view Gate Entry"}

        # If name is provided, return single document details
        if name:
            doc = frappe.get_doc("Gate Entry", name)
            return get_gate_entry_data(doc)
        else:
            return get_gate_entry_list(filters, fields, limit, offset, order_by, search_term,company, status, get_all)
            
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Gate Entry Get Error")
        return {"message": "Failed", "error": str(e)}





def get_gate_entry_data(doc):
    data = {}
    meta = frappe.get_meta("Gate Entry")
    
    exclude_fieldtypes = [
        "Section Break", "Column Break", "Tab Break", 
        "HTML", "Heading", "Fold", "Button"
    ]
    
    for field in meta.fields:
        if field.fieldtype in exclude_fieldtypes:
            continue
            
        field_name = field.fieldname
        value = getattr(doc, field_name, None)

        vehicle_details = []
        if hasattr(doc, 'vehicle_details_item') and doc.vehicle_details_item:  
            for vehicle_row in doc.vehicle_details_item:
                vehicle_link = vehicle_row.get('vehicle_details') 
                driver_name = vehicle_row.get('driver_name')
                driver_info = {"driver_name": driver_name} if driver_name else {}

                
                if vehicle_link:
                    try:
                        vehicle_doc = frappe.get_doc("Vehicle Details", vehicle_link) 
                        vehicle_info = {
                            "name": vehicle_doc.name,
                            "vehicle_no": vehicle_doc.get('vehicle_no'),
                            "driver_name": driver_name or vehicle_doc.get('driver_name'),
                            "driver_phone": vehicle_doc.get('driver_phone'),
                            "driver_license": vehicle_doc.get('driver_license'),
                            "loading_state": vehicle_doc.get('loading_state'),
                            "loading_location": vehicle_doc.get('loading_location'),
                            "transporter_name": vehicle_doc.get('transporter_name'),
                            "destination_plant": vehicle_doc.get('destination_plant'),
                            "lr_number": vehicle_doc.get('lr_number'),
                            "lr_date": vehicle_doc.get('lr_date'),
                            "vehicle_type": vehicle_doc.get('vehicle_type'),
                            "attachment": vehicle_doc.get('attachment')
                        }
                        vehicle_details.append(vehicle_info)
                       
                    except frappe.DoesNotExistError:
                        vehicle_details.append({"error": f"Vehicle {vehicle_link} not found"})
                    except Exception as vehicle_error:
                        vehicle_details.append({"error": str(vehicle_error)})
        
        
        # data["vehicle_details_item"] = vehicle_details
        
        if field.fieldtype == "Table" and value:
            child_data = []
            for child in value:
                child_dict = child.as_dict()
                child_data.append(child_dict)
            data[field_name] = child_data
       
        else:
            data[field_name] = value
        data["vehicle_details_item"] = vehicle_details
    
    return data


@frappe.whitelist()
def get_gate_entry_list(
    filters=None,
    fields=None,
    limit=20,
    offset=0,
    order_by=None,
    search_term=None,
    company=None,
    status=None,
    get_all=False  
):
    try:
       
        if not frappe.has_permission("Gate Entry", "read"):
            frappe.response.http_status_code = 403
            return {"message": "Failed", "error": "You don't have permission to view Gate Entry"}

        # Parse filters if they're passed as JSON string
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Parse fields if they're passed as JSON string
        if isinstance(fields, str):
            fields = json.loads(fields) if fields else ["name","inward_location","gate_entry_date","status","vendor","name_of_vendor","handover_to_person"]
        elif fields is None:
            fields = ["name","inward_location","gate_entry_date","status","vendor","name_of_vendor","handover_to_person"]

        # Convert parameters to proper types
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        # Convert get_all to boolean
        if isinstance(get_all, str):
            get_all = get_all.lower() in ['true', '1', 'yes']
        
        # Set default order_by if not provided
        if not order_by:
            order_by = "modified desc"

        # Build search filters
        search_filters = filters.copy()
        
        # Add company filter if provided
        if company:
            search_filters["name_of_company"] = company
        
        # Add status filter if provided
        if status:
            search_filters["status"] = status
        
        or_filters = None
        if search_term:
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["gate_entry_no", "like", f"%{search_term}%"],
                ["vendor", "like", f"%{search_term}%"],
                ["name_of_vendor", "like", f"%{search_term}%"],
                ["name_of_company", "like", f"%{search_term}%"],
                ["handover_to_person", "like", f"%{search_term}%"]
            ]

        # Prepare parameters for get_list
        list_params = {
            "doctype": "Gate Entry",
            "filters": search_filters,
            "fields": fields,
            "order_by": order_by,
            "ignore_permissions": False
        }
        
        # Add OR filters if search term exists
        if or_filters:
            list_params["or_filters"] = or_filters
        
        # Add pagination only if not getting all records
        if not get_all:
            list_params["limit"] = limit
            list_params["start"] = offset

        # Get list of documents
        documents = frappe.get_list(**list_params)

        # Get total count for pagination
        if or_filters:
            total_count = len(frappe.get_all(
                "Gate Entry",
                filters=search_filters,
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            total_count = frappe.db.count("Gate Entry", search_filters)

        # Build response
        response = {
            "message": "Success",
            "data": documents
        }
        
        # Add pagination only if not getting all records
        if not get_all:
            response["pagination"] = {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count,
                "has_previous": offset > 0
            }
        else:
            response["total_count"] = total_count

        return response

    except json.JSONDecodeError:
        frappe.response.http_status_code = 400
        return {"message": "Failed", "error": "Invalid JSON in filters or fields"}
    
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Gate Entry List Error")
        return {"message": "Failed", "error": str(e)}


#vms.APIs.dispatch.get_gate_entry.get_gate_entry_statistics
@frappe.whitelist()
def get_gate_entry_statistics(filters=None):
    try:
        # Check permission
        if not frappe.has_permission("Gate Entry", "read"):
            frappe.response.http_status_code = 403
            return {"message": "Failed", "error": "You don't have permission to view Gate Entry statistics"}

        # Parse filters if JSON string
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Get total count
        total_count = frappe.db.count("Gate Entry", filters)

        # Get company-wise count
        company_wise_sql = """
            SELECT 
                name_of_company as company,
                COUNT(*) as count
            FROM 
                `tabGate Entry`
            {where_clause}
            GROUP BY 
                name_of_company
            ORDER BY 
                count DESC
        """

        # Get status-wise count
        status_wise_sql = """
            SELECT 
                status,
                COUNT(*) as count
            FROM 
                `tabGate Entry`
            {where_clause}
            GROUP BY 
                status
            ORDER BY 
                count DESC
        """

        # Get company and status matrix (combined)
        company_status_matrix_sql = """
            SELECT 
                name_of_company as company,
                status,
                COUNT(*) as count
            FROM 
                `tabGate Entry`
            {where_clause}
            GROUP BY 
                name_of_company, status
            ORDER BY 
                name_of_company, status
        """

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

        # Execute queries
        company_wise_count = frappe.db.sql(
            company_wise_sql.format(where_clause=where_clause),
            sql_params,
            as_dict=True
        )

        status_wise_count = frappe.db.sql(
            status_wise_sql.format(where_clause=where_clause),
            sql_params,
            as_dict=True
        )

        company_status_matrix = frappe.db.sql(
            company_status_matrix_sql.format(where_clause=where_clause),
            sql_params,
            as_dict=True
        )

        # Enhance company-wise count with company names
        for item in company_wise_count:
            if item.get("company"):
                company_name = frappe.db.get_value(
                    "Company Master",
                    item["company"],
                    "company_name"
                )
                company_code = frappe.db.get_value(
                    "Company Master",
                    item["company"],
                    "company_code"
                )
                item["company_name"] = company_name
                item["company_code"] = company_code

        # Enhance matrix with company names
        for item in company_status_matrix:
            if item.get("company"):
                company_name = frappe.db.get_value(
                    "Company Master",
                    item["company"],
                    "company_name"
                )
                item["company_name"] = company_name

        return {
            "message": "Success",
            "data": {
                "total_count": total_count,
                "company_wise_count": company_wise_count,
                "status_wise_count": status_wise_count,
                # "company_status_matrix": company_status_matrix
            }
        }

    except json.JSONDecodeError:
        frappe.response.http_status_code = 400
        return {"message": "Failed", "error": "Invalid JSON in filters"}
    
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Gate Entry Statistics Error")
        return {"message": "Failed", "error": str(e)}

