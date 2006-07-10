import gobject, gtk

import deskbar

# Make epydoc document signal
__extra_epydoc_fields__ = [('signal', 'Signals')]


class CuemiacEntry (deskbar.iconentry.IconEntry):
	"""
	For all outside purposes this widget should appear to be a gtk.Entry
	with an icon inside it. Use it as such - if you find odd behavior
	don't work around it, but fix the behavior in this class instead.
	
	@signal icon-clicked: (C{gtk.gdk.Event})
	"""
	
	__gsignals__ = { 
		"icon-clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		"activate" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
		}
		
	
	def __init__(self, default_pixbuf):
		deskbar.iconentry.IconEntry.__init__ (self)
		
		self.entry = self.get_entry ()
		self.entry_icon = gtk.Image ()
		self.icon_event_box = gtk.EventBox ()
		self._default_pixbuf = default_pixbuf
		
		# Set up the event box for the entry icon
		self.icon_event_box.set_property('visible-window', False)
		self.icon_event_box.add(self.entry_icon)
		self.pack_widget (self.icon_event_box, True)

		# Set up icon		
		self.entry_icon.set_property('pixbuf', self._default_pixbuf)
		self.icon_event_box.connect ("button-press-event", self._on_icon_button_press)
		
		# Set up "inheritance" of the gtk.Entry
		# methods
		self.get_text = self.entry.get_text
		self.set_text = self.entry.set_text
		self.select_region = self.entry.select_region
		self.set_width_chars = self.entry.set_width_chars
		self.get_width_chars = self.entry.get_width_chars
		self.get_position = self.entry.get_position
		self.set_position = self.entry.set_position

		# When applications want to forward events to,
		# this widget, it is 99% likely to want to forward 
		# to the underlying gtk.Entry widget, so:
		self.event = self.entry.event
		
		# Forward commonly used entry signals
		self.entry.connect ("changed", lambda entry: self.emit("changed"))
		self.entry.connect ("activate", lambda entry: self.emit("activate"))
		self.entry.connect ("key-press-event", lambda entry, event: self.emit("key-press-event", event))
		self.entry.connect ("button-press-event", lambda entry, event: self.emit("button-press-event", event))
		self.entry.connect ("focus-out-event", lambda entry, event: self.emit("focus-out-event", event))
		
		# Set up tooltips
		self.tooltips = gtk.Tooltips()

	def grab_focus (self):
		"""
		Focus the entry, ready for text input.
		"""
		self.entry.grab_focus ()

	def set_sensitive (self, active):
		"""
		Set sensitivity of the entry including the icon.
		"""
		self.set_property ("sensitive", active)
		self.entry_icon.set_sensitive (active)
		self.icon_event_box.set_sensitive (active)

	def get_image (self):
		"""
		@return: The C{gtk.Image} packed into this entry.
		"""
		return self.entry_icon

	def set_icon (self, pixbuf):
		"""
		Set the icon in the entry to the given pixbuf.
		@param pixbuf: A C{gtk.gdk.Pixbuf}.
		"""
		self.entry_icon.set_property('pixbuf', pixbuf)
		self.entry_icon.set_size_request(deskbar.ICON_WIDTH, deskbar.ICON_HEIGHT)

	def set_icon_tooltip (self, tooltip):
		"""
		@param tooltip: A string describing the action associated to clicking the entry icon.
		"""
		self.tooltips.set_tip (self.icon_event_box, tooltip)
		
	def set_entry_tooltip (self, tooltip):
		"""
		@param tooltip: A string describing basic usage of the entry.
		"""
		self.tooltips.set_tip(self.entry, tooltip)

	def show (self):
		"""
		Show the the entry - including the icon.
		"""
		self.show_all () # We need to show the icon

	def _on_icon_button_press (self, widget, event):
		if not self.icon_event_box.get_property ('sensitive'):
			return False
		self.emit ("icon-clicked", event)
		return False	
