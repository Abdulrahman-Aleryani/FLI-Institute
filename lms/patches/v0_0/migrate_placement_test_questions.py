"""
Migrate embedded Placement Test Questions to standalone DocType
This patch converts questions stored as child table rows into standalone documents
and updates Placement Test records to reference them via the new child table.
"""
import frappe
from frappe import _

def execute():
    """Migrate existing embedded questions to standalone Placement Test Question docs"""
    
    # Get all Placement Test records with embedded questions
    tests = frappe.get_all("Placement Test", fields=["name"])
    
    if not tests:
        frappe.logger().info("No Placement Tests found to migrate")
        return
    
    migrated_count = 0
    
    for test_record in tests:
        test = frappe.get_doc("Placement Test", test_record.name)
        
        if not test.questions:
            continue
        
        # Process each embedded question
        new_questions = []
        for idx, question_row in enumerate(test.questions):
            try:
                # Check if question already exists as standalone
                existing_question = frappe.db.get_value(
                    "Placement Test Question",
                    {"question": question_row.question},
                    "name"
                )
                
                if existing_question:
                    # Question already exists, just reference it
                    new_questions.append({
                        "question": existing_question
                    })
                else:
                    # Create new standalone question from embedded data
                    new_question = frappe.get_doc({
                        "doctype": "Placement Test Question",
                        "question": question_row.question,
                        "question_type": question_row.question_type,
                        "explanation": question_row.get("explanation", ""),
                        "marks": question_row.get("marks", 1),
                        "options": question_row.get("options", [])
                    })
                    new_question.insert(ignore_permissions=True)
                    migrated_count += 1
                    
                    # Reference the new standalone question
                    new_questions.append({
                        "question": new_question.name
                    })
            except Exception as e:
                frappe.logger().error(
                    f"Failed to migrate question {idx} in test {test.name}: {str(e)}"
                )
                continue
        
        # Update test with new question references
        if new_questions:
            test.questions = new_questions
            test.save(ignore_permissions=True)
    
    frappe.logger().info(f"Migration complete: {migrated_count} questions created")
