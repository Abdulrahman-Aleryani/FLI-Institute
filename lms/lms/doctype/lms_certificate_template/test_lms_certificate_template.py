# Copyright (c) 2026, FOSS United and contributors
# See license.txt

import json

import frappe

try:
	from frappe.tests import IntegrationTestCase
except ImportError:  # Frappe v15
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from lms.lms.certificate_renderer import (
	SAMPLE_GRADES,
	_sample_parts,
	build_context,
	render_html_template,
	render_template_html,
	sanitize_css,
)
from lms.lms.doctype.lms_certificate.lms_certificate import resolve_certificate_template
from lms.lms.doctype.lms_certificate_template.lms_certificate_template import validate_layout


def make_template(name, **kwargs):
	if frappe.db.exists("LMS Certificate Template", name):
		frappe.delete_doc("LMS Certificate Template", name, force=True)
	doc = {
		"doctype": "LMS Certificate Template",
		"template_name": name,
		"template_type": "HTML",
		"html": "<div>{{ student_name }}</div>",
	}
	doc.update(kwargs)
	return frappe.get_doc(doc).insert(ignore_permissions=True)


class TestLMSCertificateTemplate(IntegrationTestCase):
	def test_placeholders_are_rendered_and_escaped(self):
		context = build_context({"student_name": "<b>Ali</b>", "serial_number": "120539"}, {})
		html = render_html_template("{{ student_name }} #{{ serial_number }}", context)
		self.assertIn("&lt;b&gt;Ali&lt;/b&gt;", html)
		self.assertIn("#120539", html)

	def test_image_placeholder_is_markup(self):
		context = build_context({}, {"logo": "data:image/png;base64,AAAA"})
		html = render_html_template("{{ logo }}", context)
		self.assertIn('<img src="data:image/png;base64,AAAA" class="cert-logo"', html)

	def test_sandbox_hides_frappe_and_doc(self):
		context = build_context({}, {})
		self.assertEqual(render_html_template("[{{ frappe }}][{{ doc }}]", context), "[][]")

	def test_sandbox_rejects_escapes(self):
		context = build_context({}, {})
		for source in (
			"{{ ''.__class__.__mro__ }}",
			"{{ ''.__class__.__mro__[1].__subclasses__() }}",
			"{{ 'a' * 10 ** 8 }}",
			"{{ 2 ** 999 }}",
			"{% include 'x' %}",
		):
			with self.assertRaises(frappe.ValidationError, msg=source):
				render_html_template(source, context)

	def test_scripts_are_stripped(self):
		html = render_html_template("<script>alert(1)</script>ok", build_context({}, {}))
		self.assertNotIn("<script", html)

	def test_sanitize_css(self):
		css = sanitize_css("@import url(x.css);</style><script>a</script>body{color:red}<!-- -->")
		self.assertNotIn("@import", css)
		self.assertNotIn("<", css)
		self.assertIn("body{color:red}", css)

	def test_validate_layout_accepts_and_normalises(self):
		layout = validate_layout(json.dumps([{"field": "student_name", "x": 10, "y": 20, "bold": 1}]))
		self.assertEqual(layout[0]["width"], 30)
		self.assertEqual(layout[0]["align"], "left")
		self.assertIs(layout[0]["bold"], True)

	def test_validate_layout_rejections(self):
		bad_layouts = [
			"not json",
			{"field": "student_name"},
			[{"field": "unknown", "x": 1, "y": 1}],
			[{"field": "student_name", "x": 101, "y": 1}],
			[{"field": "student_name", "x": True, "y": 1}],
			[{"field": "student_name", "x": 1, "y": 1, "width": 0}],
			[{"field": "student_name", "x": 1, "y": 1, "font_size": 31}],
			[{"field": "student_name", "x": 1, "y": 1, "font_family": "Comic Sans"}],
			[{"field": "student_name", "x": 1, "y": 1, "color": "red"}],
			[{"field": "student_name", "x": 1, "y": 1, "align": "justify"}],
			[{"field": "student_name", "x": 1, "y": 1}] * 61,
		]
		for layout in bad_layouts:
			with self.assertRaises(frappe.ValidationError, msg=str(layout)[:60]):
				validate_layout(layout)

	def test_image_template_requires_background(self):
		with self.assertRaises(frappe.ValidationError):
			make_template("Test Image Template", template_type="Image", html=None)

	def test_invalid_html_fails_on_save(self):
		with self.assertRaises(frappe.ValidationError):
			make_template("Test Bad Template", html="{{ ''.__class__.__mro__ }}")

	def test_resolution_order_and_disabled(self):
		batch_template = make_template("Test Batch Template")
		course_template = make_template("Test Course Template")
		default_template = make_template("Test Default Template")
		frappe.db.set_single_value("LMS Settings", "default_certificate_template", default_template.name)

		course = frappe.get_all("LMS Course", pluck="name", limit=1)
		batch = frappe.get_all("LMS Batch", pluck="name", limit=1)
		if not (course and batch):
			self.skipTest("Needs a course and a batch")
		course, batch = course[0], batch[0]

		frappe.db.set_value("LMS Course", course, "certificate_template", course_template.name)
		frappe.db.set_value("LMS Batch", batch, "certificate_template", batch_template.name)
		self.assertEqual(resolve_certificate_template(course, batch), batch_template.name)
		self.assertEqual(resolve_certificate_template(course), course_template.name)

		frappe.db.set_value("LMS Certificate Template", batch_template.name, "enabled", 0)
		self.assertEqual(resolve_certificate_template(course, batch), course_template.name)
		frappe.db.set_value("LMS Certificate Template", course_template.name, "enabled", 0)
		self.assertEqual(resolve_certificate_template(course, batch), default_template.name)

	def test_arabic_values_are_flagged(self):
		context = build_context({"student_name": "محمد الأحمد", "course_title": "English"}, {})
		self.assertTrue(context["student_name_is_arabic"])
		self.assertFalse(context["course_title_is_arabic"])
		self.assertFalse(context["batch_title_is_arabic"])

	def test_qr_png_is_a_valid_png_without_pypng(self):
		import struct
		import zlib

		from lms.lms.certificate_renderer import _png_from_matrix

		matrix = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
		png = _png_from_matrix(matrix, scale=4, quiet_zone=1)
		self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
		width, height = struct.unpack(">II", png[16:24])
		self.assertEqual((width, height), (20, 20))
		data = png[png.index(b"IDAT") + 4 : png.index(b"IEND") - 8]
		self.assertEqual(len(zlib.decompress(data)), 20 * (1 + 3))


class TestGradesPage(IntegrationTestCase):
	def template(self, include):
		return frappe.get_doc(
			{
				"doctype": "LMS Certificate Template",
				"template_name": "Grades Page Test",
				"template_type": "HTML",
				"html": "<div>{{ student_name }}</div>",
				"include_grades_page": include,
			}
		)

	def test_no_page_when_disabled(self):
		template = self.template(0)
		html = render_template_html(template, _sample_parts(template), SAMPLE_GRADES)
		self.assertNotIn("grades-page", html)

	def test_no_page_without_grades(self):
		template = self.template(1)
		html = render_template_html(template, _sample_parts(template), None)
		self.assertNotIn("grades-page", html)

	def test_page_rendered_and_escaped(self):
		template = self.template(1)
		grades = dict(SAMPLE_GRADES, teacher_comments="<script>x</script> مرحبا")
		html = render_template_html(template, _sample_parts(template), grades)
		self.assertEqual(html.count('class="cert-page'), 2)
		self.assertIn("page-break-before: always", html)
		self.assertIn("&lt;script&gt;x&lt;/script&gt; مرحبا", html)
		self.assertNotIn("<script>x", html)
		self.assertIn("Excellent", html)

	def test_image_template_also_gets_page(self):
		template = self.template(1)
		template.template_type = "Image"
		template.layout_json = "[]"
		html = render_template_html(template, _sample_parts(template), SAMPLE_GRADES)
		self.assertEqual(html.count('class="cert-page'), 2)
