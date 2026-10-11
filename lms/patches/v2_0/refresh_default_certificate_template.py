import hashlib
from pathlib import Path

import frappe

TEMPLATE = "FLI Default"

# sha256 of the stripped html / css of every revision of the stock template shipped so far.
# A template is only refreshed when both still match one of them, so edits are never lost.
SHIPPED_HTML = {
	"8c8c002371af",
	"cfb9605fc443",
	"b6a8f9f57877",
	"83663a69cf2f",
}
SHIPPED_CSS = {
	"bd9bf6ac8b8c",
	"38bcfbd66100",
	"ba1eaf766d08",
	"769d85b9d447",
}


def digest(text):
	text = (text or "").replace("\r\n", "\n").strip()
	return hashlib.sha256(text.encode()).hexdigest()[:12]


def execute():
	if not frappe.db.exists("LMS Certificate Template", TEMPLATE):
		return

	template = frappe.get_doc("LMS Certificate Template", TEMPLATE)
	if template.template_type != "HTML":
		return

	if digest(template.html) not in SHIPPED_HTML or digest(template.css) not in SHIPPED_CSS:
		return

	folder = Path(
		frappe.get_app_path("lms", "lms", "doctype", "lms_certificate_template", "default_template")
	)
	template.html = (folder / "default.html").read_text(encoding="utf-8")
	template.css = (folder / "default.css").read_text(encoding="utf-8")
	template.save(ignore_permissions=True)
