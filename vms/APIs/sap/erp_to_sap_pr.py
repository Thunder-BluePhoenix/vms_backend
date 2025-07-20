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
        













import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, JSONDecodeError
from datetime import datetime

@frappe.whitelist(allow_guest=True)
def erp_to_sap_pr(doc_name, method=None):
    print("=" * 80)
    print("SEND PR DATA TO SAP - STARTING")
    print("=" * 80)
    
    try:
        doc = frappe.get_doc("Purchase Requisition Form", doc_name)
        sap_client_code = doc.sap_client_code
        now = datetime.now()
        year_month_prefix = f"P{now.strftime('%y')}{now.strftime('%m')}"  # e.g. PRF2506

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

        # Build data payload based on PR type
        data_list = build_pr_payload(doc, name_for_sap)
        
        if not data_list:
            error_msg = "Failed to build PR payload"
            frappe.log_error(error_msg)
            return {"error": error_msg}

        # Get CSRF token and session
        csrf_result = get_pr_csrf_token_and_session(sap_client_code)
        
        if csrf_result["success"]:
            try:
                # Send details to SAP
                result = send_pr_detail(
                    csrf_result["csrf_token"], 
                    data_list, 
                    csrf_result["session_cookies"],
                    doc, 
                    sap_client_code,
                    name_for_sap
                )
                return result
                
            except Exception as send_detail_err:
                error_msg = f"send_pr_detail error: {str(send_detail_err)[:100]}"
                print(f"❌ {error_msg}")
                # Don't use frappe.log_error to avoid cascading errors
                return {"error": error_msg}
        else:
            error_msg = f"CSRF token failed: {csrf_result['error'][:100]}"
            print(f"❌ {error_msg}")
            # Don't use frappe.log_error to avoid cascading errors
            return {"error": error_msg}
            
    except Exception as main_err:
        error_msg = f"Main error: {str(main_err)[:100]}"
        print(f"❌ {error_msg}")
        # Don't use frappe.log_error to avoid cascading errors
        return {"error": error_msg}


def build_pr_payload(doc, name_for_sap):
    """Build PR payload based on purchase requisition type"""
    try:
        if doc.purchase_requisition_type == "NB":
            data_list = {
                "Banfn": "",
                "Ztype": "",
                "Ztext": "",
                "Zvmsprno": "",
                "ItemSet": []
            }
            
            for item in doc.purchase_requisition_form_table:
                data = {
                    "Bnfpo": item.item_number_of_purchase_requisition_head or "",
                    "Matnr": item.material_code_head or "",
                    "Txz01": item.short_text_head or "",
                    "Menge": item.quantity_head or "",
                    "Meins": item.uom_head or "",
                    "Werks": item.plant_head or "",
                    "Lgort": item.store_location_head or "",
                    "Afnam": item.requisitioner_name_head or "",
                    "Bsart": item.purchase_requisition_type or "",
                    "Ekgrp": item.purchase_grp_code_head or "",
                    "Ernam": item.requisitioner_name_head or "",
                    "Erdat": item.purchase_requisition_date_head.strftime("%Y%m%d") if item.purchase_requisition_date_head else "",
                    "Badat": item.delivery_date_head.strftime("%Y%m%d") if item.delivery_date_head else "",
                    "Anln1": item.main_asset_no_head or "",
                    "Anln2": item.asset_subnumber_head or "",
                    "Knttp": item.account_assignment_category_head or "",
                    "Pstyp": item.item_category_head or "",
                    "Sakto": item.gl_account_number_head or "",
                    "Kostl": item.cost_center_head or "",
                    "Preis": item.final_price_by_purchase_team_head or "",
                    "Zvmsprno": doc.prf_name_for_sap or name_for_sap
                }
                data_list["ItemSet"].append(data)

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
            
            # Process ItemSet - one row per unique head_unique_id
            packno_counter = 1
            head_to_packno = {}
            service_items = []  # Collect service items separately
            
            for head_id, items in head_groups.items():
                first_item = items[0]
                head_to_packno[head_id] = str(packno_counter)
                
                data = {
                    "Bnfpo": first_item.item_number_of_purchase_requisition_head or "",
                    "Matnr": first_item.material_code_head or "",
                    "Txz01": first_item.short_text_head or "",
                    "Menge": first_item.quantity_head or "",
                    "Meins": first_item.uom_head or "",
                    "Werks": first_item.plant_head or "",
                    "Lgort": first_item.store_location_head or "",
                    "Afnam": first_item.requisitioner_name_head or "",
                    "Bsart": first_item.purchase_requisition_type or "",
                    "Ekgrp": first_item.purchase_grp_code_head or "",
                    "Ernam": first_item.requisitioner_name_head or "",
                    "Erdat": first_item.purchase_requisition_date_head.strftime("%Y%m%d") if first_item.purchase_requisition_date_head else "",
                    "Badat": first_item.delivery_date_head.strftime("%Y%m%d") if first_item.delivery_date_head else "",
                    "Anln1": first_item.main_asset_no_head or "",
                    "Anln2": first_item.asset_subnumber_head or "",
                    "Knttp": first_item.account_assignment_category_head or "",
                    "Pstyp": first_item.item_category_head or "",
                    "Sakto": first_item.gl_account_number_head or "",
                    "Kostl": first_item.cost_center_head or "",
                    "Preis": first_item.final_price_by_purchase_team_head or "",
                    "Zvmsprno": doc.prf_name_for_sap or name_for_sap,
                    "Packno": str(packno_counter)
                }
                
                data_list["ItemSet"].append(data)
                packno_counter += 1
                
                # Collect service items for this head
                for item in items:
                    if (item.short_text_subhead or item.quantity_subhead or 
                        item.uom_subhead or item.gross_price_subhead):
                        
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
                            "Kostl": item.cost_center_subhead or "",
                            "Sakto": item.gl_account_number_subhead or ""
                        }
                        service_items.append(subdata)
            
            # Only add ServSet if there are actual service items
            if service_items:
                data_list["ServSet"] = service_items
                print(f"📋 Added {len(service_items)} service items to ServSet")
            else:
                print("📋 No service items found, skipping ServSet")
                
        else:
            frappe.log_error(f"Unknown purchase requisition type: {doc.purchase_requisition_type}")
            return None

        print(f"✅ Payload built successfully for PR type: {doc.purchase_requisition_type}")
        print(f"📦 Items in payload: {len(data_list.get('ItemSet', []))}")
        if 'ServSet' in data_list:
            print(f"🔧 Services in payload: {len(data_list.get('ServSet', []))}")
        
        return data_list
        
    except Exception as e:
        error_msg = f"Error building PR payload: {str(e)}"
        frappe.log_error(error_msg)
        print(f"❌ {error_msg}")
        return None


def get_pr_csrf_token_and_session(sap_client_code):
    """Get CSRF token and session cookies for PR API"""
    try:
        sap_settings = frappe.get_doc("SAP Settings")
        erp_to_sap_pr_url = sap_settings.sap_pr_url
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
        
        print(f"CSRF Response Status: {response.status_code}")
        print(f"CSRF Response Headers: {dict(response.headers)}")
        print(f"CSRF Response Cookies: {dict(response.cookies)}")
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
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Exception while fetching PR CSRF token: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


@frappe.whitelist(allow_guest=True)
def send_pr_detail(csrf_token, data_list, session_cookies, doc, sap_code, name_for_sap):
    """Send PR details to SAP with comprehensive logging"""
    sap_settings = frappe.get_doc("SAP Settings")
    erp_to_sap_pr_url = sap_settings.sap_pr_url
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
    print(f"Payload Data:")
    print(json.dumps(data_list, indent=2, default=str))
    print("=" * 80)
    
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data_list, timeout=30)
        sap_response_text = response.text
        
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
                
                # Check if PR code indicates error or is empty
                if pr_code == 'E' or pr_code == '' or not pr_code:
                    transaction_status = "SAP Error"
                    error_details = f"SAP returned error PR code. Banfn: '{pr_code}'"
                    print(f"❌ SAP PR Error: {error_details}")
                else:
                    transaction_status = "Success"
                    print(f"✅ PR details posted successfully. PR Code: {pr_code}")
                    
                    # Update the document with SAP details
                    doc.sent_to_sap = 1
                    doc.sap_pr_code = pr_code
                    if not doc.prf_name_for_sap:
                        doc.prf_name_for_sap = name_for_sap
                    doc.db_update()
                
                print(f"✅ Full SAP PR Response: {json.dumps(pr_sap_code, indent=2)}")
                
            except (JSONDecodeError, KeyError) as json_err:
                error_details = f"JSON parse error or missing Banfn: {str(json_err)[:200]}"
                transaction_status = "JSON Parse Error"
                print(f"❌ JSON parsing error: {error_details}")
                
        elif response.status_code == 400:
            # Handle specific SAP API errors (like ServSet property error)
            error_details = f"SAP API validation error: {response.text[:300]}"
            transaction_status = "SAP Validation Error"
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
                
        elif response.status_code == 403:
            error_details = f"CSRF Token validation failed"
            transaction_status = "CSRF Token Error"
            print(f"❌ CSRF Error: {error_details}")
            
        elif response.status_code != 201:
            error_details = f"SAP PR API returned status {response.status_code}"
            transaction_status = f"HTTP Error {response.status_code}"
            print(f"❌ Error in POST request: {error_details}")
            
        else:
            error_details = "Empty response from SAP PR API"
            transaction_status = "Empty Response"
            print(f"❌ Error: {error_details}")

    except RequestException as req_err:
        error_details = f"Network error: {str(req_err)[:200]}"
        transaction_status = "Request Exception"
        print(f"❌ Request error: {error_details}")
        sap_response_text = str(req_err)
        
    except Exception as e:
        error_details = f"Unexpected error: {str(e)[:200]}"
        transaction_status = "Unexpected Error"
        print(f"❌ Unexpected error: {error_details}")
        sap_response_text = str(e)

    # Always log the transaction with full data
    try:
        sap_log = frappe.new_doc("VMS SAP Logs")
        sap_log.purchase_requisition_link = doc.name
        
        # Store full data since erp_to_sap_data is JSON field
        sap_log.erp_to_sap_data = data_list
        
        # Store full response since sap_response is JSON field  
        if response and response.text.strip():
            try:
                sap_log.sap_response = response.json()
            except JSONDecodeError:
                sap_log.sap_response = {"raw_response": response.text, "parse_error": "Could not parse as JSON"}
        else:
            sap_log.sap_response = {"error": sap_response_text}
        
        # Create comprehensive transaction log for Code field
        total_transaction_data = {
            "request_details": {
                "url": url,
                "headers": {k: v for k, v in headers.items() if k != 'Authorization'},
                "auth_user": user,
                "payload": data_list
            },
            "response_details": {
                "status_code": response.status_code if response else "No Response",
                "headers": dict(response.headers) if response else {},
                "body": response.json() if response and response.text.strip() else sap_response_text
            },
            "transaction_summary": {
                "status": transaction_status,
                "pr_code": pr_code,
                "error_details": error_details,
                "timestamp": frappe.utils.now(),
                "sap_client_code": sap_code,
                "pr_doc_name": doc.name,
                "pr_type": doc.purchase_requisition_type,
                "name_for_sap": name_for_sap
            }
        }
        
        sap_log.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)
        sap_log.save(ignore_permissions=True)
        print(f"📝 SAP PR Log created with name: {sap_log.name}")
        
    except Exception as log_err:
        log_error_msg = f"Failed to create SAP PR log: {str(log_err)}"
        print(f"❌ Log creation error: {log_error_msg}")
        
        # Create a minimal log entry using console output only
        try:
            print("📝 Fallback: Logging to console only due to log creation failure")
            print(f"📋 Transaction: {transaction_status}")
            print(f"📋 PR Doc: {doc.name}")
            print(f"📋 Error: {error_details[:200]}")
        except Exception as fallback_err:
            print(f"❌ Even console logging failed: {str(fallback_err)}")

    # Create error log entry for transactions (with truncated messages)
    try:
        if transaction_status == "Success":
            # Create success log with short title
            success_log = frappe.new_doc("Error Log")
            success_log.method = "send_pr_detail"
            success_log.error = f"SAP PR SUCCESS: {pr_code}\nDoc: {doc.name}\nType: {doc.purchase_requisition_type}\nClient: {sap_code}"
            success_log.save(ignore_permissions=True)
            print(f"📝 Success Log created with name: {success_log.name}")
        else:
            # Create error log for failures with truncated error message
            error_log = frappe.new_doc("Error Log")
            error_log.method = "send_pr_detail"
            # Truncate error details to avoid length issues
            truncated_error = error_details[:100] + "..." if len(error_details) > 100 else error_details
            error_log.error = f"SAP PR {transaction_status}: {truncated_error}\nDoc: {doc.name}"
            error_log.save(ignore_permissions=True)
            print(f"📝 Error Log created with name: {error_log.name}")
    except Exception as err_log_err:
        print(f"❌ Failed to create Error Log: {str(err_log_err)}")
        # Don't use frappe.log_error here to avoid cascading errors
    
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


def safe_get(obj, list_name, index, attr, default=""):
    try:
        return getattr(getattr(obj, list_name)[index], attr) or default
    except (AttributeError, IndexError, TypeError):
        return default


















def onupdate_pr(doc, method = None):
    if not doc.sent_to_sap:
        erp_to_sap_pr(doc.name, method=None)
        print("on update run")





# {'Banfn': '', 'Ztype': '', 'Ztext': '', 'Zvmsprno': 'PRF-2025-06-00001', 'ItemSet': [{'Bnfpo': '10', 'Matnr': 'EJBCO-00001', 'Txz01': 'Test text t1', 'Menge': '10', 'Meins': 'EA', 'Werks': '7100', 'Lgort': 'RM01', 'Afnam': 'HARIN', 'Bsart': 'NB', 'Ekgrp': '', 'Ernam': 'PRD1', 'Erdat': datetime.date(2025, 6, 17), 'Badat': datetime.date(2025, 6, 19), 'Anln1': '', 'Anln2': '', 'Knttp': '', 'Pstyp': '', 'Sakto': '', 'Kostl': '', 'Preis': ''}]}