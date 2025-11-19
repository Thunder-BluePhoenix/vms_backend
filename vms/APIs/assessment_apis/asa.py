import frappe
from frappe import _
import json
from frappe.utils.file_manager import save_file
from frappe.utils.file_manager import get_file_url


@frappe.whitelist(allow_guest=True)
def get_asa_details(asa):
    try:
        # Get Vendor Onboarding document
        # vn_onb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get the linked QMS Assessment Form document
        asa_doc = frappe.get_doc("Annual Supplier Assessment Questionnaire",asa)

        # Get meta for field labels
        meta = frappe.get_meta("Annual Supplier Assessment Questionnaire")
        asa_data = []

        for field in meta.fields:
            fieldname = field.fieldname
            fieldlabel = field.label
            if fieldname:
                value = asa_doc.get(fieldname)
                asa_data.append({
                    "fieldname": fieldname,
                    "fieldlabel": fieldlabel,
                    "value": value
                })

        return {
            "asa_details": asa_data,
            "asa_doc_name": asa_doc.name
        }

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_asa_details Error")
        frappe.throw(_("An unexpected error occurred while fetching ASA details."))



@frappe.whitelist(allow_guest=True)
def get_asa_details_without_label(asa):
    try:
        # Get Vendor Onboarding document
        # vn_onb = frappe.get_doc("Vendor Onboarding", vendor_onboarding)

        # Get the linked QMS Assessment Form document
        asa_doc = frappe.get_doc("Annual Supplier Assessment Questionnaire",asa)

        # Get meta for field labels
        # meta = frappe.get_meta("Annual Supplier Assessment Questionnaire")
        # asa_data = []

        # for field in meta.fields:
        #     fieldname = field.fieldname
        #     fieldlabel = field.label
        #     if fieldname:
        #         value = asa_doc.get(fieldname)
        #         asa_data.append({
        #             "fieldname": fieldname,
        #             "fieldlabel": fieldlabel,
        #             "value": value
        #         })

        return {
            "asa_details": asa_doc.as_dict(),
            "asa_doc_name": asa_doc.name
        }

    except frappe.DoesNotExistError as e:
        frappe.throw(_("Document not found: {0}").format(str(e)))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_asa_details Error")
        frappe.throw(_("An unexpected error occurred while fetching ASA details."))


@frappe.whitelist(allow_guest=True)
def get_asa_list():
    # user = frappe.session.user
    # # emp = frappe.get_doc("Employee",{"user_id": user})
    # team = frappe.db.get_value("Employee", {"user_id": user}, "team")
    # user_ids = frappe.get_all("Employee", filters={"team": team}, pluck="user_id")
    # conditions = []
    # values = {}

    # conditions.append("vo.registered_by IN %(user_ids)s")
    # values["user_ids"] = user_ids


    all_asa = frappe.get_all("Annual Supplier Assessment Questionnaire", fields ="*", order_by = "modified desc")
    return all_asa


# Annual Supplier Form API

@frappe.whitelist(allow_guest=True)
def create_annual_asa_form(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		# Check if vendor_ref_no exists
		existing_doc = frappe.get_all(
			"Annual Supplier Assessment Questionnaire",
			filters={"vendor_ref_no": data.get("vendor_ref_no")},
			limit=1,
			fields=["name"]
		)

		if existing_doc:
			# Fetch and update existing doc
			annual_ass = frappe.get_doc("Annual Supplier Assessment Questionnaire", existing_doc[0].name)
		else:
			# Create new doc
			annual_ass = frappe.new_doc("Annual Supplier Assessment Questionnaire")

		# Common assignments (create or update)
		annual_ass.vendor_ref_no = data.get("vendor_ref_no")
		annual_ass.vendor_name = data.get("vendor_name")
		annual_ass.name_of_the_company = data.get("name_of_the_company")
		annual_ass.location = data.get("location")
		annual_ass.name_of_product = data.get("name_of_product")
		annual_ass.valid_consent_from_pollution_control = data.get("valid_consent_from_pollution_control")
		annual_ass.expiry_date_of_consent = data.get("expiry_date_of_consent")
		annual_ass.recycle_plastic_package_material = data.get("recycle_plastic_package_material")
		annual_ass.recycle_plastic_details = data.get("recycle_plastic_details")
		annual_ass.plans_for_recycle_materials = data.get("plans_for_recycle_materials")
		annual_ass.details_to_increase_recycle_material = data.get("details_to_increase_recycle_material")

		# Insert if new
		if not existing_doc:
			annual_ass.insert(ignore_permissions=True)
		else:
			annual_ass.save(ignore_permissions=True)

		annual_ass_name = annual_ass.name

		# File uploads (overwrite or add new)
		if "valid_consent" in frappe.request.files:
			file = frappe.request.files["valid_consent"]
			saved = save_file(file.filename, file.stream.read(), annual_ass.doctype, annual_ass.name, is_private=0)
			annual_ass.valid_consent = saved.file_url
			annual_ass.save(ignore_permissions=True)

		if "upload_file_2" in frappe.request.files:
			file = frappe.request.files["upload_file_2"]
			saved = save_file(file.filename, file.stream.read(), annual_ass.doctype, annual_ass.name, is_private=0)
			annual_ass.upload_file_2 = saved.file_url
			annual_ass.save(ignore_permissions=True)

		if "upload_file_3" in frappe.request.files:
			file = frappe.request.files["upload_file_3"]
			saved = save_file(file.filename, file.stream.read(), annual_ass.doctype, annual_ass.name, is_private=0)
			annual_ass.upload_file_3 = saved.file_url
			annual_ass.save(ignore_permissions=True)

		# Create sub-forms only if new
		if not existing_doc:
			# Governance
			governance_doc = frappe.new_doc("Governance Annual Supplier Assessment Questionnaire")
			governance_doc.annual_supplier_assessment_questionnaire = annual_ass_name
			governance_doc.insert(ignore_permissions=True)

			# Social
			social_doc = frappe.new_doc("Social Annual Supplier Assessment Questionnaire")
			social_doc.annual_supplier_assessment_questionnaire = annual_ass_name
			social_doc.insert(ignore_permissions=True)

			# Environment
			environment_doc = frappe.new_doc("Environment Annual Supplier Assessment Questionnaire")
			environment_doc.annual_supplier_assessment_questionnaire = annual_ass_name
			environment_doc.insert(ignore_permissions=True)

			# Link sub-forms
			annual_ass.governance_doctype = governance_doc.name
			annual_ass.social_doctype = social_doc.name
			annual_ass.environment_doctype = environment_doc.name
			annual_ass.save(ignore_permissions=True)
		else:
			governance_doc = frappe.get_doc("Governance Annual Supplier Assessment Questionnaire", annual_ass.governance_doctype)
			social_doc = frappe.get_doc("Social Annual Supplier Assessment Questionnaire", annual_ass.social_doctype)
			environment_doc = frappe.get_doc("Environment Annual Supplier Assessment Questionnaire", annual_ass.environment_doctype)

		return {
			"status": "success",
			"message": "Assessment form created/updated successfully",
			"assessment_name": annual_ass_name,
			"governance_doc": governance_doc.name,
			"social_doc": social_doc.name,
			"environment_doc": environment_doc.name
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create Annual Assessment Form Error")
		return {
			"status": "error",
			"message": "Failed to create/update assessment form",
			"error": str(e)
		}
     

# create env asa form
@frappe.whitelist(allow_guest=True)
def create_env_asa_form(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		annual_ass = frappe.get_doc("Annual Supplier Assessment Questionnaire", data.get("name"))
		env_doc = frappe.get_doc("Environment Annual Supplier Assessment Questionnaire", annual_ass.environment_doctype)

		env_doc.annual_supplier_assessment_questionnaire = annual_ass.name

		# Does your company have:
		env_doc.environment_sustainability_policy = data.get("environment_sustainability_policy")
		env_doc.details_1 = data.get("details_1")
		env_doc.environmental_management_certification = data.get("environmental_management_certification")
		env_doc.details_2 = data.get("details_2")
		env_doc.regular_audits_conducted = data.get("regular_audits_conducted")
		env_doc.details_3 = data.get("details_3")

		# Energy Consumption and Emissions
		env_doc.energy_consumption_tracking = data.get("energy_consumption_tracking")
		env_doc.total_energy_consumed = data.get("total_energy_consumed")
		env_doc.company_track_greenhouse_gas = data.get("company_track_greenhouse_gas")
		env_doc.scope_wise_chg_emission = data.get("scope_wise_chg_emission")
		env_doc.consume_renewable_energy = data.get("consume_renewable_energy")
		env_doc.total_renewable_energy_consumption = data.get("total_renewable_energy_consumption")
		env_doc.have_system_to_control_air_emission = data.get("have_system_to_control_air_emission")
		env_doc.details_of_system_to_control_air_emission = data.get("details_of_system_to_control_air_emission")
		env_doc.have_target_for_increase_renewable_share = data.get("have_target_for_increase_renewable_share")
		env_doc.mention_target_for_increase_renewable_share = data.get("mention_target_for_increase_renewable_share")
		env_doc.have_target_to_reduce_energy_consumption = data.get("have_target_to_reduce_energy_consumption")
		env_doc.mention_target_to_reduce_energy_consumption = data.get("mention_target_to_reduce_energy_consumption")

		env_doc.have_plan_to_improve_energy_efficiency = data.get("have_plan_to_improve_energy_efficiency")
		env_doc.list_plan_to_improve_energy_efficiency = data.get("list_plan_to_improve_energy_efficiency")

		env_doc.have_targets_to_reduce_emission = data.get("have_targets_to_reduce_emission")
		env_doc.details_of_targets_to_reduce_emission = data.get("details_of_targets_to_reduce_emission")

		env_doc.pcf_conducted = data.get("pcf_conducted")
		env_doc.details_12 = data.get("details_12")

		# Water Consumption and Management
		env_doc.water_source_tracking = data.get("water_source_tracking")
		env_doc.details_13 = data.get("details_13")
		env_doc.have_permission_for_groundwater = data.get("have_permission_for_groundwater")
		env_doc.details_14 = data.get("details_14")
		env_doc.has_system_to_track_water_withdrawals = data.get("has_system_to_track_water_withdrawals")
		env_doc.details_15 = data.get("details_15")
		env_doc.have_facility_to_recycle_wastewater = data.get("have_facility_to_recycle_wastewater")
		env_doc.details_16 = data.get("details_16")
		env_doc.have_zld_strategy = data.get("have_zld_strategy")
		env_doc.details_17 = data.get("details_17")

		env_doc.have_initiatives_to_increase_water_efficiency = data.get("have_initiatives_to_increase_water_efficiency")
		env_doc.details_to_increase_water_efficiency = data.get("details_to_increase_water_efficiency")

		env_doc.have_targets_to_reduce_water_consumption = data.get("have_targets_to_reduce_water_consumption")
		env_doc.targets_to_reduce_water_consumption = data.get("targets_to_reduce_water_consumption")

		# Waste Management
		env_doc.track_waste_generation = data.get("track_waste_generation")
		env_doc.details_20 = data.get("details_20")
		env_doc.handover_waste_to_authorized_vendor = data.get("handover_waste_to_authorized_vendor")
		env_doc.details_21 = data.get("details_21")
		env_doc.vendor_audits_for_waste_management = data.get("vendor_audits_for_waste_management")
		env_doc.details_22 = data.get("details_22")
		env_doc.have_epr_for_waste_management = data.get("have_epr_for_waste_management")
		env_doc.details_23 = data.get("details_23")
		env_doc.have_goals_to_reduce_waste = data.get("have_goals_to_reduce_waste")
		env_doc.details_of_goals_to_reduce_waste = data.get("details_of_goals_to_reduce_waste")

		# Green Products
		env_doc.certified_green_projects = data.get("certified_green_projects")
		env_doc.details_25 = data.get("details_25")

		# Biodiversity
		env_doc.have_policy_on_biodiversity = data.get("have_policy_on_biodiversity")
		env_doc.details_26 = data.get("details_26")

		# Attachments
		attach_fields = [
			"upload_file_1", "upload_file_2", "upload_file_3", "upload_file_4", "upload_file_5",
			"upload_file_6", "upload_file_7", "upload_file_8", "upload_file_9", "upload_file_10",
			"upload_file_11", "upload_file_12", "upload_file_13", "upload_file_14", "upload_file_15",
			"upload_file_16", "upload_file_17", "upload_file_18", "upload_file_19", "upload_file_20",
			"upload_file_21", "upload_file_22", "upload_file_23", "upload_file_24", "upload_file_25",
			"upload_file_26"
		]

		for attach_field in attach_fields:
			if attach_field in frappe.request.files:
				uploaded_file = frappe.request.files[attach_field]
				saved = save_file(
					uploaded_file.filename,
					uploaded_file.stream.read(),
					env_doc.doctype,
					env_doc.name,
					is_private=0
				)
				env_doc.set(attach_field, saved.file_url)

		env_doc.save(ignore_permissions=True)

		return {"status": "success", "message": "Environment ASA updated successfully", "docname": env_doc.name}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "create_env_asa_form")
		return {"status": "error", "message": str(e)}


# create social asa form
@frappe.whitelist(allow_guest=True)
def create_social_asa_form(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		annual_ass = frappe.get_doc("Annual Supplier Assessment Questionnaire", data.get("name"))
		social_doc = frappe.get_doc("Social Annual Supplier Assessment Questionnaire", annual_ass.social_doctype)

		social_doc.annual_supplier_assessment_questionnaire = annual_ass.name

		# Labor Rights and Working Conditions
		social_doc.have_prohibition_policy_of_child_labor = data.get("have_prohibition_policy_of_child_labor")
		social_doc.details_1 = data.get("details_1")
		social_doc.age_verification_before_hiring = data.get("age_verification_before_hiring")
		social_doc.details_2 = data.get("details_2")
		social_doc.ensure_modern_slavery_labor_policy = data.get("ensure_modern_slavery_labor_policy")
		social_doc.details_3 = data.get("details_3")
		social_doc.have_non_discrimination_policy = data.get("have_non_discrimination_policy")
		social_doc.details_4 = data.get("details_4")
		social_doc.has_setup_safety_report_incidents = data.get("has_setup_safety_report_incidents")
		social_doc.details_5 = data.get("details_5")
		social_doc.pending_legal_cases_workplace_harassment = data.get("pending_legal_cases_workplace_harassment")
		social_doc.details_of_pending_legal_cases = data.get("details_of_pending_legal_cases")
		social_doc.comply_minimum_wage_law_regulation = data.get("comply_minimum_wage_law_regulation")
		social_doc.details_7 = data.get("details_7")
		social_doc.legal_working_hours = data.get("legal_working_hours")
		social_doc.details_8 = data.get("details_8")
		social_doc.work_hrs_track_by_company = data.get("work_hrs_track_by_company")
		social_doc.details_9 = data.get("details_9")
		social_doc.has_diversity_inclusion_policy = data.get("has_diversity_inclusion_policy")
		social_doc.details_10 = data.get("details_10")
		social_doc.have_target_to_promote_diversity = data.get("have_target_to_promote_diversity")
		social_doc.details_of_targets = data.get("details_of_targets")

		# Grievance Mechanism
		social_doc.have_grievance_mechanism = data.get("have_grievance_mechanism")
		social_doc.details_12 = data.get("details_12")

		# Employee Well Being
		social_doc.any_emp_well_being_initiative = data.get("any_emp_well_being_initiative")
		social_doc.details_of_initiatives = data.get("details_of_initiatives")

		# Health and Safety
		social_doc.has_develop_health_safety_policy = data.get("has_develop_health_safety_policy")
		social_doc.details_14 = data.get("details_14")
		social_doc.have_healthy_safety_management = data.get("have_healthy_safety_management")
		social_doc.details_15 = data.get("details_15")
		social_doc.conduct_hira_activity = data.get("conduct_hira_activity")
		social_doc.details_16 = data.get("details_16")
		social_doc.certify_ohs_system = data.get("certify_ohs_system")
		social_doc.details_17 = data.get("details_17")
		social_doc.emp_trained_health_safety = data.get("emp_trained_health_safety")
		social_doc.details_18 = data.get("details_18")
		social_doc.mention_behavior_base_safety = data.get("mention_behavior_base_safety")
		social_doc.track_health_safety_indicators = data.get("track_health_safety_indicators")
		social_doc.details_19 = data.get("details_19")
		social_doc.provide_any_healthcare_services = data.get("provide_any_healthcare_services")
		social_doc.details_of_healthcare_services = data.get("details_of_healthcare_services")

		# Employee Satisfaction
		social_doc.conduct_esat = data.get("conduct_esat")
		social_doc.esat_score = data.get("esat_score")

		# Attachments
		attach_fields = [
			"upload_file_1", "upload_file_2", "upload_file_3", "upload_file_4", "upload_file_5",
			"upload_file_6", "upload_file_7", "upload_file_8", "upload_file_9", "upload_file_10",
			"upload_file_11", "upload_file_12", "upload_file_13", "upload_file_14", "upload_file_15",
			"upload_file_16", "upload_file_17", "upload_file_18", "upload_file_19", "upload_file_20",
			"upload_file_21"
		]

		for attach_field in attach_fields:
			if attach_field in frappe.request.files:
				uploaded_file = frappe.request.files[attach_field]
				saved = save_file(
					uploaded_file.filename,
					uploaded_file.stream.read(),
					social_doc.doctype,
					social_doc.name,
					is_private=0
				)
				social_doc.set(attach_field, saved.file_url)

		social_doc.save(ignore_permissions=True)

		return {"status": "success", "message": "Social ASA updated successfully", "docname": social_doc.name}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "create_social_asa_form")
		return {"status": "error", "message": str(e)}


# create social Governance form
@frappe.whitelist(allow_guest=True)
def create_gov_asa_form(data):
	try:
		if isinstance(data, str):
			data = json.loads(data)

		annual_ass = frappe.get_doc("Annual Supplier Assessment Questionnaire", data.get("name"))
		gov_doc = frappe.get_doc("Governance Annual Supplier Assessment Questionnaire", annual_ass.governance_doctype)

		gov_doc.annual_supplier_assessment_questionnaire = annual_ass.name

		# Governance Section
		gov_doc.have_formal_governance_structure = data.get("have_formal_governance_structure")
		gov_doc.details_1 = data.get("details_1")
		gov_doc.esg_policies_coverage = data.get("esg_policies_coverage")
		gov_doc.details_2 = data.get("details_2")
		gov_doc.esg_risk_integration = data.get("esg_risk_integration")
		gov_doc.details_3 = data.get("details_3")
		gov_doc.company_publish_sustainability_report = data.get("company_publish_sustainability_report")
		gov_doc.details_4 = data.get("details_4")
		gov_doc.esg_rating_participated = data.get("esg_rating_participated")
		gov_doc.esg_rating_score = data.get("esg_rating_score")
		gov_doc.esg_incentive_for_employee = data.get("esg_incentive_for_employee")
		gov_doc.details_6 = data.get("details_6")
		gov_doc.csat_survey_conducted = data.get("csat_survey_conducted")
		gov_doc.csat_score = data.get("csat_score")
		gov_doc.instance_of_loss_customer_data = data.get("instance_of_loss_customer_data")
		gov_doc.no_of_loss_data_incidents = data.get("no_of_loss_data_incidents")

		# Attachments
		attach_fields = [
			"upload_file_1", "upload_file_2", "upload_file_3", "upload_file_4",
			"upload_file_5", "upload_file_6", "upload_file_7", "upload_file_8"
		]

		for attach_field in attach_fields:
			if attach_field in frappe.request.files:
				uploaded_file = frappe.request.files[attach_field]
				saved = save_file(
					uploaded_file.filename,
					uploaded_file.stream.read(),
					gov_doc.doctype,
					gov_doc.name,
					is_private=0
				)
				gov_doc.set(attach_field, saved.file_url)

		gov_doc.save(ignore_permissions=True)

		annual_ass.form_is_submitted = 1
		annual_ass.save(ignore_permissions=True)

		return {"status": "success", "message": "Governance ASA updated successfully", "docname": gov_doc.name}

	except Exception as e:
		frappe.local.response["http_status_code"] = 500
		frappe.log_error(frappe.get_traceback(), "create_gov_asa_form")
		return {"status": "error", "message": str(e)}


# Verify the ASA Form
@frappe.whitelist(allow_guest=True, methods=['POST'])
def verify_asa_form(asa_name=None):
	try:
		if not asa_name:
			frappe.local.response["http_status_code"] = 404
			return {
				"status": "error",
				"message": "asa_name is required"
			}

		asa_doc = frappe.get_doc("Annual Supplier Assessment Questionnaire", asa_name)

		asa_doc.verify_by_asa_team = 1
		asa_doc.save(ignore_permissions=True)

		return {
			"status": "success",
			"message": "Verified successfully"
		}

	except frappe.DoesNotExistError:
		frappe.local.response["http_status_code"] = 404
		return {
			"status": "error",
			"message": "ASA form not found"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in verify_asa_form API")
		frappe.local.response["http_status_code"] = 500
		return {
			"status": "error",
			"message": "Something went wrong",
			"error": str(e)
		}


# send full data of asa form
@frappe.whitelist(allow_guest=True)
def get_data_ann_asa_form(vendor_ref_no):
	try:
		ann_doc = frappe.get_doc("Annual Supplier Assessment Questionnaire", {"vendor_ref_no": vendor_ref_no})

		# Section 1: Company Information
		company_information = {
			"vendor_ref_no": ann_doc.vendor_ref_no,
			"vendor_name": ann_doc.vendor_name,
			"name_of_the_company": ann_doc.name_of_the_company,
			"location": ann_doc.location,
			"name_of_product": ann_doc.name_of_product,
			# "name": ann_doc.name,
			# "governance_doctype": ann_doc.governance_doctype,
			# "environment_doctype": ann_doc.environment_doctype,
			# "social_doctype": ann_doc.social_doctype
		}

		# Section 2: General Disclosure
		general_disclosure = {
			"valid_consent_from_pollution_control": ann_doc.valid_consent_from_pollution_control,
			"expiry_date_of_consent": ann_doc.expiry_date_of_consent,
			"recycle_plastic_package_material": ann_doc.recycle_plastic_package_material,
			"plans_for_recycle_materials": ann_doc.plans_for_recycle_materials,
			"recycle_plastic_details": ann_doc.recycle_plastic_details,
			"details_to_increase_recycle_material": ann_doc.details_to_increase_recycle_material
		}

		# Handle attached file for valid_consent
		# if ann_doc.valid_consent:
		# 	file_doc = frappe.get_doc("File", {"file_url": ann_doc.valid_consent})
		# 	general_disclosure["valid_consent"] = {
		# 		"url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
		# 		"name": file_doc.name,
		# 		"file_name": file_doc.file_name
		# 	}
		# else:
		# 	general_disclosure["valid_consent"] = {
		# 		"url": "",
		# 		"name": "",
		# 		"file_name": ""
		# 	}

		for field in ["valid_consent", "upload_file_2", "upload_file_3"]:
			file_url = getattr(ann_doc, field, "")
			if file_url:
				try:
					file_doc = frappe.get_doc("File", {"file_url": file_url})
					general_disclosure[field] = {
						"url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
						"name": file_doc.name,
						"file_name": file_doc.file_name
					}
				except:
					general_disclosure[field] = {
						"url": "",
						"name": "",
						"file_name": ""
					}
			else:
				general_disclosure[field] = {
					"url": "",
					"name": "",
					"file_name": ""
			}


		# linked_documents = {
		# 	"governance_doc": ann_doc.governance_doctype,
		# 	"social_doc": ann_doc.social_doctype,
		# 	"environment_doc": ann_doc.environment_doctype
		# }

		env_manage_system = {}
		energy_cons_emis = {}
		water_cons_mang = {}
		waste_management = {}
		green_products = {}
		biodiversity = {}
		labor_rights_condi = {}
		griv_mechanism = {}
		emp_well_being = {}
		health_safety = {}
		emp_satisfaction = {}
		governance = {}

		if ann_doc.environment_doctype:
			env_doc = frappe.get_doc("Environment Annual Supplier Assessment Questionnaire", ann_doc.environment_doctype)

			# Environmental Management System section
			env_manage_system = {
				"environment_sustainability_policy": env_doc.environment_sustainability_policy,
				"environmental_management_certification": env_doc.environmental_management_certification,
				"regular_audits_conducted": env_doc.regular_audits_conducted,
				"details_1": env_doc.details_1,
				"details_2": env_doc.details_2,
				"details_3": env_doc.details_3
			}
			for i in range(1, 4):
				field = f"upload_file_{i}"
				env_manage_system[field] = get_file_data(getattr(env_doc, field, None))

			# Energy Consumption and Emissions
			energy_cons_emis = {
				"energy_consumption_tracking": env_doc.energy_consumption_tracking,
				"total_energy_consumed": env_doc.total_energy_consumed,
				"company_track_greenhouse_gas": env_doc.company_track_greenhouse_gas,
				"scope_wise_chg_emission": env_doc.scope_wise_chg_emission,
				"consume_renewable_energy": env_doc.consume_renewable_energy,
				"total_renewable_energy_consumption": env_doc.total_renewable_energy_consumption,
				"have_system_to_control_air_emission": env_doc.have_system_to_control_air_emission,
				"details_of_system_to_control_air_emission": env_doc.details_of_system_to_control_air_emission,
				"have_target_for_increase_renewable_share": env_doc.have_target_for_increase_renewable_share,
				"mention_target_for_increase_renewable_share": env_doc.mention_target_for_increase_renewable_share,
				"have_target_to_reduce_energy_consumption": env_doc.have_target_to_reduce_energy_consumption,
				"mention_target_to_reduce_energy_consumption": env_doc.mention_target_to_reduce_energy_consumption,
				"have_plan_to_improve_energy_efficiency": env_doc.have_plan_to_improve_energy_efficiency,
				"list_plan_to_improve_energy_efficiency": env_doc.list_plan_to_improve_energy_efficiency,
				"have_targets_to_reduce_emission": env_doc.have_targets_to_reduce_emission,
				"details_of_targets_to_reduce_emission": env_doc.details_of_targets_to_reduce_emission,
				"pcf_conducted": env_doc.pcf_conducted
			}
			for i in range(4, 13):
				field = f"upload_file_{i}"
				energy_cons_emis[field] = get_file_data(getattr(env_doc, field, None))

			# Water Consumption and Management
			water_cons_mang = {
				"water_source_tracking": env_doc.water_source_tracking,
				"details_13": env_doc.details_13,
				"have_permission_for_groundwater": env_doc.have_permission_for_groundwater,
				"details_14": env_doc.details_14,
				"has_system_to_track_water_withdrawals": env_doc.has_system_to_track_water_withdrawals,
				"details_15": env_doc.details_15,
				"have_facility_to_recycle_wastewater": env_doc.have_facility_to_recycle_wastewater,
				"details_16": env_doc.details_16,
				"have_zld_strategy": env_doc.have_zld_strategy,
				"details_17": env_doc.details_17,
				"have_initiatives_to_increase_water_efficiency": env_doc.have_initiatives_to_increase_water_efficiency,
				"details_to_increase_water_efficiency": env_doc.details_to_increase_water_efficiency,
				"have_targets_to_reduce_water_consumption": env_doc.have_targets_to_reduce_water_consumption,
				"targets_to_reduce_water_consumption": env_doc.targets_to_reduce_water_consumption
			}
			for i in range(13, 20):
				field = f"upload_file_{i}"
				water_cons_mang[field] = get_file_data(getattr(env_doc, field, None))

			# Waste Management
			waste_management = {
				"track_waste_generation": env_doc.track_waste_generation,
				"details_20": env_doc.details_20,
				"handover_waste_to_authorized_vendor": env_doc.handover_waste_to_authorized_vendor,
				"details_21": env_doc.details_21,
				"vendor_audits_for_waste_management": env_doc.vendor_audits_for_waste_management,
				"details_22": env_doc.details_22,
				"have_epr_for_waste_management": env_doc.have_epr_for_waste_management,
				"details_23": env_doc.details_23,
				"have_goals_to_reduce_waste": env_doc.have_goals_to_reduce_waste,
				"details_of_goals_to_reduce_waste": env_doc.details_of_goals_to_reduce_waste
			}
			for i in range(20, 25):
				field = f"upload_file_{i}"
				waste_management[field] = get_file_data(getattr(env_doc, field, None))

			# Green Products
			green_products = {
				"certified_green_projects": env_doc.certified_green_projects,
				"details_25": env_doc.details_25,
				"upload_file_25": get_file_data(getattr(env_doc, "upload_file_25", None))
			}

			# Biodiversity
			biodiversity = {
				"have_policy_on_biodiversity": env_doc.have_policy_on_biodiversity,
				"details_26":env_doc.details_26,
				"upload_file_26": get_file_data(getattr(env_doc, "upload_file_26", None))
			}

		if ann_doc.social_doctype:
			social_doc = frappe.get_doc("Social Annual Supplier Assessment Questionnaire", ann_doc.social_doctype)

			labor_rights_condi = {
				"have_prohibition_policy_of_child_labor": social_doc.have_prohibition_policy_of_child_labor,
				"age_verification_before_hiring": social_doc.age_verification_before_hiring,
				"ensure_modern_slavery_labor_policy": social_doc.ensure_modern_slavery_labor_policy,
				"have_non_discrimination_policy": social_doc.have_non_discrimination_policy,
				"has_setup_safety_report_incidents": social_doc.has_setup_safety_report_incidents,
				"pending_legal_cases_workplace_harassment": social_doc.pending_legal_cases_workplace_harassment,
				"details_of_pending_legal_cases": social_doc.details_of_pending_legal_cases,
				"comply_minimum_wage_law_regulation": social_doc.comply_minimum_wage_law_regulation,
				"legal_working_hours": social_doc.legal_working_hours,
				"work_hrs_track_by_company": social_doc.work_hrs_track_by_company,
				"has_diversity_inclusion_policy": social_doc.has_diversity_inclusion_policy,
				"have_target_to_promote_diversity": social_doc.have_target_to_promote_diversity,
				"details_of_targets": social_doc.details_of_targets
			}
			for i in range(1, 12):
				field = f"upload_file_{i}"
				labor_rights_condi[field] = get_file_data(getattr(social_doc, field, None))

			griv_mechanism = {
				"have_grievance_mechanism": social_doc.have_grievance_mechanism,
				"upload_file_12": get_file_data(getattr(social_doc, "upload_file_12", None))
			}

			emp_well_being = {
				"any_emp_well_being_initiative": social_doc.any_emp_well_being_initiative,
				"details_of_initiatives": social_doc.details_of_initiatives,
				"upload_file_13": get_file_data(getattr(social_doc, "upload_file_13", None))
			}

			health_safety = {
				"has_develop_health_safety_policy": social_doc.has_develop_health_safety_policy,
				"have_healthy_safety_management": social_doc.have_healthy_safety_management,
				"conduct_hira_activity": social_doc.conduct_hira_activity,
				"certify_ohs_system": social_doc.certify_ohs_system,
				"emp_trained_health_safety": social_doc.emp_trained_health_safety,
				"mention_behavior_base_safety": social_doc.mention_behavior_base_safety,
				"track_health_safety_indicators": social_doc.track_health_safety_indicators,
				"provide_any_healthcare_services": social_doc.provide_any_healthcare_services,
				"details_of_healthcare_services": social_doc.details_of_healthcare_services,
				"details_14": social_doc.details_14,
				"details_15": social_doc.details_15,
				"details_16": social_doc.details_16,
				"details_17": social_doc.details_17,
				"details_18": social_doc.details_18,
				"details_19": social_doc.details_19,


			}
			for i in range(14, 21):
				field = f"upload_file_{i}"
				health_safety[field] = get_file_data(getattr(social_doc, field, None))

			emp_satisfaction = {
				"conduct_esat": social_doc.conduct_esat,
				"esat_score": social_doc.esat_score,
				"upload_file_21": get_file_data(getattr(social_doc, "upload_file_21", None))
			}

		if ann_doc.governance_doctype:
			gov_doc = frappe.get_doc("Governance Annual Supplier Assessment Questionnaire", ann_doc.governance_doctype)
			governance = {
				"have_formal_governance_structure": gov_doc.have_formal_governance_structure,
				"details_1": gov_doc.details_1,
				"esg_policies_coverage": gov_doc.esg_policies_coverage,
				"details_2": gov_doc.details_2,
				"esg_risk_integration": gov_doc.esg_risk_integration,
				"details_3": gov_doc.details_3,
				"company_publish_sustainability_report": gov_doc.company_publish_sustainability_report,
				"details_4": gov_doc.details_4,
				"esg_rating_participated": gov_doc.esg_rating_participated,
				"esg_rating_score": gov_doc.esg_rating_score,
				"esg_incentive_for_employee": gov_doc.esg_incentive_for_employee,
				"details_6": gov_doc.details_6,
				"csat_survey_conducted": gov_doc.csat_survey_conducted,
				"csat_score": gov_doc.csat_score,
				"instance_of_loss_customer_data": gov_doc.instance_of_loss_customer_data,
				"no_of_loss_data_incidents": gov_doc.no_of_loss_data_incidents
			}
			for i in range(1, 9):
				field = f"upload_file_{i}"
				governance[field] = get_file_data(getattr(gov_doc, field, None))

		return {
			"status": "success",
			"message": "Data fetched successfully",
			"name": ann_doc.name,
			"form_is_submitted": ann_doc.form_is_submitted,
			"governance_doctype": ann_doc.governance_doctype,
			"environment_doctype": ann_doc.environment_doctype,
			"social_doctype": ann_doc.social_doctype,
			"company_information": company_information,
			"general_disclosure": general_disclosure,
			"env_manage_system": env_manage_system,
			"energy_cons_emis": energy_cons_emis,
			"water_cons_mang": water_cons_mang,
			"waste_management": waste_management,
			"green_products": green_products,
			"biodiversity": biodiversity,
			"labor_rights_condi": labor_rights_condi,
			"griv_mechanism": griv_mechanism,
			"emp_well_being": emp_well_being,
			"health_safety": health_safety,
			"emp_satisfaction": emp_satisfaction,
			"governance": governance
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Annual Assessment Form Data Error")
		return {
			"status": "error",
			"message": "Failed to fetch data",
			"error": str(e)
		}


def get_file_data(file_url):
	if file_url:
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		return {
			"url": f"{frappe.get_site_config().get('backend_http', 'http://10.10.103.155:3301')}{file_doc.file_url}",
			"name": file_doc.name,
			"file_name": file_doc.file_name
		}
	else:
		return {
			"url": "",
			"name": "",
			"file_name": ""
		}
