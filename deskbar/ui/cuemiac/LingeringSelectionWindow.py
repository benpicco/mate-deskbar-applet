import gtk
import glib

class LingeringSelectionWindow (gtk.Window):
	"""
	Leave an imprint on the screen of the selected row in a treeview
	when it is activated.
	This is mainly used when the window containing the treeview is
	hidden on the same activation.
	"""
	def __init__ (self, view):
		"""
		Just create the LingeringSelectionWindow passing the treeview
		to manage in the constructor and everything will be taken care of.
		"""
		gtk.Window.__init__ (self, gtk.WINDOW_POPUP)
		
		self.linger_time = 1 # Linger for one second
		
		self.set_focus_on_map (False)
				
		view.connect ("row-activated", self._on_view_activated)
		
	def _on_view_activated (self, view, path, column):
		# Check if this row has children, if it does
		# do nothing
		model = view.get_model()
		if model.iter_has_child (model.get_iter(path)) :
			"linger block"
			return
			
		pixmap = view.create_row_drag_icon (path)
		if pixmap == None:
			self.hide()
			return
			
		image = gtk.Image()
		image.set_from_pixmap (pixmap, None)
		
		if self.get_child() :
			self.remove (self.get_child())
			
		self.add (image)
		self._update_position (view, path, column)
		self._linger ()
		
	def _update_position (self, view, path, column):
		"""
		Move the window to the activated paths position
		"""
		ox, oy = view.window.get_origin ()
		area = view.get_background_area (path, column)
		x, y = view.tree_to_widget_coords (area.x, area.y)
		self.move (x + ox, area.y + oy)
		self.resize (area.width, area.height)
		
	def _linger (self):
		"""
		Display for a short while
		"""
		self.show_all ()
		glib.timeout_add_seconds (self.linger_time, self.hide)
			
