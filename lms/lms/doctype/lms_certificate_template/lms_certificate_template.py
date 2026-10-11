# Copyright (c) 2026, FOSS United and contributors
# For license information, please see license.txt

import json
import re
from pathlib import Path

import frappe
from frappe import _
from frappe.model.document import Document

from lms.lms.certificate_renderer import (
	FONT_STACKS,
	LAYOUT_FIELDS,
	MAX_LAYOUT_ELEMENTS,
	get_sample_context,
	render_html_template,
)

DEFAULT_TEMPLATE_NAME = "FLI Default"
HEX_COLOR = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
ALIGNMENTS = ("left", "center", "right")


class LMSCertificateTemplate(Document):
	def validate(self):
		if self.template_type == "Image":
			if not self.background_image:
				frappe.throw(_("Background image is required for an image template."))
			self.layout_json = json.dumps(validate_layout(self.layout_json or "[]"))
		else:
			if not (self.html or "").strip():
				frappe.throw(_("HTML is required for an HTML template."))
			# Rendering with sample data surfaces syntax errors and forbidden constructs on save.
			render_html_template(self.html, get_sample_context(self))


def _number(value, label, minimum, maximum, exclusive_min=False):
	if isinstance(value, bool) or not isinstance(value, int | float):
		frappe.throw(_("{0} must be a number.").format(label))
	too_low = value <= minimum if exclusive_min else value < minimum
	if too_low or value > maximum:
		frappe.throw(_("{0} must be between {1} and {2}.").format(label, minimum, maximum))
	return value


def validate_layout(layout_json):
	if isinstance(layout_json, str):
		try:
			layout = json.loads(layout_json) if layout_json.strip() else []
		except ValueError:
			frappe.throw(_("The layout is not valid JSON."))
	else:
		layout = layout_json or []

	if not isinstance(layout, list):
		frappe.throw(_("The layout must be a list."))
	if len(layout) > MAX_LAYOUT_ELEMENTS:
		frappe.throw(_("The layout can have at most {0} elements.").format(MAX_LAYOUT_ELEMENTS))

	cleaned = []
	for index, element in enumerate(layout, start=1):
		prefix = _("Layout element {0}").format(index)
		if not isinstance(element, dict):
			frappe.throw(_("{0} must be an object.").format(prefix))
		field = element.get("field")
		if field not in LAYOUT_FIELDS:
			frappe.throw(_("{0} has an unknown field.").format(prefix))

		item = {
			"field": field,
			"x": _number(element.get("x"), f"{prefix}: x", 0, 100),
			"y": _number(element.get("y"), f"{prefix}: y", 0, 100),
			"width": _number(element.get("width", 30), f"{prefix}: width", 0, 100, exclusive_min=True),
		}

		if element.get("font_size") not in (None, ""):
			item["font_size"] = _number(
				element["font_size"], f"{prefix}: font size", 0, 30, exclusive_min=True
			)

		font_family = element.get("font_family") or ""
		if font_family and font_family not in FONT_STACKS:
			frappe.throw(_("{0} has an unknown font.").format(prefix))
		item["font_family"] = font_family

		color = element.get("color") or ""
		if color and not (isinstance(color, str) and HEX_COLOR.match(color)):
			frappe.throw(_("{0} has an invalid color. Use a hex value such as #1E4FA3.").format(prefix))
		item["color"] = color

		align = element.get("align") or "left"
		if align not in ALIGNMENTS:
			frappe.throw(_("{0} has an invalid alignment.").format(prefix))
		item["align"] = align
		item["bold"] = bool(element.get("bold"))
		item["italic"] = bool(element.get("italic"))
		cleaned.append(item)

	return cleaned


def create_default_template():
	"""Create the stock FLI template and make it the default. Safe to run repeatedly."""
	if not frappe.db.exists("LMS Certificate Template", DEFAULT_TEMPLATE_NAME):
		folder = Path(__file__).parent / "default_template"
		frappe.get_doc(
			{
				"doctype": "LMS Certificate Template",
				"template_name": DEFAULT_TEMPLATE_NAME,
				"template_type": "HTML",
				"enabled": 1,
				"page_size": "A4",
				"orientation": "Landscape",
				"html": (folder / "default.html").read_text(encoding="utf-8"),
				"css": (folder / "default.css").read_text(encoding="utf-8"),
			}
		).insert(ignore_permissions=True)

	if not frappe.db.get_single_value("LMS Settings", "default_certificate_template"):
		frappe.db.set_single_value("LMS Settings", "default_certificate_template", DEFAULT_TEMPLATE_NAME)

	return DEFAULT_TEMPLATE_NAME
