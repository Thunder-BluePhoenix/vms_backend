import frappe
from frappe import _

# =============================================================================
# APIs to fetch master records for QMS multiselect fields
# =============================================================================

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_quality_control_systems():
    """
    Get all QMS Quality Control System records
    
    Returns:
        List of quality control systems with their details
    """
    try:
        records = frappe.get_all(
            "QMS Quality Control System",
            fields=["name", "quality_control_system", "creation", "modified"],
            order_by="quality_control_system asc"
        )
        
        return {
            "status": "success",
            "data": records,
            "count": len(records),
            "message": f"Found {len(records)} quality control systems"
        }
    except Exception as e:
        frappe.log_error(f"Error fetching quality control systems: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_procedure_documents():
    """
    Get all QMS Procedure Doc Name records
    
    Returns:
        List of procedure documents with their details
    """
    try:
        records = frappe.get_all(
            "QMS Procedure Doc Name",
            fields=["name", "procedure_doc_name", "creation", "modified"],
            order_by="procedure_doc_name asc"
        )
        
        return {
            "status": "success",
            "data": records,
            "count": len(records),
            "message": f"Found {len(records)} procedure documents"
        }
    except Exception as e:
        frappe.log_error(f"Error fetching procedure documents: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_prior_notifications():
    """
    Get all QMS Prior Notification records
    
    Returns:
        List of prior notifications with their details
    """
    try:
        records = frappe.get_all(
            "QMS Prior Notification",
            fields=["name", "prior_notification", "creation", "modified"],
            order_by="prior_notification asc"
        )
        
        return {
            "status": "success",
            "data": records,
            "count": len(records),
            "message": f"Found {len(records)} prior notifications"
        }
    except Exception as e:
        frappe.log_error(f"Error fetching prior notifications: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_inspection_reports():
    """
    Get all QMS Inspection Reports records
    
    Returns:
        List of inspection reports with their details
    """
    try:
        records = frappe.get_all(
            "QMS Inspection Reports",
            fields=["name", "inspection_report", "creation", "modified"],
            order_by="inspection_report asc"
        )
        
        return {
            "status": "success",
            "data": records,
            "count": len(records),
            "message": f"Found {len(records)} inspection reports"
        }
    except Exception as e:
        frappe.log_error(f"Error fetching inspection reports: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_batch_record_details():
    """
    Get all QMS Batch Record Details records
    
    Returns:
        List of batch record details with their details
    """
    try:
        records = frappe.get_all(
            "QMS Batch Record Details",
            fields=["name", "details_of_batch_record", "creation", "modified"],
            order_by="details_of_batch_record asc"
        )
        
        return {
            "status": "success",
            "data": records,
            "count": len(records),
            "message": f"Found {len(records)} batch record details"
        }
    except Exception as e:
        frappe.log_error(f"Error fetching batch record details: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_all_multiselect_masters():
    """
    Get all multiselect master records in a single API call
    
    Returns:
        Dictionary containing all master records categorized by type
    """
    try:
        result = {
            "status": "success",
            "data": {
                "quality_control_systems": [],
                "procedure_documents": [],
                "prior_notifications": [],
                "inspection_reports": [],
                "batch_record_details": []
            },
            "message": "All multiselect masters fetched successfully"
        }
        
        # Fetch Quality Control Systems
        qcs = frappe.get_all(
            "QMS Quality Control System",
            fields=["name", "quality_control_system"],
            order_by="quality_control_system asc"
        )
        result["data"]["quality_control_systems"] = qcs
        
        # Fetch Procedure Documents
        procedures = frappe.get_all(
            "QMS Procedure Doc Name",
            fields=["name", "procedure_doc_name"],
            order_by="procedure_doc_name asc"
        )
        result["data"]["procedure_documents"] = procedures
        
        # Fetch Prior Notifications
        notifications = frappe.get_all(
            "QMS Prior Notification",
            fields=["name", "prior_notification"],
            order_by="prior_notification asc"
        )
        result["data"]["prior_notifications"] = notifications
        
        # Fetch Inspection Reports
        reports = frappe.get_all(
            "QMS Inspection Reports",
            fields=["name", "inspection_report"],
            order_by="inspection_report asc"
        )
        result["data"]["inspection_reports"] = reports
        
        # Fetch Batch Record Details
        batch_records = frappe.get_all(
            "QMS Batch Record Details",
            fields=["name", "details_of_batch_record"],
            order_by="details_of_batch_record asc"
        )
        result["data"]["batch_record_details"] = batch_records
        
        # Add counts
        result["counts"] = {
            "quality_control_systems": len(qcs),
            "procedure_documents": len(procedures),
            "prior_notifications": len(notifications),
            "inspection_reports": len(reports),
            "batch_record_details": len(batch_records)
        }
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error fetching all multiselect masters: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": {}
        }

# =============================================================================
# APIs with search functionality
# =============================================================================

@frappe.whitelist(allow_guest=True, methods=["GET"])
def search_quality_control_systems(search_term="", limit=20):
    """
    Search QMS Quality Control System records
    
    Args:
        search_term (str): Search term for filtering
        limit (int): Maximum number of records to return
    
    Returns:
        Filtered list of quality control systems
    """
    try:
        filters = {}
        if search_term:
            filters = [
                ["quality_control_system", "like", f"%{search_term}%"]
            ]
        
        records = frappe.get_all(
            "QMS Quality Control System",
            fields=["name", "quality_control_system"],
            filters=filters,
            order_by="quality_control_system asc",
            limit=int(limit)
        )
        
        return {
            "status": "success",
            "data": records,
            "count": len(records),
            "search_term": search_term,
            "message": f"Found {len(records)} matching quality control systems"
        }
    except Exception as e:
        frappe.log_error(f"Error searching quality control systems: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=True, methods=["GET"])
def search_procedure_documents(search_term="", limit=20):
    """
    Search QMS Procedure Doc Name records
    
    Args:
        search_term (str): Search term for filtering
        limit (int): Maximum number of records to return
    """
    try:
        filters = {}
        if search_term:
            filters = [
                ["procedure_doc_name", "like", f"%{search_term}%"]
            ]
        
        records = frappe.get_all(
            "QMS Procedure Doc Name",
            fields=["name", "procedure_doc_name"],
            filters=filters,
            order_by="procedure_doc_name asc",
            limit=int(limit)
        )
        
        return {
            "status": "success",
            "data": records,
            "count": len(records),
            "search_term": search_term,
            "message": f"Found {len(records)} matching procedure documents"
        }
    except Exception as e:
        frappe.log_error(f"Error searching procedure documents: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@frappe.whitelist(allow_guest=True, methods=["GET"])
def search_batch_record_details(search_term="", limit=20):
    """
    Search QMS Batch Record Details records
    
    Args:
        search_term (str): Search term for filtering
        limit (int): Maximum number of records to return
    """
    try:
        filters = {}
        if search_term:
            filters = [
                ["details_of_batch_record", "like", f"%{search_term}%"]
            ]
        
        records = frappe.get_all(
            "QMS Batch Record Details",
            fields=["name", "details_of_batch_record"],
            filters=filters,
            order_by="details_of_batch_record asc",
            limit=int(limit)
        )
        
        return {
            "status": "success",
            "data": records,
            "count": len(records),
            "search_term": search_term,
            "message": f"Found {len(records)} matching batch record details"
        }
    except Exception as e:
        frappe.log_error(f"Error searching batch record details: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

# =============================================================================
# APIs to create new master records
# =============================================================================

@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_quality_control_system(quality_control_system):
    """
    Create a new QMS Quality Control System record
    
    Args:
        quality_control_system (str): Name of the quality control system
    """
    try:
        if not quality_control_system:
            return {
                "status": "error",
                "message": "quality_control_system is required"
            }
        
        # Check if already exists
        if frappe.db.exists("QMS Quality Control System", quality_control_system):
            return {
                "status": "exists",
                "message": "Quality control system already exists",
                "data": {"name": quality_control_system}
            }
        
        # Create new record
        doc = frappe.get_doc({
            "doctype": "QMS Quality Control System",
            "quality_control_system": quality_control_system
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Quality control system created successfully",
            "data": {
                "name": doc.name,
                "quality_control_system": doc.quality_control_system
            }
        }
    except Exception as e:
        frappe.log_error(f"Error creating quality control system: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_procedure_document(procedure_doc_name):
    """
    Create a new QMS Procedure Doc Name record
    
    Args:
        procedure_doc_name (str): Name of the procedure document
    """
    try:
        if not procedure_doc_name:
            return {
                "status": "error",
                "message": "procedure_doc_name is required"
            }
        
        # Check if already exists
        if frappe.db.exists("QMS Procedure Doc Name", procedure_doc_name):
            return {
                "status": "exists",
                "message": "Procedure document already exists",
                "data": {"name": procedure_doc_name}
            }
        
        # Create new record
        doc = frappe.get_doc({
            "doctype": "QMS Procedure Doc Name",
            "procedure_doc_name": procedure_doc_name
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Procedure document created successfully",
            "data": {
                "name": doc.name,
                "procedure_doc_name": doc.procedure_doc_name
            }
        }
    except Exception as e:
        frappe.log_error(f"Error creating procedure document: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_batch_record_detail(details_of_batch_record):
    """
    Create a new QMS Batch Record Details record
    
    Args:
        details_of_batch_record (str): Details of the batch record
    """
    try:
        if not details_of_batch_record:
            return {
                "status": "error",
                "message": "details_of_batch_record is required"
            }
        
        # Check if already exists
        if frappe.db.exists("QMS Batch Record Details", details_of_batch_record):
            return {
                "status": "exists",
                "message": "Batch record detail already exists",
                "data": {"name": details_of_batch_record}
            }
        
        # Create new record
        doc = frappe.get_doc({
            "doctype": "QMS Batch Record Details",
            "details_of_batch_record": details_of_batch_record
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Batch record detail created successfully",
            "data": {
                "name": doc.name,
                "details_of_batch_record": doc.details_of_batch_record
            }
        }
    except Exception as e:
        frappe.log_error(f"Error creating batch record detail: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }




@frappe.whitelist(allow_guest=True)
def get_quality_agreement_list():
    try:
        # Get all Quality Agreement Type records with required fields
        all_templates = frappe.get_all("Quality Agreement Type", fields=["name", "sample_document"])
        
        if not all_templates:
            return {
                "status": "success",
                "message": "No template records found.",
                "data": []
            }

        # Process each template to include attachment details
        processed_templates = []
        
        for template in all_templates:
            template_data = {
                "name": template.name
            }
            
            # Handle sample_document attachment
            if template.sample_document:
                try:
                    file_doc = frappe.get_doc("File", {"file_url": template.sample_document})
                    template_data["sample_document"] = {
                        "url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
                        "name": file_doc.name,
                        "file_name": file_doc.file_name
                    }
                except frappe.DoesNotExistError:
                    # Handle case where file document doesn't exist
                    template_data["sample_document"] = {
                        "url": "",
                        "name": "",
                        "file_name": ""
                    }
            else:
                template_data["sample_document"] = {
                    "url": "",
                    "name": "",
                    "file_name": ""
                }
            
            processed_templates.append(template_data)

        return {
            "status": "success",
            "message": f"{len(processed_templates)} template(s) found.",
            "data": processed_templates
        }

    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "Quality Agreement Type Doctype Not Found")
        return {
            "status": "error",
            "message": "Quality Agreement Type doctype does not exist."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_quality_agreement_list")
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }