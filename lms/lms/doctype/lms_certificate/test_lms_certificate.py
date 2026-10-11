# Copyright (c) 2021, FOSS United and Contributors
# See license.txt

import frappe

try:
	from frappe.tests import IntegrationTestCase
except ImportError:  # Frappe v15
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from lms.lms.doctype.lms_certificate.lms_certificate import (
	create_bulk_certificates,
	create_certificate,
	get_certificate_status,
	is_certified,
	revoke_certificate,
)


def make_certificate(member, **kwargs):
	doc = {
		"doctype": "LMS Certificate",
		"member": member,
		"template": "Certificate Template",
	}
	doc.update(kwargs)
	certificate = frappe.get_doc(doc)
	certificate.flags.ignore_eligibility = True
	return certificate.insert(ignore_permissions=True)


def get_course():
	course = frappe.get_all("LMS Course", pluck="name", limit=1)
	return course[0] if course else None


class TestLMSCertificate(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_repeat_create_certificate_returns_existing(self):
		course = get_course()
		if not course:
			self.skipTest("Needs a course")
		certificate = make_certificate("Administrator", course=course)
		self.assertEqual(is_certified(course), certificate.name)
		existing = create_certificate(course)
		self.assertEqual(existing.name, certificate.name)

	def test_student_cannot_insert_certificate(self):
		student = frappe.get_all("Has Role", {"role": "LMS Student", "parenttype": "User"}, pluck="parent")
		student = [user for user in student if user not in ("Administrator", "Guest")]
		if not student:
			self.skipTest("Needs an LMS Student user")
		frappe.set_user(student[0])
		doc = frappe.get_doc(
			{
				"doctype": "LMS Certificate",
				"member": student[0],
				"template": "Certificate",
			}
		)
		with self.assertRaises(frappe.PermissionError):
			doc.insert()

	def test_token_and_serial_are_generated_and_not_client_settable(self):
		first = make_certificate("Administrator", verification_token="client", serial_number="ZZ-CLIENT")
		second = make_certificate("Administrator")
		self.assertNotEqual(first.verification_token, "client")
		self.assertNotEqual(first.serial_number, "ZZ-CLIENT")
		self.assertGreaterEqual(len(first.verification_token), 16)
		self.assertNotEqual(first.verification_token, second.verification_token)
		self.assertNotEqual(first.serial_number, second.serial_number)
		self.assertEqual(int(second.serial_number), int(first.serial_number) + 1)

		first.serial_number = "tampered"
		first.verification_token = "tampered"
		first.save()
		first.reload()
		self.assertNotEqual(first.serial_number, "tampered")
		self.assertNotEqual(first.verification_token, "tampered")

	def test_revoked_are_not_certified(self):
		course = get_course()
		if not course:
			self.skipTest("Needs a course")
		certificate = make_certificate("Administrator", course=course)
		self.assertTrue(is_certified(course))

		revoke_certificate(certificate.name, "Issued by mistake")
		certificate.reload()
		self.assertEqual(certificate.revoked, 1)
		self.assertEqual(certificate.revocation_reason, "Issued by mistake")
		self.assertFalse(is_certified(course))
		with self.assertRaises(frappe.ValidationError):
			revoke_certificate(certificate.name, "again")

		reissued = make_certificate("Administrator", course=course)
		self.assertEqual(is_certified(course), reissued.name)
		self.assertEqual(get_certificate_status(1), "Revoked")
		self.assertEqual(get_certificate_status(0), "Valid")

	def test_revoke_requires_reason(self):
		certificate = make_certificate("Administrator")
		with self.assertRaises(frappe.ValidationError):
			revoke_certificate(certificate.name, "  ")

	def test_bulk_result_shape(self):
		batch = frappe.get_all("LMS Batch", pluck="name", limit=1)
		if not batch:
			self.skipTest("Needs a batch")
		result = create_bulk_certificates(batch[0])
		self.assertEqual(set(result), {"created", "skipped", "failed"})
		again = create_bulk_certificates(batch[0])
		self.assertEqual(again["created"], [])
		self.assertEqual(len(again["skipped"]), len(result["created"]) + len(result["skipped"]))
