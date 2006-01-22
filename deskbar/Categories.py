from gettext import gettext as _
from gettext import ngettext

class UnknownCategory (Exception):
	def __init__ (self, category_name, match):
		print "** Unknown Category '%s' requested by %s" % (category_name, match.__class__)


CATEGORIES = {
	"files"		: {	
		"name": _("Files"),
		"nest": lambda n: ngettext("%s more file", "%s more files", n), 
		"threshold": 3
	},
	"actions"	: {
		"name": _("Actions"),
		"nest": lambda n: ngettext("%s more action", "%s more actions", n), 
		"threshold": 1
	},
	"news"		: {
		"name": _("News"),
		"nest": lambda n: ngettext("%s more news item", "%s more news items", n), 
		"threshold": 3
	},
	"contacts"	: {
		"name": _("Contacts"),
		"nest": lambda n: ngettext("%s more contact", "%s more contacts", n), 
		"threshold": 3
	},
	"emails"	: {
		"name": _("Emails"),
		"nest": lambda n: ngettext("%s more email", "%s more emails", n), 
		"threshold": 3
	},
	"notes"	: {
		"name": _("Notes"),
		"nest": lambda n: ngettext("%s more note", "%s more notes", n), 
		"threshold": 3
	},
	"volumes"	: {
		"name": _("Volumes"),
		"nest": lambda n: ngettext("%s more volume", "%s more volumes", n), 
		"threshold": 3
	},
	"google"	: {
		"name": _("Google Search"),
		"nest": lambda n: ngettext("%s more online hit", "%s more online hits", n), 
		"threshold": 2
	},
	"calendar"	: {
		"name": _("Calendar"),
		"nest": lambda n: ngettext("%s more calendar item", "%s more calendar items", n), 
		"threshold": 1
	},
	"conversation"	: {
		"name": _("Conversation"),
		"nest": lambda n: ngettext("%s more conversation", "%s more conversations", n), 
		"threshold": 1
	},
	"web" : {
		"name": _("Web Browser"),
		"nest": lambda n: ngettext("%s more item", "%s more items", n), 
		"threshold": 5,
	},
	"programs" : {
		"name": _("Programs"),
		"nest": lambda n: ngettext("%s more program", "%s more programs", n), 
		"threshold": 3,
	},
	"debug" : {
		"name": _("Debug"),
		"nest": lambda n: ngettext("%s more debugging handler", "%s more debugging handlers", n), 
		"threshold": 2,
	},
}
