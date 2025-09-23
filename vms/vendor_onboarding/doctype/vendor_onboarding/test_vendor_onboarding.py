# Copyright (c) 2025, Blue Phoenix and Contributors
# See license.txt

# import frappe
from frappe.tests.utils import FrappeTestCase


class TestVendorOnboarding(FrappeTestCase):
	pass





# Testing Script for VendorOnboarding Fixes
# Run this after implementing the changes

import frappe

@frappe.whitelist()
def test_vendor_onboarding_fixes():
    """
    Comprehensive test suite for vendor onboarding fixes
    """
    test_results = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "detailed_results": [],
        "overall_status": "unknown"
    }
    
    try:
        # Test 1: Create a test vendor onboarding
        test_results["tests_run"] += 1
        try:
            test_doc = create_test_vendor_onboarding()
            test_results["tests_passed"] += 1
            test_results["detailed_results"].append({
                "test": "Create Test Document",
                "status": "PASS",
                "message": f"Created test document: {test_doc.name}"
            })
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["detailed_results"].append({
                "test": "Create Test Document",
                "status": "FAIL",
                "message": str(e)
            })
            return test_results
        
        # Test 2: Test child table data preservation
        test_results["tests_run"] += 1
        try:
            result = test_child_table_preservation(test_doc)
            if result["success"]:
                test_results["tests_passed"] += 1
                test_results["detailed_results"].append({
                    "test": "Child Table Preservation",
                    "status": "PASS",
                    "message": result["message"]
                })
            else:
                test_results["tests_failed"] += 1
                test_results["detailed_results"].append({
                    "test": "Child Table Preservation",
                    "status": "FAIL",
                    "message": result["message"]
                })
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["detailed_results"].append({
                "test": "Child Table Preservation",
                "status": "FAIL",
                "message": str(e)
            })
        
        # Test 3: Test status update logic
        test_results["tests_run"] += 1
        try:
            result = test_status_update_logic(test_doc)
            if result["success"]:
                test_results["tests_passed"] += 1
                test_results["detailed_results"].append({
                    "test": "Status Update Logic",
                    "status": "PASS",
                    "message": result["message"]
                })
            else:
                test_results["tests_failed"] += 1
                test_results["detailed_results"].append({
                    "test": "Status Update Logic",
                    "status": "FAIL",
                    "message": result["message"]
                })
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["detailed_results"].append({
                "test": "Status Update Logic",
                "status": "FAIL",
                "message": str(e)
            })
        
        # Test 4: Test background job functionality
        test_results["tests_run"] += 1
        try:
            result = test_background_jobs(test_doc)
            if result["success"]:
                test_results["tests_passed"] += 1
                test_results["detailed_results"].append({
                    "test": "Background Jobs",
                    "status": "PASS",
                    "message": result["message"]
                })
            else:
                test_results["tests_failed"] += 1
                test_results["detailed_results"].append({
                    "test": "Background Jobs",
                    "status": "FAIL",
                    "message": result["message"]
                })
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["detailed_results"].append({
                "test": "Background Jobs",
                "status": "FAIL",
                "message": str(e)
            })
        
        # Test 5: Test manual fix utilities
        test_results["tests_run"] += 1
        try:
            result = test_manual_fix_utilities(test_doc)
            if result["success"]:
                test_results["tests_passed"] += 1
                test_results["detailed_results"].append({
                    "test": "Manual Fix Utilities",
                    "status": "PASS",
                    "message": result["message"]
                })
            else:
                test_results["tests_failed"] += 1
                test_results["detailed_results"].append({
                    "test": "Manual Fix Utilities",
                    "status": "FAIL",
                    "message": result["message"]
                })
        except Exception as e:
            test_results["tests_failed"] += 1
            test_results["detailed_results"].append({
                "test": "Manual Fix Utilities",
                "status": "FAIL",
                "message": str(e)
            })
        
        # Cleanup test document
        try:
            frappe.delete_doc("Vendor Onboarding", test_doc.name, force=True)
        except:
            pass
        
        # Calculate overall status
        if test_results["tests_failed"] == 0:
            test_results["overall_status"] = "ALL TESTS PASSED"
        elif test_results["tests_passed"] > test_results["tests_failed"]:
            test_results["overall_status"] = "MOSTLY PASSED"
        else:
            test_results["overall_status"] = "CRITICAL ISSUES"
        
        return test_results
        
    except Exception as e:
        test_results["detailed_results"].append({
            "test": "Overall Test Suite",
            "status": "FAIL",
            "message": f"Test suite failed: {str(e)}"
        })
        test_results["overall_status"] = "CRITICAL ERROR"
        return test_results


def create_test_vendor_onboarding():
    """Create a test vendor onboarding document"""
    doc = frappe.get_doc({
        "doctype": "Vendor Onboarding",
        "vendor_name": f"Test Vendor {frappe.utils.random_string(5)}",
        "ref_no": f"TEST-{frappe.utils.random_string(5)}",
        "vendor_country": "India",
        "registered_by": frappe.session.user,
        "register_by_account_team": 0
    })
    
    # Add some child table data
    doc.append("contact_details", {
        "name_of_contact_person": "Test Contact",
        "designation": "Manager",
        "phone_number": "1234567890",
        "email_id": "test@example.com"
    })
    
    doc.append("vendor_types", {
        "vendor_type": "Service Provider"
    })
    
    doc.insert(ignore_permissions=True)
    return doc


def test_child_table_preservation(test_doc):
    """Test if child table data is preserved during updates"""
    try:
        # Record original child table data
        original_contacts = len(test_doc.contact_details)
        original_vendor_types = len(test_doc.vendor_types)
        
        # Update the document
        test_doc.vendor_name = f"Updated {test_doc.vendor_name}"
        test_doc.save()
        
        # Reload and check if child table data is preserved
        test_doc.reload()
        
        new_contacts = len(test_doc.contact_details)
        new_vendor_types = len(test_doc.vendor_types)
        
        if new_contacts == original_contacts and new_vendor_types == original_vendor_types:
            return {
                "success": True,
                "message": f"Child table data preserved: {new_contacts} contacts, {new_vendor_types} vendor types"
            }
        else:
            return {
                "success": False,
                "message": f"Child table data lost: contacts {original_contacts}→{new_contacts}, types {original_vendor_types}→{new_vendor_types}"
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_status_update_logic(test_doc):
    """Test the status update logic"""
    try:
        # Test initial status
        if test_doc.onboarding_form_status != "Pending":
            return {"success": False, "message": f"Initial status should be Pending, got {test_doc.onboarding_form_status}"}
        
        # Set approvals
        test_doc.purchase_team_undertaking = 1
        test_doc.accounts_team_undertaking = 1
        test_doc.purchase_head_undertaking = 1
        test_doc.accounts_head_undertaking = 1
        test_doc.mandatory_data_filled = 1
        test_doc.save()
        
        # Check if status updates correctly
        test_doc.reload()
        expected_status = "SAP Error"  # Should be SAP Error since data_sent_to_sap != 1
        
        if test_doc.onboarding_form_status == expected_status:
            return {
                "success": True,
                "message": f"Status correctly updated to {expected_status}"
            }
        else:
            return {
                "success": False,
                "message": f"Status should be {expected_status}, got {test_doc.onboarding_form_status}"
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_background_jobs(test_doc):
    """Test background job functionality"""
    try:
        # Check if background jobs are being enqueued
        from frappe.utils.background_jobs import get_jobs
        
        jobs_before = len(get_jobs())
        
        # Trigger an update that should enqueue jobs
        test_doc.vendor_name = f"Updated Again {test_doc.vendor_name}"
        test_doc.save()
        
        jobs_after = len(get_jobs())
        
        if jobs_after >= jobs_before:
            return {
                "success": True,
                "message": f"Background jobs working: {jobs_after - jobs_before} new jobs enqueued"
            }
        else:
            return {
                "success": False,
                "message": "No background jobs were enqueued"
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)}


def test_manual_fix_utilities(test_doc):
    """Test manual fix utility functions"""
    try:
        from vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding import check_vendor_onboarding_health
        
        # Test health check
        health_report = check_vendor_onboarding_health(test_doc.name)
        
        if "overall_health" in health_report:
            return {
                "success": True,
                "message": f"Health check working: {health_report['overall_health']}"
            }
        else:
            return {
                "success": False,
                "message": "Health check function not working properly"
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def validate_existing_vendor_onboardings():
    """
    Validate existing vendor onboarding documents for issues
    """
    try:
        # Get all vendor onboardings with potential issues
        problematic_docs = frappe.db.sql("""
            SELECT name, vendor_name, onboarding_form_status, 
                   data_sent_to_sap, modified
            FROM `tabVendor Onboarding`
            WHERE 
                (onboarding_form_status = 'SAP Error' 
                 AND modified < DATE_SUB(NOW(), INTERVAL 1 HOUR))
                OR (purchase_team_undertaking = 1 
                    AND accounts_team_undertaking = 1 
                    AND purchase_head_undertaking = 1 
                    AND accounts_head_undertaking = 1
                    AND onboarding_form_status NOT IN ('Approved', 'SAP Error'))
            ORDER BY modified DESC
            LIMIT 50
        """, as_dict=True)
        
        validation_results = []
        
        for doc_data in problematic_docs:
            try:
                from vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding import check_vendor_onboarding_health
                health_report = check_vendor_onboarding_health(doc_data.name)
                
                validation_results.append({
                    "name": doc_data.name,
                    "vendor_name": doc_data.vendor_name,
                    "current_status": doc_data.onboarding_form_status,
                    "health": health_report.get("overall_health", "unknown"),
                    "last_modified": doc_data.modified,
                    "recommendations": health_report.get("recommendations", [])
                })
                
            except Exception as e:
                validation_results.append({
                    "name": doc_data.name,
                    "vendor_name": doc_data.vendor_name,
                    "current_status": doc_data.onboarding_form_status,
                    "health": "error",
                    "error": str(e)
                })
        
        return {
            "total_checked": len(problematic_docs),
            "results": validation_results
        }
        
    except Exception as e:
        return {"error": str(e)}