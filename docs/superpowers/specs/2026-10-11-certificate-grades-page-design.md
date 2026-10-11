# Certificate grades page

## Goal
Optionally append a second page, a grades report, to the certificate PDF. The reference screenshot came from another institute and is only an example of the idea; the page is styled like our default certificate template.

## Data
- Mark: `Batch Grade Record.total` from the batch's submitted `Batch Grade Sheet`, matched by the certificate's member and batch.
- Term and teacher: `Batch Grade Sheet.term` and `instructor_name`.
- From/To: `LMS Batch.start_date` / `end_date`.
- Student name and course title: already in the certificate context.
- New field `Batch Grade Record.teacher_comments` (Small Text), editable in the grade sheet UI.
- Average label: new child table `Certificate Grade Band` (min_mark Float, label Data) on LMS Settings. Highest band whose `min_mark <= mark` wins; below all bands shows no label. Defaults seeded by patch: 90 Excellent, 80 Very Good, 70 Good, 60 Pass.
- No absent hours.

## Rendering
- New check `include_grades_page` on LMS Certificate Template (HTML and Image types).
- `certificate_renderer._collect_grades(cert)` returns None unless the certificate has a batch with a submitted grade sheet containing a record for the member. No grades means no second page.
- `render_template_html` appends, when enabled and grades exist, a page-break and the grades page rendered from shipped `default_template/grades.html` and `grades.css` through the same sandboxed Jinja environment. Values are escaped; the logo comes from the template context. Page size and orientation follow the template.
- Preview renders the page with sample grades.
- Verify page, print format and legacy `Certification` doctype are unchanged.

## Testing
- Unit: band lookup edges, `_collect_grades` None cases (no batch, no sheet, draft sheet, no record).
- Render: output contains a page break and the grades only when enabled and data exists.
- E2E: bulk-issue for a batch with a grade sheet, download the PDF, expect two pages.

## Out of scope
Editable grades layout per template, backfill of existing certificates (they get the page on next render if data exists).
