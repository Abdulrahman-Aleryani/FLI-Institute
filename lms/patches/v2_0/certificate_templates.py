import secrets

import frappe
from frappe.model.naming import getseries
from frappe.utils import cint


def execute():
	frappe.reload_doc("lms", "doctype", "lms_certificate_template")
	frappe.reload_doc("lms", "doctype", "lms_certificate")
	frappe.reload_doc("lms", "doctype", "lms_course")
	frappe.reload_doc("lms", "doctype", "lms_batch")
	frappe.reload_doc("lms", "doctype", "lms_settings")
	frappe.reload_doc("lms", "print_format", "certificate_template")

	from lms.lms.doctype.lms_certificate_template.lms_certificate_template import create_default_template

	create_default_template()
	backfill_serial_numbers()
	backfill_verification_tokens()
	remove_member_write_shares()


def backfill_serial_numbers():
	start = max(cint(frappe.db.get_single_value("LMS Settings", "certificate_serial_start")) - 1, 0)
	# New columns are NULL, so match with "is not set" rather than ["in", ["", None]].
	certificates = frappe.get_all(
		"LMS Certificate",
		filters={"serial_number": ["is", "not set"]},
		pluck="name",
		order_by="creation asc, name asc",
	)
	for name in certificates:
		serial = str(int(getseries("LMS-CERT-SERIAL-", 1)) + start)
		frappe.db.set_value("LMS Certificate", name, "serial_number", serial, update_modified=False)


def backfill_verification_tokens():
	certificates = frappe.get_all(
		"LMS Certificate",
		filters={"verification_token": ["is", "not set"]},
		pluck="name",
		order_by="creation asc, name asc",
	)
	for name in certificates:
		frappe.db.set_value(
			"LMS Certificate",
			name,
			"verification_token",
			secrets.token_urlsafe(16),
			update_modified=False,
		)


def remove_member_write_shares():
	frappe.db.set_value(
		"DocShare",
		{"share_doctype": "LMS Certificate", "write": 1},
		"write",
		0,
		update_modified=False,
	)
