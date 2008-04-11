import gtk
import gobject
import pango

class CuemiacCellRenderer (gtk.CellRendererText):
    """
    Base class for CuemiacCellRendererAction and CuemiacCellRendererMatch
    """
    
    __gsignals__ = {
        "activated": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
    }
    
    def __init__ (self):
        gtk.CellRendererText.__init__ (self)
        
        self.set_property("mode", gtk.CELL_RENDERER_MODE_ACTIVATABLE)
        self.__relative_header_size = -0.2 # Make header 20% smaller than normal fonts
        
        # Grab some default theme settings
        # they are probably incorrect, but we reset
        # them on each render anyway.
        style = gtk.Style ()
        self.header_font_desc = style.font_desc
        self.header_font_desc.set_weight (pango.WEIGHT_BOLD)        
        self.header_font_desc.set_size (self.header_font_desc.get_size () + int(self.header_font_desc.get_size ()*self.__relative_header_size))
        self.header_bg = style.base [gtk.STATE_NORMAL]
        
    def set_style (self, widget):
        """
        Apply the style from widget, to this cellrenderer
        """
        self.header_font_desc = widget.style.font_desc
        self.header_font_desc.set_weight (pango.WEIGHT_BOLD)
        self.header_font_desc.set_size (self.header_font_desc.get_size () + int(self.header_font_desc.get_size ()*self.__relative_header_size))
        self.header_bg = widget.style.base [gtk.STATE_NORMAL]
    
    def renderer_state_to_widget_state(self, flags):
        state = 0
        
        if (gtk.CELL_RENDERER_SELECTED & flags) == gtk.CELL_RENDERER_SELECTED:
            state |= gtk.STATE_SELECTED
        if (gtk.CELL_RENDERER_PRELIT & flags) == gtk.CELL_RENDERER_PRELIT:
            state |= gtk.STATE_PRELIGHT
        if (gtk.CELL_RENDERER_INSENSITIVE & flags) == gtk.CELL_RENDERER_INSENSITIVE:
            state |= gtk.STATE_INSENSITIVE
        if state == 0:
            state= gtk.STATE_NORMAL
        return state
    
    def do_activate(self, event, widget, path_string, background_area, cell_area, flags):
        if not isinstance(widget, gtk.TreeView):
            # Not a treeview
            return False
        
        if event == None or event.type != gtk.gdk.BUTTON_PRESS:
            # Event type not GDK_BUTTON_PRESS
            return True
        
        path = tuple([int(i) for i in path_string.split(':')])
        self.emit("activated", path)
        return True
