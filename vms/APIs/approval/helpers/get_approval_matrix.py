import fnmatch
import frappe


def get_approval_matrix_single_condition(
    doctype, docname
):
    filters = [
        ["Approval Matrix", "for_doc_type", "=", doctype],
        ["Approval Matrix", "is_active", "=", 1],
    ]

    

    matrix_list = frappe.get_all(
        "Approval Matrix",
        filters=filters,
        fields=["name", "conditional_field", "value"],
        order_by="creation desc",
    )

    if not matrix_list:
        frappe.throw(
            "No active Approval Matrix found for this document type.",
            exc=frappe.DoesNotExistError,
        )

    doc = frappe.get_cached_doc(doctype, docname)
    matrix_doc = None

    priority_matrix_list = []

    for matrix in matrix_list:
        conditional_field = matrix.get("conditional_field")
        value = matrix.get("value")
        if conditional_field and value and doc.get(conditional_field) == value:
            priority_matrix_list.append(matrix)

    if not priority_matrix_list:
        matrix_list = [
            matrix for matrix in matrix_list if not matrix.get("conditional_field")
        ]
        if not matrix_list:
            frappe.throw(
                "No active Approval Matrix found for this document type.",
                exc=frappe.DoesNotExistError,
            )

        matrix_doc = frappe.get_cached_doc(
            "Approval Matrix", matrix_list[0].get("name")
        )

    if priority_matrix_list:
        matrix_doc = frappe.get_cached_doc(
            "Approval Matrix", priority_matrix_list[0].get("name")
        )

    if not matrix_doc:
        frappe.throw(
            "No active Approval Matrix found for this document type.",
            exc=frappe.DoesNotExistError,
        )

    return matrix_doc


def get_approval_matrix_multiple_condition(
    doctype, docname
):
    """
    Returns the Approval Matrix whose ALL conditions match,
    falling back to the latest “no-condition” matrix if none match.
    If multiple match, returns the one with the highest match_count,
    and—on ties—the most recently created.
    """
    # 1) Load candidates’ names in creation order
    filters = {"for_doc_type": doctype, "is_active": 1}
   

    names = frappe.get_all(
        "Approval Matrix",
        filters=filters,
        fields=["name"],
    )
    if not names:
        frappe.log_error(f"No active Approval Matrix found for {doctype}")
        return None

    # 2) Load the target doc
    doc = frappe.get_cached_doc(doctype, docname)

    scored_matches = []  # list of (matrix_doc, match_count)
    fallbacks = []

    # 3) Evaluate each matrix’s child‐table of conditions
    for row in names:
        m = frappe.get_cached_doc("Approval Matrix", row.name)
        # count how many conditions were satisfied
        match_count = 0
        ok = True

        # single‐condition fields on the parent
        if m.conditional_field and m.value:
            if doc.get(m.conditional_field) == m.value:
                match_count += 1
            else:
                ok = False

        # any child‐table conditions?
        for cond in getattr(m, "conditions", []):
            if not ok:
                break

            actual = doc.get(cond.conditional_field)
            expected = cond.value
            op = cond.condition  # e.g. 'Equals', 'Not Equals', 'Like', etc.

            if op == "Equals":
                passed = str(actual) == str(expected)
            elif op == "Not Equals":
                passed = str(actual) != str(expected)
            elif op in ("Like", "Not Like"):
                # auto-wrap expected with '%' on both sides if none present
                has_leading_pct = expected.startswith("%")
                has_trailing_pct = expected.endswith("%")

                if not has_leading_pct and not has_trailing_pct:
                    pattern_sql = f"%{expected}%"
                else:
                    pattern_sql = expected

                # convert SQL wildcard to glob wildcard
                pattern_glob = pattern_sql.replace("%", "*").replace("_", "?")
                match = fnmatch.fnmatchcase(actual, pattern_glob)
                passed = match if op == "Like" else not match
            else:
                # unsupported operator
                passed = False

            if passed:
                match_count += 1
            else:
                ok = False

        # classify
        if not m.conditional_field and not getattr(m, "conditions", None):
            # no conditions at all → fallback candidate
            fallbacks.append(m)
        elif ok and match_count > 0:
            scored_matches.append((m, match_count))

    # 4) Pick the winner by highest match_count, breaking ties by creation order
    if scored_matches:
        # since names were loaded in creation‐desc order, ties preserve that order
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        matrix_doc = scored_matches[0][0]
    elif fallbacks:
        matrix_doc = fallbacks[0]
    else:
        frappe.throw(
            frappe._("No active Approval Matrix matched your conditions."),
            frappe.DoesNotExistError,
        )

    return matrix_doc


def get_approval_matrix(doctype, docname):
    return get_approval_matrix_multiple_condition(
        doctype, docname
    )


def get_stage_info(doctype, doc, approval_stage=None):
    try:
        matrix_doc = get_approval_matrix(doctype, doc.get("name"))
        if not matrix_doc:
                
                return {
                    "cur_stage_info": None,
                    "next_stage_info": None,
                    "approval_matrix": None
                }
        if not approval_stage:
            latest_approval = doc.approvals[-1] if doc.approvals else None
            # cur_stage = latest_approval.get("next_approval_stage") if latest_approval else 1
            cur_stage = latest_approval.get("next_approval_stage") or 1 if latest_approval else 1
        else:
            cur_stage = approval_stage
        cur_stage_info = matrix_doc.get("approval_stages", {"approval_stage": cur_stage})

        next_stage_info = matrix_doc.get(
            "approval_stages",
            {"approval_stage": cur_stage + 1},
        )

        prev_stage_info, next_to_next_stage_info = stage_info_for_qms(matrix_doc, cur_stage)
        if not cur_stage_info and not next_stage_info:
            frappe.throw("No next approval stage configured.")

        return {
            "cur_stage_info": cur_stage_info[0].as_dict() if cur_stage_info else None,
            "next_stage_info": next_stage_info[0].as_dict() if next_stage_info else None,
            "prev_stage_info": prev_stage_info[0].as_dict() if prev_stage_info else None,
            "next_to_next_stage_info": (
                next_to_next_stage_info[0].as_dict() if next_to_next_stage_info else None
            ),
            "approval_matrix": matrix_doc.get("name"),
        }
    except Exception as e:
        frappe.log_error(f"No approval matrix found for {doctype}: {str(e)}")
        return {
            "cur_stage_info": None, 
            "next_stage_info": None,
            "approval_matrix": None
        }


def stage_info_for_qms(matrix_doc, cur_stage):
    prev_stage_info = matrix_doc.get(
        "approval_stages",
        {"approval_stage": cur_stage - 1},
    )
    next_to_next_stage_info = matrix_doc.get(
        "approval_stages",
        {"approval_stage": cur_stage + 2},
    )
    return prev_stage_info, next_to_next_stage_info
