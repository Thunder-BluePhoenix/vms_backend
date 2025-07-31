

import frappe
import pandas as pd
import os
import json
from frappe.utils import get_files_path, get_site_path, now
from frappe import _

def create_field_mapping():
    
    
    field_mapping = {
        # Common fields across all booking types
        'TYPE': 'type',
        'BOOKING DATE': 'booking_date',
        'EMPLOYEE CODE': 'employee_code', 
        'BILLING COMPANY': 'billing_company',
        'DOC NO/ REQ BY': 'doc_no_req_by',
        'BASIC AMOUNT': 'basic_amount',
        'GST AMOUNT': 'gst_amount',
        'NET AMOUNT': 'net_amount',
        'SERVICE CHARGES': 'service_charges',
        'CGST AMOUNT': 'cgst_amount',
        'SGST AMOUNT': 'sgst_amount',
        'IGST AMOUNT': 'igst_amount',
        'GRAND TOTAL': 'grand_total',
        'REMARKS': 'remarks',
        'INV NO': 'inv_no',
        'DN NO': 'dn_no',
        'INV DATE': 'inv_date',
        
        # Bus Booking specific
        'NO. OF PASSENGERS': 'no_of_passengers',
        'NAME OF PASSENGERS': 'name_of_passengers',
        'FROM ORIGIN': 'from_origin',
        'TO DESTINATION': 'to_destination',
        'TRAVEL DATE ONWARD': 'travel_date_onward',
        'PNR/TICKET NUMBER': 'pnrticket_number',
        'BUS OPERATOR NAME': 'bus_operator_name',
        
        # Air Booking specific (Domestic & International)
        'TRAVEL TYPE': 'travel_type',
        'TRAVEL DATE RETURN': 'travel_date_return',
        'TICKET NUMBER': 'ticket_number',
        'FLIGHT NO. ONWARD': 'flight_no_onward',
        'FLIGHT NO. RETURN': 'flight_no_return',
        'CLASS OF BOOKING': 'class_of_booking',
        'AIRLINE NAME': 'airline_name',
        
        # International Air specific
        'RETURN FROM ORIGIN': 'return_from_origin',
        'RETURN TO DESTINATION': 'return_to_destination',
        
        # Hotel Booking specific
        'NO. OF GUEST': 'no_of_guest',
        'NAME OF GUEST': 'name_of_guest',
        'CITY NAME': 'city_name',
        'LOCATION TYPE': 'location_type',
        'CHECK IN DATE': 'check_in_date',
        'CHECK OUT DATE': 'check_out_date',
        'NO. OF NIGHTS': 'no_of_nights',
        'BOOKING REFERENCE NO.': 'booking_reference_no',
        'HOTEL NAME': 'hotel_name',
        
        # Railway Booking specific
        'TRAIN No.': 'train_no',
        'CLASS': 'class',
        'QUOTA': 'quota'
    }
    
    return field_mapping

def clean_excel_columns(df):
   
    
    cleaned_columns = []
    for col in df.columns:
        if isinstance(col, str):
            
            cleaned_col = col.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
            
            cleaned_col = ' '.join(cleaned_col.split())
            cleaned_columns.append(cleaned_col)
        else:
            cleaned_columns.append(str(col))
    
    df.columns = cleaned_columns
    return df

def validate_record_data(row, row_index, sheet_name):
    
    
    errors = []
    
    
    booking_type = row.get('TYPE')
    if pd.isna(booking_type) or str(booking_type).strip() == "":
        errors.append("TYPE field is mandatory and cannot be empty")
    else:
       
        valid_types = ['Bus Booking', 'Hotel Booking', 'Domestic Air Booking', 'International Air Booking', 'Railway Booking']
        if str(booking_type).strip() not in valid_types:
            errors.append(f"Invalid TYPE value: '{booking_type}'. Must be one of: {', '.join(valid_types)}")
    
    
    mandatory_fields = {
        'EMPLOYEE CODE': 'Employee Code is required',
        'BILLING COMPANY': 'Billing Company is required',
        'BOOKING DATE': 'Booking Date is required'
    }
    
    for field, error_msg in mandatory_fields.items():
        value = row.get(field)
        if pd.isna(value) or str(value).strip() == "":
            errors.append(error_msg)
    
   
    booking_type_str = str(booking_type).strip() if not pd.isna(booking_type) else ""
    
    if booking_type_str == 'Bus Booking':
        if pd.isna(row.get('NO. OF PASSENGERS')) or str(row.get('NO. OF PASSENGERS')).strip() == "":
            errors.append("Number of Passengers is required for Bus Booking")
        if pd.isna(row.get('FROM ORIGIN')) or str(row.get('FROM ORIGIN')).strip() == "":
            errors.append("From Origin is required for Bus Booking")
        if pd.isna(row.get('TO DESTINATION')) or str(row.get('TO DESTINATION')).strip() == "":
            errors.append("To Destination is required for Bus Booking")
    
    elif booking_type_str in ['Domestic Air Booking', 'International Air Booking']:
        if pd.isna(row.get('NO. OF PASSENGERS')) or str(row.get('NO. OF PASSENGERS')).strip() == "":
            errors.append("Number of Passengers is required for Air Booking")
        if pd.isna(row.get('FROM ORIGIN')) or str(row.get('FROM ORIGIN')).strip() == "":
            errors.append("From Origin is required for Air Booking")
        if pd.isna(row.get('TO DESTINATION')) or str(row.get('TO DESTINATION')).strip() == "":
            errors.append("To Destination is required for Air Booking")
        if pd.isna(row.get('AIRLINE NAME')) or str(row.get('AIRLINE NAME')).strip() == "":
            errors.append("Airline Name is required for Air Booking")
    
    elif booking_type_str == 'Hotel Booking':
        if pd.isna(row.get('NO. OF GUEST')) or str(row.get('NO. OF GUEST')).strip() == "":
            errors.append("Number of Guests is required for Hotel Booking")
        if pd.isna(row.get('CITY NAME')) or str(row.get('CITY NAME')).strip() == "":
            errors.append("City Name is required for Hotel Booking")
        if pd.isna(row.get('HOTEL NAME')) or str(row.get('HOTEL NAME')).strip() == "":
            errors.append("Hotel Name is required for Hotel Booking")
    
    elif booking_type_str == 'Railway Booking':
        if pd.isna(row.get('NO. OF PASSENGERS')) or str(row.get('NO. OF PASSENGERS')).strip() == "":
            errors.append("Number of Passengers is required for Railway Booking")
        if pd.isna(row.get('FROM ORIGIN')) or str(row.get('FROM ORIGIN')).strip() == "":
            errors.append("From Origin is required for Railway Booking")
        if pd.isna(row.get('TO DESTINATION')) or str(row.get('TO DESTINATION')).strip() == "":
            errors.append("To Destination is required for Railway Booking")
        if pd.isna(row.get('TRAIN No.')) or str(row.get('TRAIN No.')).strip() == "":
            errors.append("Train Number is required for Railway Booking")
    
  
    numeric_fields = ['BASIC AMOUNT', 'GST AMOUNT', 'NET AMOUNT', 'SERVICE CHARGES', 'CGST AMOUNT', 
                     'SGST AMOUNT', 'IGST AMOUNT', 'GRAND TOTAL']
    
    for field in numeric_fields:
        value = row.get(field)
        if not pd.isna(value) and str(value).strip() != "":
            try:
                float(str(value))
            except (ValueError, TypeError):
                errors.append(f"Invalid numeric value in {field}: '{value}'")
    
    return errors

def get_record_preview(row, field_mapping):
  
    
    preview = {}
    key_fields = ['TYPE', 'EMPLOYEE CODE', 'BILLING COMPANY', 'BOOKING DATE', 'NO. OF PASSENGERS', 
                  'NO. OF GUEST', 'NAME OF PASSENGERS', 'NAME OF GUEST']
    
    for field in key_fields:
        if field in row.index:
            value = row.get(field)
            if not pd.isna(value) and str(value).strip() != "":
                preview[field] = str(value).strip()
    
    return preview

def get_file_path_from_url(file_url):
  
    
    try:
       
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        
        
        if file_doc.is_private:
            
            file_path = frappe.get_site_path("private", "files", file_doc.file_name)
        else:
           
            possible_paths = [
                frappe.get_site_path("public", "files", file_doc.file_name),
                get_files_path(file_doc.file_name),
                os.path.join(frappe.get_site_path(), "public", "files", file_doc.file_name),
                os.path.join(".", frappe.local.site, "public", "files", file_doc.file_name)
            ]
            
            
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    break
            else:
                
                file_path = possible_paths[0]
        
        frappe.logger().info(f"File path resolved: {file_path}")
        return file_path
        
    except Exception as e:
        frappe.logger().error(f"Error resolving file path for {file_url}: {str(e)}")
      
        if "/files/" in file_url:
            filename = file_url.split("/files/")[-1]
            return frappe.get_site_path("public", "files", filename)
        else:
            raise e

@frappe.whitelist()
def import_earth_invoice_data(file_url):
    
    
    if not frappe.has_permission("Earth Invoice", "create"):
        frappe.throw(_("You don't have permission to import Earth Invoice data"))
    
   
    results = {
        "total_records": 0,
        "imported_count": 0,
        "failed_count": 0,
        "errors": [],
        "failed_records": [], 
        "import_summary": {}   
    }
    
    try:
       
        file_path = get_file_path_from_url(file_url)
        
        
        if not os.path.exists(file_path):
            frappe.throw(_("File not found at path: {0}").format(file_path))
        
        frappe.logger().info(f"Starting import from file: {file_path}")
        
        
        field_mapping = create_field_mapping()
        
        
        try:
            excel_file = pd.ExcelFile(file_path)
        except Exception as e:
            frappe.throw(_("Error reading Excel file: {0}. Please ensure it's a valid Excel file.").format(str(e)))
        
        
        for sheet_name in excel_file.sheet_names:
            frappe.logger().info(f"Processing sheet: {sheet_name}")
            
            sheet_results = {
                "total_records": 0,
                "imported_count": 0,
                "failed_count": 0,
                "errors": []
            }
            
            try:
                
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                
                if df.empty:
                    frappe.logger().info(f"Skipping empty sheet: {sheet_name}")
                    continue
                
            
                df = clean_excel_columns(df)
                frappe.logger().info(f"Cleaned columns for {sheet_name}: {list(df.columns)}")
                
              
                for index, row in df.iterrows():
                    try:
                        
                        if row.isna().all():
                            continue
                        
                        
                        if pd.isna(row.get('BOOKING DATE')) and pd.isna(row.get('EMPLOYEE CODE')) and pd.isna(row.get('TYPE')):
                            continue
                        
                      
                        validation_errors = validate_record_data(row, index, sheet_name)
                        
                        if validation_errors:
                           
                            sheet_results["failed_count"] += 1
                            
                            failed_record = {
                                "sheet": sheet_name,
                                "row": index + 2, 
                                "errors": validation_errors,
                                "record_preview": get_record_preview(row, field_mapping),
                                "all_data": {k: str(v) if not pd.isna(v) else "" for k, v in row.items()}
                            }
                            
                            results["failed_records"].append(failed_record)
                            
                           
                            for error in validation_errors:
                                results["errors"].append({
                                    "sheet": sheet_name,
                                    "row": index + 2,
                                    "error": error
                                })
                            
                            continue
                        
                    
                        invoice_doc = frappe.new_doc("Earth Invoice")
                        
                      
                        mapped_fields = 0
                        for excel_col, frappe_field in field_mapping.items():
                            if excel_col in df.columns and hasattr(invoice_doc, frappe_field):
                                value = row.get(excel_col)
                                if pd.notna(value) and str(value).strip() != "":
                                    setattr(invoice_doc, frappe_field, str(value).strip())
                                    mapped_fields += 1
                        
                     
                        if mapped_fields > 0:
                            try:
                                invoice_doc.insert(ignore_permissions=True)
                                sheet_results["imported_count"] += 1
                                frappe.logger().info(f"Inserted record {index + 1} from {sheet_name}")
                            except Exception as insert_error:
                               
                                sheet_results["failed_count"] += 1
                                
                                failed_record = {
                                    "sheet": sheet_name,
                                    "row": index + 2,
                                    "errors": [f"Database insertion failed: {str(insert_error)}"],
                                    "record_preview": get_record_preview(row, field_mapping),
                                    "all_data": {k: str(v) if not pd.isna(v) else "" for k, v in row.items()}
                                }
                                
                                results["failed_records"].append(failed_record)
                                results["errors"].append({
                                    "sheet": sheet_name,
                                    "row": index + 2,
                                    "error": f"Database insertion failed: {str(insert_error)}"
                                })
                        else:
                            sheet_results["failed_count"] += 1
                            
                            failed_record = {
                                "sheet": sheet_name,
                                "row": index + 2,
                                "errors": ["No valid data found in row"],
                                "record_preview": get_record_preview(row, field_mapping),
                                "all_data": {k: str(v) if not pd.isna(v) else "" for k, v in row.items()}
                            }
                            
                            results["failed_records"].append(failed_record)
                            results["errors"].append({
                                "sheet": sheet_name,
                                "row": index + 2,
                                "error": "No valid data found in row"
                            })
                        
                    except Exception as row_error:
                        sheet_results["failed_count"] += 1
                        error_msg = str(row_error)
                        frappe.logger().error(f"Error processing row {index + 1} in {sheet_name}: {error_msg}")
                        
                        failed_record = {
                            "sheet": sheet_name,
                            "row": index + 2,
                            "errors": [f"Unexpected error: {error_msg}"],
                            "record_preview": get_record_preview(row, field_mapping),
                            "all_data": {k: str(v) if not pd.isna(v) else "" for k, v in row.items()}
                        }
                        
                        results["failed_records"].append(failed_record)
                        results["errors"].append({
                            "sheet": sheet_name,
                            "row": index + 2,
                            "error": error_msg
                        })
                        continue
                
                
                sheet_results["total_records"] = len(df)
                results["import_summary"][sheet_name] = sheet_results
               
                results["imported_count"] += sheet_results["imported_count"]
                results["failed_count"] += sheet_results["failed_count"]
                results["total_records"] += sheet_results["total_records"]
                
                frappe.logger().info(f"Sheet {sheet_name} completed: {sheet_results['imported_count']} imported, {sheet_results['failed_count']} failed")
                
            except Exception as sheet_error:
                error_msg = f"Sheet processing failed: {str(sheet_error)}"
                frappe.logger().error(f"Error processing sheet {sheet_name}: {error_msg}")
                results["errors"].append({
                    "sheet": sheet_name,
                    "error": error_msg
                })
                continue
        
      
        frappe.db.commit()
        frappe.logger().info(f"Import completed successfully: {results}")
        
        return results
        
    except Exception as e:
        frappe.db.rollback()
        error_msg = str(e)
        frappe.logger().error(f"Import failed with error: {error_msg}")
        frappe.throw(_("Import failed: {0}").format(error_msg))

@frappe.whitelist()
def test_file_access(file_url):
    """Test function to debug file path issues"""
    
    try:
        file_path = get_file_path_from_url(file_url)
        
        return {
            "file_url": file_url,
            "resolved_path": file_path,
            "file_exists": os.path.exists(file_path),
            "site_path": frappe.get_site_path(),
            "current_directory": os.getcwd()
        }
    except Exception as e:
        return {
            "error": str(e),
            "file_url": file_url
        }