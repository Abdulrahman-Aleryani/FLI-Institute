from . import __version__ as app_version

# App Configuration
app_name = "frappe_lms"
app_title = "Frappe LMS"
app_publisher = "Frappe"
app_description = "Frappe LMS App"
app_icon_url = "/assets/lms/images/lms-logo.png"
app_icon_title = "Learning"
app_icon_route = "/lms"
app_color = "grey"
app_email = "jannat@frappe.io"
app_license = "AGPL"

# Includes in <head>
# ------------------
# include js, css files in header of desk.html
# app_include_css = "/assets/lms/css/lms.css"
# app_include_js = "/assets/lms/js/lms.js"

# include js, css files in header of web template
web_include_css = [
    "lms.bundle.css",
    "/assets/lms/css/placement_test.css"
]

web_include_js = [
    "/assets/lms/js/placement_test.js"
]

# include custom scss in every website theme (without file extension ".scss")
website_theme_scss = "lms/public/scss/website"

# Home Pages
# ----------
home_page = "home"
# home_page = "home"  # Commented out to allow Website Settings to control home page

# Installation
# ------------
after_install = "lms.install.after_install"
after_sync = "lms.install.after_sync"
before_uninstall = "lms.install.before_uninstall"
setup_wizard_requires = "assets/lms/js/setup_wizard.js"
after_migrate = [
    "lms.sqlite.build_index_in_background",
]

# DocType Class
# -------------
override_doctype_class = {
    "Web Template": "lms.overrides.web_template.CustomWebTemplate",
}

# Document Events
# ---------------
doc_events = {
    "Placement Test": {
        "validate": "lms.lms.doctype.placement_test.placement_test.validate"
    },
    "Placement Test Question": {
        "validate": "lms.lms.doctype.placement_test_question.placement_test_question.validate"
    },
    "Placement Test Submission": {
        "before_save": "lms.lms.doctype.placement_test_submission.placement_test_submission.before_save",
        "on_submit": "lms.lms.doctype.placement_test_submission.placement_test_submission.on_submit",
        "before_insert": "lms.lms.doctype.placement_test_submission.placement_test_submission.before_insert"
    }
}

# Scheduled Tasks
# --------------
scheduler_events = {
    "all": [
        "lms.sqlite.build_index_in_background",
    ],
    "hourly": [
        "lms.lms.doctype.lms_certificate_request.lms_certificate_request.schedule_evals",
        "lms.lms.api.update_course_statistics",
        "lms.lms.doctype.lms_certificate_request.lms_certificate_request.mark_eval_as_completed",
        "lms.lms.doctype.lms_live_class.lms_live_class.update_attendance",
    ],
    "daily": [
        "lms.job.doctype.job_opportunity.job_opportunity.update_job_openings",
        "lms.lms.doctype.lms_payment.lms_payment.send_payment_reminder",
        "lms.lms.doctype.lms_batch.lms_batch.send_batch_start_reminder",
        "lms.lms.doctype.lms_live_class.lms_live_class.send_live_class_reminder",
    ],
}

# Fixtures
fixtures = [
    "Custom Field", 
    "Function", 
    "Industry", 
    "LMS Category",
    {
        "dt": "Role",
        "filters": [["name", "in", ["Placement Test Manager", "Placement Test Taker"]]]
    },
    {
        "dt": "Custom Field",
        "filters": [["dt", "in", ["Placement Test", "Placement Test Question", "Placement Test Submission"]]]
    }
]

# Website Routes and Redirections
# ------------------------------
website_route_rules = [
    {"from_route": "/lms", "to_route": "lms"},
    {"from_route": "/lms/<path:app_path>", "to_route": "lms"},
    {"from_route": "/placement-test", "to_route": "placement_test"},
    {"from_route": "/placement-test/<level>", "to_route": "placement_test"},
    {"from_route": "/placement-test/<test_id>", "to_route": "placement_test"},
    {"from_route": "/placement-test/submit", "to_route": "placement_test_submit"},
    {"from_route": "/placement-test/result/<submission_id>", "to_route": "placement_test_result"}
]

website_routes = [
    {
        'from_route': '/placement-test',
        'to_route': 'placement_test',
        'type': 'page',
        'template': 'templates/pages/placement_test.html',
        'title': 'Placement Test',
        'description': 'Take a placement test to find the right course for your level'
    },
    {
        'from_route': '/placement-test/<level>',
        'to_route': 'placement_test',
        'type': 'page',
        'template': 'templates/pages/placement_test.html',
        'title': 'Placement Test',
        'description': 'Take a placement test to find the right course for your level'
    },
]

website_redirects = [
    {"source": "/update-profile", "target": "/edit-profile"},
    {"source": "/courses", "target": "/lms/courses"},
    {"source": r"^/courses/.*$", "target": "/lms/courses"},
    {"source": "/batches", "target": "/lms/batches"},
    {"source": r"/batches/(.*)", "target": "/lms/batches", "match_with_query_string": True},
    {"source": "/job-openings", "target": "/lms/job-openings"},
    {"source": r"/job-openings/(.*)", "target": "/lms/job-openings", "match_with_query_string": True},
    {"source": "/statistics", "target": "/lms/statistics"},
]

# Website Context and Templates
# ----------------------------
website_context = {
    "favicon": "/assets/lms/images/favicon.ico",
    "splash_image": "/assets/lms/images/splash.png"
}

update_website_context = [
    "lms.widgets.update_website_context",
]

# Jinja Environment
# ----------------
jinja = {
    "methods": [
        "lms.lms.utils.get_tags",
        "lms.lms.utils.get_lesson_count",
        "lms.lms.utils.get_instructors",
        "lms.lms.utils.get_lesson_index",
        "lms.lms.utils.get_lesson_url",
        "lms.lms.utils.is_instructor",
        "lms.lms.utils.get_palette",
    ],
    "filters": [],
}

# Authentication
# --------------
profile_url_prefix = "/users/"
signup_form_template = "lms.plugins.show_custom_signup"
on_login = "lms.lms.user.on_login"
get_site_info = "lms.activation.get_site_info"

# App Integration
# --------------
add_to_apps_screen = [
    {
        "name": "lms",
        "logo": "/assets/lms/frontend/learning.svg",
        "title": "FLi",
        "route": "/lms",
        "has_permission": "lms.lms.api.check_app_permission",
    }
]

# Search
# ------
sqlite_search = ["lms.sqlite.LearningSearch"]

# Desk Configuration
# -----------------
desk_icons = {
    "LMS Settings": "book-open",
    "Course": "book",
    "Lesson": "file-text",
    "Quiz": "help-circle",
    "LMS Batch": "users",
    "Placement Test": "list-check",
}

desk_links = {
    "LMS": {
        "label": "LMS",
        "items": [
            "Course",
            "Lesson",
            "Quiz",
            "LMS Batch",
            "Placement Test",
            "LMS Settings"
        ]
    }
}

# Markdown Macros for Lessons
lms_markdown_macro_renderers = {
    "Exercise": "lms.plugins.exercise_renderer",
    "Quiz": "lms.plugins.quiz_renderer",
    "YouTubeVideo": "lms.plugins.youtube_video_renderer",
    "Video": "lms.plugins.video_renderer",
    "Assignment": "lms.plugins.assignment_renderer",
    "Embed": "lms.plugins.embed_renderer",
    "Audio": "lms.plugins.audio_renderer",
    "PDF": "lms.plugins.pdf_renderer",
}

# Page Renderers
page_renderer = [
    "lms.page_renderers.SCORMRenderer",
]

# Permissions
has_website_permission = {
    "LMS Certificate Evaluation": "lms.lms.doctype.lms_certificate_evaluation.lms_certificate_evaluation.has_website_permission",
    "LMS Certificate": "lms.lms.doctype.lms_certificate.lms_certificate.has_website_permission",
}

# Whitelisted Methods
override_whitelisted_methods = {
    # "frappe.desk.search.get_names_for_mentions": "lms.lms.utils.get_names_for_mentions",
}
