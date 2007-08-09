import gtk
import gobject

from gettext import gettext as _

class CuemiacHeader (gtk.Layout):
    def __init__ (self, entry):
        gtk.Layout.__init__ (self)
        
        self.xof = 20
        self.yof = 17
        self.padding = 5
        self.entry = entry
        
        self.label = gtk.Label ()
        self.label.set_markup (_("<b>Search:</b>"))
        
        self._map_source = self.connect ("map", self.on_map)
        self._style_source = self.connect ("notify::style", self.set_styles) # gtk theme changes
        self._ignore_style = False
        self.label.show()
        self.entry.show ()
        
    def on_map (self, widget):
        gobject.source_remove (self._map_source)
        # We need to do layout only after the top level window has been mapped
        # or else the styles wont pick up.
        self.do_layout ()

    def do_layout (self):
        self.put (self.label, self.xof, self.yof)
        w, h = self.label.get_layout().get_pixel_size ()
        
        self.put (self.entry,
            self.xof + w + self.padding,
            self.yof - h/3)
        self.set_size_request (400, 3*h)
        
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
