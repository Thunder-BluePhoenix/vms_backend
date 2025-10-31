import frappe
from frappe import _
import json
from datetime import datetime, date
from frappe.utils.file_manager import save_file




@frappe.whitelist(allow_guest=False)
def get_all_grn_details(filters=None, fields=None, limit=None, offset=0, order_by=None, search_term=None):
    try:
        if isinstance(filters, str):
            filters = json.loads(filters) if filters else {}
        elif filters is None:
            filters = {}

        if isinstance(fields, str):
            fields = json.loads(fields) if fields else "*"
        elif fields is None:
            fields = "*"

        limit = int(limit) if limit else None
        offset = int(offset) if offset else 0
        order_by = order_by if order_by else "creation desc"

        user = frappe.session.user
        team = frappe.db.get_value("Employee", {"user_id": user}, "team")

        pg_team_map = {}
        if team:
            pg_list = frappe.get_all(
                "Purchase Group Master",
                filters={"team": team},
                fields=["purchase_group_code", "company"]
            )
            pg_team_map = {(pg["purchase_group_code"], pg["company"]) for pg in pg_list}
            print(f"🔗 Purchase Group Mappings for team: {pg_team_map}")

        if search_term:
            or_filters = [
                ["name", "like", f"%{search_term}%"],
                ["grn_no", "like", f"%{search_term}%"],
                ["sap_booking_id", "like", f"%{search_term}%"],
                ["miro_no", "like", f"%{search_term}%"],
                ["company_name", "like", f"%{search_term}%"]
            ]

            grns = frappe.get_list(
                "GRN",
                filters=filters,
                or_filters=or_filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )

            total_count_before_filter = len(frappe.get_all(
                "GRN",
                filters=filters,
                or_filters=or_filters,
                fields=["name"]
            ))
        else:
            grns = frappe.get_list(
                "GRN",
                filters=filters,
                fields=fields,
                limit=limit,
                start=offset,
                order_by=order_by,
                ignore_permissions=False
            )
            total_count_before_filter = frappe.db.count("GRN", filters)

        result = []
        missing_pos = []  

        for grn in grns:
            grn_items = frappe.get_all("GRN Items", fields="*", filters={"parent": grn["name"]})
            found_match = False

            for item in grn_items:
                po_no, plant = item.get("po_no"), item.get("plant")

                if not (po_no and plant):
                    continue

                company = grn.get("company_code")

                try:
                    pg_code = frappe.db.get_value("Purchase Order", po_no, "purchase_group")
                except Exception:
                    pg_code = None

                if not pg_code:
                    # Keep track of missing PO
                    missing_pos.append({"grn_name": grn["name"],"grn_number":grn["grn_number"], "po_no": po_no, "error": "Purchase Order not found"})
                    continue  # skip this PO, but don’t fail

                if (pg_code, company) in pg_team_map:
                    found_match = True
                    break

            if found_match or not team:
                try:
                    grn_doc = frappe.get_doc("GRN", grn["name"])

                    attachments_data = []
                    if hasattr(grn_doc, 'attachments') and grn_doc.attachments:
                        for attachment in grn_doc.attachments:
                            attachment_url = attachment.get('attachment_name')

                            attachment_info = {
                                "row_name": attachment.name,
                                "file_name": attachment.get('name1'),
                            }

                            if attachment_url:
                                try:
                                    file_doc = frappe.get_doc("File", {"file_url": attachment_url})
                                    attachment_info["full_url"] = f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}"
                                    attachment_info["file_doc_name"] = file_doc.name
                                    attachment_info["actual_file_name"] = file_doc.file_name
                                except frappe.DoesNotExistError:
                                    attachment_info["full_url"] = None
                                    attachment_info["error"] = "File document not found"
                                except Exception as e:
                                    attachment_info["full_url"] = None
                                    attachment_info["error"] = str(e)
                            else:
                                attachment_info["full_url"] = None

                            attachments_data.append(attachment_info)

                    grn["attachments"] = attachments_data
                    grn["sap_booking_id"] = grn_doc.sap_booking_id
                    grn["miro_no"] = grn_doc.miro_no
                    grn["sap_status"] = grn_doc.sap_status
                    grn["grn_date"] = grn_doc.grn_date
                    grn["grn_year"] = grn_doc.grn_year
                    grn["company_name"] = grn_doc.company_name

                except Exception as doc_error:
                    grn["attachments"] = []
                    grn["sap_booking_id"] = None
                    grn["miro_no"] = None
                    grn["sap_status"] = None
                    grn["grn_date"] = None
                    grn["grn_year"] = None
                    grn["company_name"] = None

                grn["grn_items"] = grn_items
                result.append(grn)

        return {
            "status": "success",
            "message": "Success",
            "data": result,
            "missing_pos": missing_pos,  # <── Added here
            "pagination": {
                "total_count": len(result),
                "total_count_before_team_filter": total_count_before_filter,
                "limit": limit,
                "offset": offset,
                "has_next": limit and (offset + limit) < len(result),
                "has_previous": offset > 0
            }
        }

    except json.JSONDecodeError:
        frappe.response.http_status_code = 400
        return {
            "status": "error",
            "message": "Failed",
            "error": "Invalid JSON in filters or fields"
        }

    except Exception as e:
        frappe.log_error(str(e), "Error in get_all_grn_details")
        frappe.response.http_status_code = 500
        return {
            "status": "error",
            "message": "Something went wrong while fetching GRNs.",
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_grn_details_of_grn_number(grn_number=None):
    if not grn_number:
        frappe.throw("GRN Number is required")

    user = frappe.session.user

    employee = frappe.get_all("Employee", filters={"user_id": user}, fields=["name", "designation", "team"])

    if not employee:
        frappe.throw("Employee record not found for user.")

    employee = frappe.get_doc("Employee", employee[0]) 

    if employee.designation in ["Purchase Team", "Purchase Head"]:
        user_team = employee.team
        if not user_team:
            frappe.throw("Your team is not mapped. Contact Admin.")

        grn_name = frappe.db.get_value("GRN", {"grn_number": grn_number})
        if not grn_name:
            frappe.throw("GRN not found.")

        try:
            grn_doc = frappe.get_doc("GRN", grn_name)
        except frappe.DoesNotExistError:
            frappe.throw("GRN document does not exist.")

        filtered_items = []

        grn_items = frappe.get_all("GRN Items", fields="*", filters={"parent": grn_name})
        if not grn_items:
            frappe.throw("No GRN Items found in this GRN.")

        for item in grn_items:
            po_no = item.get("po_no")
            plant = item.get("plant")

            if not po_no or not plant:
                continue

            purchase_group = frappe.db.get_value("Purchase Order", po_no, "purchase_group")
            company = frappe.db.get_value("Plant Master", plant, "company")

            if not purchase_group or not company:
                continue

            pg_master_name = f"{purchase_group}-{company}"
            pg_team = frappe.db.get_value("Purchase Group Master", pg_master_name, "team")

            if pg_team and pg_team == user_team:
                filtered_items.append(item)

        if not filtered_items:
            frappe.throw("You are not authorized to view any items in this GRN.")

        attachments_data = []
        if hasattr(grn_doc, 'attachments') and grn_doc.attachments: 
            for attachment in grn_doc.attachments:
                attachment_url = attachment.get('attachment_name')
                attachment_info = {
                    "row_name": attachment.name,    
                    "file_name": attachment.get('name1'),  
                }
                attachments_data.append(attachment_info)


                if attachment_url:
                    try:
                        file_doc = frappe.get_doc("File", {"file_url": attachment_url})
                        attachment_info["full_url"] = f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}"
                        attachment_info["file_doc_name"] = file_doc.name
                        attachment_info["actual_file_name"] = file_doc.file_name
                    except frappe.DoesNotExistError:
                        attachment_info["full_url"] = None
                        attachment_info["error"] = "File document not found"
                    except Exception as e:
                        attachment_info["full_url"] = None
                        attachment_info["error"] = str(e)
                else:
                    attachment_info["full_url"] = None
                
                attachments_data.append(attachment_info)

        return {
            "grn_no": grn_doc.grn_number,
            "grn_date": grn_doc.grn_date,
            "grn_items": filtered_items,
            "sap_booking_id":grn_doc.sap_booking_id,
            "miro_no":grn_doc.miro_no,
            "sap_status": grn_doc.sap_status,
            "grn_year": grn_doc.grn_year,
            "company_name": grn_doc.company_name,
            "attachments": attachments_data
        }
    
    else:
        grn_name = frappe.db.get_value("GRN", {"grn_number": grn_number})
        if not grn_name:
            frappe.throw("GRN not found.")

        try:
            grn_doc = frappe.get_doc("GRN", grn_name)
        except frappe.DoesNotExistError:
            frappe.throw("GRN document does not exist.")

        filtered_items = []

        grn_items = frappe.get_all("GRN Items", fields="*", filters={"parent": grn_name})
        if not grn_items:
            frappe.throw("No GRN Items found in this GRN.")

        # for item in grn_items:
        #     po_no = item.get("po_no")
        #     plant = item.get("plant")

        #     if not po_no or not plant:
        #         continue

        #     purchase_group = frappe.db.get_value("Purchase Order", po_no, "purchase_group")
        #     company = frappe.db.get_value("Plant Master", plant, "company")

        #     if not purchase_group or not company:
        #         continue

        #     pg_master_name = f"{purchase_group}-{company}"
            
        #     filtered_items.append(item)

        
            # frappe.throw("No valid items found in this GRN.")
        for item in grn_items:
            filtered_items.append(item)
            

        attachments_data = []
        if hasattr(grn_doc, 'attachments') and grn_doc.attachments: 
            for attachment in grn_doc.attachments:
                attachment_url = attachment.get('attachment_name')
                attachment_info = {
                    "row_name": attachment.name,    
                    "file_name": attachment.get('name1'),  
                }
                attachments_data.append(attachment_info)


                if attachment_url:
                    try:
                        file_doc = frappe.get_doc("File", {"file_url": attachment_url})
                        attachment_info["full_url"] = f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}"
                        attachment_info["file_doc_name"] = file_doc.name
                        attachment_info["actual_file_name"] = file_doc.file_name
                    except frappe.DoesNotExistError:
                        attachment_info["full_url"] = None
                        attachment_info["error"] = "File document not found"
                    except Exception as e:
                        attachment_info["full_url"] = None
                        attachment_info["error"] = str(e)
                else:
                    attachment_info["full_url"] = None
                
                attachments_data.append(attachment_info)

        return {
            "grn_no": grn_doc.grn_number,
            "grn_date": grn_doc.grn_date,
            "grn_items": filtered_items,
            "sap_booking_id":grn_doc.sap_booking_id,
            "miro_no":grn_doc.miro_no,
            "sap_status": grn_doc.sap_status,
            "grn_year": grn_doc.grn_year,
            "company_name": grn_doc.company_name,
            "attachments": attachments_data
        }



@frappe.whitelist(allow_guest=False)
def filtering_pr_details(page_no=None, page_length=None, company=None, purchase_requisition_type=None, usr=None):
    try:
        if usr is None:
            usr = frappe.session.user
        elif usr != frappe.session.user:
            return {
                "status": "error",
                "message": "User mismatch or unauthorized access.",
                "code": 404
            }


        # Step 1: Get user's team
        employee = frappe.db.get_value("Employee", {"user_id": usr}, ["team", "name"], as_dict=True)
        print("Employee Record:", employee)

        if not employee or not employee.team:
            return {
                "status": "error",
                "message": "No Employee record found for the user or team not assigned.",
                "pr": []
            }

        user_team = employee.team

        # Step 2: Get purchase groups from user's team
        purchase_groups = frappe.get_all(
            "Purchase Group Master",
            filters={"team": user_team},
            pluck="name"
        )

        if not purchase_groups:
            return {
                "status": "error",
                "message": "No purchase groups found for the user's team.",
                "pr": []
            }

        # Step 3: Build dynamic filters
        conditions = []
        values = {}

        conditions.append("prf.purchase_group IN %(purchase_groups)s")
        values["purchase_groups"] = purchase_groups

        if company:
            conditions.append("prf.company = %(company)s")
            values["company"] = company

        if purchase_requisition_type:
            conditions.append("prf.purchase_requisition_type = %(purchase_requisition_type)s")
            values["purchase_requisition_type"] = purchase_requisition_type

        filter_clause = " AND ".join(conditions)

        # Step 4: Pagination
        page_no = int(page_no) if page_no else 1
        page_length = int(page_length) if page_length else 5
        offset = (page_no - 1) * page_length
        values["limit"] = page_length
        values["offset"] = offset

        # Step 5: Get total count
        total_count = frappe.db.sql(f"""
            SELECT COUNT(*) AS count
            FROM `tabPurchase Requisition Form` prf
            WHERE {filter_clause}
        """, values)[0][0]

        # Step 6: Fetch paginated PR Form records
        pr_docs = frappe.db.sql(f"""
            SELECT 
                prf.name,
                prf.purchase_requisition_type,
                prf.sap_pr_code,
                prf.requisitioner,
                prf.purchase_requisition_date
            FROM `tabPurchase Requisition Form` prf
            WHERE {filter_clause}
            ORDER BY prf.creation DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, values, as_dict=True)

        return {
            "status": "200",
            "message": "Filtered PR Form records fetched successfully.",
            "total_count": total_count,
            "page_no": page_no,
            "page_length": page_length,
            "total_pr": pr_docs,
        }

    except Exception as e:
        print("ERROR OCCURRED:")
        print(frappe.get_traceback())
        return {
            "status": "error",
            "message": "Failed to fetch purchase requisition form data.",
            "error": str(e),
            "pr": []
        }

@frappe.whitelist(allow_guest=False)
def get_pr_details_simple(pr_name=None):
    try:
        # Get current user from session
        usr = frappe.session.user
        
        # Validate pr_name parameter
        if not pr_name:
            return {
                "status": "error",
                "message": "Purchase Requisition name is required.",
                "code": 400
            }
        
        # Check if Purchase Requisition Form document exists
        if not frappe.db.exists("Purchase Requisition Form", pr_name):
            return {
                "status": "error",
                "message": f"Purchase Requisition Form '{pr_name}' not found.",
                "code": 404
            }
        

        
        # Get the Purchase Requisition Form document
        pr = frappe.get_doc("Purchase Requisition Form", pr_name)
        
        return {
            "status": "success",
            "message": "Purchase Requisition details fetched successfully.",
            "data": pr.as_dict()
        }
        
    except frappe.PermissionError:
        return {
            "status": "error",
            "message": "Permission denied. You don't have access to this document.",
            "code": 403
        }
    
    except frappe.DoesNotExistError:
        return {
            "status": "error",
            "message": f"Purchase Requisition Form '{pr_name}' does not exist.",
            "code": 404
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get PR Details API Error")
        return {
            "status": "error",
            "message": "Failed to fetch Purchase Requisition details.",
            "error": str(e),
            "code": 500
        }






@frappe.whitelist(allow_guest=True)
def update_grn_with_data():
    form_data = frappe.local.form_dict
    files = frappe.request.files
    
    grn_number = form_data.get("grn_number")
    sap_booking_id = form_data.get("sap_booking_id")
    miro_no = form_data.get("miro_no")
    
    if not grn_number:
        frappe.throw("GRN Number is required")
    
    grn_name = frappe.db.get_value("GRN", {"grn_number": grn_number})
    if not grn_name:
        frappe.throw("GRN not found")
    
    grn_doc = frappe.get_doc("GRN", grn_name)
    
    if sap_booking_id:
        grn_doc.sap_booking_id = sap_booking_id
    
    if miro_no:
        grn_doc.miro_no = miro_no
    
    attachments_added = []
    uploaded_filenames = [] 
    
    if files:
        
        for file_key in files:
            file_list = files.getlist(file_key)  
            
            for uploaded_file in file_list:
                if uploaded_file and uploaded_file.filename:
                    file_doc = save_file(
                        fname=uploaded_file.filename,
                        content=uploaded_file.read(),
                        dt="GRN",
                        dn=grn_doc.name,
                        is_private=1
                    )
                
                    attachment_row = grn_doc.append("attachments", {})
                    attachment_row.attachment_name = file_doc.file_url 
                    attachment_row.name1 = uploaded_file.filename
                    
                   
                    uploaded_filenames.append(uploaded_file.filename)
    
    grn_doc.save()
    
   
    if uploaded_filenames:
        for attachment in grn_doc.attachments:
            if attachment.name1 in uploaded_filenames:
                attachments_added.append({
                    "attachment_name": attachment.attachment_name,
                    "row_name": attachment.name,  
                    "file_name": attachment.name1
                })
               
                uploaded_filenames.remove(attachment.name1)
    
    frappe.db.commit()
    
    return {
        "status": "success",
        "message": "GRN updated successfully",
        "grn_number": grn_doc.grn_number,
        "attachments": attachments_added
    }

@frappe.whitelist(allow_guest=True)
def delete_grn_attachments():
    form_data = frappe.local.form_dict
    
    grn_number = form_data.get("grn_number")
    row_names = form_data.get("row_names") 
    
    if not grn_number:
        frappe.throw("GRN Number is required")
    
    if not row_names:
        frappe.throw("Row names are required")
    
  
    if isinstance(row_names, str):
        import json
        try:
            row_names = json.loads(row_names)
        except:
            row_names = [row_names]  
    
    
    grn_name = frappe.db.get_value("GRN", {"grn_number": grn_number})
    if not grn_name:
        frappe.throw("GRN not found")
    
    grn_doc = frappe.get_doc("GRN", grn_name)
    
    deleted_attachments = []
    
    
    for row_name in row_names:
        for i, attachment in enumerate(grn_doc.attachments):
            if attachment.name == row_name:
                deleted_attachments.append({
                    "row_name": attachment.name,
                    "file_name": attachment.name1,
                    "attachment_name": attachment.attachment_name
                })
                
                grn_doc.attachments.pop(i)
                break
    

    grn_doc.save()
    frappe.db.commit()
    
    return {
        "status": "success",
        "message": f"Deleted {len(deleted_attachments)} attachment(s) successfully",
        "grn_number": grn_doc.grn_number,
        "deleted_attachments": deleted_attachments
    }


# @frappe.whitelist()
# def get_all_grn_details():
#     try:
#         print("Fetching all GRN records...")
#         grn_list = frappe.get_all(
#             "GRN",
#             fields="*",
#             filters={},
#         )
#         print(f"Fetched GRN records: {len(grn_list)}")

#         for grn in grn_list:
#             print(f"Fetching child items for GRN: {grn['name']}")
#             grn_items = frappe.get_all(
#                 "GRN Items",
#                 fields="*",
#                 filters={"parent": grn["name"]},
#             )
#             print(f"Fetched {len(grn_items)} items for GRN: {grn['name']}")
#             grn["grn_items"] = grn_items

#         if grn_items:
#                 po_number = grn_items[0].get("po_no")
#                 if po_number:
#                     print(f"Fetching Purchase Order details for PO No.: {po_number}")
#                     purchase_order = frappe.get_doc("Purchase Order", po_number)

#                     purchase_group = purchase_order.get("purchase_group")
#                     if purchase_group:
#                         print(f"Fetching Purchase Group details for: {purchase_group}")
#                         purchase_group_doc = frappe.get_doc("Purchase Group Master", purchase_group)

#                         team_value = purchase_group_doc.get("team")
#                         print(f"Team value fetched for Purchase Group {purchase_group}: {team_value}")

#                         grn["team"] = team_value

#         print("Completed fetching all GRN details.")
#         return grn_list

#     except Exception as e:
#         error_message = str(e)
#         print(f"Error occurred: {error_message}")
#         frappe.log_error(message=error_message, title="Error in fetching GRN details")
#         frappe.throw(_("An error occurred while fetching GRN details. Please check the logs for more details."))


# @frappe.whitelist()
# def get_all_grn_details():
#     try:
#         print("Fetching all GRN records...")
#         grn_list = frappe.get_all(
#             "GRN",
#             fields="*",
#             filters={},
#         )
#         print(f"Fetched GRN records: {len(grn_list)}")

#         for grn in grn_list:
#             print(f"\nProcessing GRN: {grn['name']}")

#             grn_items = frappe.get_all(
#                 "GRN Items",
#                 fields="*",
#                 filters={"parent": grn["name"]},
#             )

#             for item in grn_items:
#                 po_number = item.get("po_no")
#                 plant_code = item.get("plant")

#                 if not po_number or not plant_code:
#                     print(f"Missing PO or Plant Code in item {item.get('name')}, skipping team fetch.")
#                     item["team"] = None
#                     continue

#                 try:
#                     purchase_order = frappe.get_doc("Purchase Order", po_number)
#                     base_purchase_group = purchase_order.get("purchase_group")
#                 except frappe.DoesNotExistError:
#                     print(f"Purchase Order {po_number} not found.")
#                     item["team"] = None
#                     continue

#                 if not base_purchase_group:
#                     print(f"No purchase group in PO {po_number}")
#                     item["team"] = None
#                     continue

#                 try:
#                     plant_master = frappe.get_doc("Plant Master", plant_code)
#                     company_code = plant_master.get("company")
#                 except frappe.DoesNotExistError:
#                     print(f"Plant Master not found for Plant Code: {plant_code}")
#                     item["team"] = None
#                     continue

#                 if not company_code:
#                     print(f"No company code found for Plant {plant_code}")
#                     item["team"] = None
#                     continue

#                 full_purchase_group_id = f"{base_purchase_group}-{company_code}"
#                 print(f"Full Purchase Group ID: {full_purchase_group_id}")

#                 try:
#                     pg_doc = frappe.get_doc("Purchase Group Master", full_purchase_group_id)
#                     team = pg_doc.get("team")
#                     item["team"] = team
#                     print(f"Team for {full_purchase_group_id} is {team}")
#                 except frappe.DoesNotExistError:
#                     print(f"Purchase Group Master {full_purchase_group_id} not found.")
#                     item["team"] = None

#             grn["grn_items"] = grn_items  # update with enriched items

#         print("\nCompleted fetching all GRN details.")
#         return grn_list

#     except Exception as e:
#         error_message = str(e)
#         print(f"Error occurred: {error_message}")
#         frappe.log_error(message=error_message, title="Error in fetching GRN details")
#         frappe.throw(_("An error occurred while fetching GRN details. Please check the logs for more details."))

# @frappe.whitelist()
# def get_all_grn_details():
#     try:
#         print("Fetching all GRN records...")
#         user = frappe.session.user
#         team = frappe.db.get_value("Employee", {"user_id": user}, "team")
#         grns = frappe.get_all("GRN", fields="*")
#         print(f"📄 Total GRNs fetched: {len(grns)}")
#         pg_team_map = {}
#         if team:
#             pg_list = frappe.get_all("Purchase Group Master", filters={"team": team}, fields=["purchase_group_code", "company"])
#             pg_team_map = {(pg["purchase_group_code"], pg["company"]) for pg in pg_list}
#             print(f"🔗 Purchase Group Mappings for team: {pg_team_map}")
#         result = []
#         for grn in grns:
#             grn_items = frappe.get_all("GRN Items", fields="*", filters={"parent": grn["name"]})
#             found_match = False

#             for item in grn_items:
#                 po_no, plant = item.get("po_no"), item.get("plant")

#                 if not (po_no and plant):
#                     continue

#                 company = frappe.db.get_value("Plant Master", plant, "company")
#                 pg_code = frappe.db.get_value("Purchase Order", po_no, "purchase_group")

#                 if (pg_code, company) in pg_team_map:
#                     found_match = True
#                     break

#             if found_match or not team:
#                 grn["grn_items"] = grn_items
#                 result.append(grn)

#         print(f"Returning {len(result)} GRNs after filtering.")
#         return result

#     except Exception as e:
#         frappe.log_error(str(e), "Error in get_all_grn_details")
#         frappe.throw(_("Something went wrong while fetching GRNs."))

#-----------------------------------------------------------------------------------------------------------------------------------------------
# @frappe.whitelist()
# def get_grn_details_of_grn_number(grn_number=None):
#     if not grn_number:
#         frappe.throw("GRN Number is required")

#     user = frappe.session.user
#     user_team = frappe.db.get_value("Employee", {"user_id": user}, "team")

#     if not user_team:
#         frappe.throw("Your team is not mapped. Contact Admin.")

#     grn_name = frappe.db.get_value("GRN", {"grn_number": grn_number})
#     if not grn_name:
#         frappe.throw("GRN not found.")

#     try:
#         grn_doc = frappe.get_doc("GRN", grn_name)
#     except frappe.DoesNotExistError:
#         frappe.throw("GRN document does not exist.")

#     filtered_items = []

#     grn_items = frappe.get_all("GRN Items", fields="*", filters={"parent": grn_name})
#     if not grn_items:
#         frappe.throw("No GRN Items found in this GRN.")

#     for item in grn_items:
#         po_no = item.get("po_no")
#         plant = item.get("plant")

#         if not po_no or not plant:
#             continue

#         purchase_group = frappe.db.get_value("Purchase Order", po_no, "purchase_group")
#         company = frappe.db.get_value("Plant Master", plant, "company")

#         if not purchase_group or not company:
#             continue

#         pg_master_name = f"{purchase_group}-{company}"
#         pg_team = frappe.db.get_value("Purchase Group Master", pg_master_name, "team")

#         if pg_team and pg_team == user_team:
#             filtered_items.append(item)

#     if not filtered_items:
#         frappe.throw("You are not authorized to view any items in this GRN.")

#     return {
#         "grn_no": grn_doc.grn_number,
#         "grn_date": grn_doc.grn_date,
#         "grn_items": filtered_items
#     }





# @frappe.whitelist(allow_guest=False)
# def get_grn_details_of_grn_number(grn_number=None, page_no=None, page_length=None):
#     try:
#         # Validate grn_number parameter
#         if not grn_number:
#             return {
#                 "status": "error",
#                 "message": "GRN Number is required.",
#                 "code": 400
#             }

#         # Get current user and validate team
#         user = frappe.session.user
#         user_team = frappe.db.get_value("Employee", {"user_id": user}, "team")

#         if not user_team:
#             return {
#                 "status": "error",
#                 "message": "Your team is not mapped. Contact Admin.",
#                 "code": 403
#             }

#         # Check if GRN exists
#         grn_name = frappe.db.get_value("GRN", {"grn_number": grn_number})
#         if not grn_name:
#             return {
#                 "status": "error",
#                 "message": "GRN not found.",
#                 "code": 404
#             }

#         # Get GRN document
#         try:
#             grn_doc = frappe.get_doc("GRN", grn_name)
#         except frappe.DoesNotExistError:
#             return {
#                 "status": "error",
#                 "message": "GRN document does not exist.",
#                 "code": 404
#             }

#         # Get all GRN items
#         grn_items = frappe.get_all("GRN Items", fields="*", filters={"parent": grn_name})
#         if not grn_items:
#             return {
#                 "status": "error",
#                 "message": "No GRN Items found in this GRN.",
#                 "code": 404
#             }

#         # Filter items based on team authorization
#         filtered_items = []
        
#         for item in grn_items:
#             try:
#                 po_no = item.get("po_no")
#                 plant = item.get("plant")

#                 if not po_no or not plant:
#                     continue

#                 # Get purchase group from PO
#                 purchase_group = frappe.db.get_value("Purchase Order", po_no, "purchase_group")
#                 if not purchase_group:
#                     continue

#                 # Get company from plant
#                 company = frappe.db.get_value("Plant Master", plant, "company")
#                 if not company:
#                     continue

#                 # Check team authorization
#                 pg_master_name = f"{purchase_group}-{company}"
#                 pg_team = frappe.db.get_value("Purchase Group Master", pg_master_name, "team")

#                 if pg_team and pg_team == user_team:
#                     filtered_items.append(item)

#             except Exception as item_error:
#                 # Log individual item processing errors but continue
#                 frappe.log_error(f"Error processing GRN item {item.get('name', 'Unknown')}: {str(item_error)}", 
#                                "GRN Item Processing Error")
#                 continue

#         if not filtered_items:
#             return {
#                 "status": "error",
#                 "message": "You are not authorized to view any items in this GRN.",
#                 "code": 403
#             }

#         # Pagination setup
#         total_items = len(filtered_items)
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 10
        
#         # Enforce maximum limit of 20
#         if page_length > 20:
#             page_length = 20
        
#         # Calculate pagination
#         offset = (page_no - 1) * page_length
#         end_index = offset + page_length
        
#         # Slice the filtered items for pagination
#         paginated_items = filtered_items[offset:end_index]
        
#         # Calculate total pages
#         total_pages = (total_items + page_length - 1) // page_length

#         return {
#             "status": "success",
#             "message": "GRN details fetched successfully.",
#             "data": {
#                 "grn_no": grn_doc.grn_number,
#                 "grn_date": grn_doc.grn_date,
#                 "grn_items": paginated_items
#             },
#             "pagination": {
#                 "total_items": total_items,
#                 "page_no": page_no,
#                 "page_length": page_length,
#                 "total_pages": total_pages,
#                 "has_next_page": page_no < total_pages,
#                 "has_previous_page": page_no > 1
#             }
#         }

#     except ValueError as ve:
#         return {
#             "status": "error",
#             "message": f"Invalid parameter value: {str(ve)}",
#             "code": 400
#         }
    
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "GRN Details API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch GRN details.",
#             "error": str(e),
#             "code": 500
#         }




# Alternative version with database-level filtering for better performance
# @frappe.whitelist(allow_guest=False)
# def get_grn_details_of_grn_number_optimized(grn_number=None, page_no=None, page_length=None):
#     try:
#         # Validate grn_number parameter
#         if not grn_number:
#             return {
#                 "status": "error",
#                 "message": "GRN Number is required.",
#                 "code": 400
#             }

#         # Get current user and validate team
#         user = frappe.session.user
#         user_team = frappe.db.get_value("Employee", {"user_id": user}, "team")

#         if not user_team:
#             return {
#                 "status": "error",
#                 "message": "Your team is not mapped. Contact Admin.",
#                 "code": 403
#             }

#         # Check if GRN exists
#         grn_name = frappe.db.get_value("GRN", {"grn_number": grn_number})
#         if not grn_name:
#             return {
#                 "status": "error",
#                 "message": "GRN not found.",
#                 "code": 404
#             }

#         # Get GRN document
#         try:
#             grn_doc = frappe.get_doc("GRN", grn_name)
#         except frappe.DoesNotExistError:
#             return {
#                 "status": "error",
#                 "message": "GRN document does not exist.",
#                 "code": 404
#             }

#         # Get purchase groups for user's team
#         purchase_groups = frappe.get_all("Purchase Group Master", 
#                                         filters={"team": user_team}, 
#                                         pluck="name")
        
#         if not purchase_groups:
#             return {
#                 "status": "error",
#                 "message": "No purchase groups found for your team.",
#                 "code": 403
#             }

#         # Pagination setup
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 10
        
#         # Enforce maximum limit of 20
#         if page_length > 20:
#             page_length = 20
        
#         offset = (page_no - 1) * page_length

#         # Database query to get filtered and paginated items
#         items_query = f"""
#             SELECT gi.*, 
#                    CONCAT(po.purchase_group, '-', pm.company) as pg_master_name
#             FROM `tabGRN Items` gi
#             LEFT JOIN `tabPurchase Order` po ON gi.po_no = po.name
#             LEFT JOIN `tabPlant Master` pm ON gi.plant = pm.name
#             WHERE gi.parent = %(grn_name)s
#               AND po.purchase_group IS NOT NULL
#               AND pm.company IS NOT NULL
#               AND CONCAT(po.purchase_group, '-', pm.company) IN %(purchase_groups)s
#             ORDER BY gi.idx
#             LIMIT %(limit)s OFFSET %(offset)s
#         """

#         # Count query for total items
#         count_query = f"""
#             SELECT COUNT(*) as total
#             FROM `tabGRN Items` gi
#             LEFT JOIN `tabPurchase Order` po ON gi.po_no = po.name
#             LEFT JOIN `tabPlant Master` pm ON gi.plant = pm.name
#             WHERE gi.parent = %(grn_name)s
#               AND po.purchase_group IS NOT NULL
#               AND pm.company IS NOT NULL
#               AND CONCAT(po.purchase_group, '-', pm.company) IN %(purchase_groups)s
#         """

#         # Execute queries
#         values = {
#             "grn_name": grn_name,
#             "purchase_groups": purchase_groups,
#             "limit": page_length,
#             "offset": offset
#         }

#         # Get total count
#         total_count_result = frappe.db.sql(count_query, values, as_dict=True)
#         total_items = total_count_result[0]["total"] if total_count_result else 0

#         if total_items == 0:
#             return {
#                 "status": "error",
#                 "message": "You are not authorized to view any items in this GRN.",
#                 "code": 403
#             }

#         # Get paginated items
#         filtered_items = frappe.db.sql(items_query, values, as_dict=True)

#         # Calculate total pages
#         total_pages = (total_items + page_length - 1) // page_length

#         return {
#             "status": "success",
#             "message": "GRN details fetched successfully.",
#             "data": {
#                 "grn_no": grn_doc.grn_number,
#                 "grn_date": grn_doc.grn_date,
#                 "grn_items": filtered_items
#             },
#             "pagination": {
#                 "total_items": total_items,
#                 "page_no": page_no,
#                 "page_length": page_length,
#                 "total_pages": total_pages,
#                 "has_next_page": page_no < total_pages,
#                 "has_previous_page": page_no > 1
#             }
#         }

#     except ValueError as ve:
#         return {
#             "status": "error",
#             "message": f"Invalid parameter value: {str(ve)}",
#             "code": 400
#         }
    
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "GRN Details Optimized API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch GRN details.",
#             "error": str(e),
#             "code": 500
#         }

# @frappe.whitelist(allow_guest=False)
# def filtering_pr_details(page_no=None, page_length=None, company=None, purchase_requisition_type=None, usr=None):
#     try:
#         if usr is None:
#             usr = frappe.session.user
#         elif usr != frappe.session.user:
#             return {
#                 "status": "error",
#                 "message": "User mismatch or unauthorized access.",
#                 "code": 404
#             }

#         # Get user's employee record and team
#         employee = frappe.db.get_value("Employee", {"user_id": usr}, ["team", "name"], as_dict=True)
#         if not employee or not employee.team:
#             return {
#                 "status": "error",
#                 "message": "No Employee record found for the user or team not assigned.",
#                 "pr": []
#             }

#         user_team = employee.team

#         # Get all purchase groups that belong to the same team
#         purchase_groups = frappe.get_all("Purchase Group Master", 
#                                         filters={"team": user_team}, 
#                                         pluck="name")
        
#         if not purchase_groups:
#             return {
#                 "status": "error",
#                 "message": "No purchase groups found for the user's team.",
#                 "pr": []
#             }

#         # Base filters
#         conditions = []
#         values = {}

#         # Filter by purchase groups (team-based filtering)
#         conditions.append("pr.purchase_group IN %(purchase_groups)s")
#         values["purchase_groups"] = purchase_groups

#         # Add additional filters if provided
#         if company:
#             conditions.append("pr.company = %(company)s")
#             values["company"] = company
            
#         if purchase_requisition_type:
#             conditions.append("pr.purchase_requisition_type = %(purchase_requisition_type)s")
#             values["purchase_requisition_type"] = purchase_requisition_type
            
#         # if status:
#         #     conditions.append("pr.status = %(status)s")
#         #     values["status"] = status

#         filter_clause = " AND ".join(conditions)

        
#         total_count = frappe.db.sql(f"""
#             SELECT COUNT(*) AS count
#             FROM `tabPurchase Requisition` pr
#             WHERE {filter_clause}
#         """, values)[0][0]

       
#         page_no = int(page_no) if page_no else 1
#         page_length = int(page_length) if page_length else 5
#         offset = (page_no - 1) * page_length
#         values["limit"] = page_length
#         values["offset"] = offset

        
#         pr_docs = frappe.db.sql(f"""
#             SELECT 
#                 pr.name,
#                 pr.purchase_requisition_type,
#                 pr.sap_pr_code,
#                 pr.requisitioner,
#                 prt.purchase_requisition_date_head
#             FROM `tabPurchase Requisition Form` pr
#             LEFT JOIN `tabPurchase Requisition Form Table` prt ON pr.name = prt.parent
#             WHERE {filter_clause}
#             ORDER BY pr.creation DESC
#             LIMIT %(limit)s OFFSET %(offset)s
#         """, values, as_dict=True)

#         return {
#             "status": "success",
#             "message": "Paginated and filtered purchase requisition records fetched successfully.",
#             "total_count": total_count,
#             "page_no": page_no,
#             "page_length": page_length,
#             "total_pr": pr_docs,
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Purchase Requisition Details API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch purchase requisition data.",
#             "error": str(e),
#             "pr": []
#         }
    



# @frappe.whitelist(allow_guest=False)
# def get_pr_details_simple(pr_name=None):
#     try:
#         # Get current user from session
#         usr = frappe.session.user
        
#         # Validate pr_name parameter
#         if not pr_name:
#             return {
#                 "status": "error",
#                 "message": "Purchase Requisition name is required.",
#                 "code": 400
#             }
        
#         # Check if Purchase Requisition Form document exists
#         if not frappe.db.exists("Purchase Requisition Form", pr_name):
#             return {
#                 "status": "error",
#                 "message": f"Purchase Requisition Form '{pr_name}' not found.",
#                 "code": 404
#             }
        

        
#         # Get the Purchase Requisition Form document
#         pr = frappe.get_doc("Purchase Requisition Form", pr_name)
        
#         return {
#             "status": "success",
#             "message": "Purchase Requisition details fetched successfully.",
#             "data": pr.as_dict()
#         }
        
#     except frappe.PermissionError:
#         return {
#             "status": "error",
#             "message": "Permission denied. You don't have access to this document.",
#             "code": 403
#         }
    
#     except frappe.DoesNotExistError:
#         return {
#             "status": "error",
#             "message": f"Purchase Requisition Form '{pr_name}' does not exist.",
#             "code": 404
#         }
    
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Get PR Details API Error")
#         return {
#             "status": "error",
#             "message": "Failed to fetch Purchase Requisition details.",
#             "error": str(e),
#             "code": 500
#         }