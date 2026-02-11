import frappe
from frappe import _
from frappe.model.document import Document


class BatchAttendanceSession(Document):
	pass


@frappe.whitelist()
def get_enrollments_for_batch(batch: str):
	if not batch:
		return []

	if not frappe.has_permission("Batch Attendance Session", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return frappe.get_all(
		"LMS Batch Enrollment",
		filters={"batch": batch},
		fields=["name", "member", "member_name"],
		order_by="member_name asc",
	)
