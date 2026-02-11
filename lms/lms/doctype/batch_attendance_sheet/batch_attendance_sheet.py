import frappe
from frappe.model.document import Document


class BatchAttendanceSheet(Document):
	def on_submit(self):
		self.db_set("status", "Submitted", update_modified=False)

	def on_cancel(self):
		frappe.throw(
			"Attendance sheets cannot be cancelled. Use the Reopen action instead.",
			frappe.ValidationError,
		)

	def on_update_after_submit(self):
		frappe.throw(
			"Submitted attendance sheets are locked. Use the Reopen action to make changes.",
			frappe.ValidationError,
		)
