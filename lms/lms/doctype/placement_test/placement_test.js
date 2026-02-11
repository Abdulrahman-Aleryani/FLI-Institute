// /home/abdulrahman/frappe-bench/apps/lms/lms/placement_test/doctype/placement_test/placement_test.js
const ensureQuestionDropdownHeight = () => {
	const STYLE_ID = "placement-test-question-dropdown-style";
	if (document.getElementById(STYLE_ID)) {
		return;
	}
	const style = document.createElement("style");
	style.id = STYLE_ID;
	style.innerHTML = `
		body[data-route^="Form/Placement Test"] .grid-row-open .awesomplete ul,
		body[data-route^="Form/Placement Test"] .grid-row-open .awesomplete > ul {
			max-height: 520px !important;
			min-height: 260px !important;
			overflow-y: auto;
			font-size: 0.95rem;
		}
		body[data-route^="Form/Placement Test"] .grid-row-open .grid-form {
			min-height: 420px;
		}
		body[data-route^="Form/Placement Test"] .grid-row-open .form-column {
			max-height: 420px;
		}
	`;
	document.head.appendChild(style);
};

const setQuestionQuery = (frm) => {
	if (!frm) {
		return;
	}

	frm.set_query("question", "questions", function () {
		return {
			filters: {},
			page_length: 0,
			limit_page_length: 1000,
		};
	});
};

frappe.ui.form.on("Placement Test", {
	onload(frm) {
		ensureQuestionDropdownHeight();
		setQuestionQuery(frm);
	},

	refresh(frm) {
		ensureQuestionDropdownHeight();
		setQuestionQuery(frm);
	},

	time_limit(frm) {
		if (frm.doc.time_limit < 0) {
			frappe.msgprint(__("Time limit cannot be negative."));
			frm.set_value("time_limit", 0);
		}
	},
});