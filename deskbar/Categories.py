from gettext import gettext as _
from gettext import ngettext

class UnknownCategory (Exception):
	def __init__ (self, category_name, match):
		print "** Unknown Category '%s' requested by %s" % (category_name, match.__class__)


_generic_nest = lambda n: ngettext("%s more result", "%s more results", n)

CATEGORIES = {
	# Special categories
	"default"	: {	
		"name": _("Uncategorized"),
		"nest": _generic_nest,
		"threshold": 5
	},
	"history" : {
		"name": _("History"),
		"nest": _generic_nest, 
		"threshold": 5
	},
	"debug" : {
		"name": "Debug",
		"nest": _generic_nest, 
		"threshold": 5
	},
	
	# Standard handlers
	"documents"	: {	
		"name": _("Documents"),
		"nest": lambda n: ngettext("%s more document", "%s more documents", n), 
		"threshold": 5
	},
	"files"	: {	
		"name": _("Files"),
		"nest": lambda n: ngettext("%s more file", "%s more files", n), 
		"threshold": 5
	},
	"people"	: {
		"name": _("People"),
		"nest": _generic_nest, 
		"threshold": 5
	},
	"places"	: {	
		"name": _("Places"),
		"nest": lambda n: ngettext("%s more place", "%s more places", n), 
		"threshold": 5
	},
	"actions"	: {	
		"name": _("Actions"),
		"nest": lambda n: ngettext("%s more action", "%s more actions", n), 
		"threshold": 5
	},
	"web"	: {	
		"name": _("Web"),
		"nest": _generic_nest, 
		"threshold": 5,
	},
	"websearch"	: {	
		"name": _("Web Search"),
		"nest": _generic_nest,
	},
	
}
