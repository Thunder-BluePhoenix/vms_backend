# Copyright (c) 2025, Blue Phoenix and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cstr
from frappe.core.doctype.user.user import User
import re
from frappe.model.document import Document


class Employee(Document):
    
    def before_save(self):
        """
        Called before saving the Employee document
        Handles user creation for individual saves, bulk edits, and data imports
        """
        if self.create_user and self.company_email and self.first_name and self.designation:
            if not self.user_id:
               
                existing_user = frappe.db.exists("User", {"email": self.company_email})
                if existing_user:
                    self.user_id = existing_user
                    if not frappe.flags.in_import:
                        frappe.msgprint(f"Existing user linked to employee: {self.name}")
                else:
                   
                    try:
                        user_doc = self.create_user_during_save()
                        if user_doc:
                            self.user_id = user_doc.name
                            if not frappe.flags.in_import:
                                frappe.msgprint(f"New user created for employee: {self.name}")
                    except Exception as e:
                        frappe.log_error(f"Error creating user during save for {self.name}: {str(e)}")
                        if not frappe.flags.in_import:
                            frappe.msgprint(f"Error creating user for {self.name}: {str(e)}")

    def after_insert(self):
        """
        Called after inserting the Employee document
        """
        try:
          
            if frappe.flags.in_import and self.create_user and self.user_id:
                frappe.log_error(f"User successfully created/linked for employee {self.name} during import", "User Creation Success")
        except Exception as e:
            frappe.log_error(f"Error in after_insert for employee {self.name}: {str(e)}")

    def validate(self):
        """
        Called during validation of the Employee document
        """
        if self.create_user:
           
            if not self.company_email:
                frappe.throw("Company email is required when 'Create User' is checked")
            
            if not self.first_name:
                frappe.throw("First name is required when 'Create User' is checked")
            
            if not self.designation:
                frappe.throw("Designation is required when 'Create User' is checked")
            
           
            if not self.validate_email_format(self.company_email):
                frappe.throw(f"Invalid email format: {self.company_email}")
            
            
            existing_employee = frappe.db.exists("Employee", {
                "company_email": self.company_email,
                "name": ["!=", self.name]
            })
            if existing_employee:
                frappe.throw(f"Another employee already has this email: {self.company_email}")

    def create_user_during_save(self):
        """
        Create user during employee save - works for all scenarios
        """
        try:
            
            if not self.company_email or not self.first_name or not self.designation:
                return None
            
            
            roles = self.get_roles_from_designation(self.designation)
            if not roles:
                if not frappe.flags.in_import:
                    frappe.msgprint(f"No roles found for designation: {self.designation}")
                frappe.log_error(f"No roles found for designation: {self.designation}")
                return None
            
           
            password = self.generate_password(self.first_name)
            
            
            user_doc = frappe.new_doc("User")
            user_doc.email = self.company_email
            user_doc.first_name = self.first_name
            user_doc.last_name = self.last_name or ""
            user_doc.new_password = password
            user_doc.send_welcome_email = 0  
            user_doc.enabled = 1
            
            
            for role in roles:
                user_doc.append("roles", {
                    "role": role
                })
            
           
            user_doc.insert(ignore_permissions=True)
            
          
            frappe.log_error(f"User created: {self.company_email} with password: {password}", "User Creation Log")
            
            if not frappe.flags.in_import:
                frappe.msgprint(f"User created: {self.company_email} with password: {password}")
            
            return user_doc
            
        except Exception as e:
            frappe.log_error(f"Error creating user during save: {str(e)}")
            return None

    def get_roles_from_designation(self, designation):
        """
        Get roles from the role profile linked to designation
        """
        try:
            if not designation:
                return []
            
            
            if not frappe.db.exists("Role Profile", designation):
                frappe.log_error(f"Role Profile not found: {designation}")
                return []
            
           
            role_profile = frappe.get_doc("Role Profile", designation)
            
            roles = []
            for role_row in role_profile.roles:
                roles.append(role_row.role)
            
            return roles
        
        except Exception as e:
            frappe.log_error(f"Error getting roles from designation {designation}: {str(e)}")
            return []

    def generate_password(self, first_name):
        """
        Generate password using first name + @123
        """
        if not first_name:
            return "default@123"
        
        
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', first_name)
        return f"{clean_name}@123"

    def validate_email_format(self, email):
        """
        Validate email format
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def on_update(self):
        """
        Called after the document is saved/updated
        Handles bulk edit scenarios where create_user is checked later
        """
        
        if self.create_user and self.company_email and self.first_name and self.designation and not self.user_id:
           
            existing_user = frappe.db.exists("User", {"email": self.company_email})
            if existing_user:
                frappe.db.set_value("Employee", self.name, "user_id", existing_user)
                frappe.msgprint(f"Existing user linked to employee: {self.name}")
            else:
               
                try:
                    user_doc = self.create_user_during_save()
                    if user_doc:
                        frappe.db.set_value("Employee", self.name, "user_id", user_doc.name)
                        frappe.msgprint(f"User created for employee: {self.name}")
                except Exception as e:
                    frappe.log_error(f"Error in on_update user creation for {self.name}: {str(e)}")

   
    
    @staticmethod
    @frappe.whitelist()
    def create_users_for_employees():
        """
        Utility method to create users for all employees with create_user checked
        Can be called manually if needed
        """
        try:
            employees = frappe.get_all("Employee", 
                filters={
                    "create_user": 1,
                    "user_id": ["in", ["", None]]
                },
                fields=["name"]
            )
            
            if not employees:
                frappe.msgprint("No employees found with 'Create User' checked and no existing user.")
                return {"status": "No employees found"}
                
            success_count = 0
            error_count = 0
            
            for employee_data in employees:
                try:
                   
                    employee_doc = frappe.get_doc("Employee", employee_data.name)
                    if employee_doc.create_user and not employee_doc.user_id:
                        employee_doc.save()
                        if employee_doc.user_id:
                            success_count += 1
                        else:
                            error_count += 1
                            
                except Exception as e:
                    error_count += 1
                    frappe.log_error(f"Error processing employee {employee_data.name}: {str(e)}")
            
            message = f"Process completed. Success: {success_count}, Errors: {error_count}"
            frappe.msgprint(message)
            return {"status": "completed", "success": success_count, "errors": error_count}
            
        except Exception as e:
            frappe.log_error(f"Error in bulk user creation: {str(e)}")
            frappe.throw(f"Error in bulk user creation: {str(e)}")

    @staticmethod
    @frappe.whitelist()
    def link_existing_users():
        """
        Link existing users to employees based on email
        """
        try:
            employees = frappe.get_all("Employee", 
                filters={
                    "company_email": ["!=", ""],
                    "user_id": ["in", ["", None]]
                },
                fields=["name", "company_email"]
            )
            
            updated_count = 0
            
            for employee_data in employees:
                existing_user = frappe.db.exists("User", {"email": employee_data.company_email})
                if existing_user:
                    frappe.db.set_value("Employee", employee_data.name, "user_id", existing_user)
                    updated_count += 1
            
            frappe.db.commit()
            message = f"Linked {updated_count} employees with existing users"
            frappe.msgprint(message)
            return {"status": "completed", "linked": updated_count}
            
        except Exception as e:
            frappe.log_error(f"Error linking existing users: {str(e)}")
            frappe.throw(f"Error linking existing users: {str(e)}")