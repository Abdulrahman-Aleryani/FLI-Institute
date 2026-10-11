# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import secrets

import frappe
from frappe import _
from frappe.email.doctype.email_template.email_template import get_email_template
from frappe.model.document import Document
from frappe.model.naming import getseries, make_autoname
from frappe.utils import cint

CERTIFICATE_PRINT_FORMAT = "Certificate Template"
PRIVILEGED_ROLES = ("System Manager", "Moderator")
ELIGIBILITY_EXEMPT_ROLES = PRIVILEGED_ROLES + ("Batch Evaluator",)


class LMSCertificate(Document):
	def before_insert(self):
		# Never trust client supplied values for these.
		self.verification_token = secrets.token_urlsafe(16)
		self.serial_number = next_serial_number()
		self.revoked = 0
		self.revoked_on = None
		self.revocation_reason = None
		self.set_certificate_template()

	def set_certificate_template(self):
		if not self.certificate_template and (not self.template or self.template == CERTIFICATE_PRINT_FORMAT):
			self.certificate_template = resolve_certificate_template(self.course, self.batch_name)

		if self.certificate_template:
			self.template = CERTIFICATE_PRINT_FORMAT
		elif not self.template:
			self.template = get_default_certificate_template()

	def validate(self):
		self.protect_immutable_fields()
		self.validate_duplicate_certificate()
		self.validate_eligibility()

	def protect_immutable_fields(self):
		if self.is_new():
			return
		stored = frappe.db.get_value(
			self.doctype, self.name, ["serial_number", "verification_token"], as_dict=True
		)
		if stored:
			self.serial_number = stored.serial_number
			self.verification_token = stored.verification_token

	def validate_eligibility(self):
		if not self.is_new() or self.flags.ignore_eligibility:
			return
		if set(frappe.get_roles()) & set(ELIGIBILITY_EXEMPT_ROLES):
			return
		if self.member != frappe.session.user or not self.course:
			raise frappe.PermissionError
		validate_certification_eligibility(self.course)

	def autoname(self):
		self.name = make_autoname("hash", self.doctype)

	def after_insert(self):
		outgoing_email_account = frappe.get_cached_value(
			"Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"
		)
		if outgoing_email_account or frappe.conf.get("mail_login"):
			self.send_mail()

	def send_mail(self):
		subject = _("Congratulations on getting certified!")
		template = "certification"
		custom_template = frappe.db.get_single_value("LMS Settings", "certification_template")

		args = {
			"student_name": self.member_name,
			"course_name": self.course,
			"course_title": frappe.db.get_value("LMS Course", self.course, "title"),
			"certificate_name": self.name,
			"template": self.template,
		}

		if custom_template:
			email_template = get_email_template(custom_template, args)
			subject = email_template.get("subject")
			content = email_template.get("message")
		frappe.sendmail(
			recipients=self.member,
			subject=subject,
			template=template if not custom_template else None,
			content=content if custom_template else None,
			args=args,
			header=[subject, "green"],
		)

	def validate_duplicate_certificate(self):
		self.validate_course_duplicates()
		self.validate_batch_duplicates()

	def validate_course_duplicates(self):
		if self.course:
			course_duplicates = frappe.get_all(
				"LMS Certificate",
				filters={
					"member": self.member,
					"name": ["!=", self.name],
					"course": self.course,
					"revoked": 0,
				},
				fields=["name", "course", "course_title"],
			)
			if len(course_duplicates):
				full_name = frappe.db.get_value("User", self.member, "full_name")
				frappe.throw(
					_("{0} is already certified for the course {1}").format(
						full_name, course_duplicates[0].course_title
					)
				)

	def validate_batch_duplicates(self):
		if self.batch_name:
			batch_duplicates = frappe.get_all(
				"LMS Certificate",
				filters={
					"member": self.member,
					"name": ["!=", self.name],
					"batch_name": self.batch_name,
					"revoked": 0,
				},
				fields=["name", "batch_name", "batch_title"],
			)
			if len(batch_duplicates):
				full_name = frappe.db.get_value("User", self.member, "full_name")
				frappe.throw(
					_("{0} is already certified for the batch {1}").format(
						full_name, batch_duplicates[0].batch_title
					)
				)

	def on_update(self):
		frappe.share.add_docshare(
			self.doctype,
			self.name,
			self.member,
			write=0,
			share=1,
			flags={"ignore_share_permission": True},
		)


def has_website_permission(doc, ptype, user, verbose=False):
	return ptype in ["read", "print"]


def next_serial_number():
	start = cint(frappe.db.get_single_value("LMS Settings", "certificate_serial_start"))
	return str(int(getseries("LMS-CERT-SERIAL-", 1)) + max(start - 1, 0))


def active_certificate_condition(Certificate):
	return Certificate.revoked == 0


def get_certificate_status(revoked):
	return "Revoked" if revoked else "Valid"


def is_certified(course):
	certificate = frappe.get_all(
		"LMS Certificate", filters={"member": frappe.session.user, "course": course, "revoked": 0}
	)
	if len(certificate):
		return certificate[0].name
	return


@frappe.whitelist()
def create_certificate(course):
	existing = is_certified(course)
	if existing:
		return frappe.db.get_value("LMS Certificate", existing, ["name", "course", "template"], as_dict=True)

	validate_certification_eligibility(course)
	certificate = frappe.get_doc(
		{
			"doctype": "LMS Certificate",
			"member": frappe.session.user,
			"course": course,
		}
	)
	certificate.flags.ignore_eligibility = True
	certificate.insert(ignore_permissions=True)
	return certificate


def resolve_certificate_template(course=None, batch=None):
	"""Batch template, then course template, then the LMS Settings default. Disabled ones are skipped."""
	candidates = []
	if batch:
		candidates.append(frappe.db.get_value("LMS Batch", batch, "certificate_template"))
	if course:
		candidates.append(frappe.db.get_value("LMS Course", course, "certificate_template"))
	candidates.append(frappe.db.get_single_value("LMS Settings", "default_certificate_template"))

	for candidate in candidates:
		if candidate and frappe.db.get_value("LMS Certificate Template", candidate, "enabled"):
			return candidate
	return None


@frappe.whitelist()
def get_resolved_certificate_template(course=None, batch=None):
	frappe.only_for(PRIVILEGED_ROLES + ("Batch Evaluator",))
	return resolve_certificate_template(course, batch)


def get_default_certificate_template(course=None, batch=None):
	if resolve_certificate_template(course, batch):
		return CERTIFICATE_PRINT_FORMAT

	default_certificate_template = frappe.db.get_value(
		"Property Setter",
		{
			"doc_type": "LMS Certificate",
			"property": "default_print_format",
		},
		"value",
	)
	if not default_certificate_template:
		default_certificate_template = frappe.db.get_value(
			"Print Format",
			{
				"doc_type": "LMS Certificate",
			},
		)

	return default_certificate_template


def validate_certification_eligibility(course):
	if not frappe.db.exists("LMS Enrollment", {"course": course, "member": frappe.session.user}):
		frappe.throw(_("You are not enrolled in this course."))

	if not frappe.db.get_value("LMS Course", course, "enable_certification"):
		frappe.throw(_("Certification is not enabled for this course."))

	progress = frappe.db.get_value(
		"LMS Enrollment", {"course": course, "member": frappe.session.user}, "progress"
	)
	if (progress or 0) < 100:
		frappe.throw(_("You have not completed the course yet."))


@frappe.whitelist()
def revoke_certificate(name, reason):
	frappe.only_for(PRIVILEGED_ROLES)
	reason = (reason or "").strip()
	if not reason:
		frappe.throw(_("A reason is required to revoke a certificate."))

	certificate = frappe.db.get_value("LMS Certificate", name, ["name", "revoked"], as_dict=True)
	if not certificate:
		frappe.throw(_("Certificate {0} does not exist.").format(name))
	if certificate.revoked:
		frappe.throw(_("Certificate {0} is already revoked.").format(name))

	frappe.db.set_value(
		"LMS Certificate",
		name,
		{"revoked": 1, "revoked_on": frappe.utils.now_datetime(), "revocation_reason": reason},
	)
	frappe.get_doc("LMS Certificate", name).add_comment("Info", _("Certificate revoked: {0}").format(reason))
	return {"name": name, "revoked": 1}


@frappe.whitelist()
def create_bulk_certificates(batch, template=None, published=1, course=None):
	frappe.only_for(PRIVILEGED_ROLES)
	if not frappe.db.exists("LMS Batch", batch):
		frappe.throw(_("Batch {0} does not exist.").format(batch))
	if template and not frappe.db.exists("LMS Certificate Template", template):
		frappe.throw(_("Certificate template {0} does not exist.").format(template))

	members = []
	for member in frappe.get_all(
		"LMS Batch Enrollment",
		{"batch": batch},
		pluck="member",
		order_by="creation asc",
	):
		if member not in members:
			members.append(member)

	course_filters = {"parent": batch}
	if course:
		course_filters["course"] = course
	batch_course = (
		frappe.db.get_value(
			"Batch Course", course_filters, ["course", "evaluator"], as_dict=True, order_by="idx asc"
		)
		or frappe._dict()
	)

	created, skipped, failed = [], [], []
	for member in members:
		duplicate_filters = [{"member": member, "batch_name": batch, "revoked": 0}]
		if batch_course.get("course"):
			duplicate_filters.append({"member": member, "course": batch_course.get("course"), "revoked": 0})
		if any(frappe.db.exists("LMS Certificate", filters) for filters in duplicate_filters):
			skipped.append({"member": member, "reason": _("Already certified")})
			continue

		savepoint = "bulk_certificate"
		frappe.db.savepoint(savepoint)
		try:
			certificate = frappe.get_doc(
				{
					"doctype": "LMS Certificate",
					"member": member,
					"batch_name": batch,
					"course": batch_course.get("course"),
					"evaluator": batch_course.get("evaluator"),
					"certificate_template": template,
					"published": cint(published),
				}
			)
			certificate.flags.ignore_eligibility = True
			certificate.insert(ignore_permissions=True)
			created.append(certificate.name)
		except Exception as e:
			frappe.db.rollback(save_point=savepoint)
			failed.append({"member": member, "error": str(e)})

	return {"created": created, "skipped": skipped, "failed": failed}
