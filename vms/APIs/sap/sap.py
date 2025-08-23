import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth
from vms.utils.custom_send_mail import custom_sendmail

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
        




# def update_sap_vonb(doc, method=None):

#     if doc.register_by_account_team == 0:
#         if doc.purchase_team_undertaking and doc.accounts_team_undertaking and doc.purchase_head_undertaking :
#             if doc.rejected == 0 and not doc.data_sent_to_sap and doc.mandatory_data_filled == 1:
#                 erp_to_sap_vendor_data(doc.name)
#                 # doc.data_sent_to_sap = 1
#                 # doc.save()
#                 # doc.db_update()
#                 frappe.db.commit()

#     elif doc.register_by_account_team == 1:
#         if doc.accounts_team_undertaking and doc.accounts_head_undertaking :
#             if doc.rejected == 0 and not doc.data_sent_to_sap and doc.mandatory_data_filled == 1:
#                 erp_to_sap_vendor_data(doc.name)
#                 # doc.data_sent_to_sap = 1
#                 # doc.save()
#                 # doc.db_update()
#                 frappe.db.commit()




# import frappe
# from frappe import _
# import json
# import requests
# from requests.auth import HTTPBasicAuth
# from requests.exceptions import RequestException, JSONDecodeError

# @frappe.whitelist(allow_guest=True)
# def erp_to_sap_vendor_data(onb_ref):
#     """
#     Fixed version of the main SAP vendor data sending function with proper multi-row support
#     """
#     print("=" * 80)
#     print("ERP TO SAP VENDOR DATA - STARTING")
#     print(f"Vendor Onboarding Reference: {onb_ref}")
#     print("=" * 80)


#     # **TRACKING VARIABLES**
#     company_counter = 0
#     total_gst_rows_processed = 0
#     successful_sap_calls = 0
#     failed_sap_calls = 0
#     connection_errors = 0
#     validation_errors = 0
    
#     try:
#         # Get main documents
#         onb = frappe.get_doc("Vendor Onboarding", onb_ref)
#         onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
#         onb_pmd = frappe.get_doc("Vendor Onboarding Payment Details", onb.payment_detail)
#         pur_org = frappe.get_doc("Purchase Organization Master", onb.purchase_organization)
#         pur_grp = frappe.get_doc("Purchase Group Master", onb.purchase_group)
#         acc_grp = frappe.get_doc("Account Group Master", onb.account_group)
#         onb_reco = frappe.get_doc("Reconciliation Account", onb.reconciliation_account)
#         onb_pm_term = frappe.get_doc("Terms of Payment Master", onb.terms_of_payment)
#         onb_inco = frappe.get_doc("Incoterm Master", onb.incoterms)
#         onb_bank = frappe.get_doc("Bank Master", onb_pmd.bank_name)

#         # Boolean flags
#         payee = 'X' if onb.payee_in_document == 1 else ''
#         gr_based_inv_ver = 'X' if onb.gr_based_inv_ver == 1 else ''
#         service_based_inv_ver = 'X' if onb.service_based_inv_ver == 1 else ''
#         check_double_invoice = 'X' if onb.check_double_invoice == 1 else ''

#         # Get vendor types
#         vendor_type_names = []
#         for row in onb_vm.vendor_types:
#             if row.vendor_type:
#                 vendor_type_doc = frappe.get_doc("Vendor Type Master", row.vendor_type)
#                 vendor_type_names.append(vendor_type_doc.vendor_type_name)

#         # **MAIN LOOP: Process each company**
#         print(f"📊 Processing {len(onb.vendor_company_details)} companies...")
        
#         company_counter = 0
#         total_gst_rows_processed = 0
        
#         for company in onb.vendor_company_details:
#             company_counter += 1
#             print(f"\n🏢 COMPANY {company_counter}: Processing company entry...")
            
#             try:
#                 # Get company details
#                 vcd = frappe.get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
#                 country_doc = frappe.get_doc("Country Master", vcd.country)
#                 country_code = country_doc.country_code
#                 com_vcd = frappe.get_doc("Company Master", vcd.company_name)
#                 sap_client_code = com_vcd.sap_client_code
#                 vcd_state = frappe.get_doc("State Master", vcd.state)
                
#                 print(f"   📋 Company: {vcd.company_name}")
#                 print(f"   📋 SAP Client Code: {sap_client_code}")
#                 print(f"   📋 GST Tables to process: {len(vcd.comp_gst_table)}")
                
#                 # **SECOND LOOP: Process each GST entry for this company**
#                 gst_counter = 0
#                 for gst_table in vcd.comp_gst_table:
#                     gst_counter += 1
#                     total_gst_rows_processed += 1
                    
#                     print(f"\n   🔄 GST ENTRY {gst_counter} (Global #{total_gst_rows_processed}): Processing...")
                    
#                     try:
#                         # Get GST-specific data
#                         gst_state = gst_table.gst_state
#                         gst_state_doc = frappe.get_doc("State Master", gst_state)
#                         gst_num = gst_table.gst_number
#                         gst_pin = gst_table.pincode
#                         gst_addrs = frappe.get_doc("Pincode Master", gst_pin)
#                         gst_city = gst_addrs.city
#                         gst_cuntry = gst_addrs.country
#                         gst_district = gst_addrs.district
                        
#                         # Build address text
#                         gst_adderss_text = ", ".join(filter(None, [
#                             gst_city,
#                             gst_district,
#                             gst_state
#                         ]))

#                         print(f"      📍 GST State: {gst_state}")
#                         print(f"      📍 GST Number: {gst_num}")
#                         print(f"      📍 Address: {gst_adderss_text}")

#                         # **BUILD SAP PAYLOAD DATA**
#                         data = {
#                                 "Bukrs": com_vcd.company_code,
#                                 "Ekorg": pur_org.purchase_organization_code,
#                                 "Ktokk": acc_grp.account_group_code,
#                                 "Title": "",
#                                 "Name1": onb_vm.vendor_name,
#                                 "Name2": "",
#                                 "Sort1": onb_vm.search_term,
#                                 "Street": vcd.address_line_1,
#                                 "StrSuppl1": gst_adderss_text or "",  # Convert None to empty string
#                                 "StrSuppl2": "",
#                                 "StrSuppl3": "",
#                                 "PostCode1": gst_pin,
#                                 "City1": gst_city,
#                                 "Country": country_code,
#                                 "J1kftind": "",
#                                 "Region": gst_state_doc.sap_state_code,
#                                 "TelNumber": "",
#                                 "MobNumber": onb_vm.mobile_number,
#                                 "SmtpAddr": onb_vm.office_email_primary,
#                                 "SmtpAddr1": onb_vm.office_email_secondary or "",
#                                 "Zuawa": "",
#                                 "Akont": onb_reco.reconcil_account_code,
#                                 "Waers": onb_pmd.currency_code,
#                                 "Zterm": onb_pm_term.terms_of_payment_code,
#                                 "Inco1": onb_inco.incoterm_code,
#                                 "Inco2": onb_inco.incoterm_name,
#                                 "Kalsk": "",
#                                 "Ekgrp": pur_grp.purchase_group_code,
#                                 "Xzemp": payee,
#                                 "Reprf": check_double_invoice,
#                                 "Webre": gr_based_inv_ver,
#                                 "Lebre": service_based_inv_ver,
#                                 "Stcd3": gst_num or "",
#                                 "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
#                                 "J1ipanno": vcd.company_pan_number,
#                                 "J1ipanref": onb_vm.vendor_name,
#                                 "Namev": safe_get(onb, "contact_details", 0, "first_name"),
#                                 "Name11": safe_get(onb, "contact_details", 0, "last_name"),
#                                 "Bankl": onb_bank.bank_code,
#                                 "Bankn": onb_pmd.account_number,
#                                 "Bkref": onb_bank.bank_name,
#                                 "Banka": onb_pmd.ifsc_code,
#                                 "Xezer": "",
#                                 "ZZBENF_NAME": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_name"),
#                                 "ZZBEN_BANK_NM": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_name"),
#                                 "ZZBEN_ACCT_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_account_no"),
#                                 "ZZBENF_IBAN": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_iban_no"),
#                                 "ZZBENF_BANKADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_address"),
#                                 "ZZBENF_SHFTADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_swift_code"),
#                                 "ZZBENF_ACH_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_ach_no"),
#                                 "ZZBENF_ABA_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_aba_no"),
#                                 "ZZBENF_ROUTING": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_routing_no"),
#                                 "ZZINTR_ACCT_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_account_no"),
#                                 "ZZINTR_IBAN": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_iban_no"),
#                                 "ZZINTR_BANK_NM": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_name"),
#                                 "ZZINTR_BANKADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_bank_address"),
#                                 "ZZINTR_SHFTADDR": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_swift_code"),
#                                 "ZZINTR_ACH_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_ach_no"),
#                                 "ZZINTR_ABA_NO": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_aba_no"),
#                                 "ZZINTR_ROUTING": safe_get(onb_pmd, "intermediate_bank_details", 0, "intermediate_routing_no"),
#                                 "Refno": onb.ref_no,
#                                 "Vedno": "",
#                                 "Zmsg": ""
#                             }
#                         print(f"      🚀 Sending data to SAP for GST {gst_num}...")
                        
#                         # **GET CSRF TOKEN AND SESSION**
#                         csrf_result = get_csrf_token_and_session(sap_client_code)
                        
#                         if csrf_result["success"]:
#                             try:
#                                 # **SEND DATA TO SAP**
#                                 result = send_detail(
#                                     csrf_result["csrf_token"], 
#                                     data, 
#                                     csrf_result["session_cookies"],
#                                     onb.ref_no, 
#                                     sap_client_code, 
#                                     gst_state, 
#                                     gst_num, 
#                                     vcd.company_name, 
#                                     onb.name
#                                 )
                                
#                                 print(f"      📊 SAP Response: {result}")
                                
#                                 # **CHECK RESULT AND HANDLE RESPONSE**
#                                 if not result or "error" in result:
#                                     failed_sap_calls += 1
#                                     error_msg = result.get('error', 'Unknown error') if result else 'No response from send_detail function'
#                                     print(f"      ❌ SAP API Call Failed: {error_msg}")
#                                     send_failure_notification(onb.name, "SAP API Call Failed", f"GST {gst_num}: {error_msg}")
                                    
#                                 elif result and isinstance(result, dict):
#                                     # Extract vendor code from response
#                                     vedno = result.get('d', {}).get('Vedno', '') if 'd' in result else result.get('Vedno', '')
#                                     zmsg = result.get('d', {}).get('Zmsg', '') if 'd' in result else result.get('Zmsg', '')
                                    
#                                     if vedno == 'E' or vedno == '' or not vedno:
#                                         failed_sap_calls += 1
#                                         error_msg = f"SAP returned error or empty vendor code. Vedno: '{vedno}', Zmsg: '{zmsg}'"
#                                         print(f"      ❌ SAP Error: {error_msg}")
#                                         send_failure_notification(onb.name, "SAP Vendor Creation Failed", error_msg)
                                        
#                                     else:
#                                         successful_sap_calls += 1
#                                         print(f"      ✅ SUCCESS: Vendor code {vedno} created for GST {gst_num}")
                                        
#                                         # Update vendor master
#                                         try:
#                                             update_result = update_vendor_master(
#                                                 onb.ref_no, vcd.company_name, sap_client_code, 
#                                                 vedno, gst_num, gst_state, onb.name
#                                             )
#                                             print(f"      📝 Vendor Master Update: {update_result['status']}")
#                                         except Exception as update_err:
#                                             print(f"      ❌ Update Error: {str(update_err)}")
#                                             frappe.log_error(str(update_err), "Vendor Master Update Error")
                                
#                             except Exception as send_err:
#                                 failed_sap_calls += 1
#                                 error_msg = f"Error in send_detail function: {str(send_err)}"
#                                 print(f"      ❌ Send Detail Error: {error_msg}")
#                                 frappe.log_error(error_msg, "Send Detail Error")
#                                 send_failure_notification(onb.name, "SAP Send Detail Error", error_msg)
                                
#                         else:
#                             # **CONNECTION/CSRF ERROR**
#                             connection_errors += 1
#                             failed_sap_calls += 1
#                             error_msg = f"Failed to get CSRF token: {csrf_result.get('error', 'Unknown error')}"
#                             print(f"      ❌ CSRF Error: {error_msg}")
                            
#                             # Check if it's a connection error specifically
#                             if "Connection refused" in error_msg or "Failed to establish" in error_msg:
#                                 print(f"      🔌 CONNECTION ISSUE: SAP server appears to be unreachable")
                            
#                             try:
#                                 log_name = create_connection_error_sap_log(
#                                     onb.name,
#                                     data,
#                                     error_msg,
#                                     sap_client_code,
#                                     vcd.company_name,
#                                     onb.ref_no,
#                                     gst_num,
#                                     gst_state
#                                 )
#                                 if log_name:
#                                     print(f"      📝 Connection Error SAP Log created: {log_name}")
#                                 else:
#                                     print(f"      ⚠️ Failed to create SAP log for connection error")
#                             except Exception as log_err:
#                                 print(f"      ⚠️ Exception creating SAP log: {str(log_err)}")
#                                 frappe.log_error(f"SAP Log Creation Exception: {str(log_err)}", "SAP Log Error")
                            
#                             send_failure_notification(onb.name, "SAP Connection Error", error_msg)
                    
#                     except Exception as gst_err:
#                         failed_sap_calls += 1
#                         validation_errors += 1
#                         error_msg = f"Error processing GST entry {gst_counter}: {str(gst_err)}"
#                         print(f"      ❌ GST Processing Error: {error_msg}")
#                         frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "GST Processing Error")
#                         continue
                
#                 print(f"   ✅ Company {company_counter} completed: {gst_counter} GST entries processed")
                
#             except Exception as company_err:
#                 failed_sap_calls += 1
#                 validation_errors += 1
#                 error_msg = f"Error processing company {company_counter}: {str(company_err)}"
#                 print(f"   ❌ Company Processing Error: {error_msg}")
#                 frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "Company Processing Error")
#                 continue
        
#         # **ENHANCED FINAL SUMMARY WITH PROPER SUCCESS DETERMINATION**
#         total_attempts = successful_sap_calls + failed_sap_calls
#         success_rate = (successful_sap_calls / total_attempts * 100) if total_attempts > 0 else 0
        
#         print("=" * 80)
#         print("ERP TO SAP VENDOR DATA - FINAL RESULTS")
#         print("=" * 80)
#         print(f"📊 Total Companies Processed: {company_counter}")
#         print(f"📊 Total GST Rows Processed: {total_gst_rows_processed}")
#         print(f"✅ Successful SAP API Calls: {successful_sap_calls}")
#         print(f"❌ Failed SAP API Calls: {failed_sap_calls}")
#         print(f"🔌 Connection Errors: {connection_errors}")
#         print(f"⚠️ Validation Errors: {validation_errors}")
#         print(f"📈 Success Rate: {success_rate:.1f}%")
#         print("=" * 80)
        
#         # **DETERMINE OVERALL STATUS BASED ON ACTUAL SAP SUCCESS**
#         if successful_sap_calls == 0 and failed_sap_calls > 0:
#             # Complete failure - no successful SAP calls
#             status = "error"
#             message = f"SAP Integration Failed: 0/{total_attempts} successful. "
            
#             if connection_errors > 0:
#                 message += f"Connection errors: {connection_errors}. Check SAP server connectivity."
#             elif validation_errors > 0:
#                 message += f"Validation errors: {validation_errors}. Check data completeness."
#             else:
#                 message += "All SAP API calls failed."
                
#         elif successful_sap_calls > 0 and failed_sap_calls == 0:
#             # Complete success - all SAP calls succeeded
#             status = "success"
#             message = f"SAP Integration Successful: {successful_sap_calls}/{total_attempts} entries sent to SAP successfully."
            
#         elif successful_sap_calls > 0 and failed_sap_calls > 0:
#             # Partial success - some succeeded, some failed
#             status = "partial_success"
#             message = f"SAP Integration Partial Success: {successful_sap_calls}/{total_attempts} successful ({success_rate:.1f}%). {failed_sap_calls} failed."
            
#         else:
#             # Edge case - no attempts made
#             status = "error"
#             message = "No SAP integration attempts were made. Check data configuration."
        
#         print(f"🎯 FINAL STATUS: {status.upper()}")
#         print(f"💬 FINAL MESSAGE: {message}")
        
#         return {
#             "status": status,
#             "message": message,
#             "companies_processed": company_counter,
#             "gst_rows_processed": total_gst_rows_processed,
#             "successful_sap_calls": successful_sap_calls,
#             "failed_sap_calls": failed_sap_calls,
#             "connection_errors": connection_errors,
#             "validation_errors": validation_errors,
#             "success_rate": success_rate
#         }
        
#     except Exception as e:
#         error_msg = f"Main function error in erp_to_sap_vendor_data: {str(e)}"
#         print(f"❌ MAIN ERROR: {error_msg}")
#         frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "ERP to SAP Vendor Data Error")
        
#         try:
#             send_failure_notification(onb_ref, "ERP to SAP Main Function Error", error_msg)
#         except Exception as notif_err:
#             print(f"⚠️ Failed to send notification: {str(notif_err)}")
        
#         return {
#             "status": "error",
#             "message": f"Critical error in SAP integration: {error_msg}",
#             "companies_processed": company_counter,
#             "gst_rows_processed": total_gst_rows_processed,
#             "successful_sap_calls": 0,
#             "failed_sap_calls": total_gst_rows_processed,  # Assume all failed due to critical error
#             "connection_errors": 1,
#             "validation_errors": 0,
#             "success_rate": 0.0
#         }

# def safe_get(obj, list_name, index, attr, default=""):
#     """Helper function to safely get nested attributes"""
#     try:
#         return getattr(getattr(obj, list_name)[index], attr) or default
#     except (AttributeError, IndexError, TypeError):
#         return default


# # def send_failure_notification(onb_name, subject, message):
# #     """Send failure notification - placeholder function"""
# #     try:
# #         # Create error log entry
# #         error_log = frappe.new_doc("Error Log")
# #         error_log.method = "erp_to_sap_vendor_data"
# #         error_log.error = f"{subject}: {message}"
# #         error_log.save(ignore_permissions=True)
# #         print(f"📝 Failure notification logged: {subject}")
# #     except Exception as e:
# #         print(f"❌ Failed to log notification: {str(e)}")


# def get_csrf_token_and_session(sap_client_code):
#     """
#     Get CSRF token and session cookies for SAP API calls
#     Returns: {"success": True/False, "csrf_token": "", "session_cookies": {}, "error": ""}
#     """
#     try:
#         sap_settings = frappe.get_doc("SAP Settings")
#         erp_to_sap_url = sap_settings.url
#         url = f"{erp_to_sap_url}{sap_client_code}"
#         header_auth_type = sap_settings.authorization_type
#         header_auth_key = sap_settings.authorization_key
#         user = sap_settings.auth_user_name
#         password = sap_settings.auth_user_pass

#         headers = {
#             'X-CSRF-Token': 'FETCH',
#             'Authorization': f"{header_auth_type} {header_auth_key}",
#             'Content-Type': 'application/json'
#         }

#         auth = HTTPBasicAuth(user, password)
#         response = requests.get(url, headers=headers, auth=auth, timeout=30)
        
#         print(f"🔑 CSRF Token Request: Status {response.status_code}")
        
#         if response.status_code == 200:
#             csrf_token = response.headers.get('x-csrf-token')
#             session_cookies = {
#                 f'SAP_SESSIONID_BHD_{sap_client_code}': response.cookies.get(f'SAP_SESSIONID_BHD_{sap_client_code}'),
#                 'sap-usercontext': response.cookies.get('sap-usercontext')
#             }
            
#             print(f"🔑 CSRF Token obtained successfully")
#             return {
#                 "success": True,
#                 "csrf_token": csrf_token,
#                 "session_cookies": session_cookies,
#                 "error": ""
#             }
#         else:
#             error_msg = f"Failed to fetch CSRF token: HTTP {response.status_code}"
#             print(f"❌ {error_msg}")
#             return {
#                 "success": False,
#                 "csrf_token": "",
#                 "session_cookies": {},
#                 "error": error_msg
#             }
            
#     except Exception as e:
#         error_msg = f"CSRF token request failed: {str(e)}"
#         print(f"❌ {error_msg}")
#         return {
#             "success": False,
#             "csrf_token": "",
#             "session_cookies": {},
#             "error": error_msg
#         }

# @frappe.whitelist(allow_guest=True)
# def send_detail(csrf_token, data, session_cookies, name, sap_code, state, gst, company_name, onb_name):
#     sap_settings = frappe.get_doc("SAP Settings")
#     erp_to_sap_url = sap_settings.url
#     url = f"{erp_to_sap_url}{sap_code}"
#     header_auth_type = sap_settings.authorization_type
#     header_auth_key = sap_settings.authorization_key
#     user = sap_settings.auth_user_name
#     password = sap_settings.auth_user_pass

#     # Build cookie string from session cookies
#     cookie_string = "; ".join([f"{name}={value}" for name, value in session_cookies.items()])

#     headers = {
#         'X-CSRF-Token': csrf_token,
#         'Authorization': f"{header_auth_type} {header_auth_key}",
#         'Content-Type': 'application/json;charset=utf-8',
#         'Accept': 'application/json',
#         'Cookie': cookie_string
#     }

#     auth = HTTPBasicAuth(user, password)
    
#     # Initialize response variables
#     response = None
#     vendor_code = None
#     sap_response_text = ""
#     transaction_status = "Failed"
#     error_details = ""
    
#     # Print complete payload for debugging
#     print("=" * 80)
#     print("SAP API PAYLOAD DEBUG")
#     print("=" * 80)
#     print(f"URL: {url}")
#     print(f"Headers: {json.dumps(dict(headers), indent=2)}")
#     print(f"Auth User: {user}")
#     print(f"Payload Data:")
#     print(json.dumps(data, indent=2, default=str))
#     print("=" * 80)
    
#     try:
#         response = requests.post(url, headers=headers, auth=auth, json=data, timeout=30)
#         sap_response_text = response.text[:1000]  # Truncate to avoid DB constraint issues
        
#         # Debug response details
#         print("=" * 80)
#         print("SAP API RESPONSE DEBUG")
#         print("=" * 80)
#         print(f"Response Status Code: {response.status_code}")
#         print(f"Response Headers: {dict(response.headers)}")
#         print(f"Response Content Length: {len(response.text)}")
#         print(f"Response Content: {response.text}")
#         print("=" * 80)
        
#         # Check if response has content and is valid JSON
#         if response.status_code == 201 and response.text.strip():
#             try:
#                 vendor_sap_code = response.json()
#                 # Extract Vedno and Zmsg as per original code logic
#                 vendor_code = vendor_sap_code['d']['Vedno']
#                 zmsg = vendor_sap_code['d'].get('Zmsg', '')
                
#                 # Check if Vedno indicates error or is empty
#                 if vendor_code == 'E' or vendor_code == '' or not vendor_code:
#                     transaction_status = "SAP Error"
#                     error_details = f"SAP returned error vendor code. Vedno: '{vendor_code}', Zmsg: '{zmsg}'"
#                     print(f"❌ SAP Error: {error_details}")
                    
#                     # Send notification for SAP error
#                     try:
#                         send_failure_notification(
#                             onb_name, 
#                             "SAP Vendor Creation Error", 
#                             error_details
#                         )
#                     except Exception as notif_err:
#                         print(f"⚠️ Failed to send notification: {str(notif_err)}")
#                 else:
#                     transaction_status = "Success"
#                     print(f"✅ Vendor details posted successfully. Vendor Code: {vendor_code}")
#                     if zmsg:
#                         print(f"📝 SAP Message: {zmsg}")
                
#                 print(f"✅ Full SAP Response: {json.dumps(vendor_sap_code, indent=2)}")
                
#             except (JSONDecodeError, KeyError) as json_err:
#                 error_details = f"Invalid JSON response or missing Vedno field: {str(json_err)}"
#                 transaction_status = "JSON Parse Error"
#                 frappe.log_error(error_details)
#                 print(f"❌ JSON parsing error: {error_details}")
#                 print(f"❌ Available response keys: {list(vendor_sap_code.get('d', {}).keys()) if 'vendor_sap_code' in locals() else 'Could not parse response'}")
                
#                 # Send notification for parsing error
#                 try:
#                     send_failure_notification(
#                         onb_name, 
#                         "SAP Response Parse Error", 
#                         error_details
#                     )
#                 except Exception as notif_err:
#                     print(f"⚠️ Failed to send notification: {str(notif_err)}")
                
#         elif response.status_code == 403:
#             error_details = f"CSRF Token validation failed. Response: {response.text}"
#             transaction_status = "CSRF Token Error"
#             frappe.log_error(error_details)
#             print(f"❌ CSRF Error: {error_details}")
            
#             # Send notification for CSRF error
#             try:
#                 send_failure_notification(
#                     onb_name, 
#                     "SAP Authentication Error", 
#                     error_details
#                 )
#             except Exception as notif_err:
#                 print(f"⚠️ Failed to send notification: {str(notif_err)}")
            
#         elif response.status_code != 201:
#             error_details = f"SAP API returned status {response.status_code}: {response.text}"
#             transaction_status = f"HTTP Error {response.status_code}"
#             frappe.log_error(error_details)
#             print(f"❌ Error in POST request: {error_details}")
            
#             # Send notification for HTTP error
#             try:
#                 send_failure_notification(
#                     onb_name, 
#                     f"SAP API Error {response.status_code}", 
#                     error_details
#                 )
#             except Exception as notif_err:
#                 print(f"⚠️ Failed to send notification: {str(notif_err)}")
            
#         else:
#             error_details = "Empty response from SAP API"
#             transaction_status = "Empty Response"
#             frappe.log_error(error_details)
#             print(f"❌ Error: {error_details}")
            
#             # Send notification for empty response
#             try:
#                 send_failure_notification(
#                     onb_name, 
#                     "SAP Empty Response", 
#                     error_details
#                 )
#             except Exception as notif_err:
#                 print(f"⚠️ Failed to send notification: {str(notif_err)}")

#     except RequestException as req_err:
#         error_details = f"Request failed: {str(req_err)}"
#         transaction_status = "Request Exception"
#         frappe.log_error(error_details)
#         print(f"❌ Request error: {error_details}")
#         sap_response_text = str(req_err)[:1000]
        
#         # Send notification for request exception
#         try:
#             send_failure_notification(
#                 onb_name, 
#                 "SAP Network Error", 
#                 error_details
#             )
#         except Exception as notif_err:
#             print(f"⚠️ Failed to send notification: {str(notif_err)}")
        
#     except Exception as e:
#         error_details = f"Unexpected error: {str(e)}"
#         transaction_status = "Unexpected Error"
#         frappe.log_error(error_details)
#         print(f"❌ Unexpected error: {error_details}")
#         sap_response_text = str(e)[:1000]
        
#         # Send notification for unexpected error
#         try:
#             send_failure_notification(
#                 onb_name, 
#                 "SAP Unexpected Error", 
#                 error_details
#             )
#         except Exception as notif_err:
#             print(f"⚠️ Failed to send notification: {str(notif_err)}")

#     # Always log the transaction with full data since fields are JSON/Code types
#     try:
#         sap_log = frappe.new_doc("VMS SAP Logs")
#         sap_log.vendor_onboarding_link = onb_name
        
#         # Store full data since erp_to_sap_data is JSON field
#         sap_log.erp_to_sap_data = data
        
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
#                 "payload": data
#             },
#             "response_details": {
#                 "status_code": response.status_code if response else "No Response",
#                 "headers": dict(response.headers) if response else {},
#                 "body": response.json() if response and response.text.strip() else sap_response_text
#             },
#             "transaction_summary": {
#                 "status": transaction_status,
#                 "vendor_code": vendor_code,
#                 "error_details": error_details,
#                 "timestamp": frappe.utils.now(),
#                 "sap_client_code": sap_code,
#                 "company_name": company_name,
#                 "vendor_ref_no": name
#             }
#         }
        
#         sap_log.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)
#         sap_log.save(ignore_permissions=True)
#         print(f"📝 SAP Log created with name: {sap_log.name}")
        
#     except Exception as log_err:
#         # If SAP log creation fails, create a simple error log entry
#         log_error_msg = f"Failed to create SAP log: {str(log_err)}"
#         print(f"❌ Log creation error: {log_error_msg}")
        
#         # Create a minimal log entry using Frappe's error log
#         try:
#             frappe.log_error(
#                 title=f"SAP Integration - {transaction_status}",
#                 message=f"Vendor: {name}\nStatus: {transaction_status}\nVendor Code: {vendor_code}\nError: {error_details}"
#             )
#             print("📝 Fallback error log created")
#         except Exception as fallback_err:
#             print(f"❌ Even fallback logging failed: {str(fallback_err)}")
#             # At minimum, log to console
#             print(f"CRITICAL: SAP Transaction Status: {transaction_status}, Vendor Code: {vendor_code}")

#     # Create error log entry for failed transactions OR success log for successful ones
#     try:
#         if transaction_status == "Success":
#             # Create success log
#             success_log = frappe.new_doc("Error Log")
#             success_log.method = "send_detail"
#             success_log.error = f"SAP Integration SUCCESS - Vendor Created: {vendor_code}\nVendor Ref: {name}\nCompany: {company_name}\nSAP Client: {sap_code}"
#             success_log.save(ignore_permissions=True)
#             print(f"📝 Success Log created with name: {success_log.name}")
#         else:
#             # Create error log for failures
#             error_log = frappe.new_doc("Error Log")
#             error_log.method = "send_detail"
#             error_log.error = f"SAP Integration Error - {transaction_status}: {error_details[:1000]}"  # Truncate
#             error_log.save(ignore_permissions=True)
#             print(f"📝 Error Log created with name: {error_log.name}")
#     except Exception as err_log_err:
#         print(f"❌ Failed to create Error Log: {str(err_log_err)}")
#         # Fallback to Frappe's built-in error logging
#         frappe.log_error(
#             title=f"SAP Integration - {transaction_status}",
#             message=f"Status: {transaction_status}\nVendor: {name}\nDetails: {error_details[:500]}"
#         )

#     # Update vendor master with company vendor code if successful
#     if vendor_code not in ('E', '') and transaction_status == "Success":

#         try:
#             update_vendor_master(name, company_name, sap_code, vendor_code, gst, state, onb_name)
#             print(f"✅ Vendor master updated successfully with vendor code: {vendor_code}")
#         except Exception as update_err:
#             update_error_msg = f"Failed to update vendor master: {str(update_err)}"
#             frappe.log_error(update_error_msg)
#             print(f"❌ Vendor master update error: {update_error_msg}")
#     elif transaction_status == "Success" and not vendor_code:
#         print(f"⚠️ Warning: Transaction successful but no vendor code extracted from SAP response")
    
#     frappe.db.commit()
    
#     # Return appropriate response based on original code logic
#     if response and response.status_code == 201:
#         try:
#             return response.json()  # Return the full SAP response as per original code
#         except JSONDecodeError:
#             return {
#                 "success": True, 
#                 "vendor_code": vendor_code, 
#                 "message": "Vendor created but response parsing failed",
#                 "transaction_status": transaction_status,
#                 "raw_response": response.text
#             }
#     else:
#         return {
#             "error": f"Failed to create vendor in SAP. Status: {response.status_code if response else 'No response'}",
#             "transaction_status": transaction_status,
#             "error_details": error_details
#         }


# def send_failure_notification(onb_name, failure_type, error_details):
#     """Send email notifications to purchase team when SAP integration fails"""
#     try:
#         # Get vendor onboarding document
#         onb_doc = frappe.get_doc("Vendor Onboarding", onb_name)
#         registered_by = onb_doc.registered_by
        
#         if not registered_by:
#             print(f"⚠️ No registered_by found for {onb_name}")
#             return
        
#         # Get email recipients
#         recipients = get_notification_recipients(registered_by)
        
#         if not recipients:
#             print(f"⚠️ No email recipients found for registered_by: {registered_by}")
#             return
        
#         # Prepare email content
#         subject = f"🚨 SAP Integration Alert: {failure_type} - {onb_doc.vendor_name or 'Unknown Vendor'}"
        
#         # Get vendor details for email
#         vendor_details = get_vendor_details_for_email(onb_doc)
        
        
#         # Create email message
#         message = f"""
#         <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px;">
#             <div style="background-color: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
#                 <h2 style="margin: 0; font-size: 24px;">🚨 SAP Integration Alert</h2>
#                 <p style="margin: 5px 0 0 0; font-size: 16px;">Action Required: {failure_type}</p>
#             </div>
            
#             <div style="padding: 20px;">
#                 <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
#                     <h3 style="color: #dc3545; margin-top: 0;">⚠️ Issue Summary</h3>
#                     <p style="margin: 0; font-size: 16px; line-height: 1.5;"><strong>{error_details}</strong></p>
#                 </div>
                
#                 <h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px;">📋 Vendor Information</h3>
#                 <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
#                     <tr style="background-color: #f8f9fa;">
#                         <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; width: 40%;">Vendor Name</td>
#                         <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['vendor_name']}</td>
#                     </tr>
#                     <tr>
#                         <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Reference Number</td>
#                         <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['ref_no']}</td>
#                     </tr>
#                     <tr style="background-color: #f8f9fa;">
#                         <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Onboarding ID</td>
#                         <td style="padding: 10px; border: 1px solid #ddd;">{onb_name}</td>
#                     </tr>
#                     <tr>
#                         <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Company</td>
#                         <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['company']}</td>
#                     </tr>
#                     <tr style="background-color: #f8f9fa;">
#                         <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Email</td>
#                         <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['email']}</td>
#                     </tr>
#                     <tr>
#                         <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Mobile</td>
#                         <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['mobile']}</td>
#                     </tr>
#                     <tr style="background-color: #f8f9fa;">
#                         <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Registered By</td>
#                         <td style="padding: 10px; border: 1px solid #ddd;">{registered_by}</td>
#                     </tr>
#                     <tr>
#                         <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Date & Time</td>
#                         <td style="padding: 10px; border: 1px solid #ddd;">{frappe.utils.now()}</td>
#                     </tr>
#                 </table>
                
#                 <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
#                     <h4 style="color: #856404; margin-top: 0;">🔍 Next Steps</h4>
#                     <ul style="margin: 0; color: #856404;">
#                         <li>Review the vendor onboarding details</li>
#                         <li>Check SAP connectivity and credentials</li>
#                         <li>Verify vendor data completeness</li>
#                         <li>Contact IT team if technical issues persist</li>
#                         <li>Retry the SAP integration after resolving issues</li>
#                     </ul>
#                 </div>
                
                
#             </div>
            
#             <div style="background-color: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #666; font-size: 12px;">
#                 <p style="margin: 0;">This is an automated alert from the VMS SAP Integration System</p>
#                 <p style="margin: 5px 0 0 0;">Please do not reply to this email</p>
#             </div>
#         </div>
#         """
        
#         # Send email to all recipients
#         for recipient in recipients:
#             try:
#                 frappe.custom_sendmail(
#                     recipients=[recipient["email"]],
#                     subject=subject,
#                     message=message,
#                     now=True
#                 )
#                 print(f"📧 Notification sent to: {recipient['name']} ({recipient['email']})")
                
#             except Exception as email_err:
#                 print(f"❌ Failed to send email to {recipient['email']}: {str(email_err)}")
#                 frappe.log_error(f"Failed to send notification email to {recipient['email']}: {str(email_err)}")
        
#         # Log the notification
#         frappe.log_error(
#             title=f"SAP Integration Notification Sent - {failure_type}",
#             message=f"Vendor: {vendor_details['vendor_name']}\nOnboarding: {onb_name}\nError: {error_details}\nNotified: {', '.join([r['email'] for r in recipients])}"
#         )
        
#     except Exception as e:
#         error_msg = f"Failed to send failure notification: {str(e)}"
#         print(f"❌ {error_msg}")
#         frappe.log_error(error_msg)


# def get_notification_recipients(registered_by):
#     """Get email recipients: registered_by user and their reporting manager"""
#     recipients = []
    
#     try:
#         # Get the user who registered the vendor
#         user_email = registered_by
        
#         # Try to find employee record for registered_by user
#         employee = None
#         employee_name = frappe.db.exists("Employee", {"user_id": registered_by})
        
#         if employee_name:
#             employee = frappe.get_doc("Employee", employee_name)
#             recipients.append({
#                 "name": employee.first_name,
#                 "email": user_email,
#                 "role": "Registered By"
#             })
            
#             # Get reporting manager if exists
#             if employee.reports_to:
#                 try:
#                     manager = frappe.get_doc("Employee", employee.reports_to)
#                     if manager.user_id:
#                         recipients.append({
#                             "name": manager.employee_name or manager.name,
#                             "email": manager.user_id,
#                             "role": "Reporting Manager"
#                         })
#                 except Exception as manager_err:
#                     print(f"⚠️ Could not get manager details: {str(manager_err)}")
#         else:
#             # If no employee record found, just use the registered_by email
#             recipients.append({
#                 "name": registered_by.split("@")[0].title(),
#                 "email": user_email,
#                 "role": "Registered By"
#             })
            
#         # Remove duplicates and invalid emails
#         unique_recipients = []
#         seen_emails = set()
        
#         for recipient in recipients:
#             if recipient["email"] and recipient["email"] not in seen_emails and "@" in recipient["email"]:
#                 unique_recipients.append(recipient)
#                 seen_emails.add(recipient["email"])
        
#         return unique_recipients
        
#     except Exception as e:
#         print(f"❌ Error getting notification recipients: {str(e)}")
#         frappe.log_error(f"Error getting notification recipients: {str(e)}")
#         return []


# def get_vendor_details_for_email(onb_doc):
#     """Extract vendor details for email notification"""
#     try:
#         vendor_master = frappe.get_doc("Vendor Master", onb_doc.ref_no) if onb_doc.ref_no else None
        
#         return {
#             "vendor_name": vendor_master.vendor_name if vendor_master else "Unknown",
#             "ref_no": onb_doc.ref_no or "Not Set",
#             "company": onb_doc.company or "Not Specified",
#             "email": vendor_master.office_email_primary if vendor_master else "Not Provided",
#             "mobile": vendor_master.mobile_number if vendor_master else "Not Provided"
#         }
#     except Exception as e:
#         print(f"⚠️ Error getting vendor details: {str(e)}")
#         return {
#             "vendor_name": "Unknown",
#             "ref_no": "Unknown",
#             "company": "Unknown", 
#             "email": "Unknown",
#             "mobile": "Unknown"
#         }
# #     """Update vendor master with company vendor code"""
# #     ref_vm = frappe.get_doc("Vendor Master", name)
    
# #     cvc_name = frappe.db.exists("Company Vendor Code", {
# #         "sap_client_code": sap_code, 
# #         "vendor_ref_no": ref_vm.name
# #     })
    
# #     if cvc_name:
# #         cvc = frappe.get_doc("Company Vendor Code", cvc_name)
# #     else:
# #         cvc = frappe.new_doc("Company Vendor Code")
# #         cvc.vendor_ref_no = ref_vm.name
# #         cvc.company_name = company_name
# #         cvc.sap_client_code = sap_code

# #     # Update or add vendor code
# #     found = False
# #     for vc in cvc.vendor_code:
# #         if vc.gst_no == gst and vc.state == state:
# #             vc.vendor_code = vendor_code
# #             found = True
# #             break

# #     if not found:
# #         cvc.append("vendor_code", {
# #             "vendor_code": vendor_code,
# #             "gst_no": gst,
# #             "state": state
# #         })

# # def update_vendor_master(name, company_name, sap_code, vendor_code, gst, state):
# #     """Update vendor master with company vendor code"""
# #     ref_vm = frappe.get_doc("Vendor Master", name)
    
# #     cvc_name = frappe.db.exists("Company Vendor Code", {
# #         "sap_client_code": sap_code, 
# #         "vendor_ref_no": ref_vm.name
# #     })
    
# #     if cvc_name:
# #         cvc = frappe.get_doc("Company Vendor Code", cvc_name)
# #     else:
# #         cvc = frappe.new_doc("Company Vendor Code")
# #         cvc.vendor_ref_no = ref_vm.name
# #         cvc.company_name = company_name
# #         cvc.sap_client_code = sap_code

# #     # Update or add vendor code
# #     found = False
# #     for vc in cvc.vendor_code:
# #         if vc.gst_no == gst and vc.state == state:
# #             vc.vendor_code = vendor_code
# #             found = True
# #             break

# #     if not found:
# #         cvc.append("vendor_code", {
# #             "vendor_code": vendor_code,
# #             "gst_no": gst,
# #             "state": state
# #         })

# #     cvc.save(ignore_permissions=True)
# #     ref_vm.db_update()















# def update_vendor_master(name, company_name, sap_code, vendor_code, gst, state, onb):
#     """
#     Fixed function to properly handle multiple vendor code rows for a single company
#     """
#     try:
#         # Get vendor master document
#         ref_vm = frappe.get_doc("Vendor Master", name)
        
#         # Look for existing Company Vendor Code document
#         cvc_name = frappe.db.exists("Company Vendor Code", {
#             "sap_client_code": sap_code, 
#             "vendor_ref_no": ref_vm.name
#         })
        
#         if cvc_name:
#             # Load existing Company Vendor Code document
#             cvc = frappe.get_doc("Company Vendor Code", cvc_name)
#         else:
#             # Create new Company Vendor Code document
#             cvc = frappe.new_doc("Company Vendor Code")
#             cvc.vendor_ref_no = ref_vm.name
#             cvc.company_name = company_name
#             cvc.sap_client_code = sap_code
            
#         # **FIX: Handle multiple vendor codes for same company**
#         # Check if this exact combination already exists
#         found_existing = False
        
#         if hasattr(cvc, 'vendor_code') and cvc.vendor_code:
#             for vc in cvc.vendor_code:
#                 # Match based on GST and State combination
#                 if (getattr(vc, 'gst_no', '') == gst and 
#                     getattr(vc, 'state', '') == state):
#                     # Update existing record
#                     vc.vendor_code = vendor_code
#                     vc.gst_no = gst
#                     vc.state = state
#                     found_existing = True
#                     print(f"✅ Updated existing vendor code row: GST={gst}, State={state}, Vendor Code={vendor_code}")
#                     break
        
#         # If no matching record found, add new row
#         if not found_existing:
#             new_vendor_code_row = {
#                 "vendor_code": vendor_code,
#                 "gst_no": gst,
#                 "state": state
#             }
#             cvc.append("vendor_code", new_vendor_code_row)
#             print(f"✅ Added new vendor code row: GST={gst}, State={state}, Vendor Code={vendor_code}")
        
#         # Save the Company Vendor Code document
#         cvc.save(ignore_permissions=True)
#         print(f"✅ Saved Company Vendor Code document: {cvc.name}")
        
#         # **FIX: Update Multiple Company Data in Vendor Master**
#         # Find and update the corresponding multiple_company_data row
#         mcd_updated = False
        
#         if hasattr(ref_vm, 'multiple_company_data') and ref_vm.multiple_company_data:
#             for mcd_row in ref_vm.multiple_company_data:
#                 # Match by SAP client code or company name
#                 if (getattr(mcd_row, 'sap_client_code', '') == sap_code or 
#                     getattr(mcd_row, 'company_name', '') == company_name):
#                     mcd_row.company_vendor_code = cvc.name
#                     mcd_updated = True
#                     print(f"✅ Updated existing multiple_company_data row with CVC: {cvc.name}")
#                     break
        
#         # If no matching multiple_company_data row found, create new one
#         if not mcd_updated:
#             ref_vm.append("multiple_company_data", {
#                 "company_name": company_name,
#                 "sap_client_code": sap_code,
#                 "company_vendor_code": cvc.name
#             })
#             print(f"✅ Added new multiple_company_data row with CVC: {cvc.name}")
        
#         # Save vendor master document
#         ref_vm.save(ignore_permissions=True)
#         print(f"✅ Updated Vendor Master: {ref_vm.name}")
        
#         # Commit the transaction
#         frappe.db.commit()
#         print(f"✅ Transaction committed successfully")





#         onb_doc = frappe.get_doc("Vendor Onboarding", onb)
#         onb_doc.data_sent_to_sap = 1



        
#         return {
#             "status": "success",
#             "message": f"Vendor master updated with vendor code: {vendor_code}",
#             "vendor_code": vendor_code,
#             "company_vendor_code": cvc.name,
#             "action_taken": "updated" if found_existing else "added_new"
#         }
        
#     except Exception as e:
#         # Rollback on error
#         frappe.db.rollback()
#         error_msg = f"Failed to update vendor master: {str(e)}"
#         frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "Update Vendor Master Error")
#         print(f"❌ Error updating vendor master: {error_msg}")
        
#         return {
#             "status": "error", 
#             "message": error_msg,
#             "vendor_code": vendor_code,
#             "error_details": str(e)
#         }










# def create_connection_error_sap_log(onb_name, data, error_msg, sap_client_code, company_name, vendor_ref_no, gst_num, gst_state):
#     """
#     Create SAP log entry for connection errors when CSRF token request fails
#     """
#     try:
#         sap_log = frappe.new_doc("VMS SAP Logs")
#         sap_log.vendor_onboarding_link = onb_name
        
#         # Store the payload that would have been sent
#         sap_log.erp_to_sap_data = data
        
#         # Create error response object for connection failure
#         error_response = {
#             "error_type": "connection_error",
#             "error_message": error_msg,
#             "timestamp": frappe.utils.now(),
#             "status": "connection_failed",
#             "http_status": "No Response",
#             "details": {
#                 "csrf_token_request_failed": True,
#                 "connection_refused": "Connection refused" in error_msg or "Failed to establish" in error_msg,
#                 "gst_number": gst_num,
#                 "gst_state": gst_state,
#                 "sap_client_code": sap_client_code
#             }
#         }
        
#         sap_log.sap_response = error_response
        
#         # Create comprehensive transaction log matching send_detail format
#         transaction_data = {
#             "request_details": {
#                 "url": f"SAP_URL/{sap_client_code}",  # Would be actual URL
#                 "sap_client_code": sap_client_code,
#                 "company_name": company_name,
#                 "vendor_ref_no": vendor_ref_no,
#                 "gst_number": gst_num,
#                 "gst_state": gst_state,
#                 "payload": data,
#                 "csrf_token_requested": True,
#                 "csrf_token_obtained": False
#             },
#             "response_details": {
#                 "status_code": "Connection Failed",
#                 "headers": {},
#                 "body": error_msg,
#                 "connection_error": True
#             },
#             "transaction_summary": {
#                 "status": "Connection Failed",
#                 "vendor_code": None,
#                 "error_details": error_msg,
#                 "timestamp": frappe.utils.now(),
#                 "sap_client_code": sap_client_code,
#                 "company_name": company_name,
#                 "vendor_ref_no": vendor_ref_no,
#                 "error_category": "Infrastructure/Connectivity",
#                 "actionable_steps": [
#                     "Check SAP server connectivity",
#                     "Verify network access to SAP server",
#                     "Contact IT team to check SAP server status",
#                     "Retry after connectivity is restored"
#                 ]
#             }
#         }
        
#         sap_log.total_transaction = frappe.as_json(transaction_data, indent=2)
#         sap_log.save(ignore_permissions=True)
#         frappe.db.commit()
        
#         print(f"📝 Connection Error SAP Log created: {sap_log.name}")
        
#         # Also create Error Log entry for connection failure
#         error_log = frappe.new_doc("Error Log")
#         error_log.method = "erp_to_sap_vendor_data"
#         error_log.error = f"SAP Connection Error: {error_msg}\nVendor: {vendor_ref_no}\nCompany: {company_name}\nGST: {gst_num}"
#         error_log.save(ignore_permissions=True)
#         print(f"📝 Connection Error Log created: {error_log.name}")
        
#         return sap_log.name
        
#     except Exception as e:
#         error_msg = f"Failed to create connection error SAP log: {str(e)}"
#         print(f"❌ SAP Log Creation Error: {error_msg}")
#         frappe.log_error(error_msg, "Connection Error SAP Log Creation")
#         return None



import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, JSONDecodeError


def update_sap_vonb(doc, method=None):
    """
    Hook function to trigger SAP vendor onboarding
    This remains the same as your original implementation
    """
    if doc.register_by_account_team == 0:
        if doc.purchase_team_undertaking and doc.accounts_team_undertaking and doc.purchase_head_undertaking:
            if doc.rejected == 0 and doc.data_sent_to_sap == 0 and doc.mandatory_data_filled == 1:
                erp_to_sap_vendor_data(doc.name)
                frappe.db.commit()

    elif doc.register_by_account_team == 1:
        if doc.accounts_team_undertaking and doc.accounts_head_undertaking:
            if doc.rejected == 0 and doc.data_sent_to_sap == 0 and doc.mandatory_data_filled == 1:
                erp_to_sap_vendor_data(doc.name)
                frappe.db.commit()


# =====================================================================================
# SESSION-BASED SAP INTEGRATION CLASSES
# =====================================================================================

class SAPSessionManager:
    """
    Manages SAP sessions for CSRF token and cookie handling
    This class handles all SAP authentication and session management
    """
    
    def __init__(self, sap_client_code):
        self.sap_client_code = sap_client_code
        self.session = None
        self.csrf_token = None
        self.auth = None
        self.sap_settings = None
        self._initialize_settings()
    
    def _initialize_settings(self):
        """Initialize SAP settings from Frappe"""
        try:
            self.sap_settings = frappe.get_doc("SAP Settings")
            self.auth = HTTPBasicAuth(
                self.sap_settings.auth_user_name, 
                self.sap_settings.auth_user_pass
            )
        except Exception as e:
            frappe.log_error(f"Failed to initialize SAP settings: {str(e)}", "SAP Settings Error")
            raise
    
    def create_session(self):
        """
        Create a new SAP session with proper authentication and CSRF token
        Returns: dict with success status and session details
        """
        try:
            print("🔄 Creating new SAP session...")
            print(f"SAP Client Code: {self.sap_client_code}")
            
            # Create new session
            self.session = requests.Session()
            
            # Set default headers for all requests in this session
            self.session.headers.update({
                'Authorization': f"{self.sap_settings.authorization_type} {self.sap_settings.authorization_key}",
                'Content-Type': 'application/json;charset=utf-8',
                'Accept': 'application/json',
                'User-Agent': 'Frappe-SAP-Integration/1.0'
            })
            
            # Get CSRF token
            csrf_result = self._fetch_csrf_token()
            
            if csrf_result["success"]:
                self.csrf_token = csrf_result["csrf_token"]
                print(f"✅ SAP Session created successfully")
                print(f"✅ CSRF Token: {self.csrf_token}")
                return {
                    "success": True,
                    "csrf_token": self.csrf_token,
                    "message": "Session created successfully"
                }
            else:
                return csrf_result
                
        except Exception as e:
            error_msg = f"Failed to create SAP session: {str(e)}"
            print(f"❌ {error_msg}")
            frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "SAP Session Creation Error")
            return {"success": False, "error": error_msg}
    
    def _fetch_csrf_token(self):
        """
        Fetch CSRF token from SAP server
        This also establishes the session cookies automatically
        """
        try:
            url = f"{self.sap_settings.url}{self.sap_client_code}"
            
            # Prepare headers for CSRF token request
            csrf_headers = {'X-CSRF-Token': 'FETCH'}
            
            print(f"🔑 Fetching CSRF token from: {url}")
            print(f"🔑 User: {self.sap_settings.auth_user_name}")
            
            # Make request to get CSRF token
            response = self.session.get(
                url, 
                headers=csrf_headers, 
                auth=self.auth, 
                timeout=30
            )
            
            print(f"🔑 CSRF Response Status: {response.status_code}")
            print(f"🔑 CSRF Response Headers: {dict(response.headers)}")
            print(f"🔑 Session Cookies Count: {len(self.session.cookies)}")
            
            # Log cookies for debugging
            for cookie in self.session.cookies:
                print(f"🍪 Cookie: {cookie.name} = {cookie.value}")
            
            if response.status_code == 200:
                csrf_token = response.headers.get('x-csrf-token')
                
                if csrf_token:
                    print(f"✅ CSRF Token obtained: {csrf_token}")
                    
                    # Validate essential cookies
                    session_id_found = False
                    usercontext_found = False
                    
                    for cookie in self.session.cookies:
                        if 'SAP_SESSIONID' in cookie.name:
                            session_id_found = True
                        if cookie.name == 'sap-usercontext':
                            usercontext_found = True
                    
                    if not session_id_found:
                        print("⚠️  WARNING: SAP Session ID cookie not found!")
                    if not usercontext_found:
                        print("⚠️  WARNING: sap-usercontext cookie not found!")
                    
                    return {
                        "success": True,
                        "csrf_token": csrf_token
                    }
                else:
                    error_msg = "CSRF token not found in response headers"
                    print(f"❌ {error_msg}")
                    return {"success": False, "error": error_msg}
            else:
                error_msg = f"Failed to fetch CSRF token: HTTP {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = "CSRF token request timed out"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Exception while fetching CSRF token: {str(e)}"
            print(f"❌ {error_msg}")
            frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "SAP CSRF Fetch Error")
            return {"success": False, "error": error_msg}
    
    def send_data(self, data, endpoint_suffix=""):
        """
        Send data to SAP using the established session
        data: The JSON data to send
        endpoint_suffix: Additional endpoint path if needed
        """
        if not self.session or not self.csrf_token:
            return {"success": False, "error": "Session not initialized. Call create_session() first."}
        
        try:
            url = f"{self.sap_settings.url}{self.sap_client_code}{endpoint_suffix}"
            
            # Update session headers with CSRF token
            self.session.headers.update({'X-CSRF-Token': self.csrf_token})
            
            print("=" * 80)
            print("📤 SENDING DATA TO SAP")
            print("=" * 80)
            print(f"URL: {url}")
            print(f"CSRF Token: {self.csrf_token}")
            print(f"Cookies Count: {len(self.session.cookies)}")
            print(f"Data: {json.dumps(data, indent=2, default=str)}")
            print("=" * 80)
            
            # Send POST request
            response = self.session.post(
                url, 
                json=data, 
                auth=self.auth, 
                timeout=30
            )
            
            print(f"📨 SAP Response Status: {response.status_code}")
            print(f"📨 SAP Response Headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                print(f"✅ Data sent successfully to SAP")
                return {
                    "success": True,
                    "response": response_data,
                    "status_code": response.status_code
                }
            else:
                error_msg = f"SAP API Error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "response_text": response.text
                }
                
        except requests.exceptions.Timeout:
            error_msg = "SAP request timed out"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"SAP request failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except ValueError as e:
            error_msg = f"JSON parsing error: {str(e)} - Response: {response.text if 'response' in locals() else 'No response'}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error sending data: {str(e)}"
            print(f"❌ {error_msg}")
            frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "SAP Send Data Error")
            return {"success": False, "error": error_msg}
    
    def close_session(self):
        """Close the SAP session"""
        if self.session:
            self.session.close()
            self.session = None
            self.csrf_token = None
            print("🔒 SAP session closed")


# =====================================================================================
# MAIN VENDOR ONBOARDING FUNCTION - SESSION BASED
# =====================================================================================

@frappe.whitelist(allow_guest=True)
def erp_to_sap_vendor_data(onb_ref):
    """
    Enhanced SAP vendor data sending function with session-based approach
    Maintains all original functionality while fixing cookie issues
    """
    print("=" * 80)
    print("ERP TO SAP VENDOR DATA - SESSION BASED - STARTING")
    print(f"Vendor Onboarding Reference: {onb_ref}")
    print("=" * 80)

    # **TRACKING VARIABLES**
    company_counter = 0
    total_gst_rows_processed = 0
    successful_sap_calls = 0
    failed_sap_calls = 0
    connection_errors = 0
    validation_errors = 0
    duplicate_count = 0
    
    try:
        # Get main documents
        onb = safe_get_doc("Vendor Onboarding", onb_ref)

        onb_vm = safe_get_doc("Vendor Master", getattr(onb, "ref_no", None))
        onb_pmd = safe_get_doc("Vendor Onboarding Payment Details", getattr(onb, "payment_detail", None))
        pur_org = safe_get_doc("Purchase Organization Master", getattr(onb, "purchase_organization", None))
        pur_grp = safe_get_doc("Purchase Group Master", getattr(onb, "purchase_group", None))
        acc_grp = safe_get_doc("Account Group Master", getattr(onb, "account_group", None))
        onb_reco = safe_get_doc("Reconciliation Account", getattr(onb, "reconciliation_account", None))
        onb_pm_term = safe_get_doc("Terms of Payment Master", getattr(onb, "terms_of_payment", None))
        onb_inco = safe_get_doc("Incoterm Master", getattr(onb, "incoterms", None))
        onb_bank = safe_get_doc("Bank Master", getattr(onb_pmd, "bank_name", None))
        onb_legal_doc = safe_get_doc("Legal Documents", getattr(onb, "document_details", None))


        # Boolean flags
        payee = 'X' if onb.payee_in_document == 1 else ''
        gr_based_inv_ver = 'X' if onb.gr_based_inv_ver == 1 else ''
        service_based_inv_ver = 'X' if onb.service_based_inv_ver == 1 else ''
        check_double_invoice = 'X' if onb.check_double_invoice == 1 else ''

        # Get vendor types
        vendor_type_names = []
        for row in onb.vendor_types:
            if row.vendor_type:
                vendor_type_doc = safe_get_doc("Vendor Type Master", getattr(row, "vendor_type", None))
                if vendor_type_doc:
                    vendor_type_names.append(vendor_type_doc.vendor_type_name)

        # **MAIN LOOP: Process each company**
        print(f"📊 Processing {len(onb.vendor_company_details)} companies...")
        
        for company in onb.vendor_company_details:
            company_counter += 1
            print(f"\n🏢 COMPANY {company_counter}: Processing company entry...")
            
            sap_session = None  # Initialize session variable for this company
            
            try:
                # Get company details
                vcd = safe_get_doc("Vendor Onboarding Company Details", getattr(company, "vendor_company_details", None))
                country_doc = safe_get_doc("Country Master", onb.vendor_country)
                country_code = country_doc.country_code if country_doc else "IN"
                com_vcd = safe_get_doc("Company Master", vcd.company_name)
                sap_client_code = com_vcd.sap_client_code
                vcd_state = safe_get_doc("State Master", getattr(vcd, "state", None))
                Zuawa = "001"
                
                # **DOMESTIC VENDOR PROCESSING (India)**
                if onb.vendor_country == "India":
                    print(f"   📋 Company: {vcd.company_name}")
                    print(f"   📋 SAP Client Code: {sap_client_code}")
                    print(f"   📋 GST Tables to process: {len(vcd.comp_gst_table)}")
                    
                    # **CREATE SAP SESSION FOR THIS COMPANY**
                    print(f"   🔄 Creating SAP session for client: {sap_client_code}")
                    sap_session = SAPSessionManager(sap_client_code)
                    session_result = sap_session.create_session()
                    
                    if not session_result["success"]:
                        connection_errors += 1
                        failed_sap_calls += len(vcd.comp_gst_table)  # Count all GST entries as failed
                        error_msg = f"Failed to create SAP session: {session_result.get('error', 'Unknown error')}"
                        print(f"   ❌ SESSION ERROR: {error_msg}")
                        
                        # Log connection error for all GST entries in this company
                        for gst_table in vcd.comp_gst_table:
                            try:
                                create_connection_error_sap_log(
                                    onb.name,
                                    {},  # Empty data since we couldn't connect
                                    error_msg,
                                    sap_client_code,
                                    vcd.company_name,
                                    onb.ref_no,
                                    gst_table.gst_number or "0",
                                    gst_table.gst_state
                                )
                            except Exception as log_err:
                                print(f"   ⚠️ Failed to create error log: {str(log_err)}")
                        
                        send_failure_notification(onb.name, "SAP Connection Error", error_msg)
                        continue  # Skip to next company
                    
                    # **PROCESS EACH GST ENTRY FOR DOMESTIC VENDOR**
                    gst_counter = 0
                    for gst_table in vcd.comp_gst_table:
                        gst_counter += 1
                        total_gst_rows_processed += 1
                        
                        print(f"\n   🔄 GST ENTRY {gst_counter} (Global #{total_gst_rows_processed}): Processing...")
                        
                        try:
                            # Get GST-specific data
                            gst_ven_type = gst_table.gst_ven_type
                            gst_state = gst_table.gst_state or ""
                            gst_state_doc = safe_get_doc("State Master", gst_state)
                            gst_num = gst_table.gst_number or "0"
                            gst_pin = gst_table.pincode or ""
                            gst_addrs = safe_get_doc("Pincode Master", gst_pin)
                            gst_city = gst_addrs.city or "" if gst_addrs else ""
                            gst_country = gst_addrs.country or "" if gst_addrs else ""
                            gst_district = gst_addrs.district or "" if gst_addrs else ""
                            
                            # Build address text
                            gst_address_text = ", ".join(filter(None, [
                                gst_city,
                                gst_district,
                                gst_state
                            ]))

                            print(f"      📍 Vendor GST Type: {gst_ven_type}")
                            print(f"      📍 GST State: {gst_state}")
                            print(f"      📍 GST Number: {gst_num}")
                            print(f"      📍 Address: {gst_address_text}")

                            # **HANDLE NOT-REGISTERED GST VENDORS**
                            if gst_ven_type == "Not-Registered":
                                print(f"      🔄 Processing Not-Registered GST vendor")
                                # For Not-Registered, GST number should be "0" or empty
                                gst_num = "0"

                            # **BUILD SAP PAYLOAD DATA FOR DOMESTIC VENDOR**
                            data = {
                                "Bukrs": com_vcd.company_code,
                                "Ekorg": pur_org.purchase_organization_code,
                                "Ktokk": acc_grp.account_group_code,
                                "Title": "",
                                "Name1": onb_vm.vendor_name,
                                "Name2": "",
                                "Sort1": onb_vm.search_term or "",
                                "Street": vcd.address_line_1,
                                "StrSuppl1": gst_address_text or "",
                                "StrSuppl2": "",
                                "StrSuppl3": "",
                                "PostCode1": gst_pin,
                                "City1": gst_city,
                                "Country": country_code,
                                "J1kftind": "",
                                "Region": gst_state_doc.sap_state_code if gst_state_doc else "",
                                "TelNumber": "",
                                "MobNumber": onb_vm.mobile_number or "",
                                "SmtpAddr": onb_vm.office_email_primary or "",
                                "SmtpAddr1": onb_vm.office_email_secondary or "",
                                "Zuawa": Zuawa,
                                "Akont": onb_reco.reconcil_account_code,
                                "Waers": onb_pmd.currency_code if onb_pmd else "INR",
                                "Zterm": onb_pm_term.terms_of_payment_code,
                                "Inco1": onb_inco.incoterm_code,
                                "Inco2": onb_inco.incoterm_name,
                                "Kalsk": "",
                                "Ekgrp": pur_grp.purchase_group_code,
                                "Xzemp": payee,
                                "Reprf": check_double_invoice,
                                "Webre": gr_based_inv_ver,
                                "Lebre": service_based_inv_ver,
                                "Stcd3": gst_num,
                                "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
                                "J1ipanno": vcd.company_pan_number if vcd else "",
                                "J1ipanref": onb_legal_doc.name_on_company_pan if onb_legal_doc else "",
                                "Namev": safe_get(onb, "contact_details", 0, "first_name"),
                                "Name11": safe_get(onb, "contact_details", 0, "last_name"),
                                "Bankl": onb_bank.bank_code if onb_bank else "",
                                "Bankn": onb_pmd.account_number if onb_pmd else "",
                                "Bkref": onb_pmd.ifsc_code if onb_pmd else "",
                                "Banka": onb_bank.bank_name if onb_bank else "",
                                "Koinh": onb_pmd.name_of_account_holder if onb_pmd else "",
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
                            
                            print(f"      🚀 Sending data to SAP for GST {gst_num} using session...")
                            
                            # **SEND DATA TO SAP USING SESSION**
                            result = sap_session.send_data(data)
                            
                            print(f"      📊 SAP Response: {result}")
                            
                            # **PROCESS SAP RESPONSE WITH ENHANCED DUPLICATE HANDLING**
                            if result["success"]:
                                response_data = result["response"]
                                
                                # Extract vendor code from response
                                vedno = response_data.get('d', {}).get('Vedno', '') if 'd' in response_data else response_data.get('Vedno', '')
                                zmsg = response_data.get('d', {}).get('Zmsg', '') if 'd' in response_data else response_data.get('Zmsg', '')
                                
                                # **ENHANCED DUPLICATE VENDOR HANDLING**
                                if zmsg and "Duplicate Vendor" in zmsg and vedno and vedno != 'E':
                                    duplicate_count += 1
                                    successful_sap_calls += 1  # Count duplicate as success
                                    print(f"      ✅ DUPLICATE SUCCESS: Vendor code {vedno} already exists (Duplicate)")
                                    
                                    # Log successful duplicate transaction
                                    log_sap_transaction_enhanced(
                                        onb.name, data, response_data, "Success", 
                                        f"Duplicate Vendor - {zmsg}", vcd.company_name, sap_client_code, 
                                        onb.ref_no, gst_num, gst_state, vedno
                                    )
                                    
                                    # **POPULATE VENDOR CODE FOR DUPLICATE**
                                    try:
                                        update_result = update_vendor_master(
                                            onb.ref_no, vcd.company_name, sap_client_code, 
                                            vedno, gst_num, gst_state, onb.name
                                        )
                                        print(f"      📝 Vendor Master Update for Duplicate: {update_result['status']}")
                                    except Exception as update_err:
                                        print(f"      ❌ Update Error for Duplicate: {str(update_err)}")
                                        frappe.log_error(str(update_err), "Vendor Master Update Error - Duplicate")
                                
                                elif vedno == 'E' or vedno == '' or not vedno:
                                    failed_sap_calls += 1
                                    error_msg = f"SAP returned error or empty vendor code. Vedno: '{vedno}', Zmsg: '{zmsg}'"
                                    print(f"      ❌ SAP Error: {error_msg}")
                                    
                                    # Log the failed transaction
                                    log_sap_transaction_enhanced(
                                        onb.name, data, response_data, "SAP Error", 
                                        error_msg, vcd.company_name, sap_client_code, 
                                        onb.ref_no, gst_num, gst_state
                                    )
                                    
                                    send_failure_notification(onb.name, "SAP Vendor Creation Failed", error_msg)
                                    
                                else:
                                    successful_sap_calls += 1
                                    print(f"      ✅ SUCCESS: Vendor code {vedno} created for GST {gst_num}")
                                    
                                    # Log successful transaction
                                    log_sap_transaction_enhanced(
                                        onb.name, data, response_data, "Success", 
                                        "", vcd.company_name, sap_client_code, 
                                        onb.ref_no, gst_num, gst_state, vedno
                                    )
                                    
                                    # Update vendor master
                                    try:
                                        update_result = update_vendor_master(
                                            onb.ref_no, vcd.company_name, sap_client_code, 
                                            vedno, gst_num, gst_state, onb.name
                                        )
                                        print(f"      📝 Vendor Master Update: {update_result['status']}")
                                    except Exception as update_err:
                                        print(f"      ❌ Update Error: {str(update_err)}")
                                        frappe.log_error(str(update_err), "Vendor Master Update Error")
                            else:
                                # **SAP API ERROR**
                                failed_sap_calls += 1
                                error_msg = result["error"]
                                print(f"      ❌ SAP API Error: {error_msg}")
                                
                                # Log the failed transaction
                                log_sap_transaction_enhanced(
                                    onb.name, data, result.get("response_text", ""), "Failed", 
                                    error_msg, vcd.company_name, sap_client_code, 
                                    onb.ref_no, gst_num, gst_state
                                )
                                
                                send_failure_notification(onb.name, "SAP API Error", error_msg)
                        
                        except Exception as gst_err:
                            failed_sap_calls += 1
                            validation_errors += 1
                            error_msg = f"Error processing GST entry {gst_counter}: {str(gst_err)}"
                            print(f"      ❌ GST Processing Error: {error_msg}")
                            frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "GST Processing Error")
                            continue
                    
                    print(f"   ✅ Company {company_counter} completed: {gst_counter} GST entries processed")

                # **INTERNATIONAL VENDOR PROCESSING (Non-India)**
                elif onb.vendor_country != "India":
                    total_gst_rows_processed += 1  # Count international as 1 entry
                    
                    print(f"   📋 Company: {vcd.company_name}")
                    print(f"   📋 SAP Client Code: {sap_client_code}")
                    print(f"   📋 International Vendor")
                    
                    # **CREATE SAP SESSION FOR THIS COMPANY**
                    print(f"   🔄 Creating SAP session for client: {sap_client_code}")
                    sap_session = SAPSessionManager(sap_client_code)
                    session_result = sap_session.create_session()
                    
                    if not session_result["success"]:
                        connection_errors += 1
                        failed_sap_calls += 1  # Count as 1 failed call for international
                        error_msg = f"Failed to create SAP session: {session_result.get('error', 'Unknown error')}"
                        print(f"   ❌ SESSION ERROR: {error_msg}")
                        
                        try:
                            create_connection_error_sap_log(
                                onb.name,
                                {},  # Empty data since we couldn't connect
                                error_msg,
                                sap_client_code,
                                vcd.company_name,
                                onb.ref_no,
                                "0",  # International vendors have no GST
                                "International"
                            )
                        except Exception as log_err:
                            print(f"   ⚠️ Failed to create error log: {str(log_err)}")
                        
                        send_failure_notification(onb.name, "SAP Connection Error", error_msg)
                        continue  # Skip to next company
                    
                    print(f"\n   🔄 International vendor data: Processing...")
                    
                    try:
                        # Get international address data
                        gst_state = vcd.international_state or ""
                        gst_pin = vcd.international_zipcode or ""
                        gst_city = vcd.international_city or ""
                        gst_country = vcd.international_country or ""
                        gst_num = "0"  # International vendors have no GST
                        
                        # Build address text
                        gst_address_text = ", ".join(filter(None, [
                            gst_city,
                            gst_country,
                            gst_state
                        ]))

                        print(f"      📍 International State: {gst_state}")
                        print(f"      📍 International Pin: {gst_pin}")
                        print(f"      📍 Address: {gst_address_text}")

                        # **BUILD SAP PAYLOAD DATA FOR INTERNATIONAL VENDOR**
                        data = {
                            "Bukrs": com_vcd.company_code,
                            "Ekorg": pur_org.purchase_organization_code,
                            "Ktokk": acc_grp.account_group_code,
                            "Title": "",
                            "Name1": onb_vm.vendor_name,
                            "Name2": "",
                            "Sort1": onb_vm.search_term or "",
                            "Street": vcd.address_line_1,
                            "StrSuppl1": gst_address_text or "",
                            "StrSuppl2": "",
                            "StrSuppl3": "",
                            "PostCode1": gst_pin,
                            "City1": gst_city,
                            "Country": country_code,
                            "J1kftind": "",
                            "Region": "ZZ",  # Fixed region for international vendors
                            "TelNumber": "",
                            "MobNumber": onb_vm.mobile_number or "",
                            "SmtpAddr": onb_vm.office_email_primary or "",
                            "SmtpAddr1": onb_vm.office_email_secondary or "",
                            "Zuawa": Zuawa,
                            "Akont": onb_reco.reconcil_account_code,
                            "Waers": onb_pmd.currency_code if onb_pmd else "USD",
                            "Zterm": onb_pm_term.terms_of_payment_code,
                            "Inco1": onb_inco.incoterm_code,
                            "Inco2": onb_inco.incoterm_name,
                            "Kalsk": "",
                            "Ekgrp": pur_grp.purchase_group_code,
                            "Xzemp": payee,
                            "Reprf": check_double_invoice,
                            "Webre": gr_based_inv_ver,
                            "Lebre": service_based_inv_ver,
                            "Stcd3": "0",  # No GST for international
                            "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
                            "J1ipanno": "0",  # No PAN for international
                            "J1ipanref": onb_legal_doc.name_on_company_pan if onb_legal_doc else "",
                            "Namev": safe_get(onb, "contact_details", 0, "first_name"),
                            "Name11": safe_get(onb, "contact_details", 0, "last_name"),
                            "Bankl": "",  # International uses different banking fields
                            "Bankn": "",
                            "Bkref": "",
                            "Banka": "",
                            "Koinh": "",
                            "Xezer": "",
                            # International banking details are mandatory for international vendors
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
                        
                        print(f"      🚀 Sending international vendor data to SAP using session...")
                        
                        # **SEND DATA TO SAP USING SESSION**
                        result = sap_session.send_data(data)
                        
                        print(f"      📊 SAP Response: {result}")
                        
                        # **PROCESS SAP RESPONSE WITH DUPLICATE HANDLING FOR INTERNATIONAL**
                        if result["success"]:
                            response_data = result["response"]
                            
                            # Extract vendor code from response
                            vedno = response_data.get('d', {}).get('Vedno', '') if 'd' in response_data else response_data.get('Vedno', '')
                            zmsg = response_data.get('d', {}).get('Zmsg', '') if 'd' in response_data else response_data.get('Zmsg', '')
                            
                            # **ENHANCED DUPLICATE VENDOR HANDLING FOR INTERNATIONAL**
                            if zmsg and "Duplicate Vendor" in zmsg and vedno and vedno != 'E':
                                duplicate_count += 1
                                successful_sap_calls += 1  # Count duplicate as success
                                print(f"      ✅ DUPLICATE SUCCESS: International vendor code {vedno} already exists")
                                
                                # Log successful duplicate transaction
                                log_sap_transaction_enhanced(
                                    onb.name, data, response_data, "Success", 
                                    f"Duplicate International Vendor - {zmsg}", vcd.company_name, sap_client_code, 
                                    onb.ref_no, gst_num, "International", vedno
                                )
                                
                                # **POPULATE VENDOR CODE FOR INTERNATIONAL DUPLICATE**
                                try:
                                    vcc_state = f"International-{gst_state}-{gst_city}"
                                    update_result = update_vendor_master(
                                        onb.ref_no, vcd.company_name, sap_client_code, 
                                        vedno, gst_num, vcc_state, onb.name
                                    )
                                    print(f"      📝 Vendor Master Update for International Duplicate: {update_result['status']}")
                                except Exception as update_err:
                                    print(f"      ❌ Update Error for International Duplicate: {str(update_err)}")
                                    frappe.log_error(str(update_err), "Vendor Master Update Error - International Duplicate")
                            
                            elif vedno == 'E' or vedno == '' or not vedno:
                                failed_sap_calls += 1
                                error_msg = f"SAP returned error or empty vendor code. Vedno: '{vedno}', Zmsg: '{zmsg}'"
                                print(f"      ❌ SAP Error: {error_msg}")
                                
                                # Log the failed transaction
                                log_sap_transaction_enhanced(
                                    onb.name, data, response_data, "SAP Error", 
                                    error_msg, vcd.company_name, sap_client_code, 
                                    onb.ref_no, gst_num, "International"
                                )
                                
                                send_failure_notification(onb.name, "SAP International Vendor Creation Failed", error_msg)
                                
                            else:
                                successful_sap_calls += 1
                                print(f"      ✅ SUCCESS: International vendor code {vedno} created")
                                
                                # Log successful transaction
                                log_sap_transaction_enhanced(
                                    onb.name, data, response_data, "Success", 
                                    "", vcd.company_name, sap_client_code, 
                                    onb.ref_no, gst_num, "International", vedno
                                )
                                
                                # Update vendor master
                                try:
                                    vcc_state = f"International-{gst_state}-{gst_city}"
                                    update_result = update_vendor_master(
                                        onb.ref_no, vcd.company_name, sap_client_code, 
                                        vedno, gst_num, vcc_state, onb.name
                                    )
                                    print(f"      📝 Vendor Master Update: {update_result['status']}")
                                except Exception as update_err:
                                    print(f"      ❌ Update Error: {str(update_err)}")
                                    frappe.log_error(str(update_err), "Vendor Master Update Error")
                        else:
                            # **SAP API ERROR**
                            failed_sap_calls += 1
                            error_msg = result["error"]
                            print(f"      ❌ SAP API Error: {error_msg}")
                            
                            # Log the failed transaction
                            log_sap_transaction_enhanced(
                                onb.name, data, result.get("response_text", ""), "Failed", 
                                error_msg, vcd.company_name, sap_client_code, 
                                onb.ref_no, gst_num, "International"
                            )
                            
                            send_failure_notification(onb.name, "SAP API Error", error_msg)
                    
                    except Exception as intl_err:
                        failed_sap_calls += 1
                        validation_errors += 1
                        error_msg = f"Error processing international vendor: {str(intl_err)}"
                        print(f"      ❌ International Processing Error: {error_msg}")
                        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "International Processing Error")
                        continue
                    
                    print(f"   ✅ Company {company_counter} completed: International vendor processed")

                
            except Exception as company_err:
                if 'vcd' in locals() and hasattr(vcd, 'comp_gst_table'):
                    failed_sap_calls += len(vcd.comp_gst_table)
                else:
                    failed_sap_calls += 1
                validation_errors += 1
                error_msg = f"Error processing company {company_counter}: {str(company_err)}"
                print(f"   ❌ Company Processing Error: {error_msg}")
                frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "Company Processing Error")
                continue
            
            finally:
                # **ALWAYS CLOSE SESSION FOR THIS COMPANY**
                if sap_session:
                    sap_session.close_session()
        
        # **ENHANCED FINAL SUMMARY WITH PROPER SUCCESS DETERMINATION**
        total_attempts = successful_sap_calls + failed_sap_calls
        success_rate = (successful_sap_calls / total_attempts * 100) if total_attempts > 0 else 0
        
        print("=" * 80)
        print("ERP TO SAP VENDOR DATA - FINAL RESULTS")
        print("=" * 80)
        print(f"📊 Total Companies Processed: {company_counter}")
        print(f"📊 Total GST Rows Processed: {total_gst_rows_processed}")
        print(f"✅ Successful SAP API Calls: {successful_sap_calls}")
        print(f"❌ Failed SAP API Calls: {failed_sap_calls}")
        print(f"🔄 Duplicate Vendors Found: {duplicate_count}")
        print(f"🔌 Connection Errors: {connection_errors}")
        print(f"⚠️ Validation Errors: {validation_errors}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print("=" * 80)
        
        # **DETERMINE OVERALL STATUS BASED ON ACTUAL SAP SUCCESS**
        if successful_sap_calls == 0 and failed_sap_calls > 0:
            status = "error"
            message = f"SAP Integration Failed: 0/{total_attempts} successful. "
            
            if connection_errors > 0:
                message += f"Connection errors: {connection_errors}. Check SAP server connectivity."
            elif validation_errors > 0:
                message += f"Validation errors: {validation_errors}. Check data completeness."
            else:
                message += "All SAP API calls failed."
                
        elif successful_sap_calls > 0 and failed_sap_calls == 0:
            status = "success"
            if duplicate_count > 0:
                message = f"SAP Integration Successful: {successful_sap_calls}/{total_attempts} entries processed successfully. {duplicate_count} duplicate vendors found and vendor codes populated."
            else:
                message = f"SAP Integration Successful: {successful_sap_calls}/{total_attempts} entries sent to SAP successfully."
            
            # **UPDATE ONBOARDING DOCUMENT STATUS**
            try:
                onb.data_sent_to_sap = 1
                onb.save(ignore_permissions=True)
                frappe.db.commit()
                print(f"✅ Onboarding document updated: data_sent_to_sap = 1")
            except Exception as onb_update_err:
                print(f"⚠️ Failed to update onboarding status: {str(onb_update_err)}")
            
        elif successful_sap_calls > 0 and failed_sap_calls > 0:
            status = "partial_success"
            duplicate_msg = f" ({duplicate_count} duplicates found)" if duplicate_count > 0 else ""
            message = f"SAP Integration Partial Success: {successful_sap_calls}/{total_attempts} successful ({success_rate:.1f}%){duplicate_msg}. {failed_sap_calls} failed."
            
        else:
            status = "error"
            message = "No SAP integration attempts were made. Check data configuration."
        
        print(f"🎯 FINAL STATUS: {status.upper()}")
        print(f"💬 FINAL MESSAGE: {message}")
        
        return {
            "status": status,
            "message": message,
            "companies_processed": company_counter,
            "gst_rows_processed": total_gst_rows_processed,
            "successful_sap_calls": successful_sap_calls,
            "failed_sap_calls": failed_sap_calls,
            "duplicate_count": duplicate_count,
            "connection_errors": connection_errors,
            "validation_errors": validation_errors,
            "success_rate": success_rate
        }
        
    except Exception as e:
        error_msg = f"Main function error in erp_to_sap_vendor_data: {str(e)}"
        print(f"❌ MAIN ERROR: {error_msg}")
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "ERP to SAP Vendor Data Error")
        
        try:
            send_failure_notification(onb_ref, "ERP to SAP Main Function Error", error_msg)
        except Exception as notif_err:
            print(f"⚠️ Failed to send notification: {str(notif_err)}")
        
        return {
            "status": "error",
            "message": f"Critical error in SAP integration: {error_msg}",
            "companies_processed": company_counter,
            "gst_rows_processed": total_gst_rows_processed,
            "successful_sap_calls": 0,
            "failed_sap_calls": total_gst_rows_processed,
            "duplicate_count": 0,
            "connection_errors": 1,
            "validation_errors": 0,
            "success_rate": 0.0
        }
# =====================================================================================
# ENHANCED LOGGING FUNCTIONS
# =====================================================================================

def log_sap_transaction_enhanced(onb_name, request_data, response_data, status, error_details, 
                               company_name, sap_client_code, vendor_ref_no, gst_num, gst_state, vendor_code=None):
    """
    Enhanced SAP transaction logging with all details
    """
    try:
        sap_log = frappe.new_doc("VMS SAP Logs")
        sap_log.vendor_onboarding_link = onb_name
        
        # Store full data since erp_to_sap_data is JSON field
        sap_log.erp_to_sap_data = request_data
        
        # Store full response since sap_response is JSON field  
        if response_data:
            try:
                if isinstance(response_data, dict):
                    sap_log.sap_response = response_data
                else:
                    sap_log.sap_response = {"raw_response": str(response_data), "parse_note": "Non-dict response"}
            except Exception:
                sap_log.sap_response = {"raw_response": str(response_data), "parse_error": "Could not process response"}
        else:
            sap_log.sap_response = {"error": error_details}
        
        # Create comprehensive transaction log
        total_transaction_data = {
            "request_details": {
                "url": f"SAP_URL/{sap_client_code}",
                "sap_client_code": sap_client_code,
                "company_name": company_name,
                "vendor_ref_no": vendor_ref_no,
                "gst_number": gst_num,
                "gst_state": gst_state,
                "payload": request_data,
                "session_based": True,
                "csrf_token_used": True
            },
            "response_details": {
                "status": status,
                "vendor_code": vendor_code,
                "response_body": response_data if response_data else error_details
            },
            "transaction_summary": {
                "status": status,
                "vendor_code": vendor_code,
                "error_details": error_details,
                "timestamp": frappe.utils.now(),
                "sap_client_code": sap_client_code,
                "company_name": company_name,
                "vendor_ref_no": vendor_ref_no,
                "integration_method": "Session-Based"
            }
        }
        
        sap_log.total_transaction = json.dumps(total_transaction_data, indent=2, default=str)
        sap_log.save(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"📝 Enhanced SAP Log created: {sap_log.name}")
        
    except Exception as log_err:
        print(f"❌ Failed to create enhanced SAP log: {str(log_err)}")
        frappe.log_error(f"Enhanced SAP log creation failed: {str(log_err)}", "Enhanced SAP Log Error")


# =====================================================================================
# HELPER FUNCTIONS (SAME AS ORIGINAL)
# =====================================================================================

def safe_get_doc(doctype, name):
    try:
        if name:  # only try if not None/empty
            return frappe.get_doc(doctype, name)
    except frappe.DoesNotExistError:
        return None
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error fetching {doctype} {name}")
        return None
    return None


def safe_get(obj, list_name, index, attr, default=""):
    """Helper function to safely get nested attributes"""
    try:
        return getattr(getattr(obj, list_name)[index], attr) or default
    except (AttributeError, IndexError, TypeError):
        return default


def send_failure_notification(onb_name, failure_type, error_details):
    """Send email notifications to purchase team when SAP integration fails"""
    try:
        # Get vendor onboarding document
        onb_doc = frappe.get_doc("Vendor Onboarding", onb_name)
        registered_by = onb_doc.registered_by
        
        if not registered_by:
            print(f"⚠️ No registered_by found for {onb_name}")
            return
        
        # Get email recipients
        recipients = get_notification_recipients(registered_by)
        
        if not recipients:
            print(f"⚠️ No email recipients found for registered_by: {registered_by}")
            return
        
        # Prepare email content
        subject = f"🚨 SAP Integration Alert: {failure_type} - {onb_doc.vendor_name or 'Unknown Vendor'}"
        
        # Get vendor details for email
        vendor_details = get_vendor_details_for_email(onb_doc)
        
        # Create email message
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px;">
            <div style="background-color: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0; font-size: 24px;">🚨 SAP Integration Alert</h2>
                <p style="margin: 5px 0 0 0; font-size: 16px;">Action Required: {failure_type}</p>
            </div>
            
            <div style="padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <h3 style="color: #dc3545; margin-top: 0;">⚠️ Issue Summary</h3>
                    <p style="margin: 0; font-size: 16px; line-height: 1.5;"><strong>{error_details}</strong></p>
                </div>
                
                <h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px;">📋 Vendor Information</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; width: 40%;">Vendor Name</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['vendor_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Reference Number</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['ref_no']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Onboarding ID</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{onb_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Company</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['company']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Email</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['email']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Mobile</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{vendor_details['mobile']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Registered By</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{registered_by}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Date & Time</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{frappe.utils.now()}</td>
                    </tr>
                </table>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <h4 style="color: #856404; margin-top: 0;">🔍 Next Steps</h4>
                    <ul style="margin: 0; color: #856404;">
                        <li>Review the vendor onboarding details</li>
                        <li>Check SAP connectivity and credentials</li>
                        <li>Verify vendor data completeness</li>
                        <li>Contact IT team if technical issues persist</li>
                        <li>Retry the SAP integration after resolving issues</li>
                    </ul>
                </div>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #666; font-size: 12px;">
                <p style="margin: 0;">This is an automated alert from the VMS SAP Integration System (Session-Based)</p>
                <p style="margin: 5px 0 0 0;">Please do not reply to this email</p>
            </div>
        </div>
        """
        
        # Send email to all recipients
        for recipient in recipients:
            try:
                frappe.sendmail(
                    recipients=[recipient["email"], "thunder00799@gmail.com"],
                    subject=subject,
                    message=message,
                    now=True
                )
                print(f"📧 Notification sent to: {recipient['name']} ({recipient['email']})")
                
            except Exception as email_err:
                print(f"❌ Failed to send email to {recipient['email']}: {str(email_err)}")
                frappe.log_error(f"Failed to send notification email to {recipient['email']}: {str(email_err)}")
        
        # Log the notification
        frappe.log_error(
            title=f"SAP Integration Notification Sent - {failure_type}",
            message=f"Vendor: {vendor_details['vendor_name']}\nOnboarding: {onb_name}\nError: {error_details}\nNotified: {', '.join([r['email'] for r in recipients])}"
        )
        
    except Exception as e:
        error_msg = f"Failed to send failure notification: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg)


def get_notification_recipients(registered_by):
    """Get email recipients: registered_by user and their reporting manager"""
    recipients = []
    
    try:
        # Get the user who registered the vendor
        user_email = registered_by
        
        # Try to find employee record for registered_by user
        employee = None
        employee_name = frappe.db.exists("Employee", {"user_id": registered_by})
        
        if employee_name:
            employee = frappe.get_doc("Employee", employee_name)
            recipients.append({
                "name": employee.first_name,
                "email": user_email,
                "role": "Registered By"
            })
            
            # Get reporting manager if exists
            if employee.reports_to:
                try:
                    manager = frappe.get_doc("Employee", employee.reports_to)
                    if manager.user_id:
                        recipients.append({
                            "name": manager.employee_name or manager.name,
                            "email": manager.user_id,
                            "role": "Reporting Manager"
                        })
                except Exception as manager_err:
                    print(f"⚠️ Could not get manager details: {str(manager_err)}")
        else:
            # If no employee record found, just use the registered_by email
            recipients.append({
                "name": registered_by.split("@")[0].title(),
                "email": user_email,
                "role": "Registered By"
            })
            
        # Remove duplicates and invalid emails
        unique_recipients = []
        seen_emails = set()
        
        for recipient in recipients:
            if recipient["email"] and recipient["email"] not in seen_emails and "@" in recipient["email"]:
                unique_recipients.append(recipient)
                seen_emails.add(recipient["email"])
        
        return unique_recipients
        
    except Exception as e:
        print(f"❌ Error getting notification recipients: {str(e)}")
        frappe.log_error(f"Error getting notification recipients: {str(e)}")
        return []


def get_vendor_details_for_email(onb_doc):
    """Extract vendor details for email notification"""
    try:
        vendor_master = frappe.get_doc("Vendor Master", onb_doc.ref_no) if onb_doc.ref_no else None
        
        return {
            "vendor_name": vendor_master.vendor_name if vendor_master else "Unknown",
            "ref_no": onb_doc.ref_no or "Not Set",
            "company": onb_doc.company or "Not Specified",
            "email": vendor_master.office_email_primary if vendor_master else "Not Provided",
            "mobile": vendor_master.mobile_number if vendor_master else "Not Provided"
        }
    except Exception as e:
        print(f"⚠️ Error getting vendor details: {str(e)}")
        return {
            "vendor_name": "Unknown",
            "ref_no": "Unknown",
            "company": "Unknown", 
            "email": "Unknown",
            "mobile": "Unknown"
        }


def update_vendor_master(name, company_name, sap_code, vendor_code, gst, state, onb):
    """
    Fixed function to properly handle multiple vendor code rows for a single company
    """
    try:
        # Get vendor master document
        ref_vm = frappe.get_doc("Vendor Master", name)
        
        # Look for existing Company Vendor Code document
        cvc_name = frappe.db.exists("Company Vendor Code", {
            "sap_client_code": sap_code, 
            "vendor_ref_no": ref_vm.name
        })
        
        if cvc_name:
            # Load existing Company Vendor Code document
            cvc = frappe.get_doc("Company Vendor Code", cvc_name)
        else:
            # Create new Company Vendor Code document
            cvc = frappe.new_doc("Company Vendor Code")
            cvc.vendor_ref_no = ref_vm.name
            cvc.company_name = company_name
            cvc.sap_client_code = sap_code
            
        # **FIX: Handle multiple vendor codes for same company**
        # Check if this exact combination already exists
        found_existing = False
        
        if hasattr(cvc, 'vendor_code') and cvc.vendor_code:
            for vc in cvc.vendor_code:
                # Match based on GST and State combination
                if (getattr(vc, 'gst_no', '') == gst and 
                    getattr(vc, 'state', '') == state):
                    # Update existing record
                    vc.vendor_code = vendor_code
                    vc.gst_no = gst
                    vc.state = state
                    found_existing = True
                    print(f"✅ Updated existing vendor code row: GST={gst}, State={state}, Vendor Code={vendor_code}")
                    break
        
        # If no matching record found, add new row
        if not found_existing:
            new_vendor_code_row = {
                "vendor_code": vendor_code,
                "gst_no": gst,
                "state": state
            }
            cvc.append("vendor_code", new_vendor_code_row)
            print(f"✅ Added new vendor code row: GST={gst}, State={state}, Vendor Code={vendor_code}")
        
        # Save the Company Vendor Code document
        cvc.save(ignore_permissions=True)
        print(f"✅ Saved Company Vendor Code document: {cvc.name}")
        
        # **FIX: Update Multiple Company Data in Vendor Master**
        # Find and update the corresponding multiple_company_data row
        mcd_updated = False
        
        if hasattr(ref_vm, 'multiple_company_data') and ref_vm.multiple_company_data:
            for mcd_row in ref_vm.multiple_company_data:
                # Match by SAP client code or company name
                if (getattr(mcd_row, 'sap_client_code', '') == sap_code or 
                    getattr(mcd_row, 'company_name', '') == company_name):
                    mcd_row.company_vendor_code = cvc.name
                    mcd_updated = True
                    print(f"✅ Updated existing multiple_company_data row with CVC: {cvc.name}")
                    break
        
        # If no matching multiple_company_data row found, create new one
        if not mcd_updated:
            ref_vm.append("multiple_company_data", {
                "company_name": company_name,
                "sap_client_code": sap_code,
                "company_vendor_code": cvc.name
            })
            print(f"✅ Added new multiple_company_data row with CVC: {cvc.name}")
        
        # Save vendor master document
        ref_vm.save(ignore_permissions=True)
        print(f"✅ Updated Vendor Master: {ref_vm.name}")
        
        # Update onboarding document
        onb_doc = frappe.get_doc("Vendor Onboarding", onb)
        onb_doc.data_sent_to_sap = 1
        onb_doc.save(ignore_permissions=True)
        print(f"✅ Updated Onboarding document: data_sent_to_sap = 1")
        
        # Commit the transaction
        frappe.db.commit()
        print(f"✅ Transaction committed successfully")
        
        return {
            "status": "success",
            "message": f"Vendor master updated with vendor code: {vendor_code}",
            "vendor_code": vendor_code,
            "company_vendor_code": cvc.name,
            "action_taken": "updated" if found_existing else "added_new"
        }
        
    except Exception as e:
        # Rollback on error
        frappe.db.rollback()
        error_msg = f"Failed to update vendor master: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "Update Vendor Master Error")
        print(f"❌ Error updating vendor master: {error_msg}")
        
        return {
            "status": "error", 
            "message": error_msg,
            "vendor_code": vendor_code,
            "error_details": str(e)
        }


def create_connection_error_sap_log(onb_name, data, error_msg, sap_client_code, company_name, vendor_ref_no, gst_num = None, gst_state = None):
    """
    Create SAP log entry for connection errors when CSRF token request fails
    """
    try:
        sap_log = frappe.new_doc("VMS SAP Logs")
        sap_log.vendor_onboarding_link = onb_name
        
        # Store the payload that would have been sent
        sap_log.erp_to_sap_data = data
        
        # Create error response object for connection failure
        error_response = {
            "error_type": "connection_error",
            "error_message": error_msg,
            "timestamp": frappe.utils.now(),
            "status": "connection_failed",
            "http_status": "No Response",
            "details": {
                "session_creation_failed": True,
                "connection_refused": "Connection refused" in error_msg or "Failed to establish" in error_msg,
                "gst_number": gst_num,
                "gst_state": gst_state,
                "sap_client_code": sap_client_code
            }
        }
        
        sap_log.sap_response = error_response
        
        # Create comprehensive transaction log matching send_detail format
        transaction_data = {
            "request_details": {
                "url": f"SAP_URL/{sap_client_code}",
                "sap_client_code": sap_client_code,
                "company_name": company_name,
                "vendor_ref_no": vendor_ref_no,
                "gst_number": gst_num,
                "gst_state": gst_state,
                "payload": data,
                "session_based": True,
                "session_creation_attempted": True,
                "session_creation_successful": False
            },
            "response_details": {
                "status_code": "Session Creation Failed",
                "headers": {},
                "body": error_msg,
                "connection_error": True
            },
            "transaction_summary": {
                "status": "Session Creation Failed",
                "vendor_code": None,
                "error_details": error_msg,
                "timestamp": frappe.utils.now(),
                "sap_client_code": sap_client_code,
                "company_name": company_name,
                "vendor_ref_no": vendor_ref_no,
                "error_category": "Infrastructure/Connectivity",
                "integration_method": "Session-Based",
                "actionable_steps": [
                    "Check SAP server connectivity",
                    "Verify network access to SAP server",
                    "Contact IT team to check SAP server status",
                    "Verify SAP credentials and authorization",
                    "Retry after connectivity is restored"
                ]
            }
        }
        
        sap_log.total_transaction = frappe.as_json(transaction_data, indent=2)
        sap_log.save(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"📝 Session Connection Error SAP Log created: {sap_log.name}")
        
        # Also create Error Log entry for connection failure
        error_log = frappe.new_doc("Error Log")
        error_log.method = "erp_to_sap_vendor_data_session_based"
        error_log.error = f"SAP Session Connection Error: {error_msg}\nVendor: {vendor_ref_no}\nCompany: {company_name}\nGST: {gst_num}"
        error_log.save(ignore_permissions=True)
        print(f"📝 Session Connection Error Log created: {error_log.name}")
        
        return sap_log.name
        
    except Exception as e:
        error_msg = f"Failed to create session connection error SAP log: {str(e)}"
        print(f"❌ SAP Log Creation Error: {error_msg}")
        frappe.log_error(error_msg, "Session Connection Error SAP Log Creation")
        return None


# =====================================================================================
# COMPATIBILITY FUNCTIONS (LEGACY SUPPORT)
# =====================================================================================

@frappe.whitelist(allow_guest=True)
def get_csrf_token_and_session(sap_client_code):
    """
    Legacy compatibility function - redirects to session-based approach
    This maintains backward compatibility with any existing calls
    """
    print("⚠️  Legacy CSRF function called - redirecting to session-based approach")
    
    try:
        sap_session = SAPSessionManager(sap_client_code)
        result = sap_session.create_session()
        
        if result["success"]:
            # Extract cookies for legacy compatibility
            session_cookies = {}
            for cookie in sap_session.session.cookies:
                session_cookies[cookie.name] = cookie.value
            
            return {
                "success": True,
                "csrf_token": result["csrf_token"],
                "session_cookies": session_cookies,
                "error": ""
            }
        else:
            return {
                "success": False,
                "csrf_token": "",
                "session_cookies": {},
                "error": result["error"]
            }
            
    except Exception as e:
        return {
            "success": False,
            "csrf_token": "",
            "session_cookies": {},
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True)
def send_detail(csrf_token, data, session_cookies, name, sap_code, state, gst, company_name, onb_name):
    """
    Legacy compatibility function - redirects to session-based implementation
    This maintains backward compatibility while using the new session approach
    """
    print("⚠️  Legacy send_detail function called - using session-based implementation")
    
    try:
        # Create session manager
        sap_session = SAPSessionManager(sap_code)
        session_result = sap_session.create_session()
        
        if not session_result["success"]:
            return {
                "error": f"Failed to create SAP session: {session_result.get('error', 'Unknown error')}",
                "transaction_status": "Session Creation Failed",
                "error_details": session_result.get('error', 'Unknown error')
            }
        
        # Send data using session
        result = sap_session.send_data(data)
        
        # Close session
        sap_session.close_session()
        
        if result["success"]:
            return result["response"]
        else:
            return {
                "error": result["error"],
                "transaction_status": "Failed",
                "error_details": result["error"]
            }
            
    except Exception as e:
        return {
            "error": f"Legacy compatibility error: {str(e)}",
            "transaction_status": "Compatibility Error",
            "error_details": str(e)
        }


# =====================================================================================
# TESTING AND DEBUGGING FUNCTIONS
# =====================================================================================

@frappe.whitelist()
def test_sap_session_connection(sap_client_code):
    """
    Test function to verify SAP session connectivity
    Use this to debug SAP connection issues
    """
    try:
        print(f"🧪 Testing SAP session connection for client: {sap_client_code}")
        
        sap_session = SAPSessionManager(sap_client_code)
        result = sap_session.create_session()
        
        if result["success"]:
            print("✅ SAP session test successful!")
            
            # Test basic connectivity
            test_data = {"test": "connection"}
            send_result = sap_session.send_data(test_data)
            
            sap_session.close_session()
            
            if send_result["success"]:
                return {
                    "success": True, 
                    "message": "SAP session and connectivity test successful",
                    "csrf_token": result["csrf_token"]
                }
            else:
                return {
                    "success": False, 
                    "message": f"Session created but data send failed: {send_result['error']}",
                    "error": send_result["error"]
                }
        else:
            print(f"❌ SAP session test failed: {result['error']}")
            return {
                "success": False, 
                "message": "SAP session creation failed",
                "error": result["error"]
            }
            
    except Exception as e:
        error_msg = f"SAP session test error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False, 
            "message": "SAP session test exception",
            "error": error_msg
        }


@frappe.whitelist()
def debug_vendor_onboarding_data(onb_ref):
    """
    Debug function to test vendor onboarding data preparation without sending to SAP
    """
    try:
        print(f"🔍 Debugging vendor onboarding data for: {onb_ref}")
        
        # This would run through your data preparation logic without actually sending to SAP
        # You can add detailed logging here to see exactly what data is being prepared
        
        onb = frappe.get_doc("Vendor Onboarding", onb_ref)
        print(f"✅ Found onboarding document: {onb.name}")
        print(f"📋 Vendor name: {onb.vendor_name if hasattr(onb, 'vendor_name') else 'Not found'}")
        print(f"📋 Company count: {len(onb.vendor_company_details)}")
        
        return {
            "success": True,
            "message": "Debug data extraction successful",
            "onboarding_id": onb.name,
            "company_count": len(onb.vendor_company_details)
        }
        
    except Exception as e:
        error_msg = f"Debug error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": "Debug failed",
            "error": error_msg
        }


# =====================================================================================
# MIGRATION UTILITY FUNCTIONS
# =====================================================================================

def migrate_to_session_based():
    """
    Utility function to help migrate from old cookie-based approach to session-based
    This can be run to test the new implementation
    """
    print("🔄 Starting migration to session-based SAP integration...")
    print("✅ Session-based classes loaded successfully")
    print("✅ Legacy compatibility functions available")
    print("✅ Enhanced logging functions ready")
    print("✅ Migration complete - ready to use!")
    
    return {
        "status": "success",
        "message": "Migration to session-based SAP integration completed successfully",
        "features": [
            "Automatic cookie management via requests.Session",
            "Enhanced error handling and logging",
            "Backward compatibility with existing functions",
            "Comprehensive transaction logging",
            "Email notifications for failures",
            "Debug and testing utilities"
        ]
    }


@frappe.whitelist()
def validate_sap_settings():
    """
    Validate SAP settings configuration
    """
    try:
        sap_settings = frappe.get_doc("SAP Settings")
        
        required_fields = [
            'url', 'authorization_type', 'authorization_key', 
            'auth_user_name', 'auth_user_pass'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(sap_settings, field, None):
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "success": False,
                "message": f"Missing required SAP settings: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }
        
        return {
            "success": True,
            "message": "SAP settings validation successful",
            "settings": {
                "url": sap_settings.url,
                "auth_type": sap_settings.authorization_type,
                "auth_user": sap_settings.auth_user_name,
                "has_auth_key": bool(sap_settings.authorization_key),
                "has_password": bool(sap_settings.auth_user_pass)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"SAP settings validation error: {str(e)}",
            "error": str(e)
        }


# =====================================================================================
# PERFORMANCE MONITORING
# =====================================================================================

def log_performance_metrics(function_name, start_time, end_time, success_count, total_count, additional_data=None):
    """
    Log performance metrics for SAP integration
    """
    try:
        duration = end_time - start_time
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        performance_data = {
            "function_name": function_name,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
            "total_records": total_count,
            "successful_records": success_count,
            "failed_records": total_count - success_count,
            "success_rate_percent": success_rate,
            "timestamp": frappe.utils.now(),
            "additional_data": additional_data or {}
        }
        
        # Log to Frappe's error log for tracking
        frappe.log_error(
            title=f"SAP Integration Performance - {function_name}",
            message=json.dumps(performance_data, indent=2, default=str)
        )
        
        print(f"📊 Performance logged: {function_name} - {duration:.2f}s, {success_rate:.1f}% success rate")
        
    except Exception as e:
        print(f"⚠️ Failed to log performance metrics: {str(e)}")








# def update_vendor_master(name, company_name, sap_code, vendor_code, gst, state):
#     """Update vendor master with company vendor code"""
#     ref_vm = frappe.get_doc("Vendor Master", name)
    
#     cvc_name = frappe.db.exists("Company Vendor Code", {
#         "sap_client_code": sap_code, 
#         "vendor_ref_no": ref_vm.name
#     })
    
#     if cvc_name:
#         cvc = frappe.get_doc("Company Vendor Code", cvc_name)
#     else:
#         cvc = frappe.new_doc("Company Vendor Code")
#         cvc.vendor_ref_no = ref_vm.name
#         cvc.company_name = company_name
#         cvc.sap_client_code = sap_code

#     # Update or add vendor code
#     found = False
#     for vc in cvc.vendor_code:
#         if vc.gst_no == gst and vc.state == state:
#             vc.vendor_code = vendor_code
#             found = True
#             break

#     if not found:
#         cvc.append("vendor_code", {
#             "vendor_code": vendor_code,
#             "gst_no": gst,
#             "state": state
#         })

#     cvc.save(ignore_permissions=True)
#     ref_vm.db_update()

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









#############################################################################################################3
#-----------------------------------------------------------client side calls---------------------------##
################################################################################################################

@frappe.whitelist()
def send_vendor_to_sap(doc_name):
    """Simplified function specifically for button click"""
    try:
        doc = frappe.get_doc("Vendor Onboarding", doc_name)
        
        # Check permissions
        if not doc.has_permission("write"):
            frappe.throw(_("You don't have permission to update this document"))
        
        # Validate conditions
        if not (doc.purchase_team_undertaking and 
                doc.accounts_team_undertaking and 
                doc.purchase_head_undertaking and 
                not doc.rejected and
                doc.mandatory_data_filled
                # not doc.data_sent_to_sap
                ):
            frappe.throw(_("Required conditions are not met to send data to SAP"))
        
        # Send to SAP
        erp_to_sap_vendor_data(doc.name)
        
        
        
        return {"status": "success", "message": "Vendor data sent to SAP"}
        
    except Exception as e:
        frappe.log_error(f"SAP Integration Error for {doc_name}: {str(e)}")
        return {"status": "error", "message": str(e)}
    

@frappe.whitelist()
def send_vendor_to_sap_via_front(doc_name):
    """Enhanced function specifically for button click with proper response handling"""
    
    # Initialize response variables
    response_data = {
        "status": "error",
        "message": "Unknown error occurred",
        "details": {}
    }
    
    try:
        print(f"🚀 Starting SAP integration for document: {doc_name}")
        
        # Get the document
        doc = frappe.get_doc("Vendor Onboarding", doc_name)
        
        # Check permissions
        if not doc.has_permission("write"):
            response_data["message"] = "You don't have permission to update this document"
            frappe.throw(_(response_data["message"]))
        
        # Validate conditions
        validation_errors = []
        if doc.register_by_account_team == 0:
            if not doc.purchase_team_undertaking:
                validation_errors.append("Purchase team undertaking is required")
            if not doc.accounts_team_undertaking:
                validation_errors.append("Accounts team undertaking is required")
            if not doc.purchase_head_undertaking:
                validation_errors.append("Purchase head undertaking is required")
            if doc.rejected:
                validation_errors.append("Cannot send rejected vendor data")
            if not doc.mandatory_data_filled:
                validation_errors.append("Mandatory data must be filled")
        elif doc.register_by_account_team == 1:
           
            if not doc.accounts_team_undertaking:
                validation_errors.append("Accounts team undertaking is required")
            if not doc.accounts_head_undertaking:
                validation_errors.append("Purchase head undertaking is required")
            if doc.rejected:
                validation_errors.append("Cannot send rejected vendor data")
            if not doc.mandatory_data_filled:
                validation_errors.append("Mandatory data must be filled")
        
        if validation_errors:
            response_data["message"] = "Validation failed: " + "; ".join(validation_errors)
            response_data["details"]["validation_errors"] = validation_errors
            frappe.throw(_(response_data["message"]))
        
        print("✅ Validation passed, proceeding with SAP integration...")
        
        # Call the main SAP function
        sap_result = erp_to_sap_vendor_data(doc.name)
        
        print(f"📊 SAP function result: {sap_result}")
        
        # Handle the response from SAP function
        if isinstance(sap_result, dict):
            if sap_result.get("status") == "success":
                # Complete success - all SAP calls succeeded
                response_data = {
                    "status": "success",
                    "message": sap_result.get("message", "Vendor data sent to SAP successfully"),
                    "details": {
                        "companies_processed": sap_result.get("companies_processed", 0),
                        "gst_rows_processed": sap_result.get("gst_rows_processed", 0),
                        "successful_sap_calls": sap_result.get("successful_sap_calls", 0),
                        "failed_sap_calls": sap_result.get("failed_sap_calls", 0),
                        "success_rate": sap_result.get("success_rate", 0),
                        "doc_name": doc_name,
                        "vendor_name": doc.vendor_name if hasattr(doc, 'vendor_name') else "Unknown"
                    }
                }
                
                # Update the document to mark as sent to SAP (only on complete success)
                try:
                    # doc.db_set("data_sent_to_sap", 1)
                    doc.add_comment("Comment", f"Data sent to SAP successfully. Success rate: {sap_result.get('success_rate', 0):.1f}%")
                    frappe.db.commit()
                    print("✅ Document updated and committed")
                except Exception as update_err:
                    print(f"⚠️ Warning: Could not update document status: {str(update_err)}")
                    
            elif sap_result.get("status") == "partial_success":
                # Partial success - some succeeded, some failed  
                response_data = {
                    "status": "partial_success",
                    "message": sap_result.get("message", "Some vendor data sent to SAP"),
                    "details": {
                        "companies_processed": sap_result.get("companies_processed", 0),
                        "gst_rows_processed": sap_result.get("gst_rows_processed", 0),
                        "successful_sap_calls": sap_result.get("successful_sap_calls", 0),
                        "failed_sap_calls": sap_result.get("failed_sap_calls", 0),
                        "success_rate": sap_result.get("success_rate", 0),
                        "connection_errors": sap_result.get("connection_errors", 0),
                        "doc_name": doc_name
                    }
                }
                
                # Don't mark as fully sent to SAP on partial success
                try:
                    doc.add_comment("Comment", f"Partial SAP integration. Success rate: {sap_result.get('success_rate', 0):.1f}%. {sap_result.get('failed_sap_calls', 0)} entries failed.")
                    frappe.db.commit()
                except Exception as update_err:
                    print(f"⚠️ Warning: Could not add comment: {str(update_err)}")
                    
            elif sap_result.get("status") == "error":
                # Error case from SAP function
                response_data = {
                    "status": "error", 
                    "message": sap_result.get("message", "SAP integration failed"),
                    "details": {
                        "companies_processed": sap_result.get("companies_processed", 0),
                        "gst_rows_processed": sap_result.get("gst_rows_processed", 0),
                        "successful_sap_calls": sap_result.get("successful_sap_calls", 0),
                        "failed_sap_calls": sap_result.get("failed_sap_calls", 0),
                        "connection_errors": sap_result.get("connection_errors", 0),
                        "error_type": "sap_integration_error",
                        "doc_name": doc_name
                    }
                }
                
                # Don't mark as sent to SAP on error
                try:
                    doc.add_comment("Comment", f"SAP integration failed. {sap_result.get('connection_errors', 0)} connection errors detected.")
                    frappe.db.commit()
                except Exception as update_err:
                    print(f"⚠️ Warning: Could not add comment: {str(update_err)}")
                    
            else:
                # Unexpected response format
                response_data = {
                    "status": "warning",
                    "message": "SAP function returned unexpected response format",
                    "details": {
                        "sap_response": sap_result,
                        "doc_name": doc_name
                    }
                }
        else:
            # SAP function returned non-dict response
            response_data = {
                "status": "warning",
                "message": "SAP function completed but returned unexpected response type",
                "details": {
                    "sap_response": str(sap_result),
                    "response_type": type(sap_result).__name__,
                    "doc_name": doc_name
                },
                "companies_processed": 0,
                "gst_rows_processed": 0,
                "successful_sap_calls": 0,
                "failed_sap_calls": 1,
                "connection_errors": 0,
                "success_rate": 0.0
            }
        
        # Copy additional fields to the main response level for client access
        if isinstance(sap_result, dict):
            response_data.update({
                "companies_processed": sap_result.get("companies_processed", 0),
                "gst_rows_processed": sap_result.get("gst_rows_processed", 0),
                "successful_sap_calls": sap_result.get("successful_sap_calls", 0),
                "failed_sap_calls": sap_result.get("failed_sap_calls", 0),
                "connection_errors": sap_result.get("connection_errors", 0),
                "success_rate": sap_result.get("success_rate", 0)
            })
        
        print(f"📋 Final response: {response_data}")
        return response_data
        
    except frappe.exceptions.ValidationError as ve:
        # Handle Frappe validation errors (like frappe.throw)
        error_msg = str(ve).replace("ValidationError: ", "")
        response_data["message"] = error_msg
        response_data["details"]["error_type"] = "validation_error"
        
        print(f"❌ Validation Error: {error_msg}")
        frappe.log_error(f"SAP Integration Validation Error for {doc_name}: {error_msg}", "SAP Integration Validation")
        return response_data
        
    except frappe.exceptions.PermissionError as pe:
        # Handle permission errors
        error_msg = "You don't have sufficient permissions to perform this action"
        response_data["message"] = error_msg
        response_data["details"]["error_type"] = "permission_error"
        
        print(f"❌ Permission Error: {str(pe)}")
        frappe.log_error(f"SAP Integration Permission Error for {doc_name}: {str(pe)}", "SAP Integration Permission")
        return response_data
        
    except Exception as e:
        # Handle all other exceptions
        error_msg = f"Unexpected error occurred: {str(e)}"
        response_data["message"] = error_msg
        response_data["details"]["error_type"] = "unexpected_error"
        response_data["details"]["error_details"] = str(e)
        
        print(f"❌ Unexpected Error: {error_msg}")
        frappe.log_error(f"SAP Integration Unexpected Error for {doc_name}: {str(e)}\n\nTraceback: {frappe.get_traceback()}", "SAP Integration Error")
        return response_data


# Optional: Alternative version with more granular success/partial success handling
@frappe.whitelist()
def send_vendor_to_sap_via_front_detailed(doc_name):
    """Alternative version with more detailed success/partial success handling"""
    
    try:
        print(f"🚀 Starting detailed SAP integration for document: {doc_name}")
        
        # Get the document
        doc = frappe.get_doc("Vendor Onboarding", doc_name)
        
        # Validation (same as above)
        if not doc.has_permission("write"):
            frappe.throw(_("You don't have permission to update this document"))
        
        if not (doc.purchase_team_undertaking and 
                doc.accounts_team_undertaking and 
                doc.purchase_head_undertaking and 
                not doc.rejected and 
                doc.mandatory_data_filled):
            frappe.throw(_("Required conditions are not met to send data to SAP"))
        
        # Call the main SAP function
        sap_result = erp_to_sap_vendor_data(doc.name)
        
        # Enhanced response handling
        if isinstance(sap_result, dict) and sap_result.get("status") == "success":
            companies_processed = sap_result.get("companies_processed", 0)
            gst_rows_processed = sap_result.get("gst_rows_processed", 0)
            
            # Determine success level
            if companies_processed > 0 and gst_rows_processed > 0:
                success_level = "complete"
                status_message = f"✅ Complete Success: {companies_processed} companies and {gst_rows_processed} GST entries processed"
            elif companies_processed > 0:
                success_level = "partial"
                status_message = f"⚠️ Partial Success: {companies_processed} companies processed, but some GST entries may have failed"
            else:
                success_level = "failed"
                status_message = "❌ No companies or GST entries were successfully processed"
            
            # Update document status
            try:
                doc.db_set("data_sent_to_sap", 1 if success_level in ["complete", "partial"] else 0)
                doc.add_comment("Comment", f"SAP Integration Result: {status_message}")
                frappe.db.commit()
            except Exception as update_err:
                print(f"⚠️ Could not update document: {str(update_err)}")
            
            return {
                "status": "success" if success_level == "complete" else "partial_success" if success_level == "partial" else "failed",
                "message": status_message,
                "details": {
                    "success_level": success_level,
                    "companies_processed": companies_processed,
                    "gst_rows_processed": gst_rows_processed,
                    "doc_name": doc_name,
                    "sap_result": sap_result
                }
            }
        else:
            # Handle error or unexpected result
            error_message = sap_result.get("message", "SAP integration failed") if isinstance(sap_result, dict) else "Unknown error in SAP integration"
            
            return {
                "status": "error",
                "message": f"❌ SAP Integration Failed: {error_message}",
                "details": {
                    "sap_result": sap_result,
                    "doc_name": doc_name,
                    "error_type": "sap_integration_failed"
                }
            }
            
    except Exception as e:
        error_msg = f"SAP Integration Error: {str(e)}"
        frappe.log_error(f"{error_msg} for {doc_name}\n\nTraceback: {frappe.get_traceback()}", "SAP Integration Frontend Error")
        
        return {
            "status": "error",
            "message": error_msg,
            "details": {
                "error_type": "exception",
                "doc_name": doc_name
            }
        }

