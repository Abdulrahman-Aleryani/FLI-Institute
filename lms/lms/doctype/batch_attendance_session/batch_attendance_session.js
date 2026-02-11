frappe.ui.form.on("Batch Attendance Session", {
	batch(frm) {
		if (!frm.doc.batch) {
			return;
		}

		frappe.call({
			method: "lms.lms.doctype.batch_attendance_session.batch_attendance_session.get_enrollments_for_batch",
			args: { batch: frm.doc.batch },
			callback: ({ message }) => {
				if (!Array.isArray(message)) {
					return;
				}

				frm.clear_table("attendance_records");

				message.forEach((enrollment) => {
					const row = frm.add_child("attendance_records");
					row.enrollment = enrollment.name;
					row.student = enrollment.member;
					row.student_name = enrollment.member_name;
					row.status = "Absent";
				});

				frm.refresh_field("attendance_records");
			},
		});
	},
});
