import hmac
import re

import frappe
from frappe import _
from frappe.utils import cint, format_date

from lms.lms.certificate_renderer import DATE_FORMAT
from lms.lms.doctype.lms_certificate.lms_certificate import get_certificate_status

no_cache = 1

TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
RATE_LIMIT = 30
RATE_WINDOW = 60


def get_context(context):
	context.no_cache = 1
	context.no_breadcrumbs = True
	context.no_sitemap = 1
	context.title = _("Certificate Verification")

	check_rate_limit()
	certificate = get_certificate(frappe.form_dict.get("token"))

	if not certificate:
		frappe.local.response["http_status_code"] = 404
		context.found = False
		return

	context.found = True
	context.status = get_certificate_status(certificate.revoked)
	context.student_name = certificate.member_name
	context.course_title = certificate.course_title
	context.batch_title = certificate.batch_title
	context.start_date = format_date(certificate.start_date, DATE_FORMAT) if certificate.start_date else ""
	context.end_date = format_date(certificate.end_date, DATE_FORMAT) if certificate.end_date else ""
	context.serial_number = certificate.serial_number


def check_rate_limit():
	key = f"lms_verify_rate:{frappe.local.request_ip or 'unknown'}"
	cache = frappe.cache()
	count = cint(cache.get_value(key))
	if count >= RATE_LIMIT:
		frappe.throw(_("Too many requests. Please try again later."), frappe.TooManyRequestsError)
	cache.set_value(key, count + 1, expires_in_sec=RATE_WINDOW)


def get_certificate(token):
	if not token or not TOKEN_PATTERN.match(token):
		return None

	certificate = frappe.db.get_value(
		"LMS Certificate",
		{"verification_token": token},
		[
			"name",
			"verification_token",
			"member_name",
			"course_title",
			"batch_name",
			"batch_title",
			"serial_number",
			"revoked",
		],
		as_dict=True,
	)
	# The database collation may be case-insensitive, so confirm the exact token.
	if not certificate or not hmac.compare_digest(certificate.verification_token.encode(), token.encode()):
		return None

	certificate.start_date = certificate.end_date = None
	if certificate.batch_name:
		dates = frappe.db.get_value(
			"LMS Batch", certificate.batch_name, ["start_date", "end_date"], as_dict=True
		)
		if dates:
			certificate.start_date = dates.start_date
			certificate.end_date = dates.end_date
	return certificate
