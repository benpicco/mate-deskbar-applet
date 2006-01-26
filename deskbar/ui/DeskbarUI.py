import gtk, gobject

class DeskbarUI (gobject.GObject):
	"""
	This class represents an abstraction of a deskbar user interface.
	The constructor of any class deriving from it should take a gnomeapplet.Applet
	as single argument, if it is to be instantiated from a DeskbarApplet instance
	(which most will).
	
	Signals:
		"match-selected" (text, Match):
			A match has been selected by the user. Passes the selected match along.
			
		"request-history-show" (gtk.Widget, gnomeapplet.ORIENT_*)
			The user has performed and action such that the history should be popped up.
			The widget is the widget to align the popup to, the ORIENT_* is the alignment
			the popup should have relative to the widget.
			
		"request-history-hide" ():
			Request that the history window will be hidden.
		
		"start-query" (query_string, max_hits):
			Request a query on the given string returning maximally max_hits hits.
			
		"stop-query" ():
			Signal that we no longer will handle returned queries. Fx. when the user hits
			Esc, or the result list have become hidden.
			
		"request-keybinding" (Match, key_binding):
			The user has performed an action which should attach a keybinding to the given match.
		
		"keyboard-shortcut" (string, keyval):
			Te user has triggered a keyboard shortcut, the query and keyval are passed (from gdk event)
			
	"""
	__gsignals__ = {
		"match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT]),
		"start-query" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
		"stop-query" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		"request-keybinding" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
		"keyboard-shortcut" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_UINT]),
	}
	
	def __init__ (self, applet, prefs):
		gobject.GObject.__init__ (self)
		self.applet = applet
		self.prefs = prefs
	
	def on_change_orient (self, applet):
		"""
		Connected to the applets "change-orient" signal.
		"""
		pass
	
	def on_change_size (self, applet):
		"""
		Connected to the applets "change-size" signal.
		"""
		pass
		
	def recieve_focus (self):
		"""
		Called when the applet recieves focus. Use fx. to pop up a text entry with focus.
		"""
		pass
	
	def middle_click(self):
		"""
		Called when the applet receives a middle click. Must return True if the middle click event is handled
		"""
		return False
		
	def set_sensitive (self, active):
		"""
		Called when the UI should be in/active because modules are loading
		"""
		pass
		
	def append_matches (self, matches):
		"""
		Called in response to sending a "start-query" signal.
		
		This method should take both a single (non-list) match and a list
		of matches.
		
		The list of matches is a list of tuples (text, match), text is the query
		string and match is a Match instance
		"""
		raise NotImplementedError
		
	def get_view (self):
		"""
		Return the widget to be displayed for this UI.
		"""
		raise NotImplementedError
		
if gtk.pygtk_version < (2,8,0):
	gobject.type_register(DeskbarUI)
