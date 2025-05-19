import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth


# @frappe.whitelist(allow_guest=True)
# #def sap_fetch_token(data, method):
# def sap_tokens(name):
#     url = f"http://10.10.103.133:8000/sap/opu/odata/sap/ZMM_VENDOR_SRV/VENDORSet?sap-client={sap_code}"
#     print("******************* First URL *************", url)
#     headers = {
#         'X-CSRF-TOKEN': 'Fetch',
#         'Authorization': 'Basic V0YtQkFUQ0g6TUB3YiMkJTIwMjQ=',
#         'Content-Type': 'application/json'
#         }
#     auth = HTTPBasicAuth('WF-BATCH ', 'M@wb#$%2024')
#     response = requests.get(url, headers=headers, auth=auth)

#     if response.status_code == 200:
#         print("****** GET CSRF TOKEN *********")
#         csrf_token = response.headers.get('x-csrf-token')
#         key1 = response.cookies.get(f'SAP_SESSIONID_BHD_{sap_code}')
#         key2 = response.cookies.get('sap-usercontext')
        
#         # Sending details to SAP
#         send_detail(csrf_token, data, key1, key2, name, sap_code)
#         print("*********** KEY1 ***********", key1)
#         print("*********** KEY2 ***********", key2)
#         print("$$$$$$$$$$$ CSRF TOKEN $$$$$$$$$$$$$$$$$$",csrf_token)
#         print("*********** JSON DATA ************", data)
#         print(response.headers.get('x-csrf-token'))
#         return data
@frappe.whitelist(allow_guest=True)
def erp_to_sap_vendor_data(onb_ref):
    onb = frappe.get_doc("Vendor Onboarding", onb_ref)
    onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
    onb_pmd = frappe.get_doc("Vendor Onboarding Payment Details", onb.payment_detail)
    # onb_doc = frappe.get_doc("Legal Documents", onb.document_details)
    # onb_cer = frappe.get_doc("Vendor Onboarding Certificates", onb.certificate_details)
    # onb_mnd = frappe.get_doc("Vendor Onboarding Manufacturing Details", onb.manufacturing_details)
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
        com_vcd = frappe.get_doc("Company Master", vcd.company_name)
        com_code = com_vcd.company_code
        sap_client_code = com_vcd.sap_client_code




        data =  {
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
            "Country": vcd.country,
            "J1kftind": "",
            "Region": vcd.state,
            "TelNumber": "",
            "MobNumber": onb_vm.mobile_number,
            "SmtpAddr": onb_vm.office_email_primary,
            "SmtpAddr1": onb_vm.office_email_secondary,
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
            "J1ivtyp": vendor_type_names[0],
            "J1ipanno": vcd.company_pan_number,
            "J1ipanref": onb_vm.vendor_name,
            "Namev": onb_vm.first_name,
            "Name11": onb_vm.last_name,
            "Bankl": onb_bank.bank_code,
            "Bankn": onb_pmd.account_number,
            "Bkref": onb_bank.bank_name,
            "Banka": onb_bank.ifsc_code,
            # "koinh": name_of_account_holder,
            # "Xezer": "",
            # "ZZBENF_NAME" : benf_name,
            # "ZZBEN_BANK_NM" : benf_bank_name,
            # "ZZBEN_ACCT_NO" : benf_account_no,
            # "ZZBENF_IBAN" : benf_iban_no,
            # "ZZBENF_BANKADDR" : benf_bank_add,
            # "ZZBENF_SHFTADDR" : benf_swift_code,
            # "ZZBENF_ACH_NO" : benf_ach_no,
            # "ZZBENF_ABA_NO" : benf_aba_no,
            # "ZZBENF_ROUTING" : benf_routing_no,
            # "ZZINTR_ACCT_NO" : intr_account_no,
            # "ZZINTR_IBAN" : intr_iban_no,
            # "ZZINTR_BANK_NM" : intr_bank_name,
            # "ZZINTR_BANKADDR" : intr_bank_add,
            # "ZZINTR_SHFTADDR" : intr_swift_code,
            # "ZZINTR_ACH_NO" : intr_ach_no,
            # "ZZINTR_ABA_NO" : intr_aba_no,
            # "ZZINTR_ROUTING" : intr_routing_no,
            "Refno": onb.ref_no,
            "Vedno": "",
            "Zmsg": ""
                }
        data_list.append(data)



        url = f"http://10.10.103.133:8000/sap/opu/odata/sap/ZMM_VENDOR_SRV/VENDORSet?sap-client={sap_client_code}"
        
        headers = {
            'X-CSRF-TOKEN': 'Fetch',
            'Authorization': 'Basic V0YtQkFUQ0g6TUB3YiMkJTIwMjQ=',
            'Content-Type': 'application/json'
            }
        auth = HTTPBasicAuth('WF-BATCH ', 'M@wb#$%2024')
        response = requests.get(url, headers=headers, auth=auth)
    
        if response.status_code == 200:
            
            csrf_token = response.headers.get('x-csrf-token')
            key1 = response.cookies.get(f'SAP_SESSIONID_BHD_{sap_client_code}')
            key2 = response.cookies.get('sap-usercontext')
            
            # Sending details to SAP
            send_detail(csrf_token, data, key1, key2, onb.ref_no, sap_client_code, onb_ref)
            
            return data
        else:
            frappe.log_error(f"Failed to fetch CSRF token from SAP: {response.status_code if response else 'No response'}")
            return None
   
#******************************* SAP PUSH  ************************************************************

@frappe.whitelist(allow_guest=True)
def send_detail(csrf_token, data, key1, key2, name, sap_code):

    url = f"http://10.10.103.133:8000/sap/opu/odata/sap/ZMM_VENDOR_SRV/VENDORSet?sap-client={sap_code}"
    key1 = key1
    key2 = key2
    name = name
    #pdb.set_trace()
    headers = {

        'X-CSRF-TOKEN': csrf_token,
        'Content-Type': 'application/json;charset=utf-8',
        'Accept': 'application/json',
        'Authorization': 'Basic V0YtQkFUQ0g6TUB3YiMkJTIwMjQ=',
        'Cookie': f"SAP_SESSIONID_BHD_{sap_code}={key1}; sap-usercontext={key2}"
    }
    auth = HTTPBasicAuth('WF-BATCH ', 'M@wb#$%2024')
    print("*************")
    
    try:
        response = requests.post(url, headers=headers, auth=auth ,json=data)
        print("****************** RESPONSE ************",response)
        print("********* STATUS CODE *****************", response.json(), response.status_code)
        #return response.json()
        vendor_sap_code = response.json()
        print("********** Here is the vendor_sap_code **********", vendor_sap_code)
        vendor_code = vendor_sap_code['d']['Vedno']
        

        frappe.db.sql(""" UPDATE `tabVendor Master` SET vendor_code=%s where name=%s """, (vendor_code, name))
        frappe.db.commit()
        
        return response.json()
    except ValueError:
        print("************************** Response is here *********************", response.json())
    
    
    if response.status_code == 201:  
        print("*****************************************")
        print("Vendor details posted successfully.")
        return response.json()

    else:
        print("******************************************")
        print("Error in POST request:", response.status_code)
        
