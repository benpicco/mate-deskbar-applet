import deskbar.core.Utils
import gtk.gdk
from deskbar.core.Categories import CATEGORIES 

"""
Represents a match returned by handlers
"""

class Match:
	def __init__(self, **args):
		"""
		You can pass the named paramter "icon" as a string being an
		absolute path or name of an icon.
		"""
		self._name = ""
		self._icon = None
		self._pixbuf = None
		self._category = "default"
		self._priority = 0
		self._actions = []
		self.__actions_hashes = set()
		if "name" in args:
			self._name = args["name"]
		if "icon" in args:
			self._icon = args["icon"]
		if "pixbuf" in args and isinstance(args["pixbuf"], gtk.gdk.Pixbuf):
			# WARNING: Only set a pixbuf if skip_history() always returns True
			# Otherwise saving to history won't work
			self._pixbuf = args["pixbuf"]
		if "category" in args:
			self._category = args["category"]
		if "priority" in args:
			self._priority = args["priority"]
	
	def _get_default_icon(self):
		if CATEGORIES[self.get_category()].has_key("icon"):
			return CATEGORIES[self.get_category()]["icon"]
		else:
			return CATEGORIES["default"]["icon"]
	
	def get_priority(self):
		return self._priority
	
	def set_priority(self, prio):
		self._priority = prio
		
	def get_icon(self):
		"""
		Returns a GdkPixbuf hat represents this match.
		Returns None if there is no associated icon.
		"""
		if self._pixbuf != None:
			# Only for Matches that won't be stored in history
			return self._pixbuf
		elif self._icon != None:
			return deskbar.core.Utils.load_icon(self._icon)
		else:
			return self._get_default_icon()
	
	def set_icon(self, iconname):
		self._icon = iconname
	
	def get_category(self):
		"""
		Returns a string corresponding to a key in the Categories.py file, indicating
		in which category this match should be put in.
		
		Returning None, uses the default category
		"""
		return self._category
	
	def set_category(self, cat):
		self._category = cat
        
	def get_actions(self):
		return self._actions
    
	def add_action(self, action):
		if not action.get_hash() in self.__actions_hashes:
			self.__actions_hashes.add(action.get_hash())
			self._actions.append(action)
	
	def add_all_actions(self, actions):
		for action in actions:
			self.add_action(action)
	
	def get_hash(self, text=None):
		"""
		Returns a hash used to verify if a query has one or more duplicates.
		Matches that have same hash will be selected based on the handler priority.
		text is the entered query string.
		By default, if the handler does not override this, it will return None.
		Returning None means no duplication check will be performed.
		"""
		return None
	
	def get_name(self, text=None):
		return self._name
	