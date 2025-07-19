import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth

# @frappe.whitelist(allow_guest=True)
# def erp_to_sap_vendor_data(onb_ref):
#     onb = frappe.get_doc("Vendor Onboarding", onb_ref)
#     onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
#     onb_pmd = frappe.get_doc("Vendor Onboarding Payment Details", onb.payment_detail)
#     # onb_doc = frappe.get_doc("Legal Documents", onb.document_details)
#     # onb_cer = frappe.get_doc("Vendor Onboarding Certificates", onb.certificate_details)
#     # onb_mnd = frappe.get_doc("Vendor Onboarding Manufacturing Details", onb.manufacturing_details)
#     pur_org = frappe.get_doc("Purchase Organization Master", onb.purchase_organization)
#     pur_grp = frappe.get_doc("Purchase Group Master", onb.purchase_group)
#     acc_grp = frappe.get_doc("Account Group Master", onb.account_group)
#     onb_reco = frappe.get_doc("Reconciliation Account", onb.reconciliation_account)
#     onb_pm_term = frappe.get_doc("Terms of Payment Master", onb.terms_of_payment)
#     onb_inco = frappe.get_doc("Incoterm Master", onb.incoterms)
#     onb_bank = frappe.get_doc("Bank Master", onb_pmd.bank_name)


#     payee = 'X' if onb.payee_in_document == 1 else ''
#     gr_based_inv_ver = 'X' if onb.gr_based_inv_ver == 1 else ''
#     service_based_inv_ver = 'X' if onb.service_based_inv_ver == 1 else ''
#     check_double_invoice = 'X' if onb.check_double_invoice == 1 else ''

    
#     vendor_type_names = []
#     for row in onb_vm.vendor_types:
#         if row.vendor_type:
#             vendor_type_doc = frappe.get_doc("Vendor Type Master", row.vendor_type)
#             vendor_type_names.append(vendor_type_doc.vendor_type_name)
#     vendor_type_names_str = ", ".join(vendor_type_names)


#     data_list = []
#     for company in onb.vendor_company_details:
#         vcd = frappe.get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
#         country_doc = frappe.get_doc("Country Master", vcd.country)
#         country_code = country_doc.country_code
#         com_vcd = frappe.get_doc("Company Master", vcd.company_name)
#         com_code = com_vcd.company_code
#         sap_client_code = com_vcd.sap_client_code
#         vcd_state = frappe.get_doc("State Master", vcd.state)

        




#         data =  {
#             "Bukrs": com_vcd.company_code,
#             "Ekorg": pur_org.purchase_organization_code,
#             "Ktokk": acc_grp.account_group_code,
#             "Title": "",
#             "Name1": onb_vm.vendor_name,
#             "Name2": "",
#             "Sort1": onb_vm.search_term,
#             "Street": vcd.address_line_1,
#             "StrSuppl1": vcd.address_line_2,
#             "StrSuppl2": "",
#             "StrSuppl3": "",
#             "PostCode1": vcd.pincode,
#             "City1": vcd.city,
#             "Country": country_code,
#             "J1kftind": "",
#             "Region": vcd_state.sap_state_code,
#             "TelNumber": "",
#             "MobNumber": onb_vm.mobile_number,
#             "SmtpAddr": onb_vm.office_email_primary,
#             "SmtpAddr1": onb_vm.office_email_secondary or "",
#             "Zuawa": "",
#             "Akont": onb_reco.reconcil_account_code,
#             "Waers": onb_pmd.currency_code,
#             "Zterm": onb_pm_term.terms_of_payment_code,
#             "Inco1": onb_inco.incoterm_code,
#             "Inco2": onb_inco.incoterm_name,
#             "Kalsk": "",
#             "Ekgrp": pur_grp.purchase_group_code,
#             "Xzemp": payee,
#             "Reprf": check_double_invoice,
#             "Webre": gr_based_inv_ver,
#             "Lebre": service_based_inv_ver,
#             "Stcd3": vcd.gst,
#             "J1ivtyp": vendor_type_names[0],
#             "J1ipanno": vcd.company_pan_number,
#             "J1ipanref": onb_vm.vendor_name,
#             "Namev": safe_get(onb, "contact_details", 0, "first_name"),
#             "Name11": safe_get(onb, "contact_details", 0, "last_name"),
#             "Bankl": onb_bank.bank_code,
#             "Bankn": onb_pmd.account_number,
#             "Bkref": onb_bank.bank_name,
#             "Banka": onb_pmd.ifsc_code ,
#             # "koinh": onb_pmd.name_of_account_holder, #name_of_account_holder,
#             "Xezer": "",
#             "ZZBENF_NAME": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_name"),
#             "ZZBEN_BANK_NM": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_name"),
#             "ZZBEN_ACCT_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_account_no"),
#             "ZZBENF_IBAN": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_iban_no"),
#             "ZZBENF_BANKADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_address"),
#             "ZZBENF_SHFTADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_swift_code"),
#             "ZZBENF_ACH_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_ach_no"),
#             "ZZBENF_ABA_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_aba_no"),
#             "ZZBENF_ROUTING": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_routing_no"),

#             "ZZINTR_ACCT_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_account_no"),
#             "ZZINTR_IBAN": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_iban_no"),
#             "ZZINTR_BANK_NM": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_name"),
#             "ZZINTR_BANKADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_address"),
#             "ZZINTR_SHFTADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_swift_code"),
#             "ZZINTR_ACH_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_ach_no"),
#             "ZZINTR_ABA_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_aba_no"),
#             "ZZINTR_ROUTING": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_routing_no"),
#             "Refno": onb.ref_no,
#             "Vedno": "",
#             "Zmsg": ""
#                 }
#         data_list.append(data)

#         sap_settings = frappe.get_doc("SAP Settings")
#         erp_to_sap_url = sap_settings.url
#         url = f"{erp_to_sap_url}{sap_client_code}"
#         header_auth_type = sap_settings.authorization_type
#         header_auth_key = sap_settings.authorization_key
#         user = sap_settings.auth_user_name
#         password = sap_settings.auth_user_pass

#         headers = {
#             'X-CSRF-TOKEN': 'Fetch',
#             'Authorization': f"{header_auth_type} {header_auth_key}",
#             'Content-Type': 'application/json'
#         }

#         # url = f"http://10.10.103.133:8000/sap/opu/odata/sap/ZMM_VENDOR_SRV/VENDORSet?sap-client={sap_client_code}"
        
#         # headers = {
#         #     'X-CSRF-TOKEN': 'Fetch',
#         #     'Authorization': 'Basic V0YtQkFUQ0g6TUB3YiMkJTIwMjQ=',
#         #     'Content-Type': 'application/json'
#         #     }
#         auth = HTTPBasicAuth(user, password)
#         response = requests.get(url, headers=headers, auth=auth)
#         print("SAP HEADER", headers, auth, response)
    
#         if response.status_code == 200:
            
#             csrf_token = response.headers.get('x-csrf-token')
#             print("SAP csrf_token", csrf_token)
#             key1 = response.cookies.get(f'SAP_SESSIONID_BHD_{sap_client_code}')
#             key2 = response.cookies.get('sap-usercontext')
            
#             # Sending details to SAP
#             send_detail(csrf_token, data, key1, key2, onb.ref_no, sap_client_code, vcd.state, vcd.gst, vcd.company_name, onb.name)
            
#             return data
#         else:
#             frappe.log_error(f"Failed to fetch CSRF token from SAP: {response.status_code if response else 'No response'}")
#             return None
   

# def safe_get(obj, list_name, index, attr, default=""):
#     try:
#         return getattr(getattr(obj, list_name)[index], attr) or default
#     except (AttributeError, IndexError, TypeError):
#         return default

# #******************************* SAP PUSH  ************************************************************

# @frappe.whitelist(allow_guest=True)
# def send_detail(csrf_token, data, key1, key2, name, sap_code, state, gst, company_name, onb_name):
#     print("send details sap csrf token", csrf_token)

#     sap_settings = frappe.get_doc("SAP Settings")
#     erp_to_sap_url = sap_settings.url
#     url = f"{erp_to_sap_url}{sap_code}"
#     header_auth_type = sap_settings.authorization_type
#     header_auth_key = sap_settings.authorization_key
#     user = sap_settings.auth_user_name
#     password = sap_settings.auth_user_pass

#     headers = {
#         'X-CSRF-TOKEN': csrf_token,
#         # 'Authorization': f"{header_auth_type} {header_auth_key}",
#         'Content-Type': 'application/json;charset=utf-8',
#         'Accept': 'application/json',
#         'Cookie': f"SAP_SESSIONID_BHD_{sap_code}={key1}; sap-usercontext={key2}"
#     }
#     print("headersssssss", headers)

#     # url = f"http://10.10.103.133:8000/sap/opu/odata/sap/ZMM_VENDOR_SRV/VENDORSet?sap-client={sap_code}"
   
#     # #pdb.set_trace()
#     # headers = {

#     #     'X-CSRF-TOKEN': csrf_token,
#     #     'Content-Type': 'application/json;charset=utf-8',
#     #     'Accept': 'application/json',
#     #     'Authorization': 'Basic V0YtQkFUQ0g6TUB3YiMkJTIwMjQ=',
#     #     'Cookie': f"SAP_SESSIONID_BHD_{sap_code}={key1}; sap-usercontext={key2}"
#     # }
#     auth = HTTPBasicAuth(user, password)
#     print("*************")
    
#     try:
#         response = requests.post(url, headers=headers, auth=auth ,json=data)
#         vendor_sap_code = response.json()
#         vendor_code = vendor_sap_code['d']['Vedno']
#         # frappe.log_error(f"vendor code: {vendor_sap_code if response else 'No response'}")
#         print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", response.txt)
        


#         ref_vm = frappe.get_doc("Vendor Master", name)
        
#         cvc = None
#         cvc_name = frappe.db.exists("Company Vendor Code", {"sap_client_code": sap_code, "vendor_ref_no": ref_vm.name})
#         cvc = frappe.get_doc("Company Vendor Code", cvc_name) if cvc_name else None



#         if cvc == None:
#             cvc = frappe.new_doc("Company Vendor Code")  
#             cvc.vendor_ref_no = ref_vm.name
#             cvc.company_name = company_name
#             cvc.append("vendor_code", {
#                 "vendor_code": vendor_code,
#                 "gst_no": gst,
#                 "state": state
#             })
#         else:
#             found = False
#             for vc in cvc.vendor_code:
#                 if vc.gst_no == gst or vc.state == state:
#                     vc.vendor_code = vendor_code
#                     vc.gst_no = gst
#                     vc.state = state
#                     found = True
#                     break

#             if not found:
#                 cvc.append("vendor_code", {
#                     "vendor_code": vendor_code,
#                     "gst_no": gst,
#                     "state": state
#                 })

#         cvc.save()

#         # found = False
#         # for mcd in ref_vm.multiple_company_data:
#         #     if mcd.sap_client_code == sap_code:
#         #         mcd.company_vendor_code = cvc.name
#         #         found = True
#         #         break

#         # if not found:
#         #     ref_vm.append("multiple_company_data", {
#         #         "company_vendor_code": cvc.name,
#         #         "gst_no": gst,
#         #         "state": state
#         #     })
#         ref_vm.db_update()
#         sap_log = frappe.new_doc("VMS SAP Logs")
#         sap_log.vendor_onboarding_link = onb_name
#         sap_log.erp_to_sap_data = data
#         sap_log.sap_response = response.text

#         sap_log.save(ignore_permissions=True)
        

        
#         frappe.db.commit()
        
#         return response.json()
#     except ValueError:
#         print("************************** Response is here *********************", response.json())
#         sap_log = frappe.new_doc("VMS SAP Logs")
#         sap_log.vendor_onboarding_link = onb_name
#         sap_log.erp_to_sap_data = data
#         sap_log.sap_response =  response.text
#         sap_log.save()
    
    
#     if response.status_code == 201:  
#         print("*****************************************")
#         print("Vendor details posted successfully.")
#         return response.json()
    

#     else:
#         print("******************************************")
#         print("Error in POST request:", response.status_code)
        




def update_sap_vonb(doc, method=None):
    if doc.purchase_team_undertaking and doc.accounts_team_undertaking and doc.purchase_head_undertaking and not doc.rejected and not doc.data_sent_to_sap:
        erp_to_sap_vendor_data(doc.name)
        doc.data_sent_to_sap = 1
        # doc.save()
        doc.db_update()
        frappe.db.commit()





import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, JSONDecodeError

@frappe.whitelist(allow_guest=True)
def erp_to_sap_vendor_data(onb_ref):
    onb = frappe.get_doc("Vendor Onboarding", onb_ref)
    onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
    onb_pmd = frappe.get_doc("Vendor Onboarding Payment Details", onb.payment_detail)
    pur_org = frappe.get_doc("Purchase Organization Master", onb.purchase_organization)
    pur_grp = frappe.get_doc("Purchase Group Master", onb.purchase_group)
    acc_grp = frappe.get_doc("Account Group Master", onb.account_group)
    onb_reco = frappe.get_doc("Reconciliation Account", onb.reconciliation_account)
    onb_pm_term = frappe.get_doc("Terms of Payment Master", onb.terms_of_payment)
    onb_inco = frappe.get_doc("Incoterm Master", onb.incoterms)
    onb_bank = frappe.get_doc("Bank Master", onb_pmd.bank_name)

    payee = 'X' if onb.payee_in_document == 1 else ''
    gr_based_inv_ver = 'X' if onb.gr_based_inv_ver == 1 else ''
    service_based_inv_ver = 'X' if onb.service_based_inv_ver == 1 else ''
    check_double_invoice = 'X' if onb.check_double_invoice == 1 else ''

    vendor_type_names = []
    for row in onb_vm.vendor_types:
        if row.vendor_type:
            vendor_type_doc = frappe.get_doc("Vendor Type Master", row.vendor_type)
            vendor_type_names.append(vendor_type_doc.vendor_type_name)
    vendor_type_names_str = ", ".join(vendor_type_names)

    data_list = []
    for company in onb.vendor_company_details:
        vcd = frappe.get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
        country_doc = frappe.get_doc("Country Master", vcd.country)
        country_code = country_doc.country_code
        com_vcd = frappe.get_doc("Company Master", vcd.company_name)
        com_code = com_vcd.company_code
        sap_client_code = com_vcd.sap_client_code
        vcd_state = frappe.get_doc("State Master", vcd.state)

        data = {
            "Bukrs": com_vcd.company_code,
            "Ekorg": pur_org.purchase_organization_code,
            "Ktokk": acc_grp.account_group_code,
            "Title": "",
            "Name1": onb_vm.vendor_name,
            "Name2": "",
            "Sort1": onb_vm.search_term,
            "Street": vcd.address_line_1,
            "StrSuppl1": vcd.address_line_2,
            "StrSuppl2": "",
            "StrSuppl3": "",
            "PostCode1": vcd.pincode,
            "City1": vcd.city,
            "Country": country_code,
            "J1kftind": "",
            "Region": vcd_state.sap_state_code,
            "TelNumber": "",
            "MobNumber": onb_vm.mobile_number,
            "SmtpAddr": onb_vm.office_email_primary,
            "SmtpAddr1": onb_vm.office_email_secondary or "",
            "Zuawa": "",
            "Akont": onb_reco.reconcil_account_code,
            "Waers": onb_pmd.currency_code,
            "Zterm": onb_pm_term.terms_of_payment_code,
            "Inco1": onb_inco.incoterm_code,
            "Inco2": onb_inco.incoterm_name,
            "Kalsk": "",
            "Ekgrp": pur_grp.purchase_group_code,
            "Xzemp": payee,
            "Reprf": check_double_invoice,
            "Webre": gr_based_inv_ver,
            "Lebre": service_based_inv_ver,
            "Stcd3": vcd.gst,
            "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
            "J1ipanno": vcd.company_pan_number,
            "J1ipanref": onb_vm.vendor_name,
            "Namev": safe_get(onb, "contact_details", 0, "first_name"),
            "Name11": safe_get(onb, "contact_details", 0, "last_name"),
            "Bankl": onb_bank.bank_code,
            "Bankn": onb_pmd.account_number,
            "Bkref": onb_bank.bank_name,
            "Banka": onb_pmd.ifsc_code,
            "Xezer": "",
            "ZZBENF_NAME": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_name"),
            "ZZBEN_BANK_NM": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_name"),
            "ZZBEN_ACCT_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_account_no"),
            "ZZBENF_IBAN": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_iban_no"),
            "ZZBENF_BANKADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_address"),
            "ZZBENF_SHFTADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_swift_code"),
            "ZZBENF_ACH_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_ach_no"),
            "ZZBENF_ABA_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_aba_no"),
            "ZZBENF_ROUTING": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_routing_no"),
            "ZZINTR_ACCT_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_account_no"),
            "ZZINTR_IBAN": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_iban_no"),
            "ZZINTR_BANK_NM": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_name"),
            "ZZINTR_BANKADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_address"),
            "ZZINTR_SHFTADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_swift_code"),
            "ZZINTR_ACH_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_ach_no"),
            "ZZINTR_ABA_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_aba_no"),
            "ZZINTR_ROUTING": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_routing_no"),
            "Refno": onb.ref_no,
            "Vedno": "",
            "Zmsg": ""
        }
        data_list.append(data)

        sap_settings = frappe.get_doc("SAP Settings")
        erp_to_sap_url = sap_settings.url
        url = f"{erp_to_sap_url}{sap_client_code}"
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
        
        try:
            response = requests.get(url, headers=headers, auth=auth, timeout=30)
            
            if response.status_code == 200:
                csrf_token = response.headers.get('x-csrf-token')
                key1 = response.cookies.get(f'SAP_SESSIONID_BHD_{sap_client_code}')
                key2 = response.cookies.get('sap-usercontext')
                
                # Sending details to SAP
                result = send_detail(csrf_token, data, key1, key2, onb.ref_no, sap_client_code, vcd.state, vcd.gst, vcd.company_name, onb.name)
                return result
            else:
                error_msg = f"Failed to fetch CSRF token from SAP. Status: {response.status_code}, Response: {response.text}"
                frappe.log_error(error_msg)
                return {"error": error_msg}
                
        except RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            frappe.log_error(error_msg)
            return {"error": error_msg}


def safe_get(obj, list_name, index, attr, default=""):
    try:
        return getattr(getattr(obj, list_name)[index], attr) or default
    except (AttributeError, IndexError, TypeError):
        return default


@frappe.whitelist(allow_guest=True)
def send_detail(csrf_token, data, key1, key2, name, sap_code, state, gst, company_name, onb_name):
    sap_settings = frappe.get_doc("SAP Settings")
    erp_to_sap_url = sap_settings.url
    url = f"{erp_to_sap_url}{sap_code}"
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
    
    # Initialize response variables
    response = None
    vendor_code = None
    sap_response_text = ""
    transaction_status = "Failed"
    error_details = ""
    
    # Print complete payload for debugging
    print("=" * 80)
    print("SAP API PAYLOAD DEBUG")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(dict(headers), indent=2)}")
    print(f"Auth User: {user}")
    print(f"Payload Data:")
    print(json.dumps(data, indent=2, default=str))
    print("=" * 80)
    
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, timeout=30)
        sap_response_text = response.text
        
        # Debug response details
        print("=" * 80)
        print("SAP API RESPONSE DEBUG")
        print("=" * 80)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content Length: {len(response.text)}")
        print(f"Response Content: {response.text}")
        print("=" * 80)
        
        # Check if response has content and is valid JSON
        if response.status_code == 201 and response.text.strip():
            try:
                vendor_sap_code = response.json()
                vendor_code = vendor_sap_code.get('d', {}).get('Vedno', '')
                transaction_status = "Success"
                print(f"✅ Vendor details posted successfully. Vendor Code: {vendor_code}")
                
            except (JSONDecodeError, KeyError) as json_err:
                error_details = f"Invalid JSON response from SAP: {str(json_err)}"
                transaction_status = "JSON Parse Error"
                frappe.log_error(error_details)
                print(f"❌ JSON parsing error: {error_details}")
                
        elif response.status_code != 201:
            error_details = f"SAP API returned status {response.status_code}: {response.text}"
            transaction_status = f"HTTP Error {response.status_code}"
            frappe.log_error(error_details)
            print(f"❌ Error in POST request: {error_details}")
            
        else:
            error_details = "Empty response from SAP API"
            transaction_status = "Empty Response"
            frappe.log_error(error_details)
            print(f"❌ Error: {error_details}")

    except RequestException as req_err:
        error_details = f"Request failed: {str(req_err)}"
        transaction_status = "Request Exception"
        frappe.log_error(error_details)
        print(f"❌ Request error: {error_details}")
        sap_response_text = str(req_err)
        
    except Exception as e:
        error_details = f"Unexpected error: {str(e)}"
        transaction_status = "Unexpected Error"
        frappe.log_error(error_details)
        print(f"❌ Unexpected error: {error_details}")
        sap_response_text = str(e)

    # Always log the transaction with detailed information
    try:
        sap_log = frappe.new_doc("VMS SAP Logs")
        sap_log.vendor_onboarding_link = onb_name
        sap_log.erp_to_sap_data = json.dumps(data, indent=2, default=str)
        sap_log.sap_response = sap_response_text
        
        # Add the total_transaction field for debugging
        sap_log.total_transaction = json.dumps({
            "request_url": url,
            "request_headers": dict(headers),
            "request_payload": data,
            "response_status": response.status_code if response else "No Response",
            "response_headers": dict(response.headers) if response else {},
            "response_body": response.text if response else "No Response",
            "transaction_status": transaction_status,
            "error_details": error_details,
            "vendor_code": vendor_code,
            "timestamp": frappe.utils.now(),
            "sap_client_code": sap_code,
            "company_name": company_name,
            "vendor_ref_no": name
        }, indent=2, default=str)
        
        sap_log.save(ignore_permissions=True)
        print(f"📝 SAP Log created with name: {sap_log.name}")
        
    except Exception as log_err:
        log_error_msg = f"Failed to create SAP log: {str(log_err)}"
        frappe.log_error(log_error_msg)
        print(f"❌ Log creation error: {log_error_msg}")

    # Create error log entry for failed transactions
    if transaction_status != "Success":
        try:
            error_log = frappe.new_doc("Error Log")
            error_log.method = "send_detail"
            error_log.error = f"SAP Integration Error - {transaction_status}: {error_details}"
            error_log.save(ignore_permissions=True)
            print(f"📝 Error Log created with name: {error_log.name}")
        except Exception as err_log_err:
            print(f"❌ Failed to create Error Log: {str(err_log_err)}")

    # Update vendor master with company vendor code if successful
    if vendor_code:
        try:
            update_vendor_master(name, company_name, sap_code, vendor_code, gst, state)
            print(f"✅ Vendor master updated successfully")
        except Exception as update_err:
            update_error_msg = f"Failed to update vendor master: {str(update_err)}"
            frappe.log_error(update_error_msg)
            print(f"❌ Vendor master update error: {update_error_msg}")
    
    frappe.db.commit()
    
    # Return appropriate response
    if response and response.status_code == 201:
        try:
            return response.json()
        except JSONDecodeError:
            return {
                "success": True, 
                "vendor_code": vendor_code, 
                "message": "Vendor created but response parsing failed",
                "transaction_status": transaction_status
            }
    else:
        return {
            "error": f"Failed to create vendor in SAP. Status: {response.status_code if response else 'No response'}",
            "transaction_status": transaction_status,
            "error_details": error_details
        }


def update_vendor_master(name, company_name, sap_code, vendor_code, gst, state):
    """Update vendor master with company vendor code"""
    ref_vm = frappe.get_doc("Vendor Master", name)
    
    cvc_name = frappe.db.exists("Company Vendor Code", {
        "sap_client_code": sap_code, 
        "vendor_ref_no": ref_vm.name
    })
    
    if cvc_name:
        cvc = frappe.get_doc("Company Vendor Code", cvc_name)
    else:
        cvc = frappe.new_doc("Company Vendor Code")
        cvc.vendor_ref_no = ref_vm.name
        cvc.company_name = company_name
        cvc.sap_client_code = sap_code

    # Update or add vendor code
    found = False
    for vc in cvc.vendor_code:
        if vc.gst_no == gst and vc.state == state:
            vc.vendor_code = vendor_code
            found = True
            break

    if not found:
        cvc.append("vendor_code", {
            "vendor_code": vendor_code,
            "gst_no": gst,
            "state": state
        })

    cvc.save(ignore_permissions=True)
    ref_vm.db_update()

# data = {
#     "ZZBENF_NAME": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_name"),
#     "ZZBEN_BANK_NM": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_name"),
#     "ZZBEN_ACCT_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_account_no"),
#     "ZZBENF_IBAN": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_iban_no"),
#     "ZZBENF_BANKADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_address"),
#     "ZZBENF_SHFTADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_swift_code"),
#     "ZZBENF_ACH_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_ach_no"),
#     "ZZBENF_ABA_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_aba_no"),
#     "ZZBENF_ROUTING": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_routing_no"),

#     "ZZINTR_ACCT_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_account_no"),
#     "ZZINTR_IBAN": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_iban_no"),
#     "ZZINTR_BANK_NM": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_name"),
#     "ZZINTR_BANKADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_address"),
#     "ZZINTR_SHFTADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_swift_code"),
#     "ZZINTR_ACH_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_ach_no"),
#     "ZZINTR_ABA_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_aba_no"),
#     "ZZINTR_ROUTING": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_routing_no"),
# }
