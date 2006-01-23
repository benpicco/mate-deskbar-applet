import gtk
import gnomeapplet
import gobject

class DeskbarAppletButton (gtk.HBox):
	"""
	Button consisting of two toggle buttons. A "main" with and image, and an "arrow"
	with a gtk.Arrow.
	
	It automatically arranges itself according to one of 
	gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
	
	Signals:
		toggled-main: The main button has been toggled
		toggle-arrow: the arrow button has been toggled
		
	The widget implements an interface like the gtk.ToggleButton, with _main or _arrow
	appended to method names for each button.
	"""
	__gsignals__ = {
		"toggled-main" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		"toggled-arrow" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
	}

	def __init__ (self, applet):
		"""
		popup_dir: gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}
		set the image in the main button with DeskbarAppletButton.set_button_image_from_file(filename)
		"""
		gtk.HBox.__init__ (self)
		self.applet = applet
		self.popup_dir = applet.get_orient()
		
		if self.popup_dir in [gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_DOWN]:
			self.box = gtk.HBox ()
		else:
			self.box = gtk.VBox ()
					
		self.button_main = gtk.ToggleButton ()
		self.button_main.set_relief (gtk.RELIEF_NONE)
		self.image = gtk.Image ()
		self.button_main.add (self.image)
		self.button_main.connect ("toggled", lambda widget: self.emit ("toggled-main", widget))
		
		self.button_arrow = gtk.ToggleButton ()
		self.button_arrow.set_relief (gtk.RELIEF_NONE)
		self.arrow = gtk.Arrow (self.gnomeapplet_dir_to_arrow_dir(self.popup_dir), gtk.SHADOW_IN)
		self.button_arrow.add (self.arrow)
		self.button_arrow.connect ("toggled", lambda widget: self.emit ("toggled-arrow", widget))
				
		if self.popup_dir in [gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_DOWN]:
			self.separator = gtk.VSeparator ()
		else:
			self.separator = gtk.HSeparator ()
		
		self.box.pack_start (self.button_arrow, False)
		self.box.pack_start (self.separator, False)
		self.box.pack_start (self.button_main)
		self.add (self.box)
	
		self.connect("button-press-event", self.on_button_press_event)
		self.button_arrow.connect("button-press-event", self.on_button_press_event)
		self.button_main.connect("button-press-event", self.on_button_press_event)
		self.separator.connect("button-press-event", self.on_button_press_event)
	
	def on_button_press_event(self, widget, event):
		if event.button == 3:
			self.applet.emit("button-press-event", event)
			return True
		
		return False
		
	def toggle_main (self):
		self.button_main.toggled ()
		
	def toggle_arrow (self):
		self.button_arrow.toggled ()
	
	def get_active_main (self):
		return self.button_main.get_active ()
	
	def set_active_main (self, is_active):
		self.button_main.set_active (is_active)
	
	def get_active_arrow (self):
		return self.button_arrow.get_active ()

	def set_active_arrow (self, is_active):
		self.button_arrow.set_active (is_active)
			
	def set_button_image_from_file (self, filename):
		# FIXME: Take self.popup_dir into account. Rotate img if necesary

		# We use an intermediate pixbuf to scale the image
		if self.popup_dir in [gnomeapplet.ORIENT_DOWN, gnomeapplet.ORIENT_UP]:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size (filename, 40, 18)
		else:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size (filename, 18, 40)
		self.image.set_from_pixbuf (pixbuf)
		
	def gnomeapplet_dir_to_arrow_dir (self, gnomeapplet_dir):
		"""
		Returns the appropriate gtk.ARROW_{UP,DOWN,LEFT,RIGHT} corresponding
		to gnomeapplet_dir; which can be one of
		gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}
		"""
		if gnomeapplet_dir == gnomeapplet.ORIENT_DOWN:
			return gtk.ARROW_DOWN
		elif gnomeapplet_dir == gnomeapplet.ORIENT_UP:
			return gtk.ARROW_UP
		elif gnomeapplet_dir == gnomeapplet.ORIENT_LEFT:
			print "l"
			return gtk.ARROW_LEFT
		else:
			return gtk.ARROW_RIGHT
	
	def set_orientation (self, orientation, reshow=True):
		"""orientation should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
		reshow indicates whether or not the widget should call show() on all
		its children."""
		self.remove (self.box)	
		self.box.remove (self.button_arrow)
		self.box.remove (self.separator)
		self.box.remove (self.button_main)
		self.button_arrow.remove (self.arrow)
		
		if orientation in [gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_DOWN]:
			self.box = gtk.HBox ()
			self.separator = gtk.VSeparator ()
		else:
			self.box = gtk.VBox ()
			self.separator = gtk.HSeparator ()
		
		self.arrow = gtk.Arrow (self.gnomeapplet_dir_to_arrow_dir(orientation), gtk.SHADOW_IN)
		
		self.add (self.box)
		self.box.pack_start (self.button_arrow, False)
		self.button_arrow.add (self.arrow)
		self.box.pack_start (self.separator, False)
		self.box.pack_start (self.button_main)
		
		if reshow:
			self.show_all ()
		
if __name__ == "__main__":
	button = DeskbarAppletButton (gnomeapplet.ORIENT_RIGHT)
	
	win = gtk.Window ()
	win.connect ("destroy", gtk.main_quit)
	win.add (button)
	win.show_all ()
		
	button.set_button_image_from_file ("/home/mikkel/Documents/deskbar.svg")
	
	button.connect ("toggled-main", lambda x,y: button.set_orientation (gnomeapplet.ORIENT_DOWN))
	button.connect ("toggled-arrow", lambda x,y: button.set_orientation (gnomeapplet.ORIENT_RIGHT))
	
	gtk.main ()
