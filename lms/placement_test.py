import frappe
from frappe import _
from frappe.utils import now_datetime
import json

@frappe.whitelist(allow_guest=True)
def get_context(context):
    context.title = _("Placement Test")
    context.no_cache = 1
    
    # Add any additional context variables here
    context.levels = [
        {
            'name': 'beginner',
            'title': _('Beginner'),
            'description': _('New to the language? Start here to build a strong foundation.'),
            'icon': 'seedling',
            'color': 'primary'
        },
        {
            'name': 'intermediate',
            'title': _('Intermediate'),
            'description': _('Have some knowledge? Test your skills and see where you stand.'),
            'icon': 'chart-line',
            'color': 'warning'
        },
        {
            'name': 'advanced',
            'title': _('Advanced'),
            'description': _('Confident in your skills? Challenge yourself with advanced questions.'),
            'icon': 'trophy',
            'color': 'success'
        }
    ]
    
    return context


@frappe.whitelist(allow_guest=True)
def list_tests():
    return frappe.get_all(
        "Placement Test",
        filters={"is_active": 1},
        fields=["name", "test_title", "description", "time_limit", "passing_score"],
        order_by="modified desc",
        ignore_permissions=True,
    )


@frappe.whitelist(allow_guest=True)
def get_test_data(test_id):
    test = frappe.get_doc("Placement Test", test_id)

    questions = []
    for row in (test.questions or []):
        if not row.question:
            continue

        q = frappe.get_doc("Placement Test Question", row.question)
        questions.append(
            {
                "name": q.name,
                "question": q.question,
                "question_type": q.question_type,
                "explanation": q.explanation,
                "options": [
                    {
                        "option_text": opt.option_text,
                    }
                    for opt in (q.options or [])
                ],
            }
        )

    return {
        "name": test.name,
        "test_title": test.test_title,
        "description": test.description,
        "time_limit": test.time_limit,
        "passing_score": test.passing_score,
        "questions": questions,
    }



@frappe.whitelist(allow_guest=True)
def create_test_submission(test_id, full_name, date_of_birth, email, phone, interview_time=None):
    submission = frappe.new_doc("Placement Test Submission")
    submission.placement_test = test_id
    submission.full_name = full_name
    submission.date_of_birth = date_of_birth
    submission.email = email
    submission.phone_number = phone
    if interview_time:
        submission.interview_time = interview_time
    submission.start_time = now_datetime()
    submission.status = "In Progress"

    submission.insert(ignore_permissions=True)
    return submission.name


def _is_answer_correct(question_doc, selected_indices):
    correct_indices = [i for i, opt in enumerate(question_doc.options or []) if opt.is_correct]

    if question_doc.question_type == "Single Answer":
        return len(selected_indices) == 1 and selected_indices[0] in correct_indices

    return set(selected_indices) == set(correct_indices)


@frappe.whitelist(allow_guest=True)
def submit_test_answers(submission_id, answers, full_name=None, date_of_birth=None, email=None, phone=None):
    submission = frappe.get_doc("Placement Test Submission", submission_id)
    test = frappe.get_doc("Placement Test", submission.placement_test)

    # Update participant info if provided (handles cases where page reload loses state)
    if full_name:
        submission.full_name = full_name
    if date_of_birth:
        submission.date_of_birth = date_of_birth
    if email:
        submission.email = email
    if phone:
        submission.phone_number = phone

    if isinstance(answers, str):
        try:
            answers = json.loads(answers)
        except Exception:
            answers = []

    if not isinstance(answers, list):
        answers = []

    submission.answers = []
    incorrect_answers = []
    correct_count = 0

    for item in (answers or []):
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except Exception:
                item = {}

        if not isinstance(item, dict):
            item = {}

        question_name = item.get("question")
        selected_options_raw = item.get("selected_options")

        if not question_name:
            continue

        try:
            selected_indices = json.loads(selected_options_raw or "[]")
            if not isinstance(selected_indices, list):
                selected_indices = []
        except Exception:
            selected_indices = []

        q = frappe.get_doc("Placement Test Question", question_name)
        is_correct = _is_answer_correct(q, selected_indices)

        submission.append(
            "answers",
            {
                "question": q.name,
                "selected_options": json.dumps(selected_indices),
                "is_correct": 1 if is_correct else 0,
            },
        )

        if is_correct:
            correct_count += 1
        else:
            incorrect_answers.append(
                {
                    "question": {
                        "name": q.name,
                        "question": q.question,
                        "question_type": q.question_type,
                        "explanation": q.explanation,
                        "options": [
                            {
                                "option_text": opt.option_text,
                                "is_correct": 1 if opt.is_correct else 0,
                            }
                            for opt in (q.options or [])
                        ],
                    },
                    "user_answer": selected_indices,
                }
            )

    submission.save(ignore_permissions=True)

    total_questions = len(submission.answers or [])
    score = submission.score or 0
    passed = bool(submission.passed)

    return {
        "total_questions": total_questions,
        "correct_answers": correct_count,
        "score": score,
        "passed": passed,
        "passing_score": test.passing_score,
        "incorrect_answers": incorrect_answers,
    }
