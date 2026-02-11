import frappe
from frappe.tests import UnitTestCase

from lms.lms.doctype.batch_grade_sheet.batch_grade_sheet import (
	MAX_TOTAL,
	GRADE_COMPONENTS,
	recalculate_row_total,
)


class TestBatchGradeSheet(UnitTestCase):
	def test_recalculate_row_total_enforces_limits(self):
		row = frappe._dict(
			{
				"attendance": 10,
				"participation": 10,
				"assignments": 10,
				"speaking": 10,
				"writing": 15,
				"communicative_competence": 10,
				"final_oral": 10,
				"exam": 25,
			}
		)

		total = recalculate_row_total(row, enforce_limits=True)
		self.assertEqual(total, MAX_TOTAL)

		row.exam = 30
		with self.assertRaises(frappe.ValidationError):
			recalculate_row_total(row, enforce_limits=True)

	def test_grade_components_max_total(self):
		self.assertEqual(sum(component["max"] for component in GRADE_COMPONENTS.values()), MAX_TOTAL)
