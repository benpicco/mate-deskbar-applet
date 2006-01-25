#
# Release dependant:
#
# - (EASY [Hard part solved]) Store expandedness state of categories (DONE)
#   Missing: Store states in Gconf. Hint: Just store CuemiacTreeView.__collapsed_rows
#
# - (?) Take category/handler ordering into account
#   Idea: Use no category sorting per default, then let the treeview be reoderable.
#         store sorting in gconf.
#
# - (TRIVIAL but THINK) Trim category names to as few as possible, and really get the names right
#   As long as categories are static it might also be a good idea to include a few generic'ish,
#   like "info" or something, for custom handlers..?
#
# - (TRIVIAL) Handlers don't need "prefixes" like "Google Live:" or "Open news item", also adjust
#   max hits per handler (especially beagle-live should return a skazillion hits)
#
# - Use icon entry instead of normal gtk.Entry (and update the icon correctly)
#
# - Always make sure that the selection is visible in scrolled windows. gtk.TreeView has an api
#   for this, but I can't get it to work.
#
# - Implement history popup
#
# - Focus entry on Alt-F3
#
# Would be really really nice:
#
# - (MEDIUM) User defined (non-static) categories *WITHOUT PERFOMANCE HIT*
#
# - (?) Optimize memory and speed
#
# - (?) Multiscreen logic.
#
# - (EASY) Fine tune aligned window behavior for vertical panels
#   Should probably check the window.gravity and construct the popup window according to that;
#   - ie. entry at bottom, hits on top, for applets in lower half of the screen, and vice versa
#   for applets in the top half (this can be read frm the CuemiacAlignedWindow.gravity).
#
# Bonus features/Ideas
#
# - (HARD) Detach the search window to "save" the search
#
# - (MEDIUM) Drag hits onto desktop/nautilus to create links (likely to require additional Match api)
#
# - Go into shortcur mode when ctrl is pressed (with entry focus) and show flat list of avail
#   shortcuts. When match list is focussed bind shortcuts when user hits ctrl-*. 
#   Give visual clue like : http://raphael.slinckx.net/mocku.png

from os.path import *
from gettext import gettext as _

import cgi
import sys

import gtk
incompatible = gtk.check_version (2,8,0)
if incompatible:
	print _("You need Gtk+ version 2.8.0 or higher to use this module")
	print incompatible
	sys.exit (1) # FIXME: Throw an appropriate exception instead, so we can use a gui notification
del incompatible

import gnome, gobject
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
	def __init__(self, nest_msg, parent):
		self.__nest_msg = nest_msg
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
	def __init__ (self, name, parent, threshold=5):
		"""
		name: i18n'ed name for the category
		parent: CuemiacTreeStore in which this category belongs
		threshold: max number of hits before nesting
		"""
		self.__category_row_ref = None
		self.__nest_row_ref = None
		self.__parent = parent

		self.__name = name
		self.__threshold = threshold
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
		return self.__name
	
	def inc_count (self):
		"""increase total number of hits in this category"""
		self.__count = self.__count + 1
	
	def get_count (self):
		"""return the total number of hits in this category"""
		return self.__count
	
	def get_threshold (self):
		return self.__threshold

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
	
	__gsignals__ = {
		"category-added" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
		"nest-added" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT])
	}
	
	def __init__ (self):
		gtk.TreeStore.__init__ (self, gobject.TYPE_PYOBJECT)
		self.__categories = {}
		self.append_method = gtk.TreeStore.append # Alternatively gtk.TreeStore.prepend for bottom panel layout
		
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
		cat = CuemiacCategory (CATEGORIES[match_obj.get_category()]["name"], self)
		iter = self.append_method (self, None, [cat])
		cat.set_category_iter (iter)
		self.__categories [match_obj.get_category()] = cat

		# Append the match to the category		
		self.append_method (self, iter, [match])
		cat.inc_count ()
		self.emit ("category-added", cat, cat.get_category_row_path ())
		
	
	def __append_to_category (self, match):
		qstring, match_obj = match
		cat = self.__categories [match_obj.get_category ()]
		row_iter = None
		
		if cat.get_count() < cat.get_threshold() :
			# We havent reached threshold, append normally
			cat.inc_count ()
			gtk.TreeStore.append (self, cat.get_category_iter(), [match])
			
		elif cat.get_count() == cat.get_threshold():
			# We reached the threshold with this match
			# Set up a Nest, and append the match to that
			nest = Nest (CATEGORIES[match_obj.get_category ()]["nest"], cat)
			nest_iter = self.append_method (self, cat.get_category_iter(), [nest])
			cat.set_nest_iter (nest_iter)
			
			cat.inc_count ()
			self.append_method (self, nest_iter, [match])
			self.emit ("nest-added", nest, cat.get_nest_row_path ())
		else:
			# We've already passed the threshold. Append the match in the nest.
			cat.inc_count ()
			self.append_method (self, cat.get_nest_iter(), [match])
			# Update the nested count in the nest row:
			self.row_changed (cat.get_nest_row_path(), cat.get_nest_iter())
			
		# Update the row count in the view:
		self.row_changed (cat.get_category_row_path(), cat.get_category_iter())
		
	def clear (self):
		"""Clears this model of data."""
		gtk.TreeStore.clear (self)
		self.__categories = {}
		
	def paths_equal (self, path1, path2):
		"""Returns true if the two paths point to the same cell."""
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
		self.set_property ("hover-selection", True)
		self.connect ("button-press-event", self.__on_click)
		self.connect ("key-press-event", self.__on_key_press)
				
		self.set_enable_search (False)
		self.set_reorderable(True)
		# FIXME: Make it so that categories *only* can be reordered by dragging
		# gtkTreeView does not use normal gtk DnD api.
		# it uses the api from hell
		
		gtk_style = gtk.Style ()
		self.header_bg = gtk_style.bg[gtk.STATE_NORMAL]
		self.match_bg = gtk_style.base [gtk.STATE_NORMAL]
		
		# Stuff to handle persistant expansion states.
		# A category will be expanded if it's in __collapsed_rows
		# a Nest will never be expanded (this is not a bug, but policy)
		self.__collapsed_rows = [] 
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
	
	def __on_row_expanded (self, widget, iter, path, model):
		idx = model[iter][model.MATCHES].get_id ()
		if idx in self.__collapsed_rows:
			self.__collapsed_rows.remove (idx)
		
	def __on_row_collapsed (self, widget, iter, path, model):
		idx = model[iter][model.MATCHES].get_id ()
		self.__collapsed_rows.append (idx)
	
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
			#cell.set_property ("height", 20)
			cell.set_property ("category-header", match.get_name())
			cell.set_property ("match-count", match.get_count ())
			return
		
		cell.set_property ("category-header", None)
		cell.set_property ("height", -1)
		cell.set_property ("cell-background-gdk", self.match_bg)
		
		if match.__class__ == Nest:
			cell.set_property ("markup", match.get_verb() % match.get_name())
			return
		
		qstring, match_obj = match
		# Pass unescaped query to the matches
		verbs = {"text" : qstring}
		verbs.update(match_obj.get_name(qstring))
		# Escape the query now for display
		verbs["text"] = cgi.escape(verbs["text"])
		
		cell.set_property ("markup", match_obj.get_verb () % verbs)

	def __on_click (self, widget, event):
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
			
			self.emit ("match-selected", match)
		

class CuemiacUI (DeskbarUI):
	
	navigation_keys = [65364, 65362, 43, 45, 65293] # Down, Up, +, -, Enter
	
	def __init__ (self, applet, prefs):
		DeskbarUI.__init__ (self, applet, prefs)
		
		self.deskbar_button = DeskbarAppletButton (applet)
		self.deskbar_button.connect ("toggled-main", lambda x,y: self.show_entry())
		self.deskbar_button.connect ("toggled-arrow", lambda x,y: self.show_history())

		self.popup = CuemiacAlignedWindow (self.deskbar_button.button_main, applet.get_orient())
		self.entry = gtk.Entry()
		self.history = get_deskbar_history ()
		self.history_popup = CuemiacHistoryPopup (self.history, self.deskbar_button.button_arrow, applet.get_orient ())
		self.model = CuemiacModel ()
		self.cview = CuemiacTreeView (self.model)
		self.scroll_win = gtk.ScrolledWindow ()
		
		#self.scroll_win = gtk.ScrolledWindow (hadjustment=cview.get_hadjustment())
		self.scroll_win.set_policy (gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)	
		self.box = gtk.VBox ()
		
		self.set_layout_by_orientation (applet.get_orient(), reshow=False, setup=True)
			
		self.popup.add (self.box)
		self.scroll_win.add_with_viewport (self.cview)
		
		self.box.connect ("size-request", self.adjust_size)
		on_entry_changed_id = self.entry.connect ("changed", self.on_entry_changed)
		
		# Connect first the history handler then the regular key handler
		self.history_entry_manager = EntryHistoryManager(self.entry, on_entry_changed_id)
		self.history_entry_manager.connect('history-set', self.on_history_set)
		
		self.entry.connect ("key-press-event", self.on_entry_key_press)
		self.entry.connect ("activate", self.on_entry_activate)
		self.cview.connect ("key-press-event", self.on_cview_key_press)
		self.cview.get_selection().connect ("changed", self.scroll_cview_to_selection)
		self.cview.connect ("match-selected", self.on_match_selected)
		self.history_popup.connect ("match-selected", self.on_match_selected)
		#self.cview.set_vadjustment (self.scroll_win.get_vadjustment())
		
		
		self.screen_height = self.popup.get_screen().get_height ()
		self.screen_width = self.popup.get_screen().get_width ()
		self.max_window_height = int (0.6 * self.screen_height)
		self.max_window_width = int (0.4 * self.screen_width)

		self.deskbar_button.realize ()
		self.box.show ()
		self.entry.show ()
		
		self.set_sensitive(False)
		try:
			self.applet.set_background_widget(self.deskbar_button)
		except Exception, msg:
			print 'Could not set background widget, no transparency:', msg
		
		self.invalid = True
		self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
		
	def on_match_selected (self, cview, match):
		if match.__class__ == Nest or match.__class__ == CuemiacCategory:
			return
		self.emit ("match-selected", match[0], match[1])
		self.deskbar_button.button_main.set_active (False)
	
	def show_entry (self):
		if self.deskbar_button.get_active_main ():
			self.popup.update_position ()
			self.popup.show ()
			self.entry.grab_focus ()
		else:
			if self.entry.get_text().strip() == "":
				self.scroll_win.hide ()
			self.popup.hide ()
			self.emit ("stop-query")
	
	def show_history (self):
		if self.deskbar_button.get_active_arrow ():
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
		print "CuemiacUI changing orientation to", applet.get_orient()
	
	def on_change_size (self, applet):
		if applet.get_orient () in [gnomeapplet.ORIENT_UP, gnomeapplet.ORIENT_DOWN]:
			# We're horizontal
			self.deskbar_button.set_button_image_from_file (join(deskbar.ART_DATA_DIR, "deskbar-horiz.svg"), applet.get_size())
		else:
			self.deskbar_button.set_button_image_from_file (join(deskbar.ART_DATA_DIR, "deskbar-vert.svg"), applet.get_size())
	
	def append_matches (self, matches):
		if self.invalid :
			self.invalid = False
			self.model.clear()
		self.model.append (matches)
		self.popup.show_all ()
		
	def recieve_focus (self):
		self.deskbar_button.set_active_main (True)
		self.popup.show_all ()
		self.entry.grab_focus ()
	
	def scroll_cview_to_selection (self, tree_sel):
		model, iter = tree_sel.get_selected ()
		if iter is None:
			return
		tree_sel.get_tree_view().scroll_to_cell (model.get_path (iter))
	
	def set_layout_by_orientation (self, orient, reshow=True, setup=False):
		"""orient should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
		reshow indicates whether or not the widget should call show() on all
		its children.
		setup should be true if this is the first time the widgets are laid out."""
		if not setup:
			self.box.remove (self.entry)
			self.box.remove (self.scroll_win)
		
		if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
			self.box.pack_start (self.entry, False)
			self.box.pack_start (self.scroll_win)
			self.cview.append_method = gtk.TreeStore.append
			if orient == gnomeapplet.ORIENT_DOWN:
				self.deskbar_button.set_button_image_from_file (join(deskbar.ART_DATA_DIR, "deskbar-horiz.svg"), self.applet.get_size ())
			else:
				self.deskbar_button.set_button_image_from_file (join(deskbar.ART_DATA_DIR, "deskbar-vert.svg"), self.applet.get_size ())
		else:
			# We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
			self.box.pack_start (self.scroll_win)
			self.box.pack_start (self.entry, False)
			self.cview.append_method = gtk.TreeStore.prepend
			self.deskbar_button.set_button_image_from_file (join(deskbar.ART_DATA_DIR, "deskbar-horiz.svg"))
			
		# Update the DeskbarAppletButton accordingly
		self.deskbar_button.set_orientation (orient, reshow)
		
		# Update how the popups is aligned
		self.popup.alignment = self.applet.get_orient ()
		self.history_popup.alignment = self.applet.get_orient ()
		
		if reshow:
			self.box.show_all ()
		
	def adjust_size (self, child, event):
		"""adjust window size to the size of the children"""
		# FIXME: Should we handle width intelligently also?
		w, h = self.cview.size_request ()
		h = h + self.entry.allocation.height + 4 # To ensure we don't always show scrollbars
		h = min (h, self.max_window_height)
		w = min (w, self.max_window_width)
		self.popup.resize (w, h)
		
	def on_entry_changed (self, entry):
		self.history.reset()
		qstring = self.entry.get_text().strip()
		self.cview.set_query_string (qstring)
		if qstring == "":
			self.model.clear()
			self.scroll_win.hide ()
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
			
			#self.entry.set_text("")
			self.deskbar_button.set_active_main (False)
			return True
		
		if event.keyval == 65362: # Up
			self.cview.grab_focus ()
			last = self.cview.last_visible_path ()
			self.cview.set_cursor (last)
			return True
			
		elif event.keyval == 65364: # Down
			self.cview.grab_focus ()
			self.cview.set_cursor (self.model.get_path(self.model.get_iter_first()))
			return True

		return False
		
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
			iter = self.model.iter_next(iter)
		#FIXME: this seems broken
		if iter is None:
			return
			
		# FIXME check that selection is not cat or nest, and then activate			
		self.on_match_selected(widget, self.model[iter][self.model.MATCHES])


	def on_history_set(self, historymanager, set):
		if not set:
			#self.entry.set_text("")
			pass
			
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
		else:
			pass
			#self.cview.scroll_to_cell (path)
			#print "scroll"
		return False		

gobject.type_register (CuemiacUI)

if gtk.pygtk_version < (2,8,0):	
	gobject.type_register (CuemiacTreeView)
	gobject.type_register (CellRendererCuemiacCategory)
	gobject.type_register (CuemiacModel)
