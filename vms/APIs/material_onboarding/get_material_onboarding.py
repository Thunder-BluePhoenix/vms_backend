import json
import frappe
from frappe import _


#vms.APIs.material_onboarding.get_material_onboarding.get_material_onboarding_list
@frappe.whitelist()
def get_material_onboarding_list(
    filters=None,
    limit=20,
    offset=0,
    order_by=None,
    search_term=None
):
    try:
    
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        # Convert limit and offset to integers
        limit = int(limit) if limit else 20
        offset = int(offset) if offset else 0
        
        # Set default order_by if not provided
        if not order_by:
            order_by = "request_date DESC, creation DESC"

        # Build the query for requestor masters
        requestor_filters = {}
        
        # Apply filters to requestor master fields
        if "name" in filters:
            requestor_filters["name"] = filters["name"]
        if "approval_status" in filters:
            requestor_filters["approval_status"] = filters["approval_status"]
        if "requested_by" in filters:
            requestor_filters["requested_by"] = filters["requested_by"]
        if "requestor_company" in filters:
            requestor_filters["requestor_company"] = filters["requestor_company"]

        # Get all requestors (we'll flatten their children)
        requestors_query = frappe.get_all(
            "Requestor Master",
            filters=requestor_filters,
            fields=["name", "requested_by", "request_date", "requestor_company", 
                    "contact_information_email", "approval_status","requested_by_place"],
            order_by=order_by
        )

        # Flatten all material requests from all requestors
        material_onboarding_list = []
        
        for requestor in requestors_query:
            requestor_doc = frappe.get_doc("Requestor Master", requestor.name)
            
            for material in requestor_doc.material_request:
                # Apply material-level filters if provided
                if "material_name" in filters and material.name != filters["name"]:
                    continue
                if "material_type" in filters and material.material_type != filters["material_type"]:
                    continue
                if "company_name" in filters and material.company_name != filters["company_name"]:
                    continue
                if "plant" in filters and material.plant != filters["plant"]:
                    continue

                # Apply search filter
                if search_term:
                    search_match = (
                        (material.material_name_description and search_term.lower() in material.material_name_description.lower()) or
                        (material.material_code_revised and search_term.lower() in material.material_code_revised.lower()) or
                        (requestor.requested_by and search_term.lower() in requestor.requested_by.lower()) or
                        (material.plant and search_term.lower() in material.plant.lower())
                    )
                    if not search_match:
                        continue

                # Get company name
                company_name = None
                if material.company_name:
                    company_name = frappe.db.get_value(
                        "Company Master",
                        material.company_name,
                        "company_name"
                    )

                entry = {
                    "requestor_ref_no": requestor_doc.name,
                    "child_table_row_id": material.name,
                    "material_name_description": material.material_name_description,
                    "material_code_revised": material.material_code_revised,
                    "material_company_code": material.company_name,
                    "material_company_name": company_name,
                    "plant": material.plant,
                    "material_category": material.material_category,
                    "material_type": material.material_type,
                    "unit_of_measure": material.unit_of_measure,
                    "comment_by_user": material.comment_by_user,
                    "material_specifications": material.material_specifications,
                    "is_revised_code_new": material.is_revised_code_new,
                    "requested_by": requestor.requested_by,
                    "request_date": requestor.request_date,
                    "requestor_company": requestor.requestor_company,
                    "contact_information_email": requestor.contact_information_email,
                    "approval_status": requestor.approval_status,
                    "requested_by_place": requestor.requested_by_place,
                    "requested_by": requestor_doc.requested_by,
                    "request_date": requestor_doc.request_date,
                    "requestor_company": requestor_doc.requestor_company,
                    "department": requestor_doc.requestor_department,
                    "sub_department": requestor_doc.sub_department,
                    "hod": requestor_doc.requestor_hod,
                    "immediate_reporting_head": requestor_doc.immediate_reporting_head,
                    "contact_information_email": requestor_doc.contact_information_email,
                    "contact_information_phone": requestor_doc.contact_information_phone,
                }

                material_onboarding_list.append(entry)

        # Get total count before pagination
        total_count = len(material_onboarding_list)

        # Apply pagination
        paginated_list = material_onboarding_list[offset:offset + limit]

        return {
            "message": "Success",
            "data": paginated_list,
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
        return {"message": "Failed", "error": "Invalid JSON in filters"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Material Onboarding List Error")
        return {"message": "Failed", "error": str(e)}


#vms.APIs.material_onboarding.get_material_onboarding.get_material_onboarding_details
@frappe.whitelist()
def get_material_onboarding_details(name, material_name):
   
    try:
        # Validate required parameters
        if not name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Requestor Master name is required"}

        if not material_name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Material name (child_table_row_id) is required"}

        # Get Requestor Master document
        try:
            requestor_doc = frappe.get_doc("Requestor Master", name)
        except frappe.DoesNotExistError:
            frappe.response.http_status_code = 404
            return {"message": "Failed", "error": f"Requestor Master '{name}' not found"}

       
        requestor_dict = requestor_doc.as_dict()

        
        for row in requestor_dict.get("material_request", []):
            if row.get("material_type"):
                material_type_name = frappe.db.get_value(
                    "Material Type Master",
                    row["material_type"],
                    "material_type_name"
                )
                row["material_type_name"] = material_type_name or ""

        
        if requestor_doc.requestor_company:
            requestor_dict["requestor_company"] = frappe.db.get_value(
                "Company Master",
                requestor_doc.requestor_company,
                "company_name"
            )

        
        selected_row = next(
            (row for row in requestor_doc.material_request if row.name == material_name),
            None
        )

        if not selected_row:
            frappe.response.http_status_code = 404
            return {"message": "Failed", "error": f"Material request item '{material_name}' not found"}

        
        material_type_name = ""
        if selected_row.material_type:
            material_type_name = frappe.db.get_value(
                "Material Type Master",
                selected_row.material_type,
                "material_type_name"
            ) or ""

        
        material_request_item = selected_row.as_dict()
        if material_type_name:
            material_request_item["material_type_name"] = material_type_name

        
        if selected_row.company_name:
            material_request_item["company_name_display"] = frappe.db.get_value(
                "Company Master",
                selected_row.company_name,
                "company_name"
            )

        
        material_master_data = {}
        mm_ref = requestor_doc.get("material_master_ref_no")
        if mm_ref:
            try:
                material_doc = frappe.get_doc("Material Master", mm_ref)
                material_master_data = material_doc.as_dict()
                
                material_master_data["children"] = [
                    d.as_dict() for d in material_doc.get_all_children()
                ]
            except frappe.DoesNotExistError:
                frappe.log_error(
                    f"Material Master '{mm_ref}' linked but not found",
                    "Material Onboarding Details - Missing Reference"
                )
            except Exception as e:
                frappe.log_error(
                    f"Failed to get Material Master '{mm_ref}': {str(e)}",
                    "Material Onboarding Details - Material Master Error"
                )

        
        material_onboarding_data = {}
        mo_ref = requestor_doc.get("material_onboarding_ref_no")
        if mo_ref:
            try:
                mo_doc = frappe.get_doc("Material Onboarding", mo_ref)
                material_onboarding_data = mo_doc.as_dict()
                # Include all children
                material_onboarding_data["children"] = [
                    d.as_dict() for d in mo_doc.get_all_children()
                ]
                # Add company name
                if mo_doc.company:
                    material_onboarding_data["company_name"] = frappe.db.get_value(
                        "Company Master",
                        mo_doc.company,
                        "company_name"
                    )
            except frappe.DoesNotExistError:
                frappe.log_error(
                    f"Material Onboarding '{mo_ref}' linked but not found",
                    "Material Onboarding Details - Missing Reference"
                )
            except Exception as e:
                frappe.log_error(
                    f"Failed to get Material Onboarding '{mo_ref}': {str(e)}",
                    "Material Onboarding Details - Material Onboarding Error"
                )

        return {
            "message": "Success",
            "data": {
                "requestor_master": requestor_dict,
                "material_request_item": material_request_item,
                "material_master": material_master_data,
                "material_onboarding": material_onboarding_data
            }
        }

    except json.JSONDecodeError:
        frappe.response.http_status_code = 400
        return {"message": "Failed", "error": "Invalid JSON format"}
    
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Material Onboarding Details Error")
        return {"message": "Failed", "error": str(e)}