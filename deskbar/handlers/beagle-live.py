import os, sys, cgi, re
import gobject,gtk, gnome.ui, gnomevfs
import deskbar, deskbar.Handler, deskbar.Utils
from gettext import gettext as _
from os.path import exists

MAX_RESULTS = 20 # per handler

def _check_requirements():
	try:
		import deskbar
		import beagle
		return (deskbar.Handler.HANDLER_IS_HAPPY, None, None)
	except:
		return (deskbar.Handler.HANDLER_IS_NOT_APPLICABLE, "Could not load beagle, libbeagle has been compiled without python bindings", None)
	
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
		"action": "evolution %(uri)s",
		"icon"	: "stock_contact",
		"description": _("Addressbook entry for %s") % "<b>%(name)s</b>",
		"category": "people",
		},
	
	"MailMessage" 	: {
		"name"	:("dc:title", "parent:dc:title"),
		"action": "evolution %(uri)s",
		"icon"	: "stock_mail",
		"extra": {"sender":("fixme:from_name", "parent:fixme:from_name")},
		#translators: First %s is mail sender, second %s is mail subject.
		"description": _("View email from <i>%(sender)s</i>: <b>%(name)s</b>"),
		"snippet": True,
		"category": "documents",
		},
	"File" 		: {
		"name"	: ("beagle:ExactFilename",), 
		"action": "gnome-open %(uri)s",
		"icon"	: "stock_new",
		#translators: This is a file.
		"description": _("Open %s") % "<b>%(name)s</b>",
		"snippet": True,
		"category": "files",
		},
	"FeedItem"	: {
		"name"	: ("dc:title",),
		"extra" : {"identifier": ("dc:identifier",)},
		"action": "gnome-open %(identifier)s",
		"icon"	: "stock_news",
		"description": _("Open news item %s") % "<b>%(name)s</b>",
		"snippet": True,
		"category": "web",
		},
	"Note"		: {
		"name"	: ("dc:title",),
		"action": "tomboy --open-note %(uri)s",
		"icon"	:"stock_notes",
		"description": _("Open note %s") % "<b>%(name)s</b>",
		"snippet": True,
		"category": "documents",
		},
	"IMLog"		: {
		"name"	: ("fixme:speakingto",),
		"action": "beagle-imlogviewer %(uri)s",
		"icon"	: "im",
		"description": _("View conversation with %s") % "<b>%(name)s</b>",
		"snippet": True,
		"category": "documents",
		},
	"Calendar"	: {
		"name"	: ("fixme:summary",),
		"action": "evolution %(uri)s",
		"icon"	: "stock_calendar",
		"description": _("View calendar %s") % "<b>%(name)s</b>",
		"category": "documents",
		},
	"WebHistory": {
		"name"	: ("dc:title",),
		"action": "gnome-open %(uri)s",
		"icon"	: "stock_bookmark",
		"description": _("Open History Item %s") % "<b>%(name)s</b>",
		"snippet": True,
		"category": "web",
		},
}

# Append snippet text for snippet-enabled handlers
for key, val in TYPES.items():
	if "snippet" in val and val["snippet"]:
		val["description"] += "%(snippet)s"
		
class BeagleLiveMatch (deskbar.Match.Match):
	def __init__(self, handler, result=None, **args):
		"""
		result: a dict containing:
			"name" : a name sensible to display for this match
			"uri": the uri of the match as provided by the beagled 'Uri: '-field
			"type": One of the types listed in the TYPES dict

		-- and optionally extra fields as provided by the corresponding entry in TYPES.
		Fx. "MailMessage". has an extra "sender" entry.
		"""
		deskbar.Match.Match.__init__ (self, handler, name=result["name"], **args)
		self.result = result

		# IM Log viewer take loca paths only		
		action = TYPES[self.result["type"]]["action"]
		if action.startswith("beagle-imlogviewer"):
			# Strip the uti descriptor, because imlogviewer takes a local path
			self.result["uri"] = gnomevfs.get_local_path_from_uri(self.result["uri"])
		
		# Load the correct icon
		
		#
		# There is bug http://bugzilla.gnome.org/show_bug.cgi?id=319549
		# which has been fixed and comitted, so we re-enable this snippet
		#
		
		self._icon = None
		if result["type"] == "File":
			try:
				self._icon = deskbar.Utils.load_icon_for_file(result["uri"])
			except Exception:
				pass
		
		if self._icon == None:
			# Just use an icon from the ICON table
			self._icon = handler.ICONS[result["type"]]
		
	def get_category (self):
		try:
			return TYPES[self.result["type"]]["category"]
		except:
			return "default"
		
	def get_name (self, text=None):
		# We use the result dict itself to look up words
		return self.result
	
	def get_verb(self):
		# Fetch the "description" template from TYPES
		return TYPES[self.result["type"]]["description"]
		
	def action(self, text=None):
	
		# Retrieve the associated action
		action = TYPES[self.result["type"]]["action"] % self.result
		args = ' '.split(action)

		print "BeagleLive spawning:", action, args
		gobject.spawn_async(args, flags=gobject.SPAWN_SEARCH_PATH)
	
	def get_hash(self, text=None):
		if "uri" in self.result:
			return self.result["uri"]

class SnippetContainer:
	def __init__(self, hit):
		self.hit = hit
		self.snippet = None
	
class BeagleLiveHandler(deskbar.Handler.SignallingHandler):
	def __init__(self):
		deskbar.Handler.SignallingHandler.__init__(self, ("system-search", "best"))
		self.counter = {}
		self.snippets = {}
		
	def initialize (self):
		import beagle
		self.beagle = beagle.Client()
		self.ICONS = self.__load_icons()
	
	def __load_icons (self):
		res = {}
		for t in TYPES.iterkeys():
			icon_file = TYPES[t]["icon"]
			if not icon_file: continue
			res[t] = deskbar.Utils.load_icon(icon_file)
		return res
		
	def query (self, qstring, qmax):
		import beagle
		beagle_query = beagle.Query()
		beagle_query.add_text(qstring)
		beagle_query.connect("hits-added", self.hits_added, qstring, MAX_RESULTS)
		try:
			self.beagle.send_request_async(beagle_query)
		except:
			return
			
		self.counter[qstring] = {}
		
	def _on_snippet_received(self, request, response, query, container, qstring, qmax):
		container.snippet = response.get_snippet()
		self._on_hit_added(query, container, qstring, qmax)
	
	def _on_snippet_closed(self, request, query, container, qstring, qmax):
		if container.snippet == None:
			self._on_hit_added(query, container.hit, qstring, qmax)
			
		container.hit.unref()
			
	def _on_hit_added(self, query, hit, qstring, qmax):
		fire_signal = False
		snippet = None
		if hit.__class__ == SnippetContainer:
			hit, snippet = hit.hit, hit.snippet
			fire_signal = True
			
		if not hit.get_type() in self.counter[qstring]:
			self.counter[qstring][hit.get_type()] = 0

		if self.counter[qstring][hit.get_type()] >= qmax:
			return
			
		hit_type = TYPES[hit.get_type()]
		result = {
			"uri":  hit.get_uri(),
			"type": hit.get_type(),
		}
		
		if snippet != None:
			tmp = re.sub(r"<.*?>", "", snippet)
			tmp = re.sub(r"</.*?>", "", tmp)
			result["snippet"] = "\n<span foreground='grey' size='small'>%s</span>" % cgi.escape(tmp)
		else:
			result["snippet"] = ""
			
		for prop in hit_type["name"]:
			try:
				name = hit.get_one_property(prop)
			except:
				try:
					# Beagle < 0.2
					name = hit.get_property(prop)
				except:
					continue
					
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
					try:
						val = hit.get_one_property(key)
					except:
						try:
							# Beagle < 0.2
							val = hit.get_property(key)
						except:
							continue
					if val != None:
						result[prop] = cgi.escape(val)
						break
				else:
					#translators: This is used for unknown values returned by beagle
					#translators: for example unknown email sender, or unknown note title
					result[prop] = _("?")
					
		self.counter[qstring][hit.get_type()] = self.counter[qstring][hit.get_type()] +1

		match = BeagleLiveMatch(self, result)
		if fire_signal:
			self.emit_query_ready(qstring, [match])
		else:	
			return match
		
	def hits_added(self, query, response, qstring, qmax):
		import beagle
		hit_matches = []
		for hit in response.get_hits():
			if "snippet" in TYPES[hit.get_type()] and TYPES[hit.get_type()]["snippet"]:
				req = beagle.SnippetRequest()
				req.set_query(query)
				req.set_hit(hit)
				container = SnippetContainer(hit)
				hit.ref()
				req.connect('response', self._on_snippet_received, query, container, qstring, qmax)
				req.connect('closed', self._on_snippet_closed, query, container, qstring, qmax)
				self.beagle.send_request_async(req)
				continue
							
			match = self._on_hit_added(query, hit, qstring, qmax)
			if match != None:
				hit_matches.append(match)				
			
		self.emit_query_ready(qstring, hit_matches)
