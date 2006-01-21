from gettext import gettext as _

class UnknownCategory (Exception):
	def __init__ (self, category_name, match):
		print "** Unknown Category '%s' requested by %s" % (category_name, match.__class__)


CATEGORIES = {
	"files"		: {	
		"name": _("Files"),
		"nest": _("<b>%(count)s</b> <i>more files</i>"), 
		"threshold": 3
	},
	"actions"	: {
		"name": _("Actions"),
		"nest": _("<b>%(count)s</b> <i>more actions</i>"), 
		"threshold": 1
	},
	"news"		: {
		"name": _("News"),
		"nest": _("<b>%(count)s</b> <i>more news items</i>"), 
		"threshold": 3
	},
	"contacts"	: {
		"name": _("Contacts"),
		"nest": _("<b>%(count)s</b> <i>more contacts</i>"),
		"threshold": 3
	},
	"emails"	: {
		"name": _("Emails"),
		"nest": _("<b>%(count)s</b> <i>more emails</i>"), 
		"threshold": 3
	},
	"notes"	: {
		"name": _("Notes"),
		"nest": _("<b>%(count)s</b> <i>more notes</i>"), 
		"threshold": 3
	},
	"volumes"	: {
		"name": _("Volumes"),
		"nest": _("<b>%(count)s</b> <i>more volumes</i>"), 
		"threshold": 3
	},
	"google"	: {
		"name": _("Google Search"),
		"nest": _("<b>%(count)s</b> <i>more online hits</i>"), 
		"threshold": 2
	},
	"calendar"	: {
		"name": _("Calendar"),
		"nest": _("<b>%(count)s</b> <i>more calendar items</i>"), 
		"threshold": 1
	},
	"conversation"	: {
		"name": _("Conversation"),
		"nest": _("<b>%(count)s</b> <i>more conversations</i>"), 
		"threshold": 1
	},
	"web" : {
		"name":_("Web Browser"),
		"nest":_("<b>%(count)s</b> <i>more items</i>"),
		"threshold":5,
	},
	"programs" : {
		"name":_("Programs"),
		"nest":_("<b>%(count)s</b> <i>more programs</i>"),
		"threshold":3,
	},
	"debug" : {
		"name":_("Debug"),
		"nest":_("<b>%(count)s</b> <i>more debugging handlers</i>"),
		"threshold":2,
	},
}
