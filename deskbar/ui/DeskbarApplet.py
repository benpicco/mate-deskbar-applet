import gnomeapplet
import gtk
import deskbar
import os.path
import gobject
from deskbar.ui.AbstractCuemiacDeskbarIcon import AbstractCuemiacDeskbarIcon
from gettext import gettext as _

class DeskbarApplet (gnomeapplet.Applet, AbstractCuemiacDeskbarIcon):
    
    def __init__(self, applet):
        gnomeapplet.Applet.__init__(self)
        AbstractCuemiacDeskbarIcon.__init__(self)
        
        self.applet = applet
        
        self.handler_size_allocate_id = self.applet.connect ("size-allocate", self.on_allocate)
        self.applet.set_applet_flags (gnomeapplet.EXPAND_MINOR)
        self.applet.set_background_widget(self)
        
        self.tray = gtk.EventBox()
        self.tray.set_visible_window(False)
        self.tray.set_sensitive(False)
        self.tray.connect('button-press-event', self.on_button_press)
        self.applet.add(self.tray)
        self.tray.show()
        
        self.tooltips = gtk.Tooltips()
        self.tooltips.set_tip(self.tray, _("Show search entry"))
        
        self.image = gtk.Image ()
        self.tray.add(self.image)
        self.image.show()
        
        self.setup_menu()
        self._setup_mvc()
        
        self._set_image(self.applet.get_size())
        
        self.applet.show_all()

    def on_allocate(self, applet, alloc):
        if self.applet.get_orient () in [gnomeapplet.ORIENT_UP, gnomeapplet.ORIENT_DOWN]:
            size_alloc = alloc.height
        else:
            size_alloc = alloc.width
            
        self._set_image(size_alloc)
        
    def _set_image(self, size_alloc):
        """
        @param size_alloc: The space that's available in pixels
        """
        pixbuf = self.get_deskbar_icon(size_alloc)
        
        self.applet.handler_block(self.handler_size_allocate_id)
        self.image.set_from_pixbuf (pixbuf)
        self.tray.set_size_request (size_alloc, size_alloc)
        # If we unblock immediately we get an infinite loop
        gobject.timeout_add(100, self.unblock_allocate)
        
    def unblock_allocate(self):
        self.applet.handler_unblock (self.handler_size_allocate_id)
        return False
    
    def on_button_press(self, widget, event):
        if event.button == 1: # left mouse button
            self.set_active (not self.get_active(), event.time)
            return True
    
    def get_reference_widget(self):
        return self.image
    
    def get_applet(self):
        return self.applet
      
    def on_loaded(self, sender):
        AbstractCuemiacDeskbarIcon.on_loaded (self, sender)
        self.tray.set_sensitive(True)
      
    def setup_menu(self):
        self.applet.setup_menu_from_file (
            deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml",
            None, [
            ("About", lambda a,b: self._controller.on_show_about(a)),
            ("Prefs", lambda a,b: self._controller.on_show_preferences(a)),
            ("Clear", lambda a,b: self._controller.on_clear_history(a),),
            ("Help", lambda a,b: self._controller.on_show_help(a),)
            ])
        