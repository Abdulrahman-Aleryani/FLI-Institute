# /home/abdulrahman/frappe-bench/apps/lms/lms/placement_test/doctype/placement_test/placement_test.py
import frappe
from frappe.model.document import Document

class PlacementTest(Document):
    def validate(self):
        self.validate_questions()
        self.validate_time_limit()
        
    def validate_questions(self):
        if not self.questions or len(self.questions) < 1:
            frappe.throw("Please add at least one question to the test.")
            
    def validate_time_limit(self):
        if self.time_limit < 0:
            frappe.throw("Time limit cannot be negative.")

def validate(doc, method=None):
    doc.validate()