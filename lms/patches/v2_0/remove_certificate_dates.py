import json

import frappe

from lms.patches.v2_0.refresh_default_certificate_template import execute as refresh_default_template

DATE_FIELDS = ("issue_date", "expiry_date")


def execute():
	frappe.reload_doc("lms", "doctype", "lms_certificate")
	refresh_default_template()
	remove_dates_from_image_layouts()


def remove_dates_from_image_layouts():
	for name, layout_json in frappe.get_all(
		"LMS Certificate Template",
		filters={"layout_json": ["is", "set"]},
		fields=["name", "layout_json"],
		as_list=True,
	):
		try:
			layout = json.loads(layout_json)
		except ValueError:
			continue
		if not isinstance(layout, list):
			continue

		kept = [item for item in layout if not (isinstance(item, dict) and item.get("field") in DATE_FIELDS)]
		if len(kept) != len(layout):
			frappe.db.set_value(
				"LMS Certificate Template", name, "layout_json", json.dumps(kept), update_modified=False
			)
