import frappe
from frappe.utils import flt

DEFAULT_GRADE_BANDS = [
	(90, "Excellent"),
	(80, "Very Good"),
	(70, "Good"),
	(60, "Pass"),
]


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
			["total", "teacher_comments"],
			as_dict=True,
		)
		if record:
			return {
				"mark": flt(record.total),
				"grade_label": get_grade_label(record.total),
				"term": sheet.term or "",
				"teacher_name": sheet.instructor_name or "",
				"teacher_comments": record.teacher_comments or "",
			}
	return None
