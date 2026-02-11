import frappe
from frappe import _

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
