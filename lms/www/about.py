import frappe

sitemap = 1

def get_context(context):
	context.doc = frappe.get_cached_doc("About Us Settings")
	if getattr(context.doc, "is_disabled", False):
		frappe.local.flags.redirect_location = "/404"
		raise frappe.Redirect
	return context
