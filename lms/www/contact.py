import frappe
from frappe import _

no_cache = 1

def get_context(context):
    contact_settings = frappe.get_single("Contact Us Settings")
    
    context.heading = contact_settings.heading or _("Contact Us")
    context.introduction = contact_settings.introduction
    context.query_options = contact_settings.query_options
    context.address_title = contact_settings.address_title
    context.address_line1 = contact_settings.address_line1
    context.address_line2 = contact_settings.address_line2
    context.city = contact_settings.city
    context.state = contact_settings.state
    context.pincode = contact_settings.pincode
    context.country = contact_settings.country
    context.phone = contact_settings.phone
    context.email_id = contact_settings.email_id
    context.skype = contact_settings.skype
    
    return context
