# Certificate Grades Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optionally append a grades report page (mark, average label, term, teacher, comments) to the certificate PDF.

**Architecture:** A new module `lms/lms/certificate_grades.py` gathers grade data from the submitted `Batch Grade Sheet` and maps a mark to a label via configurable bands. `certificate_renderer.render_template_html` appends a built-in `grades.html` page (rendered in the existing Jinja sandbox) when the template's `include_grades_page` is on and grade data exists.

**Tech Stack:** Frappe v15, Jinja sandbox, wkhtmltopdf, Vue 3 / frappe-ui.

**Spec:** `docs/superpowers/specs/2026-10-11-certificate-grades-page-design.md`

## Global Constraints

- No absent hours anywhere. The screenshot in the request is an example from another institute, not the client's design.
- Grades page style follows the default template (colours `#1E4FA3`, `#B8893A`, `#14233f`, font stack of `default.css`).
- Page size and orientation follow the template.
- No grades data means no second page, never an error.
- Do not add attribution trailers to commits. Commit locally on `pr-1`; do not push.
- Tabs for indentation in Python and Vue, matching surrounding files.
- Verify page, print format and legacy `Certification` doctype are untouched.

## Review Focus

- Student has no grade record in the batch: certificate renders one page, no error.
- Only a draft (docstatus 0) or cancelled (2) grade sheet exists: ignored.
- Two submitted sheets for the batch (two instructors): the latest sheet containing the student wins.
- Mark exactly on a band boundary (90, 89.99) and mark below every band: boundary picks the higher band; below all bands gives an empty label.
- Teacher comments containing HTML or Arabic text: escaped, rendered, no layout break.
- Certificate without a batch (course-completion certificate): no grades page even when the toggle is on.
- LMS Settings band table empty: built-in default bands apply.

---

### Task 1: Grade data module and band doctype

**Files:**
- Create: `lms/lms/doctype/certificate_grade_band/__init__.py` (empty)
- Create: `lms/lms/doctype/certificate_grade_band/certificate_grade_band.json`
- Create: `lms/lms/doctype/certificate_grade_band/certificate_grade_band.py`
- Create: `lms/lms/certificate_grades.py`
- Create: `lms/lms/test_certificate_grades.py`
- Modify: `lms/lms/doctype/batch_grade_record/batch_grade_record.json` (add `teacher_comments`)
- Modify: `lms/lms/doctype/lms_settings/lms_settings.json` (add band table)

**Interfaces:**
- Produces: `DEFAULT_GRADE_BANDS: list[tuple[float, str]]`, `get_grade_label(mark, bands=None) -> str`, `get_grade_bands() -> list[tuple[float, str]]`, `collect_grades(cert) -> dict | None` with keys `mark` (float), `grade_label` (str), `term`, `teacher_name`, `teacher_comments` (all str).
- Consumes: `LMS Certificate` doc fields `batch_name`, `member`.

- [ ] **Step 1: Write the failing tests** in `lms/lms/test_certificate_grades.py`

```python
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

		with patch("frappe.get_all", return_value=sheets), patch("frappe.db.get_value", side_effect=get_value):
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
```

- [ ] **Step 2: Run to verify failure**

Run (user's terminal, docker needs sudo): `sudo docker compose exec -w /home/frappe/frappe-bench frappe bench --site lms.localhost run-tests --app lms --module lms.lms.test_certificate_grades`
Expected: ImportError, `lms.lms.certificate_grades` missing.

- [ ] **Step 3: Implement** `lms/lms/certificate_grades.py`

```python
import frappe
from frappe.utils import flt

DEFAULT_GRADE_BANDS = [
	(90, "Excellent"),
	(80, "Very Good"),
	(70, "Good"),
	(60, "Pass"),
]


def get_grade_label(mark, bands=None):
	"""Label of the highest band whose minimum is <= mark, else empty."""
	mark = flt(mark)
	for minimum, label in sorted(bands if bands is not None else get_grade_bands(), reverse=True):
		if mark >= minimum:
			return label
	return ""


def get_grade_bands():
	rows = frappe.get_all(
		"Certificate Grade Band",
		filters={"parent": "LMS Settings", "parenttype": "LMS Settings"},
		fields=["min_mark", "label"],
	)
	return [(flt(row.min_mark), row.label) for row in rows] or DEFAULT_GRADE_BANDS


def collect_grades(cert):
	"""Grades for a certificate's member from the latest submitted sheet of its batch, or None."""
	if not cert.batch_name:
		return None

	sheets = frappe.get_all(
		"Batch Grade Sheet",
		filters={"batch": cert.batch_name, "docstatus": 1},
		fields=["name", "term", "instructor_name"],
		order_by="modified desc",
	)
	for sheet in sheets:
		record = frappe.db.get_value(
			"Batch Grade Record",
			{"parent": sheet.name, "parenttype": "Batch Grade Sheet", "student": cert.member},
			["total", "teacher_comments"],
			as_dict=True,
		)
		if record:
			return {
				"mark": flt(record.total),
				"grade_label": get_grade_label(record.total),
				"term": sheet.term or "",
				"teacher_name": sheet.instructor_name or "",
				"teacher_comments": record.teacher_comments or "",
			}
	return None
```

`certificate_grade_band.py`:

```python
from frappe.model.document import Document


class CertificateGradeBand(Document):
	pass
```

`certificate_grade_band.json`: `istable: 1`, `editable_grid: 1`, module `Lms`, `field_order` `["min_mark","label"]`, fields `min_mark` (Float, reqd, in_list_view, label "Minimum Mark"), `label` (Data, reqd, in_list_view, label "Label"). Copy the remaining boilerplate keys (`actions`, `creation`, `engine`, `modified`, `owner`, `permissions: []`) from `lms/lms/doctype/batch_grade_record/batch_grade_record.json`.

`batch_grade_record.json`: add `"teacher_comments"` to `field_order` after `"total"` and the field `{"fieldname": "teacher_comments", "fieldtype": "Small Text", "label": "Teacher Comments"}`.

`lms_settings.json`: in `field_order` insert after `"livecode_url"`: `"certificate_grades_section"`, `"certificate_grade_bands"`; add fields `{"fieldname": "certificate_grades_section", "fieldtype": "Section Break", "label": "Certificate Grades"}` and `{"fieldname": "certificate_grade_bands", "fieldtype": "Table", "label": "Grade Bands", "options": "Certificate Grade Band", "description": "Maps a mark to the label shown on the certificate grades page. Built-in defaults apply when empty."}`.

- [ ] **Step 4: Migrate and run tests**

Run: `sudo docker compose exec -w /home/frappe/frappe-bench frappe bench --site lms.localhost migrate` then the Step 2 command.
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add lms/lms/certificate_grades.py lms/lms/test_certificate_grades.py lms/lms/doctype/certificate_grade_band lms/lms/doctype/batch_grade_record lms/lms/doctype/lms_settings
git commit -m "feat(certificates): grade data collection and grade bands"
```

### Task 2: Template toggle and grades page rendering

**Files:**
- Create: `lms/lms/doctype/lms_certificate_template/default_template/grades.html`
- Create: `lms/lms/doctype/lms_certificate_template/default_template/grades.css`
- Modify: `lms/lms/doctype/lms_certificate_template/lms_certificate_template.json` (field `include_grades_page`)
- Modify: `lms/lms/certificate_renderer.py` (`render_template_html`, `render_certificate`, `preview_certificate_template`, new `_render_grades_page`)
- Modify: `lms/lms/doctype/lms_certificate_template/test_lms_certificate_template.py`

**Interfaces:**
- Consumes: `collect_grades(cert)` from Task 1; `build_context`, `render_html_template`, `_page_dimensions`, `_font_face_css`, `escape` already in the renderer.
- Produces: `render_template_html(template, parts, grades=None)`; `SAMPLE_GRADES` dict in the renderer.

- [ ] **Step 1: Write failing tests** (append to `test_lms_certificate_template.py`)

```python
from lms.lms.certificate_renderer import SAMPLE_GRADES, render_template_html, _sample_parts

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
```

- [ ] **Step 2: Run, expect FAIL** (ImportError on `SAMPLE_GRADES`). Same run-tests command with `--module lms.lms.doctype.lms_certificate_template.test_lms_certificate_template`.

- [ ] **Step 3: Implement**

`lms_certificate_template.json`: add `"include_grades_page"` to `field_order` after `"orientation"` and the field `{"default": "0", "fieldname": "include_grades_page", "fieldtype": "Check", "label": "Include Grades Page", "description": "Adds a grades report as a second page when the student has submitted grades for the batch."}`.

`certificate_renderer.py` additions:

```python
from pathlib import Path

GRADES_FOLDER = Path(__file__).parent / "doctype" / "lms_certificate_template" / "default_template"

SAMPLE_GRADES = {
	"mark": 92,
	"grade_label": "Excellent",
	"term": "Term 3",
	"teacher_name": "Sample Teacher",
	"teacher_comments": "A cooperative and hard-working student with strong speaking and writing.",
}


def _render_grades_page(template, parts, grades):
	context, values, images = parts
	grade_context = dict(context)
	for key, value in grades.items():
		grade_context[key] = str(int(value) if key == "mark" and float(value).is_integer() else value)
		grade_context[f"{key}_is_arabic"] = bool(ARABIC_RE.search(grade_context[key]))
	width, height = _page_dimensions(template)
	body = render_html_template((GRADES_FOLDER / "grades.html").read_text(encoding="utf-8"), grade_context)
	css = sanitize_css((GRADES_FOLDER / "grades.css").read_text(encoding="utf-8"))
	return (
		f"<style>{css}</style>"
		f'<div class="cert-page grades-page" style="page-break-before: always; '
		f'width:{width}mm; height:{height}mm;">{body}</div>'
	)
```

Change `render_template_html`:

```python
def render_template_html(template, parts, grades=None):
	context, values, images = parts
	if template.template_type == "Image":
		html = _render_image_template(template, values, images)
	else:
		html = _page_shell(template, render_html_template(template.html, context), sanitize_css(template.css))
	if template.get("include_grades_page") and grades:
		html = html.replace("</body>", _render_grades_page(template, parts, grades) + "\n</body>")
	return html
```

In `render_certificate` (non-sample): `grades = collect_grades(cert) if template.include_grades_page else None` (import from `lms.lms.certificate_grades`), sample: `grades = SAMPLE_GRADES`; pass `render_template_html(template, parts, grades)`. In `preview_certificate_template` pass `SAMPLE_GRADES`.

Note: `class="cert-page grades-page"` contains `class="cert-page` so the test count of 2 holds; the first page uses `class="cert-page"`.

`grades.html` (uses only placeholders, all escaped by autoescape):

```html
<div class="gr-frame"></div>
<div class="gr-header">
	{{ logo }}
	<div class="gr-title">Grades Report</div>
</div>
<div class="gr-meta">
	<div class="gr-line"><span class="gr-label">Name</span> <span class="gr-value {% if student_name_is_arabic %}gr-ar{% endif %}">{{ student_name }}</span></div>
	<div class="gr-line"><span class="gr-label">Course</span> <span class="gr-value">{{ course_title }}</span></div>
	<div class="gr-line"><span class="gr-label">Batch</span> <span class="gr-value">{{ batch_title }}</span></div>
	<div class="gr-line"><span class="gr-label">Term</span> <span class="gr-value">{{ term }}</span></div>
	<div class="gr-line"><span class="gr-label">Period</span> <span class="gr-value">{{ start_date }} - {{ end_date }}</span></div>
	<div class="gr-line"><span class="gr-label">Certificate No.</span> <span class="gr-value">{{ serial_number }}</span></div>
</div>
<table class="gr-marks">
	<tr><th>Mark</th><th>Average</th></tr>
	<tr><td>{{ mark }}</td><td>{{ grade_label }}</td></tr>
</table>
<div class="gr-teacher"><span class="gr-label">Teacher</span> <span class="gr-value">{{ teacher_name }}</span></div>
<div class="gr-comments">
	<div class="gr-label">Teacher's Comments</div>
	<div class="gr-text {% if teacher_comments_is_arabic %}gr-ar{% endif %}">{{ teacher_comments }}</div>
</div>
```

`grades.css` (positions are relative to a page of size `width x height`, content laid out with normal flow and margins so it works for both orientations):

```css
.grades-page { position: relative; background: #fff; color: #14233f; font-family: "EB Garamond", "Noto Naskh Arabic", Georgia, "Times New Roman", serif; padding: 18mm 24mm; -webkit-box-sizing: border-box; box-sizing: border-box; }
.grades-page .gr-frame { position: absolute; left: 6mm; top: 6mm; right: 6mm; bottom: 6mm; border: 0.8mm solid #1E4FA3; }
.grades-page .gr-header { text-align: center; margin-bottom: 8mm; }
.grades-page .cert-logo { height: 16mm; width: auto; }
.grades-page .gr-title { margin-top: 4mm; font-size: 22pt; letter-spacing: 0.3em; text-transform: uppercase; color: #1E4FA3; font-weight: 600; }
.grades-page .gr-line { font-size: 12pt; margin-bottom: 2mm; }
.grades-page .gr-label { font-size: 8pt; letter-spacing: 0.22em; text-transform: uppercase; color: #B8893A; font-weight: 600; display: inline-block; width: 38mm; }
.grades-page .gr-value { font-size: 12pt; color: #0F2347; }
.grades-page .gr-marks { border-collapse: collapse; margin: 8mm 0; width: 100mm; }
.grades-page .gr-marks th, .grades-page .gr-marks td { border: 0.25mm solid #B8893A; padding: 2mm 4mm; text-align: center; font-size: 12pt; }
.grades-page .gr-marks th { font-size: 8pt; letter-spacing: 0.22em; text-transform: uppercase; color: #B8893A; }
.grades-page .gr-teacher { font-size: 12pt; margin-bottom: 6mm; }
.grades-page .gr-comments { border: 0.25mm solid #B8893A; padding: 4mm 6mm; }
.grades-page .gr-text { font-size: 11pt; line-height: 1.4; margin-top: 2mm; }
.grades-page .gr-ar { font-family: "Noto Naskh Arabic", serif; }
```

- [ ] **Step 4: Run tests, expect PASS.**
- [ ] **Step 5: Commit** `git commit -m "feat(certificates): append grades page to certificate PDF"` (add listed files).

### Task 3: Frontend

**Files:**
- Modify: `frontend/src/pages/BatchGrading.vue` (comments column)
- Modify: `frontend/src/components/Settings/CertificateTemplateForm.vue` (checkbox)

**Interfaces:**
- Consumes: `teacher_comments` on `Batch Grade Record` (Task 1), `include_grades_page` on the template (Task 2).

- [ ] **Step 1: BatchGrading.vue.** Add a header cell after Total: `<th class="px-4 py-3 text-left font-medium">{{ __('Teacher Comments') }}</th>`. Add the matching cell after the total `<td>`:

```vue
<td class="px-2 py-3 min-w-[260px]">
	<FormControl
		v-model="row.teacher_comments"
		type="textarea"
		:rows="2"
		:disabled="isReadOnly"
	/>
</td>
```

In `populateStudents` set `teacher_comments: ''` on each new record. `serializeDoc` already spreads the row, so comments are saved. Raise the table `min-w-[900px]` to `min-w-[1160px]`.

- [ ] **Step 2: CertificateTemplateForm.vue.** After the `enabled` checkbox block add:

```vue
<div class="flex items-end pb-1">
	<FormControl
		v-model="template.include_grades_page"
		type="checkbox"
		:label="__('Include grades page')"
	/>
</div>
```

Add `include_grades_page: 0` to `defaults()`. Confirm the save payload sends the whole `template` object (it does for `enabled`); the preview call already posts the whole object so the sample grades page appears in preview.

- [ ] **Step 3: Build** (user's terminal): `sudo docker compose exec -w /home/frappe/frappe-bench/apps/lms frappe yarn build` or the project's frontend build command used earlier; confirm no errors.
- [ ] **Step 4: Commit** `git commit -m "feat(certificates): grades page toggle and teacher comments UI"`.

### Task 4: Docs and end-to-end verification

**Files:**
- Modify: `docs/certificate-templates-contract.md` (new section "Grades page": toggle, data source, band defaults, no placeholders added, rendering rules)

- [ ] **Step 1: Document** the toggle, the data source (latest submitted `Batch Grade Sheet` containing the member), band configuration in LMS Settings with the default bands, and that the page is skipped when no data.
- [ ] **Step 2: E2E with Playwright** after the user runs migrate + build + restart: enter marks and a comment in a grade sheet for `e2e-batch`, submit it, enable the toggle on `E2E HTML Template`, issue a certificate, download the PDF via `sid` cookie + curl, check `pdfinfo` reports 2 pages and `pdftotext` contains the mark, label and comment. Repeat with a student lacking a grade record (1 page) and with the toggle off (1 page). Check the preview in the template editor.
- [ ] **Step 3: Commit** `git commit -m "docs: certificate grades page"`.

---

## Self-review

- Spec coverage: data (Task 1), bands (Task 1), toggle (Task 2/3), renderer + preview (Task 2), comment UI (Task 3), docs/e2e (Task 4). Out-of-scope items not planned.
- Types: `collect_grades` keys match those consumed in `_render_grades_page` and `SAMPLE_GRADES`.
- Review Focus lines covered by tests in Task 1 (no batch, no sheet, missing student, latest sheet, docstatus filter, boundaries, below bands) and Task 2 (escaping, Arabic, disabled, image type); empty settings table covered by the `DEFAULT_GRADE_BANDS` fallback in `get_grade_bands`.
