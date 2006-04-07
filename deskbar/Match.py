import deskbar.Utils

"""
Represents a match returned by handlers
"""

class Match:
	def __init__(self, handler, **args):
		self._priority = 0
		self._handler = handler
		self._icon = None
		
		self.name = None
		self.icon = None
		if "name" in args:
			self.name = args["name"]
		if "icon" in args:
			self.icon = args["icon"]
	
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
		return {"name": self.name}
		
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
		Returns the priority of the given match as a tuple (int,int).
		This number can be used to compare the match from the
		same handler.
		The first number in the tuple is the match's handler prio, the second
		is the prio relative to other matces from the hander
		"""
		return (self._handler.get_priority(), self._priority)
	
	def get_hash(self, text=None):
		"""
		Returns a hash used to verify if a query has one or more duplicates.
		Matches that have same hash will be selected based on the handler priority.
		text is the entered query string.
		By default, if the handler does not override this, it will return None.
		Returning None means no duplication check will be performed.
		"""
		return None
		
	def get_icon(self):
		"""
		Returns a GdkPixbuf hat represents this match.
		Returns None if there is no associated icon.
		"""
		if self._icon == None:
			if self.icon != None:
				self._icon = deskbar.Utils.load_icon(self.icon)
			if self._icon == None:
				self._icon = False
		
		if self._icon == False:
			return self.get_handler().get_icon()
		else:
			return self._icon
	
	def get_category(self):
		"""
		Returns a string corresponding to a key in the Categories.py file, indicating
		in which category this match should be put in.
		
		Returning None, uses the default category
		"""
		return None
		
	def action(self, text=None):
		"""
		Tell the match to do the associated action.
		This method should not block.
		The optional text is the additional argument entered in the entry
		"""
		raise NotImplementedError
	
	def is_valid(self, text=None):
		"""
		Tests wether the match is still valid, by default it's True.
		For example if a file has moved, the file match is invalid
		The optional text is the additional argument entered in the entry
		"""
		return True
		
	def serialize(self):
		serialized = {}
		for prop, val in [(prop, getattr(self, prop)) for prop in dir(self)
								if not prop.startswith("_") and
								not callable(getattr(self, prop))]:
			serialized[prop] = val
		
		return serialized

	def copy(self):
		try:
			return self._handler.deserialize(str(self.__class__)[str(self.__class__).rfind(".")+1:], self.serialize())
		except:
			return None
