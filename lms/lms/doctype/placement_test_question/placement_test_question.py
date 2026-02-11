# /home/abdulrahman/frappe-bench/apps/lms/lms/placement_test/doctype/placement_test_question/placement_test_question.py
import frappe
from frappe.model.document import Document

class PlacementTestQuestion(Document):
    def validate(self):
        self.validate_options()
        
    def validate_options(self):
        if not self.options or len(self.options) < 2:
            frappe.throw("Please add at least 2 options for the question.")
            
        # Ensure at least one correct answer is selected
        correct_answers = [option for option in self.options if option.get("is_correct")]
        if not correct_answers:
            frappe.throw("Please mark at least one option as correct.")

def validate(doc, method=None):
    doc.validate()