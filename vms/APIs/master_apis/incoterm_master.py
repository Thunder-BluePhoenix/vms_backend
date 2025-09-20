import frappe 
from frappe import _




@frappe.whitelist(allow_guest=True)
def get_incoterm_list(company_name=None):
    try:
        if company_name:
            # Query to get incoterms filtered by company from child table
            query = """
                SELECT DISTINCT 
                    im.name, 
                    im.incoterm_code, 
                    im.incoterm_name,
                    im.delivery_point,
                    im.transportation_costs,
                    im.risk_transfer,
                    im.note
                FROM `tabIncoterm Master` im
                INNER JOIN `tabIncoterm Company Table` ict ON im.name = ict.parent
                WHERE ict.company = %s AND im.inactive = 0
                ORDER BY im.incoterm_name
            """
            
            incoterms = frappe.db.sql(query, (company_name,), as_dict=True)
            
            if not incoterms:
                return {
                    "status": "success",
                    "message": f"No Incoterm records found for company: {company_name}",
                    "data": []
                }
            
            return {
                "status": "success",
                "message": f"{len(incoterms)} Incoterm(s) found for company: {company_name}",
                "data": incoterms
            }
        
        else:
            # If no company filter, get all incoterms
            all_incoterms = frappe.get_all(
                "Incoterm Master",
                filters={"inactive": 0},
                fields=["name", "incoterm_code", "incoterm_name", "delivery_point", 
                       "transportation_costs", "risk_transfer", "note"],
                order_by="incoterm_name"
            )
            
            if not all_incoterms:
                return {
                    "status": "success",
                    "message": "No Incoterm records found.",
                    "data": []
                }
            
            return {
                "status": "success",
                "message": f"{len(all_incoterms)} Incoterm(s) found.",
                "data": all_incoterms
            }

    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "Incoterm Master Doctype Not Found")
        return {
            "status": "error",
            "message": "Incoterm Master doctype does not exist."
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_incoterm_list")
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }