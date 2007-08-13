import gtk
import gtk.gdk
import gobject

from gettext import gettext as _

class CuemiacHeader (gtk.Layout):
    def __init__ (self, entry):
        gtk.Layout.__init__ (self)
        
        self.xpadding = 50
        self.ypadding = 17
        self.spacing = 6
        self.min_entry_width = 200
        self.entry = entry
        
        self.label = gtk.Label ()
        self.label.set_markup (_("<b>Search:</b>"))
        
        self._map_source = self.connect ("map", self.on_map)
        self._style_source = self.connect ("notify::style", self.set_styles) # gtk theme changes
        self.connect("expose-event", self.on_expose)
        self._ignore_style = False
        self.label.show()
        self.entry.show ()
        
    def on_map (self, widget):
        gobject.source_remove (self._map_source)
        # We need to do layout only after the top level window has been mapped
        # or else the styles wont pick up.
        self.do_layout ()

    def do_layout (self):
        self.put (self.label, self.xpadding, self.ypadding)
        w, h = self.label.get_layout().get_pixel_size ()
        
        x =   self.xpadding + w + self.spacing
        y =   self.ypadding - h/3
        self.put (self.entry, x, y)
    
    def on_expose(self, widget, event):
        label_width, label_height = self.label.get_layout().get_pixel_size ()
        
        outer_width = event.area.width-2*self.xpadding
        entry_width = outer_width - 2*label_width
        
        if outer_width < -1:
            outer_width = -1
        if entry_width < -1:
            entry_width = -1
        
        self.entry.set_size_request (entry_width ,  -1)
        self.set_size_request (outer_width, 3*label_height)
       
    def set_styles (self, obj, prop):
        if self._ignore_style:
            return
        # Ignore style changes for the next split second,
        # since we trigger ones our selves (endless recursion)
        self._ignore_style = True 
        self.modify_bg (gtk.STATE_NORMAL, self.style.bg[gtk.STATE_SELECTED])
        self.label.modify_fg (gtk.STATE_NORMAL, self.style.fg[gtk.STATE_SELECTED])
        self.entry.modify_bg (gtk.STATE_NORMAL, self.style.bg[gtk.STATE_SELECTED])
        gobject.timeout_add (100, self._enable_styles) # reenable style changes
    
    def _enable_styles (self):
        self._ignore_style = False
        
        
if __name__ == "__main__":
    entry = gtk.Entry ()
    header = CuemiacHeader (entry)
    win = gtk.Window()
    win.add (header)
    win.resize (400, 60)
    win.show_all ()
    win.connect ("destroy", gtk.main_quit)
    gtk.main()
