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
                    "Valuation Class",
                    row.valuation_class,
                    "valuation_class_name"
                ) or ""
            
            profit_center_description = ""
            if row.profit_center:
                profit_center_description = frappe.get_value(
                    "Profit Center",
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
            if row.company_name:
                company_name = frappe.get_value(
                    "Company Master",
                    row.company_name,
                    "company_name"
                ) or ""
            company_rows.append({
                "company": row.company_name,
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

# #vms.APIs.master_apis.material_type.get_material_type_master_list
# @frappe.whitelist()
# def get_material_type_master_list(
#     filters=None,
#     fields=None,
#     limit=None,
#     offset=0,
#     order_by=None,
#     search_term=None,
#     include_child_tables=True
# ):
#     try:
        
#         if isinstance(filters, str):
#             filters = json.loads(filters) if filters else {}
#         elif filters is None:
#             filters = {}

       
#         if isinstance(fields, str):
#             fields = json.loads(fields) if fields else [
#                 "name", "material_type_name", "description",
#                 "company", "material_category_type"
#             ]
#         elif fields is None:
#             fields = [
#                 "name", "material_type_name", "description",
#                 "company", "material_category_type"
#             ]

        
#         limit = int(limit) if limit else None
#         offset = int(offset) if offset else 0
        
        
#         if isinstance(include_child_tables, str):
#             include_child_tables = include_child_tables.lower() in ['true', '1', 'yes']
        
       
#         if not order_by:
#             order_by = "creation desc"

      
#         search_filters = filters.copy()
#         or_filters = None
        
#         if search_term:
           
#             or_filters = [
#                 ["name", "like", f"%{search_term}%"],
#                 ["material_type_name", "like", f"%{search_term}%"],
#                 ["description", "like", f"%{search_term}%"]
#             ]

     
#         if or_filters:
#             documents = frappe.get_list(
#                 "Material Type Master",
#                 filters=search_filters,
#                 or_filters=or_filters,
#                 fields=fields,
#                 limit=limit,
#                 start=offset,
#                 order_by=order_by,
#                 ignore_permissions=True
#             )
            
        
#             total_count = len(frappe.get_all(
#                 "Material Type Master",
#                 filters=search_filters,
#                 or_filters=or_filters,
#                 fields=["name"]
#             ))
#         else:
#             documents = frappe.get_list(
#                 "Material Type Master",
#                 filters=search_filters,
#                 fields=fields,
#                 limit=limit,
#                 start=offset,
#                 order_by=order_by,
#                 ignore_permissions=True
#             )
            
          
#             total_count = frappe.db.count("Material Type Master", search_filters)

      
#         if include_child_tables:
#             result = []
#             for item in documents:
#                 doc = frappe.get_doc("Material Type Master", item.name)

               
#                 valuation_rows = []
#                 for row in doc.valuation_and_profit:
#                     valuation_class_description = ""
#                     if row.valuation_class:
#                         valuation_class_description = frappe.get_value(
#                             "Valuation Class",
#                             row.valuation_class,
#                             "valuation_class_name"
#                         ) or ""
                    
#                     profit_center_description = ""
#                     if row.profit_center:
#                         profit_center_description = frappe.get_value(
#                             "Profit Center",
#                             row.profit_center,
#                             "description"
#                         ) or ""

#                     division_code = ""
#                     division_description = ""
#                     if row.division:
#                         division_code = frappe.get_value(
#                             "Division Master",
#                             row.division,
#                             "division_code"
#                         ) or ""
#                         division_description = frappe.get_value(
#                             "Division Master",
#                             row.division,
#                             "description"
#                         ) or ""

#                     valuation_rows.append({
#                         "valuation_class": row.valuation_class,
#                         "valuation_class_description": valuation_class_description,
#                         "profit_center": row.profit_center,
#                         "profit_center_description": profit_center_description,
#                         "division": row.division,
#                         "division_name": " - ".join(filter(None, [division_code, division_description])),
#                         "company": row.company,
#                     })

                
#                 company_rows = []
#                 for row in doc.multiple_company:
#                     company_name = ""
#                     if row.company_name:
#                         company_name = frappe.get_value(
#                             "Company Master",
#                             row.company_name,
#                             "company_name"
#                         ) or ""
#                     company_rows.append({
#                         "company": row.company_name,
#                         "company_name": company_name,
#                     })

               
#                 storage_rows = []
#                 for row in doc.storage_location_table:
#                     storage_desc = ""
#                     if row.storage_location:
#                         storage_desc = frappe.get_value(
#                             "Storage Location Master",
#                             row.storage_location,
#                             "storage_location_name"
#                         ) or ""
#                     storage_rows.append({
#                         "storage_location": row.storage_location,
#                         "storage_name": storage_desc,
#                     })

#                 result.append({
#                     "name": doc.name,
#                     "material_type_name": doc.material_type_name,
#                     "material_category_type": doc.material_category_type,
#                     "description": doc.description,
#                     "plant_code": doc.plant_code,
#                     "valuation_and_profit": valuation_rows,
#                     "multiple_company": company_rows,
#                     "storage_location_table": storage_rows,
#                 })
#         else:
           
#             result = documents

#         return {
#             "message": "Success",
#             "data": result,
#             "pagination": {
#                 "total_count": total_count,
#                 "limit": limit,
#                 "offset": offset,
#                 "has_next": (offset + limit) < total_count,
#                 "has_previous": offset > 0
#             }
#         }

#     except json.JSONDecodeError:
#         frappe.response.http_status_code = 400
#         return {"message": "Failed", "error": "Invalid JSON in filters or fields"}
    
#     except Exception as e:
#         frappe.response.http_status_code = 500
#         frappe.log_error(frappe.get_traceback(), "Material Type Master List Error")
#         return {"message": "Failed", "error": str(e)}

@frappe.whitelist()
def get_material_type_master_list(
    filters=None,
    limit=None,
    offset=0,
    order_by=None,
    search_term=None,
    include_child_tables=True
):
    try:
        # ---- Normalize inputs ----
        limit = int(limit) if limit else None
        offset = int(offset) if offset else 0
        order_by = order_by or "creation desc"

        # Parse filters
        if isinstance(filters, str):
            filters = json.loads(filters)
        filters = filters or {}

        company = filters.get("company") if filters else frappe.form_dict.get("company")
        material_category_type = filters.get("material_category_type") if filters else frappe.form_dict.get("material_category_type")


        # ---- Build Frappe filters ----
        frappe_filters = {}
        if material_category_type:
            frappe_filters["material_category_type"] = material_category_type

        # Search term handling
        if search_term:
            frappe_filters["or_filters"] = [
                ["Material Type Master", "name", "like", f"%{search_term}%"],
                ["Material Type Master", "material_type_name", "like", f"%{search_term}%"],
                ["Material Type Master", "description", "like", f"%{search_term}%"],
            ]

        # ---- Filter by company (through child table) ----
        if company:
            parents = frappe.get_all(
                "Multiple Company Name",
                filters={"company_name": company},
                pluck="parent",
            )
            if parents:
                frappe_filters["name"] = ["in", parents]
            else:
                frappe.msgprint(f"No company-specific Material Types found for {company}. Returning all.")

        # ---- Fetch parent records ----
        records = frappe.get_all(
            "Material Type Master",
            filters=frappe_filters,
            fields=[
                "name",
                "material_type_name",
                "description",
                "material_category_type",
                "company",
                "plant_code",
            ],
            order_by=order_by,
            limit_start=offset,
            limit_page_length=limit,
        )

        total_count = frappe.db.count("Material Type Master", filters=frappe_filters)

        # ---- Expand child tables ----
        include_child_tables = (
            str(include_child_tables).lower() in ["true", "1", "yes"]
        )
        if include_child_tables:
            detailed_records = []
            for rec in records:
                doc = frappe.get_doc("Material Type Master", rec.name)

                # Child: Valuation and Profit
                valuation_rows = []
                for row in doc.valuation_and_profit:
                    valuation_rows.append({
                        "valuation_class": row.valuation_class,
                        "valuation_class_description": frappe.get_value(
                            "Valuation Class", row.valuation_class, "valuation_class_name"
                        ) or "",
                        "profit_center": row.profit_center,
                        "profit_center_description": frappe.get_value(
                            "Profit Center", row.profit_center, "description"
                        ) or "",
                        "division": row.division,
                        "division_name": " - ".join(
                            filter(
                                None,
                                [
                                    frappe.get_value("Division Master", row.division, "division_code"),
                                    frappe.get_value("Division Master", row.division, "description"),
                                ],
                            )
                        ),
                        "company": row.company,
                    })

                # Child: Company
                company_rows = [
                    {
                        "company": row.company_name,
                        "company_name": frappe.get_value(
                            "Company Master", row.company_name, "company_name"
                        ) or "",
                    }
                    for row in doc.multiple_company
                ]

                # Child: Storage
                storage_rows = [
                    {
                        "storage_location": row.storage_location,
                        "storage_name": frappe.get_value(
                            "Storage Location Master",
                            row.storage_location,
                            "storage_location_name",
                        ) or "",
                    }
                    for row in doc.storage_location_table
                ]

                detailed_records.append({
                    **rec,
                    "valuation_and_profit": valuation_rows,
                    "multiple_company": company_rows,
                    "storage_location_table": storage_rows,
                })

            records = detailed_records

        return {
            "message": "Success",
            "data": records,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + (limit or 0)) < total_count,
                "has_previous": offset > 0,
            },
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Material Type Master List Error")
        frappe.response.http_status_code = 500
        return {"message": "Failed", "error": str(e)}
