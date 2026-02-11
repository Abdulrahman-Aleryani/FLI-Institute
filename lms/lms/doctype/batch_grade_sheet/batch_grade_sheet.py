import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

GRADE_COMPONENTS = {
	"attendance": {"label": _("Attendance"), "max": 10},
	"participation": {"label": _("Participation"), "max": 10},
	"assignments": {"label": _("Assignments"), "max": 10},
	"speaking": {"label": _("Speaking"), "max": 10},
	"writing": {"label": _("Writing"), "max": 15},
	"communicative_competence": {"label": _("Communicative Competence"), "max": 10},
	"final_oral": {"label": _("Final Oral"), "max": 10},
	"exam": {"label": _("Exam"), "max": 25},
}
GRADE_FIELDS = tuple(GRADE_COMPONENTS.keys())
MAX_TOTAL = sum(component["max"] for component in GRADE_COMPONENTS.values())


def ensure_batch_permission(batch: str, user: str | None = None) -> None:
	"""Ensure the given user can manage grades for the batch."""
	if not batch:
		frappe.throw(_("Batch is required."), frappe.ValidationError)

	user = user or frappe.session.user
	if user == "Administrator" or frappe.db.get_value("Has Role", {"parent": user, "role": "System Manager"}):
		return

	exists = frappe.db.exists(
		"Course Instructor",
		{
			"parent": batch,
			"parenttype": "LMS Batch",
			"instructor": user,
		},
	)

	if not exists:
		frappe.throw(
			_("You are not allowed to manage grades for batch {0}.").format(batch),
			frappe.PermissionError,
		)


def _student_label(row) -> str:
	return row.student_name or row.student or _("row #{0}").format(row.idx)


def recalculate_row_total(row, enforce_limits: bool = False) -> float:
	"""Recalculate and set the total for a child row."""
	total = 0.0
	for fieldname, component in GRADE_COMPONENTS.items():
		raw_value = row.get(fieldname)
		value = None if raw_value in (None, "") else flt(raw_value, 2)

		if value is not None:
			if enforce_limits and (value < 0 or value > component["max"]):
				frappe.throw(
					_("{label} for {student} must be between 0 and {max_points}.").format(
						label=component["label"],
						student=_student_label(row),
						max_points=component["max"],
					)
				)

			total += value

	row.total = flt(total, 2)
	return row.total


class BatchGradeSheet(Document):
	def validate(self):
		ensure_batch_permission(self.batch)
		self._recompute_totals(enforce_limits=True)

	def before_submit(self):
		ensure_batch_permission(self.batch)

		if not self.grade_records:
			frappe.throw(_("Add at least one grade record before submitting."))

		for row in self.grade_records:
			for fieldname, component in GRADE_COMPONENTS.items():
				if row.get(fieldname) in (None, ""):
					frappe.throw(
						_("Please enter {label} for {student} before submitting.").format(
							label=component["label"],
							student=_student_label(row),
						)
					)

			row_total = recalculate_row_total(row, enforce_limits=True)

			if row_total > MAX_TOTAL:
				frappe.throw(
					_("Total for {student} cannot exceed {max_points}.").format(
						student=_student_label(row),
						max_points=MAX_TOTAL,
					),
				)

	def _recompute_totals(self, enforce_limits: bool = False):
		for row in self.grade_records or []:
			recalculate_row_total(row, enforce_limits=enforce_limits)
