import os, sys, cgi
import gobject,gtk, gnome.ui, gnomevfs
import deskbar, deskbar.handler, deskbar.handler_utils
from gettext import gettext as _
from os.path import exists

MAX_RESULTS = 2 # per handler

def _check_requirements():
	try:
		import deskbar.beagle
		return (True, None)
	except:
		return (False, "Could not load deskbar.beagle, deskbar has been compiled without beagle support")
	
HANDLERS = {
	"BeagleLiveHandler" : {
		"name": _("Beagle Live"),
		"description": _("Search all of your documents (using Beagle), as you type"),
		# We must see how to detect properly beagle, for now it will fail on creating a new client
		# when beagle is not available.
		"requirements" : _check_requirements,
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
#
# Note:
#  The templates are a tuple of strings which should be tested in order to retreive the beagle property

TYPES = {
	"Contact"	: {
		"name"	: ("fixme:FileAs",),
		"action": "evolution",
		"icon"	: "stock_contact",
		"description": _("Addressbook entry for %s") % "<b>%(name)s</b>"
		},
	
	"MailMessage" 	: {
		"name"	:("dc:title", "parent:dc:title"),
		"action": "evolution",
		"icon"	: "stock_mail",
		"extra": {"sender":("fixme:from_name", "parent:fixme:from_name")},
		#translators: First %s is mail sender, second %s is mail subject.
		"description": _("View email from %s: %s") % ("<i>%(sender)s</i>", "<b>%(name)s</b>")
		},
	"File" 		: {
		"name"	: ("beagle:ExactFilename",), 
		"action": "gnome-open",
		"icon"	: "stock_new",
		#translators: This is a file.
		"description": _("Open %s") % "<b>%(name)s</b>"
		},
	"FeedItem"	: {
		"name"	: ("dc:title",),
		"action": "gnome-open",
		"icon"	: "stock_news",
		"description": _("Open news item %s") % "<b>%(name)s</b>"
		},
	"Note"		: {
		"name"	: ("dc:title",),
		"action": "tomboy",
		"action_args": "--open-note",
		"icon"	:"stock_notes",
		"description": _("Open note %s") % "<b>%(name)s</b>"
		},
	"IMLog"		: {
		"name"	: ("fixme:speakingto",),
		"action": "beagle-imlogviewer",
		"icon"	: "im",
		"description": _("View conversation with %s") % "<b>%(name)s</b>"
		},
	"Calendar"	: {
		"name"	: ("fixme:summary",),
		"action": "evolution",
		"icon"	: "stock_calendar",
		"description": _("View calendar %s") % "<b>%(name)s</b>"
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
		#
		# There's a nasty bug in gnome.ui forcing us to leave out file thumbnailing atm.
		# http://bugzilla.gnome.org/show_bug.cgi?id=319549
		#
		
		#if result["type"] == "File":
		#	try:
		#		icon = deskbar.handler_utils.load_icon_for_file(result["uri"])
		#		if icon:
		#			deskbar.handler.Match.__init__ (self, handler, result["name"], icon)
		#		else:
		#			raise Exception()
		#	except Exception:
		#		deskbar.handler.Match.__init__ (self, handler, result["name"], handler.ICONS["File"])
		#		print >> sys.stderr, "BeagleLive: Failed to load icon for file %s" % result["uri"]
		#
		#else:
		#	# We are not a file. Just use an icon from the ICON table
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
		
		if action == "beagle-imlogviewer":
			# Strip the uti descriptor, because imlogviewer takes a local path
			args.append (gnomevfs.get_local_path_from_uri(self.__result["uri"]))
		else:
			args.append (self.__result["uri"])

		print "BeagleLive spawning:", action, args
		gobject.spawn_async(args, flags=gobject.SPAWN_SEARCH_PATH)
	
	def get_hash(self, text=None):
		if "uri" in self.__result:
			return self.__result["uri"]
		
class BeagleLiveHandler(deskbar.handler.SignallingHandler):
	def __init__(self):
		deskbar.handler.SignallingHandler.__init__(self, "best")
		self.counter = {}
		
	def initialize (self):
		import deskbar.beagle
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
		import deskbar.beagle
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
				"uri":  hit.get_uri(),
				"type": hit.get_type(),
			}
			for prop in hit_type["name"]:
				name = hit.get_property(prop)
				if name != None:
					result["name"] = cgi.escape(name)
					break
			else:
				#translators: This is used for unknown values returned by beagle
				#translators: for example unknown email sender, or unknown note title
				result["name"] = _("?")
				
			if "extra" in hit_type:
				for prop, keys in hit_type["extra"].items():
					for key in keys:
						val = hit.get_property(key)
						if val != None:
							result[prop] = cgi.escape(val)
							break
					else:
						result[prop] = None
			
			hit_matches.append(BeagleLiveMatch(self, result))
			
			self.counter[qstring][hit.get_type()] = self.counter[qstring][hit.get_type()] +1
			
		self.emit_query_ready(hit_matches, qstring)
