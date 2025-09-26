# COMPREHENSIVE DATA INTEGRITY SYSTEM
# Based on actual document creation process from vendor import staging

import frappe
from frappe.utils import now_datetime, cstr, flt, cint, add_to_date
import json
import re
from collections import defaultdict

class VendorImportDataIntegritySystem:
    """
    Comprehensive data integrity system that validates ALL documents created
    from Vendor Import Staging, including main docs and child table link fields
    """
    
    @staticmethod
    def get_complete_document_schema():
        """
        Get complete schema of ALL documents created from vendor import staging
        """
        
        document_schema = {
            # Main Documents Created
            "main_documents": {
                "Vendor Master": {
                    "link_fields": {
                        "country": "Country Master",
                        "vendor_title": "Vendor Title",
                        "onboarding_ref_no": "Vendor Onboarding",
                        "bank_details": "Vendor Bank Details",
                        "document_details": "Vendor Document Details",
                        "manufacturing_details": "Vendor Manufacturing Details"
                    },
                    "child_tables": {
                        "multiple_company_data": "Multiple Company Data",
                        "vendor_types": "Vendor Type Group",
                        "vendor_onb_records": "Vendor Onboarding Records",
                        "vendor_company_details": "Imported Vendor Company"
                    }
                },
                
                "Company Vendor Code": {
                    "link_fields": {
                        "vendor_ref_no": "Vendor Master",
                        "company_name": "Company Master"
                    },
                    "child_tables": {
                        "vendor_code": "Vendor Code Child"  # Child table with state, vendor_code, gst_no
                    }
                },
                
                "Vendor Onboarding Company Details": {
                    "link_fields": {
                        "company_name": "Company Master",
                        "type_of_business": "Type of Business", 
                        "nature_of_company": "Company Nature Master",
                        "ref_no": "Vendor Onboarding"
                    },
                    "child_tables": {
                        "multiple_location_table": "Multiple Location Table Child Table"
                    }
                },
                
                "Vendor Bank Details": {
                    "link_fields": {
                        "ref_no": "Vendor Master",
                        "bank_name": "Bank Master",
                        "currency": "Currency Master",
                        "country": "Country Master",
                        "vendor_onboarding": "Vendor Onboarding"
                    },
                    "child_tables": {
                        "banker_details": "Banker Details",
                        "international_bank_details": "International Bank Details",
                        "intermediate_bank_details": "Intermediate Bank Details"
                    }
                }
            },
            
            # Child Table Schemas
            "child_table_schemas": {
                "Multiple Company Data": {
                    "link_fields": {
                        "company_name": "Company Master",
                        "purchase_organization": "Purchase Organization Master",
                        "account_group": "Account Group Master",
                        "terms_of_payment": "Terms of Payment Master",
                        "purchase_group": "Purchase Group Master",
                        "order_currency": "Currency Master",
                        "incoterm": "Incoterm Master",
                        "reconciliation_account": "Reconciliation Account",
                        "company_vendor_code": "Company Vendor Code"
                    }
                },
                
                "Vendor Type Group": {
                    "link_fields": {
                        "vendor_type": "Vendor Type Master"
                    }
                },
                
                "Banker Details": {
                    "link_fields": {
                        "bank_name": "Bank Master"
                    }
                },
                
                "International Bank Details": {
                    "link_fields": {
                        "beneficiary_currency": "Currency Master"
                    }
                },
                
                "Intermediate Bank Details": {
                    "link_fields": {
                        "intermediate_currency": "Currency Master"
                    }
                },
                
                "Multiple Location Table Child Table": {
                    "link_fields": {
                        "state": "State Master"
                    }
                }
            }
        }
        
        return document_schema
    
    @staticmethod
    def validate_complete_data_integrity(staging_doc):
        """
        Validate data integrity for ALL documents that will be created
        """
        
        validation_results = {
            "overall_status": "Valid",
            "staging_validation": {},
            "main_documents_validation": {},
            "child_tables_validation": {},
            "missing_masters": defaultdict(set),
            "critical_errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # 1. Validate Staging Document Fields
            staging_validation = VendorImportDataIntegritySystem.validate_staging_fields(staging_doc)
            validation_results["staging_validation"] = staging_validation
            
            if staging_validation.get("errors"):
                validation_results["critical_errors"].extend(staging_validation["errors"])
                validation_results["overall_status"] = "Invalid"
            
            # 2. Validate Main Documents That Will Be Created
            main_doc_validation = VendorImportDataIntegritySystem.validate_main_documents_integrity(staging_doc)
            validation_results["main_documents_validation"] = main_doc_validation
            
            if main_doc_validation.get("errors"):
                validation_results["critical_errors"].extend(main_doc_validation["errors"])
                validation_results["overall_status"] = "Invalid"
            
            # 3. Validate Child Tables That Will Be Created
            child_validation = VendorImportDataIntegritySystem.validate_child_tables_integrity(staging_doc)
            validation_results["child_tables_validation"] = child_validation
            
            if child_validation.get("errors"):
                validation_results["critical_errors"].extend(child_validation["errors"])
                validation_results["overall_status"] = "Invalid"
            
            # 4. Collect Missing Masters
            validation_results["missing_masters"] = VendorImportDataIntegritySystem.collect_missing_masters(
                staging_validation, main_doc_validation, child_validation
            )
            
            # 5. Generate Recommendations
            validation_results["recommendations"] = VendorImportDataIntegritySystem.generate_comprehensive_recommendations(
                validation_results, staging_doc
            )
            
        except Exception as e:
            validation_results["critical_errors"].append(f"System error during validation: {str(e)}")
            validation_results["overall_status"] = "Error"
            frappe.log_error(f"Error in complete data integrity validation: {str(e)}")
        
        return validation_results
    
    @staticmethod
    def validate_staging_fields(staging_doc):
        """Validate staging document fields"""
        
        validation = {
            "errors": [],
            "warnings": [],
            "field_validation": {},
            "missing_masters": defaultdict(set)
        }
        
        # Basic required field validation
        required_fields = ["vendor_name", "vendor_code", "c_code"]
        for field in required_fields:
            if not getattr(staging_doc, field, None):
                validation["errors"].append(f"Required field '{field}' is missing")
        
        # Format validation
        if staging_doc.gstn_no:
            gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
            if not re.match(gst_pattern, staging_doc.gstn_no.upper()):
                validation["errors"].append("Invalid GST number format")
        
        if staging_doc.pan_no:
            pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
            if not re.match(pan_pattern, staging_doc.pan_no.upper()):
                validation["errors"].append("Invalid PAN number format")
        
        # Check if Company Master exists (critical for all downstream docs)
        if staging_doc.c_code:
            if not frappe.db.exists("Company Master", {"company_code": staging_doc.c_code}):
                validation["errors"].append(f"Company Master not found for code: {staging_doc.c_code}")
                validation["missing_masters"]["Company Master"].add(staging_doc.c_code)
        
        return validation
    
    @staticmethod 
    def validate_main_documents_integrity(staging_doc):
        """
        Validate integrity for main documents that will be created
        """
        
        validation = {
            "errors": [],
            "warnings": [],
            "documents": {},
            "missing_masters": defaultdict(set)
        }
        
        schema = VendorImportDataIntegritySystem.get_complete_document_schema()
        
        # Validate Vendor Master integrity
        vendor_master_validation = VendorImportDataIntegritySystem.validate_vendor_master_integrity(staging_doc)
        validation["documents"]["Vendor Master"] = vendor_master_validation
        
        # Validate Company Vendor Code integrity  
        cvc_validation = VendorImportDataIntegritySystem.validate_company_vendor_code_integrity(staging_doc)
        validation["documents"]["Company Vendor Code"] = cvc_validation
        
        # Validate Vendor Onboarding Company Details integrity
        company_details_validation = VendorImportDataIntegritySystem.validate_company_details_integrity(staging_doc)
        validation["documents"]["Vendor Onboarding Company Details"] = company_details_validation
        
        # Validate Vendor Bank Details integrity
        bank_details_validation = VendorImportDataIntegritySystem.validate_bank_details_integrity(staging_doc)
        validation["documents"]["Vendor Bank Details"] = bank_details_validation
        
        # Collect all errors
        for doc_name, doc_validation in validation["documents"].items():
            if doc_validation.get("errors"):
                validation["errors"].extend([f"{doc_name}: {error}" for error in doc_validation["errors"]])
            if doc_validation.get("warnings"):
                validation["warnings"].extend([f"{doc_name}: {warning}" for warning in doc_validation["warnings"]])
            if doc_validation.get("missing_masters"):
                for doctype, values in doc_validation["missing_masters"].items():
                    validation["missing_masters"][doctype].update(values)
        
        return validation
    
    @staticmethod
    def validate_vendor_master_integrity(staging_doc):
        """Validate Vendor Master document integrity"""
        
        validation = {
            "errors": [],
            "warnings": [], 
            "missing_masters": defaultdict(set)
        }
        
        # Country validation
        if staging_doc.country:
            if not frappe.db.exists("Country Master", staging_doc.country):
                validation["warnings"].append(f"Country Master '{staging_doc.country}' not found")
                validation["missing_masters"]["Country Master"].add(staging_doc.country)
        
        # Vendor type validation
        if staging_doc.vendor_type:
            if not frappe.db.exists("Vendor Type Master", staging_doc.vendor_type):
                validation["warnings"].append(f"Vendor Type Master '{staging_doc.vendor_type}' not found")
                validation["missing_masters"]["Vendor Type Master"].add(staging_doc.vendor_type)
        
        return validation
    
    @staticmethod 
    def validate_company_vendor_code_integrity(staging_doc):
        """Validate Company Vendor Code document integrity"""
        
        validation = {
            "errors": [],
            "warnings": [],
            "missing_masters": defaultdict(set)
        }
        
        # Company Master validation (critical)
        if staging_doc.c_code:
            company_exists = frappe.db.exists("Company Master", {"company_code": staging_doc.c_code})
            if not company_exists:
                validation["errors"].append(f"Company Master with code '{staging_doc.c_code}' not found")
                validation["missing_masters"]["Company Master"].add(staging_doc.c_code)
        
        # State validation for vendor code child table
        if staging_doc.state:
            if not frappe.db.exists("State Master", staging_doc.state):
                validation["warnings"].append(f"State Master '{staging_doc.state}' not found")
                validation["missing_masters"]["State Master"].add(staging_doc.state)
        
        return validation
    
    @staticmethod
    def validate_company_details_integrity(staging_doc):
        """Validate Vendor Onboarding Company Details integrity"""
        
        validation = {
            "errors": [],
            "warnings": [],
            "missing_masters": defaultdict(set)
        }
        
        # Company Master validation
        if staging_doc.c_code:
            company_exists = frappe.db.exists("Company Master", {"company_code": staging_doc.c_code})
            if not company_exists:
                validation["errors"].append(f"Company Master with code '{staging_doc.c_code}' not found")
                validation["missing_masters"]["Company Master"].add(staging_doc.c_code)
        
        # Type of Business validation
        if staging_doc.type_of_industry:
            if not frappe.db.exists("Type of Business", staging_doc.type_of_industry):
                validation["warnings"].append(f"Type of Business '{staging_doc.type_of_industry}' not found")
                validation["missing_masters"]["Type of Business"].add(staging_doc.type_of_industry)
        
        # Nature of Company validation 
        if staging_doc.nature:
            if not frappe.db.exists("Company Nature Master", staging_doc.nature):
                validation["warnings"].append(f"Company Nature Master '{staging_doc.nature}' not found")
                validation["missing_masters"]["Company Nature Master"].add(staging_doc.nature)
        
        return validation
    
    @staticmethod
    def validate_bank_details_integrity(staging_doc):
        """Validate Vendor Bank Details integrity"""
        
        validation = {
            "errors": [],
            "warnings": [],
            "missing_masters": defaultdict(set)
        }
        
        # Bank Master validation
        if staging_doc.bank_name:
            if not frappe.db.exists("Bank Master", staging_doc.bank_name):
                validation["warnings"].append(f"Bank Master '{staging_doc.bank_name}' not found")
                validation["missing_masters"]["Bank Master"].add(staging_doc.bank_name)
        
        # Currency validation
        if staging_doc.order_currency:
            if not frappe.db.exists("Currency Master", staging_doc.order_currency):
                validation["warnings"].append(f"Currency Master '{staging_doc.order_currency}' not found")
                validation["missing_masters"]["Currency Master"].add(staging_doc.order_currency)
        
        # Beneficiary currency validation
        if staging_doc.beneficiary_currency:
            if not frappe.db.exists("Currency Master", staging_doc.beneficiary_currency):
                validation["warnings"].append(f"Currency Master '{staging_doc.beneficiary_currency}' not found")
                validation["missing_masters"]["Currency Master"].add(staging_doc.beneficiary_currency)
        
        return validation
    
    @staticmethod
    def validate_child_tables_integrity(staging_doc):
        """Validate child table integrity"""
        
        validation = {
            "errors": [],
            "warnings": [],
            "child_tables": {},
            "missing_masters": defaultdict(set)
        }
        
        # Multiple Company Data validation
        mcd_validation = VendorImportDataIntegritySystem.validate_multiple_company_data(staging_doc)
        validation["child_tables"]["Multiple Company Data"] = mcd_validation
        
        # Collect errors from child tables
        if mcd_validation.get("errors"):
            validation["errors"].extend(mcd_validation["errors"])
        if mcd_validation.get("warnings"):
            validation["warnings"].extend(mcd_validation["warnings"])
        if mcd_validation.get("missing_masters"):
            for doctype, values in mcd_validation["missing_masters"].items():
                validation["missing_masters"][doctype].update(values)
        
        return validation
    
    @staticmethod
    def validate_multiple_company_data(staging_doc):
        """Validate Multiple Company Data child table"""
        
        validation = {
            "errors": [],
            "warnings": [],
            "missing_masters": defaultdict(set)
        }
        
        # Purchase Organization validation
        if staging_doc.purchase_organization:
            if not frappe.db.exists("Purchase Organization Master", staging_doc.purchase_organization):
                validation["warnings"].append(f"Purchase Organization Master '{staging_doc.purchase_organization}' not found")
                validation["missing_masters"]["Purchase Organization Master"].add(staging_doc.purchase_organization)
        
        # Account Group validation
        if staging_doc.account_group:
            if not frappe.db.exists("Account Group Master", staging_doc.account_group):
                validation["warnings"].append(f"Account Group Master '{staging_doc.account_group}' not found")
                validation["missing_masters"]["Account Group Master"].add(staging_doc.account_group)
        
        # Terms of Payment validation
        if staging_doc.terms_of_payment:
            if not frappe.db.exists("Terms of Payment Master", staging_doc.terms_of_payment):
                validation["warnings"].append(f"Terms of Payment Master '{staging_doc.terms_of_payment}' not found")
                validation["missing_masters"]["Terms of Payment Master"].add(staging_doc.terms_of_payment)
        
        # Purchase Group validation
        if staging_doc.purchase_group:
            if not frappe.db.exists("Purchase Group Master", staging_doc.purchase_group):
                validation["warnings"].append(f"Purchase Group Master '{staging_doc.purchase_group}' not found")
                validation["missing_masters"]["Purchase Group Master"].add(staging_doc.purchase_group)
        
        # Order Currency validation
        if staging_doc.order_currency:
            if not frappe.db.exists("Currency Master", staging_doc.order_currency):
                validation["warnings"].append(f"Currency Master '{staging_doc.order_currency}' not found")
                validation["missing_masters"]["Currency Master"].add(staging_doc.order_currency)
        
        # Incoterm validation
        if staging_doc.incoterm:
            if not frappe.db.exists("Incoterm Master", staging_doc.incoterm):
                validation["warnings"].append(f"Incoterm Master '{staging_doc.incoterm}' not found")
                validation["missing_masters"]["Incoterm Master"].add(staging_doc.incoterm)
        
        # Reconciliation Account validation
        if staging_doc.reconciliation_account:
            if not frappe.db.exists("Reconciliation Account", staging_doc.reconciliation_account):
                validation["warnings"].append(f"Reconciliation Account '{staging_doc.reconciliation_account}' not found")
                validation["missing_masters"]["Reconciliation Account"].add(staging_doc.reconciliation_account)
        
        return validation
    
    @staticmethod
    def collect_missing_masters(staging_validation, main_doc_validation, child_validation):
        """Collect all missing masters from all validations"""
        
        all_missing = defaultdict(set)
        
        # From staging validation
        if staging_validation.get("missing_masters"):
            for doctype, values in staging_validation["missing_masters"].items():
                all_missing[doctype].update(values)
        
        # From main documents validation
        if main_doc_validation.get("missing_masters"):
            for doctype, values in main_doc_validation["missing_masters"].items():
                all_missing[doctype].update(values)
        
        # From child tables validation
        if child_validation.get("missing_masters"):
            for doctype, values in child_validation["missing_masters"].items():
                all_missing[doctype].update(values)
        
        return dict(all_missing)
    
    @staticmethod
    def generate_comprehensive_recommendations(validation_results, staging_doc):
        """Generate comprehensive recommendations for all validation issues"""
        
        recommendations = []
        
        # Critical errors first
        if validation_results["critical_errors"]:
            recommendations.append("🔴 CRITICAL: Fix these errors before processing:")
            for error in validation_results["critical_errors"][:5]:
                recommendations.append(f"  • {error}")
        
        # Missing masters recommendations
        missing_masters = validation_results["missing_masters"]
        if missing_masters:
            recommendations.append("📋 CREATE MISSING MASTER DATA:")
            for doctype, values in missing_masters.items():
                if len(values) <= 3:
                    recommendations.append(f"  • {doctype}: {', '.join(list(values))}")
                else:
                    recommendations.append(f"  • {doctype}: {len(values)} missing records")
        
        # Document-specific recommendations
        main_doc_issues = validation_results.get("main_documents_validation", {})
        if main_doc_issues.get("errors"):
            recommendations.append("🔧 FIX MAIN DOCUMENT ISSUES:")
            for error in main_doc_issues["errors"][:3]:
                recommendations.append(f"  • {error}")
        
        # Child table recommendations
        child_table_issues = validation_results.get("child_tables_validation", {})
        if child_table_issues.get("errors"):
            recommendations.append("🔗 FIX CHILD TABLE LINK ISSUES:")
            for error in child_table_issues["errors"][:3]:
                recommendations.append(f"  • {error}")
        
        # Processing readiness
        if validation_results["overall_status"] == "Valid":
            recommendations.append("✅ READY FOR PROCESSING: All critical validations passed")
            if validation_results.get("warnings"):
                recommendations.append("⚠️ Consider fixing warnings for better data quality")
        else:
            recommendations.append("❌ NOT READY: Fix critical errors before vendor master creation")
        
        return recommendations


# API METHODS FOR ENHANCED DATA INTEGRITY SYSTEM


@frappe.whitelist() 
def check_missing_masters_for_single_record(docname):
    """Check missing masters for a single record"""
    
    try:
        staging_doc = frappe.get_doc("Vendor Import Staging", docname)
        missing_masters = []
        
        # Check key masters
        if staging_doc.c_code:
            if not frappe.db.exists("Company Master", {"company_code": staging_doc.c_code}):
                missing_masters.append({"doctype": "Company Master", "value": staging_doc.c_code})
        
        if staging_doc.state:
            if not frappe.db.exists("State Master", staging_doc.state):
                missing_masters.append({"doctype": "State Master", "value": staging_doc.state})
        
        if staging_doc.bank_name:
            if not frappe.db.exists("Bank Master", staging_doc.bank_name):
                missing_masters.append({"doctype": "Bank Master", "value": staging_doc.bank_name})
        
        return missing_masters
        
    except Exception as e:
        return [{"doctype": "Error", "value": str(e)[:100]}]


print("✅ Updated Validation System loaded successfully!")


@frappe.whitelist()
def comprehensive_data_integrity_check():
    """Run comprehensive data integrity check on all staging records"""
    
    try:
        integrity_data = {
            "timestamp": now_datetime(),
            "overall_status": "Healthy",
            "total_records": 0,
            "validation_summary": {
                "valid_records": 0,
                "invalid_records": 0,
                "warning_records": 0
            },
            "document_integrity_analysis": {},
            "missing_masters_analysis": {},
            "child_table_issues": {},
            "processing_readiness": {},
            "recommendations": []
        }
        
        # Get staging records to validate
        staging_records = frappe.get_all("Vendor Import Staging",
            filters={"import_status": ["in", ["Pending", "Failed"]]},
            fields=["name"],
            limit=500  # Process in manageable batches
        )
        
        integrity_data["total_records"] = len(staging_records)
        
        if not staging_records:
            integrity_data["overall_status"] = "No Records"
            return integrity_data
        
        # Analyze each record
        all_missing_masters = defaultdict(lambda: defaultdict(int))
        document_issues = defaultdict(int)
        child_table_issues = defaultdict(int)
        
        for record in staging_records:
            try:
                staging_doc = frappe.get_doc("Vendor Import Staging", record.name)
                
                # Run comprehensive validation
                validation_results = VendorImportDataIntegritySystem.validate_complete_data_integrity(staging_doc)
                
                # Categorize record
                if validation_results["overall_status"] == "Valid":
                    integrity_data["validation_summary"]["valid_records"] += 1
                elif validation_results.get("critical_errors"):
                    integrity_data["validation_summary"]["invalid_records"] += 1
                else:
                    integrity_data["validation_summary"]["warning_records"] += 1
                
                # Collect missing masters statistics
                for doctype, values in validation_results.get("missing_masters", {}).items():
                    for value in values:
                        all_missing_masters[doctype][value] += 1
                
                # Collect document issues
                main_doc_validation = validation_results.get("main_documents_validation", {})
                for doc_name, doc_validation in main_doc_validation.get("documents", {}).items():
                    if doc_validation.get("errors"):
                        document_issues[doc_name] += len(doc_validation["errors"])
                
                # Collect child table issues
                child_validation = validation_results.get("child_tables_validation", {})
                for child_name, child_data in child_validation.get("child_tables", {}).items():
                    if child_data.get("errors"):
                        child_table_issues[child_name] += len(child_data["errors"])
                        
            except Exception as e:
                frappe.log_error(f"Error validating record {record.name}: {str(e)}")
                integrity_data["validation_summary"]["invalid_records"] += 1
        
        # Process missing masters analysis
        integrity_data["missing_masters_analysis"] = VendorImportDataIntegritySystem.process_missing_masters_analysis(all_missing_masters)
        
        # Process document integrity analysis
        integrity_data["document_integrity_analysis"] = dict(document_issues)
        integrity_data["child_table_issues"] = dict(child_table_issues)
        
        # Calculate overall health
        total_records = integrity_data["total_records"]
        if total_records > 0:
            invalid_percentage = (integrity_data["validation_summary"]["invalid_records"] / total_records) * 100
            
            if invalid_percentage < 5:
                integrity_data["overall_status"] = "Excellent"
            elif invalid_percentage < 15:
                integrity_data["overall_status"] = "Good"
            elif invalid_percentage < 30:
                integrity_data["overall_status"] = "Warning"
            else:
                integrity_data["overall_status"] = "Critical"
        
        # Generate system recommendations
        integrity_data["recommendations"] = VendorImportDataIntegritySystem.generate_system_recommendations(integrity_data)
        
        return integrity_data
        
    except Exception as e:
        frappe.log_error(f"Error in comprehensive data integrity check: {str(e)}")
        return {
            "overall_status": "Error",
            "error": str(e),
            "timestamp": now_datetime()
        }


@frappe.whitelist()
def single_record_comprehensive_check(docname):
    """Run comprehensive check on a single staging record"""
    
    try:
        staging_doc = frappe.get_doc("Vendor Import Staging", docname)
        
        # Run comprehensive validation
        validation_results = VendorImportDataIntegritySystem.validate_complete_data_integrity(staging_doc)
        
        # Enhanced results with processing readiness
        enhanced_results = {
            "record_name": docname,
            "vendor_name": staging_doc.vendor_name,
            "company_code": staging_doc.c_code,
            "validation_results": validation_results,
            "processing_readiness": VendorImportDataIntegritySystem.assess_processing_readiness(validation_results),
            "document_creation_preview": VendorImportDataIntegritySystem.generate_document_creation_preview(staging_doc),
            "checked_at": now_datetime()
        }
        
        return enhanced_results
        
    except Exception as e:
        frappe.log_error(f"Error in single record comprehensive check: {str(e)}")
        return {
            "overall_status": "Error",
            "error": str(e),
            "checked_at": now_datetime()
        }


@frappe.whitelist()
def get_missing_masters_breakdown():
    """Get detailed breakdown of missing master data across all staging records"""
    
    try:
        # Run comprehensive check
        integrity_data = comprehensive_data_integrity_check()
        
        missing_masters = integrity_data.get("missing_masters_analysis", {})
        
        breakdown = {
            "timestamp": now_datetime(),
            "summary": {
                "total_doctypes_affected": len(missing_masters),
                "total_missing_records": sum(
                    sum(items.values()) for items in missing_masters.values()
                )
            },
            "detailed_breakdown": {},
            "priority_actions": []
        }
        
        # Process each doctype
        for doctype, missing_items in missing_masters.items():
            breakdown["detailed_breakdown"][doctype] = {
                "total_missing": len(missing_items),
                "total_references": sum(missing_items.values()),
                "missing_items": dict(missing_items),
                "priority": VendorImportDataIntegritySystem.calculate_priority(missing_items)
            }
        
        # Generate priority actions
        breakdown["priority_actions"] = VendorImportDataIntegritySystem.generate_priority_actions(missing_masters)
        
        return breakdown
        
    except Exception as e:
        frappe.log_error(f"Error getting missing masters breakdown: {str(e)}")
        return {"error": str(e)}


# HELPER METHODS

class VendorImportDataIntegritySystem:
    
    @staticmethod
    def process_missing_masters_analysis(all_missing_masters):
        """Process missing masters for analysis"""
        
        analysis = {}
        for doctype, items_count in all_missing_masters.items():
            analysis[doctype] = dict(items_count)
        
        return analysis
    
    @staticmethod
    def assess_processing_readiness(validation_results):
        """Assess if record is ready for vendor master creation"""
        
        readiness = {
            "ready": validation_results["overall_status"] in ["Valid"],
            "confidence_level": "Low",
            "blocking_issues": validation_results.get("critical_errors", []),
            "warnings_count": len(validation_results.get("warnings", [])),
            "missing_masters_count": sum(
                len(values) for values in validation_results.get("missing_masters", {}).values()
            )
        }
        
        if readiness["ready"]:
            if readiness["warnings_count"] == 0 and readiness["missing_masters_count"] == 0:
                readiness["confidence_level"] = "High"
            elif readiness["warnings_count"] <= 2 and readiness["missing_masters_count"] <= 3:
                readiness["confidence_level"] = "Medium"
            else:
                readiness["confidence_level"] = "Low"
        
        return readiness
    
    @staticmethod
    def generate_document_creation_preview(staging_doc):
        """Generate preview of documents that will be created"""
        
        preview = {
            "main_documents": [],
            "child_tables": [],
            "estimated_records": 0
        }
        
        # Main documents that will be created
        preview["main_documents"] = [
            {
                "doctype": "Vendor Master",
                "key_fields": {
                    "vendor_name": staging_doc.vendor_name,
                    "country": staging_doc.country
                }
            },
            {
                "doctype": "Company Vendor Code", 
                "key_fields": {
                    "company_code": staging_doc.c_code,
                    "vendor_code": staging_doc.vendor_code
                }
            },
            {
                "doctype": "Vendor Onboarding Company Details",
                "key_fields": {
                    "company_name": staging_doc.c_code,
                    "gst": staging_doc.gstn_no
                }
            }
        ]
        
        # Add bank details if bank data exists
        if staging_doc.bank_name or staging_doc.account_number:
            preview["main_documents"].append({
                "doctype": "Vendor Bank Details",
                "key_fields": {
                    "bank_name": staging_doc.bank_name,
                    "account_number": staging_doc.account_number
                }
            })
        
        # Child tables that will be created
        preview["child_tables"] = [
            {
                "parent_doctype": "Vendor Master",
                "child_table": "Multiple Company Data",
                "records_count": 1 if staging_doc.c_code else 0
            },
            {
                "parent_doctype": "Company Vendor Code",
                "child_table": "Vendor Code Child", 
                "records_count": 1 if staging_doc.vendor_code else 0
            }
        ]
        
        # Add vendor types if exists
        if staging_doc.vendor_type:
            preview["child_tables"].append({
                "parent_doctype": "Vendor Master",
                "child_table": "Vendor Type Group",
                "records_count": 1
            })
        
        # Calculate estimated total records
        preview["estimated_records"] = len(preview["main_documents"]) + sum(
            ct["records_count"] for ct in preview["child_tables"]
        )
        
        return preview
    
    @staticmethod
    def calculate_priority(missing_items):
        """Calculate priority based on number of references"""
        
        total_refs = sum(missing_items.values())
        
        if total_refs >= 50:
            return "High"
        elif total_refs >= 10:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def generate_priority_actions(missing_masters):
        """Generate priority actions for missing masters"""
        
        actions = []
        
        # Sort by impact
        sorted_masters = sorted(
            missing_masters.items(),
            key=lambda x: sum(x[1].values()),
            reverse=True
        )
        
        for doctype, items in sorted_masters[:5]:  # Top 5 priorities
            total_refs = sum(items.values())
            unique_items = len(items)
            
            actions.append({
                "priority": VendorImportDataIntegritySystem.calculate_priority(items),
                "doctype": doctype,
                "action": f"Create {unique_items} missing {doctype} records",
                "impact": f"Affects {total_refs} staging records",
                "missing_items": list(items.keys())[:5]  # Show first 5 items
            })
        
        return actions
    
    @staticmethod
    def generate_system_recommendations(integrity_data):
        """Generate system-level recommendations"""
        
        recommendations = []
        
        # Overall health recommendations
        if integrity_data["overall_status"] == "Critical":
            recommendations.append("🚨 CRITICAL: System requires immediate attention")
        elif integrity_data["overall_status"] == "Warning":
            recommendations.append("⚠️ WARNING: Multiple data quality issues detected")
        
        # Missing masters recommendations
        missing_analysis = integrity_data.get("missing_masters_analysis", {})
        if missing_analysis:
            high_priority = [
                doctype for doctype, items in missing_analysis.items()
                if sum(items.values()) >= 10
            ]
            if high_priority:
                recommendations.append(f"📋 HIGH PRIORITY: Create missing masters for {', '.join(high_priority)}")
        
        # Document integrity recommendations
        doc_issues = integrity_data.get("document_integrity_analysis", {})
        if doc_issues:
            recommendations.append("🔧 Fix document integrity issues before processing")
        
        # Processing recommendations
        valid_count = integrity_data["validation_summary"]["valid_records"]
        if valid_count > 0:
            recommendations.append(f"✅ {valid_count} records ready for processing")
        
        return recommendations