import os, sys, cgi
import gtk, gnome.ui
import deskbar, deskbar.handler, deskbar.beagle, deskbar.handler_utils
from gettext import gettext as _
from os.path import exists

MAX_RESULTS = 2 # per handler

HANDLERS = {
	"BeagleLiveHandler" : {
		"name": _("Live Beagle Queries"),
		"description": _("Query Beagle automatically as you type."),
		# Better detection here ?
		"requirements" : lambda: (exists("/usr/share/applications/best.desktop"), "Beagle was not detected on your system"),
	}
}

# The TYPES dict contains Beagle HitTypes as keys with
# templates for the valid fields.
#
# A Hit Type consists of:
#	"name"		: Template used to find a user-displayable name
#	"action"	: Command to execute
#	"icon"		: The *name* of the icon to be sued for this type. Set to None for no icon.
#	"description"	: A short description. %(*)s may refer to *=name,uri,action or any field in "extra" (see below)
#
# Optionally:
#	"extra"	: A dict containing key:template pairs to search for. You can use %(key)s in "description".

TYPES = {
	"Contact"	: {
		"name"	: "fixme:FileAs",
		"action": "evolution",
		"icon"	: "stock_contact",
		"description": _("Addressbook entry for <b>%(name)s</b>")
		},
	
	"MailMessage" 	: {
		"name"	:"dc:title",
		"action": "evolution",
		"icon"	: "stock_mail",
		"extra": {"sender":"from_name"},
		"description": _("View email from <i>%(sender)s</i>: <b>%(name)s</b>")
		},
	"File" 		: {
		"name"	: "beagle:ExactFilename", 
		"action": "gnome-open",
		"icon"	: None,
		"description": _("Open <b>%(name)s</b>")
		},
	"FeedItem"	: {
		"name"	:"dc:title",
		"action": "gnome-open",
		"icon"	: "stock_news",
		"description": _("Open news item <b>%(name)s</b>"),
		},
	"Note"		: {
		"name"	: "dc:title",
		"action": "tomboy",
		"action_args": "--open-note",
		"icon"	:"stock_notes",
		"description": _("Open note <b>%(name)s</b>")
		},
	"IMLog"		: {
		"name"	: "fixme:speakingto",
		"action": "beagle-imlogviewer",
		"icon"	: "im",
		"description": _("View conversation with <b>%(name)s</b>")
		},
	"Calendar"	: {
		"name"	: "fixme:summary",
		"action": "evolution",
		"icon"	: "stock_calendar",
		"description": _("View calendar <b>%s(name)</b>")
		},
}

class BeagleLiveMatch (deskbar.handler.Match):
	def __init__(self, handler, result):
		"""
		result: a dict containing:
			"name" : a name sensible to display for this match
			"uri": the uri of the match as provided by the beagled 'Uri: '-field
			"type": One of the types listed in the TYPES dict

		-- and optionally extra fields as provided by the corresponding entry in TYPES.
		Fx. "MailMessage". has an extra "sender" entry.
		"""
		if result["type"] == "File":
			try:
				icon = deskbar.handler_utils.load_icon_for_file(result["uri"])
				if icon:
					deskbar.handler.Match.__init__ (self, handler, result["name"], icon)
				else:
					raise Exception()
			except Exception:
				deskbar.handler.Match.__init__ (self, handler, result["name"], handler.ICONS["File"])
				print >> sys.stderr, "BeagleLive: Failed to load icon for file %s" % result["uri"]

		else:
			# We are not a file. Just use an icon from the ICON table
			deskbar.handler.Match.__init__ (self, handler, result["name"], handler.ICONS[result["type"]])
		
		self.__result = result
	
	def get_name (self, text=None):
		# We use the result dict itself to look up words
		return self.__result
	
	def get_verb(self):
		# Fetch the "description" template from TYPES
		return TYPES[self.__result["type"]]["description"]
		
	def action(self, text=None):
	
		# Retrieve the associated action
		action = TYPES[self.__result["type"]]["action"]
		args = [action]

		# If the result requires additional arguments
		# prepend them to args.
		if TYPES[self.__result["type"]].has_key ("action_args"):
			args.append(TYPES[self.__result["type"]]["action_args"])
		
		# Gross hack, imlogviewer doesn't take URI as args, but a filename
		if action == "beagle-imlogviewer":
			# Strip the file://
			args.append (self.__result["uri"][7:])
		else:
			args.append (self.__result["uri"])

		print "BeagleLive spawning:", action, args
		os.spawnvp(os.P_NOWAIT, action, args)
		
class BeagleLiveHandler(deskbar.handler.SignallingHandler):
	def __init__(self):
		deskbar.handler.SignallingHandler.__init__(self, "best")
		self.counter = {}
		
	def initialize (self):
		self.beagle = deskbar.beagle.Client()
		self.ICONS = self.__load_icons()
	
	def __load_icons (self):
		res = {}
		for t in TYPES.iterkeys():
			icon_file = TYPES[t]["icon"]
			if not icon_file: continue
			res[t] = deskbar.handler_utils.load_icon(icon_file)
		return res
		
	def query (self, qstring, qmax=5):
		beagle_query = deskbar.beagle.Query()
		beagle_query.add_text(qstring)
		beagle_query.connect("hits-added", self.hits_added, qstring, MAX_RESULTS)
		self.beagle.send_request_async(beagle_query)
		self.counter[qstring] = {}
		
	def hits_added(self, query, response, qstring, qmax):
		hit_matches = []
		for hit in response.get_hits():
			if not hit.get_type() in self.counter[qstring]:
				self.counter[qstring][hit.get_type()] = 0

			if self.counter[qstring][hit.get_type()] >= qmax:
				continue
				
			hit_type = TYPES[hit.get_type()]
			result = {
				"name": hit.get_property(hit_type["name"]),
				"uri":  hit.get_uri(),
				"type": hit.get_type(),
			}
			if result["name"] != None:
				result["name"] = cgi.escape(result["name"])
			else:
				result["name"] = _("?")
				
			if "extra" in hit_type:
				for prop, key in hit_type["extra"].items():
					val = hit.get_property(key)
					if val != None:
						result[prop] = cgi.escape(val)
					else:
						result[prop] = val
			
			hit_matches.append(BeagleLiveMatch(self, result))
			
			self.counter[qstring][hit.get_type()] = self.counter[qstring][hit.get_type()] +1
			
		self.emit_query_ready(hit_matches, qstring)
