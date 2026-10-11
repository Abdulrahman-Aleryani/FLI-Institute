import base64
import io
import json
import mimetypes
import re
import struct
import zlib
from html import escape

import frappe
from frappe import _
from frappe.utils import format_date, get_url
from jinja2 import ChainableUndefined, TemplateError
from jinja2.exceptions import SecurityError
from jinja2.sandbox import ImmutableSandboxedEnvironment
from markupsafe import Markup

# Landscape sizes in mm (width, height). Swapped for Portrait.
PAGE_SIZES = {"A4": (297, 210), "Letter": (279.4, 215.9)}
DATE_FORMAT = "dd MMM yyyy"
MAX_INLINE_FILE_SIZE = 8 * 1024 * 1024
MAX_LAYOUT_ELEMENTS = 60
LONG_NAME_LENGTH = 28
ARABIC_RE = re.compile("[\u0600-\u06ff\u0750-\u077f\ufb50-\ufdff\ufe70-\ufeff]")

TEXT_KEYS = (
	"student_name",
	"course_title",
	"batch_title",
	"start_date",
	"end_date",
	"serial_number",
	"certificate_id",
	"verification_url",
	"logo_url",
	"signer_1_name",
	"signer_1_title",
	"signer_2_name",
	"signer_2_title",
	"evaluator_name",
	"institute_name",
)
IMAGE_KEYS = ("qr_code", "logo", "signature_1", "signature_2")
LAYOUT_FIELDS = tuple(key for key in TEXT_KEYS if key != "logo_url") + IMAGE_KEYS

ARABIC_FALLBACK = '"Noto Naskh Arabic", "Amiri", serif'
FONT_STACKS = {
	"EB Garamond": '"EB Garamond", "Noto Naskh Arabic", Georgia, "Times New Roman", "Amiri", serif',
	"Noto Naskh Arabic": ARABIC_FALLBACK,
	"Georgia": f'Georgia, "Times New Roman", {ARABIC_FALLBACK}',
	"Helvetica": f'"Helvetica Neue", Helvetica, Arial, {ARABIC_FALLBACK}',
}
DEFAULT_FONT = "EB Garamond"

# (family, weight, style, file)
FONT_FILES = (
	("EB Garamond", 400, "normal", "EBGaramond-Regular.ttf"),
	("EB Garamond", 600, "normal", "EBGaramond-SemiBold.ttf"),
	("EB Garamond", 400, "italic", "EBGaramond-Italic.ttf"),
	("Noto Naskh Arabic", 400, "normal", "NotoNaskhArabic-Regular.ttf"),
	("Noto Naskh Arabic", 700, "normal", "NotoNaskhArabic-Bold.ttf"),
)

HEX_COLOR = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
SCRIPT_TAG = re.compile(r"</?\s*script\b[^>]*>", re.IGNORECASE)
CSS_IMPORT = re.compile(r"@import\b[^;]*;?", re.IGNORECASE)
CSS_STYLE_TAG = re.compile(r"</?\s*style", re.IGNORECASE)


class CertificateSandbox(ImmutableSandboxedEnvironment):
	# Operators that can build huge objects out of small input.
	intercepted_binops = frozenset(["**", "*"])

	def unsafe_undefined(self, obj, attribute):
		# Fail loudly instead of rendering an empty value for private attributes.
		raise SecurityError(f"access to attribute {attribute!r} is not allowed")

	def call_binop(self, context, operator, left, right):
		if operator == "**" or isinstance(left, str | bytes) or isinstance(right, str | bytes):
			raise SecurityError(f"operator {operator} is not allowed")
		return super().call_binop(context, operator, left, right)


def _safe_translate(message):
	return _(str(message))


def get_sandbox():
	env = CertificateSandbox(autoescape=True, undefined=ChainableUndefined, loader=None)
	env.globals.clear()
	env.globals["_"] = _safe_translate
	return env


def render_html_template(html, context):
	html = SCRIPT_TAG.sub("", html or "")
	try:
		return get_sandbox().from_string(html).render(**context)
	except SecurityError:
		frappe.throw(_("The certificate template uses something that is not allowed."))
	except TemplateError as e:
		frappe.throw(_("The certificate template is invalid: {0}").format(escape(str(e))))
	except Exception as e:
		frappe.throw(_("The certificate template is invalid: {0}").format(escape(str(e))))


def sanitize_css(css):
	css = css or ""
	css = SCRIPT_TAG.sub("", css)
	css = CSS_STYLE_TAG.sub("", css)
	css = css.replace("<!--", "").replace("-->", "")
	return CSS_IMPORT.sub("", css)


def _fmt_date(value):
	if not value:
		return ""
	return format_date(value, DATE_FORMAT)


def _file_to_url(url):
	if not url:
		return ""
	if url.startswith("data:image/") or url.startswith(("http://", "https://")):
		return url
	if url.startswith(("/files/", "/private/files/")):
		try:
			file_name = frappe.db.get_value("File", {"file_url": url}, "name")
			if file_name:
				file_doc = frappe.get_doc("File", file_name)
				if file_doc.file_size and file_doc.file_size > MAX_INLINE_FILE_SIZE:
					raise ValueError("File is too large to inline")
				content = file_doc.get_content()
				if isinstance(content, str):
					content = content.encode()
				if len(content) > MAX_INLINE_FILE_SIZE:
					raise ValueError("File is too large to inline")
				mime = mimetypes.guess_type(url)[0] or "image/png"
				return f"data:{mime};base64,{base64.b64encode(content).decode()}"
		except Exception:
			frappe.log_error(title="Certificate image could not be inlined")
	return get_url(url)


def _png_from_matrix(matrix, scale=8, quiet_zone=1):
	"""Encode a QR module matrix as a 1-bit PNG. No imaging library needed."""
	size = (len(matrix) + 2 * quiet_zone) * scale
	row_modules = [0] * quiet_zone
	rows = []
	blank = bytes([255] * ((size + 7) // 8))
	for _i in range(quiet_zone * scale):
		rows.append(b"\x00" + blank)
	for line in matrix:
		modules = row_modules + [int(v) for v in line] + row_modules
		bits = []
		for module in modules:
			bits.extend([0 if module else 1] * scale)
		bits.extend([1] * (-len(bits) % 8))
		packed = bytes(int("".join(map(str, bits[i : i + 8])), 2) for i in range(0, len(bits), 8))
		rows.extend([b"\x00" + packed] * scale)
	for _i in range(quiet_zone * scale):
		rows.append(b"\x00" + blank)

	def chunk(kind, data):
		body = kind + data
		return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

	header = struct.pack(">IIBBBBB", size, size, 1, 0, 0, 0, 0)
	return (
		b"\x89PNG\r\n\x1a\n"
		+ chunk(b"IHDR", header)
		+ chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
		+ chunk(b"IEND", b"")
	)


def _qr_data_uri(text):
	try:
		import pyqrcode

		matrix = pyqrcode.create(text, error="M").code
		return "data:image/png;base64," + base64.b64encode(_png_from_matrix(matrix)).decode()
	except Exception:
		frappe.log_error(title="Certificate QR code could not be generated")
		return ""


def _image_markup(url, css_class, alt):
	if not url:
		return Markup("")
	return Markup('<img src="{}" class="{}" alt="{}">').format(url, css_class, alt)


def build_context(values, images):
	context = {key: str(values.get(key) or "") for key in TEXT_KEYS}
	# wkhtmltopdf cannot fall back between web fonts per glyph, so templates need to know
	# when a value is Arabic to switch its font family (`{{ student_name_is_arabic }}`)
	for key in TEXT_KEYS:
		context[f"{key}_is_arabic"] = bool(ARABIC_RE.search(context[key]))
	context["logo_url"] = images.get("logo") or ""
	context["qr_code"] = _image_markup(images.get("qr_code"), "cert-qr", "QR code")
	context["logo"] = _image_markup(images.get("logo"), "cert-logo", "Logo")
	context["signature_1"] = _image_markup(images.get("signature_1"), "cert-signature", "Signature")
	context["signature_2"] = _image_markup(images.get("signature_2"), "cert-signature", "Signature")
	return context


def get_logo_url():
	logo = frappe.db.get_single_value("Website Settings", "app_logo") or frappe.db.get_single_value(
		"Website Settings", "banner_image"
	)
	return _file_to_url(logo or "/assets/lms/images/lms-logo.png")


def _collect(cert, template):
	batch = {}
	if cert.batch_name:
		batch = (
			frappe.db.get_value(
				"LMS Batch", cert.batch_name, ["title", "start_date", "end_date"], as_dict=True
			)
			or {}
		)

	course_title = cert.course_title
	if not course_title and cert.course:
		course_title = frappe.db.get_value("LMS Course", cert.course, "title")

	student = cert.member_name or frappe.db.get_value("User", cert.member, "full_name")
	verification_url = get_url(f"/verify/{cert.verification_token}") if cert.verification_token else ""

	values = {
		"student_name": student,
		"course_title": course_title,
		"batch_title": batch.get("title") or cert.batch_title,
		"start_date": _fmt_date(batch.get("start_date")),
		"end_date": _fmt_date(batch.get("end_date")),
		"serial_number": cert.serial_number,
		"certificate_id": cert.name,
		"verification_url": verification_url,
		"signer_1_name": template.signer_1_name,
		"signer_1_title": template.signer_1_title,
		"signer_2_name": template.signer_2_name,
		"signer_2_title": template.signer_2_title,
		"evaluator_name": cert.evaluator_name,
		"institute_name": frappe.db.get_single_value("Website Settings", "app_name"),
	}
	images = {
		"logo": get_logo_url(),
		"qr_code": _qr_data_uri(verification_url) if verification_url else "",
		"signature_1": _file_to_url(template.signer_1_signature),
		"signature_2": _file_to_url(template.signer_2_signature),
	}
	return values, images


def get_certificate_context(cert, template=None):
	template = template or frappe.get_doc("LMS Certificate Template", cert.certificate_template)
	values, images = _collect(cert, template)
	return build_context(values, images)


def _sample_parts(template=None):
	values = {
		"student_name": "Afnan Khaled Mohammed Ali Al-Ashwal",
		"course_title": "English for Communication, Level 6A",
		"batch_title": "Batch 24 - Evening",
		"start_date": "05 Jan 2026",
		"end_date": "30 Mar 2026",
		"serial_number": "120539",
		"certificate_id": "SAMPLE-CERTIFICATE",
		"verification_url": "https://example.com/verify/sample-verification-token",
		"signer_1_name": "Signer One",
		"signer_1_title": "Director",
		"signer_2_name": "Signer Two",
		"signer_2_title": "Academic Manager",
		"evaluator_name": "Sample Evaluator",
		"institute_name": frappe.db.get_single_value("Website Settings", "app_name") or "",
	}
	images = {
		"logo": get_logo_url(),
		"qr_code": _qr_data_uri(values["verification_url"]),
		"signature_1": "",
		"signature_2": "",
	}
	if template:
		for index in (1, 2):
			if template.get(f"signer_{index}_name"):
				values[f"signer_{index}_name"] = template.get(f"signer_{index}_name")
				values[f"signer_{index}_title"] = template.get(f"signer_{index}_title") or ""
			images[f"signature_{index}"] = _file_to_url(template.get(f"signer_{index}_signature"))
	return build_context(values, images), values, images


def get_sample_context(template=None):
	return _sample_parts(template)[0]


def _page_dimensions(template):
	width, height = PAGE_SIZES.get(template.page_size or "A4", PAGE_SIZES["A4"])
	if template.orientation == "Portrait":
		width, height = height, width
	return width, height


def _font_face_css():
	rules = []
	for family, weight, style, file in FONT_FILES:
		url = get_url(f"/assets/lms/fonts/{file}")
		rules.append(
			f'@font-face {{ font-family: "{family}"; font-weight: {weight}; font-style: {style}; '
			f'src: url("{url}") format("truetype"); }}'
		)
	return "\n".join(rules)


def _page_shell(template, body, extra_css=""):
	width, height = _page_dimensions(template)
	page_size = template.page_size if template.page_size in PAGE_SIZES else "A4"
	orientation = "Portrait" if template.orientation == "Portrait" else "Landscape"
	return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="pdfkit-page-size" content="{page_size}">
<meta name="pdfkit-orientation" content="{orientation}">
<meta name="pdfkit-margin-top" content="0">
<meta name="pdfkit-margin-bottom" content="0">
<meta name="pdfkit-margin-left" content="0">
<meta name="pdfkit-margin-right" content="0">
<style>
{_font_face_css()}
@page {{ size: {page_size} {orientation.lower()}; margin: 0; }}
.print-format {{ margin-top: 0mm; margin-bottom: 0mm; margin-left: 0mm; margin-right: 0mm; page-size: {page_size}; orientation: {orientation}; }}
html, body {{ margin: 0; padding: 0; background: #fff; }}
body {{ font-family: {FONT_STACKS[DEFAULT_FONT]}; }}
.cert-page {{ position: relative; width: {width}mm; height: {height}mm; overflow: hidden; }}
{extra_css}
</style>
</head>
<body>
<div class="cert-page">{body}</div>
</body>
</html>"""


def _render_image_template(template, values, images):
	from lms.lms.doctype.lms_certificate_template.lms_certificate_template import validate_layout

	width, height = _page_dimensions(template)
	layout = validate_layout(template.layout_json or "[]")
	background = _file_to_url(template.background_image)

	parts = []
	if background:
		parts.append(
			f'<img src="{escape(background)}" style="position:absolute;left:0;top:0;'
			f'width:{width}mm;height:{height}mm;">'
		)

	for element in layout:
		field = element["field"]
		left = element["x"] * width / 100
		top = element["y"] * height / 100
		box = element["width"] * width / 100

		if field in IMAGE_KEYS:
			url = images.get(field)
			if not url:
				continue
			parts.append(
				f'<div style="position:absolute;left:{left:.2f}mm;top:{top:.2f}mm;width:{box:.2f}mm;">'
				f'<img src="{escape(url)}" style="width:100%;height:auto;"></div>'
			)
			continue

		text = str(values.get(field) or "")
		if not text:
			continue

		font_percent = element.get("font_size") or 3
		font_pt = font_percent * height / 100 * 72 / 25.4
		if field == "student_name" and len(text) > LONG_NAME_LENGTH:
			font_pt = font_pt * LONG_NAME_LENGTH / len(text)

		stack = FONT_STACKS.get(element.get("font_family") or DEFAULT_FONT, FONT_STACKS[DEFAULT_FONT])
		if ARABIC_RE.search(text):
			stack = FONT_STACKS["Noto Naskh Arabic"]
		color = element.get("color") or "#000000"
		style = (
			f"position:absolute;left:{left:.2f}mm;top:{top:.2f}mm;width:{box:.2f}mm;"
			f"font-family:{stack};font-size:{font_pt:.2f}pt;line-height:1.15;color:{color};"
			f"text-align:{element.get('align', 'left')};"
			f"font-weight:{'bold' if element.get('bold') else 'normal'};"
			f"font-style:{'italic' if element.get('italic') else 'normal'};"
		)
		parts.append(f'<div style="{escape(style)}">{escape(text)}</div>')

	return _page_shell(template, "\n".join(parts))


def render_template_html(template, parts):
	context, values, images = parts
	if template.template_type == "Image":
		return _render_image_template(template, values, images)
	return _page_shell(template, render_html_template(template.html, context), sanitize_css(template.css))


def render_certificate(cert_name, template=None, sample=False):
	cert = frappe.get_doc("LMS Certificate", cert_name)
	template = template or cert.certificate_template
	if not template:
		frappe.throw(_("This certificate does not use a certificate template."))

	if isinstance(template, str):
		template = frappe.get_doc("LMS Certificate Template", template)

	if sample:
		parts = _sample_parts(template)
	else:
		values, images = _collect(cert, template)
		parts = (build_context(values, images), values, images)
	return render_template_html(template, parts)


def render_lms_certificate(name):
	doc = frappe.get_doc("LMS Certificate", name)
	if not (frappe.has_permission("LMS Certificate", "print", doc) or frappe.has_website_permission(doc)):
		raise frappe.PermissionError
	return render_certificate(name)


def _template_from_input(template):
	if isinstance(template, str):
		stripped = template.strip()
		if stripped.startswith("{"):
			template = json.loads(stripped)
		else:
			return frappe.get_doc("LMS Certificate Template", stripped)

	if isinstance(template, dict):
		doc = frappe.new_doc("LMS Certificate Template")
		doc.update(template)
		return doc
	frappe.throw(_("Invalid template"))


@frappe.whitelist()
def preview_certificate_template(template, format="html"):
	frappe.only_for(["System Manager", "Moderator"])
	from lms.lms.doctype.lms_certificate_template.lms_certificate_template import validate_layout

	doc = _template_from_input(template)
	if doc.template_type == "Image":
		doc.layout_json = json.dumps(validate_layout(doc.layout_json or "[]"))
	else:
		doc.validate()

	html = render_template_html(doc, _sample_parts(doc))
	if format == "pdf":
		from frappe.utils.pdf import get_pdf

		frappe.local.response.filename = "certificate-preview.pdf"
		frappe.local.response.filecontent = get_pdf(html)
		frappe.local.response.type = "pdf"
		return
	return html
