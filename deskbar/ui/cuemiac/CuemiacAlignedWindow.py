import gtk, gnomeapplet, gobject

class CuemiacAlignedWindow (gtk.Window):
	"""
	Borderless window aligning itself to a given widget.
	Use CuemiacWindow.update_position() to align it.
	"""
	def __init__(self, widgetToAlignWith, applet):
		"""
		alignment should be one of
			gnomeapplet.ORIENT_{DOWN,UP,LEFT,RIGHT}
		
		Call CuemiacWindow.update_position () to position the window.
		"""
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		self.set_decorated (False)

		# Skip the taskbar, and the pager, stick and stay on top
		self.stick()
		self.set_keep_above(True)
		self.set_skip_pager_hint(True)
		self.set_skip_taskbar_hint(True)
		
		self.widgetToAlignWith = widgetToAlignWith
		self.applet = applet
		self.alignment = applet.get_orient ()

		self.is_realized = False
		self.connect ("realize", lambda win : self.__register_realize ())
		
	def update_position (self):
		"""
		Calculates the position and moves the window to it.
		IMPORATNT: widgetToAlignWith should be realized!
		"""
		if not self.is_realized:
			self.realize ()
			
		# Get our own dimensions & position
		window_width  = (self.window.get_geometry())[2]
	   	window_height = (self.window.get_geometry())[3]

		# Get the dimensions/position of the widgetToAlignWith
		(x, y) = self.widgetToAlignWith.window.get_origin()

		(w, h) = self.size_request()

		target_w = self.widgetToAlignWith.allocation.width
		target_h = self.widgetToAlignWith.allocation.height

		screen = self.get_screen()
		# XXX: FIXME: we should get the monitor that the applet is on,
		# not the realised window
		monitor = screen.get_monitor_geometry (screen.get_monitor_at_window (self.applet.window))
		
		#print "monitor %i" % screen.get_monitor_at_window (self.applet.window)
		#print "x = %i, y = %i, w = %i, h = %i" % (x, y, target_w, target_h)
		#print "monitor: x = %i, y = %i, w = %i, h = %i" % (monitor.x, monitor.y, monitor.width, monitor.height)
		
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
				#print "got alignment:DOWN"
				y += target_h

				if ((x + target_w) > (monitor.x + monitor.width)):
					#print "will exceed monitor"
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
	
	def __register_realize (self):
		self.is_realized = True
		
gobject.type_register (CuemiacAlignedWindow)
