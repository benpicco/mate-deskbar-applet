# For TODO items previously in this file, see the TODO file in the root

from os.path import *
from gettext import gettext as _

import cgi
import sys

import gtk

import gnome, gobject, gconf
import gnome.ui, gnomeapplet
import pango

import deskbar
from deskbar.Categories import CATEGORIES
from deskbar.ui import EntryHistoryManager
from deskbar.ui.DeskbarUI import DeskbarUI
from deskbar.ui.cuemiac.DeskbarAppletButton import DeskbarAppletButton
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow
from deskbar.ui.cuemiac.CuemiacHistory import CuemiacHistoryPopup
from deskbar.DeskbarHistory import get_deskbar_history
from deskbar.ui.EntryHistoryManager import EntryHistoryManager

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
		
		if cat.get_count() < cat.get_threshold() :
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

class CellRendererCuemiacCategory (gtk.CellRendererText):
	"""
	Special cell renderer for the CuemiacTreeView.
	If the cell to be rendered is a normal Match, it falls back to the normal
	gtk.CellRendererText render method.
	If the cell is a CuemiacCategory it takes the icon column of the view into
	consideration and correctly left justifies the category title.
	
	This renderer also creates a small space between category headers. This is
	to ensure that they don't appear as one solid block when collapsed.
	"""
	__gproperties__ = {
        		'category-header' : (gobject.TYPE_STRING, 'markup for category title string',
                  	'markup for category title string, None if this is not a category header',
                 	 None, gobject.PARAM_READWRITE),
                 	 
                 'match-count' : (gobject.TYPE_INT, 'number of hits in the category',
                  	'the number of hits for the CuemiacCategory to be rendered',
                 	 0,1000,0, gobject.PARAM_READWRITE)
        }
	
	def __init__ (self):
		gtk.CellRendererText.__init__ (self)
		self.__category_header = None
		self.__match_count = 0
		
		# Obtain theme font and set it to bold and decrease size 2 points
		style = gtk.Style ()
		self.header_font_desc = style.font_desc
		self.header_font_desc.set_weight (pango.WEIGHT_BOLD)
		self.header_font_desc.set_size (self.header_font_desc.get_size () - pango.SCALE *2)
		self.header_bg = style.base [gtk.STATE_NORMAL]
	
	def do_render (self, window, widget, background_area, cell_area, expose_area, flags):
		if not self.get_property ("category-header"):
			gtk.CellRendererText.do_render (self, window, widget, background_area, cell_area, expose_area, flags)
		else:
			self.render_category (window, widget, background_area, cell_area, expose_area, flags)
	
	def render_category (self, window, widget, background_area, cell_area, expose_area, flag):
		"""
		Renders the category title from the "category-header" property and displays a rigth aligned
		hit count (read from the "match-count" property).
		"""
		ctx = window.cairo_create ()
		
		# Set up a pango.Layout for the category title
		cat_layout = ctx.create_layout ()
		cat_layout.set_text (self.get_property("category-header"))
		cat_layout.set_font_description (self.header_font_desc)
		
		# Set up a pango.Layout for the hit count
		count_layout = ctx.create_layout ()
		count_layout.set_text ("(" + str(self.get_property("match-count")) + ")")
		count_layout.set_font_description (self.header_font_desc)
		
		# Position and draw the layouts
		ctx.move_to (18, background_area.y + 6)
		ctx.show_layout (cat_layout)
		w, h = count_layout.get_pixel_size()
		ctx.move_to (background_area.width - w + 10, background_area.y + 6)
		ctx.show_layout (count_layout)
		
		# Draw a line in the normal background color in the top of the header,
		# to separate rows a bit.
		ctx.set_source_color (self.header_bg)
		ctx.move_to (0, background_area.y + 1)
		ctx.line_to (background_area.width + 100, background_area.y + 1) #FIXME: This 100 should really be the icon column width
		ctx.stroke ()
		
	def do_get_property(self, property):
		if property.name == 'category-header':
			return self.__category_header
		elif property.name == 'match-count':
			return self.__match_count
		else:
			raise AttributeError, 'unknown property %s' % property.name

	def do_set_property(self, property, value):
		if property.name == 'category-header':
			self.__category_header = value
		elif property.name == 'match-count':
			self.__match_count = value
		else:
			raise AttributeError, 'unknown property %s' % property.name
		
class CuemiacTreeView (gtk.TreeView):
	"""
	Shows a DeskbarCategoryModel. Sets the background of the root nodes (category headers)
	to gtk.Style().bg[gtk.STATE_NORMAL].
	"""
	
	activation_keys = [65293] # Enter  - Space makes a mess when users type in queries with spaces
	
	__gsignals__ = {
		"match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}
	
	def __init__ (self, model):
		gtk.TreeView.__init__ (self, model)
				
		icon = gtk.CellRendererPixbuf ()
		hit_title = CellRendererCuemiacCategory ()
		hit_title.set_property ("ellipsize", pango.ELLIPSIZE_END)
		hit_title.set_property ("width-chars", 50) #FIXME: Pick width according to screen size
		hits = gtk.TreeViewColumn ("Hits")
		hits.pack_start (icon)
		hits.pack_start (hit_title)
		hits.set_cell_data_func(hit_title, self.__get_match_title_for_cell)			
		hits.set_cell_data_func(icon, self.__get_match_icon_for_cell)
		self.append_column (hits)
		
		self.connect ("cursor-changed", self.__on_cursor_changed)
		self.set_property ("headers-visible", False)
		self.connect ("row-activated", self.__on_activated)
		self.connect ("key-press-event", self.__on_key_press)
				
		self.set_enable_search (False)
		#self.set_reorderable(True)
		# FIXME: Make it so that categories *only* can be reordered by dragging
		# gtkTreeView does not use normal gtk DnD api.
		# it uses the api from hell
		
		gtk_style = gtk.Style ()
		self.header_bg = gtk_style.bg[gtk.STATE_NORMAL]
		self.match_bg = gtk_style.base [gtk.STATE_NORMAL]
		
		# Stuff to handle persistant expansion states.
		# A category will be expanded if it's in __collapsed_rows
		# a Nest will never be expanded (this is not a bug, but policy)
		self.__collapsed_rows = deskbar.GCONF_CLIENT.get_list(deskbar.GCONF_COLLAPSED_CAT, gconf.VALUE_STRING)
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_COLLAPSED_CAT, lambda x, y, z, a: self.__on_config_expanded_cat(z.value))
		
		self.connect ("row-expanded", self.__on_row_expanded, model)
		self.connect ("row-collapsed", self.__on_row_collapsed, model)
		model.connect ("category-added", self.__on_category_added)
		model.connect ("nest-added", self.__on_nest_added)
		
		self.qstring = ""

	def clear (self):
		self.model.clear ()
	
	def set_query_string (self, qstring):
		self.qstring = qstring
	
	def last_visible_path (self):
		"""Returns the path to the last visible cell."""
		model = self.get_model ()
		iter = model.get_iter_first ()
		next = model.iter_next (iter)
		
		# Find last category node (they are always visible)
		while next:
			iter = next
			next = model.iter_next (iter)
		
		# If this category is not expanded return
		if not self.row_expanded (model.get_path (iter)):
			return model.get_path (iter)
		
		# Go to last child of category
		num_children = model.iter_n_children (iter)
		iter = model.iter_nth_child (iter, num_children - 1)
		
		# The child might be a Nest. If it's expanded
		# go into that. If not return.
		if not self.row_expanded (model.get_path (iter)):
			return model.get_path (iter)
			
		num_children = model.iter_n_children (iter)
		iter = model.iter_nth_child (iter, num_children - 1)
		return model.get_path (iter)
	
	def __on_config_expanded_cat (self, value):
		if value != None and value.type == gconf.VALUE_LIST:
			self.__collapsed_rows = [h.get_string() for h in value.get_list()]
			
	def __on_row_expanded (self, widget, iter, path, model):
		idx = model[iter][model.MATCHES].get_id ()
		if idx in self.__collapsed_rows:
			self.__collapsed_rows.remove (idx)
			deskbar.GCONF_CLIENT.set_list(deskbar.GCONF_COLLAPSED_CAT, gconf.VALUE_STRING, self.__collapsed_rows)
		
	def __on_row_collapsed (self, widget, iter, path, model):
		idx = model[iter][model.MATCHES].get_id ()
		self.__collapsed_rows.append (idx)
		deskbar.GCONF_CLIENT.set_list(deskbar.GCONF_COLLAPSED_CAT, gconf.VALUE_STRING, self.__collapsed_rows)
	
	def __on_category_added (self, widget, cat, path):
		if cat.get_id() not in self.__collapsed_rows:
			self.expand_row (path, False)
		
	def __on_nest_added (self, widget, cat, path):
		pass
		
	def __on_cursor_changed (self, view):
		model, iter = self.get_selection().get_selected()
	
	def __get_match_icon_for_cell (self, column, cell, model, iter, data=None):
	
		match = model[iter][model.MATCHES]
		
		if match.__class__ == CuemiacCategory:
			cell.set_property ("pixbuf", None)
			cell.set_property ("cell-background-gdk", self.header_bg)
			
		else:
			cell.set_property ("cell-background-gdk", self.match_bg)
			if match.__class__ == Nest:
				cell.set_property ("pixbuf", None)		
			else:
				qstring, match_obj = match
				cell.set_property ("pixbuf", match_obj.get_icon())

		
	def __get_match_title_for_cell (self, column, cell, model, iter, data=None):
	
		match = model[iter][model.MATCHES]
		
		if match.__class__ == CuemiacCategory:
			# Look up i18n category name
			cell.set_property ("cell-background-gdk", self.header_bg)
			cell.set_property ("height", 20)
			cell.set_property ("category-header", match.get_name())
			cell.set_property ("match-count", match.get_count ())
			return
		
		cell.set_property ("category-header", None)
		cell.set_property ("height", -1)
		cell.set_property ("cell-background-gdk", self.match_bg)
		
		if match.__class__ == Nest:
			cell.set_property ("markup", match.get_verb() % match.get_name())
			return
		
		cell.set_property ("markup", model[iter][model.ACTIONS])

	def __on_activated (self, treeview, path, column):
		model, iter = self.get_selection().get_selected()
		match = model[iter][model.MATCHES]
		self.emit ("match-selected", match)
	
	def __on_key_press (self, widget, event):
		# FIXME: In the future we should check for ctrl being pressed to create shortcuts
		model, iter = self.get_selection().get_selected()
		if iter is None:
			return False
		match = model[iter][model.MATCHES]
		# If this is a category or nest, toggle expansion state
		if event.keyval in self.activation_keys:
			if match.__class__ == Nest or match.__class__ == CuemiacCategory:
				path = model.get_path (iter)
				if self.row_expanded (path):
					self.collapse_row (path)
				else:
					self.expand_row (path, False)
				return True
			
		return False
		

class CuemiacUI (DeskbarUI):
	
	navigation_keys = [65364, 65362, 43, 45, 65293] # Down, Up, +, -, Enter
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		
		self.default_entry_pixbuf = deskbar.Utils.load_icon("deskbar-applet-small.png", width=-1)
		self.clipboard = gtk.clipboard_get (selection="PRIMARY")
		
		self.deskbar_button = DeskbarAppletButton (applet)
		self.deskbar_button.connect ("toggled-main", lambda x,y: self.show_entry())
		self.deskbar_button.connect ("toggled-arrow", lambda x,y: self.show_history())

		self.popup = CuemiacAlignedWindow (self.deskbar_button.button_main, applet)
		self.icon_entry = deskbar.iconentry.IconEntry ()
		self.entry = self.icon_entry.get_entry ()
		self.entry_icon = gtk.Image ()
		self.history = get_deskbar_history ()
		self.history_popup = CuemiacHistoryPopup (self.deskbar_button.button_arrow, applet)
		self.model = CuemiacModel ()
		self.cview = CuemiacTreeView (self.model)
		self.scroll_win = gtk.ScrolledWindow ()
		self.scroll_win.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)	
		self.box = gtk.VBox ()
		
		self.set_layout_by_orientation (applet.get_orient(), reshow=False, setup=True)
			
		self.popup.add (self.box)
		self.scroll_win.add(self.cview)
		self.icon_entry.pack_widget (self.entry_icon, True)
		self.entry_icon.set_property('pixbuf', self.default_entry_pixbuf)
		
		self.popup.set_border_width (1)
		self.history_popup.set_border_width (1)
		
		self.box.connect ("size-request", lambda box, event: self.adjust_popup_size())
		on_entry_changed_id = self.entry.connect ("changed", self.on_entry_changed)
		
		# Connect first the history handler then the regular key handler
		self.history_entry_manager = EntryHistoryManager(self.entry, on_entry_changed_id)
		self.history_entry_manager.connect('history-set', self.on_history_set)
		
		self.entry.connect ("key-press-event", self.on_entry_key_press)
		self.entry.connect_after ("changed", lambda entry : self.update_entry_icon())
		self.entry.connect ("activate", self.on_entry_activate)
		self.cview.connect ("key-press-event", self.on_cview_key_press)
		self.cview.connect ("match-selected", self.on_match_selected)
		self.cview.connect_after ("cursor-changed", lambda treeview : self.update_entry_icon())
		self.history_popup.connect ("match-selected", self.on_match_selected, True)
		self.history_popup.connect ("key-press-event", self.on_history_key_press)		
		
		self.screen_height = self.popup.get_screen().get_height ()
		self.screen_width = self.popup.get_screen().get_width ()
		self.max_window_height = int (0.8 * self.screen_height)
		self.max_window_width = int (0.6 * self.screen_width)

		self.box.show ()
		self.icon_entry.show_all ()
		
		self.set_sensitive(False)
		try:
			self.applet.set_background_widget(self.deskbar_button)
		except Exception, msg:
			pass
		
		self.invalid = True
		
		self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
		self.applet.set_flags(gtk.CAN_FOCUS)
		
	def update_entry_icon (self, icon=None):
		if icon == None:
			icon = self.default_entry_pixbuf
			path, column = self.cview.get_cursor ()
		
			if path != None:
				item = self.model[self.model.get_iter(path)][self.model.MATCHES]
				if item.__class__ != CuemiacCategory and item.__class__ != Nest:
					text, match = item
					icon=match.get_icon()
				
		self.entry_icon.set_property('pixbuf', icon)
		self.entry_icon.set_size_request(deskbar.ICON_WIDTH, deskbar.ICON_HEIGHT)
		
	def on_match_selected (self, cview, match, is_historic=False):
		if match.__class__ == Nest or match.__class__ == CuemiacCategory:
			return
		self.emit ("match-selected", match[0], match[1])
		if is_historic :
			self.deskbar_button.button_arrow.set_active (False)
		else:
			self.deskbar_button.button_main.set_active (False)
	
	def show_entry (self, time=None):
		if self.deskbar_button.get_active_main ():
			# Unselect what we have in the entry, so we don't occupy the middle-click-clipboard
			# thus clearing the model on popup
			self.entry.select_region (0,0)
		
			# If the entry is empty or there's something in the middle-click-clipboard
			# clear the popup so that we can paste into the entry.
			if self.entry.get_text().strip() == "" or self.clipboard.wait_for_text():
				self.entry.set_text("")
				self.model.clear ()
				self.scroll_win.hide ()
				
			self.deskbar_button.button_arrow.set_active (False)
			self.adjust_popup_size ()
			# self.popup.update_position ()
			self.update_entry_icon ()
			
			if time != None:
				self.popup.present_with_time (time)
			else:
				self.popup.present ()
			
			self.entry.grab_focus ()
		else:
			self.popup.hide ()
			self.emit ("stop-query")
	
	def receive_focus (self, time):
		# Toggle expandedness of the popup
		self.deskbar_button.button_main.set_active(not self.deskbar_button.button_main.get_active())
		# This will focus the entry since we are passing the real event time and not the toggling time
		if self.deskbar_button.button_main.get_active():
			self.show_entry(time)
		
	def show_history (self):
		if self.deskbar_button.get_active_arrow ():
			self.deskbar_button.button_main.set_active (False)
			# self.history_popup.update_position ()
			self.history_popup.show_all ()
		else:
			self.history_popup.hide ()
	
	def get_view (self):
		return self.deskbar_button
		
	def set_sensitive (self, active):
		self.deskbar_button.set_sensitive (active)
		self.deskbar_button.button_main.set_sensitive (active)
		self.deskbar_button.button_arrow.set_sensitive (active)
		
	def on_change_orient (self, applet):
		self.set_layout_by_orientation (applet.get_orient())
	
	def on_change_size (self, applet):
		# FIXME: This is ugly, but i don't know how to get it right
		image_name = "deskbar-applet-panel"
		if applet.get_orient () in [gnomeapplet.ORIENT_UP, gnomeapplet.ORIENT_DOWN]:
			image_name += "-h"
		else:
			image_name += "-v"
		
		if applet.get_size() <= 36:
			image_name += ".png"
			s = 24
		else:
			image_name += ".svg"
			s = applet.get_size()-12
		
		self.deskbar_button.set_button_image_from_file (join(deskbar.ART_DATA_DIR, image_name), s)
	
	def append_matches (self, matches):
		if self.invalid :
			self.invalid = False
			self.model.clear()
			
		entry_text = self.entry.get_text().strip()
		#valid_matches = False
		#for text, match in matches:
		#	if text == entry_text: # FIXME: Maybe it will suffice to only check the first match
		#		self.model.append ((text,match))
		#		valid_matches = True
		#if valid_matches:
		#	self.popup.show_all ()
		for text, match in matches:
			self.model.append ((text, match))
		self.popup.show_all ()
		
	def middle_click(self):
		text = self.clipboard.wait_for_text ()
		if text != None:
			self.deskbar_button.button_main.set_active (True)
			self.entry.grab_focus()
			self.entry.set_text(text)
		
	def set_layout_by_orientation (self, orient, reshow=True, setup=False):
		"""orient should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
		reshow indicates whether or not the widget should call show() on all
		its children.
		setup should be true if this is the first time the widgets are laid out."""
		if not setup:
			self.box.remove (self.icon_entry)
			self.box.remove (self.scroll_win)
		
		if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
			self.box.pack_start (self.icon_entry, False)
			self.box.pack_start (self.scroll_win)
			self.cview.append_method = gtk.TreeStore.append
			self.cview.get_model().set_sort_order(gtk.SORT_DESCENDING)
		else:
			# We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
			self.box.pack_start (self.scroll_win)
			self.box.pack_start (self.icon_entry, False)
			self.cview.append_method = gtk.TreeStore.prepend
			self.cview.get_model().set_sort_order(gtk.SORT_ASCENDING)
			
		# Update icon accordingto direction
		self.on_change_size (self.applet)
		
		# Update the DeskbarAppletButton accordingly
		self.deskbar_button.set_orientation (orient, reshow)
		
		# Update how the popups is aligned
		self.popup.alignment = self.applet.get_orient ()
		self.history_popup.alignment = self.applet.get_orient ()
		
		if reshow:
			self.box.show_all ()
		
	def adjust_popup_size (self):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.cview.size_request ()
		h = h + self.icon_entry.allocation.height + 4 # To ensure we don't always show scrollbars
		h = min (h, self.max_window_height)
		w = min (w, self.max_window_width)
		if w > 0 and h > 0:
			self.popup.resize (w, h)
		
	def on_entry_changed (self, entry):
		self.history.reset()
		qstring = self.entry.get_text().strip()
		self.cview.set_query_string (qstring)
		if qstring == "":
			self.model.clear()
			self.scroll_win.hide ()
			self.emit ("stop-query")
			return
		
		self.invalid = True
		self.popup.show ()
		self.emit ("start-query", qstring, 100)
	
	def hide_if_entry_empty (self):
		"""Checks if the entry is empty, and hides the window if so.
		Used by on_entry_changed() with a gobject.timeout_add()."""
		if self.entry.get_text().strip() == "":
			self.popup.hide ()
	
	def on_entry_key_press (self, entry, event):
		
		if event.keyval == gtk.keysyms.Escape:
			# bind Escape to clear the GtkEntry
			if not entry.get_text().strip() == "":
				# If we clear some text, tell async handlers to stop.
				self.emit ("stop-query")
			
			self.deskbar_button.set_active_main (False)
			return True
		
		if 	event.state&gtk.gdk.MOD1_MASK != 0:
			# Some Handlers want to know about Alt-keypress
			# combinations, for example.  Here, we notify such
			# Handlers.
			text = entry.get_text().strip()
			if text != "":
				self.emit('stop-query')
				self.emit('keyboard-shortcut', text, event.keyval)
			entry.set_text("")
			
			# Broadcast an escape
			event.state = 0
			event.keyval = gtk.keysyms.Escape
			entry.emit('key-press-event', event)
			return True
			
		if event.keyval == 65362: # Up
			self.cview.grab_focus ()
			last = self.cview.last_visible_path ()
			self.cview.set_cursor (last)
			return True
			
		if event.keyval == 65364: # Down
			self.cview.grab_focus ()
			self.cview.set_cursor (self.model.get_path(self.model.get_iter_first()))
			return True

		return False
		
	def on_history_key_press (self, history, event):
		if event.keyval == gtk.keysyms.Escape:
			self.deskbar_button.button_arrow.set_active (False)
		self.update_entry_icon ()
			
	def on_entry_activate(self, widget):
		# if we have an active history item, use it
		if self.history_entry_manager.current_history != None:
			text, match = self.history_entry_manager.current_history
			self.on_match_selected(widget, (text, match))
			return
			
		path, column = self.cview.get_cursor ()
		iter = None
		if path != None:
			iter = self.model.get_iter (path)
			
		if iter is None:
			# No selection, select top element # FIXME do this
			iter = self.model.get_iter_first()
			while (not self.model.iter_has_child(iter)) or (not self.cview.row_expanded(self.model.get_path(iter))):
				iter = self.model.iter_next(iter)
			iter = self.model.iter_children(iter)

		if iter is None:
			return
			
		# FIXME check that selection is not cat or nest, and then activate			
		self.on_match_selected(widget, self.model[iter][self.model.MATCHES])


	def on_history_set(self, historymanager, set):
		if set:
			text, match = historymanager.current_history
			self.update_entry_icon (icon=match.get_icon())
		else:
			self.entry.set_text("")
			
	def on_cview_key_press (self, cview, event):
		# If this is an ordinary keystroke just let the
		# entry handle it.
		if not event.keyval in self.navigation_keys:
			self.entry.event (event)
			return True
			
		path, column = cview.get_cursor ()
		model = cview.get_model ()
		if model.paths_equal (path, model.get_path(model.get_iter_first())):
			if event.keyval == 65362: # Up
				gobject.timeout_add (1, lambda : self.entry.grab_focus ())
			
		elif model.paths_equal (path, cview.last_visible_path()):
			if event.keyval == 65364: # Down
				gobject.timeout_add (1, lambda : self.entry.grab_focus ())

		return False		

gobject.type_register (CuemiacUI)

if gtk.pygtk_version < (2,8,0):	
	gobject.type_register (CuemiacTreeView)
	gobject.type_register (CellRendererCuemiacCategory)
	gobject.type_register (CuemiacModel)
