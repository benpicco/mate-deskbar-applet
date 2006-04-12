import gtk

import deskbar
from deskbar.Categories import CATEGORIES

class Nest :
	"""
	A class used to handle nested results in the CuemiacModel.
	"""
	def __init__(self, id, parent):
		try:
			self.__nest_msg = CATEGORIES[id]["nest"]
		except:
			self.__nest_msg = CATEGORIES["default"]["nest"]

		self.__parent = parent # The CuemiacCategory to which this nest belongs
	
	def get_name (self, text=None):
		n = self.get_count()
		# <i>%s More files</i> % <b>%d</b> % n
		return {"msg" : "<i>%s</i>" % (self.__nest_msg(n) % ("<b>%d</b>" % n))}
	
	def get_verb (self):
		return "%(msg)s"
		
	def get_count (self):
		return self.__parent.get_count () - self.__parent.get_threshold ()
		
	def get_id (self):
		"""id used to store expansion state"""
		return self.__parent.get_name () + "::nest"

class CuemiacCategory :
	"""
	A class representing a root node in the cuemiac model/view.
	"""
	def __init__ (self, id, parent):
		"""
		name: i18n'ed name for the category
		parent: CuemiacTreeStore in which this category belongs
		threshold: max number of hits before nesting
		"""
		self.__category_row_ref = None
		self.__nest_row_ref = None
		self.__parent = parent
		
		try:
			self.__name = CATEGORIES[id]["name"]
			self.__id = id
			if "threshold" in CATEGORIES[id]:
				self.__threshold = CATEGORIES[id]["threshold"]
			else:
				#FIXME: this needs to be a really big number..
				self.__threshold = 100000
		except:
			self.__name = CATEGORIES["default"]["name"]
			self.__threshold = CATEGORIES["default"]["threshold"]
			self.__id = "default"

			
		self.__priority = -1
		self.__count = 0

	def get_category_row_path (self):
		if self.__category_row_ref is None:
			return None
		return self.__category_row_ref.get_path ()
		
	def get_nest_row_path (self):
		if self.__nest_row_ref is None:
			return None
		return self.__nest_row_ref.get_path ()

	def set_category_iter (self, iter):
		self.__category_row_ref = gtk.TreeRowReference (self.__parent, self.__parent.get_path(iter))
		
	def get_category_iter (self):
		"""Returns a gtk.TreeIter pointing at the category"""
		if self.__category_row_ref is None:
			return None
		return self.__parent.get_iter (self.__category_row_ref.get_path())
		
	def set_nest_iter (self, iter):
		self.__nest_row_ref = gtk.TreeRowReference (self.__parent, self.__parent.get_path(iter))	
		
	def get_nest_iter (self):
		"""Returns a gtk.TreeIter pointing at the nested row"""
		if self.__nest_row_ref is None:
			return None
		return self.__parent.get_iter (self.__nest_row_ref.get_path())
	
	def get_name (self):
		return self.__name
		
	def get_id (self):
		"""id used to store expansion state"""
		return self.__id
	
	def inc_count (self):
		"""increase total number of hits in this category"""
		self.__count = self.__count + 1
	
	def get_count (self):
		"""return the total number of hits in this category"""
		return self.__count
	
	def get_threshold (self):
		return self.__threshold
	
	def get_priority(self):
		return self.__priority
	
	def set_priority(self, match):
		p = match.get_priority()[0]
		if self.__priority < p:
			self.__priority = p
