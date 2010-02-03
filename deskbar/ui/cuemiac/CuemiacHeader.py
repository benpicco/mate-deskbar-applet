import gtk
import gtk.gdk
import glib

from gettext import gettext as _

class CuemiacHeader (gtk.EventBox):
    def __init__ (self, entry):
        gtk.EventBox.__init__ (self)
        
        self.xpadding = 0
        self.ypadding = 0
        self.spacing = 0
        self.entry = entry
        
        self.alignment = gtk.Alignment(xscale=1.0)
        self.alignment.set_padding(self.ypadding, self.ypadding, self.xpadding, self.xpadding)
        self.alignment.show()
        self.add(self.alignment)
        
        self.hbox = gtk.HBox(spacing=self.spacing)
        self.hbox.show()
        self.alignment.add(self.hbox)
        
        self.hbox.pack_start(self.entry)
        self.entry.show ()
        
if __name__ == "__main__":
    entry = gtk.Entry ()
    header = CuemiacHeader (entry)
    win = gtk.Window()
    win.add (header)
    win.resize (400, 60)
    win.show_all ()
    win.connect ("destroy", gtk.main_quit)
    gtk.main()
