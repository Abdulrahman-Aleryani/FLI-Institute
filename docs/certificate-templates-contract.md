# Certificate templates: contract

## Records and files
- Doctype: `LMS Certificate Template` (`lms/lms/doctype/lms_certificate_template/`).
- Default template record: **`FLI Default`** (HTML, A4 Landscape). Source: `lms/lms/doctype/lms_certificate_template/default_template/default.html` and `default.css`. Created by `create_default_template()` on install and by the `certificate_templates` patch; it also fills LMS Settings `default_certificate_template` if empty.
- Print Format used for every template-based certificate: **`Certificate Template`** (`lms/lms/print_format/certificate_template/`). It renders `{{ render_lms_certificate(doc.name) }}`. Older certificates keep their old print format.
- Renderer: `lms/lms/certificate_renderer.py`. Verify page: `lms/www/verify.py` + `verify.html`, route `/verify/<token>`.
- Fonts: `lms/public/fonts/` (static EB Garamond and Noto Naskh Arabic, OFL).

## Template resolution
Batch `certificate_template` > course `certificate_template` > LMS Settings `default_certificate_template`. Disabled templates are skipped. Issuers can still choose a template explicitly.

## Placeholders (HTML templates)
Use `{{ name }}`. Text placeholders are auto-escaped strings (empty string when missing). Image placeholders are ready-made `<img>` HTML.

| Placeholder | Kind | Notes |
| --- | --- | --- |
| `student_name` | text | |
| `course_title` | text | |
| `batch_title` | text | |
| `start_date`, `end_date` | text | batch dates, `dd MMM yyyy` |
| `serial_number` | text | printed reference only |
| `certificate_id` | text | |
| `verification_url` | text | `/verify/<token>` |
| `logo_url` | text | URL / data URI of the site logo (HTML templates only, not placeable in image layouts) |
| `signer_1_name`, `signer_1_title`, `signer_2_name`, `signer_2_title` | text | from the template |
| `evaluator_name` | text | |
| `institute_name` | text | Website Settings `app_name` |
| `qr_code` | image | `<img class="cert-qr">` |
| `logo` | image | `<img class="cert-logo">`; site brand logo (Website Settings `app_logo`, else `banner_image`, else `/assets/lms/images/lms-logo.png`) |
| `signature_1`, `signature_2` | image | `<img class="cert-signature">`; empty when no signature |

Every text placeholder also has a boolean `<name>_is_arabic` (for example `student_name_is_arabic`), true when the value contains Arabic letters. wkhtmltopdf cannot fall back between web fonts per glyph, so switch the font yourself: `<div class="cert-name{% if student_name_is_arabic %} cert-ar{% endif %}">` with `.cert-ar { font-family: "Noto Naskh Arabic", serif; letter-spacing: 0; }`. Image layouts do this automatically.

Also available: `_("text")` for translation. Nothing else: no `frappe`, `doc` or Jinja globals. The environment is an immutable Jinja sandbox; `**`, any `*` on strings, private attributes and `{% include %}` are rejected. `<script>` tags are stripped; CSS has `@import`, `<style` and comments removed.

## Image templates: `layout_json`
A JSON list (max 60 elements). Each element:

| Key | Rule |
| --- | --- |
| `field` | any text key except `logo_url`, or `qr_code`, `logo`, `signature_1`, `signature_2` |
| `x`, `y` | number 0..100 (% of page width / height); booleans rejected |
| `width` | number > 0..100, default 30 |
| `font_size` | optional, > 0..30, % of page height |
| `font_family` | empty or `EB Garamond`, `Noto Naskh Arabic`, `Georgia`, `Helvetica` |
| `color` | empty or `#rgb` / `#rrggbb` |
| `align` | `left` (default) / `center` / `right` |
| `bold`, `italic` | coerced to bool |

`student_name` shrinks proportionally when longer than 28 characters.

## API
All paths are `/api/method/<dotted path>`.

| Path | Args | Returns | Roles |
| --- | --- | --- | --- |
| `lms.lms.certificate_renderer.preview_certificate_template` | `template` (JSON string of an unsaved doc, or a saved name), `format` = `html` / `pdf` | HTML string, or a PDF file response | System Manager, Moderator |
| `lms.lms.doctype.lms_certificate.lms_certificate.create_certificate` | `course` | existing certificate (`name`, `course`, `template`) or the new doc | logged-in student (eligibility checked) |
| `lms.lms.doctype.lms_certificate.lms_certificate.get_resolved_certificate_template` | `course`, `batch` | template name or null | System Manager, Moderator, Batch Evaluator |
| `lms.lms.doctype.lms_certificate.lms_certificate.revoke_certificate` | `name`, `reason` | `{name, revoked: 1}` | System Manager, Moderator |
| `lms.lms.doctype.lms_certificate.lms_certificate.create_bulk_certificates` | `batch`, `template`, `published`, `course` | `{created: [names], skipped: [{member, reason}], failed: [{member, error}]}` | System Manager, Moderator |
| `lms.lms.api.save_certificate_details` | existing args + `template`, `certificate_template` | certificate name | evaluator of the course/batch, System Manager, Moderator |
| `lms.lms.api.save_evaluation_details` | unchanged | evaluation name | same as above |
| `lms.lms.api.get_certification_details` | `course` | now also returns `serial_number`, `verification_token` on `certificate` | logged in |

## Security model
- Each certificate gets `verification_token = secrets.token_urlsafe(16)` and a sequential `serial_number`, both set server side on insert and immutable afterwards. The QR code encodes `/verify/<token>`; there is no lookup by serial.
- Revoked certificates are not "certified" and are hidden from public listings. Revoked certificates can be re-issued.
- LMS Students can no longer create or write LMS Certificates.

## wkhtmltopdf CSS rules (HTML templates)
The PDF engine is old QtWebKit. In a template use only:
- absolute / relative positioning in `mm` inside `.cert-page` (it is exactly the page size and clips overflow); tables are fine
- no flexbox, grid, CSS variables, `calc()`, `gap`, `:is()` / `:where()`, `object-fit`, `@import` or script
- inline SVG without filters or masks; `-webkit-transform` for mirroring
- fonts via the families in `fonts.css` (`EB Garamond`, `Noto Naskh Arabic`), which are registered by the page shell
- no SVG `opacity` / `stroke-opacity` / `fill-opacity` (ignored in the PDF): use a pre-blended solid colour
- no `unicode-range`; Arabic text needs its own font family (see `*_is_arabic` above)
- keep everything inside the page: nothing may spill to a second page

Page size, orientation and zero margins are set by the renderer through a `.print-format { ... }` rule (the only mechanism Frappe v15 honours); do not override them.
