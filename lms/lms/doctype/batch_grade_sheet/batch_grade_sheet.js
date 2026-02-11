const gradeFields = [
	"attendance",
	"participation",
	"assignments",
	"speaking",
	"writing",
	"communicative_competence",
	"final_oral",
	"exam",
];
const MAX_TOTAL = 100;

function recalcRowTotal(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!row) {
		return;
	}

	let total = 0;
	gradeFields.forEach((fieldname) => {
		const value = frappe.utils.flt(row[fieldname]);
		if (!isNaN(value)) {
			total += value;
		}
	});

	frappe.model.set_value(cdt, cdn, "total", frappe.utils.flt(total, 2));
	refreshTotalWarning(frm);
}

function refreshTotalWarning(frm) {
	const hasOverLimit = (frm.doc.grade_records || []).some((row) => frappe.utils.flt(row.total) > MAX_TOTAL);

	if (hasOverLimit) {
		frm.dashboard.set_headline(
			__("Some student totals exceed {0}. Please adjust before submitting.").format(MAX_TOTAL),
			"red",
		);
	} else {
		frm.dashboard.clear_headline();
	}
}

function recalcAllRows(frm) {
	(frm.doc.grade_records || []).forEach((row) => {
		let total = 0;
		gradeFields.forEach((fieldname) => {
			const value = frappe.utils.flt(row[fieldname]);
			if (!isNaN(value)) {
				total += value;
			}
		});
		row.total = frappe.utils.flt(total, 2);
	});

	frm.refresh_field("grade_records");
	refreshTotalWarning(frm);
}

async function populateStudentsIfNeeded(frm) {
	if (!frm.doc.batch) {
		return;
	}

	const existingStudents = new Set((frm.doc.grade_records || []).map((row) => row.student));
	if (existingStudents.size) {
		return;
	}

	frm.dashboard.set_headline(_("Loading enrolled students…"), "blue");

	const { message } = await frappe.call({
		method: "lms.lms.api.get_enrolled_students",
		args: { batch_name: frm.doc.batch },
		freeze: true,
		freeze_message: __("Fetching enrolled students"),
	});

	frm.dashboard.clear_headline();

	if (!Array.isArray(message) || !message.length) {
		return;
	}

	message.forEach((student) => {
		if (existingStudents.has(student.student)) {
			return;
		}

		const row = frm.add_child("grade_records");
		row.student = student.student;
		row.student_name = student.student_name;
	});

	frm.refresh_field("grade_records");
}

frappe.ui.form.on("Batch Grade Sheet", {
	onload(frm) {
		recalcAllRows(frm);
		populateStudentsIfNeeded(frm);
	},
	refresh(frm) {
		recalcAllRows(frm);
		populateStudentsIfNeeded(frm);
	},
	batch(frm) {
		populateStudentsIfNeeded(frm);
	},
});

const childEvents = {};
gradeFields.forEach((fieldname) => {
	childEvents[fieldname] = function (frm, cdt, cdn) {
		recalcRowTotal(frm, cdt, cdn);
	};
});

frappe.ui.form.on("Batch Grade Record", childEvents);
