import gtk
import gobject

import cgi

import deskbar
from deskbar.Categories import CATEGORIES
from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory, Nest
			
# The sort function ids
SORT_BY_CATEGORY = 1

class CuemiacModel (gtk.TreeStore):
	"""
	A tree model to store hits sorted by categories. CuemiacCategory's are root nodes,
	with each child representing a hit or a "nest" containing additional hits.
	Schematically this looks like:
	
	CuemiacCategory->
		-> deskbar.handler.Match
		-> deskbar.handler.Match
		...
		-> deskbar.handler.Match
		-> Nest
			-> deskbar.handler.Match
			-> deskbar.handler.Match
			...
	CuemiacCategory->
		...
	...
	
	Signal arguments:
		"category-added" : CuemiacCategory, gtk.TreePath
		"nest-added" : CuemiacCategory, gtk.TreePath
	"""
	# Column name
	MATCHES = 0
	ACTIONS = 1
	
	__gsignals__ = {
		"category-added" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
		"nest-added" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT])
	}
	
	def __init__ (self):
		gtk.TreeStore.__init__ (self, gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)
		self.__categories = {}
		self.append_method = gtk.TreeStore.append # Alternatively gtk.TreeStore.prepend for bottom panel layout
		self.set_sort_func(SORT_BY_CATEGORY, self.__on_sort_categories)
	
	def set_sort_order(self, order):
		self.set_sort_column_id(SORT_BY_CATEGORY, order)
	
	def __on_sort_categories(self, treemodel, iter1, iter2):
		match1 = treemodel[iter1][self.MATCHES]
		match2 = treemodel[iter2][self.MATCHES]

		# Sort categories according to handler preferences
		if match1.__class__ == CuemiacCategory:
			return match1.get_priority() - match2.get_priority()
		
		# Ensure Nests are always last
		if match1.__class__ == Nest:
			return -1
		if match2.__class__ == Nest:
			return 1
		
		# Sort matches inside category according to handler prefs, then match prio
		text1, match1 = match1
		text2, match2 = match2
		
		diff = match1.get_priority()[0] - match2.get_priority()[0]
		if diff != 0:
			return diff
			
		diff = match1.get_priority()[1] - match2.get_priority()[1]
		if diff != 0:
			return diff
		
		# Finally use the Action to sort alphabetically, is this a bottleneck ?
		a = treemodel[iter1][self.ACTIONS]
		b = treemodel[iter2][self.ACTIONS]
		if a != None:
			a = a.strip().lower()
		if b != None:
			b = b.strip().lower()
			
		if a < b:
			return 1
		elif a > b:
			return -1
		else:
			return 0
		
	def append (self, match):
		"""
		Automagically append a match or list of matches 
		to correct category(s), or create a new one(s) if needed.
		"""
		if type (match) == list:
			for hit in match:
				self.__append (hit)
		else:
			self.__append (match)
		
	def __append (self, match):
		qstring, match_obj = match
		if self.__categories.has_key (match_obj.get_category()):
			self.__append_to_category (match)
		else:
			self.__create_category_with_match (match)
			
			
	def __create_category_with_match (self, match):
		"""
		Assumes that the category for the match does not exist.
		"""
		qstring, match_obj = match
		#FIXME: Check validity of category name and use  proper i18n
		# Set up a new category
		cat = CuemiacCategory (match_obj.get_category(), self)
		cat.set_priority(match_obj)	

		iter = self.append_method (self, None, [cat, None])
		cat.set_category_iter (iter)
		self.__categories [match_obj.get_category()] = cat

		# Append the match to the category	
		self.__append_match_to_iter (iter, match)
		cat.inc_count ()
		self.emit ("category-added", cat, cat.get_category_row_path ())
		
	
	def __append_to_category (self, match):
		qstring, match_obj = match
		cat = self.__categories [match_obj.get_category ()]
		cat.set_priority(match_obj)
		row_iter = None
		
		# Test to remove nesting temporarily
		if True:#cat.get_count() < cat.get_threshold() :
			# We havent reached threshold, append normally
			cat.inc_count ()
			self.__append_match_to_iter (cat.get_category_iter(), match)
			
		elif cat.get_count() == cat.get_threshold():
			# We reached the threshold with this match
			# Set up a Nest, and append the match to that
			nest = Nest (match_obj.get_category (), cat)
			nest_iter = self.append_method (self, cat.get_category_iter(), [nest, None])
			cat.set_nest_iter (nest_iter)
			
			cat.inc_count ()
			self.__append_match_to_iter (nest_iter, match)
			self.emit ("nest-added", nest, cat.get_nest_row_path ())
		else:
			# We've already passed the threshold. Append the match in the nest.
			cat.inc_count ()
			self.__append_match_to_iter (cat.get_nest_iter(), match)
			# Update the nested count in the nest row:
			self.row_changed (cat.get_nest_row_path(), cat.get_nest_iter())
			
		# Update the row count in the view:
		self.row_changed (cat.get_category_row_path(), cat.get_category_iter())

	def __append_match_to_iter (self, iter, match):
		qstring, match_obj = match
		# Pass unescaped query to the matches
		verbs = {"text" : qstring}
		verbs.update(match_obj.get_name(qstring))
		# Escape the query now for display
		verbs["text"] = cgi.escape(verbs["text"])
		
		self.append_method (self, iter, [match, match_obj.get_verb () % verbs])
		
	def clear (self):
		"""Clears this model of data."""
		gtk.TreeStore.clear (self)
		self.__categories = {}
		
	def paths_equal (self, path1, path2):
		"""Returns true if the two paths point to the same cell."""
		if path1 == None or path2 == None:
			return False
			
		return ( self.get_string_from_iter (self.get_iter(path1)) == self.get_string_from_iter (self.get_iter(path2)) )

		


if gtk.pygtk_version < (2,8,0):	
	gobject.type_register (CuemiacModel)
