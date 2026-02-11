# /home/abdulrahman/frappe-bench/apps/lms/lms/placement_test/doctype/placement_test_submission/placement_test_submission.py
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, format_duration, nowdate
import json
from datetime import datetime, timedelta

class PlacementTestSubmission(Document):
    def before_save(self):
        self.calculate_score()
        
    def calculate_score(self):
        if not self.answers:
            return
            
        total_questions = len(self.answers)
        if total_questions == 0:
            return
            
        correct_answers = 0
        
        for answer in self.answers:
            if answer.is_correct:
                correct_answers += 1
                
        self.score = (correct_answers / total_questions) * 100
        self.passed = self.score >= frappe.db.get_value("Placement Test", self.placement_test, "passing_score")
        
    def on_submit(self):
        self.status = "Completed"
        self.end_time = now_datetime()
        self.save()
        
    def before_insert(self):
        self.start_time = now_datetime()
        self.status = "In Progress"
        
        # Set expiration time if test has time limit
        test = frappe.get_doc("Placement Test", self.placement_test)
        if test.time_limit > 0:
            self.expiry_time = (get_datetime(self.start_time) + 
                              timedelta(minutes=test.time_limit)).strftime("%Y-%m-%d %H:%M:%S")


def before_insert(doc, method=None):
    doc.before_insert()


def before_save(doc, method=None):
    doc.before_save()


def on_submit(doc, method=None):
    if method:
        getattr(doc, method)()
    else:
        doc.on_submit()