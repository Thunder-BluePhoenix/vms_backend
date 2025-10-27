# import frappe
# from frappe import _
# import json
# import requests
# from requests.auth import HTTPBasicAuth
# from datetime import datetime



# @frappe.whitelist(allow_guest=True)
# def erp_to_sap_pr(doc_name, method=None):
#     print("SEND data to sap run")
#     doc = frappe.get_doc("Purchase Requisition Form", doc_name)
#     sap_client_code = doc.sap_client_code
#     now = datetime.now()
#     year_month_prefix = f"P{now.strftime('%y')}{now.strftime('%m')}"  # e.g. PRF2506

#     # Get max existing count for this prefix
#     # Filter by prf_name_for_sap starting with year_month_prefix
#     existing_max = frappe.db.sql(
#         """
#         SELECT MAX(CAST(SUBSTRING(prf_name_for_sap, 8) AS UNSIGNED))
#         FROM `tabPurchase Requisition Form`
#         WHERE prf_name_for_sap LIKE %s
#         """,
#         (year_month_prefix + "%",),
#         as_list=True
#     )

#     max_count = existing_max[0][0] or 0
#     new_count = max_count + 1

#     # Format new prf_name_for_sap with zero-padded count (6 digits)
#     name_for_sap = f"{year_month_prefix}{str(new_count).zfill(5)}"

    
#     data_list = None
#     data = None
#     subdata =None


#     if doc.purchase_requisition_type == "NB":
#         data_list = {
#             "Banfn": "",
#             "Ztype": "",
#             "Ztext": "",
#             "Zvmsprno": "",
#             "ItemSet":[]
#         }
#         # child_data = []
#         for item in doc.purchase_requisition_form_table:
            
#             data =  {
#                     "Bnfpo" : item.item_number_of_purchase_requisition_head or "",
#                     "Matnr" : item.material_code_head or "",
#                     "Txz01" : item.short_text_head or "",
#                     "Menge" : item.quantity_head or "",
#                     "Meins" : item.uom_head or "",
#                     "Werks" : item.plant_head or "",
#                     "Lgort" : item.store_location_head or "",
#                     "Afnam" : item.requisitioner_name_head or "",
#                     "Bsart" : item.purchase_requisition_type or "",
#                     "Ekgrp" : item.purchase_grp_code_head or "",
#                     "Ernam" : item.requisitioner_name_head or "",
#                     "Erdat": item.purchase_requisition_date_head.strftime("%Y%m%d") if item.purchase_requisition_date_head else "",
#                     "Badat": item.delivery_date_head.strftime("%Y%m%d") if item.delivery_date_head else "",
#                     "Anln1" : item.main_asset_no_head or "",
#                     "Anln2" : item.asset_subnumber_head or "",
#                     "Knttp" : item.account_assignment_category_head or "",
#                     "Pstyp" : item.item_category_head or "",
#                     "Sakto" : item.gl_account_number_head or "",
#                     "Kostl" : item.cost_center_head or "",
#                     "Preis" : item.final_price_by_purchase_team_head or "",
#                     "Zvmsprno": doc.prf_name_for_sap or name_for_sap
#                     }

#             data_list["ItemSet"].append(data)
#             print("json data", data)

#             print("data_list", data_list)


#     elif doc.purchase_requisition_type == "SB":
#         data_list = {
#             "Banfn": "",
#             "Ztype": "",
#             "Ztext": "",
#             "Zvmsprno": "",
#             "ItemSet":[],
#             "ServSet":[],
#         }
        
#         # Group items by head_unique_id
#         head_groups = {}
#         for item in doc.purchase_requisition_form_table:
#             head_id = item.head_unique_id
#             if head_id not in head_groups:
#                 head_groups[head_id] = []
#             head_groups[head_id].append(item)
        
#         # Process ItemSet - one row per unique head_unique_id
#         packno_counter = 1
#         head_to_packno = {}  # Map head_unique_id to its packno
        
#         for head_id, items in head_groups.items():
#             # Take the first item for this head_unique_id
#             first_item = items[0]
            
#             # Assign packno to this head_unique_id
#             head_to_packno[head_id] = str(packno_counter)
            
#             data = {
#                 "Bnfpo": first_item.item_number_of_purchase_requisition_head or "",
#                 "Matnr": first_item.material_code_head or "",
#                 "Txz01": first_item.short_text_head or "",
#                 "Menge": first_item.quantity_head or "",
#                 "Meins": first_item.uom_head or "",
#                 "Werks": first_item.plant_head or "",
#                 "Lgort": first_item.store_location_head or "",
#                 "Afnam": first_item.requisitioner_name_head or "",
#                 "Bsart": first_item.purchase_requisition_type or "",
#                 "Ekgrp": first_item.purchase_grp_code_head or "",
#                 "Ernam": first_item.requisitioner_name_head or "",
#                 "Erdat": first_item.purchase_requisition_date_head.strftime("%Y%m%d") if first_item.purchase_requisition_date_head else "",
#                 "Badat": first_item.delivery_date_head.strftime("%Y%m%d") if first_item.delivery_date_head else "",
#                 "Anln1": first_item.main_asset_no_head or "",
#                 "Anln2": first_item.asset_subnumber_head or "",
#                 "Knttp": first_item.account_assignment_category_head or "",
#                 "Pstyp": first_item.item_category_head or "",
#                 "Sakto": first_item.gl_account_number_head or "",
#                 "Kostl": first_item.cost_center_head or "",
#                 "Preis": first_item.final_price_by_purchase_team_head or "",
#                 "Zvmsprno": doc.prf_name_for_sap or name_for_sap,
#                 "Packno": str(packno_counter)
#             }
            
#             data_list["ItemSet"].append(data)
#             packno_counter += 1
        
#         # Process ServSet - all rows grouped by head_unique_id
#         for head_id, items in head_groups.items():
#             packno = head_to_packno[head_id]  # Use the same packno as ItemSet
            
#             for item in items:
#                 subdata = {
#                     "Bnfpo": item.item_number_of_purchase_requisition_subhead or "",
#                     "Packno": packno,
#                     "Introw": "1",
#                     "Extrow": "1",
#                     "Subpackno": "",
#                     "Spackage": "",
#                     "Frompos": "",
#                     "Srvpos": "",
#                     "Ktext1": item.short_text_subhead or "",
#                     "Menge": item.quantity_subhead or "",
#                     "Meins": item.uom_subhead or "",
#                     "Brtwr": item.gross_price_subhead or "",
#                     "Zebkn": "",
#                     "Kostl": item.cost_center_subhead or "",
#                     "Sakto": item.gl_account_number_subhead or ""
#                 }
                
#                 data_list["ServSet"].append(subdata)

#         print("json data for SB type", data_list)
#         print("json data", data)

#         print("data_list", data_list)






#         # data_list = ["ItemSet"]

#     sap_settings = frappe.get_doc("SAP Settings")
#     erp_to_sap_pr_url = sap_settings.sap_pr_url
#     url = f"{erp_to_sap_pr_url}{sap_client_code}"
#     header_auth_type = sap_settings.authorization_type
#     header_auth_key = sap_settings.authorization_key
#     user = sap_settings.auth_user_name
#     password = sap_settings.auth_user_pass

#     headers = {
#         'x-csrf-token': 'fetch',
#         'Authorization': f"{header_auth_type} {header_auth_key}",
#         'Content-Type': 'application/json'
#     }

    
#     auth = HTTPBasicAuth(user, password)
#     response = requests.get(url, headers=headers, auth=auth)
#     print("resssssssssssssssssssssssssss",response.text)

#     if response.status_code == 200:
        
#         csrf_token = response.headers.get('x-csrf-token')
#         key1 = response.cookies.get(f'SAP_SESSIONID_BHD_{sap_client_code}')
#         key2 = response.cookies.get('sap-usercontext')
        
#         # Sending details to SAP
#         send_detail(csrf_token, data_list, key1, key2, doc, sap_client_code)
        
#         return data_list
#     else:
#         frappe.log_error(f"Failed to fetch CSRF token from SAP: {response.status_code if response else 'No response'}")
#         return None
    

# def safe_get(obj, list_name, index, attr, default=""):
#     try:
#         return getattr(getattr(obj, list_name)[index], attr) or default
#     except (AttributeError, IndexError, TypeError):
#         return default






# @frappe.whitelist(allow_guest=True)
# def send_detail(csrf_token, data_list, key1, key2, doc, sap_code):

#     sap_settings = frappe.get_doc("SAP Settings")
#     erp_to_sap_pr_url = sap_settings.sap_pr_url
#     url = f"{erp_to_sap_pr_url}{sap_code}"
#     header_auth_type = sap_settings.authorization_type
#     header_auth_key = sap_settings.authorization_key
#     user = sap_settings.auth_user_name
#     password = sap_settings.auth_user_pass

#     headers = {
#         'X-CSRF-TOKEN': csrf_token,
#         'Authorization': f"{header_auth_type} {header_auth_key}",
#         'Content-Type': 'application/json;charset=utf-8',
#         'Accept': 'application/json',
#         'Cookie': f"SAP_SESSIONID_BHD_{sap_code}={key1}; sap-usercontext={key2}"
#     }

#     auth = HTTPBasicAuth(user, password)
#     print("*************")
    
#     try:
#         response = requests.post(url, headers=headers, auth=auth, json=data_list)
#         pr_sap_code = response.json()
#         pr_code = pr_sap_code['d']['Banfn']
#         # print("response", response.json())
        
        


#         # pr_doc = frappe.get_doc("Purchase Requisition Form", name)
#         doc.sent_to_sap = 1
#         doc.sap_pr_code = pr_code
#         doc.db_update()
#         print(doc)

        
        
        
#         sap_log = frappe.new_doc("VMS SAP Logs")
#         sap_log.purchase_requisition_link = doc.name
#         sap_log.erp_to_sap_data = data_list
#         sap_log.sap_response = response.text

#         sap_log.save(ignore_permissions=True)
        

        
#         frappe.db.commit()
        
#         return response.json()
#     except ValueError:
#         print("************************** Response is here *********************", response.json())
#         sap_log = frappe.new_doc("VMS SAP Logs")
#         sap_log.purchase_requisition_link = doc.name
#         sap_log.erp_to_sap_data = data_list
#         sap_log.sap_response = response.text

#         sap_log.save(ignore_permissions=True)
    
    
#     if response.status_code == 201:  
#         print("*****************************************")
#         print("Vendor details posted successfully.")
#         return response.json()
    

#     else:
#         print("******************************************")
#         print("Error in POST request:", response.status_code)
        












#______________________---------------------------------------------------------------below was working--------------------------------------------------


# import frappe
# from frappe import _
# import json
# import requests
# from requests.auth import HTTPBasicAuth
# from requests.exceptions import RequestException, JSONDecodeError
# from datetime import datetime

# @frappe.whitelist(allow_guest=True)
# def erp_to_sap_pr(doc_name, method=None):
#     print("=" * 80)
#     print("SEND PR DATA TO SAP - STARTING")
#     print("=" * 80)
    
#     try:
#         doc = frappe.get_doc("Purchase Requisition Form", doc_name)
#         sap_client_code = doc.sap_client_code
#         now = datetime.now()
#         year_month_prefix = f"P{now.strftime('%y')}{now.strftime('%m')}"  # e.g. PRF2506

#         # Get max existing count for this prefix
#         existing_max = frappe.db.sql(
#             """
#             SELECT MAX(CAST(SUBSTRING(prf_name_for_sap, 8) AS UNSIGNED))
#             FROM `tabPurchase Requisition Form`
#             WHERE prf_name_for_sap LIKE %s
#             """,
#             (year_month_prefix + "%",),
#             as_list=True
#         )

#         max_count = existing_max[0][0] or 0
#         new_count = max_count + 1
#         name_for_sap = f"{year_month_prefix}{str(new_count).zfill(5)}"

#         # Build data payload based on PR type
#         data_list = build_pr_payload(doc, name_for_sap)
        
#         if not data_list:
#             error_msg = "Failed to build PR payload"
#             frappe.log_error(error_msg)
#             return {"error": error_msg}

#         # Get CSRF token and session
#         csrf_result = get_pr_csrf_token_and_session(sap_client_code)
        
#         if csrf_result["success"]:
#             try:
#                 # Send details to SAP
#                 result = send_pr_detail(
#                     csrf_result["csrf_token"], 
#                     data_list, 
#                     csrf_result["session_cookies"],
#                     doc, 
#                     sap_client_code,
#                     name_for_sap
#                 )
#                 return result
                
#             except Exception as send_detail_err:
#                 error_msg = f"send_pr_detail error: {str(send_detail_err)[:100]}"
#                 print(f"❌ {error_msg}")
#                 # Don't use frappe.log_error to avoid cascading errors
#                 return {"error": error_msg}
#         else:
#             error_msg = f"CSRF token failed: {csrf_result['error'][:100]}"
#             print(f"❌ {error_msg}")
#             # Don't use frappe.log_error to avoid cascading errors
#             return {"error": error_msg}
            
#     except Exception as main_err:
#         error_msg = f"Main error: {str(main_err)[:100]}"
#         print(f"❌ {error_msg}")
#         # Don't use frappe.log_error to avoid cascading errors
#         return {"error": error_msg}


# def build_pr_payload(doc, name_for_sap):
#     """Build PR payload based on purchase requisition type"""
#     try:
#         if doc.purchase_requisition_type == "NB":
#             data_list = {
#                 "Banfn": "",
#                 "Ztype": "",
#                 "Ztext": "",
#                 "Zvmsprno": "",
#                 "ItemSet": []
#             }
            
#             for item in doc.purchase_requisition_form_table:
#                 data = {
#                     "Bnfpo": item.item_number_of_purchase_requisition_head or "",
#                     "Matnr": item.material_code_head or "",
#                     "Txz01": item.short_text_head or "",
#                     "Menge": item.quantity_head or "",
#                     "Meins": item.uom_head or "",
#                     "Werks": frappe.db.get_value("Plant Master", item.plant_head, "plant_code") or "",
#                     "Lgort": frappe.db.get_value("Storage Location Master", item.store_location_head, "storage_location")or "",
#                     "Afnam": doc.requisitioner_first_name or "",
#                     "Bsart": item.purchase_requisition_type or "",
#                     "Ekgrp": item.purchase_grp_code_head or "",
#                     "Ernam": doc.requisitioner_first_name or "",
#                     "Erdat": item.purchase_requisition_date_head.strftime("%Y%m%d") if item.purchase_requisition_date_head else "",
#                     "Badat": item.delivery_date_head.strftime("%Y%m%d") if item.delivery_date_head else "",
#                     "Anln1": item.main_asset_no_head or "",
#                     "Anln2": item.asset_subnumber_head or "",
#                     "Knttp": item.account_assignment_category_head or "",
#                     "Pstyp": item.item_category_head or "",
#                     "Sakto": item.gl_account_number_head or "",
#                     "Kostl": item.cost_center_head or "",
#                     "Preis": item.final_price_by_purchase_team_head or "",
#                     "Zvmsprno": doc.prf_name_for_sap or name_for_sap
#                 }
#                 data_list["ItemSet"].append(data)

#         elif doc.purchase_requisition_type == "SB":
#             data_list = {
#                 "Banfn": "",
#                 "Ztype": "",
#                 "Ztext": "",
#                 "Zvmsprno": "",
#                 "ItemSet": []
#             }
            
#             # Group items by head_unique_id
#             head_groups = {}
#             for item in doc.purchase_requisition_form_table:
#                 head_id = item.head_unique_id
#                 if head_id not in head_groups:
#                     head_groups[head_id] = []
#                 head_groups[head_id].append(item)
            
#             # Process ItemSet - one row per unique head_unique_id
#             packno_counter = 1
#             head_to_packno = {}
#             service_items = []  # Collect service items separately
            
#             for head_id, items in head_groups.items():
#                 first_item = items[0]
#                 head_to_packno[head_id] = str(packno_counter)
                
#                 data = {
#                     "Bnfpo": first_item.item_number_of_purchase_requisition_head or "",
#                     "Matnr": first_item.material_code_head or "",
#                     "Txz01": first_item.short_text_head or "",
#                     "Menge": first_item.quantity_head or "",
#                     "Meins": first_item.uom_head or "",
#                     "Werks": first_item.plant_head or "",
#                     "Lgort": first_item.store_location_head or "",
#                     "Afnam": doc.requisitioner_first_name or "",
#                     "Bsart": first_item.purchase_requisition_type or "",
#                     "Ekgrp": first_item.purchase_grp_code_head or "",
#                     "Ernam": doc.requisitioner_first_name or "",
#                     "Erdat": first_item.purchase_requisition_date_head.strftime("%Y%m%d") if first_item.purchase_requisition_date_head else "",
#                     "Badat": first_item.delivery_date_head.strftime("%Y%m%d") if first_item.delivery_date_head else "",
#                     "Anln1": first_item.main_asset_no_head or "",
#                     "Anln2": first_item.asset_subnumber_head or "",
#                     "Knttp": first_item.account_assignment_category_head or "",
#                     "Pstyp": first_item.item_category_head or "",
#                     "Sakto": first_item.gl_account_number_head or "",
#                     "Kostl": first_item.cost_center_head or "",
#                     "Preis": first_item.final_price_by_purchase_team_head or "",
#                     "Zvmsprno": doc.prf_name_for_sap or name_for_sap,
#                     "Packno": str(packno_counter)
#                 }
                
#                 data_list["ItemSet"].append(data)
#                 packno_counter += 1
                
#                 # Collect service items for this head
#                 for item in items:
#                     if (item.short_text_subhead or item.quantity_subhead or 
#                         item.uom_subhead or item.gross_price_subhead):
                        
#                         subdata = {
#                             "Bnfpo": item.item_number_of_purchase_requisition_subhead or "",
#                             "Packno": head_to_packno[head_id],
#                             "Introw": "1",
#                             "Extrow": "1",
#                             "Subpackno": "",
#                             "Spackage": "",
#                             "Frompos": "",
#                             "Srvpos": "",
#                             "Ktext1": item.short_text_subhead or "",
#                             "Menge": item.quantity_subhead or "",
#                             "Meins": item.uom_subhead or "",
#                             "Brtwr": item.gross_price_subhead or "",
#                             "Zebkn": "",
#                             "Kostl": item.cost_center_subhead or "",
#                             "Sakto": item.gl_account_number_subhead or ""
#                         }
#                         service_items.append(subdata)
            
#             # Only add ServSet if there are actual service items
#             if service_items:
#                 data_list["ServSet"] = service_items
#                 print(f"📋 Added {len(service_items)} service items to ServSet")
#             else:
#                 print("📋 No service items found, skipping ServSet")
                
#         else:
#             frappe.log_error(f"Unknown purchase requisition type: {doc.purchase_requisition_type}")
#             return None

#         print(f"✅ Payload built successfully for PR type: {doc.purchase_requisition_type}")
#         print(f"📦 Items in payload: {len(data_list.get('ItemSet', []))}")
#         if 'ServSet' in data_list:
#             print(f"🔧 Services in payload: {len(data_list.get('ServSet', []))}")
        
#         return data_list
        
#     except Exception as e:
#         error_msg = f"Error building PR payload: {str(e)}"
#         frappe.log_error(error_msg)
#         print(f"❌ {error_msg}")
#         return None


# def get_pr_csrf_token_and_session(sap_client_code):
#     """Get CSRF token and session cookies for PR API"""
#     try:
#         sap_settings = frappe.get_doc("SAP Settings")
#         erp_to_sap_pr_url = sap_settings.sap_pr_url
#         url = f"{erp_to_sap_pr_url}{sap_client_code}"
#         header_auth_type = sap_settings.authorization_type
#         header_auth_key = sap_settings.authorization_key
#         user = sap_settings.auth_user_name
#         password = sap_settings.auth_user_pass

#         # Create a session to maintain cookies
#         session = requests.Session()
#         auth = HTTPBasicAuth(user, password)

#         headers = {
#             'x-csrf-token': 'fetch',
#             'Authorization': f"{header_auth_type} {header_auth_key}",
#             'Content-Type': 'application/json'
#         }

#         print("=" * 80)
#         print("FETCHING PR CSRF TOKEN")
#         print("=" * 80)
#         print(f"URL: {url}")
#         print(f"User: {user}")
#         print("=" * 80)

#         response = session.get(url, headers=headers, auth=auth, timeout=30)
        
#         print(f"CSRF Response Status: {response.status_code}")
#         print(f"CSRF Response Headers: {dict(response.headers)}")
#         print(f"CSRF Response Cookies: {dict(response.cookies)}")
#         print("=" * 80)
        
#         if response.status_code == 200:
#             csrf_token = response.headers.get('x-csrf-token')
            
#             # Get all session cookies properly
#             session_cookies = {}
#             for cookie in response.cookies:
#                 session_cookies[cookie.name] = cookie.value
            
#             print(f"✅ PR CSRF Token obtained: {csrf_token}")
#             print(f"✅ PR Session cookies: {session_cookies}")
            
#             return {
#                 "success": True,
#                 "csrf_token": csrf_token,
#                 "session_cookies": session_cookies,
#                 "session": session
#             }
#         else:
#             error_msg = f"Failed to fetch PR CSRF token. Status: {response.status_code}, Response: {response.text}"
#             print(f"❌ {error_msg}")
#             return {"success": False, "error": error_msg}
            
#     except Exception as e:
#         error_msg = f"Exception while fetching PR CSRF token: {str(e)}"
#         print(f"❌ {error_msg}")
#         return {"success": False, "error": error_msg}


# @frappe.whitelist(allow_guest=True)
# def send_pr_detail(csrf_token, data_list, session_cookies, doc, sap_code, name_for_sap):
#     """Send PR details to SAP with comprehensive logging"""
#     sap_settings = frappe.get_doc("SAP Settings")
#     erp_to_sap_pr_url = sap_settings.sap_pr_url
#     url = f"{erp_to_sap_pr_url}{sap_code}"
#     header_auth_type = sap_settings.authorization_type
#     header_auth_key = sap_settings.authorization_key
#     user = sap_settings.auth_user_name
#     password = sap_settings.auth_user_pass

#     # Build cookie string from session cookies
#     cookie_string = "; ".join([f"{name}={value}" for name, value in session_cookies.items()])

#     headers = {
#         'X-CSRF-TOKEN': csrf_token,
#         'Authorization': f"{header_auth_type} {header_auth_key}",
#         'Content-Type': 'application/json;charset=utf-8',
#         'Accept': 'application/json',
#         'Cookie': cookie_string
#     }

#     auth = HTTPBasicAuth(user, password)
    
#     # Initialize response variables
#     response = None
#     pr_code = None
#     sap_response_text = ""
#     transaction_status = "Failed"
#     error_details = ""
    
#     # Print complete payload for debugging
#     print("=" * 80)
#     print("SAP PR API PAYLOAD DEBUG")
#     print("=" * 80)
#     print(f"URL: {url}")
#     print(f"Headers: {json.dumps(dict(headers), indent=2)}")
#     print(f"Auth User: {user}")
#     print(f"Payload Data:")
#     print(json.dumps(data_list, indent=2, default=str))
#     print("=" * 80)
    
#     try:
#         response = requests.post(url, headers=headers, auth=auth, json=data_list, timeout=30)
#         sap_response_text = response.text
        
#         # Debug response details
#         print("=" * 80)
#         print("SAP PR API RESPONSE DEBUG")
#         print("=" * 80)
#         print(f"Response Status Code: {response.status_code}")
#         print(f"Response Headers: {dict(response.headers)}")
#         print(f"Response Content Length: {len(response.text)}")
#         print(f"Response Content: {response.text}")
#         print("=" * 80)
        
#         # Check if response has content and is valid JSON
#         if response.status_code == 201 and response.text.strip():
#             try:
#                 pr_sap_code = response.json()
#                 # Extract PR code (Banfn)
#                 pr_code = pr_sap_code['d']['Banfn']
                
#                 # Check if PR code indicates error or is empty
#                 if pr_code == 'E' or pr_code == '' or not pr_code:
#                     transaction_status = "SAP Error"
#                     error_details = f"SAP returned error PR code. Banfn: '{pr_code}'"
#                     print(f"❌ SAP PR Error: {error_details}")
#                 else:
#                     transaction_status = "Success"
#                     print(f"✅ PR details posted successfully. PR Code: {pr_code}")
                    
#                     # Update the document with SAP details
#                     doc.sent_to_sap = 1
#                     doc.sap_pr_code = pr_code
#                     if not doc.prf_name_for_sap:
#                         doc.prf_name_for_sap = name_for_sap
#                     doc.db_update()
                
#                 print(f"✅ Full SAP PR Response: {json.dumps(pr_sap_code, indent=2)}")
                
#             except (JSONDecodeError, KeyError) as json_err:
#                 error_details = f"JSON parse error or missing Banfn: {str(json_err)[:200]}"
#                 transaction_status = "JSON Parse Error"
#                 print(f"❌ JSON parsing error: {error_details}")
                
#         elif response.status_code == 400:
#             # Handle specific SAP API errors (like ServSet property error)
#             error_details = f"SAP API validation error: {response.text[:300]}"
#             transaction_status = "SAP Validation Error"
#             print(f"❌ SAP Validation Error: {error_details}")
            
#             # Extract specific error message for better debugging
#             try:
#                 error_json = response.json()
#                 sap_error_msg = error_json.get('error', {}).get('message', {}).get('value', 'Unknown SAP error')
#                 print(f"📋 SAP Error Details: {sap_error_msg}")
                
#                 # Check if it's a ServSet issue
#                 if 'ServSet' in sap_error_msg:
#                     print("⚠️ ISSUE: ServSet property is invalid - check your SB type payload structure")
#                     error_details = f"ServSet validation failed: {sap_error_msg}"
                    
#             except:
#                 pass
                
#         elif response.status_code == 403:
#             error_details = f"CSRF Token validation failed"
#             transaction_status = "CSRF Token Error"
#             print(f"❌ CSRF Error: {error_details}")
            
#         elif response.status_code != 201:
#             error_details = f"SAP PR API returned status {response.status_code}"
#             transaction_status = f"HTTP Error {response.status_code}"
#             print(f"❌ Error in POST request: {error_details}")
            
#         else:
#             error_details = "Empty response from SAP PR API"
#             transaction_status = "Empty Response"
#             print(f"❌ Error: {error_details}")

#     except RequestException as req_err:
#         error_details = f"Network error: {str(req_err)[:200]}"
#         transaction_status = "Request Exception"
#         print(f"❌ Request error: {error_details}")
#         sap_response_text = str(req_err)
        
#     except Exception as e:
#         error_details = f"Unexpected error: {str(e)[:200]}"
#         transaction_status = "Unexpected Error"
#         print(f"❌ Unexpected error: {error_details}")
#         sap_response_text = str(e)

#     # Always log the transaction with full data
#     try:
#         sap_log = frappe.new_doc("VMS SAP Logs")
#         sap_log.purchase_requisition_link = doc.name
        
#         # Store full data since erp_to_sap_data is JSON field
#         sap_log.erp_to_sap_data = data_list
        
#         # Store full response since sap_response is JSON field  
#         if response and response.text.strip():
#             try:
#                 sap_log.sap_response = response.json()
#             except JSONDecodeError:
#                 sap_log.sap_response = {"raw_response": response.text, "parse_error": "Could not parse as JSON"}
#         else:
#             sap_log.sap_response = {"error": sap_response_text}
        
#         # Create comprehensive transaction log for Code field
#         total_transaction_data = {
#             "request_details": {
#                 "url": url,
#                 "headers": {k: v for k, v in headers.items() if k != 'Authorization'},
#                 "auth_user": user,
#                 "payload": data_list
#             },
#             "response_details": {
#                 "status_code": response.status_code if response else "No Response",
#                 "headers": dict(response.headers) if response else {},
#                 "body": response.json() if response and response.text.strip() else sap_response_text
#             },
#             "transaction_summary": {
#                 "status": transaction_status,
#                 "pr_code": pr_code,
#                 "error_details": error_details,
#                 "timestamp": frappe.utils.now(),
#                 "sap_client_code": sap_code,
#                 "pr_doc_name": doc.name,
#                 "pr_type": doc.purchase_requisition_type,
#                 "name_for_sap": name_for_sap
#             }
#         }
        
#         sap_log.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)
#         sap_log.save(ignore_permissions=True)
#         print(f"📝 SAP PR Log created with name: {sap_log.name}")
        
#     except Exception as log_err:
#         log_error_msg = f"Failed to create SAP PR log: {str(log_err)}"
#         print(f"❌ Log creation error: {log_error_msg}")
        
#         # Create a minimal log entry using console output only
#         try:
#             print("📝 Fallback: Logging to console only due to log creation failure")
#             print(f"📋 Transaction: {transaction_status}")
#             print(f"📋 PR Doc: {doc.name}")
#             print(f"📋 Error: {error_details[:200]}")
#         except Exception as fallback_err:
#             print(f"❌ Even console logging failed: {str(fallback_err)}")

#     # Create error log entry for transactions (with truncated messages)
#     try:
#         if transaction_status == "Success":
#             # Create success log with short title
#             success_log = frappe.new_doc("Error Log")
#             success_log.method = "send_pr_detail"
#             success_log.error = f"SAP PR SUCCESS: {pr_code}\nDoc: {doc.name}\nType: {doc.purchase_requisition_type}\nClient: {sap_code}"
#             success_log.save(ignore_permissions=True)
#             print(f"📝 Success Log created with name: {success_log.name}")
#         else:
#             # Create error log for failures with truncated error message
#             error_log = frappe.new_doc("Error Log")
#             error_log.method = "send_pr_detail"
#             # Truncate error details to avoid length issues
#             truncated_error = error_details[:100] + "..." if len(error_details) > 100 else error_details
#             error_log.error = f"SAP PR {transaction_status}: {truncated_error}\nDoc: {doc.name}"
#             error_log.save(ignore_permissions=True)
#             print(f"📝 Error Log created with name: {error_log.name}")
#     except Exception as err_log_err:
#         print(f"❌ Failed to create Error Log: {str(err_log_err)}")
#         # Don't use frappe.log_error here to avoid cascading errors
    
#     frappe.db.commit()
    
#     # Return appropriate response
#     if response and response.status_code == 201:
#         try:
#             return response.json()  # Return the full SAP response
#         except JSONDecodeError:
#             return {
#                 "success": True, 
#                 "pr_code": pr_code, 
#                 "message": "PR created but response parsing failed",
#                 "transaction_status": transaction_status,
#                 "raw_response": response.text
#             }
#     else:
#         return {
#             "error": f"Failed to create PR in SAP. Status: {response.status_code if response else 'No response'}",
#             "transaction_status": transaction_status,
#             "error_details": error_details
#         }


# def safe_get(obj, list_name, index, attr, default=""):
#     try:
#         return getattr(getattr(obj, list_name)[index], attr) or default
#     except (AttributeError, IndexError, TypeError):
#         return default





#______________________---------------------------------------------------------------above--------------------------------------------------



from pickle import NONE
import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, JSONDecodeError
from datetime import datetime
from vms.utils.custom_send_mail import custom_sendmail

@frappe.whitelist(allow_guest=True)
def erp_to_sap_pr(doc_name, method=None):
    print("=" * 80)
    print("SEND PR DATA TO SAP - STARTING")
    print(f"Document Name: {doc_name}")
    print("=" * 80)
    
    try:
        doc = frappe.get_doc("Purchase Requisition Form", doc_name)
        prf_type = frappe.db.get_value("Purchase Requisition Type", doc.purchase_requisition_type, "purchase_requisition_type_name") 
        sap_client_code = doc.sap_client_code
        now = datetime.now()
        year_month_prefix = f"P{now.strftime('%y')}{now.strftime('%m')}"  # e.g. PRF2506

        print(f"📋 Processing PR document: {doc.name}")
        print(f"📋 PR Type: {doc.purchase_requisition_type}")
        print(f"📋 SAP Client Code: {sap_client_code}")
        print(f"📋 Items to process: {len(doc.purchase_requisition_form_table)}")

        # Get max existing count for this prefix
        existing_max = frappe.db.sql(
            """
            SELECT MAX(CAST(SUBSTRING(prf_name_for_sap, 8) AS UNSIGNED))
            FROM `tabPurchase Requisition Form`
            WHERE prf_name_for_sap LIKE %s
            """,
            (year_month_prefix + "%",),
            as_list=True
        )

        max_count = existing_max[0][0] or 0
        new_count = max_count + 1
        name_for_sap = f"{year_month_prefix}{str(new_count).zfill(5)}"

        print(f"📋 Generated SAP Name: {name_for_sap}")

        # Build data payload based on PR type
        print(f"🔧 Building payload for PR type: {doc.purchase_requisition_type}")
        data_list = build_pr_payload(doc, name_for_sap)
        
        if not data_list:
            error_msg = "Failed to build PR payload - payload is empty or invalid"
            print(f"❌ PAYLOAD ERROR: {error_msg}")
            
            # **CREATE VMS SAP LOG FOR PAYLOAD BUILD FAILURE**
            sap_stat = "Payload Build Failed" 
            create_pr_sap_log(doc, None, None, sap_stat, error_msg, sap_client_code, name_for_sap)
            
            # Send failure notification
            send_pr_failure_notification(
                doc.name,
                "PR Payload Build Failed",
                error_msg
            )
            
            frappe.log_error(error_msg, "PR Payload Build Error")
            return {"error": error_msg}

        print(f"✅ Payload built successfully")
        print(f"📦 ItemSet count: {len(data_list.get('ItemSet', []))}")
        if 'ServSet' in data_list:
            print(f"🔧 ServSet count: {len(data_list.get('ServSet', []))}")

        # Get CSRF token and session
        print(f"🔑 Getting CSRF token for SAP client: {sap_client_code}")
        csrf_result = get_pr_csrf_token_and_session(sap_client_code, prf_type)
        
        if csrf_result["success"]:
            print(f"✅ CSRF token obtained successfully")
            try:
                # Send details to SAP
                print(f"🚀 Sending PR data to SAP...")
                result = send_pr_detail(
                    csrf_result["csrf_token"], 
                    data_list, 
                    csrf_result["session_cookies"],
                    doc, 
                    sap_client_code,
                    name_for_sap,
                    prf_type
                )
                
                # **CHECK RESULT AND HANDLE RESPONSE**
                if not result or "error" in result:
                    error_msg = result.get('error', 'Unknown error') if result else 'No response from send_pr_detail function'
                    print(f"❌ SAP PR API Call Failed: {error_msg}")
                    
                    # **CREATE VMS SAP LOG FOR API CALL FAILURE**
                    sap_stat = "API Call Failed"
                    create_pr_sap_log(doc, data_list, None, sap_stat, error_msg, sap_client_code, name_for_sap)
                    
                    # Send failure notification
                    send_pr_failure_notification(
                        doc.name,
                        "SAP PR API Call Failed",
                        f"The SAP PR integration API call failed. Error: {error_msg}"
                    )
                    
                    return {"error": error_msg}
                    
                elif result and isinstance(result, dict):
                    # Extract PR code from response
                    pr_code = result.get('d', {}).get('Banfn', '') if 'd' in result else result.get('Banfn', '')
                    zmsg = result.get('d', {}).get('Message', '') if 'd' in result else result.get('Message', '')
                    ztype = result.get('d', {}).get('Ztype', '') if 'd' in result else result.get('Ztype', '')
                    
                    if ztype == 'E' or ztype == '' or not ztype:
                        error_msg = f"SAP returned error or empty PR code. Banfn: '{pr_code}', Message: '{zmsg}'"
                        print(f"❌ SAP PR Error: {error_msg}")
                        
                        # **CREATE VMS SAP LOG FOR SAP ERROR**
                        sap_stat = "SAP Error"
                        create_pr_sap_log(doc, data_list, result, sap_stat, error_msg, sap_client_code, name_for_sap)
                        
                        # Send failure notification
                        send_pr_failure_notification(
                            doc.name,
                            "SAP PR Creation Failed",
                            error_msg
                        )
                        
                        return {"error": error_msg}
                    else:
                        print(f"✅ SUCCESS: PR code {pr_code} created successfully")
                        
                        # **UPDATE DOCUMENT WITH SUCCESS DATA**
                        try:
                            # doc.sent_to_sap = 1
                            # doc.sap_pr_code = pr_code
                            # if not doc.prf_name_for_sap:
                            #     doc.prf_name_for_sap = name_for_sap
                            # doc.db_update()
                            print(f"📝 Document updated successfully with PR code: {pr_code}")
                            
                            # **CREATE VMS SAP LOG FOR SUCCESS**
                            sap_stat = "Success"
                            create_pr_sap_log(doc, data_list, result, sap_stat, f"PR Code: {pr_code}", sap_client_code, name_for_sap)
                            
                            # Send success notification
                            send_pr_success_notification(
                                doc.name,
                                pr_code,
                                name_for_sap,
                                doc.purchase_requisition_type
                            )
                            doc.db_set({
                                            "sent_to_sap": 1,
                                            "sap_pr_code": pr_code,
                                            "prf_name_for_sap": name_for_sap if not doc.prf_name_for_sap else doc.prf_name_for_sap
                                        })

                            
                        except Exception as update_err:
                            error_msg = f"Failed to update document: {str(update_err)}"
                            print(f"❌ Update Error: {error_msg}")
                            frappe.log_error(error_msg, "PR Document Update Error")
                            
                            # **CREATE VMS SAP LOG FOR UPDATE FAILURE**
                            sap_stat = "Document Update Failed"
                            create_pr_sap_log(doc, data_list, result, sap_stat, error_msg, sap_client_code, name_for_sap)
                            
                            # Send notification for update failure
                            send_pr_failure_notification(
                                doc.name,
                                "PR Document Update Failed",
                                error_msg
                            )
                
                print("=" * 80)
                print("SEND PR DATA TO SAP - COMPLETED SUCCESSFULLY")
                print(f"✅ PR Code: {pr_code}")
                print(f"✅ SAP Name: {name_for_sap}")
                print("=" * 80)
                
                return result
                
            except Exception as send_detail_err:
                error_msg = f"send_pr_detail error: {str(send_detail_err)}"
                print(f"❌ SEND DETAIL ERROR: {error_msg}")
                frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "Send PR Detail Error")
                
                # **CREATE VMS SAP LOG FOR SEND DETAIL ERROR**
                sap_stat = "Send Detail Error"
                create_pr_sap_log(doc, data_list, None, sap_stat, error_msg, sap_client_code, name_for_sap)
                
                # Send failure notification
                send_pr_failure_notification(
                    doc.name,
                    "SAP PR Send Detail Error",
                    error_msg
                )
                
                return {"error": error_msg}
        else:
            error_msg = f"CSRF token failed: {csrf_result.get('error', 'Unknown error')}"
            print(f"❌ CSRF TOKEN ERROR: {error_msg}")
            
            # **CREATE VMS SAP LOG FOR CSRF TOKEN FAILURE**
            sap_stat = "CSRF Token Failed"
            create_pr_sap_log(doc, data_list, None, sap_stat, error_msg, sap_client_code, name_for_sap)
            
            # Send failure notification
            send_pr_failure_notification(
                doc.name,
                "SAP PR CSRF Token Error",
                error_msg
            )
            
            return {"error": error_msg}
            
    except Exception as main_err:
        error_msg = f"Main function error in erp_to_sap_pr: {str(main_err)}"
        print(f"❌ MAIN ERROR: {error_msg}")
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "ERP to SAP PR Main Error")
        
        # **CREATE VMS SAP LOG FOR MAIN ERROR**
        try:
            doc = frappe.get_doc("Purchase Requisition Form", doc_name)
            sap_stat = "Main Function Error"
            create_pr_sap_log(doc, None, None, sap_stat, error_msg, doc.sap_client_code if hasattr(doc, 'sap_client_code') else "Unknown", "")
        except Exception as log_err:
            print(f"❌ Failed to create VMS SAP Log for main error: {str(log_err)}")
        
        # Send notification for main error
        try:
            send_pr_failure_notification(
                doc_name,
                "ERP to SAP PR Main Function Error",
                error_msg
            )
        except Exception as notif_err:
            print(f"⚠️ Failed to send notification: {str(notif_err)}")
        
        return {"error": error_msg}


def build_pr_payload(doc, name_for_sap):
    """Build PR payload based on purchase requisition type"""
    try:
        print(f"🔧 Building payload for PR type: {doc.purchase_requisition_type}")
        
        if doc.purchase_requisition_type == "NB":
            data_list = {
                "Banfn": "",
                "Ztype": "",
                "Ztext": "",
                "Zvmsprno": "",
                "ItemSet": []
            }
            
            item_counter = 0
            for item in doc.purchase_requisition_form_table:
                item_counter += 1
                print(f"   📦 Processing NB item {item_counter}: {item.short_text_head}")
                
                data = {
                    "Bnfpo": item.item_number_of_purchase_requisition_head or "",
                    "Matnr": frappe.db.get_value("Material Code", item.material_code_head, "material_code") or "",
                    "Txz01": item.short_text_head or "",
                    "Menge": item.quantity_head or "",
                    "Meins": item.uom_head or "",
                    "Werks": frappe.db.get_value("Plant Master", item.plant_head, "plant_code") or "",
                    "Lgort": frappe.db.get_value("Storage Location Master", item.store_location_head, "storage_location") or "",
                    "Afnam": doc.requisitioner_first_name or "",
                    "Bsart": item.purchase_requisition_type or "",
                    "Ekgrp": item.purchase_grp_code_head or "",
                    "Ernam": doc.requisitioner_first_name or "",
                    "Erdat": item.purchase_requisition_date_head.strftime("%Y%m%d") if item.purchase_requisition_date_head else "",
                    "Badat": item.delivery_date_head.strftime("%Y%m%d") if item.delivery_date_head else "",
                    "Anln1": item.main_asset_no_head or "",
                    "Anln2": item.asset_subnumber_head or "",
                    "Knttp": item.account_assignment_category_head or "",
                    "Pstyp": item.item_category_head or "",
                    "Sakto": frappe.db.get_value("GL Account", item.gl_account_number_head, "gl_account_code") or "",
                    "Kostl": frappe.db.get_value("Cost Center", item.cost_center_head, "cost_center_code") or "",
                    "Preis": item.final_price_by_purchase_team_head or "",
                    "Zvmsprno": doc.prf_name_for_sap or name_for_sap
                }
                data_list["ItemSet"].append(data)
                print(f"      ✅ NB item {item_counter} added to payload")

        elif doc.purchase_requisition_type == "SB":
            data_list = {
                "Banfn": "",
                "Ztype": "",
                "Ztext": "",
                "Zvmsprno": "",
                "ItemSet": []
            }
            
            # Group items by head_unique_id
            head_groups = {}
            for item in doc.purchase_requisition_form_table:
                head_id = item.head_unique_id
                if head_id not in head_groups:
                    head_groups[head_id] = []
                head_groups[head_id].append(item)
            
            print(f"   📊 Found {len(head_groups)} unique head groups for SB type")
            
            # Process ItemSet - one row per unique head_unique_id
            packno_counter = 1
            head_to_packno = {}
            service_items = []  # Collect service items separately
            
            for head_id, items in head_groups.items():
                first_item = items[0]
                head_to_packno[head_id] = str(packno_counter)
                
                print(f"   📦 Processing SB head group {packno_counter}: {first_item.short_text_head}")
                material_group = frappe.db.get_value("Material Code", first_item.material_code_head, "material_group")
                matkl = frappe.db.get_value("Material Group Master", material_group, "material_group_name") or ""

                
                data = {
                    "Bnfpo": first_item.item_number_of_purchase_requisition_head or "",
                    "Matnr": frappe.db.get_value("Material Code", first_item.material_code_head, "material_code") or "",
                    "Matkl": matkl,
                    "Txz01": first_item.short_text_head or "",
                    "Menge": first_item.quantity_head or "",
                    "Meins": first_item.uom_head or "",
                    "Werks": frappe.db.get_value("Plant Master", first_item.plant_head, "plant_code") or "",
                    "Lgort": frappe.db.get_value("Storage Location Master", first_item.store_location_head, "storage_location") or "",
                    "Afnam": doc.requisitioner_first_name or "",
                    "Bsart": first_item.purchase_requisition_type or "",
                    "Ekgrp": first_item.purchase_grp_code_head or "",
                    "Ernam": doc.requisitioner_first_name or "",
                    "Erdat": first_item.purchase_requisition_date_head.strftime("%Y%m%d") if first_item.purchase_requisition_date_head else "",
                    "Badat": first_item.delivery_date_head.strftime("%Y%m%d") if first_item.delivery_date_head else "",
                    "Anln1": first_item.main_asset_no_head or "",
                    "Anln2": first_item.asset_subnumber_head or "",
                    "Knttp": first_item.account_assignment_category_head or "",
                    "Pstyp": first_item.item_category_head or "",
                    "Sakto": frappe.db.get_value("GL Account", first_item.gl_account_number_head, "gl_account_code") or "",
                    "Kostl": frappe.db.get_value("Cost Center", first_item.cost_center_head, "cost_center_code") or "",
                    "Preis": first_item.final_price_by_purchase_team_head or "",
                    "Zvmsprno": doc.prf_name_for_sap or name_for_sap,
                    "Packno": str(packno_counter)
                }
                
                data_list["ItemSet"].append(data)
                print(f"      ✅ SB head item {packno_counter} added to ItemSet")
                packno_counter += 1
                
                # Collect service items for this head
                service_counter = 0
                for item in items:
                    if (item.short_text_subhead or item.quantity_subhead or 
                        item.uom_subhead or item.gross_price_subhead):
                        
                        service_counter += 1
                        print(f"      🔧 Processing service item {service_counter} for head {head_id}")
                        
                        subdata = {
                            "Bnfpo": item.item_number_of_purchase_requisition_subhead or "",
                            "Packno": head_to_packno[head_id],
                            "Introw": "1",
                            "Extrow": "1",
                            "Subpackno": "",
                            "Spackage": "",
                            "Frompos": "",
                            "Srvpos": "",
                            "Ktext1": item.short_text_subhead or "",
                            "Menge": item.quantity_subhead or "",
                            "Meins": item.uom_subhead or "",
                            "Brtwr": item.gross_price_subhead or "",
                            "Zebkn": "",
                            "Kostl": frappe.db.get_value("Cost Center", item.cost_center_head, "cost_center_code") or "",
                            "Sakto": frappe.db.get_value("GL Account", item.gl_account_number_head, "gl_account_code") or ""
                        }
                        service_items.append(subdata)
                        print(f"         ✅ Service item {service_counter} added to collection")
            
            # Only add ServSet if there are actual service items
            if service_items:
                data_list["ServSet"] = service_items
                print(f"📋 Added {len(service_items)} service items to ServSet")
            else:
                print("📋 No service items found, skipping ServSet")
                
        else:
            error_msg = f"Unknown purchase requisition type: {doc.purchase_requisition_type}"
            print(f"❌ PAYLOAD ERROR: {error_msg}")
            frappe.log_error(error_msg, "PR Payload Build Error")
            return None

        print(f"✅ Payload built successfully for PR type: {doc.purchase_requisition_type}")
        print(f"📦 Items in payload: {len(data_list.get('ItemSet', []))}")
        if 'ServSet' in data_list:
            print(f"🔧 Services in payload: {len(data_list.get('ServSet', []))}")
        
        return data_list
        
    except Exception as e:
        error_msg = f"Error building PR payload: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "PR Payload Build Error")
        print(f"❌ PAYLOAD BUILD ERROR: {error_msg}")
        return None


def get_pr_csrf_token_and_session(sap_client_code, prf_type):
    """Get CSRF token and session cookies for PR API"""
    try:
        sap_settings = frappe.get_doc("SAP Settings")
        erp_to_sap_pr_url = None
        if prf_type == "NB":
            erp_to_sap_pr_url = sap_settings.sap_pr_url_nb

        else:
            erp_to_sap_pr_url = sap_settings.sap_pr_url_sb


        url = f"{erp_to_sap_pr_url}{sap_client_code}"
        header_auth_type = sap_settings.authorization_type
        header_auth_key = sap_settings.authorization_key
        user = sap_settings.auth_user_name
        password = sap_settings.auth_user_pass

        # Create a session to maintain cookies
        session = requests.Session()
        auth = HTTPBasicAuth(user, password)

        headers = {
            'x-csrf-token': 'fetch',
            'Authorization': f"{header_auth_type} {header_auth_key}",
            'Content-Type': 'application/json'
        }

        print("=" * 80)
        print("FETCHING PR CSRF TOKEN")
        print("=" * 80)
        print(f"URL: {url}")
        print(f"User: {user}")
        print("=" * 80)

        response = session.get(url, headers=headers, auth=auth, timeout=30)
        
        print(f"🔑 CSRF Response Status: {response.status_code}")
        print(f"🔑 CSRF Response Headers: {dict(response.headers)}")
        print(f"🔑 CSRF Response Cookies: {dict(response.cookies)}")
        print("=" * 80)
        
        if response.status_code == 200:
            csrf_token = response.headers.get('x-csrf-token')
            
            # Get all session cookies properly
            session_cookies = {}
            for cookie in response.cookies:
                session_cookies[cookie.name] = cookie.value
            
            print(f"✅ PR CSRF Token obtained: {csrf_token}")
            print(f"✅ PR Session cookies: {session_cookies}")
            
            return {
                "success": True,
                "csrf_token": csrf_token,
                "session_cookies": session_cookies,
                "session": session
            }
        else:
            error_msg = f"Failed to fetch PR CSRF token. Status: {response.status_code}, Response: {response.text}"
            print(f"❌ CSRF ERROR: {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Exception while fetching PR CSRF token: {str(e)}"
        print(f"❌ CSRF EXCEPTION: {error_msg}")
        return {"success": False, "error": error_msg}


@frappe.whitelist(allow_guest=True)
def send_pr_detail(csrf_token, data_list, session_cookies, doc, sap_code, name_for_sap, prf_type):
    """Send PR details to SAP with comprehensive logging - Enhanced Version"""
    sap_settings = frappe.get_doc("SAP Settings")
    erp_to_sap_pr_url = None
    if prf_type == "NB":
        erp_to_sap_pr_url = sap_settings.sap_pr_url_nb

    else:
        erp_to_sap_pr_url = sap_settings.sap_pr_url_sb
    url = f"{erp_to_sap_pr_url}{sap_code}"
    header_auth_type = sap_settings.authorization_type
    header_auth_key = sap_settings.authorization_key
    user = sap_settings.auth_user_name
    password = sap_settings.auth_user_pass

    # Build cookie string from session cookies
    cookie_string = "; ".join([f"{name}={value}" for name, value in session_cookies.items()])

    headers = {
        'X-CSRF-TOKEN': csrf_token,
        'Authorization': f"{header_auth_type} {header_auth_key}",
        'Content-Type': 'application/json;charset=utf-8',
        'Accept': 'application/json',
        'Cookie': cookie_string
    }

    auth = HTTPBasicAuth(user, password)
    
    # Initialize response variables
    response = None
    pr_code = None
    sap_response_text = ""
    transaction_status = "Failed"
    error_details = ""
    
    # Print complete payload for debugging
    print("=" * 80)
    print("SAP PR API PAYLOAD DEBUG")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(dict(headers), indent=2)}")
    print(f"Auth User: {user}")
    print(f"SAP Client Code: {sap_code}")
    print(f"PR Document: {doc.name}")
    print(f"PR Type: {doc.purchase_requisition_type}")
    print(f"Name for SAP: {name_for_sap}")
    print(f"Payload Data:")
    print(json.dumps(data_list, indent=2, default=str))
    print("=" * 80)
    
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data_list, timeout=30)
        sap_response_text = response.text[:1000]  # Truncate to avoid DB constraint issues
        
        # Debug response details
        print("=" * 80)
        print("SAP PR API RESPONSE DEBUG")
        print("=" * 80)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content Length: {len(response.text)}")
        print(f"Response Content: {response.text}")
        print("=" * 80)
        
        # Check if response has content and is valid JSON
        if response.status_code == 201 and response.text.strip():
            try:
                pr_sap_code = response.json()
                # Extract PR code (Banfn)
                pr_code = pr_sap_code['d']['Banfn']
                zmsg = pr_sap_code['d'].get('Message', '')
                ztype = pr_sap_code['d'].get('Ztype', '')
                
                # Check if PR code indicates error or is empty
                if ztype == 'E' or ztype == '' or not ztype:
                    transaction_status = "SAP Error"
                    error_details = f"SAP returned error PR code. Banfn: '{pr_code}', Message: '{zmsg}'"
                    print(f"❌ SAP PR Error: {error_details}")
                    
                    # Send notification for SAP error
                    try:
                        send_pr_failure_notification(
                            doc.name,
                            "SAP PR Creation Error",
                            error_details
                        )
                    except Exception as notif_err:
                        print(f"⚠️ Failed to send notification: {str(notif_err)}")
                else:
                    transaction_status = "Success"
                    print(f"✅ PR details posted successfully. PR Code: {pr_code}")
                    if zmsg:
                        print(f"📝 SAP Message: {zmsg}")
                
                print(f"✅ Full SAP PR Response: {json.dumps(pr_sap_code, indent=2)}")
                
            except (JSONDecodeError, KeyError) as json_err:
                error_details = f"Invalid JSON response or missing Banfn field: {str(json_err)}"
                transaction_status = "JSON Parse Error"
                frappe.log_error(error_details, "SAP PR JSON Parse Error")
                print(f"❌ JSON parsing error: {error_details}")
                
                # Send notification for parsing error
                try:
                    send_pr_failure_notification(
                        doc.name,
                        "SAP PR Response Parse Error",
                        error_details
                    )
                except Exception as notif_err:
                    print(f"⚠️ Failed to send notification: {str(notif_err)}")
                
        elif response.status_code == 400:
            # Handle specific SAP API errors (like ServSet property error)
            error_details = f"SAP API validation error: {response.text[:300]}"
            transaction_status = "SAP Validation Error"
            frappe.log_error(error_details, "SAP PR Validation Error")
            print(f"❌ SAP Validation Error: {error_details}")
            
            # Extract specific error message for better debugging
            try:
                error_json = response.json()
                sap_error_msg = error_json.get('error', {}).get('message', {}).get('value', 'Unknown SAP error')
                print(f"📋 SAP Error Details: {sap_error_msg}")
                
                # Check if it's a ServSet issue
                if 'ServSet' in sap_error_msg:
                    print("⚠️ ISSUE: ServSet property is invalid - check your SB type payload structure")
                    error_details = f"ServSet validation failed: {sap_error_msg}"
                    
            except:
                pass
            
            # Send notification for validation error
            try:
                send_pr_failure_notification(
                    doc.name,
                    "SAP PR Validation Error",
                    error_details
                )
            except Exception as notif_err:
                print(f"⚠️ Failed to send notification: {str(notif_err)}")
                
        elif response.status_code == 403:
            error_details = f"CSRF Token validation failed. Response: {response.text}"
            transaction_status = "CSRF Token Error"
            frappe.log_error(error_details, "SAP PR CSRF Error")
            print(f"❌ CSRF Error: {error_details}")
            
            # Send notification for CSRF error
            try:
                send_pr_failure_notification(
                    doc.name,
                    "SAP PR Authentication Error",
                    error_details
                )
            except Exception as notif_err:
                print(f"⚠️ Failed to send notification: {str(notif_err)}")
            
        elif response.status_code != 201:
            error_details = f"SAP PR API returned status {response.status_code}: {response.text}"
            transaction_status = f"HTTP Error {response.status_code}"
            frappe.log_error(error_details, f"SAP PR HTTP Error {response.status_code}")
            print(f"❌ Error in POST request: {error_details}")
            
            # Send notification for HTTP error
            try:
                send_pr_failure_notification(
                    doc.name,
                    f"SAP PR API Error {response.status_code}",
                    error_details
                )
            except Exception as notif_err:
                print(f"⚠️ Failed to send notification: {str(notif_err)}")
            
        else:
            error_details = "Empty response from SAP PR API"
            transaction_status = "Empty Response"
            frappe.log_error(error_details, "SAP PR Empty Response")
            print(f"❌ Error: {error_details}")
            
            # Send notification for empty response
            try:
                send_pr_failure_notification(
                    doc.name,
                    "SAP PR Empty Response",
                    error_details
                )
            except Exception as notif_err:
                print(f"⚠️ Failed to send notification: {str(notif_err)}")

    except RequestException as req_err:
        error_details = f"Request failed: {str(req_err)}"
        transaction_status = "Request Exception"
        frappe.log_error(error_details, "SAP PR Request Exception")
        print(f"❌ Request error: {error_details}")
        sap_response_text = str(req_err)[:1000]
        
        # Send notification for request exception
        try:
            send_pr_failure_notification(
                doc.name,
                "SAP PR Network Error",
                error_details
            )
        except Exception as notif_err:
            print(f"⚠️ Failed to send notification: {str(notif_err)}")
        
    except Exception as e:
        error_details = f"Unexpected error: {str(e)}"
        transaction_status = "Unexpected Error"
        frappe.log_error(error_details, "SAP PR Unexpected Error")
        print(f"❌ Unexpected error: {error_details}")
        sap_response_text = str(e)[:1000]
        
        # Send notification for unexpected error
        try:
            send_pr_failure_notification(
                doc.name,
                "SAP PR Unexpected Error",
                error_details
            )
        except Exception as notif_err:
            print(f"⚠️ Failed to send notification: {str(notif_err)}")

    # **COMPREHENSIVE LOGGING - Same as vendor function**
    # try:
    #     sap_log = frappe.new_doc("PR SAP Logs")
    #     sap_log.purchase_requisition_link = doc.name
        
    #     # Store full data since erp_to_sap_data is JSON field
    #     sap_log.erp_to_sap_data = data_list
        
    #     # Store full response since sap_response is JSON field  
    #     if response and response.text.strip():
    #         try:
    #             sap_log.sap_response = response.json()
    #         except JSONDecodeError:
    #             sap_log.sap_response = {"raw_response": response.text, "parse_error": "Could not parse as JSON"}
    #     else:
    #         sap_log.sap_response = {"error": sap_response_text}
        
    #     # Create comprehensive transaction log for Code field
    #     total_transaction_data = {
    #         "request_details": {
    #             "url": url,
    #             "headers": {k: v for k, v in headers.items() if k != 'Authorization'},
    #             "auth_user": user,
    #             "payload": data_list
    #         },
    #         "response_details": {
    #             "status_code": response.status_code if response else "No Response",
    #             "headers": dict(response.headers) if response else {},
    #             "body": response.json() if response and response.text.strip() else sap_response_text
    #         },
    #         "transaction_summary": {
    #             "status": transaction_status,
    #             "pr_code": pr_code,
    #             "error_details": error_details,
    #             "timestamp": frappe.utils.now(),
    #             "sap_client_code": sap_code,
    #             "pr_doc_name": doc.name,
    #             "pr_type": doc.purchase_requisition_type,
    #             "name_for_sap": name_for_sap
    #         }
    #     }
        
    #     sap_log.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)
    #     sap_log.save(ignore_permissions=True)
    #     print(f"📝 SAP PR Log created with name: {sap_log.name}")
        
    # except Exception as log_err:
    #     log_error_msg = f"Failed to create SAP PR log: {str(log_err)}"
    #     print(f"❌ Log creation error: {log_error_msg}")
        


        
        # Create a minimal log entry using Frappe's error log
        try:
            frappe.log_error(
                title=f"SAP PR Integration - {transaction_status}",
                message=f"PR Doc: {doc.name}\nStatus: {transaction_status}\nPR Code: {pr_code}\nError: {error_details}"
            )
            print("📝 Fallback error log created")
        except Exception as fallback_err:
            print(f"❌ Even fallback logging failed: {str(fallback_err)}")
            # At minimum, log to console
            print(f"CRITICAL: SAP PR Transaction Status: {transaction_status}, PR Code: {pr_code}")

    # **CREATE ERROR LOG ENTRY - Same as vendor function**
    try:
        if transaction_status == "Success":
            # Create success log
            success_log = frappe.new_doc("Error Log")
            success_log.method = "send_pr_detail"
            success_log.error = f"SAP PR Integration SUCCESS - PR Created: {pr_code}\nPR Doc: {doc.name}\nPR Type: {doc.purchase_requisition_type}\nSAP Client: {sap_code}\nSAP Name: {name_for_sap}"
            success_log.save(ignore_permissions=True)
            print(f"📝 Success Log created with name: {success_log.name}")
        else:
            # Create error log for failures
            error_log = frappe.new_doc("Error Log")
            error_log.method = "send_pr_detail"
            error_log.error = f"SAP PR Integration Error - {transaction_status}: {error_details[:1000]}"  # Truncate
            error_log.save(ignore_permissions=True)
            print(f"📝 Error Log created with name: {error_log.name}")
    except Exception as err_log_err:
        print(f"❌ Failed to create Error Log: {str(err_log_err)}")
        # Fallback to Frappe's built-in error logging
        frappe.log_error(
            title=f"SAP PR Integration - {transaction_status}",
            message=f"Status: {transaction_status}\nPR Doc: {doc.name}\nDetails: {error_details[:500]}"
        )
    
    frappe.db.commit()
    
    # Return appropriate response
    if response and response.status_code == 201:
        try:
            return response.json()  # Return the full SAP response
        except JSONDecodeError:
            return {
                "success": True, 
                "pr_code": pr_code, 
                "message": "PR created but response parsing failed",
                "transaction_status": transaction_status,
                "raw_response": response.text
            }
    else:
        return {
            "error": f"Failed to create PR in SAP. Status: {response.status_code if response else 'No response'}",
            "transaction_status": transaction_status,
            "error_details": error_details
        }


def send_pr_failure_notification(doc_name, failure_type, error_details):
    """Send email notifications to thunder00799@gmail.com when SAP PR integration fails"""
    try:
        # Get PR document
        pr_doc = frappe.get_doc("Purchase Requisition Form", doc_name)
        
        # Prepare email content
        subject = f"🚨 SAP PR Integration Alert: {failure_type} - {pr_doc.name}"
        
        # Get PR details for email
        pr_details = get_pr_details_for_email(pr_doc)
        
        # Create email message
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="background-color: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0; font-size: 24px;">🚨 SAP PR Integration Alert</h2>
                <p style="margin: 5px 0 0 0; font-size: 16px;">Action Required: {failure_type}</p>
            </div>
           
            <div style="padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <h3 style="color: #dc3545; margin-top: 0;">⚠️ Issue Summary</h3>
                    <p style="margin: 0; font-size: 16px; line-height: 1.5;"><strong>{error_details}</strong></p>
                </div>
               
                <h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px;">📋 Purchase Requisition Information</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; width: 40%;">PR Document</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['pr_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">PR Type</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['pr_type']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">SAP Client Code</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['sap_client_code']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Requisitioner</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['requisitioner']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Department</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['department']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Items Count</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['items_count']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Created By</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['owner']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Date & Time</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{frappe.utils.now()}</td>
                    </tr>
                </table>
               
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <h4 style="color: #856404; margin-top: 0;">🔍 Next Steps</h4>
                    <ul style="margin: 0; color: #856404;">
                        <li>Review the PR document details and processing logs</li>
                        <li>Check SAP connectivity and credentials</li>
                        <li>Verify PR data completeness and format</li>
                        <li>Check for payload structure issues (especially for SB type)</li>
                        <li>Contact IT team if technical issues persist</li>
                        <li>Retry the SAP PR integration after resolving issues</li>
                    </ul>
                </div>
            </div>
           
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #666; font-size: 12px;">
                <p style="margin: 0;">This is an automated alert from the VMS SAP PR Integration System</p>
                <p style="margin: 5px 0 0 0;">Please do not reply to this email</p>
            </div>
        </div>
        """
        
        # Send email to thunder00799@gmail.com
        try:
            frappe.custom_sendmail(
                recipients=["thunder00799@gmail.com", "rishi.hingad@merillife.com", "abhishek@mail.hybrowlabs.com"],
                subject=subject,
                message=message,
                now=True
            )
            print(f"📧 PR Failure notification sent to: thunder00799@gmail.com")
            
        except Exception as email_err:
            print(f"❌ Failed to send email to thunder00799@gmail.com: {str(email_err)}")
            frappe.log_error(f"Failed to send PR notification email: {str(email_err)}")
        
        # Log the notification
        frappe.log_error(
            title=f"SAP PR Integration Notification Sent - {failure_type}",
            message=f"PR Doc: {pr_details['pr_name']}\nError: {error_details}\nNotified: thunder00799@gmail.com"
        )
        
    except Exception as e:
        error_msg = f"Failed to send PR failure notification: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg)


def send_pr_success_notification(doc_name, pr_code, name_for_sap, pr_type):
    """Send success notification to thunder00799@gmail.com when PR is created successfully in SAP"""
    try:
        # Get PR document
        pr_doc = frappe.get_doc("Purchase Requisition Form", doc_name)
        
        # Prepare success email content
        subject = f"✅ SAP PR Integration Success: {pr_doc.name} - PR Code: {pr_code}"
        
        # Get PR details for email
        pr_details = get_pr_details_for_email(pr_doc)
        
        # Create success email message
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="background-color: #28a745; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0; font-size: 24px;">✅ SAP PR Integration Success</h2>
                <p style="margin: 5px 0 0 0; font-size: 16px;">Purchase Requisition Created Successfully</p>
            </div>
           
            <div style="padding: 20px;">
                <div style="background-color: #d4edda; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <h3 style="color: #155724; margin-top: 0;">🎉 Success Summary</h3>
                    <p style="margin: 0; font-size: 16px; line-height: 1.5;"><strong>PR successfully created in SAP with code: {pr_code}</strong></p>
                </div>
               
                <h3 style="color: #333; border-bottom: 2px solid #28a745; padding-bottom: 5px;">📋 Purchase Requisition Details</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; width: 40%;">SAP PR Code</td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: #28a745; font-weight: bold;">{pr_code}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">SAP Name</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{name_for_sap}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">PR Document</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['pr_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">PR Type</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['pr_type']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">SAP Client Code</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['sap_client_code']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Requisitioner</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['requisitioner']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Items Count</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{pr_details['items_count']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Processing Time</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{frappe.utils.now()}</td>
                    </tr>
                </table>
            </div>
           
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #666; font-size: 12px;">
                <p style="margin: 0;">This is an automated success notification from the VMS SAP PR Integration System</p>
                <p style="margin: 5px 0 0 0;">Please do not reply to this email</p>
            </div>
        </div>
        """
        
        # Send success email to thunder00799@gmail.com
        try:
            frappe.custom_sendmail(
                recipients=["thunder00799@gmail.com", "rishi.hingadd@merillife.com", "abhishek@mail.hybrowlabs.com"],
                subject=subject,
                message=message,
                now=True
            )
            print(f"📧 PR Success notification sent to: thunder00799@gmail.com")
            
        except Exception as email_err:
            print(f"❌ Failed to send success email to thunder00799@gmail.com: {str(email_err)}")
            frappe.log_error(f"Failed to send PR success notification email: {str(email_err)}")
        
        # Log the success notification
        frappe.log_error(
            title=f"SAP PR Integration Success Notification Sent",
            message=f"PR Doc: {pr_details['pr_name']}\nPR Code: {pr_code}\nSAP Name: {name_for_sap}\nNotified: thunder00799@gmail.com"
        )
        
    except Exception as e:
        error_msg = f"Failed to send PR success notification: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg)


def create_pr_sap_log(doc, request_data=None, response_data=None, transaction_status=None, error_details=None, sap_client_code=None, name_for_sap=None):
    """Create VMS SAP Log entry for PR transactions - Always creates log like vendor function"""
    try:
        print(f"📝 Creating VMS SAP Log for transaction status: {transaction_status or 'Unknown'}")
        
        # Handle None doc
        if not doc:
            print("❌ No document provided to create_pr_sap_log")
            return {"status": "error", "message": "Document is required"}
        
        sap_log = frappe.new_doc("PR SAP Logs")
        sap_log.purchase_requisition_link = doc.name
        sap_log.status = transaction_status or "Unknown"
        
        # Extract PR code (Banfn) with None handling
        pr_code = ""
        try:
            if response_data and hasattr(response_data, 'json'):
                pr_sap_code = response_data.json()
                if pr_sap_code and isinstance(pr_sap_code, dict):
                    pr_code = pr_sap_code.get('d', {}).get('Banfn', '')
        except Exception as pr_extract_err:
            print(f"⚠️ Could not extract PR code: {str(pr_extract_err)}")
        
        # Store request data (payload) - handle None
        sap_log.erp_to_sap_data = request_data if request_data is not None else {"error": "No request data available"}
        
        # Store response data - handle None and various types
        if response_data is not None:
            try:
                if isinstance(response_data, str):
                    # Try to parse string response as JSON
                    try:
                        sap_log.sap_response = json.loads(response_data)
                    except (json.JSONDecodeError, ValueError):
                        sap_log.sap_response = {"raw_response": response_data, "parse_error": "Could not parse as JSON"}
                elif hasattr(response_data, 'json'):
                    # Handle response objects with json() method
                    try:
                        sap_log.sap_response = response_data.json()
                    except Exception:
                        sap_log.sap_response = {"raw_response": str(response_data), "parse_error": "Could not call json() method"}
                else:
                    sap_log.sap_response = response_data
            except Exception as parse_err:
                sap_log.sap_response = {"response_data": str(response_data), "parse_error": str(parse_err)}
        else:
            sap_log.sap_response = {"error": error_details or "No response data available"}
        
        # Get PR type safely
        pr_type = getattr(doc, 'purchase_requisition_type', None) or "Unknown"
        
        # Create comprehensive transaction log for Code field (same structure as vendor function)
        total_transaction_data = {
            "request_details": {
                "url": f"SAP PR API - Client {sap_client_code or 'Unknown'}",
                "method": "POST",
                "payload": request_data if request_data is not None else "No payload available",
                "pr_document": doc.name if doc else "Unknown",
                "pr_type": pr_type
            },
            "response_details": {
                "status_code": "N/A - Error before API call" if response_data is None else "201",
                "body": response_data if response_data is not None else "No response received"
            },
            "transaction_summary": {
                "status": transaction_status or "Unknown",
                "pr_code": pr_code or "",
                "error_details": error_details or "",
                "timestamp": frappe.utils.now(),
                "sap_client_code": sap_client_code or "Unknown",
                "pr_doc_name": doc.name if doc else "Unknown",
                "pr_type": pr_type,
                "name_for_sap": name_for_sap or "",
                "failure_stage": transaction_status or "Unknown"
            }
        }
        
        sap_log.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)
        sap_log.save(ignore_permissions=True)
        print(f"📝 VMS SAP Log created successfully with name: {sap_log.name}")
        
        # Also create Error Log entry for consistency with vendor function
        try:
            if transaction_status == "Success":
                # Create success log
                success_log = frappe.new_doc("Error Log")
                success_log.method = "erp_to_sap_pr"
                success_log.error = (
                    f"SAP PR Integration SUCCESS - PR Doc: {doc.name if doc else 'Unknown'}\n"
                    f"PR Type: {pr_type}\n"
                    f"SAP Client: {sap_client_code or 'Unknown'}"
                )
                success_log.save(ignore_permissions=True)
                print(f"📝 Success Error Log created: {success_log.name}")
            else:
                # Create error log for failures
                error_log = frappe.new_doc("Error Log")
                error_details_str = str(error_details) if error_details else "No error details provided"
                error_log.method = "erp_to_sap_pr"
                error_log.error = f"SAP PR Integration Error - {transaction_status or 'Unknown'}: {error_details_str[:1000]}"  # Truncate
                error_log.save(ignore_permissions=True)
                print(f"📝 Failure Error Log created: {error_log.name}")
        except Exception as err_log_err:
            print(f"❌ Failed to create Error Log: {str(err_log_err)}")
        
        frappe.db.commit()
        return {"status": "success", "log_name": sap_log.name}
        
    except Exception as log_err:
        log_error_msg = f"Failed to create VMS SAP PR log: {str(log_err)}"
        print(f"❌ VMS SAP Log creation error: {log_error_msg}")
        
        # Create a minimal log entry using Frappe's error log as fallback
        try:
            doc_name = doc.name if doc and hasattr(doc, 'name') else 'Unknown'
            frappe.log_error(
                title=f"SAP PR Integration - {transaction_status or 'Unknown'}",
                message=(
                    f"PR Doc: {doc_name}\n"
                    f"Status: {transaction_status or 'Unknown'}\n"
                    f"Error: {error_details or 'No error details'}"
                )
            )
            print("📝 Fallback error log created")
        except Exception as fallback_err:
            print(f"❌ Even fallback logging failed: {str(fallback_err)}")
        
        return {"status": "error", "message": log_error_msg}

def get_pr_details_for_email(pr_doc):
    """Extract PR details for email notification"""
    try:
        return {
            "pr_name": pr_doc.name or "Unknown",
            "pr_type": pr_doc.purchase_requisition_type or "Not Set",
            "sap_client_code": pr_doc.sap_client_code or "Not Set",
            "requisitioner": pr_doc.requisitioner_first_name or "Not Set",
            "department": getattr(pr_doc, 'department', 'Not Specified'),  # Use getattr to avoid AttributeError
            "items_count": len(pr_doc.purchase_requisition_form_table) if pr_doc.purchase_requisition_form_table else 0,
            "owner": pr_doc.owner or "Unknown"
        }
    except Exception as e:
        print(f"⚠️ Error getting PR details: {str(e)}")
        return {
            "pr_name": "Unknown",
            "pr_type": "Unknown",
            "sap_client_code": "Unknown",
            "requisitioner": "Unknown",
            "department": "Unknown",
            "items_count": 0,
            "owner": "Unknown"
        }


def safe_get(obj, list_name, index, attr, default=""):
    """Helper function to safely get nested attributes"""
    try:
        return getattr(getattr(obj, list_name)[index], attr) or default
    except (AttributeError, IndexError, TypeError):
        return default








def onupdate_pr(doc, method = None):
    if not doc.sent_to_sap and doc.pr_approved:
        erp_to_sap_pr(doc.name, method=None)
        print("on update run")





# {'Banfn': '', 'Ztype': '', 'Ztext': '', 'Zvmsprno': 'PRF-2025-06-00001', 'ItemSet': [{'Bnfpo': '10', 'Matnr': 'EJBCO-00001', 'Txz01': 'Test text t1', 'Menge': '10', 'Meins': 'EA', 'Werks': '7100', 'Lgort': 'RM01', 'Afnam': 'HARIN', 'Bsart': 'NB', 'Ekgrp': '', 'Ernam': 'PRD1', 'Erdat': datetime.date(2025, 6, 17), 'Badat': datetime.date(2025, 6, 19), 'Anln1': '', 'Anln2': '', 'Knttp': '', 'Pstyp': '', 'Sakto': '', 'Kostl': '', 'Preis': ''}]}