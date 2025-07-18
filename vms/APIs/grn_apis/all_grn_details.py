import frappe
from frappe import _

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
        print(f"Current user: {user}")
        team = frappe.db.get_value("Employee", {"user_id": user}, "team")
        print(f"Team filter applied: {team}")
        
        grn_list = frappe.get_all("GRN", fields="*")
        print(f"Fetched GRN records: {len(grn_list)}")

        team_pg_codes = []
        if team:
            print(f"Filtering Purchase Group Master with team: {team}")
            pg_list = frappe.get_all(
                "Purchase Group Master",
                filters={"team": team},
                fields=["name", "purchase_group_code", "company"]
            )
            team_pg_codes = pg_list

        filtered_grns = []

        for grn in grn_list:
            print(f"\nProcessing GRN: {grn['name']}")
            
            grn_items = frappe.get_all(
                "GRN Items",
                fields="*",
                filters={"parent": grn["name"]}
            )

            found_team_match = False

            for item in grn_items:
                po_number = item.get("po_no")
                plant_code = item.get("plant")

                if not po_number or not plant_code:
                    item["team"] = None
                    continue

                try:
                    plant_master = frappe.get_doc("Plant Master", plant_code)
                    company_code = plant_master.get("company")
                except frappe.DoesNotExistError:
                    item["team"] = None
                    continue

                if not company_code:
                    item["team"] = None
                    continue

                try:
                    purchase_order = frappe.get_doc("Purchase Order", po_number)
                    po_pg_code = purchase_order.get("purchase_group")
                except frappe.DoesNotExistError:
                    item["team"] = None
                    continue

                if not po_pg_code:
                    item["team"] = None
                    continue

                matched_team = None
                for pg in team_pg_codes:
                    if pg["company"] == company_code and pg["purchase_group_code"] == po_pg_code:
                        matched_team = team
                        break

                item["team"] = matched_team
                if matched_team == team:
                    found_team_match = True

            if team:
                if found_team_match:
                    grn["grn_items"] = grn_items
                    filtered_grns.append(grn)
            else:
                grn["grn_items"] = grn_items
                filtered_grns.append(grn)

        print(f"\nReturning {len(filtered_grns)} GRNs after filtering by team.")
        return filtered_grns

    except Exception as e:
        error_message = str(e)
        print(f"Error occurred: {error_message}")
        frappe.log_error(message=error_message, title="Error in fetching GRN details")
        frappe.throw(_("An error occurred while fetching GRN details. Please check the logs for more details."))


@frappe.whitelist()
def get_grn_details_of_grn_number(grn_number):
    
    if not grn_number:
        frappe.throw("GRN number is required")

    grn = frappe.get_all(
        "GRN",
        filters={"grn_no": grn_number},
        fields=["*"]
    )

    if not grn:
        return []

    for record in grn:
        record["grn_items"] = frappe.get_all(
            "GRN Items",
            filters={"parent": record.get("name")},
            fields=["*"]
        )

    return grn