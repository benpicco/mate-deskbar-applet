import gobject
import gtk
import deskbar.ui.iconentry

# Make epydoc document signal
__extra_epydoc_fields__ = [('signal', 'Signals')]


class CuemiacEntry (deskbar.ui.iconentry.IconEntry):
    """
    For all outside purposes this widget should appear to be a gtk.Entry
    with an icon inside it. Use it as such - if you find odd behavior
    don't work around it, but fix the behavior in this class instead.
    
    @signal icon-clicked: (C{gtk.gdk.Event})
    """
    
    __gsignals__ = { 
        "icon-clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "activate" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "go-next" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, []),
        "go-previous" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, []),
        }
        
    
    def __init__(self, default_pixbuf):
        deskbar.ui.iconentry.IconEntry.__init__ (self)
        
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
        self.handler_changed_id = self.entry.connect ("changed", lambda entry: self.emit("changed"))
        self.entry.connect ("activate", lambda entry: self.emit("activate"))
        self.entry.connect ("key-press-event", self.__on_key_press_event )
        self.entry.connect ("button-press-event", lambda entry, event: self.emit("button-press-event", event))
        self.entry.connect ("focus-out-event", lambda entry, event: self.emit("focus-out-event", event))

    def __on_key_press_event(self, entry, event):
        if event.keyval == gtk.keysyms.Down:
            ret = self.emit("go-next")
            if ret:
                return True
        elif event.keyval == gtk.keysyms.Up:
            ret = self.emit("go-previous")
            if ret:
                return True
        return self.emit("key-press-event", event)

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
        self.icon_event_box.set_tooltip_markup(tooltip)
        
    def set_entry_tooltip (self, tooltip):
        """
        @param tooltip: A string describing basic usage of the entry.
        """
        self.entry.set_tooltip_markup(tooltip)

    def show (self):
        """
        Show the the entry - including the icon.
        """
        self.show_all () # We need to show the icon

    def set_history_item(self, item):
        if item == None:
            self.set_icon( self._default_pixbuf )
            self.entry.set_text("")
        else:
            text, match = item
            self.entry.handler_block( self.handler_changed_id )
            self.entry.set_text(text)
            icon = match.get_icon()
            if icon == None:
                icon = self._default_pixbuf
            if isinstance(icon, gtk.gdk.Pixbuf) :
                pixbuf = icon
            else:
                pixbuf = deskbar.core.Utils.load_icon(icon)
            self.set_icon ( pixbuf )
            self.entry.select_region(0, -1)
            self.entry.handler_unblock( self.handler_changed_id )

    def _on_icon_button_press (self, widget, event):
        if not self.icon_event_box.get_property ('sensitive'):
            return False
        self.emit ("icon-clicked", event)
        return False    
