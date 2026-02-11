# /home/abdulrahman/frappe-bench/apps/lms/lms/placement_test/doctype/placement_test_question_answer/placement_test_question_answer.py
import frappe
from frappe.model.document import Document
import json

class PlacementTestQuestionAnswer(Document):
    def validate(self):
        self.validate_selected_options()
        
    def validate_selected_options(self):
        if not self.selected_options:
            return
            
        try:
            selected = json.loads(self.selected_options)
            if not isinstance(selected, list):
                frappe.throw("Selected options must be a valid JSON array")
        except:
            frappe.throw("Invalid format for selected options. Must be a valid JSON array")