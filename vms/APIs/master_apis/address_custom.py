import frappe
import json


@frappe.whitelist(allow_guest = True)
def address_filter(pincode=None, city_name=None, district_name=None, state_name=None, country_name=None):
    try:
        result = {
            "pincode": None,
            "city": None,
            "district": None,
            "state": None,
            "country": None
        }

        if pincode:
            if not frappe.db.exists("Pincode Master", pincode):
                raise frappe.DoesNotExistError(f"Pincode {pincode} not found")
            
            pincode_doc = frappe.get_doc("Pincode Master", pincode)

            city = frappe.db.get_value("City Master", pincode_doc.city, ["name", "city_code", "city_name"], as_dict=True) if pincode_doc.city else None
            district = frappe.db.get_value("District Master", pincode_doc.district, ["name", "district_code", "district_name"], as_dict=True) if pincode_doc.district else None
            state = frappe.db.get_value("State Master", pincode_doc.state, ["name", "state_code", "state_name"], as_dict=True) if pincode_doc.state else None
            country = frappe.db.get_value("Country Master", pincode_doc.country, ["name", "country_code", "country_name"], as_dict=True) if pincode_doc.country else None

            result["pincode"] = {
                "name": pincode_doc.name,
                "zone": pincode_doc.zone
            }
            result["city"] = city
            result["district"] = district
            result["state"] = state
            result["country"] = country

        elif city_name:
            if not frappe.db.exists("City Master", city_name):
                raise frappe.DoesNotExistError(f"City {city_name} not found")
            
            city = frappe.get_doc("City Master", city_name)
            result["city"] = {
                "name": city.name,
                "city_code": city.city_code,
                "city_name": city.city_name
            }
            result["district"] = {"name": city.district}
            result["state"] = {"name": city.state}
            result["country"] = {"name": city.country}

        elif district_name:
            if not frappe.db.exists("District Master", district_name):
                raise frappe.DoesNotExistError(f"District {district_name} not found")
            
            district = frappe.get_doc("District Master", district_name)
            result["district"] = {
                "name": district.name,
                "district_code": district.district_code,
                "district_name": district.district_name
            }
            result["state"] = {"name": district.state}
            result["country"] = {"name": district.country}
            cities = frappe.get_all("City Master", filters={"district": district.name}, fields=["name", "city_code", "city_name"])
            result["city"] = cities  # Keep as array for multiple cities

        elif state_name:
            if not frappe.db.exists("State Master", state_name):
                raise frappe.DoesNotExistError(f"State {state_name} not found")
            
            state = frappe.get_doc("State Master", state_name)
            result["state"] = {
                "name": state.name,
                "state_code": state.state_code,
                "state_name": state.state_name
            }
            result["country"] = {"name": state.country_name}
            districts = frappe.get_all("District Master", filters={"state": state.name}, fields=["name", "district_code", "district_name"])
            result["district"] = districts  # Keep as array for multiple districts
            district_names = [d["name"] for d in districts]
            cities = frappe.get_all("City Master", filters={"district": ["in", district_names]}, fields=["name", "city_code", "city_name"])
            result["city"] = cities  # Keep as array for multiple cities

        elif country_name:
            countries = frappe.get_all("Country Master", filters={"name": country_name}, fields=["name", "country_code", "country_name"])
            if not countries:
                raise frappe.DoesNotExistError(f"Country {country_name} not found")
            
            result["country"] = countries[0]  # Single country object
            states = frappe.get_all("State Master", filters={"country_name": country_name}, fields=["name", "state_code", "state_name"])
            result["state"] = states  # Keep as array for multiple states
            state_names = [s["name"] for s in states]
            districts = frappe.get_all("District Master", filters={"state": ["in", state_names]}, fields=["name", "district_code", "district_name"])
            result["district"] = districts  # Keep as array for multiple districts
            district_names = [d["name"] for d in districts]
            cities = frappe.get_all("City Master", filters={"district": ["in", district_names]}, fields=["name", "city_code", "city_name"])
            result["city"] = cities  # Keep as array for multiple cities

        else:
            raise frappe.ValidationError("Please provide at least one parameter (pincode, city_name, district_name, state_name, or country_name)")

        frappe.response["http_status_code"] = 200
        return {
            "success": True,
            "message": "Address hierarchy fetched successfully",
            "data": result
        }

    except Exception as e:
        return handle_api_exception(e, "Address Filter API")
    





def handle_api_exception(e, operation_name="API Operation"):
    """Dynamic exception handler for Frappe APIs"""
    
    # Get exception type and name
    exc_type = type(e)
    exc_name = exc_type.__name__
    
    # Dynamic mapping based on exception name patterns
    status_code = 500
    error_type = "Internal server error"
    default_message = "An unexpected error occurred"
    
    # Check frappe exception types dynamically
    if hasattr(frappe, exc_name):
        if "NotFound" in exc_name or "DoesNotExist" in exc_name:
            status_code = 404
            error_type = "Resource not found"
            default_message = "The requested resource does not exist"
        elif "Permission" in exc_name:
            status_code = 403
            error_type = "Permission denied"
            default_message = "You don't have permission to access this resource"
        elif "Validation" in exc_name:
            status_code = 400
            error_type = "Validation error"
            default_message = "Invalid data provided"
        elif "Data" in exc_name:
            status_code = 400
            error_type = "Data error"
            default_message = "Invalid field or data structure"
        elif "Duplicate" in exc_name:
            status_code = 409
            error_type = "Duplicate entry"
            default_message = "Resource already exists"
        elif "Link" in exc_name:
            status_code = 400
            error_type = "Link validation error"
            default_message = "Invalid link reference"
    
    # Set HTTP status code
    frappe.response["http_status_code"] = status_code
    
    # Log error with operation context
    log_title = f"{operation_name} - {error_type}"
    frappe.log_error(frappe.get_traceback(), log_title)
    
    # Return structured error response
    return {
        "success": False,
        "error": error_type,
        "message": f"{default_message}: {str(e)}" if str(e) else default_message,
        "exception_type": exc_name
    }

