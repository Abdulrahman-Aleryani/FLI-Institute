from unittest.mock import patch

import frappe

try:
	from frappe.tests import IntegrationTestCase
except ImportError:  # Frappe v15
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from lms.lms.certificate_grades import (
	DEFAULT_GRADE_BANDS,
	collect_grades,
	get_grade_label,
	is_passing,
)


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


class TestIsPassing(IntegrationTestCase):
	def test_missing_grades_pass(self):
		self.assertTrue(is_passing(None))
		self.assertTrue(is_passing({}))

	def test_boundary(self):
		self.assertTrue(is_passing({"mark": 75}))
		self.assertTrue(is_passing({"mark": 75.0}))
		self.assertFalse(is_passing({"mark": 74.99}))
		self.assertFalse(is_passing({"mark": 0}))


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

		real_get_value = frappe.db.get_value
		record = frappe._dict(
			total=92,
			teacher_comments="Great",
			final_exam=25,
			unit_quiz_1=15,
			homework=10,
			attendance=10,
			class_participation=10,
			story_discussion=10,
			writing=10,
			oral_exam=2,
		)

		def get_value(doctype, filters, *args, **kwargs):
			if doctype != "Batch Grade Record":
				return real_get_value(doctype, filters, *args, **kwargs)
			if filters["parent"] == "S2":
				return None
			return record

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

	def test_stored_total_is_recomputed_from_components(self):
		# A stored ``total`` that drifted from the component marks must not leak
		# through: the earned total is summed again from the components.
		sheets = [frappe._dict(name="S1", term="3", instructor_name="T")]
		record = frappe._dict(total=100, attendance=10, writing=15)
		real_get_value = frappe.db.get_value

		def get_value(doctype, *args, **kwargs):
			if doctype == "Batch Grade Record":
				return record
			return real_get_value(doctype, *args, **kwargs)

		def get_all(doctype, **kwargs):
			return sheets if doctype == "Batch Grade Sheet" else []

		with patch("frappe.get_all", side_effect=get_all), patch("frappe.db.get_value", side_effect=get_value):
			grades = collect_grades(self.cert())

		self.assertEqual(grades["mark"], 25)
		self.assertFalse(is_passing(grades))

	def test_stored_total_used_when_components_empty(self):
		sheets = [frappe._dict(name="S1", term="3", instructor_name="T")]
		record = frappe._dict(total=80)

		def get_all(doctype, **kwargs):
			return sheets if doctype == "Batch Grade Sheet" else []

		with patch("frappe.get_all", side_effect=get_all), patch("frappe.db.get_value", return_value=record):
			grades = collect_grades(self.cert())

		self.assertEqual(grades["mark"], 80)
		self.assertTrue(is_passing(grades))
