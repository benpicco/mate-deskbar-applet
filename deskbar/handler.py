from os.path import join
import gtk, gobject
import deskbar

class Match:
	def __init__(self, handler, name, icon=None):
		self._priority = 0
		self._handler = handler
		self._name = name
		self._icon = icon
	
	def get_handler(self):
		"""
		Returns the handler owning this match.
		"""
		return self._handler
		
	def get_name(self, text=None):
		"""
		Returns a dictionary whose entries will be used in the Action
		string returned by get_verb.
		
		The passed string is the complete query string.
		
		The resulting action text will be
		match.get_verb() % match.get_name(query)
		
		Remember to escape pango markup if needed.
		"""
		return {"name": self._name}
		
	def get_verb(self):
		"""
		Returns the action string associated to this handler.
		
		The string must contain one or more "%(name)s" that will
		be replaced by the match get_name().
		
		The %(text)s will be replaced by the typed text.
		By default the %(name)s will be replaced by the self._name
		
		The string can also contain pango markup.
		
		Examples:
		 Send mail to %(address)s
		 Search <b>%s</b> for %(text)s
		 Execute %(prog)s
		"""
		raise NotImplementedError
		
	def get_priority(self):
		"""
		Returns the priority of the given match as int.
		This number can be used to compare the match from the
		same handler.
		"""
		return self._priority
	
	def get_icon(self):
		"""
		Returns a GdkPixbuf hat represents this match.
		Returns None if there is no associated icon.
		"""
		return self._icon
		
	def action(self, text=None):
		"""
		Tell the match to do the associated action.
		This method should not block.
		The optional text is the additional argument entered in the entry
		"""
		raise NotImplementedError
		
class Handler:
	def __init__(self, iconfile):
		"""
		The constructor of the Handler should generally not block. 
		Heavy duty tasks such as indexing should be done in the initialize() method.
		"""
		# We load the icon file, and if it fails load an empty one
		try:
			self._icon = gtk.gdk.pixbuf_new_from_file_at_size(join(deskbar.ART_DATA_DIR, iconfile), deskbar.ICON_SIZE, deskbar.ICON_SIZE)
		except Exception:
			self._icon = None
		
	def get_priority(self):
		"""
		Returns the global priority of this handler as int
		"""
		raise NotImplementedError
		
	def get_icon(self):
		"""
		Returns a GdkPixbuf hat represents this handler.
		Returns None if there is no associated icon.
		"""
		return self._icon
	
	def initialize(self):
		"""
		The constructor of the Handler should generally not block. 
		Heavy duty tasks such as indexing should be done in this method.
		
		Handler.initialize() is guarantied to be called before the handler
		is queried.
		
		If you need to perform gtk-related function you might want to use
		initialize_safe() instead of initialize(), the module loader will ensure
		gtk.threads_enter/leave is called appropriately.
		"""
		pass
	
	def stop(self):
		"""
		If the handler needs any cleaning up before it is unloaded, do it here.
		
		Handler.stop() is guarantied to be called before the handler is 
		unloaded.
		"""
		pass
		
	def query(self, query, max=5):
		"""
		Searches the handler for the given query string.
		Returns a list of matches objects of maximum length
		"max".
		"""
		raise NotImplementedError
