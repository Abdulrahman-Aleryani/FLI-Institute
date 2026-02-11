"""Grading-specific backend APIs used by the instructor UI."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.query_builder import DocType

from lms.lms.doctype.batch_grade_sheet.batch_grade_sheet import ensure_batch_permission


def _require_logged_in_user() -> str:
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to access instructor tools."), frappe.PermissionError)

	return frappe.session.user


@frappe.whitelist()
def get_batches_for_current_instructor():
	"""Return batches where the current user is mapped as Course Instructor."""
	user = _require_logged_in_user()

	Batch = DocType("LMS Batch")
	CourseInstructor = DocType("Course Instructor")

	query = (
		frappe.qb.from_(Batch)
		.join(CourseInstructor)
		.on((CourseInstructor.parent == Batch.name) & (CourseInstructor.parenttype == "LMS Batch"))
		.where(CourseInstructor.instructor == user)
		.select(
			Batch.name,
			Batch.title,
			Batch.start_date,
			Batch.end_date,
			Batch.timezone,
		)
		.orderby(Batch.start_date, order=frappe.qb.asc)
	)

	return query.run(as_dict=True)


@frappe.whitelist()
def get_enrolled_students(batch_name: str | None = None):
	"""Return enrolled students for the provided batch (id + full name)."""
	if not batch_name:
		return []

	ensure_batch_permission(batch_name)

	return frappe.get_all(
		"LMS Batch Enrollment",
		filters={"batch": batch_name},
		fields=["member as student", "member_name as student_name"],
		order_by="member_name asc",
	)


@frappe.whitelist()
def get_or_create_grade_sheet(batch_name: str | None = None):
	if not batch_name:
		frappe.throw(_("Batch is required."), frappe.ValidationError)

	user = _require_logged_in_user()
	ensure_batch_permission(batch_name, user=user)

	existing = frappe.get_all(
		"Batch Grade Sheet",
		filters={
			"batch": batch_name,
			"instructor": user,
			"docstatus": ["!=", 2],
		},
		fields=["name"],
		limit=1,
	)

	if existing:
		doc = frappe.get_doc("Batch Grade Sheet", existing[0].name)
	else:
		doc = frappe.new_doc("Batch Grade Sheet")
		doc.batch = batch_name
		doc.instructor = user
		doc.insert()

	return doc.as_dict()
