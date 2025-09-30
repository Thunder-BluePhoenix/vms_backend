import json
import frappe
from frappe import _
from frappe.utils import nowdate
from vms.utils.custom_send_mail import custom_sendmail


#vms.APIs.requestor_master.create_requestor_master.create_requestor_master
@frappe.whitelist()
def create_requestor_master():
    try:
       
        if frappe.request.data:
            try:
                form_data = json.loads(frappe.request.data)
            except:
                form_data = frappe.form_dict.copy()
        else:
            form_data = frappe.form_dict.copy()

        requestor_data = form_data.get("requestor_data")
        material_request = form_data.get("material_request")
        send_email = form_data.get("send_email", True)

       
        if not requestor_data:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "requestor_data is required"}

      
        if isinstance(requestor_data, str):
            requestor_data = json.loads(requestor_data)
        
        if isinstance(material_request, str):
            material_request = json.loads(material_request)

      
        if not isinstance(requestor_data, dict):
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "requestor_data must be an object/dictionary"}

       
        if not requestor_data.get("requested_by"):
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "requested_by is required in requestor_data"}
        
       
        
        if not requestor_data.get("request_date"):
            requestor_data["request_date"] = nowdate()
        
        if not requestor_data.get("approval_status"):
            requestor_data["approval_status"] = "Pending by CP"

        
        requestor_doc = frappe.get_doc({
            "doctype": "Requestor Master",
            **requestor_data  
        })

        
        if material_request and isinstance(material_request, list):
            for item_data in material_request:
            
                if isinstance(item_data, dict):
                    requestor_doc.append("material_request", item_data)  

      
        requestor_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        if isinstance(send_email, str):
            send_email = send_email.lower() not in ['false', '0', 'no']
        
        if send_email:
            try:
                send_requestor_email(
                    requestor_name=requestor_doc.name,
                    action="created"
                )
            except Exception as email_error:
                frappe.log_error(
                    f"Email sending failed for {requestor_doc.name}: {str(email_error)}",
                    "Requestor Email Notification Error"
                )

        return {
            "message": "Success",
            "data": {
                "name": requestor_doc.name,
                "approval_status": requestor_doc.approval_status,
                "request_date": requestor_doc.request_date
            }
        }

    except json.JSONDecodeError as e:
        frappe.response.http_status_code = 400
        frappe.log_error(frappe.get_traceback(), "Requestor Master JSON Parse Error")
        return {"message": "Failed", "error": f"Invalid JSON format: {str(e)}"}

    except frappe.DuplicateEntryError:
        frappe.response.http_status_code = 409
        return {"message": "Failed", "error": "Duplicate entry"}
    
    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Requestor Master Creation Failed")
        return {"message": "Failed", "error": str(e)}


#vms.APIs.requestor_master.create_requestor_master.update_requestor_master
@frappe.whitelist()
def update_requestor_master():

    try:
    
        if frappe.request.data:
            try:
                form_data = json.loads(frappe.request.data)
            except:
                form_data = frappe.form_dict.copy()
        else:
            form_data = frappe.form_dict.copy()

        doc_name = form_data.get("name") or form_data.get("requestor_name")
        
        if not doc_name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Document name (name or requestor_name) is required"}

        try:
            requestor_doc = frappe.get_doc("Requestor Master", doc_name)
        except frappe.DoesNotExistError:
            frappe.response.http_status_code = 404
            return {"message": "Failed", "error": "Requestor Master not found"}

        requestor_data = form_data.get("requestor_data")
        material_request = form_data.get("material_request")
        send_email = form_data.get("send_email", True)

        if requestor_data:
           
            if isinstance(requestor_data, str):
                requestor_data = json.loads(requestor_data)
            
            if not isinstance(requestor_data, dict):
                frappe.response.http_status_code = 400
                return {"message": "Failed", "error": "requestor_data must be an object/dictionary"}
            
            for field, value in requestor_data.items():
                if hasattr(requestor_doc, field):
                    requestor_doc.set(field, value)

        requestor_doc.approval_status = "Pending by CP"

        if material_request:
          
            if isinstance(material_request, str):
                material_request = json.loads(material_request)

           
            if not isinstance(material_request, list):
                frappe.response.http_status_code = 400
                return {"message": "Failed", "error": "material_request must be a list/array"}

        
            requestor_doc.set("material_request", [])
            
            for item_data in material_request:
                if isinstance(item_data, dict):
                    requestor_doc.append("material_request", item_data)  # Direct append!

      
        requestor_doc.save(ignore_permissions=True)
        frappe.db.commit()

     
        if isinstance(send_email, str):
            send_email = send_email.lower() not in ['false', '0', 'no']
        
        if send_email:
            try:
                send_requestor_email(
                    requestor_name=requestor_doc.name,
                    action="updated"
                )
            except Exception as email_error:

                frappe.log_error(
                    f"Email sending failed for {requestor_doc.name}: {str(email_error)}",
                    "Requestor Email Notification Error"
                )

        return {
            "message": "Success",
            "data": {
                "name": requestor_doc.name,
                "approval_status": requestor_doc.approval_status,
                "request_date": requestor_doc.request_date
            }
        }

    except json.JSONDecodeError as e:
        frappe.response.http_status_code = 400
        frappe.log_error(frappe.get_traceback(), "Requestor Master JSON Parse Error")
        return {"message": "Failed", "error": f"Invalid JSON format: {str(e)}"}

    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Requestor Master Update Failed")
        return {"message": "Failed", "error": str(e)}


#vms.APIs.requestor_master.create_requestor_master.delete_requestor_master
@frappe.whitelist()
def delete_requestor_master():
    try:
       
        if frappe.request.data:
            try:
                form_data = json.loads(frappe.request.data)
            except:
                form_data = frappe.form_dict.copy()
        else:
            form_data = frappe.form_dict.copy()

       
        doc_name = form_data.get("name") or form_data.get("requestor_name")
        
        if not doc_name:
            frappe.response.http_status_code = 400
            return {"message": "Failed", "error": "Document name (name or requestor_name) is required"}

        if not frappe.db.exists("Requestor Master", doc_name):
            frappe.response.http_status_code = 404
            return {"message": "Failed", "error": "Requestor Master not found"}

        frappe.delete_doc("Requestor Master", doc_name, ignore_permissions=True)
        frappe.db.commit()

        return {
            "message": "Success",
            "data": {"name": doc_name, "deleted": True}
        }

    except frappe.PermissionError:
        frappe.response.http_status_code = 403
        return {"message": "Failed", "error": "Permission denied"}
    
    except Exception as e:
        frappe.response.http_status_code = 500
        frappe.log_error(frappe.get_traceback(), "Requestor Master Deletion Failed")
        return {"message": "Failed", "error": str(e)}


# ===== EMAIL NOTIFICATION HELPER =====

def send_requestor_email(requestor_name, action="created"):
    try:
        requestor_doc = frappe.get_doc("Requestor Master", requestor_name)
        
       
        requestor_person = requestor_doc.requested_by
        child_records = requestor_doc.get("material_request", [])

        

        # Get CP and Store employees
        requestor_emps_cp = frappe.get_all(
            "Employee",
            filters={"designation": "CP"},
            fields=["user_id", "full_name"]
        )
        requestor_emps_store = frappe.get_all(
            "Employee",
            filters={"designation": "Store"},
            fields=["user_id", "full_name"]
        )

        # Get unique emails for CC
        unique_emps = {}
        for emp in requestor_emps_cp + requestor_emps_store:
            if emp.get("user_id"):
                unique_emps[emp["user_id"]] = emp.get("full_name", "")

      
        table_rows = ""
        for row in child_records:
            table_rows += f"""
                <tr>
                    <td style="border: 1px solid #ccc; padding: 8px;">{row.company_name or ''}</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">{row.plant or ''}</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">{row.material_category or ''}</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">{row.material_type or ''}</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">{row.material_code_revised or ''}</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">{row.material_name_description or ''}</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">{row.unit_of_measure or ''}</td>
                    <td style="border: 1px solid #ccc; padding: 8px;">{row.comment_by_user or ''}</td>
                </tr>
            """

        table_html = f"""
            <table style="border-collapse: collapse; width: 100%; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ccc; padding: 8px;">Company Name</th>
                        <th style="border: 1px solid #ccc; padding: 8px;">Plant Name</th>
                        <th style="border: 1px solid #ccc; padding: 8px;">Material Category</th>
                        <th style="border: 1px solid #ccc; padding: 8px;">Material Type</th>
                        <th style="border: 1px solid #ccc; padding: 8px;">Material Code (Revised)</th>
                        <th style="border: 1px solid #ccc; padding: 8px;">Material Description</th>
                        <th style="border: 1px solid #ccc; padding: 8px;">Base UOM</th>
                        <th style="border: 1px solid #ccc; padding: 8px;">Comment</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows if table_rows else '<tr><td colspan="8" style="text-align:center; padding: 8px;">No material requests</td></tr>'}
                </tbody>
            </table>
        """

    
        requestor_head = frappe.get_value("Employee", requestor_person, "reports_to")
        requestor_head_email = frappe.get_value("Employee", requestor_head, "user_id") if requestor_head else None
        requestor_head_name = frappe.get_value("Employee", requestor_head, "full_name") if requestor_head else "Team"

    
        if action == "created":
            subject = "Request to Generate New Material Code Submitted"
            body = f"""
                <p>Dear {requestor_head_name},</p>
                <p>
                    A request to generate a new material code "<strong>{requestor_name}</strong>" has been successfully submitted by <strong>{requestor_person}</strong>.
                </p>
                <p>Preview the details:</p>
                {table_html}
                <p>Regards,<br>Meril VMS Team</p>
            """
        else:  # updated
            subject = "Requestor Master Updated"
            body = f"""
                <p>Dear {requestor_head_name},</p>
                <p>
                    The Requestor Master "<strong>{requestor_name}</strong>" has been <strong>updated</strong> by <strong>{requestor_person}</strong>.
                </p>
                <p>Here are the updated material request details:</p>
                {table_html}
                <p>Regards,<br>Meril VMS Team</p>
            """

        # Prepare recipients
        recipient_emails = list(unique_emps.keys())
        
        

        # Prepare recipients list
        recipients = []
        if requestor_head_email:
            recipients.append(requestor_head_email)
        
        # CC recipients
        cc_recipients = recipient_emails if recipient_emails else []

        try:
            frappe.custom_sendmail(
                recipients=recipients,
                cc=cc_recipients,
                subject=subject,
                message=body,
                now=True
            )
        except Exception as email_error:
            frappe.log_error(
                f"Email Send Error: {str(email_error)}\n{frappe.get_traceback()}",
                f"Email Send Error - {requestor_name}"
            )
            raise email_error

    except Exception as e:
        frappe.log_error(
            f"Email notification error: {str(e)}\n{frappe.get_traceback()}",
            f"Requestor Email Error - {requestor_name}"
        )
        raise


