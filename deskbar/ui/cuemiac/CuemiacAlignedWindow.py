import gtk, gnomeapplet, gobject

class CuemiacAlignedWindow (gtk.Window):
	"""
	Borderless window aligning itself to a given widget.
	Use CuemiacWindow.update_position() to align it.
	"""
	def __init__(self, widgetToAlignWith, alignment):
		"""
		alignment should be one of
			gnomeapplet.ORIENT_{DOWN,UP,LEFT,RIGHT}
		
		Call CuemiacWindow.update_position () to position the window.
		"""
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.set_decorated (False)
		self.set_focus_on_map (True) # grab focus when popping up
		
		# Skip the taskbar, and the pager, stick and stay on top
		self.stick()
		self.set_keep_above(True)
		self.set_skip_pager_hint(True)
		self.set_skip_taskbar_hint(True)
		#self.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_DOCK) # This line makes me unable to focus the window
		
		self.widgetToAlignWith = widgetToAlignWith
		self.alignment = alignment
		
		self.connect_after('realize', self.update_position)
		
	def update_position (self, widget):
		"""
		Calculates the position and moves the window to it.
		IMPORATNT: widgetToAlignWith should be realized!
		"""
		# Get our own dimensions & position
		window_width  = (self.window.get_geometry())[2]
	   	window_height = (self.window.get_geometry())[3]

		# Get the dimensions/position of the widgetToAlignWith
		(x, y) = self.widgetToAlignWith.window.get_origin()

		(w, h) = self.size_request()

		target_w = self.widgetToAlignWith.allocation.width
		target_h = self.widgetToAlignWith.allocation.height

		screen = self.get_screen()

		found_monitor = False
		n = screen.get_n_monitors()
		for i in range(0, n):
				monitor = screen.get_monitor_geometry(i)
				if (x >= monitor.x and x <= monitor.x + monitor.width and \
					y >= monitor.y and y <= monitor.y + monitor.height):
						found_monitor = True
						break
		
		if not found_monitor:
				monitor = gtk.gdk.Rectangle(0, 0, screen.get_width(), screen.get_width())
		
		self.alignment
		if self.alignment == gnomeapplet.ORIENT_RIGHT:
				x += target_w

				if ((y + h) > monitor.y + monitor.height):
						y -= (y + h) - (monitor.y + monitor.height)
				
				if ((y + h) > (monitor.height / 2)):
						gravity = gtk.gdk.GRAVITY_SOUTH_WEST	
				else:
						gravity = gtk.gdk.GRAVITY_NORTH_WEST
		elif self.alignment == gnomeapplet.ORIENT_LEFT:
				x -= w

				if ((y + h) > monitor.y + monitor.height):
						y -= (y + h) - (monitor.y + monitor.height)
				
				if ((y + h) > (monitor.height / 2)):
						gravity = gtk.gdk.GRAVITY_SOUTH_EAST
				else:
						gravity = gtk.gdk.GRAVITY_NORTH_EAST
		elif self.alignment == gnomeapplet.ORIENT_DOWN:
				y += target_h

				if ((x + w) > monitor.x + monitor.width):
						x -= (x + w) - (monitor.x + monitor.width)

				gravity = gtk.gdk.GRAVITY_NORTH_WEST
		elif self.alignment == gnomeapplet.ORIENT_UP:
				y -= h
				print h

				if ((x + w) > monitor.x + monitor.width):
						x -= (x + w) - (monitor.x + monitor.width)

				gravity = gtk.gdk.GRAVITY_SOUTH_WEST
		
		self.move(x, y)
		self.set_gravity(gravity)
				
gobject.type_register (CuemiacAlignedWindow)
