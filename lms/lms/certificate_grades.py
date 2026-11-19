from html import unescape

import frappe
from frappe.utils import flt

from lms.lms.doctype.batch_grade_sheet.batch_grade_sheet import (
	GRADE_COMPONENTS,
	GRADE_FIELDS,
	recalculate_row_total,
)

DEFAULT_GRADE_BANDS = [
	(90, "Excellent"),
	(80, "Very Good"),
	(70, "Good"),
	(60, "Pass"),
]

PASSING_MARK = 75


def is_passing(grades):
	"""Whether collected grades meet the passing mark.

	When a student has no grade record, failure cannot be proven, so the
	certificate is treated as passing.
	"""
	if not grades:
		return True
	return flt(grades.get("mark")) >= PASSING_MARK


def get_grade_bands():
	rows = frappe.get_all(
		"Certificate Grade Band",
		filters={"parent": "LMS Settings", "parenttype": "LMS Settings"},
		fields=["min_mark", "label"],
	)
	return [(flt(row.min_mark), row.label) for row in rows] or DEFAULT_GRADE_BANDS


def get_grade_label(mark, bands=None):
	"""Label of the highest band whose minimum is <= mark, else empty."""
	mark = flt(mark)
	for minimum, label in sorted(bands if bands is not None else get_grade_bands(), reverse=True):
		if mark >= minimum:
			return label
	return ""


def earned_total(record):
	"""Earned total from the component marks, not the stored ``total`` field.

	``total`` can drift from the components — e.g. when a row is written
	directly — so the marks are summed again, matching ``recalculate_row_total``.
	Over-max marks count as entered (they are what was earned on record); when
	no component mark exists at all, the stored total is the only thing to go on.
	"""
	if any(record.get(fieldname) not in (None, "") for fieldname in GRADE_FIELDS):
		return recalculate_row_total(record)
	return flt(record.total)


def collect_grades(cert):
	"""Grades for a certificate's member from the latest submitted sheet of its batch, or None."""
	if not cert.batch_name:
		return None

	sheets = frappe.get_all(
		"Batch Grade Sheet",
		filters={"batch": cert.batch_name, "docstatus": 1},
		fields=["name", "term", "instructor_name"],
		order_by="modified desc",
	)
	for sheet in sheets:
		record = frappe.db.get_value(
			"Batch Grade Record",
			{"parent": sheet.name, "parenttype": "Batch Grade Sheet", "student": cert.member},
			["total", "teacher_comments"] + list(GRADE_FIELDS),
			as_dict=True,
		)
		if record:
			mark = earned_total(record)
			return {
				"mark": mark,
				"grade_label": get_grade_label(mark),
				"term": sheet.term or "",
				"teacher_name": sheet.instructor_name or "",
				# Frappe stores "&" as "&amp;" in text fields; the template escapes on output
				"teacher_comments": unescape(record.teacher_comments or ""),
				"components": [
					{
						"key": fieldname,
						"label": str(GRADE_COMPONENTS[fieldname]["label"]),
						"mark": flt(record.get(fieldname)),
						"max": GRADE_COMPONENTS[fieldname]["max"],
					}
					for fieldname in GRADE_FIELDS
				],
			}
	return None
