"""Attendance-specific backend APIs used by the LMS frontend."""

from __future__ import annotations

from collections import defaultdict, OrderedDict
from datetime import timedelta
from typing import Dict, Iterable

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import formatdate, getdate, nowdate

ALLOWED_ATTENDANCE_ROLES = {"Administrator", "Moderator", "Instructor", "LMS Instructor"}
ADMIN_ROLES = {"Administrator", "Moderator"}
ATTENDANCE_STATUSES = {"Present", "Absent", "Late", "Excused"}


def _require_attendance_role() -> set[str]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to manage attendance."), frappe.PermissionError)

	roles = set(frappe.get_roles(frappe.session.user))
	if roles.isdisjoint(ALLOWED_ATTENDANCE_ROLES):
		frappe.throw(_("You are not allowed to manage attendance."), frappe.PermissionError)

	return roles


def _has_admin_privileges(roles: Iterable[str]) -> bool:
	return not ADMIN_ROLES.isdisjoint(set(roles))


def _ensure_batch_access(batch: str, roles: Iterable[str] | None = None) -> None:
	if not batch:
		frappe.throw(_("Batch is required."), frappe.ValidationError)

	roles = roles or _require_attendance_role()
	if _has_admin_privileges(roles):
		return

	if frappe.db.exists(
		"Course Instructor",
		{
			"parent": batch,
			"parenttype": "LMS Batch",
			"instructor": frappe.session.user,
		},
	):
		return

	frappe.throw(_("You do not have access to this batch."), frappe.PermissionError)


def _active_batch_conditions(batch_alias: DocType, reference_date):
	"""Return QB conditions representing an 'active' batch."""
	return [
		batch_alias.published == 1,
		batch_alias.start_date <= reference_date,
		(batch_alias.end_date >= reference_date) | (batch_alias.end_date.isnull()),
	]


def _serialize_session(doc) -> Dict:
	doc = doc.as_dict()
	return {
		"name": doc.name,
		"batch": doc.batch,
		"session_date": doc.session_date,
		"status": doc.status,
		"docstatus": doc.docstatus,
		"notes": doc.get("notes"),
		"attendance_records": [
			{
				"name": row.name,
				"enrollment": row.enrollment,
				"student": row.student,
				"student_name": row.student_name,
				"status": row.status,
				"excuse_reason": row.excuse_reason,
				"notes": row.notes,
			}
			for row in doc.get("attendance_records", [])
		],
	}


def _serialize_record(record) -> Dict:
	return {
		"name": record.name,
		"enrollment": record.enrollment,
		"student": record.student,
		"student_name": record.student_name,
		"status": record.status,
		"excuse_reason": record.excuse_reason,
		"notes": record.notes,
	}


def _ensure_session_date_within_batch(batch: str, session_date):
	start_date, end_date = frappe.db.get_value("LMS Batch", batch, ["start_date", "end_date"])
	if start_date and session_date < getdate(start_date):
		frappe.throw(
			_("Session date {0} is before the batch starts.").format(session_date), frappe.ValidationError
		)
	if end_date and session_date > getdate(end_date):
		frappe.throw(
			_("Session date {0} is after the batch ends.").format(session_date), frappe.ValidationError
		)


def _create_session_with_enrollments(batch: str, session_date) -> frappe.model.document.Document:
	enrollments = frappe.get_all(
		"LMS Batch Enrollment",
		filters={"batch": batch},
		fields=["name", "member", "member_name"],
		order_by="member_name asc",
	)

	if not enrollments:
		frappe.throw(_("Cannot create attendance session because the batch has no enrollments yet."))

	session = frappe.new_doc("Batch Attendance Session")
	session.batch = batch
	session.session_date = session_date
	session.notes = ""

	for enrollment in enrollments:
		session.append(
			"attendance_records",
			{
				"enrollment": enrollment.name,
				"student": enrollment.member,
				"student_name": enrollment.member_name,
				"status": "Absent",
			},
		)

	session.insert()
	return session


@frappe.whitelist()
def get_instructor_batches():
	"""Return batches the logged-in instructor/moderator can take attendance for (active only)."""
	roles = _require_attendance_role()
	user = frappe.session.user
	today = getdate()

	Batch = DocType("LMS Batch")
	query = (
		frappe.qb.from_(Batch)
		.select(Batch.name, Batch.title, Batch.start_date, Batch.end_date, Batch.timezone)
	)

	for condition in _active_batch_conditions(Batch, today):
		query = query.where(condition)

	if not _has_admin_privileges(roles):
		CourseInstructor = DocType("Course Instructor")
		query = (
			query.join(CourseInstructor)
			.on((CourseInstructor.parent == Batch.name) & (CourseInstructor.parenttype == "LMS Batch"))
			.where(CourseInstructor.instructor == user)
		)

	query = query.orderby(Batch.start_date, order=frappe.qb.asc)

	return query.run(as_dict=True)


@frappe.whitelist()
def get_or_create_session(batch: str, session_date: str | None = None):
	roles = _require_attendance_role()
	_ensure_batch_access(batch, roles)

	session_date = getdate(session_date or nowdate())
	_ensure_session_date_within_batch(batch, session_date)

	existing = frappe.db.exists(
		"Batch Attendance Session",
		{"batch": batch, "session_date": session_date},
	)

	if existing:
		doc = frappe.get_doc("Batch Attendance Session", existing)
	else:
		doc = _create_session_with_enrollments(batch, session_date)

	return _serialize_session(doc)


@frappe.whitelist()
def submit_session(name: str):
	roles = _require_attendance_role()
	doc = frappe.get_doc("Batch Attendance Session", name)
	_ensure_batch_access(doc.batch, roles)

	if doc.docstatus == 1:
		return _serialize_session(doc)

	doc.submit()
	doc.reload()
	return _serialize_session(doc)


@frappe.whitelist()
def reopen_session(name: str):
	roles = _require_attendance_role()
	if not _has_admin_privileges(roles):
		frappe.throw(_("Only Moderators or Administrators can reopen submitted sessions."), frappe.PermissionError)

	doc = frappe.get_doc("Batch Attendance Session", name)
	if doc.docstatus != 1:
		frappe.throw(_("Only submitted sessions can be reopened."), frappe.ValidationError)

	frappe.db.set_value("Batch Attendance Session", name, {"docstatus": 0, "status": "Draft"})
	doc.reload()
	return _serialize_session(doc)


@frappe.whitelist()
def update_attendance_record(record_name: str, status: str | None = None, excuse_reason: str | None = None, notes: str | None = None):
	roles = _require_attendance_role()
	record = frappe.get_doc("Batch Attendance Record", record_name)
	session = frappe.get_doc("Batch Attendance Session", record.parent)
	_ensure_batch_access(session.batch, roles)

	if session.docstatus != 0:
		frappe.throw(_("You cannot edit a submitted attendance session. Please reopen it first."))

	if status:
		if status not in ATTENDANCE_STATUSES:
			frappe.throw(_("Invalid attendance status: {0}").format(status))
		record.status = status

	if record.status == "Excused":
		if not (excuse_reason or record.excuse_reason):
			frappe.throw(_("Excuse reason is required when marking a student as Excused."))
		record.excuse_reason = excuse_reason or record.excuse_reason
	else:
		record.excuse_reason = ""

	if notes is not None:
		record.notes = notes

	record.save(ignore_permissions=True)
	record.reload()
	return _serialize_record(record)


@frappe.whitelist()
def get_attendance_summary(batch: str, from_date: str | None = None, to_date: str | None = None):
	roles = _require_attendance_role()
	_ensure_batch_access(batch, roles)

	if not from_date and not to_date:
		from_date = to_date = nowdate()

	if not from_date:
		from_date = to_date
	if not to_date:
		to_date = from_date

	from_date = getdate(from_date)
	to_date = getdate(to_date)

	if from_date > to_date:
		from_date, to_date = to_date, from_date

	sessions = frappe.get_all(
		"Batch Attendance Session",
		filters={
			"batch": batch,
			"session_date": ["between", [from_date, to_date]],
		},
		fields=["name", "session_date", "status", "docstatus", "notes"],
		order_by="session_date asc",
	)

	students_totals: Dict[str, Dict] = {}
	overall_counts = defaultdict(int)
	serialized_sessions = []

	for session in sessions:
		records = frappe.get_all(
			"Batch Attendance Record",
			filters={"parent": session.name},
			fields=["name", "enrollment", "student", "student_name", "status", "excuse_reason", "notes"],
			order_by="student_name asc",
		)

		for record in records:
			key = record.student or record.enrollment
			if key not in students_totals:
				students_totals[key] = {
					"student": record.student,
					"student_name": record.student_name,
					"enrollment": record.enrollment,
					"counts": {status: 0 for status in ATTENDANCE_STATUSES},
					"total_sessions": 0,
				}

			students_totals[key]["counts"][record.status] += 1
			students_totals[key]["total_sessions"] += 1
			overall_counts[record.status] += 1

		session_dict = {
			**session,
			"attendance_records": records,
		}
		serialized_sessions.append(session_dict)

	for student in students_totals.values():
		total = student["total_sessions"]
		present = student["counts"]["Present"]
		student["attendance_percentage"] = round((present / total) * 100, 2) if total else 0

	return {
		"batch": batch,
		"from_date": str(from_date),
		"to_date": str(to_date),
		"sessions": serialized_sessions,
		"student_totals": list(students_totals.values()),
		"overall_counts": dict(overall_counts),
	}


# ---------------------------------------------------------------------------
# Batch-wide attendance sheet helpers
# ---------------------------------------------------------------------------

def _get_batch_doc(batch: str):
	doc = frappe.get_doc("LMS Batch", batch)
	if not doc.start_date or not doc.end_date:
		frappe.throw(
			_("Batch {0} needs both start and end dates set before taking attendance.").format(batch)
		)
	return doc


def _get_sheet_doc(batch: str):
	name = frappe.db.exists("Batch Attendance Sheet", {"batch": batch})
	if name:
		return frappe.get_doc("Batch Attendance Sheet", name)
	return None


def _ensure_sheet_dates(sheet, batch_doc):
	updated = False
	for field in ("start_date", "end_date", "timezone"):
		value = batch_doc.get(field) or sheet.get(field)
		if sheet.get(field) != value:
			sheet.set(field, value)
			updated = True
	if updated:
		sheet.db_set({"start_date": sheet.start_date, "end_date": sheet.end_date, "timezone": sheet.timezone})


def _get_batch_enrollments(batch: str):
	enrollments = frappe.get_all(
		"LMS Batch Enrollment",
		filters={"batch": batch},
		fields=["name", "member", "member_name"],
		order_by="member_name asc",
	)
	if not enrollments:
		frappe.throw(_("Cannot create attendance sheet because the batch has no enrollments yet."))
	return enrollments


def _format_week_label(index: int, week_start, week_end):
	start_str = formatdate(week_start, "MMM d")
	end_str = formatdate(week_end, "MMM d")
	return _("Week {0} · {1} – {2}").format(index, start_str, end_str)


def _ensure_sheet_entries(sheet, batch_doc, enrollments, save=True):
	start_date = getdate(batch_doc.start_date)
	end_date = getdate(batch_doc.end_date)
	total_days = (end_date - start_date).days + 1

	existing = {
		(str(entry.attendance_date), entry.enrollment)
		for entry in sheet.get("attendance_entries")
	}

	for day_offset in range(total_days):
		current_date = start_date + timedelta(days=day_offset)
		week_index = (day_offset // 7) + 1
		week_start = start_date + timedelta(days=(week_index - 1) * 7)
		week_end = min(week_start + timedelta(days=6), end_date)
		week_label = _format_week_label(week_index, week_start, week_end)
		weekday_name = formatdate(current_date, "ddd")

		date_key = str(current_date)

		for enrollment in enrollments:
			key = (date_key, enrollment.name)
			if key in existing:
				continue
			sheet.append(
				"attendance_entries",
				{
					"attendance_date": current_date,
					"week_index": week_index,
					"week_label": week_label,
					"weekday_name": weekday_name,
					"enrollment": enrollment.name,
					"student": enrollment.member,
					"student_name": enrollment.member_name,
					"status": "Absent",
				},
			)
			existing.add(key)

	if save:
		sheet.save(ignore_permissions=True)


@frappe.whitelist()
def get_batch_summary(batch: str):
	roles = _require_attendance_role()
	_ensure_batch_access(batch, roles)
	return frappe.db.get_value(
		"LMS Batch",
		batch,
		["name", "title", "start_date", "end_date", "timezone"],
		as_dict=True,
	)


def _serialize_sheet(sheet, include_entries=True):
	result = {
		"name": sheet.name,
		"batch": sheet.batch,
		"status": sheet.status,
		"docstatus": sheet.docstatus,
		"start_date": str(sheet.start_date),
		"end_date": str(sheet.end_date),
		"timezone": sheet.timezone,
		"notes": sheet.notes,
	}

	if not include_entries:
		return result

	weeks = OrderedDict()
	rows = {}

	for entry in sorted(
		sheet.get("attendance_entries"), key=lambda e: (str(e.attendance_date), e.student_name or "")
	):
		date_key = str(entry.attendance_date)
		week_info = weeks.setdefault(
			entry.week_index,
			{
				"index": entry.week_index,
				"label": entry.week_label,
				"days": OrderedDict(),
			},
		)
		week_info["days"].setdefault(
			date_key,
			{
				"date": date_key,
				"weekday": entry.weekday_name,
			},
		)

		row = rows.setdefault(
			entry.enrollment,
			{
				"enrollment": entry.enrollment,
				"student": entry.student,
				"student_name": entry.student_name,
				"entries": {},
			},
		)
		row["entries"][date_key] = {
			"name": entry.name,
			"status": entry.status,
			"excuse_reason": entry.excuse_reason,
			"notes": entry.notes,
			"week_index": entry.week_index,
		}

	result["weeks"] = [
		{
			"index": week_data["index"],
			"label": week_data["label"],
			"days": list(week_data["days"].values()),
		}
		for week_data in weeks.values()
	]
	result["rows"] = sorted(rows.values(), key=lambda r: (r["student_name"] or r["student"] or ""))
	return result


def _get_or_create_sheet(batch: str, roles: Iterable[str]):
	_ensure_batch_access(batch, roles)
	batch_doc = _get_batch_doc(batch)
	sheet = _get_sheet_doc(batch)
	enrollments = _get_batch_enrollments(batch)

	if not sheet:
		sheet = frappe.new_doc("Batch Attendance Sheet")
		sheet.batch = batch
		sheet.start_date = batch_doc.start_date
		sheet.end_date = batch_doc.end_date
		sheet.timezone = batch_doc.timezone
		_ensure_sheet_entries(sheet, batch_doc, enrollments, save=False)
		sheet.flags.ignore_permissions = True
		sheet.insert()
	else:
		_ensure_sheet_dates(sheet, batch_doc)

	_ensure_sheet_entries(sheet, batch_doc, enrollments)
	sheet.reload()
	return sheet


@frappe.whitelist()
def get_or_create_sheet(batch: str):
	roles = _require_attendance_role()
	sheet = _get_or_create_sheet(batch, roles)
	return _serialize_sheet(sheet)


@frappe.whitelist()
def submit_sheet(name: str):
	roles = _require_attendance_role()
	sheet = frappe.get_doc("Batch Attendance Sheet", name)
	_ensure_batch_access(sheet.batch, roles)

	if sheet.docstatus == 0:
		sheet.submit()
		sheet.reload()
	return _serialize_sheet(sheet)


@frappe.whitelist()
def reopen_sheet(name: str):
	roles = _require_attendance_role()
	if not _has_admin_privileges(roles):
		frappe.throw(_("Only Moderators or Administrators can reopen submitted sheets."), frappe.PermissionError)
	sheet = frappe.get_doc("Batch Attendance Sheet", name)
	if sheet.docstatus != 1:
		return _serialize_sheet(sheet)
	frappe.db.set_value(
		"Batch Attendance Sheet",
		name,
		{
			"docstatus": 0,
			"status": "Draft",
		},
		update_modified=True,
	)
	sheet.reload()
	return _serialize_sheet(sheet)


@frappe.whitelist()
def update_attendance_entry(entry_name: str, status: str | None = None, excuse_reason: str | None = None, notes: str | None = None):
	roles = _require_attendance_role()
	entry = frappe.get_doc("Batch Attendance Entry", entry_name)
	sheet = frappe.get_doc("Batch Attendance Sheet", entry.parent)
	_ensure_batch_access(sheet.batch, roles)

	if sheet.docstatus != 0:
		frappe.throw(_("You cannot edit a submitted attendance sheet. Please reopen it first."))

	if status:
		if status not in ATTENDANCE_STATUSES:
			frappe.throw(_("Invalid attendance status: {0}").format(status))
		entry.status = status

	if entry.status == "Excused":
		if not (excuse_reason or entry.excuse_reason):
			frappe.throw(_("Excuse reason is required when marking a student as Excused."))
		entry.excuse_reason = excuse_reason or entry.excuse_reason
	else:
		entry.excuse_reason = ""

	if notes is not None:
		entry.notes = notes

	entry.save(ignore_permissions=True)
	entry.reload()
	return {
		"name": entry.name,
		"status": entry.status,
		"excuse_reason": entry.excuse_reason,
		"notes": entry.notes,
	}


@frappe.whitelist()
def save_sheet(name: str, notes: str | None = None):
	roles = _require_attendance_role()
	sheet = frappe.get_doc("Batch Attendance Sheet", name)
	_ensure_batch_access(sheet.batch, roles)

	if sheet.docstatus != 0:
		frappe.throw(_("You cannot edit a submitted attendance sheet. Please reopen it first."))

	if notes is not None:
		sheet.notes = notes
		sheet.save(ignore_permissions=True)

	return _serialize_sheet(sheet, include_entries=False)
