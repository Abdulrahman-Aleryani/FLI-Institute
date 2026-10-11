from unittest.mock import patch

import frappe

try:
	from frappe.tests import IntegrationTestCase
except ImportError:  # Frappe v15
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from lms.lms.certificate_grades import DEFAULT_GRADE_BANDS, collect_grades, get_grade_label


class TestGradeLabel(IntegrationTestCase):
	def test_boundaries(self):
		self.assertEqual(get_grade_label(90, DEFAULT_GRADE_BANDS), "Excellent")
		self.assertEqual(get_grade_label(89.99, DEFAULT_GRADE_BANDS), "Very Good")
		self.assertEqual(get_grade_label(100, DEFAULT_GRADE_BANDS), "Excellent")
		self.assertEqual(get_grade_label(60, DEFAULT_GRADE_BANDS), "Pass")

	def test_below_all_bands_is_empty(self):
		self.assertEqual(get_grade_label(59.9, DEFAULT_GRADE_BANDS), "")

	def test_unordered_bands(self):
		bands = [(60, "Pass"), (90, "Excellent")]
		self.assertEqual(get_grade_label(95, bands), "Excellent")


class TestCollectGrades(IntegrationTestCase):
	def cert(self, batch="B-1", member="s@example.com"):
		return frappe._dict(batch_name=batch, member=member)

	def test_no_batch_returns_none(self):
		self.assertIsNone(collect_grades(self.cert(batch=None)))

	def test_no_sheet_returns_none(self):
		with patch("frappe.get_all", return_value=[]):
			self.assertIsNone(collect_grades(self.cert()))

	def test_student_missing_from_sheet_returns_none(self):
		sheets = [frappe._dict(name="S1", term="3", instructor_name="T")]
		with patch("frappe.get_all", return_value=sheets), patch("frappe.db.get_value", return_value=None):
			self.assertIsNone(collect_grades(self.cert()))

	def test_latest_sheet_with_student_wins(self):
		sheets = [
			frappe._dict(name="S2", term="4", instructor_name="Second"),
			frappe._dict(name="S1", term="3", instructor_name="First"),
		]

		def get_value(doctype, filters, fields, as_dict=False):
			if filters["parent"] == "S2":
				return None
			return frappe._dict(total=92, teacher_comments="Great")

		def get_all(doctype, **kwargs):
			if doctype == "Batch Grade Sheet":
				return sheets
			return []

		with patch("frappe.get_all", side_effect=get_all), patch("frappe.db.get_value", side_effect=get_value):
			grades = collect_grades(self.cert())
		self.assertEqual(grades["mark"], 92)
		self.assertEqual(grades["grade_label"], "Excellent")
		self.assertEqual(grades["term"], "3")
		self.assertEqual(grades["teacher_name"], "First")
		self.assertEqual(grades["teacher_comments"], "Great")

	def test_sheet_query_only_submitted(self):
		with patch("frappe.get_all", return_value=[]) as get_all:
			collect_grades(self.cert())
		self.assertEqual(get_all.call_args.kwargs["filters"]["docstatus"], 1)

	def test_comments_entities_are_unescaped(self):
		sheets = [frappe._dict(name="S1", term="3", instructor_name="T")]
		record = frappe._dict(total=70, teacher_comments="Fast &amp; keen")

		def get_all(doctype, **kwargs):
			return sheets if doctype == "Batch Grade Sheet" else []

		with patch("frappe.get_all", side_effect=get_all), patch("frappe.db.get_value", return_value=record):
			self.assertEqual(collect_grades(self.cert())["teacher_comments"], "Fast & keen")
