import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth



@frappe.whitelist(allow_guest=True)
def erp_to_sap_pr(doc_name, method=None):
    print("SEND data to sap run")
    doc = frappe.get_doc("Purchase Requisition Form", doc_name)
    sap_client_code = doc.sap_client_code

    


    data_list = {
        "Banfn": "",
        "Ztype": "",
        "Ztext": "",
        "Zvmsprno": "",
        "ItemSet":[]
    }
    # child_data = []
    for item in doc.purchase_requisition_form_table:
        
        data =  {
                "Bnfpo" : item.item_number_of_purchase_requisition or "",
                "Matnr" : item.material_code or "",
                "Txz01" : item.short_text or "",
                "Menge" : item.quantity or "",
                "Meins" : item.uom or "",
                "Werks" : item.plant or "",
                "Lgort" : item.store_location or "",
                "Afnam" : item.requisitioner_name or "",
                "Bsart" : item.purchase_requisition_type or "",
                "Ekgrp" : item.purchase_group or "",
                "Ernam" : item.created_by or "",
                "Erdat" : item.requisition_date or "",
                "Badat" : item.delivery_date or "",
                "Anln1" : item.main_asset_no or "",
                "Anln2" : item.asset_subnumber or "",
                "Knttp" : item.account_assignment_category or "",
                "Pstyp" : item.item_category or "",
                "Sakto" : item.gl_account_number or "",
                "Kostl" : item.cost_center or "",
                "Preis" : item.price_in_purchase_requisition or "",
                "Zvmsprno": doc.name
                }

        data_list["ItemSet"].append(data)
        # print("json data", data)

    # print("data_list", data_list)

    # data_list = ["ItemSet"]

    sap_settings = frappe.get_doc("SAP Settings")
    erp_to_sap_pr_url = sap_settings.sap_pr_url
    url = f"{erp_to_sap_pr_url}"
    header_auth_type = sap_settings.authorization_type
    header_auth_key = sap_settings.authorization_key
    user = sap_settings.auth_user_name
    password = sap_settings.auth_user_pass

    headers = {
        'X-CSRF-TOKEN': 'Fetch',
        'Authorization': f"{header_auth_type} {header_auth_key}",
        'Content-Type': 'application/json'
    }

    
    auth = HTTPBasicAuth(user, password)
    response = requests.get(url, headers=headers, auth=auth)
    # print("resssssssssssssssssssssssssss",response.text)

    if response.status_code == 200:
        
        csrf_token = response.headers.get('x-csrf-token')
        key1 = response.cookies.get(f'SAP_SESSIONID_BHD_{sap_client_code}')
        key2 = response.cookies.get('sap-usercontext')
        
        # Sending details to SAP
        send_detail(csrf_token, data_list, key1, key2, doc_name, sap_client_code)
        
        return data
    else:
        # frappe.log_error(f"Failed to fetch CSRF token from SAP: {response.status_code if response else 'No response'}")
        return None
   

def safe_get(obj, list_name, index, attr, default=""):
    try:
        return getattr(getattr(obj, list_name)[index], attr) or default
    except (AttributeError, IndexError, TypeError):
        return default






@frappe.whitelist(allow_guest=True)
def send_detail(csrf_token, data_list, key1, key2, name, sap_code):

    sap_settings = frappe.get_doc("SAP Settings")
    erp_to_sap_pr_url = sap_settings.sap_pr_url
    url = f"{erp_to_sap_pr_url}"
    header_auth_type = sap_settings.authorization_type
    header_auth_key = sap_settings.authorization_key
    user = sap_settings.auth_user_name
    password = sap_settings.auth_user_pass

    headers = {
        'X-CSRF-TOKEN': csrf_token,
        'Authorization': f"{header_auth_type} {header_auth_key}",
        'Content-Type': 'application/json;charset=utf-8',
        'Accept': 'application/json',
        'Cookie': f"SAP_SESSIONID_BHD_{sap_code}={key1}; sap-usercontext={key2}"
    }

    auth = HTTPBasicAuth(user, password)
    print("*************")
    
    try:
        response = requests.post(url, headers=headers, auth=auth ,json=data_list)
        pr_sap_code = response.json()
        # pr_code = pr_sap_code['d']['Vedno']
        # print("response", response.json())
        
        


        pr_doc = frappe.get_doc("Purchase Requisition Form", name)
        pr_doc.sent_to_sap = 1
        
        
        
        sap_log = frappe.new_doc("VMS SAP Logs")
        sap_log.purchase_requisition_link = name
        sap_log.erp_to_sap_data = data_list
        sap_log.sap_response = response.text

        sap_log.save(ignore_permissions=True)
        

        
        frappe.db.commit()
        
        return response.json()
    except ValueError:
        print("************************** Response is here *********************", response.json())
        sap_log = frappe.new_doc("VMS SAP Logs")
        sap_log.purchase_requisition_link = name
        sap_log.erp_to_sap_data = data_list
        sap_log.sap_response = response.text

        sap_log.save(ignore_permissions=True)
    
    
    if response.status_code == 201:  
        print("*****************************************")
        print("Vendor details posted successfully.")
        return response.json()
    

    else:
        print("******************************************")
        print("Error in POST request:", response.status_code)
        



def onupdate_pr(doc, method = None):
    if doc.sent_to_sap is not 1:
        erp_to_sap_pr(doc.name, method=None)
        print("on update run")





# {'Banfn': '', 'Ztype': '', 'Ztext': '', 'Zvmsprno': 'PRF-2025-06-00001', 'ItemSet': [{'Bnfpo': '10', 'Matnr': 'EJBCO-00001', 'Txz01': 'Test text t1', 'Menge': '10', 'Meins': 'EA', 'Werks': '7100', 'Lgort': 'RM01', 'Afnam': 'HARIN', 'Bsart': 'NB', 'Ekgrp': '', 'Ernam': 'PRD1', 'Erdat': datetime.date(2025, 6, 17), 'Badat': datetime.date(2025, 6, 19), 'Anln1': '', 'Anln2': '', 'Knttp': '', 'Pstyp': '', 'Sakto': '', 'Kostl': '', 'Preis': ''}]}