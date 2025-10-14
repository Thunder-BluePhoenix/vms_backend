import frappe
import json


# @frappe.whitelist(allow_guest = True)
# def get_po():
#     all_po = frappe.get_all("Purchase Order", fields ="*", order_by = "modified desc")
#     return all_po


@frappe.whitelist(allow_guest=True)
def get_po(page_no=None, page_length=None):
    try:
        # Set default pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 20
        start = (page_no - 1) * page_length

        user = frappe.session.user
        user_roles = frappe.get_roles(user)

        # VENDOR FLOW
        if "Vendor" in user_roles:
            # Get Vendor Master entries where user's email matches primary or secondary email
            ref_no = frappe.get_all("Vendor Master", filters={"office_email_primary": user}, pluck="name")

            if ref_no:
                company_vendor_codes = frappe.get_all(
                    "Company Vendor Code",
                    filters={"vendor_ref_no": ["in", ref_no]},
                    pluck="name"
                )

                if company_vendor_codes:
                    vendor_codes_set = set()
                    for code_name in company_vendor_codes:
                        doc = frappe.get_doc("Company Vendor Code", code_name)
                        if doc.vendor_code:
                            for row in doc.vendor_code:
                                vendor_codes_set.add(row.vendor_code)

                    vendor_codes = list(vendor_codes_set)

                    if vendor_codes:
                        total_count = frappe.db.count("Purchase Order", {
                            "vendor_code": ["in", vendor_codes],
                            "sent_to_vendor": 1
                        })

                        total_pages = (total_count + page_length - 1) // page_length

                        all_po = frappe.get_all(
                            "Purchase Order",
                            filters={
                                "vendor_code": ["in", vendor_codes],
                                "sent_to_vendor": 1
                            },
                            fields="*",
                            order_by="modified desc",
                            start=start,
                            page_length=page_length
                        )

                        return {
                            "status": "success",
                            "message": "Purchase Orders fetched successfully.",
                            "data": all_po,
                            "total_count": total_count,
                            "page_no": page_no,
                            "page_length": page_length,
                            "total_pages": total_pages
                        }

            # No Vendor Master or Vendor Codes
            return {
                "status": "success",
                "message": "No Purchase Orders found for vendor.",
                "data": [],
                "total_count": 0,
                "page_no": page_no,
                "page_length": page_length,
                "total_pages": 0
            }

        # NON-VENDOR FLOW
        else:
            emp_data = frappe.get_value("Employee", {"user_id": user}, ["team", "designation"])

            if not emp_data:
                return {
                    "status": "error",
                    "message": "Employee record not found for the current user.",
                    "error": f"No employee found with user_id: {user}",
                    "data": [],
                    "total_count": 0,
                    "page_no": page_no,
                    "page_length": page_length,
                    "total_pages": 0
                }

            team, designation = emp_data

            pur_grp_codes = frappe.get_all(
                "Purchase Group Master",
                filters={"team": team},
                pluck="purchase_group_code"
            )

            if not pur_grp_codes:
                return {
                    "status": "success",
                    "message": "No purchase groups found for the user's team.",
                    "data": [],
                    "total_count": 0,
                    "page_no": page_no,
                    "page_length": page_length,
                    "total_pages": 0
                }

            # Fetch purchase orders where purchase_group matches these codes
            total_count = frappe.db.count("Purchase Order", {
                "purchase_group": ["in", pur_grp_codes],
                "sent_to_vendor": 1
            })

            total_pages = (total_count + page_length - 1) // page_length

            all_po = frappe.get_all("Purchase Order",
                                    filters={
                                        "purchase_group": ["in", pur_grp_codes],
                                        "sent_to_vendor": 1
                                    },
                                    fields="*",
                                    order_by="modified desc",
                                    start=start,
                                    page_length=page_length)

            return {
                "status": "success",
                "message": "Purchase Orders fetched successfully.",
                "data": all_po,
                "total_count": total_count,
                "page_no": page_no,
                "page_length": page_length,
                "total_pages": total_pages
            }


    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_po error")
        frappe.throw(f"Error while fetching purchase orders: {str(e)}")



@frappe.whitelist(allow_guest = True)
def get_po_details(po_name):
    try:
        po = frappe.get_doc("Purchase Order", po_name)
        po_dict = po.as_dict()
        
        po_dict["requisitioner_email"] = None
        po_dict["requisitioner_name"] = None
        po_dict["bill_to_company_details"] = None
        po_dict["ship_to_company_details"] = None
        po_dict["vendor_address_details"] = None

        pr_no = po.get("ref_pr_no")
        bill_to_company = po.get("bill_to_company")
        ship_to_company = po.get("ship_to_company")
        vendor_code = po.get("vendor_code")
        company_code = po.get("company_code")

        if bill_to_company:
            bill_to_company_details = get_company_details_with_state(bill_to_company)
            
            if bill_to_company_details:
                po_dict["bill_to_company_details"] = bill_to_company_details

        if ship_to_company:
            ship_to_company_details = get_company_details_with_state(ship_to_company)
            if ship_to_company_details:
                po_dict["ship_to_company_details"] = ship_to_company_details

        if vendor_code and company_code:
            vendor_address = get_vendor_address_details(vendor_code, company_code)
            if vendor_address:
                po_dict["vendor_address_details"] = vendor_address

        if pr_no:
            pr_form_name = frappe.db.get_value("Purchase Requisition Form", {"sap_pr_code": pr_no}, "name")
            
            if pr_form_name:
                pr_doc = frappe.get_doc("Purchase Requisition Form", pr_form_name)
                purchase_requisitioner = pr_doc.get("requisitioner")
                
                if purchase_requisitioner:
                    po_dict["requisitioner_email"] = purchase_requisitioner
                    
                    requisitioner_name = frappe.get_value("User", purchase_requisitioner, "first_name") or frappe.get_value("User", purchase_requisitioner, "full_name")
                    po_dict["requisitioner_name"] = requisitioner_name

        return po_dict
        
    except frappe.DoesNotExistError:
        frappe.throw(f"Purchase Order '{po_name}' not found")
    except Exception as e:
        frappe.log_error(f"Error in get_po_details: {str(e)}")
        frappe.throw(f"An error occurred while fetching PO details: {str(e)}")


def get_company_details_with_state(company_name):
   
    try:
        company_details = frappe.db.get_value(
            "Company Master", 
            company_name,
            ["name", "sap_client_code", "company_code", "company_name", "company_short_form", 
             "description", "gstin_number", "dl_number", "ssi_region_number", "street_1", 
             "street_2", "city", "pincode", "inactive", "qms_required", "contact_no", "state"],
            as_dict=True
        )
        
        if company_details and company_details.get("state"):
          
            state_code = frappe.db.get_value("State Master", company_details.get("state"), "custom_gst_state_code")
            
           
            company_details["state_code"] = state_code
            
            company_details["state_full"] = f"{state_code}-{company_details.get('state')}" if state_code else company_details.get('state')
        
        return company_details
        
    except Exception as e:
        frappe.log_error(f"Error in get_company_details_with_state: {str(e)}")
        return None



def get_vendor_address_details(vendor_code, company_code):
    
    try:
       
        company_vendor_codes = frappe.get_all(
            "Company Vendor Code",
            filters={"company_code": company_code},
            fields=["name", "vendor_ref_no", "vendor_name"]  
        )
        
        if not company_vendor_codes:
            return None
        
        
        for cvc in company_vendor_codes:
            
            vendor_code_entries = frappe.get_all(
                "Vendor Code",
                filters={
                    "parent": cvc.name,
                    "vendor_code": vendor_code
                },
                fields=["vendor_code", "state", "gst_no", "address_line_1", 
                        "address_line_2", "zip_code", "city", "district", "country"]
            )
            
            if vendor_code_entries:
               
                result = vendor_code_entries[0]
                
                
                result["vendor_name"] = cvc.get("vendor_name")
                
                return result
        
        return None
        
    except Exception as e:
        frappe.log_error(f"Error in get_vendor_address_details: {str(e)}")
        return None

@frappe.whitelist(allow_guest = True)
def filtering_data(data):
    pass






# @frappe.whitelist(allow_guest=True)
# def get_po_details_withformat(po_name, po_format_name=None):
#     try:
#         # Check if PO exists
#         if not frappe.db.exists("Purchase Order", po_name):
#             raise frappe.DoesNotExistError(f"Purchase Order {po_name} not found")
        
#         # Validate permissions
#         if not frappe.has_permission("Purchase Order", "read"):
#             raise frappe.PermissionError("Insufficient permissions to read Purchase Order")
        
#         po = frappe.get_doc("Purchase Order", po_name)
        
#         # Update PO format if provided
#         if po_format_name:
#             # Validate write permission if updating
#             if not frappe.has_permission("Purchase Order", "write"):
#                 raise frappe.PermissionError("Insufficient permissions to update Purchase Order")
            
#             # Validate format exists
#             if not frappe.db.exists("PO PrintFormat Master", po_format_name):
#                 raise frappe.DoesNotExistError(f"Print Format {po_format_name} not found")
            
#             po.purchase_order_format = po_format_name
#             po.save()
#             frappe.db.commit()
        
#         po_dict = po.as_dict()
        
#         # Populate po_format_name from updated/existing field
#         po_dict["po_format_name"] = po.get("purchase_order_format")
        
#         # Initialize requisitioner fields
#         po_dict["requisitioner_email"] = None
#         po_dict["requisitioner_name"] = None
#         po_dict["sign_url1"] = None
#         po_dict["sign_url2"] = None
#         po_dict["sign_url3"] = None
        
#         pr_no = po.get("ref_pr_no")
        
#         if pr_no:
#             pr_form_name = frappe.db.get_value("Purchase Requisition Form", {"sap_pr_code": pr_no}, "name")
            
#             if pr_form_name:
#                 pr_doc = frappe.get_doc("Purchase Requisition Form", pr_form_name)
#                 purchase_requisitioner = pr_doc.get("requisitioner")
                
#                 if purchase_requisitioner:
#                     po_dict["requisitioner_email"] = purchase_requisitioner
#                     requisitioner_name = frappe.get_value("User", purchase_requisitioner, "first_name") or frappe.get_value("User", purchase_requisitioner, "full_name")
#                     po_dict["requisitioner_name"] = requisitioner_name


#         if po.sign_of_approval1:
#             file_doc = frappe.get_doc("File", {"file_url": po.sign_of_approval1})
#             po_dict["sign_url1"] = {
#                 "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
#                 "name": file_doc.name,
#                 "file_name": file_doc.file_name

#             }
#         if po.sign_of_approval2:
#             file_doc = frappe.get_doc("File", {"file_url": po.sign_of_approval2})
#             po_dict["sign_url2"] = {
#                 "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
#                 "name": file_doc.name,
#                 "file_name": file_doc.file_name

#             }
#         if po.sign_of_approval3:
#             file_doc = frappe.get_doc("File", {"file_url": po.sign_of_approval3})
#             po_dict["sign_url3"] = {
#                 "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
#                 "name": file_doc.name,
#                 "file_name": file_doc.file_name

#             }

        
#         # Success response
#         frappe.response["http_status_code"] = 200
#         return {
#             "success": True,
#             "message": f"PO details retrieved{' and format updated' if po_format_name else ''} successfully",
#             "data": po_dict
#         }
        
#     except Exception as e:
#         frappe.db.rollback()
#         return handle_api_exception(e, "PO Details API")
    






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




import base64
import mimetypes
import os

@frappe.whitelist(allow_guest=True)
def get_po_details_withformat(po_name, po_format_name=None):
    try:
        # Check if PO exists
        if not frappe.db.exists("Purchase Order", po_name):
            raise frappe.DoesNotExistError(f"Purchase Order {po_name} not found")
        
        # Validate permissions
        if not frappe.has_permission("Purchase Order", "read"):
            raise frappe.PermissionError("Insufficient permissions to read Purchase Order")
        
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Update PO format if provided
        if po_format_name:
            # Validate write permission if updating
            if not frappe.has_permission("Purchase Order", "write"):
                raise frappe.PermissionError("Insufficient permissions to update Purchase Order")
            
            # Validate format exists
            if not frappe.db.exists("PO PrintFormat Master", po_format_name):
                raise frappe.DoesNotExistError(f"Print Format {po_format_name} not found")
            
            po.purchase_order_format = po_format_name
            po.save()
            frappe.db.commit()
        
        po_dict = po.as_dict()
        
        # Populate po_format_name from updated/existing field
        po_dict["po_format_name"] = po.get("purchase_order_format")
        
        # Initialize requisitioner fields
        po_dict["requisitioner_email"] = None
        po_dict["requisitioner_name"] = None
        po_dict["sign_url1"] = None
        po_dict["sign_url2"] = None
        po_dict["sign_url3"] = None
        po_dict["company_logo"] = None
        po_dict["bill_to_company_details"] = None
        po_dict["ship_to_company_details"] = None
        po_dict["vendor_address_details"] = None


        bill_to_company = po.get("bill_to_company")
        
        ship_to_company = po.get("ship_to_company")
        vendor_code = po.get("vendor_code")
        company_code = po.get("company_code")
        pr_no = po.get("ref_pr_no")

        if bill_to_company:
            
            bill_to_company_details = get_company_details_with_state(bill_to_company)
            
            if bill_to_company_details:
                po_dict["bill_to_company_details"] = bill_to_company_details

        if ship_to_company:
            ship_to_company_details = get_company_details_with_state(ship_to_company)
            if ship_to_company_details:
                po_dict["ship_to_company_details"] = ship_to_company_details

        if vendor_code and company_code:
            vendor_address = get_vendor_address_details(vendor_code, company_code)
            if vendor_address:
                po_dict["vendor_address_details"] = vendor_address
        
        
            
        
        if pr_no:
            pr_form_name = frappe.db.get_value("Purchase Requisition Form", {"sap_pr_code": pr_no}, "name")
            
            if pr_form_name:
                pr_doc = frappe.get_doc("Purchase Requisition Form", pr_form_name)
                purchase_requisitioner = pr_doc.get("requisitioner")
                
                if purchase_requisitioner:
                    po_dict["requisitioner_email"] = purchase_requisitioner
                    requisitioner_name = frappe.get_value("User", purchase_requisitioner, "first_name") or frappe.get_value("User", purchase_requisitioner, "full_name")
                    po_dict["requisitioner_name"] = requisitioner_name

        # Helper function to get file data with base64
        def get_file_data_with_base64(file_url):
            try:
                file_doc = frappe.get_doc("File", {"file_url": file_url})
                
                # Get the full file path
                # file_path = frappe.get_site_path() + file_doc.file_url
                file_path = file_doc.get_full_path()
                
                # Initialize base64 data
                base64_data = None
                mime_type = None
                
                # Read file and convert to base64 if it exists
                if os.path.exists(file_path):
                    with open(file_path, "rb") as file:
                        file_content = file.read()
                        base64_data = base64.b64encode(file_content).decode('utf-8')
                        
                    # Get MIME type
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if not mime_type:
                        # Default to common image types if unable to detect
                        file_ext = os.path.splitext(file_doc.file_name)[1].lower()
                        mime_type_map = {
                            '.png': 'image/png',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.gif': 'image/gif',
                            '.pdf': 'application/pdf',
                            '.svg': 'image/svg+xml',
                            '.webp': 'image/webp',
                        }
                        mime_type = mime_type_map.get(file_ext, 'application/octet-stream')
                
                return {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                    "name": file_doc.name,
                    "file_name": file_doc.file_name,
                    "base64": base64_data,
                    "mime_type": mime_type,
                    "data_url": f"data:{mime_type};base64,{base64_data}" if base64_data and mime_type else None
                }
            except Exception as e:
                frappe.log_error(f"Error processing file {file_url}: {str(e)}", "File Base64 Conversion")
                return {
                    "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_url}",
                    "name": None,
                    "file_name": None,
                    "base64": None,
                    "mime_type": None,
                    "data_url": None,
                    "error": f"Failed to process file: {str(e)}"
                }

        # Process signature files with base64 conversion
        if po.sign_of_approval1:
            po_dict["sign_url1"] = get_file_data_with_base64(po.sign_of_approval1)
            
        if po.sign_of_approval2:
            po_dict["sign_url2"] = get_file_data_with_base64(po.sign_of_approval2)
            
        if po.sign_of_approval3:
            po_dict["sign_url3"] = get_file_data_with_base64(po.sign_of_approval3)


        if bill_to_company:
            company_details = frappe.db.get_value(
                "Company Master",
                bill_to_company,
                ["company_logo"],
                as_dict=True
            )
            
            if company_details and company_details.get("company_logo"):
                po_dict["company_logo"] = get_file_data_with_base64(company_details.get("company_logo"))
        
        # Success response
        frappe.response["http_status_code"] = 200
        return {
            "success": True,
            "message": f"PO details retrieved{' and format updated' if po_format_name else ''} successfully",
            "data": po_dict
        }
        
    except Exception as e:
        frappe.db.rollback()
        return handle_api_exception(e, "PO Details API")