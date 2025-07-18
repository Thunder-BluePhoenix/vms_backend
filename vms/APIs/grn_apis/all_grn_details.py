import frappe
from frappe import _
import json
from datetime import datetime, date


# @frappe.whitelist()
# def get_all_grn_details():
#     try:
#         print("Fetching all GRN records...")
#         grn_list = frappe.get_all(
#             "GRN",
#             fields="*",
#             filters={},
#         )
#         print(f"Fetched GRN records: {len(grn_list)}")

#         for grn in grn_list:
#             print(f"Fetching child items for GRN: {grn['name']}")
#             grn_items = frappe.get_all(
#                 "GRN Items",
#                 fields="*",
#                 filters={"parent": grn["name"]},
#             )
#             print(f"Fetched {len(grn_items)} items for GRN: {grn['name']}")
#             grn["grn_items"] = grn_items

#         if grn_items:
#                 po_number = grn_items[0].get("po_no")
#                 if po_number:
#                     print(f"Fetching Purchase Order details for PO No.: {po_number}")
#                     purchase_order = frappe.get_doc("Purchase Order", po_number)

#                     purchase_group = purchase_order.get("purchase_group")
#                     if purchase_group:
#                         print(f"Fetching Purchase Group details for: {purchase_group}")
#                         purchase_group_doc = frappe.get_doc("Purchase Group Master", purchase_group)

#                         team_value = purchase_group_doc.get("team")
#                         print(f"Team value fetched for Purchase Group {purchase_group}: {team_value}")

#                         grn["team"] = team_value

#         print("Completed fetching all GRN details.")
#         return grn_list

#     except Exception as e:
#         error_message = str(e)
#         print(f"Error occurred: {error_message}")
#         frappe.log_error(message=error_message, title="Error in fetching GRN details")
#         frappe.throw(_("An error occurred while fetching GRN details. Please check the logs for more details."))


# @frappe.whitelist()
# def get_all_grn_details():
#     try:
#         print("Fetching all GRN records...")
#         grn_list = frappe.get_all(
#             "GRN",
#             fields="*",
#             filters={},
#         )
#         print(f"Fetched GRN records: {len(grn_list)}")

#         for grn in grn_list:
#             print(f"\nProcessing GRN: {grn['name']}")

#             grn_items = frappe.get_all(
#                 "GRN Items",
#                 fields="*",
#                 filters={"parent": grn["name"]},
#             )

#             for item in grn_items:
#                 po_number = item.get("po_no")
#                 plant_code = item.get("plant")

#                 if not po_number or not plant_code:
#                     print(f"Missing PO or Plant Code in item {item.get('name')}, skipping team fetch.")
#                     item["team"] = None
#                     continue

#                 try:
#                     purchase_order = frappe.get_doc("Purchase Order", po_number)
#                     base_purchase_group = purchase_order.get("purchase_group")
#                 except frappe.DoesNotExistError:
#                     print(f"Purchase Order {po_number} not found.")
#                     item["team"] = None
#                     continue

#                 if not base_purchase_group:
#                     print(f"No purchase group in PO {po_number}")
#                     item["team"] = None
#                     continue

#                 try:
#                     plant_master = frappe.get_doc("Plant Master", plant_code)
#                     company_code = plant_master.get("company")
#                 except frappe.DoesNotExistError:
#                     print(f"Plant Master not found for Plant Code: {plant_code}")
#                     item["team"] = None
#                     continue

#                 if not company_code:
#                     print(f"No company code found for Plant {plant_code}")
#                     item["team"] = None
#                     continue

#                 full_purchase_group_id = f"{base_purchase_group}-{company_code}"
#                 print(f"Full Purchase Group ID: {full_purchase_group_id}")

#                 try:
#                     pg_doc = frappe.get_doc("Purchase Group Master", full_purchase_group_id)
#                     team = pg_doc.get("team")
#                     item["team"] = team
#                     print(f"Team for {full_purchase_group_id} is {team}")
#                 except frappe.DoesNotExistError:
#                     print(f"Purchase Group Master {full_purchase_group_id} not found.")
#                     item["team"] = None

#             grn["grn_items"] = grn_items  # update with enriched items

#         print("\nCompleted fetching all GRN details.")
#         return grn_list

#     except Exception as e:
#         error_message = str(e)
#         print(f"Error occurred: {error_message}")
#         frappe.log_error(message=error_message, title="Error in fetching GRN details")
#         frappe.throw(_("An error occurred while fetching GRN details. Please check the logs for more details."))

@frappe.whitelist()
def get_all_grn_details():
    try:
        print("Fetching all GRN records...")
        user = frappe.session.user
        team = frappe.db.get_value("Employee", {"user_id": user}, "team")
        grns = frappe.get_all("GRN", fields="*")
        print(f"📄 Total GRNs fetched: {len(grns)}")
        pg_team_map = {}
        if team:
            pg_list = frappe.get_all("Purchase Group Master", filters={"team": team}, fields=["purchase_group_code", "company"])
            pg_team_map = {(pg["purchase_group_code"], pg["company"]) for pg in pg_list}
            print(f"🔗 Purchase Group Mappings for team: {pg_team_map}")
        result = []
        for grn in grns:
            grn_items = frappe.get_all("GRN Items", fields="*", filters={"parent": grn["name"]})
            found_match = False

            for item in grn_items:
                po_no, plant = item.get("po_no"), item.get("plant")

                if not (po_no and plant):
                    continue

                company = frappe.db.get_value("Plant Master", plant, "company")
                pg_code = frappe.db.get_value("Purchase Order", po_no, "purchase_group")

                if (pg_code, company) in pg_team_map:
                    found_match = True
                    break

            if found_match or not team:
                grn["grn_items"] = grn_items
                result.append(grn)

        print(f"Returning {len(result)} GRNs after filtering.")
        return result

    except Exception as e:
        frappe.log_error(str(e), "Error in get_all_grn_details")
        frappe.throw(_("Something went wrong while fetching GRNs."))


@frappe.whitelist()
def get_grn_details_of_grn_number(grn_number=None):
    if not grn_number:
        frappe.throw("GRN Number is required")

    user = frappe.session.user
    user_team = frappe.db.get_value("Employee", {"user_id": user}, "team")

    if not user_team:
        frappe.throw("Your team is not mapped. Contact Admin.")

    grn_name = frappe.db.get_value("GRN", {"grn_no_t": grn_number})
    if not grn_name:
        frappe.throw("GRN not found.")

    try:
        grn_doc = frappe.get_doc("GRN", grn_name)
    except frappe.DoesNotExistError:
        frappe.throw("GRN document does not exist.")

    filtered_items = []

    grn_items = frappe.get_all("GRN Items", fields="*", filters={"parent": grn_name})
    if not grn_items:
        frappe.throw("No GRN Items found in this GRN.")

    for item in grn_items:
        po_no = item.get("po_no")
        plant = item.get("plant")

        if not po_no or not plant:
            continue

        purchase_group = frappe.db.get_value("Purchase Order", po_no, "purchase_group")
        company = frappe.db.get_value("Plant Master", plant, "company")

        if not purchase_group or not company:
            continue

        pg_master_name = f"{purchase_group}-{company}"
        pg_team = frappe.db.get_value("Purchase Group Master", pg_master_name, "team")

        if pg_team and pg_team == user_team:
            filtered_items.append(item)

    if not filtered_items:
        frappe.throw("You are not authorized to view any items in this GRN.")

    return {
        "grn_no": grn_doc.grn_no_t,
        "grn_date": grn_doc.grn_date,
        "grn_items": filtered_items
    }