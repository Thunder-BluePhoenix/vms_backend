import json
import frappe
from frappe import _


#vms.APIs.master_apis.material_type.get_material_type_master_details
@frappe.whitelist()
def get_material_type_master_details(name):
    try:
        if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Document name is required"}

        
        doc = frappe.get_doc("Material Type Master", name)

       
        valuation_rows = []
        for row in doc.valuation_and_profit:
            valuation_class_description = ""
            if row.valuation_class:
                valuation_class_description = frappe.get_value(
                    "Valuation Class Master",
                    row.valuation_class,
                    "valuation_class_name"
                ) or ""
            
            profit_center_description = ""
            if row.profit_center:
                profit_center_description = frappe.get_value(
                    "Profit Center Master",
                    row.profit_center,
                    "description"
                ) or ""

            division_code = ""
            division_description = ""
            if row.division:
                division_code = frappe.get_value(
                    "Division Master",
                    row.division,
                    "division_code"
                ) or ""
                division_description = frappe.get_value(
                    "Division Master",
                    row.division,
                    "description"
                ) or ""

            valuation_rows.append({
                "valuation_class": row.valuation_class,
                "valuation_class_description": valuation_class_description,
                "profit_center": row.profit_center,
                "profit_center_description": profit_center_description,
                "division": row.division,
                "division_name": " - ".join(filter(None, [division_code, division_description])),
                "company": row.company,
            })

     
        company_rows = []
        for row in doc.multiple_company:
            company_name = ""
            if row.code_of_company:
                company_name = frappe.get_value(
                    "Company Master",
                    row.code_of_company,
                    "company_name"
                ) or ""
            company_rows.append({
                "company": row.code_of_company,
                "company_name": company_name,
            })

        
        storage_rows = []
        for row in doc.storage_location_table:
            storage_desc = ""
            if row.storage_location:
                storage_desc = frappe.get_value(
                    "Storage Location Master",
                    row.storage_location,
                    "storage_location_name"
                ) or ""
            storage_rows.append({
                "storage_location": row.storage_location,
                "storage_name": storage_desc,
            })

     
        result = {
            "name": doc.name,
            "material_type_name": doc.material_type_name,
            "description": doc.description,
            "company": doc.company,
            "material_category_type": doc.material_category_type,
            "valuation_and_profit": valuation_rows,
            "multiple_company": company_rows,
            "storage_location_table": storage_rows,
        }

        return {
            "message": "Success",
            "data": result
        }

    except frappe.DoesNotExistError:
        frappe.response.http_status_code = 404
        return {"message": "Failed", "error": "Material Type Master not found"}
    
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Material Type Master Detail Error")
        return {"message": "Failed", "error": str(e)}

#vms.APIs.master_apis.material_type.get_material_type_master_list
@frappe.whitelist()
def get_material_type_master_list(
    filters=None,
    fields=None,
    limit=20,
    offset=0,
    order_by=None,
    search_term=None,
    include_child_tables=True
):
    try:
        
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

       
        if isinstance(fields, str):
            fields = json.loads(fields) if fields else [
                "name", "material_type_name", "description",
                "company", "material_category_type"
            ]
        elif fields is None:
            fields = [
                "name", "material_type_name", "description",
                "company", "material_category_type"
            ]

        
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        
        if isinstance(include_child_tables, str):
            include_child_tables = include_child_tables.lower() in ['true', '1', 'yes']
        
       
        if not order_by:
            order_by = "creation desc"

      
        search_filters = filters.copy()
        or_filters = None
        
        if search_term:
           
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["material_type_name", "like", f"%{search_term}%"],
                ["description", "like", f"%{search_term}%"]
            ]

     
        if or_filters:
            documents = frappe.get_list(
                "Material Type Master",
                filters=search_filters,
                or_filters=or_filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=True
            )
            
        
            total_count = len(frappe.get_all(
                "Material Type Master",
                filters=search_filters,
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            documents = frappe.get_list(
                "Material Type Master",
                filters=search_filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=True
            )
            
          
            total_count = frappe.db.count("Material Type Master", search_filters)

      
        if include_child_tables:
            result = []
            for item in documents:
                doc = frappe.get_doc("Material Type Master", item.name)

               
                valuation_rows = []
                for row in doc.valuation_and_profit:
                    valuation_class_description = ""
                    if row.valuation_class:
                        valuation_class_description = frappe.get_value(
                            "Valuation Class Master",
                            row.valuation_class,
                            "valuation_class_name"
                        ) or ""
                    
                    profit_center_description = ""
                    if row.profit_center:
                        profit_center_description = frappe.get_value(
                            "Profit Center Master",
                            row.profit_center,
                            "description"
                        ) or ""

                    division_code = ""
                    division_description = ""
                    if row.division:
                        division_code = frappe.get_value(
                            "Division Master",
                            row.division,
                            "division_code"
                        ) or ""
                        division_description = frappe.get_value(
                            "Division Master",
                            row.division,
                            "description"
                        ) or ""

                    valuation_rows.append({
                        "valuation_class": row.valuation_class,
                        "valuation_class_description": valuation_class_description,
                        "profit_center": row.profit_center,
                        "profit_center_description": profit_center_description,
                        "division": row.division,
                        "division_name": " - ".join(filter(None, [division_code, division_description])),
                        "company": row.company,
                    })

                
                company_rows = []
                for row in doc.multiple_company:
                    company_name = ""
                    if row.code_of_company:
                        company_name = frappe.get_value(
                            "Company Master",
                            row.code_of_company,
                            "company_name"
                        ) or ""
                    company_rows.append({
                        "company": row.code_of_company,
                        "company_name": company_name,
                    })

               
                storage_rows = []
                for row in doc.storage_location_table:
                    storage_desc = ""
                    if row.storage_location:
                        storage_desc = frappe.get_value(
                            "Storage Location Master",
                            row.storage_location,
                            "storage_location_name"
                        ) or ""
                    storage_rows.append({
                        "storage_location": row.storage_location,
                        "storage_name": storage_desc,
                    })

                result.append({
                    "name": doc.name,
                    "material_type_name": doc.material_type_name,
                    "description": doc.description,
                    "company": doc.company,
                    "material_category_type": doc.material_category_type,
                    "valuation_and_profit": valuation_rows,
                    "multiple_company": company_rows,
                    "storage_location_table": storage_rows,
                })
        else:
           
            result = documents

        return {
            "message": "Success",
            "data": result,
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
        frappe.log_error(frappe.get_traceback(), "Material Type Master List Error")
        return {"message": "Failed", "error": str(e)}