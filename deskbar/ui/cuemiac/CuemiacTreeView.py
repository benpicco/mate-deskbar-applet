import gtk
import gobject
import pango
import gconf

import deskbar
from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory

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
		
		# Grab some default theme settings
		# they are probably incorrect, but we reset
		# them on each render anyway.
		style = gtk.Style ()
		self.header_font_desc = style.font_desc
		self.header_font_desc.set_weight (pango.WEIGHT_BOLD)
		self.header_font_desc.set_size (self.header_font_desc.get_size () - pango.SCALE *2)
		self.header_bg = style.base [gtk.STATE_NORMAL]
	
	def set_style (self, widget):
		"""
		Apply the style from widget, to this cellrenderer
		"""
		self.header_font_desc = widget.style.font_desc
		self.header_font_desc.set_weight (pango.WEIGHT_BOLD)
		self.header_font_desc.set_size (self.header_font_desc.get_size () - pango.SCALE *2)
		self.header_bg = widget.style.base [gtk.STATE_NORMAL]
	
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
		# Ensure we have fresh style settings
		self.set_style (widget)
		
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
		self.connect ("button-press-event", self.__on_button_press)		
		self.connect ("key-press-event", self.__on_key_press)
				
		self.set_enable_search (False)
		#self.set_reorderable(True)
		# FIXME: Make it so that categories *only* can be reordered by dragging
		# gtkTreeView does not use normal gtk DnD api.
		# it uses the api from hell
		
		# Stuff to handle persistant expansion states.
		# A category will be expanded if it's in __collapsed_rows
		self.__collapsed_rows = deskbar.GCONF_CLIENT.get_list(deskbar.GCONF_COLLAPSED_CAT, gconf.VALUE_STRING)
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_COLLAPSED_CAT, lambda x, y, z, a: self.__on_config_expanded_cat(z.value))
		
		self.connect ("row-expanded", self.__on_row_expanded, model)
		self.connect ("row-collapsed", self.__on_row_collapsed, model)
		model.connect ("category-added", self.__on_category_added)
		
		self.qstring = ""

	def is_ready (self):
		""" Returns True if the view is ready for user interaction """
		num_children = self.get_model().iter_n_children (None)
		return self.get_property ("visible") and num_children

	def clear (self):
		self.model.clear ()
	
	def set_query_string (self, qstring):
		self.qstring = qstring
	
	def last_visible_path (self):
		"""Returns the path to the last visible cell."""
		model = self.get_model ()
		iter = model.get_iter_first ()
		if iter == None:
			return None

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
		return model.get_path (iter)

	def move_cursor_up_down (self, count):
		"""
		Move cursor one step up or down in the tree.
		@param count: 1 for up/next, -1 for down/previous.
		@return: True if the move was succesful.
		"""
		# The implementation of this method is one big hack. 
		# This method is needed because gtk.TreeView does not handle events
		# correctly when unfocused (and we need to forward events to it).
		# See bug #326254.
		# We cannot simply port the navigational model because 
		# gtk.TreeView uses a GtkRBTree, which is not a part of the public api,
		# to implement the navigational model.
		path, col = self.get_cursor ()
		rect = self.get_cell_area (path, col)
		
		new_cell_y = 0
		if count == -1:
			# Select a point in the cell above the cursor
			new_cell_y = rect.y - 5
		else:
			if count != 1:
				print "WARNING in CuemiacTreeView - in move_cursor_up_down, the count must be 1 or -1."
			# Select a point in the cell below the cursor
			new_cell_y = rect.height + rect.y + 5
				
		# Select the cell meeting the point (rect.x, new_cell_y)
		cell_ctx = self.get_path_at_pos (rect.x, new_cell_y)
		if cell_ctx is None:
			return False
		path, col, x, y = cell_ctx
		self.set_cursor (path, col)
		
		return True
		
	def focus_bottom_match (self):
		last = self.last_visible_path ()
		self.set_cursor (last)
	
	def focus_top_match (self):
		model = self.get_model ()
		first = model.get_path(model.get_iter_first())
		self.set_cursor (first)

	def coord_is_category (self, x, y):
		path_ctx = self.get_path_at_pos(int(x), int(y))
		if path_ctx is None:
			return False
		path, col, x, y = path_ctx
		model = self.get_model()
		match = model[model.get_iter(path)][model.MATCHES]
		if match.__class__ == CuemiacCategory:
			return True
		else:
			return False

	def __on_button_press (self, treeview, event):
		# We want to activate items on single click
		path_ctx = self.get_path_at_pos (int(event.x), int(event.y))
		if path_ctx is not None:
			path, col, x, y = path_ctx
			model = self.get_model ()
			match = model[model.get_iter(path)][model.MATCHES]
			if match.__class__ != CuemiacCategory:
				self.emit ("row-activated", path, col)
				#self.emit ("match-selected", match)
	
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
				
	def __on_cursor_changed (self, view):
		model, iter = self.get_selection().get_selected()
	
	def __get_match_icon_for_cell (self, column, cell, model, iter, data=None):
	
		match = model[iter][model.MATCHES]
		
		if match.__class__ == CuemiacCategory:
			cell.set_property ("pixbuf", None)
			cell.set_property ("cell-background-gdk", self.style.bg[gtk.STATE_NORMAL])
			
		else:
			cell.set_property ("cell-background-gdk", self.style.base[gtk.STATE_NORMAL])
			qstring, match_obj = match
			cell.set_property ("pixbuf", match_obj.get_icon())

		
	def __get_match_title_for_cell (self, column, cell, model, iter, data=None):
	
		match = model[iter][model.MATCHES]
		
		if match.__class__ == CuemiacCategory:
			# Look up i18n category name
			cell.set_property ("cell-background-gdk", self.style.bg[gtk.STATE_NORMAL])
			cell.set_property ("height", 20)
			cell.set_property ("category-header", match.get_name())
			cell.set_property ("match-count", match.get_count ())
			return
		
		cell.set_property ("category-header", None)
		cell.set_property ("height", -1)
		cell.set_property ("cell-background-gdk", self.style.base[gtk.STATE_NORMAL])
				
		cell.set_property ("markup", model[iter][model.ACTIONS])

	def __on_activated (self, treeview, path, col):
		model = self.get_model()
		iter = model.get_iter (path)
		match = model[iter][model.MATCHES]
		
		# Check if this s really a match and not just
		# a category
		if match.__class__ == CuemiacCategory:
			return
			
		# So we have a Match, tell the world
		self.emit ("match-selected", match)
		
		
	def __on_key_press (self, widget, event):
		# FIXME: In the future we should check for ctrl being pressed to create shortcuts
		model, iter = self.get_selection().get_selected()
		if iter is None:
			return False
		match = model[iter][model.MATCHES]
		# If this is a category, toggle expansion state
		if event.keyval in self.activation_keys:
			if match.__class__ == CuemiacCategory:
				path = model.get_path (iter)
				if self.row_expanded (path):
					self.collapse_row (path)
				else:
					self.expand_row (path, False)
				return True
			
		return False

if gtk.pygtk_version < (2,8,0):	
	gobject.type_register (CuemiacTreeView)
	gobject.type_register (CellRendererCuemiacCategory)
