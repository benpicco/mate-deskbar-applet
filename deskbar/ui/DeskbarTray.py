from deskbar.ui.AbstractCuemiacDeskbarIcon import AbstractCuemiacDeskbarIcon
from gettext import gettext as _
from os.path import join
import deskbar
import gnomeapplet
import gobject
import gtk
        
class DeskbarTray (gtk.EventBox, AbstractCuemiacDeskbarIcon):
    """
    It automatically arranges itself according to one of 
    gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
    """

    def __init__ (self, applet):
        gtk.EventBox.__init__ (self)
        AbstractCuemiacDeskbarIcon.__init__(self)
        
        gtk.EventBox.set_visible_window(self, False)
        gtk.EventBox.set_sensitive(self, False)
        
        self.applet = applet
        self.applet.set_background_widget(applet)
        self.applet.set_applet_flags (gnomeapplet.EXPAND_MINOR)
        self.applet.connect ("change-size", self.on_change_size)
        # popup_dir = gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}
        self.popup_dir = applet.get_orient()
        
        self.image = gtk.Image ()
        gtk.EventBox.add(self, self.image)
        gtk.EventBox.connect(self, 'button-press-event', self.on_button_press)
        
        self.tooltips = gtk.Tooltips()
        self.tooltips.set_tip(self, _("Show search entry"))
        
        self.setup_menu()
        self._setup_mvc()
        
        self.on_change_size(self.applet, self.applet.get_size())
    
    def on_button_press(self, widget, event):
        if event.button == 1: # left mouse button
            AbstractCuemiacDeskbarIcon.set_active (self, not self.active, event.time)
            return True
       
    def on_loaded(self, sender):
        AbstractCuemiacDeskbarIcon.on_loaded (self, sender)
        gtk.EventBox.set_sensitive(self, True)
        
    def set_button_image_from_file (self, filename, size):
        # We use an intermediate pixbuf to scale the image
        if self.popup_dir in [gnomeapplet.ORIENT_DOWN, gnomeapplet.ORIENT_UP]:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size (filename, -1, size)
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size (filename, size, -1)
        self.image.set_from_pixbuf (pixbuf)
        
    def on_change_size (self, applet, size):
        # FIXME: This is ugly, but i don't know how to get it right
        image_name = "deskbar-applet-panel"
        if self.applet.get_orient () in [gnomeapplet.ORIENT_UP, gnomeapplet.ORIENT_DOWN]:
            image_name += "-h"
        else:
            image_name += "-v"
        
        if size > 36 and self._has_svg_support():
            image_name += ".svg"
            s = size-12
        else:
            image_name += ".png"
            s = -1
        
        self.set_button_image_from_file (join(deskbar.ART_DATA_DIR, image_name), s)
        
        self.set_size_request (size, size)
    
    def setup_menu(self):
        self.applet.setup_menu_from_file (
            deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml",
            None, [
            ("About", lambda a,b: self._controller.on_show_about(a)),
            ("Prefs", lambda a,b: self._controller.on_show_preferences(a)),
            ("Clear", lambda a,b: self._controller.on_clear_history(a),),
            ("Help", lambda a,b: self._controller.on_show_help(a),)
            ])
         
if gtk.pygtk_version < (2,8,0):            
    gobject.type_register(DeskbarTray)