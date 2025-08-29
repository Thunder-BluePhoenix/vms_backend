# Copyright (c) 2024, Meril and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType


class ApprovalMatrix(Document):
    def autoname(self):
        prefix = f"AM-"

        ApprovalMatrixTable = DocType("Approval Matrix")

        # Fetch names that match the prefix
        names = (
            frappe.qb.from_(ApprovalMatrixTable)
            .select(ApprovalMatrixTable.name)
            .where(ApprovalMatrixTable.name.like(f"{prefix}%"))
        ).run(pluck=True)

        # Extract numeric parts and sort manually
        numbers = [
            int(name.split("-")[-1]) for name in names if name.split("-")[-1].isdigit()
        ]
        last_number = max(numbers) if numbers else 0
        next_number = last_number + 1

        self.name = f"{prefix}{str(next_number).zfill(5)}"

    def update_approval_stage(self):
        if self.approval_stages:
            for approval_stage in self.approval_stages:
                if approval_stage.approval_stage != approval_stage.idx:
                    approval_stage.db_set("approval_stage", approval_stage.idx)

    def after_insert(self):
        self.update_approval_stage()

    def on_update(self):
        self.update_approval_stage()
