import frappe
import json
from datetime import datetime
from frappe import _
from vms.APIs.material_onboarding.material_master_onboarding_field_map import MATERIAL_FIELDS, MATERIAL_ONBOARDING_FIELDS




"""
Material Onboarding SAP Integration
Similar to Vendor Onboarding SAP Integration
Sends material data from ERP to SAP and logs all transactions
"""

import frappe
from frappe import _
import json
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from requests.exceptions import RequestException


# =====================================================================================
# UTILITY FUNCTIONS
# =====================================================================================

def safe_get_doc(doctype, name):
    """Safely get document or return None"""
    try:
        return frappe.get_doc(doctype, name) if name else None
    except Exception as e:
        print(f"❌ Error getting {doctype} {name}: {str(e)}")
        return None


def safe_get(obj, attr, default=""):
    """Safely get attribute from object"""
    try:
        val = getattr(obj, attr, default)
        return val if val is not None else default
    except:
        return default


def safe_get_child(obj, list_name, index, attr, default=""):
    """Safely get child table attribute"""
    try:
        return getattr(getattr(obj, list_name)[index], attr) or default
    except (AttributeError, IndexError, TypeError):
        return default
    

def safe_get_value(doctype, filters, fieldname):
    """Safely get a value from database"""
    try:
        return frappe.get_value(doctype, filters, fieldname) or ""
    except Exception as e:
        print(f"❌ Error getting value from {doctype}: {str(e)}")
        return ""
        

# =====================================================================================
# SESSION-BASED SAP INTEGRATION CLASS
# =====================================================================================

class SAPSessionManager:
    """
    Manages SAP sessions for Material Onboarding CSRF token and cookie handling
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
            print("✅ SAP settings initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize SAP settings: {str(e)}"
            print(f"❌ {error_msg}")
            frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "SAP Settings Init Error")
            raise
    
    def create_session(self):
        """Create a new SAP session and fetch CSRF token"""
        try:
            self.session = requests.Session()
            print(f"🔐 Creating new SAP session for client code: {self.sap_client_code}")
            
            csrf_result = self._fetch_csrf_token()
            
            if csrf_result["success"]:
                self.csrf_token = csrf_result["csrf_token"]
                print(f"✅ SAP session created successfully")
                return {"success": True}
            else:
                error_msg = csrf_result.get("error", "Unknown error")
                print(f"❌ Failed to create SAP session: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            error_msg = f"Exception during session creation: {str(e)}"
            print(f"❌ {error_msg}")
            frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "SAP Session Creation Error")
            return {"success": False, "error": error_msg}
    
    def _fetch_csrf_token(self):
        """Fetch CSRF token from SAP server"""
        try:
            url = f"{self.sap_settings.mo_sap_link}{self.sap_client_code}"
            
            csrf_headers = {'X-CSRF-Token': 'FETCH'}
            
            print(f"🔑 Fetching CSRF token from: {url}")
            print(f"🔑 User: {self.sap_settings.auth_user_name}")
            
            response = self.session.get(
                url, 
                headers=csrf_headers, 
                auth=self.auth, 
                timeout=30
            )
            
            print(f"🔑 CSRF Response Status: {response.status_code}")
            print(f"🔑 Session Cookies Count: {len(self.session.cookies)}")
            
            for cookie in self.session.cookies:
                print(f"🍪 Cookie: {cookie.name} = {cookie.value}")
            
            if response.status_code == 200:
                csrf_token = response.headers.get('x-csrf-token')
                
                if csrf_token:
                    print(f"✅ CSRF Token obtained: {csrf_token}")
                    
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
                    
                    return {"success": True, "csrf_token": csrf_token}
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
    
    def send_data(self, data):
        """Send data to SAP using the established session"""
        if not self.session or not self.csrf_token:
            return {"success": False, "error": "Session not initialized. Call create_session() first."}
        
        try:
            url = f"{self.sap_settings.mo_sap_link}{self.sap_client_code}"
            
            headers = {
                'X-CSRF-Token': self.csrf_token,
                'Content-Type': 'application/json;charset=utf-8',
                'Accept': 'application/json'
            }
            
            print(f"📤 Sending data to SAP: {url}")
            print(f"📦 Payload preview: {json.dumps(data, indent=2)[:500]}...")
            
            response = self.session.post(
                url,
                headers=headers,
                auth=self.auth,
                json=data,
                timeout=60
            )
            
            print(f"📥 SAP Response Status: {response.status_code}")
            print(f"📥 SAP Response: {response.text[:500]}...")
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    return {"success": True, "data": response_data, "status_code": response.status_code}
                except:
                    return {"success": True, "data": response.text, "status_code": response.status_code}
            else:
                error_msg = f"SAP returned status {response.status_code}: {response.text}"
                return {"success": False, "error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.Timeout:
            error_msg = "Request to SAP timed out"
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Error sending data to SAP: {str(e)}"
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
# PAYLOAD BUILDER
# =====================================================================================

def build_material_payload(requestor_doc, material_master_doc, onboarding_doc):
    """
    Build the SAP payload for material onboarding
    Returns: dict with material data structure
    """
    try:
        print("=" * 80)
        print("BUILDING MATERIAL PAYLOAD")
        print("=" * 80)
        
        # Use the documents passed as parameters instead of fetching again
        requestor = requestor_doc
        material_master = material_master_doc
        onboarding = onboarding_doc
        
        # Get SAP Settings
        sap_settings = safe_get_doc("SAP Settings", "SAP Settings")
        
        # Initialize variables
        sap_client_code = ""
        material_items = []
        
        # Process material request items
        for item in safe_get(requestor, "material_request", []):
            material_items.append({
                "material_name_description": safe_get(item, "material_name_description"),
                "material_code_revised": safe_get(item, "material_code_revised"),
                "company_code": safe_get(item, "company_name"),
                "plant_name": safe_get(item, "plant"),
                "material_category": safe_get(item, "material_category"),
                "material_type": safe_get(item, "material_type"),
                "unit_of_measure": safe_get(item, "unit_of_measure"),
                "comment_by_user": safe_get(item, "comment_by_user"),
                "material_specifications": safe_get(item, "material_specifications")
            })
            
            # Get SAP client code from first item's company
            if not sap_client_code and safe_get(item, "company_name"):
                company_doc = safe_get_doc("Company Master", safe_get(item, "company_name"))
                if company_doc:
                    sap_client_code = safe_get(company_doc, "sap_client_code")
        
        print("SAP CLIENT CODE--->", sap_client_code)
        
        # Get company code from first material request item
        company_code = safe_get_child(requestor, "material_request", 0, "company_name")
        
        if not company_code:
            frappe.throw("Company Code is missing from material request item.")
        
        # Get first material item for reference
        first_item = material_items[0] if material_items else {}
        
        # Build field values with safe gets
        availability_check = safe_get(material_master, "availability_check")
        bukrs = company_code
        batch_value = safe_get(material_master, "batch_requirements_yn")
        batch_management_indicator = "X" if batch_value == "Yes" and availability_check == "CH" else ""
        
        inspection_1 = safe_get(onboarding, "inspection_require")
        inspection_sap = "X" if inspection_1 == "Yes" else ""
        inspection_01 = "01" if safe_get(onboarding, "incoming_inspection_01") else ""
        inspection_09 = "09" if safe_get(onboarding, "incoming_inspection_09") else ""
        
        serial_number_profile = safe_get(material_master, "serial_number_profile")
        serial_number = "" if serial_number_profile == "No" else serial_number_profile
        
        # Get codes from master tables using safe_get_value
        material_type_code = safe_get_value("Material Type Master", 
            {"name": first_item.get("material_type")}, "material_type") if first_item.get("material_type") else ""
        
        plant_code = safe_get_value("Plant Master", 
            {"name": first_item.get("plant_name")}, "plant_code") if first_item.get("plant_name") else ""
        
        category_code = safe_get_value("Material Category Master", 
            {"name": first_item.get("material_category")}, "material_category_code") if first_item.get("material_category") else ""
        
        storage_code = safe_get_value("Storage Location Master", 
            {"name": safe_get(material_master, "storage_location")}, "storage_location") if safe_get(material_master, "storage_location") else ""
        
        purchase_group_code = safe_get_value("Purchase Group Master", 
            {"name": safe_get(material_master, "purchasing_group")}, "purchase_group_code") if safe_get(material_master, "purchasing_group") else ""
        
        division_code = safe_get_value("Division Master", 
            {"name": safe_get(material_master, "division")}, "division_code") if safe_get(material_master, "division") else ""
        
        material_group_code = safe_get_value("Material Group Master", 
            {"name": safe_get(material_master, "material_group")}, "material_group_name") if safe_get(material_master, "material_group") else ""
        
        mrp_code = safe_get_value("MRP Type Master", 
            {"name": safe_get(material_master, "mrp_type")}, "mrp_code") if safe_get(material_master, "mrp_type") else ""
        
        valuation_class_code = safe_get_value("Valuation Class Master", 
            {"name": safe_get(onboarding, "valuation_class")}, "valuation_class_code") if safe_get(onboarding, "valuation_class") else ""
        
        material_code = safe_get(material_master, "material_code_revised")
        
        mrp_controller_name = safe_get_value("MRP Controller Master", 
            {"name": safe_get(material_master, "mrp_controller_revised")}, "mrp_controller") if safe_get(material_master, "mrp_controller_revised") else ""
        
        # Build the main data structure
        data = {
            "Reqno": safe_get(requestor, "request_id"),
            "Bukrs": bukrs,
            "Matnr": material_code,
            "Adrnr": "",
            "Matkey": "",
            "Mat": category_code,
            "Mtart": material_type_code,
            "Mbrsh": "P",
            "Werks": plant_code,
            "Lgort": storage_code,
            "Maktx": first_item.get("material_name_description", ""),
            "Meins": first_item.get("unit_of_measure", ""),
            "Matkl": material_group_code,
            "Spart": division_code,
            "Brgew": "",
            "Ntgew": "",
            "Gewei": "",
            "Bmatnr": "",
            "Xchpf": batch_management_indicator,
            "Mtvfp": safe_get(material_master, "availability_check"),
            "Ekgrp": purchase_group_code,
            "Bstme": safe_get(material_master, "purchase_uom"),
            "Umrez": safe_get(material_master, "numerator_purchase_uom"),
            "Umren": safe_get(material_master, "denominator_purchase_uom"),
            "Webaz": safe_get(material_master, "gr_processing_time"),
            "Dismm": mrp_code,
            "Dispo": mrp_controller_name,
            "Disls": safe_get(material_master, "lot_size_key"),
            "Bstma": "",
            "Mabst": "",
            "Beskz": safe_get(material_master, "procurement_type"),
            "Lgortep": "",
            "Plifz": safe_get(material_master, "lead_time"),
            "Fhori": safe_get(material_master, "scheduling_margin_key"),
            "Eisbe": "",
            "Mhdrz": safe_get(onboarding, "minimum_remaining_shell_life"),
            "Mhdhb": safe_get(onboarding, "total_shell_life"),
            "Iprkz": safe_get(onboarding, "expiration_date"),
            "Prctr": safe_get(onboarding, "profit_center"),
            "Ausme": safe_get(material_master, "issue_unit"),
            "Umren1": safe_get(material_master, "numerator_issue_uom"),
            "Umrez1": safe_get(material_master, "denominator_issue_uom"),
            "Qmatv": inspection_sap,
            "Qminst": inspection_01,
            "Qminst1": inspection_09,
            "Prfrq": safe_get(onboarding, "inspection_interval"),
            "Bklas": valuation_class_code,
            "Vprsv": safe_get(onboarding, "price_control"),
            "Ncost": safe_get(onboarding, "do_not_cost"),
            "Ekalr": "X",
            "Hkmat": "X",
            "Oldmat": safe_get(material_master, "old_material_code"),
            "Sernp": serial_number,
            "Taxim": "1",
            "Steuc": "",
            "Aedat": "",
            "Aezet": "",
            "Aenam": "",
            "Emailid": "",
            "Storecom": safe_get(onboarding, "comment_by_store"),
            "Purcom": safe_get(material_master, "purchase_order_text"),
            "Taxcom": "",
            "Div": "",
            "Ygroup": "",
            "Sgroup": "",
            "Tcode": "", 
            "Ekwsl": safe_get(material_master, "purchasing_value_key"),
            "Mstcom": "",
            "Qacom": "",
            "Class": safe_get(material_master, "class_type"),
            "Klart": safe_get(material_master, "class_number"),
            "Disgr": safe_get(material_master, "mrp_group"),
            "Lgpro": "",
            "Serlv": ""
        }
        
        payload = {
            "ZMATSet": [data]
        }
        
        print(f"✅ Payload built successfully")
        print(f"📦 Material Code: {data.get('Matnr', 'N/A')}")
        print(f"📦 Material Name: {data.get('Maktx', 'N/A')}")
        print(f"📦 Request ID: {data.get('Reqno', 'N/A')}")
        print("=" * 80)
        
        return payload
        
    except Exception as e:
        error_msg = f"Error building material payload: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "Material Payload Build Error")
        print(f"❌ PAYLOAD BUILD ERROR: {error_msg}")
        return None




        

# =====================================================================================
# SAP LOG CREATION
# =====================================================================================

def create_mo_sap_log(requestor_ref, material_onboarding_link, payload, sap_response, status, direction="ERP to SAP"):
    """
    Create MO SAP Logs entry
    """
    try:
        log = frappe.new_doc("MO SAP Logs")
        log.requestor_ref = requestor_ref
        log.material_onboarding_link = material_onboarding_link or ""
        log.direction = direction
        log.status = status
        
        if direction == "ERP to SAP":
            log.erp_to_sap_data = json.dumps(payload, indent=2, ensure_ascii=False) if payload else ""
            log.sap_response = json.dumps(sap_response, indent=2, ensure_ascii=False) if sap_response else ""
        
        # Create transaction summary
        summary = create_transaction_summary(requestor_ref, material_onboarding_link, payload, sap_response, status)
        log.total_transaction = summary
        
        log.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"✅ MO SAP Log created: {log.name}")
        return log.name
        
    except Exception as e:
        error_msg = f"Failed to create MO SAP Log: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "MO SAP Log Creation Error")
        print(f"❌ {error_msg}")
        return None


def create_transaction_summary(requestor_ref, material_onboarding_link, payload, sap_response, status):
    """Create a formatted transaction summary"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract key info from payload
    material_code = ""
    material_name = ""
    request_id = ""
    
    if payload and "ZMATSet" in payload and len(payload["ZMATSet"]) > 0:
        mat_data = payload["ZMATSet"][0]
        material_code = mat_data.get("Matnr", "")
        material_name = mat_data.get("Maktx", "")
        request_id = mat_data.get("Reqno", "")
    
    # Extract SAP response info
    sap_message = ""
    sap_text = ""
    
    if isinstance(sap_response, dict):
        if 'd' in sap_response:
            sap_message = sap_response['d'].get('Zmsg', '')
            sap_text = sap_response['d'].get('Ztext', '')
        else:
            sap_message = sap_response.get('Zmsg', '')
            sap_text = sap_response.get('Ztext', '')
    
    summary = {
        "transaction_summary": {
            "status": status,
            "material_code": material_code,
            "material_name": material_name,
            "request_id": request_id,
            "sap_message": sap_message,
            "sap_text": sap_text,
            "timestamp": timestamp,
            "integration_method": "API-Based"
        },
        "request_details": {
            "requestor_ref": requestor_ref,
            "material_onboarding_link": material_onboarding_link,
            "request_id": request_id,
            "payload": payload
        },
        "response_details": {
            "status": status,
            "material_code": material_code,
            "sap_message": sap_message,
            "sap_text": sap_text,
            "response_body": sap_response if sap_response else {}
        }
    }
    
    return json.dumps(summary, indent=2, ensure_ascii=False)


# =====================================================================================
# MAIN INTEGRATION FUNCTION
# =====================================================================================

@frappe.whitelist(allow_guest=True)
def erp_to_sap_material_onboarding(requestor_ref):
    """
    Main function to send Material Onboarding data to SAP
    Similar structure to Vendor Onboarding SAP integration
    """
    print("=" * 80)
    print("ERP TO SAP MATERIAL ONBOARDING - STARTING")
    print(f"Requestor Reference: {requestor_ref}")
    print("=" * 80)
    
    successful_calls = 0
    failed_calls = 0
    
    try:
        # Get main documents
        requestor = safe_get_doc("Requestor Master", requestor_ref)
        if not requestor:
            frappe.throw(f"Requestor Master not found: {requestor_ref}")
        
        material_master = safe_get_doc("Material Master", safe_get(requestor, "material_master_ref_no"))
        if not material_master:
            frappe.throw(f"Material Master not found for requestor: {requestor_ref}")
        
        onboarding = safe_get_doc("Material Onboarding", safe_get(requestor, "material_onboarding_ref_no"))
        if not onboarding:
            frappe.throw(f"Material Onboarding not found for requestor: {requestor_ref}")
        
        # Get SAP client code from material request
        sap_client_code = ""
        if requestor.material_request and len(requestor.material_request) > 0:
            company_code = requestor.material_request[0].company_name
            try:
                company_doc = frappe.get_doc("Company Master", company_code)
                sap_client_code = company_doc.sap_client_code or ""
            except Exception as e:
                frappe.log_error(f"Company Master fetch failed for {company_code}", str(e))
        
        if not sap_client_code:
            frappe.throw("SAP Client Code not found. Please check Company Master configuration.")
        
        print(f"✅ SAP Client Code: {sap_client_code}")
        
        # Build payload
        payload = build_material_payload(requestor, material_master, onboarding)
        
        if not payload:
            error_msg = "Failed to build material payload"
            create_mo_sap_log(requestor_ref, onboarding.name, None, {"error": error_msg}, "Payload Build Failed")
            frappe.throw(error_msg)
        
        # Create SAP session
        sap_session = SAPSessionManager(sap_client_code)
        session_result = sap_session.create_session()
        
        if not session_result["success"]:
            error_msg = f"Failed to create SAP session: {session_result.get('error', 'Unknown error')}"
            create_mo_sap_log(requestor_ref, onboarding.name, payload, {"error": error_msg}, "Session Failed")
            frappe.throw(error_msg)
        
        # Send data to SAP
        print(f"🚀 Sending material data to SAP...")
        result = sap_session.send_data(payload)
        
        # Close session
        sap_session.close_session()
        
        # Handle result
        if result["success"]:
            successful_calls += 1
            
            # Extract material code from response
            material_code = ""
            sap_message = ""
            sap_text = ""
            
            if isinstance(result.get("data"), dict):
                response_data = result["data"]
                if 'd' in response_data:
                    material_code = response_data['d'].get('Matnr', '')
                    sap_message = response_data['d'].get('Zmsg', '')
                    sap_text = response_data['d'].get('Ztext', '')
                else:
                    material_code = response_data.get('Matnr', '')
                    sap_message = response_data.get('Zmsg', '')
                    sap_text = response_data.get('Ztext', '')
            
            print(f"✅ SAP Integration Successful")
            print(f"📦 Material Code: {material_code}")
            print(f"📝 SAP Message: {sap_message}")
            print(f"📝 SAP Text: {sap_text}")
            
            # Update Requestor Master
            requestor.zmsg = sap_message
            requestor.maktx = material_code
            requestor.ztext = sap_text
            requestor.sap_summary = json.dumps(result.get("data", {}), indent=2)
            requestor.approval_status = "Sent to SAP"
            requestor.save(ignore_permissions=True)
            
            # Create success log
            create_mo_sap_log(requestor_ref, onboarding.name, payload, result.get("data"), "Success")
            
            frappe.db.commit()
            
            return {
                "status": "success",
                "message": "Material successfully sent to SAP",
                "material_code": material_code,
                "sap_message": sap_message,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls
            }
        else:
            failed_calls += 1
            error_msg = result.get("error", "Unknown error")
            
            print(f"❌ SAP Integration Failed: {error_msg}")
            
            # Create failure log
            create_mo_sap_log(requestor_ref, onboarding.name, payload, {"error": error_msg}, "Failed")
            
            # Update requestor status
            requestor.approval_status = "SAP Error"
            requestor.save(ignore_permissions=True)
            frappe.db.commit()
            
            return {
                "status": "error",
                "message": f"SAP Integration Failed: {error_msg}",
                "successful_calls": successful_calls,
                "failed_calls": failed_calls
            }
            
    except Exception as e:
        failed_calls += 1
        error_msg = f"Exception in Material Onboarding SAP Integration: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "Material Onboarding SAP Error")
        print(f"❌ {error_msg}")
        
        # Try to create error log
        try:
            create_mo_sap_log(requestor_ref, "", None, {"error": error_msg}, "Exception")
        except:
            pass
        
        return {
            "status": "error",
            "message": error_msg,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls
        }


# =====================================================================================
# HELPER FUNCTIONS FOR HOOKS / TRIGGERS
# =====================================================================================

def trigger_mo_sap_integration(doc, method=None):
    """
    Hook function to trigger Material Onboarding SAP integration
    Can be called from Material Onboarding document hooks
    """
    try:
        # Check if material should be sent to SAP
        if (doc.approval_stage == "Approved" and 
            doc.approval_status != "Sent to SAP" and
            doc.requestor_ref_no):
            
            print(f"🎯 Triggering SAP integration for Material Onboarding: {doc.name}")
            
            # Enqueue the SAP integration
            frappe.enqueue(
                method="vms.APIs.sap.erp_to_sap_mo.erp_to_sap_material_onboarding",
                queue='default',
                timeout=600,
                now=False,
                job_name=f'mo_sap_integration_{doc.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                requestor_ref=doc.requestor_ref_no
            )
            
            print(f"✅ SAP integration enqueued for Material Onboarding: {doc.name}")
            
    except Exception as e:
        error_msg = f"Error triggering Material Onboarding SAP integration: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "MO SAP Trigger Error")
        print(f"❌ {error_msg}")


# =====================================================================================
# EMAIL NOTIFICATION FUNCTIONS
# =====================================================================================

def send_mo_success_notification(requestor_ref, material_code, material_name):
    """Send success notification email"""
    try:
        requestor = frappe.get_doc("Requestor Master", requestor_ref)
        email = requestor.contact_information_email
        
        if not email:
            print("⚠️  No email found for requestor")
            return
        
        subject = f"Material Onboarding Successful - {material_name}"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center;">
                <h2 style="color: white; margin: 0;">✅ Material Onboarding Successful</h2>
            </div>
            
            <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e0e0e0;">
                <p>Dear {requestor.requested_by},</p>
                
                <p>Your material onboarding request has been successfully processed and sent to SAP.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Material Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #fff;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Material Code</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{material_code}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Material Name</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{material_name}</td>
                        </tr>
                        <tr style="background-color: #fff;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Request ID</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{requestor.request_id or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Status</td>
                            <td style="padding: 10px; border: 1px solid #ddd;"><span style="color: #28a745; font-weight: bold;">✓ Sent to SAP</span></td>
                        </tr>
                    </table>
                </div>
                
                <p>Your material is now available in the SAP system and can be used for transactions.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>Material Management Team</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                <p>This is an automated notification from the Material Onboarding System</p>
            </div>
        </div>
        """
        
        frappe.custom_sendmail(
            recipients=[email],
            subject=subject,
            message=message,
            delayed=False
        )
        
        print(f"✅ Success notification sent to {email}")
        
    except Exception as e:
        error_msg = f"Failed to send success notification: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "MO Email Notification Error")
        print(f"❌ {error_msg}")


def send_mo_failure_notification(requestor_ref, error_message):
    """Send failure notification email to support team"""
    try:
        requestor = frappe.get_doc("Requestor Master", requestor_ref)
        
        # Get support team emails (customize as needed)
        support_emails = ["sap.support@company.com", "material.team@company.com"]
        
        subject = f"Material Onboarding SAP Error - {requestor.name}"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; text-align: center;">
                <h2 style="color: white; margin: 0;">⚠️ Material Onboarding SAP Error</h2>
            </div>
            
            <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e0e0e0;">
                <p>Dear Support Team,</p>
                
                <p>A material onboarding request has encountered an error during SAP integration.</p>
                
                <div style="background-color: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <h3 style="color: #856404; margin-top: 0;">Error Details</h3>
                    <p style="color: #856404; margin: 0;"><strong>Error:</strong> {error_message}</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Request Information</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #fff;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Requestor Name</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{requestor.requested_by or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Request ID</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{requestor.request_id or 'N/A'}</td>
                        </tr>
                        <tr style="background-color: #fff;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Company</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{requestor.requestor_company or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Department</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{requestor.requestor_department or 'N/A'}</td>
                        </tr>
                        <tr style="background-color: #fff;">
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Email</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{requestor.contact_information_email or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Date</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #d1ecf1; padding: 15px; border-left: 4px solid #0c5460; margin: 20px 0;">
                    <h4 style="color: #0c5460; margin-top: 0;">Next Steps</h4>
                    <ul style="color: #0c5460; margin: 0;">
                        <li>Review the material onboarding details</li>
                        <li>Check SAP connectivity and credentials</li>
                        <li>Verify material data completeness</li>
                        <li>Contact IT team if issue persists</li>
                        <li>Update requestor on the status</li>
                    </ul>
                </div>
                
                <p style="margin-top: 30px;">This requires immediate attention.</p>
                
                <p>Best regards,<br>Material Onboarding System</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                <p>This is an automated notification from the Material Onboarding System</p>
            </div>
        </div>
        """
        
        frappe.custom_sendmail(
            recipients=support_emails,
            subject=subject,
            message=message,
            delayed=False
        )
        
        print(f"✅ Failure notification sent to support team")
        
    except Exception as e:
        error_msg = f"Failed to send failure notification: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "MO Email Notification Error")
        print(f"❌ {error_msg}")


# =====================================================================================
# MANUAL RETRY FUNCTION
# =====================================================================================

@frappe.whitelist()
def retry_mo_sap_integration(requestor_ref):
    """
    Manual retry function for Material Onboarding SAP integration
    Can be called from UI button or workflow
    """
    try:
        print(f"🔄 Manual retry requested for Material Onboarding: {requestor_ref}")
        
        # Check if requestor exists
        if not frappe.db.exists("Requestor Master", requestor_ref):
            return {
                "status": "error",
                "message": f"Requestor Master not found: {requestor_ref}"
            }
        
        # Enqueue the SAP integration
        frappe.enqueue(
            method="vms.APIs.sap.erp_to_sap_mo.erp_to_sap_material_onboarding",
            queue='default',
            timeout=600,
            now=False,
            job_name=f'mo_sap_retry_{requestor_ref}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            requestor_ref=requestor_ref
        )
        
        return {
            "status": "success",
            "message": "SAP integration retry has been queued"
        }
        
    except Exception as e:
        error_msg = f"Error in manual retry: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "MO SAP Retry Error")
        return {
            "status": "error",
            "message": error_msg
        }


# =====================================================================================
# BULK PROCESSING FUNCTION
# =====================================================================================

@frappe.whitelist()
def bulk_process_mo_to_sap(requestor_refs):
    """
    Process multiple Material Onboarding requests to SAP in bulk
    requestor_refs: JSON string or list of requestor references
    """
    try:
        if isinstance(requestor_refs, str):
            requestor_refs = json.loads(requestor_refs)
        
        if not isinstance(requestor_refs, list):
            return {
                "status": "error",
                "message": "Invalid input format. Expected list of requestor references."
            }
        
        print(f"📦 Bulk processing {len(requestor_refs)} Material Onboarding requests")
        
        results = {
            "total": len(requestor_refs),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for requestor_ref in requestor_refs:
            try:
                # Enqueue each integration
                frappe.enqueue(
                    method="vms.APIs.sap.erp_to_sap_mo.erp_to_sap_material_onboarding",
                    queue='default',
                    timeout=600,
                    now=False,
                    job_name=f'mo_sap_bulk_{requestor_ref}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    requestor_ref=requestor_ref
                )
                
                results["success"] += 1
                results["details"].append({
                    "requestor_ref": requestor_ref,
                    "status": "queued",
                    "message": "Integration queued successfully"
                })
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "requestor_ref": requestor_ref,
                    "status": "error",
                    "message": str(e)
                })
        
        return {
            "status": "success",
            "message": f"Bulk processing completed. {results['success']} queued, {results['failed']} failed.",
            "results": results
        }
        
    except Exception as e:
        error_msg = f"Error in bulk processing: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "MO Bulk Processing Error")
        return {
            "status": "error",
            "message": error_msg
        }


# =====================================================================================
# STATUS CHECK FUNCTION
# =====================================================================================

@frappe.whitelist()
def check_mo_sap_status(requestor_ref):
    """
    Check the SAP integration status for a Material Onboarding request
    Returns latest log entry and current status
    """
    try:
        # Get requestor
        requestor = frappe.get_doc("Requestor Master", requestor_ref)
        
        # Get latest MO SAP Log
        logs = frappe.get_all(
            "MO SAP Logs",
            filters={"requestor_ref": requestor_ref},
            fields=["name", "status", "direction", "creation", "material_onboarding_link"],
            order_by="creation desc",
            limit=1
        )
        
        if not logs:
            return {
                "status": "no_logs",
                "message": "No SAP logs found for this material onboarding",
                "requestor_status": requestor.approval_status
            }
        
        latest_log = logs[0]
        
        # Get full log details
        log_doc = frappe.get_doc("MO SAP Logs", latest_log.name)
        
        return {
            "status": "success",
            "requestor_status": requestor.approval_status,
            "log_status": latest_log.status,
            "log_name": latest_log.name,
            "log_direction": latest_log.direction,
            "log_created": latest_log.creation,
            "material_onboarding": latest_log.material_onboarding_link,
            "transaction_summary": log_doc.total_transaction if log_doc.total_transaction else None
        }
        
    except Exception as e:
        error_msg = f"Error checking SAP status: {str(e)}"
        frappe.log_error(f"{error_msg}\n\nTraceback: {frappe.get_traceback()}", "MO SAP Status Check Error")
        return {
            "status": "error",
            "message": error_msg
        }



@frappe.whitelist()
def send_sap_duplicate_change_email(doc_name, changed_fields):
    try:
        print("*******SAP TEAM DUPLICATE CHANGE EMAIL HIT********", doc_name)
        
        # Fetch required documents
        requestor = frappe.get_doc("Requestor Master", doc_name)
        mo_doc_name = requestor.material_onboarding_ref_no
        mo_details = frappe.get_doc("Material Onboarding", mo_doc_name)
        request_id = requestor.request_id
        
        # Get SAP team email (primary recipient)
        sap_email = frappe.get_value("Employee", {"designation": "SAP Team"}, "company_email")
        if not sap_email:
            frappe.log_error("No SAP team email found", f"Requestor: {doc_name}")
            return {"status": "fail", "message": _("No SAP team email found")}
        
        # Build CC list
        cc_emails = []
        
        # Add requestor email
        if requestor.contact_information_email:
            cc_emails.append(requestor.contact_information_email)
        
        # Add CP team email
        cp_team = mo_details.approved_by
        if cp_team:
            cp_email = frappe.get_value("Employee", {"user_id": cp_team}, "company_email")
            if cp_email:
                cc_emails.append(cp_email)
        
        # Add reporting head email
        if requestor.immediate_reporting_head:
            cc_email2 = frappe.get_value("Employee", {"name": requestor.immediate_reporting_head}, "company_email")
            if cc_email2:
                cc_emails.append(cc_email2)
        
        # Remove duplicates from CC list
        cc_emails = list(set(cc_emails))
        
        # Build changes HTML
        changes_html = "".join(
            f"<li><strong>{prettify_field_name(f)}:</strong> '{o}' ➜ '{n}'</li>"
            for f, o, n in changed_fields
        )
        
        # Email subject and message
        subject = f"🔄 Changes Detected for Existing Material Request - {request_id}"
        
        message = f"""
            <p>Dear SAP Team,</p>
            <p>The request <strong>{request_id}</strong> was already found in SAP.</p>
            <p>However, the following changes were detected in the latest update:</p>
            <ul>{changes_html}</ul>
            <p>Regards,<br/>ERP System</p>
        """
        
        # Send email using frappe.custom_sendmail
        frappe.custom_sendmail(
            recipients=[sap_email],
            cc=cc_emails,
            subject=subject,
            message=message,
            now=True
        )
        
        print("Duplicate change email sent successfully.")
        return {"status": "success", "message": _("Email sent successfully")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "SAP Duplicate Change Email Error")
        return {"status": "fail", "message": _("Failed to send email.")}
    



@frappe.whitelist()
def send_sap_team_email(doc_name):
    try:
        print("*******SAP TEAM EMAIL HIT********", doc_name)
        
        # Fetch required documents
        requestor = frappe.get_doc("Requestor Master", doc_name)
        print("Requestor--->", requestor)
        
        requestor_name = requestor.requested_by
        request_id = requestor.request_id
        
        # Get SAP team email (primary recipient)
        sap_email = frappe.get_value("Employee Master", {"role": "SAP"}, "email")
        if not sap_email:
            frappe.log_error("No SAP team email found", f"Requestor: {doc_name}")
            return {"status": "fail", "message": _("No SAP team email found")}
        
        # Validate material request exists
        if not requestor.material_request:
            frappe.throw("No material items found in the request.")
            print("No Material Request Child table.")
        
        # Get material details
        material_row = requestor.material_request[0]
        company_code = material_row.company_name or "-"
        company_name = frappe.get_value("Company Master", {"name": company_code}, "company_name")
        plant_name = material_row.plant_name or "-"
        material_type = material_row.material_type or "-"
        material_description = material_row.material_name_description or "-"
        
        # Build CC list
        cc_emails = []
        
        # Add requestor email
        if requestor.contact_information_email:
            cc_emails.append(requestor.contact_information_email)
        
        # Add Material Onboarding approved_by email
        mo_doc_name = requestor.material_onboarding_ref_no
        mo_details = frappe.get_doc("Material Onboarding", mo_doc_name)
        cc_team = mo_details.approved_by_name
        print("CP Team--->", cc_team)
        
        if cc_team:
            cc_email = frappe.get_value("Employee Master", {"name": cc_team}, "email")
            print("CP Team Email--->", cc_email)
            if cc_email:
                cc_emails.append(cc_email)
        
        # Get CP name for email body
        cp_name = frappe.get_value("Employee Master", {"name": cc_team}, "full_name") if cc_team else "N/A"
        print("CP Team Full Name--->", cp_name)
        
        # Add reporting head email
        cc_2 = requestor.immediate_reporting_head
        print("Reporting Head--->", cc_2)
        if cc_2:
            cc_email2 = frappe.get_value("Employee Master", {"name": cc_2}, "email")
            if cc_email2:
                cc_emails.append(cc_email2)
        
        # Remove duplicates from CC list
        cc_emails = list(set(cc_emails))
        
        # Email subject and message
        subject = f"Request for Creating New Material Code in {company_code}-{company_name}"
        
        message = f"""
            <p>Dear SAP Team,</p>
            <p>The following request to generate or create a new material code has been submitted by <strong>{cp_name}</strong>, which was initially requested by <strong>{requestor_name}</strong>.</p>
            <ul>
                <li><strong>Request ID:</strong> {request_id}</li>
                <li><strong>Company:</strong> {company_code} - {company_name}</li>
                <li><strong>Plant:</strong> {plant_name}</li>
                <li><strong>Material Type:</strong> {material_type}</li>
                <li><strong>Material Description:</strong> {material_description}</li>
            </ul>
            <p>Regards,<br/>ERP System</p>
        """
        
        # Send email using frappe.custom_sendmail
        frappe.custom_sendmail(
            recipients=[sap_email],
            cc=cc_emails,
            subject=subject,
            message=message,
            now=True
        )
        
        print("Email Sent Successfully")
        return {"status": "success", "message": _("Email sent successfully.")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "SAP Email Send Failed")
        return {"status": "fail", "message": _("Failed to send email.")}

def prettify_field_name(field_name):
    return field_name.replace("_", " ").title()