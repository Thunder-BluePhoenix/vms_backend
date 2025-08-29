from typing import Optional, Protocol, Any, Union
import frappe
from frappe.model.document import Document


class StageLike(Protocol):
    approval_stage: int
    approval_stage_name: str


def _as_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _stage_no(stage: Optional[StageLike]) -> Optional[int]:
    if stage is None:
        return None
    try:
        return int(getattr(stage, "approval_stage"))
    except Exception:
        return None


def _stage_name(stage: Optional[StageLike]) -> str:
    if stage is None:
        return ""
    return str(getattr(stage, "approval_stage_name", "") or "").strip()


def _require(condition: bool, msg: str):
    if not condition:
        frappe.throw(msg)


def add_approval_entry(
    doctype: str,
    doc: Union[Document, Any],
    next_action_by: Optional[str],
    cur_stage: StageLike,
    next_stage: Optional[StageLike],
    is_approved: Union[bool, int, str],
    action: str,
    remark: Optional[str],
):
    """
    Append a row to `approvals` child table with consistent, validated fields.

    Rules:
      - If `is_approved` and `next_stage` is None => final approval (approval_status=1, next_approval_stage=None).
      - If `is_approved` and `next_stage` exists => move to that stage (approval_status=0, next_approval_stage=next_stage.no).
      - If not approved => remain on current stage (approval_status=0, next_approval_stage=cur_stage.no).
      - `next_action_by` is only set when moving forward to a real next stage.
    """
    try:
        # ---- Basic validation ----
        _require(bool(doctype and str(doctype).strip()), "doctype is required.")
        _require(
            hasattr(doc, "append") and hasattr(doc, "save"), "Invalid doc provided."
        )
        cur_no = _stage_no(cur_stage)
        cur_name = _stage_name(cur_stage)
        _require(
            cur_no is not None,
            "cur_stage.approval_stage is required and must be an integer.",
        )
        _require(bool(cur_name), "cur_stage.approval_stage_name is required.")

        nxt_no = _stage_no(next_stage)
        nxt_name = _stage_name(next_stage) if next_stage else ""

        approved = _as_bool(is_approved)
        current_user = frappe.session.user or "Administrator"

        # ---- Derive statuses safely ----
        final_approval = approved and next_stage is None
        approval_status = 1 if final_approval else 0

        if approved:
            # Approved path
            if next_stage is not None and nxt_no is None:
                frappe.throw(
                    "next_stage.approval_stage must be an integer when provided."
                )
            next_approval_stage = nxt_no  # may be None for final step
            # Set next_action_by only if we actually have a next stage
            next_action_value = (
                (next_action_by or "").strip()
                if next_approval_stage is not None
                else ""
            )
        else:
            # Not approved: stay on current stage
            next_approval_stage = cur_no
            next_action_value = ""

        # Optional: normalize fields
        action_val = (action or "").strip()
        remark_val = (remark or "").strip()

        # ---- Check child table exists ----
        # Ensure the child table 'approvals' is defined on the DocType
        has_approvals = any(
            df.fieldname == "approvals"
            for df in getattr(doc.meta, "get_table_fields", lambda: [])()
        )
        _require(has_approvals, "Child table 'approvals' not found on this document.")

        # ---- Append row ----
        doc.append(
            "approvals",
            {
                "for_doc_type": doctype,
                # store the stage that was just acted upon
                "approval_stage": cur_no,
                "approval_stage_name": cur_name,
                "approved_by": current_user,
                "approval_status": approval_status,
                # where the workflow should go next (None/NULL if final)
                "next_approval_stage": next_approval_stage,
                "action": action_val,
                "next_action_by": next_action_value,
                "remark": remark_val,
            },
        )

        # ---- Save robustly ----
        # ignore_permissions keeps behavior compatible with your original function
        doc.save(ignore_permissions=True)

    except Exception as e:
        # Rich, structured error logging without dumping full doc contents
        context = {
            "doctype": doctype,
            "doc_doctype": getattr(doc, "doctype", None),
            "doc_name": getattr(doc, "name", None),
            "next_action_by": next_action_by,
            "cur_stage_no": _stage_no(cur_stage),
            "cur_stage_name": _stage_name(cur_stage),
            "next_stage_no": _stage_no(next_stage) if next_stage else None,
            "next_stage_name": _stage_name(next_stage) if next_stage else None,
            "is_approved": is_approved,
            "action": action,
        }
        frappe.log_error(
            title="add_approval_entry failed", message=frappe.as_json(context)
        )
        # Keep original behavior: re-raise as a user-visible error
        frappe.throw(str(e))
