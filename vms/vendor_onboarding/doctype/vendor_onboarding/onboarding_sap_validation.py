# Backend API Functions
# Add these to a new file: vms/vendor_onboarding/api/sap_validation_api.py

import frappe
import json
from frappe import _
# from vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding import validate_mandatory_data


@frappe.whitelist()
def get_sap_validation_display_data(onb_ref):
    """
    Get validation data for JavaScript rendering
    No database field updates needed - purely data API
    """
    try:
       
        
        # Get validation result
        result = validate_mandatory_data(onb_ref)
        
        # Prepare data for frontend rendering
        display_data = {
            "validation_passed": result["success"],
            "vendor_type": result.get("vendor_type", "Unknown"),
            "companies_count": len(result.get("data", [])),
            "message": result.get("message", ""),
            "timestamp": frappe.utils.now(),
            "missing_fields_summary": [],
            "total_missing_count": 0
        }
        
        if not result["success"]:
            # Parse missing fields from the message
            missing_fields_text = result.get("message", "")
            if "Missing Mandatory Fields:" in missing_fields_text:
                missing_fields_list = missing_fields_text.replace("Missing Mandatory Fields:\n", "").split("\n")
                clean_fields = [f.strip() for f in missing_fields_list if f.strip()]
                
                display_data["missing_fields_summary"] = clean_fields
                display_data["total_missing_count"] = len(clean_fields)
        
        return {
            "success": True,
            "display_data": display_data,
            "message": "Validation data retrieved successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting validation display data: {str(e)}", "Validation Display Data API")
        return {
            "success": False,
            "message": f"Error retrieving validation data: {str(e)}",
            "display_data": {
                "validation_passed": False,
                "vendor_type": "Unknown",
                "companies_count": 0,
                "message": f"Error: {str(e)}",
                "timestamp": frappe.utils.now(),
                "missing_fields_summary": [],
                "total_missing_count": 0
            }
        }


@frappe.whitelist()
def get_validation_summary_widget(onb_ref):
    """
    Get compact validation summary for dashboard/widget use
    """
    try:
        
        
        result = validate_mandatory_data(onb_ref)
        
        summary = {
            "validation_passed": result["success"],
            "vendor_type": result.get("vendor_type", "Unknown"),
            "companies_count": len(result.get("data", [])),
            "status_text": "Ready for SAP" if result["success"] else "Validation Failed",
            "error_count": 0,
            "timestamp": frappe.utils.now()
        }
        
        if not result["success"]:
            missing_fields_text = result.get("message", "")
            if "Missing Mandatory Fields:" in missing_fields_text:
                missing_fields_list = missing_fields_text.replace("Missing Mandatory Fields:\n", "").split("\n")
                summary["error_count"] = len([f for f in missing_fields_list if f.strip()])
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting validation summary: {str(e)}", "Validation Summary API")
        return {
            "success": False,
            "message": str(e),
            "summary": {
                "validation_passed": False,
                "vendor_type": "Unknown",
                "companies_count": 0,
                "status_text": "Error",
                "error_count": 0,
                "timestamp": frappe.utils.now()
            }
        }


@frappe.whitelist()
def trigger_manual_validation(onb_ref):
    """
    Manually trigger validation and return updated status
    This can be called from a button to force re-validation
    """
    try:
    
        
        # Run validation
        result = validate_mandatory_data(onb_ref)
        
        # Update the mandatory_data_filled field
        onb_doc = frappe.get_doc("Vendor Onboarding", onb_ref)
        onb_doc.mandatory_data_filled = 1 if result["success"] else 0
        onb_doc.save(ignore_permissions=True)
        
        # Return the result for JavaScript to process
        return {
            "success": True,
            "validation_passed": result["success"],
            "message": "Validation completed successfully",
            "validation_result": result
        }
        
    except Exception as e:
        frappe.log_error(f"Error in manual validation trigger: {str(e)}", "Manual Validation Trigger")
        return {
            "success": False,
            "message": f"Error during validation: {str(e)}"
        }


# Optional: Field mapping helper for detailed error display
@frappe.whitelist()
def get_field_doctype_mapping():
    """
    Return field to doctype mapping for better error display
    """
    try:
        field_mapping = {
            # Company and Organization Fields
            "Company Code": "Company Master",
            "Purchase Organization": "Purchase Organization Master", 
            "Account Group": "Account Group Master",
            
            # Vendor Master Fields
            "Vendor Name": "Vendor Master",
            "Mobile Number": "Vendor Master",
            "Primary Email": "Vendor Master",
            
            # Address Fields
            "Address Line 1": "Vendor Onboarding Company Details",
            "Pin Code": "Vendor Onboarding Company Details",
            "City": "Vendor Onboarding Company Details",
            "State": "Vendor Onboarding Company Details",
            "Country": "Vendor Onboarding Company Details",
            
            # Tax and Legal Fields
            "GST Number": "Vendor Onboarding Company Details",
            "PAN Number": "Vendor Onboarding Company Details",
            "Vendor Type": "Vendor Type Master",
            
            # Financial and Payment Fields
            "Reconciliation Account": "Reconciliation Account",
            "Currency": "Vendor Onboarding Payment Details",
            "Payment Terms": "Terms of Payment Master",
            
            # Purchase Fields
            "Purchase Group": "Purchase Group Master",
            "Incoterm Code": "Incoterm Master",
            "Incoterm Description": "Incoterm Master",
            
            # Banking Fields
            "Bank Code": "Bank Master",
            "Bank Name": "Bank Master",
            "Account Number": "Vendor Onboarding Payment Details",
            "IFSC Code": "Vendor Onboarding Payment Details",
            "Account Holder Name": "Vendor Onboarding Payment Details",
            
            # International Banking Fields
            "Beneficiary Name": "International Bank Details",
            "Beneficiary Bank Name": "International Bank Details",
            "Beneficiary Account Number": "International Bank Details",
            "Beneficiary IBAN": "International Bank Details",
            "SWIFT Code": "International Bank Details"
        }
        
        return {
            "success": True,
            "field_mapping": field_mapping
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "field_mapping": {}
        }











@frappe.whitelist()
def get_validation_summary(onb_ref):
    """
    API endpoint to get validation summary without HTML
    Useful for dashboard widgets or quick checks
    """
    try:
        
        
        result = validate_mandatory_data(onb_ref)
        
        # Extract summary information
        summary = {
            "validation_passed": result["success"],
            "vendor_type": result.get("vendor_type", "Unknown"),
            "companies_count": len(result.get("data", [])),
            "error_count": 0,
            "missing_fields": []
        }
        
        if not result["success"]:
            missing_fields_list = result.get("message", "").replace("Missing Mandatory Fields:\n", "").split("\n")
            summary["error_count"] = len([f for f in missing_fields_list if f.strip()])
            summary["missing_fields"] = [f.strip() for f in missing_fields_list if f.strip()][:5]  # First 5 only
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting validation summary: {str(e)}", "Validation Summary API")
        return {
            "success": False,
            "message": str(e)
        }
    











    # Enhanced Backend API - provides complete validation data for comprehensive display
# File: vms/vendor_onboarding/api/sap_validation_api.py


@frappe.whitelist()
def get_complete_validation_data(onb_ref):
    """
    Get comprehensive validation data for JavaScript rendering
    Returns ALL validation information for complete error display
    """
    try:
       
        
        # Get validation result
        result = validate_mandatory_data(onb_ref)
        
        # Get additional document info for enhanced display
        onb_doc = frappe.get_doc("Vendor Onboarding", onb_ref)
        
        # Prepare comprehensive data for frontend rendering
        validation_data = {
            "validation_passed": result["success"],
            "vendor_type": result.get("vendor_type", "Unknown"),
            "companies_count": len(result.get("data", [])),
            "message": result.get("message", ""),
            "timestamp": frappe.utils.now(),
            "missing_fields_summary": [],
            "total_missing_count": 0,
            "total_fields_validated": 0,
            "validation_details": {},
            "document_references": {},
            "banking_status": "Unknown",
            "field_categories": {}
        }
        
        if result["success"]:
            # For successful validation, add success details
            validation_data.update({
                "banking_status": "Verified",
                "total_fields_validated": "All required",
                "completion_percentage": 100,
                "sap_ready": True,
                "data_summary": result.get("data", [])
            })
        else:
            # For failed validation, parse and categorize ALL missing fields
            missing_fields_text = result.get("message", "")
            if "Missing Mandatory Fields:" in missing_fields_text:
                missing_fields_list = missing_fields_text.replace("Missing Mandatory Fields:\n", "").split("\n")
                clean_fields = [f.strip() for f in missing_fields_list if f.strip()]
                
                validation_data.update({
                    "missing_fields_summary": clean_fields,
                    "total_missing_count": len(clean_fields),
                    "banking_status": "Incomplete",
                    "completion_percentage": max(0, 100 - (len(clean_fields) * 2)),  # Rough completion estimate
                    "sap_ready": False
                })
                
                # Categorize missing fields for better display
                validation_data["field_categories"] = categorize_validation_fields(clean_fields)
                
                # Add detailed field information
                validation_data["validation_details"] = get_detailed_field_info(clean_fields)
        
        # Add document reference information
        validation_data["document_references"] = get_document_references(onb_doc)
        
        return {
            "success": True,
            "validation_data": validation_data,
            "message": "Complete validation data retrieved successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting complete validation data: {str(e)}", "Complete Validation Data API")
        return {
            "success": False,
            "message": f"Error retrieving validation data: {str(e)}",
            "validation_data": {
                "validation_passed": False,
                "vendor_type": "Unknown",
                "companies_count": 0,
                "message": f"Error: {str(e)}",
                "timestamp": frappe.utils.now(),
                "missing_fields_summary": [],
                "total_missing_count": 0,
                "banking_status": "Error",
                "completion_percentage": 0,
                "sap_ready": False
            }
        }


def categorize_validation_fields(missing_fields_list):
    """
    Categorize missing fields into logical groups for better display
    """
    categories = {
        "Company & Organization": [],
        "Vendor Master Data": [],
        "Address & Contact Information": [],
        "Banking & Payment Details": [],
        "International Banking": [],
        "Tax & Legal Information": [],
        "Purchase & Account Settings": [],
        "Other SAP Fields": []
    }
    
    # Enhanced field categorization mapping
    field_category_map = {
        # Company & Organization
        "company code": "Company & Organization",
        "company master": "Company & Organization",
        "purchase organization": "Company & Organization",
        "purchase group": "Company & Organization",
        "ekorg": "Company & Organization",
        "bukrs": "Company & Organization",
        "ekgrp": "Company & Organization",
        
        # Vendor Master Data
        "vendor name": "Vendor Master Data",
        "vendor master": "Vendor Master Data",
        "mobile number": "Vendor Master Data",
        "search term": "Vendor Master Data",
        "vendor type": "Vendor Master Data",
        "name1": "Vendor Master Data",
        "sort1": "Vendor Master Data",
        "j1ivtyp": "Vendor Master Data",
        
        # Address & Contact
        "address": "Address & Contact Information",
        "city": "Address & Contact Information",
        "state": "Address & Contact Information",
        "pincode": "Address & Contact Information",
        "pin code": "Address & Contact Information",
        "country": "Address & Contact Information",
        "email": "Address & Contact Information",
        "telephone": "Address & Contact Information",
        "contact": "Address & Contact Information",
        "street": "Address & Contact Information",
        "city1": "Address & Contact Information",
        "region": "Address & Contact Information",
        "postcode1": "Address & Contact Information",
        
        # Banking & Payment Details
        "bank": "Banking & Payment Details",
        "ifsc": "Banking & Payment Details",
        "account number": "Banking & Payment Details",
        "account holder": "Banking & Payment Details",
        "payment details": "Banking & Payment Details",
        "currency": "Banking & Payment Details",
        "bankl": "Banking & Payment Details",
        "bankn": "Banking & Payment Details",
        "bkref": "Banking & Payment Details",
        "banka": "Banking & Payment Details",
        "koinh": "Banking & Payment Details",
        "waers": "Banking & Payment Details",
        
        # International Banking
        "beneficiary": "International Banking",
        "intermediate": "International Banking",
        "swift": "International Banking",
        "iban": "International Banking",
        "international bank": "International Banking",
        "zzbenf": "International Banking",
        "zzben": "International Banking",
        "zzintr": "International Banking",
        
        # Tax & Legal
        "gst": "Tax & Legal Information",
        "pan": "Tax & Legal Information",
        "tax": "Tax & Legal Information",
        "stcd3": "Tax & Legal Information",
        "j1ipanno": "Tax & Legal Information",
        "j1ipanref": "Tax & Legal Information",
        
        # Purchase & Account Settings
        "reconciliation": "Purchase & Account Settings",
        "account group": "Purchase & Account Settings",
        "terms of payment": "Purchase & Account Settings",
        "incoterm": "Purchase & Account Settings",
        "akont": "Purchase & Account Settings",
        "ktokk": "Purchase & Account Settings",
        "zterm": "Purchase & Account Settings",
        "inco1": "Purchase & Account Settings",
        "inco2": "Purchase & Account Settings"
    }
    
    # Categorize each missing field
    for field in missing_fields_list:
        if not field or not field.strip():
            continue
        
        category = "Other SAP Fields"
        field_lower = field.lower()
        
        # Find the best matching category
        for keyword in field_category_map:
            if keyword in field_lower:
                category = field_category_map[keyword]
                break
        
        categories[category].append(field)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def get_detailed_field_info(missing_fields_list):
    """
    Get detailed information about each missing field
    """
    field_details = {}
    
    # SAP field to description mapping
    sap_field_descriptions = {
        "Bukrs": {
            "sap_code": "BUKRS",
            "description": "Company Code",
            "importance": "Critical",
            "data_type": "CHAR(4)"
        },
        "Ekorg": {
            "sap_code": "EKORG", 
            "description": "Purchasing Organization",
            "importance": "Critical",
            "data_type": "CHAR(4)"
        },
        "Name1": {
            "sap_code": "NAME1",
            "description": "Vendor Name",
            "importance": "Critical", 
            "data_type": "CHAR(35)"
        },
        "Street": {
            "sap_code": "STRAS",
            "description": "Street Address",
            "importance": "High",
            "data_type": "CHAR(35)"
        },
        "City1": {
            "sap_code": "ORT01",
            "description": "City",
            "importance": "High",
            "data_type": "CHAR(35)"
        },
        "PostCode1": {
            "sap_code": "PSTLZ",
            "description": "Postal Code",
            "importance": "High",
            "data_type": "CHAR(10)"
        },
        "Region": {
            "sap_code": "REGIO",
            "description": "Region/State",
            "importance": "High",
            "data_type": "CHAR(3)"
        },
        "Country": {
            "sap_code": "LAND1",
            "description": "Country Key",
            "importance": "Critical",
            "data_type": "CHAR(3)"
        },
        "Stcd3": {
            "sap_code": "STCD3",
            "description": "Tax Number 3 (GST)",
            "importance": "Critical",
            "data_type": "CHAR(18)"
        },
        "Bankl": {
            "sap_code": "BANKL",
            "description": "Bank Key",
            "importance": "Critical",
            "data_type": "CHAR(15)"
        },
        "Bankn": {
            "sap_code": "BANKN", 
            "description": "Bank Account Number",
            "importance": "Critical",
            "data_type": "CHAR(18)"
        }
    }
    
    for field in missing_fields_list:
        field_name = field.split("(")[0].strip()
        
        # Extract SAP field code if present
        sap_code = None
        for code in sap_field_descriptions:
            if code.lower() in field.lower():
                sap_code = code
                break
        
        field_details[field] = {
            "field_name": field_name,
            "sap_info": sap_field_descriptions.get(sap_code, {}) if sap_code else {},
            "resolution_priority": "High" if sap_code in ["Bukrs", "Name1", "Country", "Stcd3"] else "Medium"
        }
    
    return field_details


def get_document_references(onb_doc):
    """
    Get references to related documents for navigation
    """
    references = {}
    
    try:
        # Vendor Master reference
        if onb_doc.ref_no:
            references["vendor_master"] = {
                "doctype": "Vendor Master",
                "name": onb_doc.ref_no,
                "exists": frappe.db.exists("Vendor Master", onb_doc.ref_no)
            }
        
        # Payment Details reference
        if onb_doc.payment_detail:
            references["payment_details"] = {
                "doctype": "Vendor Onboarding Payment Details",
                "name": onb_doc.payment_detail,
                "exists": frappe.db.exists("Vendor Onboarding Payment Details", onb_doc.payment_detail)
            }
        
        # Company Details references
        if onb_doc.vendor_company_details:
            references["company_details"] = []
            for company in onb_doc.vendor_company_details:
                if company.vendor_company_details:
                    references["company_details"].append({
                        "doctype": "Vendor Onboarding Company Details",
                        "name": company.vendor_company_details,
                        "exists": frappe.db.exists("Vendor Onboarding Company Details", company.vendor_company_details)
                    })
        
        # Master data references
        if onb_doc.purchase_organization:
            references["purchase_organization"] = {
                "doctype": "Purchase Organization Master",
                "name": onb_doc.purchase_organization,
                "exists": frappe.db.exists("Purchase Organization Master", onb_doc.purchase_organization)
            }
        
        if onb_doc.account_group:
            references["account_group"] = {
                "doctype": "Account Group Master", 
                "name": onb_doc.account_group,
                "exists": frappe.db.exists("Account Group Master", onb_doc.account_group)
            }
            
    except Exception as e:
        frappe.log_error(f"Error getting document references: {str(e)}", "Document References")
    
    return references


@frappe.whitelist()
def get_validation_statistics(onb_ref=None):
    """
    Get validation statistics across all vendor onboarding documents
    Useful for dashboard displays
    """
    try:
        filters = {}
        if onb_ref:
            filters["name"] = onb_ref
        
        # Get all vendor onboarding documents
        onboarding_docs = frappe.get_all("Vendor Onboarding", 
                                       fields=["name", "mandatory_data_filled", "vendor_country", "onboarding_form_status"],
                                       filters=filters)
        
        total_docs = len(onboarding_docs)
        validated_docs = len([doc for doc in onboarding_docs if doc.mandatory_data_filled == 1])
        pending_docs = total_docs - validated_docs
        
        # Country distribution
        country_stats = {}
        for doc in onboarding_docs:
            country = doc.vendor_country or "Unknown"
            country_stats[country] = country_stats.get(country, 0) + 1
        
        # Status distribution  
        status_stats = {}
        for doc in onboarding_docs:
            status = doc.onboarding_form_status or "Unknown"
            status_stats[status] = status_stats.get(status, 0) + 1
        
        return {
            "success": True,
                "total_documents": total_docs,
                "validated_documents": validated_docs,
                "pending_documents": pending_docs,
                "validation_rate": (validated_docs / total_docs * 100) if total_docs > 0 else 0,
                "country_distribution": country_stats,
                "status_distribution": status_stats,
                "last_updated": frappe.utils.now()
            }
        
        
    except Exception as e:
        frappe.log_error(f"Error getting validation statistics: {str(e)}", "Validation Statistics API")
        return {
            "success": False,
            "message": str(e),
            "statistics": {}
        }


@frappe.whitelist()
def export_validation_report(onb_ref):
    """
    Export detailed validation report for download
    """
    try:
        # Get complete validation data
        validation_response = get_complete_validation_data(onb_ref)
        
        if not validation_response["success"]:
            return validation_response
        
        validation_data = validation_response["validation_data"]
        
        # Create detailed report data
        report_data = {
            "document_info": {
                "onboarding_reference": onb_ref,
                "validation_date": validation_data["timestamp"],
                "validation_status": "PASSED" if validation_data["validation_passed"] else "FAILED",
                "vendor_type": validation_data["vendor_type"],
                "companies_count": validation_data["companies_count"]
            },
            "validation_summary": {
                "total_fields_checked": validation_data.get("total_fields_validated", "Unknown"),
                "missing_fields_count": validation_data["total_missing_count"],
                "completion_percentage": validation_data.get("completion_percentage", 0),
                "banking_status": validation_data["banking_status"],
                "sap_ready": validation_data["sap_ready"]
            },
            "missing_fields_by_category": validation_data.get("field_categories", {}),
            "detailed_field_info": validation_data.get("validation_details", {}),
            "document_references": validation_data.get("document_references", {}),
            "recommendations": generate_validation_recommendations(validation_data)
        }
        
        return {
            "success": True,
            "report_data": report_data,
            "message": "Validation report generated successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error exporting validation report: {str(e)}", "Export Validation Report")
        return {
            "success": False,
            "message": str(e)
        }


def generate_validation_recommendations(validation_data):
    """
    Generate specific recommendations based on validation results
    """
    recommendations = []
    
    if not validation_data["validation_passed"]:
        missing_count = validation_data["total_missing_count"]
        field_categories = validation_data.get("field_categories", {})
        
        # Priority recommendations based on missing field categories
        if "Company & Organization" in field_categories and field_categories["Company & Organization"]:
            recommendations.append({
                "priority": "Critical",
                "category": "Company & Organization",
                "action": "Complete company and organizational setup",
                "description": f"{len(field_categories['Company & Organization'])} critical company fields are missing. These are required for SAP integration.",
                "estimated_time": "15-30 minutes"
            })
        
        if "Banking & Payment Details" in field_categories and field_categories["Banking & Payment Details"]:
            vendor_type = validation_data.get("vendor_type", "").lower()
            if "international" in vendor_type:
                recommendations.append({
                    "priority": "Critical",
                    "category": "Banking & Payment Details", 
                    "action": "Complete international banking information",
                    "description": "International vendors require complete beneficiary and potentially intermediate bank details.",
                    "estimated_time": "20-45 minutes"
                })
            else:
                recommendations.append({
                    "priority": "Critical",
                    "category": "Banking & Payment Details",
                    "action": "Complete domestic banking information", 
                    "description": "Ensure Bank Name, IFSC Code, Account Number, and Account Holder Name are provided.",
                    "estimated_time": "10-15 minutes"
                })
        
        if "Tax & Legal Information" in field_categories and field_categories["Tax & Legal Information"]:
            recommendations.append({
                "priority": "High",
                "category": "Tax & Legal Information",
                "action": "Complete tax registration details",
                "description": "GST and PAN information are mandatory for compliance and SAP processing.",
                "estimated_time": "5-10 minutes"
            })
        
        if "Address & Contact Information" in field_categories and field_categories["Address & Contact Information"]:
            recommendations.append({
                "priority": "Medium",
                "category": "Address & Contact Information",
                "action": "Complete address and contact details",
                "description": "Accurate address information is required for vendor correspondence and delivery.",
                "estimated_time": "10-20 minutes"
            })
        
        # Overall recommendations
        if missing_count > 20:
            recommendations.append({
                "priority": "Critical",
                "category": "Overall Process",
                "action": "Schedule dedicated completion session",
                "description": f"With {missing_count} missing fields, consider scheduling a focused 1-2 hour session to complete all requirements.",
                "estimated_time": "1-2 hours"
            })
        elif missing_count > 10:
            recommendations.append({
                "priority": "High", 
                "category": "Overall Process",
                "action": "Complete in phases",
                "description": f"Break down the {missing_count} missing fields into 2-3 completion phases by category.",
                "estimated_time": "45-90 minutes"
            })
        else:
            recommendations.append({
                "priority": "Medium",
                "category": "Overall Process", 
                "action": "Final completion push",
                "description": f"Only {missing_count} fields remaining. Complete these for immediate SAP readiness.",
                "estimated_time": "15-30 minutes"
            })
    
    else:
        recommendations.append({
            "priority": "Success",
            "category": "Validation Complete",
            "action": "Proceed with SAP integration",
            "description": "All mandatory fields are complete. The vendor data is ready for SAP transmission.",
            "estimated_time": "Ready now"
        })
    
    return recommendations


@frappe.whitelist()
def trigger_batch_validation(onb_refs=None):
    """
    Trigger validation for multiple onboarding documents
    Useful for bulk validation operations
    """
    try:
        if not onb_refs:
            # Get all pending onboarding documents
            onb_refs = frappe.get_all("Vendor Onboarding", 
                                    filters={"mandatory_data_filled": 0, "docstatus": ["!=", 2]}, 
                                    pluck="name")
        
        if isinstance(onb_refs, str):
            onb_refs = [onb_refs]
        
        results = []
        
        for onb_ref in onb_refs:
            try:
                # Import your existing validation function
                from vms.APIs.sap.mandatory_data_validation import validate_mandatory_data
                
                # Run validation
                result = validate_mandatory_data(onb_ref)
                
                # Update the document
                frappe.db.set_value("Vendor Onboarding", onb_ref, "mandatory_data_filled", 1 if result["success"] else 0)
                
                results.append({
                    "onboarding_ref": onb_ref,
                    "validation_passed": result["success"],
                    "error_count": len(result.get("message", "").split("\n")) if not result["success"] else 0
                })
                
            except Exception as e:
                results.append({
                    "onboarding_ref": onb_ref,
                    "validation_passed": False,
                    "error": str(e)
                })
        
        frappe.db.commit()
        
        # Summary statistics
        total_processed = len(results)
        passed_count = len([r for r in results if r["validation_passed"]])
        failed_count = total_processed - passed_count
        
        return {
            "success": True,
            "summary": {
                "total_processed": total_processed,
                "passed": passed_count,
                "failed": failed_count,
                "success_rate": (passed_count / total_processed * 100) if total_processed > 0 else 0
            },
            "detailed_results": results,
            "message": f"Batch validation completed: {passed_count}/{total_processed} documents passed"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in batch validation: {str(e)}", "Batch Validation")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def get_field_navigation_info(field_name, onb_ref):
    """
    Get specific navigation information for a field
    Helps users know exactly where to go to fix a specific field
    """
    try:
        # Field to navigation mapping
        field_navigation = {
            "Vendor Name": {"route": "Form/Vendor Master", "field": "vendor_name"},
            "Mobile Number": {"route": "Form/Vendor Master", "field": "mobile_number"},
            "Primary Email": {"route": "Form/Vendor Master", "field": "office_email_primary"},
            "Company Code": {"route": "Form/Company Master", "field": "company_code"},
            "Purchase Organization": {"route": "Form/Purchase Organization Master", "field": "purchase_organization_code"},
            "Bank Name": {"route": "Form/Bank Master", "field": "bank_name"},
            "IFSC Code": {"route": "Form/Vendor Onboarding Payment Details", "field": "ifsc_code"},
            "Account Number": {"route": "Form/Vendor Onboarding Payment Details", "field": "account_number"},
            "GST Number": {"route": "Form/Vendor Onboarding Company Details", "field": "gst"},
            "Address Line 1": {"route": "Form/Vendor Onboarding Company Details", "field": "address_line_1"},
            "City": {"route": "Form/Vendor Onboarding Company Details", "field": "city"},
            "State": {"route": "Form/Vendor Onboarding Company Details", "field": "state"},
            "Pin Code": {"route": "Form/Vendor Onboarding Company Details", "field": "pincode"}
        }
        
        navigation_info = field_navigation.get(field_name, {})
        
        if navigation_info:
            # Get the specific document reference
            onb_doc = frappe.get_doc("Vendor Onboarding", onb_ref)
            
            if "Vendor Master" in navigation_info["route"] and onb_doc.ref_no:
                navigation_info["document_name"] = onb_doc.ref_no
            elif "Payment Details" in navigation_info["route"] and onb_doc.payment_detail:
                navigation_info["document_name"] = onb_doc.payment_detail
            # Add more document reference mappings as needed
        
        return {
            "success": True,
            "navigation_info": navigation_info,
            "field_name": field_name
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
    





def safe_get_contact_detail(onb_doc, field_name):
    """
    Safely get contact detail field from the first contact record
    Similar to safe_get function used in SAP.py
    """
    try:
        if hasattr(onb_doc, 'contact_details') and onb_doc.contact_details and len(onb_doc.contact_details) > 0:
            first_contact = onb_doc.contact_details[0]
            return getattr(first_contact, field_name, "") or ""
        return ""
    except:
        return ""


def safe_get(doc, table_field, index, field_name):
    """
    Safely get field from table record matching SAP integration function
    """
    try:
        if hasattr(doc, table_field):
            table_data = getattr(doc, table_field)
            if table_data and len(table_data) > index:
                return getattr(table_data[index], field_name, "") or ""
        return ""
    except:
        return ""


def validate_mandatory_data(onb_ref):
    """
    Enhanced validation function that matches SAP integration logic exactly
    Handles domestic (India), international, and Not-Registered GST vendors
    """
    try:
        # Get main documents
        onb = frappe.get_doc("Vendor Onboarding", onb_ref)
        onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
        onb_pmd = frappe.get_doc("Vendor Onboarding Payment Details", onb.payment_detail)
        pur_org = frappe.get_doc("Purchase Organization Master", onb.purchase_organization)
        pur_grp = frappe.get_doc("Purchase Group Master", onb.purchase_group)
        acc_grp = frappe.get_doc("Account Group Master", onb.account_group)
        onb_reco = frappe.get_doc("Reconciliation Account", onb.reconciliation_account)
        onb_pm_term = frappe.get_doc("Terms of Payment Master", onb.terms_of_payment)
        onb_inco = frappe.get_doc("Incoterm Master", onb.incoterms)
        onb_legal_doc = frappe.get_doc("Legal Documents", onb.document_details)
        
        # Get bank master document only if bank_name exists
        onb_bank = None
        if onb_pmd.bank_name:
            onb_bank = frappe.get_doc("Bank Master", onb_pmd.bank_name)

        # Boolean field mappings
        payee = 'X' if onb.payee_in_document == 1 else ''
        gr_based_inv_ver = 'X' if onb.gr_based_inv_ver == 1 else ''
        service_based_inv_ver = 'X' if onb.service_based_inv_ver == 1 else ''
        check_double_invoice = 'X' if onb.check_double_invoice == 1 else ''

        # Get vendor type names
        vendor_type_names = []
        for row in onb.vendor_types:
            if row.vendor_type:
                vendor_type_names.append(row.vendor_type)

        validation_errors = []
        data_list = []

        # Check vendor country to determine if domestic or international
        is_domestic_vendor = onb.vendor_country == "India"

        # Validate banking details based on vendor country
        banking_validation_errors = validate_banking_details(onb_pmd, is_domestic_vendor)
        if banking_validation_errors:
            validation_errors.extend(banking_validation_errors)

        # Process each company in vendor_company_details
        for company in onb.vendor_company_details:
            vcd = frappe.get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
            com_vcd = frappe.get_doc("Company Master", vcd.company_name)
            
            # Get country information for this company
            country_doc = frappe.get_doc("Country Master", vcd.country)
            country_code = country_doc.country_code
            
            # Set Zuawa based on SAP client code logic from integration
            sap_client_code = com_vcd.sap_client_code
            Zuawa = "001"  # Default value as per integration code

            if is_domestic_vendor:
                # **DOMESTIC VENDOR - Process GST entries**
                print(f"Processing Domestic Vendor - Company: {vcd.company_name}")
                
                if not hasattr(vcd, 'comp_gst_table') or not vcd.comp_gst_table:
                    validation_errors.append(f"Company {com_vcd.company_code}: No GST entries found for domestic vendor")
                    continue
                
                # Process each GST entry for domestic vendors
                for gst_index, gst_table in enumerate(vcd.comp_gst_table):
                    # Get GST-specific data
                    gst_ven_type = gst_table.gst_ven_type
                    gst_state = gst_table.gst_state
                    gst_num = gst_table.gst_number or "0"
                    gst_pin = gst_table.pincode
                    
                    # Get address details
                    gst_addrs = frappe.get_doc("Pincode Master", gst_pin)
                    gst_city = gst_addrs.city
                    gst_country = gst_addrs.country
                    gst_district = gst_addrs.district
                    gst_state_doc = frappe.get_doc("State Master", gst_state)
                    
                    # Build address text as per integration logic
                    gst_address_text = ", ".join(filter(None, [
                        gst_city,
                        gst_district,
                        gst_state
                    ]))

                    # Build complete data dictionary following SAP integration structure
                    data = {
                        "Bukrs": com_vcd.company_code,
                        "Ekorg": pur_org.purchase_organization_code,
                        "Ktokk": acc_grp.account_group_code,
                        "Title": "",
                        "Name1": onb_vm.vendor_name,
                        "Name2": "",
                        "Sort1": onb_vm.search_term if hasattr(onb_vm, 'search_term') else "",
                        "Street": vcd.address_line_1,
                        "StrSuppl1": gst_address_text or "",
                        "StrSuppl2": "",
                        "StrSuppl3": "",
                        "PostCode1": gst_pin,
                        "City1": gst_city,
                        "Country": country_code,
                        "J1kftind": "",
                        "Region": gst_state_doc.sap_state_code if hasattr(gst_state_doc, 'sap_state_code') else "",
                        "TelNumber": "",
                        "MobNumber": onb_vm.mobile_number,
                        "SmtpAddr": onb_vm.office_email_primary,
                        "SmtpAddr1": onb_vm.office_email_secondary if hasattr(onb_vm, 'office_email_secondary') else "",
                        "Zuawa": Zuawa,
                        "Akont": onb_reco.reconcil_account_code,
                        "Waers": onb_pmd.currency_code if hasattr(onb_pmd, 'currency_code') else "",
                        "Zterm": onb_pm_term.terms_of_payment_code,
                        "Inco1": onb_inco.incoterm_code,
                        "Inco2": onb_inco.incoterm_name,
                        "Kalsk": "",
                        "Ekgrp": pur_grp.purchase_group_code,
                        "Xzemp": payee,
                        "Reprf": check_double_invoice,
                        "Webre": gr_based_inv_ver,
                        "Lebre": service_based_inv_ver,
                        "Stcd3": gst_num if gst_ven_type != "Not-Registered" else "0",
                        "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
                        "J1ipanno": vcd.company_pan_number if gst_ven_type != "Not-Registered" and hasattr(vcd, 'company_pan_number') else "0",
                        "J1ipanref": onb_legal_doc.name_on_company_pan if hasattr(onb_legal_doc, 'name_on_company_pan') else "",
                        "Namev": safe_get_contact_detail(onb, "first_name"),
                        "Name11": safe_get_contact_detail(onb, "last_name"),
                        "Bankl": onb_bank.bank_code if onb_bank else "",
                        "Bankn": onb_pmd.account_number if hasattr(onb_pmd, 'account_number') else "",
                        "Bkref": onb_pmd.ifsc_code if hasattr(onb_pmd, 'ifsc_code') else "",
                        "Banka": onb_bank.bank_name if onb_bank else "",
                        "Koinh": onb_pmd.name_of_account_holder if hasattr(onb_pmd, 'name_of_account_holder') else "",
                        "Xezer": "",
                        # International bank fields (empty for domestic)
                        "ZZBENF_NAME": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_name"),
                        "ZZBEN_BANK_NM": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_name"),
                        "ZZBEN_ACCT_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_account_no"),
                        "ZZBENF_IBAN": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_iban_no"),
                        "ZZBENF_BANKADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_address"),
                        "ZZBENF_SHFTADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_swift_code"),
                        "ZZBENF_ACH_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_ach_no"),
                        "ZZBENF_ABA_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_aba_no"),
                        "ZZBENF_ROUTING": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_routing_no"),
                        # Intermediate bank fields (empty for domestic)
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
                    
                    # Validate this GST entry
                    validation_result = validate_data_fields(data, f"Company {com_vcd.company_code} - GST Entry {gst_index + 1} ({gst_num})", is_domestic_vendor, gst_ven_type)
                    if validation_result["errors"]:
                        validation_errors.extend(validation_result["errors"])
                    
                    data_list.append(data)

            else:
                # **INTERNATIONAL VENDOR - Single entry per company**
                print(f"Processing International Vendor - Company: {vcd.company_name}")
                
                # Get international address details
                gst_state = vcd.international_state if hasattr(vcd, 'international_state') else ""
                gst_pin = vcd.international_zipcode if hasattr(vcd, 'international_zipcode') else ""
                gst_city = vcd.international_city if hasattr(vcd, 'international_city') else ""
                gst_country = vcd.international_country if hasattr(vcd, 'international_country') else ""
                
                # Build address text for international
                gst_address_text = ", ".join(filter(None, [
                    gst_city,
                    gst_country,
                    gst_state
                ]))

                # Build data for international vendor
                data = {
                    "Bukrs": com_vcd.company_code,
                    "Ekorg": pur_org.purchase_organization_code,
                    "Ktokk": acc_grp.account_group_code,
                    "Title": "",
                    "Name1": onb_vm.vendor_name,
                    "Name2": "",
                    "Sort1": onb_vm.search_term if hasattr(onb_vm, 'search_term') else "",
                    "Street": vcd.address_line_1,
                    "StrSuppl1": gst_address_text or "",
                    "StrSuppl2": "",
                    "StrSuppl3": "",
                    "PostCode1": gst_pin,
                    "City1": gst_city,
                    "Country": country_code,
                    "J1kftind": "",
                    "Region": "ZZ",  # Fixed value for international as per integration
                    "TelNumber": "",
                    "MobNumber": onb_vm.mobile_number,
                    "SmtpAddr": onb_vm.office_email_primary,
                    "SmtpAddr1": onb_vm.office_email_secondary if hasattr(onb_vm, 'office_email_secondary') else "",
                    "Zuawa": Zuawa,
                    "Akont": onb_reco.reconcil_account_code,
                    "Waers": onb_pmd.currency_code if hasattr(onb_pmd, 'currency_code') else "",
                    "Zterm": onb_pm_term.terms_of_payment_code,
                    "Inco1": onb_inco.incoterm_code,
                    "Inco2": onb_inco.incoterm_name,
                    "Kalsk": "",
                    "Ekgrp": pur_grp.purchase_group_code,
                    "Xzemp": payee,
                    "Reprf": check_double_invoice,
                    "Webre": gr_based_inv_ver,
                    "Lebre": service_based_inv_ver,
                    "Stcd3": "0",  # Fixed value for international
                    "J1ivtyp": vendor_type_names[0] if vendor_type_names else "",
                    "J1ipanno": "0",  # Fixed value for international
                    "J1ipanref": onb_legal_doc.name_on_company_pan if hasattr(onb_legal_doc, 'name_on_company_pan') else "",
                    "Namev": safe_get_contact_detail(onb, "first_name"),
                    "Name11": safe_get_contact_detail(onb, "last_name"),
                    "Bankl": onb_bank.bank_code if onb_bank else "",
                    "Bankn": onb_pmd.account_number if hasattr(onb_pmd, 'account_number') else "",
                    "Bkref": onb_pmd.ifsc_code if hasattr(onb_pmd, 'ifsc_code') else "",
                    "Banka": onb_bank.bank_name if onb_bank else "",
                    "Koinh": onb_pmd.name_of_account_holder if hasattr(onb_pmd, 'name_of_account_holder') else "",
                    "Xezer": "",
                    # International bank fields (mandatory for international)
                    "ZZBENF_NAME": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_name"),
                    "ZZBEN_BANK_NM": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_name"),
                    "ZZBEN_ACCT_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_account_no"),
                    "ZZBENF_IBAN": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_iban_no"),
                    "ZZBENF_BANKADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_bank_address"),
                    "ZZBENF_SHFTADDR": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_swift_code"),
                    "ZZBENF_ACH_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_ach_no"),
                    "ZZBENF_ABA_NO": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_aba_no"),
                    "ZZBENF_ROUTING": safe_get(onb_pmd, "international_bank_details", 0, "beneficiary_routing_no"),
                    # Intermediate bank fields (optional for international)
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
                
                # Validate international vendor data
                validation_result = validate_data_fields(data, f"Company {com_vcd.company_code} - International", is_domestic_vendor, "International")
                if validation_result["errors"]:
                    validation_errors.extend(validation_result["errors"])
                
                data_list.append(data)
				
        # Return results based on validation
        if validation_errors:
            error_message = "Missing Mandatory Fields:\n" + "\n".join(validation_errors)
            frappe.log_error(error_message, "Mandatory Data Validation Failed")
            return {
                "success": False,
                "message": error_message,
                "data": data_list,
                "vendor_type": "International" if not is_domestic_vendor else "Domestic"
            }
        else:
            return {
                "success": True,
                "message": f"✅ Validation passed for {len(data_list)} company records. Vendor Type: {'Domestic (India)' if is_domestic_vendor else 'International'}",
                "data": data_list,
                "vendor_type": "International" if not is_domestic_vendor else "Domestic"
            }
			
    except Exception as e:
        error_message = f"Error during validation: {str(e)}"
        frappe.log_error(error_message, "Mandatory Data Validation Error")
        return {
            "success": False,
            "message": error_message,
            "data": [],
            "vendor_type": "Unknown"
        }


def validate_data_fields(data, context_label, is_domestic_vendor, gst_ven_type):
    """
    Validate data fields based on vendor type and GST registration status
    """
    validation_errors = []
    
    # Field descriptions for better error messages
    field_descriptions = {
        "Bukrs": "Company Code (Company Master)",
        "Ekorg": "Purchase Organization Code (Purchase Organization Master)",
        "Ktokk": "Account Group Code (Account Group Master)",
        "Name1": "Vendor Name (Vendor Master)",
        "Street": "Address Line 1 (Vendor Onboarding Company Details)",
        "PostCode1": "Pincode (Vendor Onboarding Company Details)",
        "City1": "City (Vendor Onboarding Company Details)",
        "Country": "Country (Vendor Onboarding Company Details)",
        "Region": "State/Region (State Master or International)",
        "MobNumber": "Mobile Number (Vendor Master)",
        "SmtpAddr": "Primary Email (Vendor Master)",
        "Akont": "Reconciliation Account Code (Reconciliation Account)",
        "Waers": "Currency Code (Vendor Onboarding Payment Details)",
        "Zterm": "Terms of Payment Code (Terms of Payment Master)",
        "Inco1": "Incoterm Code (Incoterm Master)",
        "Inco2": "Incoterm Name (Incoterm Master)",
        "Ekgrp": "Purchase Group Code (Purchase Group Master)",
        "J1ivtyp": "Vendor Type (Vendor Type Master)",
        "Refno": "Reference Number (Vendor Onboarding)",
        # Banking fields
        "Bankl": "Bank Code (Bank Master)",
        "Bankn": "Account Number (Vendor Onboarding Payment Details)",
        "Bkref": "IFSC Code (Vendor Onboarding Payment Details)",
        "Banka": "Bank Name (Bank Master)",
        "Koinh": "Name of Account Holder (Vendor Onboarding Payment Details)",
        # International bank fields
        "ZZBENF_NAME": "Beneficiary Name (International Bank Details)",
        "ZZBEN_BANK_NM": "Beneficiary Bank Name (International Bank Details)",
        "ZZBEN_ACCT_NO": "Beneficiary Account Number (International Bank Details)",
        "ZZBENF_SHFTADDR": "Beneficiary SWIFT Code (International Bank Details)",
        # Intermediate bank fields
        "ZZINTR_BANK_NM": "Intermediate Bank Name (Intermediate Bank Details)",
        "ZZINTR_SHFTADDR": "Intermediate SWIFT Code (Intermediate Bank Details)",
    }

    # Fields allowed to be empty based on vendor type and GST status
    allowed_empty_fields = {
        "Title", "Name2", "StrSuppl2", "StrSuppl3", "J1kftind", "Zuawa", 
        "Kalsk", "TelNumber", "SmtpAddr1", "Namev", "Name11", "Sort1",
        "Xezer", "Vedno", "Zmsg", "StrSuppl1"
    }
    
    # Add conditional allowed empty fields based on vendor type
    if is_domestic_vendor:
        # For domestic vendors, international/intermediate bank fields can be empty
        allowed_empty_fields.update({
            "ZZBENF_NAME", "ZZBEN_BANK_NM", "ZZBEN_ACCT_NO", "ZZBENF_IBAN",
            "ZZBENF_BANKADDR", "ZZBENF_SHFTADDR", "ZZBENF_ACH_NO", "ZZBENF_ABA_NO",
            "ZZBENF_ROUTING", "ZZINTR_ACCT_NO", "ZZINTR_IBAN", "ZZINTR_BANK_NM",
            "ZZINTR_BANKADDR", "ZZINTR_SHFTADDR", "ZZINTR_ACH_NO", "ZZINTR_ABA_NO",
            "ZZINTR_ROUTING"
        })
        
        # For Not-Registered GST vendors, GST-related fields can be empty/default
        if gst_ven_type == "Not-Registered":
            allowed_empty_fields.update({"Stcd3", "J1ipanno"})
        
    else:
        # For international vendors, domestic bank fields can be empty, but some international fields are mandatory
        allowed_empty_fields.update({
            "Bankl", "Bankn", "Bkref", "Banka", "Koinh", "Stcd3", "J1ipanno"
        })
        
        # Additional international fields that can be empty
        allowed_empty_fields.update({
            "J1ipanref", "ZZBENF_IBAN", "ZZBENF_ACH_NO", "ZZBENF_ABA_NO", "ZZBENF_ROUTING"
        })
        
        # Intermediate bank fields are optional for international vendors
        allowed_empty_fields.update({
            "ZZINTR_ACCT_NO", "ZZINTR_IBAN", "ZZINTR_BANK_NM",
            "ZZINTR_BANKADDR", "ZZINTR_SHFTADDR", "ZZINTR_ACH_NO", 
            "ZZINTR_ABA_NO", "ZZINTR_ROUTING"
        })

    # Check for missing mandatory data
    missing_fields = []
    for field_key, field_value in data.items():
        # Skip fields that are intentionally allowed to be empty
        if field_key in allowed_empty_fields:
            continue
            
        # Check if field is None, empty string, or whitespace only
        if field_value is None or field_value == "" or (isinstance(field_value, str) and field_value.strip() == ""):
            field_description = field_descriptions.get(field_key, field_key)
            missing_fields.append(f"{field_description}")

    if missing_fields:
        validation_errors.append(f"{context_label}: Missing mandatory fields - {', '.join(missing_fields)}")
    
    return {"errors": validation_errors}


def validate_banking_details(payment_details, is_domestic_vendor):
    """
    Validate banking details based on vendor country - matches SAP integration logic
    India = domestic bank validation
    Other countries = international + intermediate bank validation
    """
    validation_errors = []
    
    if is_domestic_vendor:
        # Validate domestic banking details for Indian vendors
        if not hasattr(payment_details, 'bank_name') or not payment_details.bank_name:
            validation_errors.append("Bank Name is required for domestic vendors")
        if not hasattr(payment_details, 'ifsc_code') or not payment_details.ifsc_code:
            validation_errors.append("IFSC Code is required for domestic vendors")
        if not hasattr(payment_details, 'account_number') or not payment_details.account_number:
            validation_errors.append("Account Number is required for domestic vendors")
        if not hasattr(payment_details, 'name_of_account_holder') or not payment_details.name_of_account_holder:
            validation_errors.append("Name of Account Holder is required for domestic vendors")
    else:
        # Validate international banking details for foreign vendors
        if not hasattr(payment_details, 'international_bank_details') or not payment_details.international_bank_details or len(payment_details.international_bank_details) == 0:
            validation_errors.append("International Bank Details table is empty (required for international vendors)")
        else:
            # Validate first international bank record (primary bank)
            intl_bank = payment_details.international_bank_details[0]
            required_intl_fields = {
                'beneficiary_name': 'Beneficiary Name',
                'beneficiary_bank_name': 'Beneficiary Bank Name',
                'beneficiary_account_no': 'Beneficiary Account Number',
                'beneficiary_swift_code': 'Beneficiary SWIFT Code'
            }
            
            for field, label in required_intl_fields.items():
                if not hasattr(intl_bank, field) or not getattr(intl_bank, field):
                    validation_errors.append(f"{label} is required in International Bank Details")
        
        # Check if intermediate bank details are provided and validate them
        if hasattr(payment_details, 'add_intermediate_bank_details') and payment_details.add_intermediate_bank_details:
            if not hasattr(payment_details, 'intermediate_bank_details') or not payment_details.intermediate_bank_details or len(payment_details.intermediate_bank_details) == 0:
                validation_errors.append("Intermediate Bank Details table is empty but 'Add Intermediate Bank Details' is checked")
            else:
                # Validate first intermediate bank record
                inter_bank = payment_details.intermediate_bank_details[0]
                required_inter_fields = {
                    'intermediate_bank_name': 'Intermediate Bank Name',
                    'intermediate_swift_code': 'Intermediate SWIFT Code'
                }
                
                for field, label in required_inter_fields.items():
                    if not hasattr(inter_bank, field) or not getattr(inter_bank, field):
                        validation_errors.append(f"{label} is required in Intermediate Bank Details")
    
    return validation_errors


# Additional helper function for testing validation
@frappe.whitelist(allow_guest=True)
def test_validation_with_sap_structure(onb_ref):
    """
    Test function to validate data structure matches SAP integration exactly
    Returns detailed comparison between validation and SAP integration logic
    """
    try:
        # Run validation
        validation_result = validate_mandatory_data(onb_ref)
        
        # Get the same documents for comparison
        onb = frappe.get_doc("Vendor Onboarding", onb_ref)
        onb_vm = frappe.get_doc("Vendor Master", onb.ref_no)
        
        is_domestic_vendor = onb.vendor_country == "India"
        
        comparison_result = {
            "validation_result": validation_result,
            "vendor_type_detected": "Domestic" if is_domestic_vendor else "International",
            "vendor_country": onb.vendor_country,
            "companies_count": len(onb.vendor_company_details),
            "data_records_generated": len(validation_result.get("data", [])),
            "validation_passed": validation_result.get("success", False)
        }
        
        # Add GST processing info for domestic vendors
        if is_domestic_vendor:
            total_gst_entries = 0
            for company in onb.vendor_company_details:
                vcd = frappe.get_doc("Vendor Onboarding Company Details", company.vendor_company_details)
                if hasattr(vcd, 'comp_gst_table') and vcd.comp_gst_table:
                    total_gst_entries += len(vcd.comp_gst_table)
            
            comparison_result["total_gst_entries"] = total_gst_entries
            comparison_result["expected_data_records"] = total_gst_entries
        else:
            comparison_result["total_gst_entries"] = 0
            comparison_result["expected_data_records"] = len(onb.vendor_company_details)
        
        # Check if data record count matches expected
        comparison_result["data_count_matches"] = (
            comparison_result["data_records_generated"] == 
            comparison_result["expected_data_records"]
        )
        
        return comparison_result
        
    except Exception as e:
        return {
            "error": f"Test validation failed: {str(e)}",
            "validation_result": None
        }


# Additional helper function to preview SAP data structure
@frappe.whitelist(allow_guest=True)
def preview_sap_data_structure(onb_ref):
    """
    Preview the exact data structure that will be sent to SAP
    Useful for debugging and verification
    """
    try:
        validation_result = validate_mandatory_data(onb_ref)
        
        if not validation_result.get("data"):
            return {
                "error": "No data generated",
                "validation_result": validation_result
            }
        
        # Show structure of first data record
        sample_data = validation_result["data"][0]
        
        # Categorize fields for better understanding
        categorized_fields = {
            "company_info": {},
            "vendor_basic": {},
            "address_info": {},
            "contact_info": {},
            "sap_config": {},
            "banking_domestic": {},
            "banking_international": {},
            "banking_intermediate": {},
            "reference_info": {}
        }
        
        field_categories = {
            # Company and organizational
            "Bukrs": "company_info", "Ekorg": "company_info", "Ktokk": "company_info",
            "Ekgrp": "company_info", "Zuawa": "company_info",
            
            # Vendor basic info
            "Name1": "vendor_basic", "Name2": "vendor_basic", "Sort1": "vendor_basic",
            "Title": "vendor_basic", "J1ivtyp": "vendor_basic",
            
            # Address
            "Street": "address_info", "StrSuppl1": "address_info", "StrSuppl2": "address_info",
            "StrSuppl3": "address_info", "PostCode1": "address_info", "City1": "address_info",
            "Country": "address_info", "Region": "address_info",
            
            # Contact
            "TelNumber": "contact_info", "MobNumber": "contact_info", 
            "SmtpAddr": "contact_info", "SmtpAddr1": "contact_info",
            "Namev": "contact_info", "Name11": "contact_info",
            
            # SAP Configuration
            "Akont": "sap_config", "Waers": "sap_config", "Zterm": "sap_config",
            "Inco1": "sap_config", "Inco2": "sap_config", "Kalsk": "sap_config",
            "Xzemp": "sap_config", "Reprf": "sap_config", "Webre": "sap_config",
            "Lebre": "sap_config", "Stcd3": "sap_config", "J1ipanno": "sap_config",
            "J1ipanref": "sap_config", "J1kftind": "sap_config", "Xezer": "sap_config",
            
            # Domestic Banking
            "Bankl": "banking_domestic", "Bankn": "banking_domestic", 
            "Bkref": "banking_domestic", "Banka": "banking_domestic", 
            "Koinh": "banking_domestic",
            
            # International Banking
            "ZZBENF_NAME": "banking_international", "ZZBEN_BANK_NM": "banking_international",
            "ZZBEN_ACCT_NO": "banking_international", "ZZBENF_IBAN": "banking_international",
            "ZZBENF_BANKADDR": "banking_international", "ZZBENF_SHFTADDR": "banking_international",
            "ZZBENF_ACH_NO": "banking_international", "ZZBENF_ABA_NO": "banking_international",
            "ZZBENF_ROUTING": "banking_international",
            
            # Intermediate Banking
            "ZZINTR_ACCT_NO": "banking_intermediate", "ZZINTR_IBAN": "banking_intermediate",
            "ZZINTR_BANK_NM": "banking_intermediate", "ZZINTR_BANKADDR": "banking_intermediate",
            "ZZINTR_SHFTADDR": "banking_intermediate", "ZZINTR_ACH_NO": "banking_intermediate",
            "ZZINTR_ABA_NO": "banking_intermediate", "ZZINTR_ROUTING": "banking_intermediate",
            
            # Reference
            "Refno": "reference_info", "Vedno": "reference_info", "Zmsg": "reference_info"
        }
        
        # Categorize the sample data
        for field, value in sample_data.items():
            category = field_categories.get(field, "other")
            if category not in categorized_fields:
                categorized_fields[category] = {}
            categorized_fields[category][field] = value
        
        return {
            "success": True,
            "total_records": len(validation_result["data"]),
            "vendor_type": validation_result.get("vendor_type"),
            "sample_data_structure": categorized_fields,
            "validation_status": validation_result.get("success"),
            "validation_message": validation_result.get("message"),
            "all_sap_fields": list(sample_data.keys())
        }
        
    except Exception as e:
        return {
            "error": f"Preview failed: {str(e)}"
        }