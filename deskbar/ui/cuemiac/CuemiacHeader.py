import gtk
import gtk.gdk
import gobject

from gettext import gettext as _

class CuemiacHeader (gtk.EventBox):
    def __init__ (self, entry):
        gtk.EventBox.__init__ (self)
        
        self.xpadding = 50
        self.ypadding = 17
        self.spacing = 6
        self.entry = entry
        
        self.alignment = gtk.Alignment(xscale=1.0)
        self.alignment.set_padding(self.ypadding, self.ypadding, self.xpadding, self.xpadding)
        self.alignment.show()
        self.add(self.alignment)
        
        self.hbox = gtk.HBox(spacing=self.spacing)
        self.hbox.show()
        self.alignment.add(self.hbox)
        
        self.label = gtk.Label ()
        self.label.set_markup (_("<b>Search:</b>"))
        self.label.show()
        self.hbox.pack_start(self.label, False)
        
        self.hbox.pack_start(self.entry)
        self.entry.show ()
        
        self._style_source = self.connect ("notify::style", self.set_styles) # gtk theme changes
        self._ignore_style = False
              
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
