# monitoring_dashboard.py
# Place this file in: vms/vendor_onboarding/monitoring_dashboard.py

import frappe
from frappe.utils import now, add_days, get_datetime
import json

@frappe.whitelist()
def get_monitoring_data():
    """Get comprehensive monitoring data"""
    try:
        data = {
            "stuck_documents": get_stuck_documents(),
            "sap_error_count": get_sap_error_count(),
            "pending_approvals": get_pending_approvals(),
            "system_health": get_system_health(),
            "summary_stats": get_summary_stats(),
            "recent_activities": get_recent_activities()
        }
        
        return {
            "status": "success",
            "data": data,
            "timestamp": now()
        }
    except Exception as e:
        frappe.log_error(f"Error in get_monitoring_data: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": now()
        }

def get_stuck_documents():
    """Get documents stuck in processing"""
    try:
        stuck_docs = frappe.db.sql("""
            SELECT 
                name, 
                ref_no, 
                vendor_name, 
                onboarding_form_status,
                modified,
                TIMESTAMPDIFF(HOUR, modified, NOW()) as hours_stuck
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status = 'SAP Error'
                AND data_sent_to_sap != 1
                AND purchase_team_undertaking = 1
                AND accounts_team_undertaking = 1
                AND purchase_head_undertaking = 1
                AND accounts_head_undertaking = 1
                AND modified < DATE_SUB(NOW(), INTERVAL 2 HOUR)
            ORDER BY modified DESC
            LIMIT 50
        """, as_dict=True)
        
        return {
            "count": len(stuck_docs),
            "documents": stuck_docs
        }
    except Exception as e:
        return {"count": 0, "documents": [], "error": str(e)}

def get_sap_error_count():
    """Get SAP error statistics"""
    try:
        # Today's SAP errors
        today_errors = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVMS SAP Logs`
            WHERE 
                transaction_status = 'Error'
                AND DATE(creation) = CURDATE()
        """, as_dict=True)[0].count
        
        # This week's SAP errors
        week_errors = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVMS SAP Logs`
            WHERE 
                transaction_status = 'Error'
                AND creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, as_dict=True)[0].count
        
        # Recent error details
        recent_errors = frappe.db.sql("""
            SELECT 
                vendor_onboarding,
                error_message,
                creation,
                response_data
            FROM `tabVMS SAP Logs`
            WHERE transaction_status = 'Error'
            ORDER BY creation DESC
            LIMIT 10
        """, as_dict=True)
        
        return {
            "today": today_errors,
            "week": week_errors,
            "recent_errors": recent_errors
        }
    except Exception as e:
        return {"today": 0, "week": 0, "recent_errors": [], "error": str(e)}

def get_pending_approvals():
    """Get pending approval statistics"""
    try:
        # Pending purchase team approvals
        purchase_pending = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status = 'Pending'
                AND purchase_team_undertaking = 0
                AND mail_sent_to_purchase_team = 1
        """, as_dict=True)[0].count
        
        # Pending accounts team approvals
        accounts_pending = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status = 'Pending'
                AND accounts_team_undertaking = 0
                AND mail_sent_to_account_team = 1
        """, as_dict=True)[0].count
        
        # Pending head approvals
        head_pending = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status = 'Pending'
                AND (purchase_head_undertaking = 0 OR accounts_head_undertaking = 0)
                AND (mail_sent_to_purchase_head = 1 OR mail_sent_to_account_head = 1)
        """, as_dict=True)[0].count
        
        # Overdue approvals (more than 3 days)
        overdue_approvals = frappe.db.sql("""
            SELECT 
                name, 
                vendor_name, 
                ref_no,
                modified,
                DATEDIFF(NOW(), modified) as days_pending
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status = 'Pending'
                AND modified < DATE_SUB(NOW(), INTERVAL 3 DAY)
            ORDER BY modified ASC
            LIMIT 20
        """, as_dict=True)
        
        return {
            "purchase_team": purchase_pending,
            "accounts_team": accounts_pending,
            "heads": head_pending,
            "overdue": {
                "count": len(overdue_approvals),
                "documents": overdue_approvals
            }
        }
    except Exception as e:
        return {
            "purchase_team": 0,
            "accounts_team": 0,
            "heads": 0,
            "overdue": {"count": 0, "documents": []},
            "error": str(e)
        }

def get_system_health():
    """Get overall system health metrics"""
    try:
        # Total documents in last 30 days
        total_docs = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, as_dict=True)[0].count
        
        # Approved documents in last 30 days
        approved_docs = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status = 'Approved'
                AND creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, as_dict=True)[0].count
        
        # Average processing time (in days)
        avg_processing_time = frappe.db.sql("""
            SELECT AVG(DATEDIFF(modified, creation)) as avg_days
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status = 'Approved'
                AND creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, as_dict=True)
        
        avg_days = avg_processing_time[0].avg_days if avg_processing_time and avg_processing_time[0].avg_days else 0
        
        # Success rate
        success_rate = (approved_docs / total_docs * 100) if total_docs > 0 else 0
        
        # System status based on metrics
        if success_rate >= 80 and avg_days <= 7:
            system_status = "excellent"
        elif success_rate >= 60 and avg_days <= 14:
            system_status = "good"
        elif success_rate >= 40:
            system_status = "warning"
        else:
            system_status = "critical"
        
        return {
            "total_documents": total_docs,
            "approved_documents": approved_docs,
            "success_rate": round(success_rate, 2),
            "avg_processing_days": round(avg_days, 2),
            "system_status": system_status
        }
    except Exception as e:
        return {
            "total_documents": 0,
            "approved_documents": 0,
            "success_rate": 0,
            "avg_processing_days": 0,
            "system_status": "error",
            "error": str(e)
        }

def get_summary_stats():
    """Get summary statistics for dashboard"""
    try:
        # Status distribution
        status_stats = frappe.db.sql("""
            SELECT 
                onboarding_form_status,
                COUNT(*) as count
            FROM `tabVendor Onboarding`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY onboarding_form_status
        """, as_dict=True)
        
        # Daily registrations for last 7 days
        daily_registrations = frappe.db.sql("""
            SELECT 
                DATE(creation) as date,
                COUNT(*) as count
            FROM `tabVendor Onboarding`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(creation)
            ORDER BY date DESC
        """, as_dict=True)
        
        return {
            "status_distribution": status_stats,
            "daily_registrations": daily_registrations
        }
    except Exception as e:
        return {
            "status_distribution": [],
            "daily_registrations": [],
            "error": str(e)
        }

def get_recent_activities():
    """Get recent system activities"""
    try:
        # Recent approvals
        recent_approvals = frappe.db.sql("""
            SELECT 
                name,
                vendor_name,
                onboarding_form_status,
                modified,
                modified_by
            FROM `tabVendor Onboarding`
            WHERE 
                onboarding_form_status IN ('Approved', 'Rejected')
                AND modified >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY modified DESC
            LIMIT 10
        """, as_dict=True)
        
        # Recent registrations
        recent_registrations = frappe.db.sql("""
            SELECT 
                name,
                vendor_name,
                ref_no,
                creation,
                registered_by
            FROM `tabVendor Onboarding`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY creation DESC
            LIMIT 10
        """, as_dict=True)
        
        return {
            "recent_approvals": recent_approvals,
            "recent_registrations": recent_registrations
        }
    except Exception as e:
        return {
            "recent_approvals": [],
            "recent_registrations": [],
            "error": str(e)
        }

# Bulk operations for tools
@frappe.whitelist()
def bulk_cleanup_stuck_documents():
    """Cleanup all stuck documents"""
    try:
        from vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding import cleanup_stuck_sap_status
        result = cleanup_stuck_sap_status()
        return {
            "status": "success",
            "message": "Bulk cleanup completed",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Bulk cleanup failed: {str(e)}"
        }

@frappe.whitelist()
def bulk_health_check():
    """Run health check on all recent documents"""
    try:
        from vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding import check_vendor_onboarding_health
        
        # Get recent documents
        recent_docs = frappe.db.sql("""
            SELECT name
            FROM `tabVendor Onboarding`
            WHERE modified >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY modified DESC
            LIMIT 50
        """, as_dict=True)
        
        health_results = []
        for doc in recent_docs:
            health_report = check_vendor_onboarding_health(doc.name)
            if health_report.get("overall_health") in ["warning", "critical", "error"]:
                health_results.append(health_report)
        
        return {
            "status": "success",
            "total_checked": len(recent_docs),
            "issues_found": len(health_results),
            "health_issues": health_results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Bulk health check failed: {str(e)}"
        }

@frappe.whitelist()
def run_comprehensive_test_suite():
    """Run comprehensive test suite"""
    try:
        from vms.vendor_onboarding.doctype.vendor_onboarding.vendor_onboarding import test_vendor_onboarding_fixes
        result = test_vendor_onboarding_fixes()
        return {
            "status": "success",
            "message": "Test suite completed",
            "results": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test suite failed: {str(e)}"
        }