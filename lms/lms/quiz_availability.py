import frappe
from frappe import _
from frappe.utils import format_datetime, get_datetime, now_datetime


STAFF_ROLES = {"System Manager", "Moderator", "Course Creator"}


def user_can_manage_quizzes(user=None):
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	if user in {"Administrator"}:
		return True
	return bool(STAFF_ROLES.intersection(set(frappe.get_roles(user))))


def get_quiz_availability(quiz_name, user=None):
	user = user or frappe.session.user
	doc = (
		quiz_name
		if isinstance(quiz_name, frappe.model.document.Document)
		else frappe.get_cached_doc("LMS Quiz", quiz_name)
	)
	start = get_datetime(doc.available_from) if doc.available_from else None
	end = get_datetime(doc.available_until) if doc.available_until else None
	now = now_datetime()

	is_staff = user_can_manage_quizzes(user)
	status = "open"
	message = None
	can_view = True
	can_start = True

	if not is_staff:
		if start and now < start:
			status = "upcoming"
			message = _("This quiz will be available on {0}").format(format_datetime(start))
			can_view = False
			can_start = False
		elif end and now > end:
			status = "expired"
			message = _("This quiz is no longer available")
			can_view = False
			can_start = False

	return frappe._dict(
		{
			"quiz": doc.name,
			"title": doc.title,
			"available_from": doc.available_from,
			"available_until": doc.available_until,
			"status": status,
			"message": message,
			"can_view": can_view or is_staff,
			"can_start": can_start or is_staff,
			"is_staff": is_staff,
		}
	)


def ensure_quiz_can_start(quiz_name, user=None):
	availability = get_quiz_availability(quiz_name, user=user)
	if not availability.can_start:
		frappe.throw(availability.message, frappe.PermissionError)
	return availability
