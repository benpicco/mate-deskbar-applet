import gnomeapplet
import gtk
import deskbar
import os.path
import glib
import gobject
from deskbar.ui.AbstractCuemiacDeskbarIcon import AbstractCuemiacDeskbarIcon
from deskbar.ui.cuemiac.CuemiacHistory import CuemiacHistoryView, CuemiacHistoryPopup
from gettext import gettext as _

class ToggleEventBox(gtk.EventBox):
    __gsignals__ = {
        "toggled" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
    }
    
    def __init__(self):
        gtk.EventBox.__init__(self)
        self.active = False
        self.set_visible_window(False)
        self.connect('button-press-event', self.on_button_press)
    
    def on_button_press(self, widget, event):
        if event.button == 1:
            self.set_active(not self.active)
            return True
                
    def get_active(self):
        return self.active
    
    def set_active(self, active):
        changed = (self.active != active)
        self.active = active
        
        if changed:
            self.emit("toggled")
    
class CuemiacAppletButton (gtk.HBox):
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
        "toggled-main" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "toggled-arrow" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])
    }

    def __init__ (self, applet):
        gtk.HBox.__init__ (self)
        self.applet = applet
        self.applet.connect("change-orient", lambda applet, orient: self.set_layout_by_orientation(orient))
        self.arrow = None
        self.box = None
        popup_dir = applet.get_orient()
            
        self.button_main = ToggleEventBox()
        self.button_main.connect ("toggled", lambda widget: self.emit ("toggled-main"))
        
        self.image = gtk.Image ()
        self.button_main.add (self.image)
        
        self.button_arrow = ToggleEventBox()
        self.button_arrow.connect ("toggled", lambda widget: self.emit ("toggled-arrow"))
                
        self.button_main.set_tooltip_markup(_("Show search entry"))
        self.button_arrow.set_tooltip_markup(_("Show previously used actions"))
        
        self.set_layout_by_orientation(popup_dir)
        
    def get_active_main (self):
        return self.button_main.get_active ()
    
    def set_active_main (self, is_active):
        self.button_main.set_active (is_active)
    
    def get_active_arrow (self):
        return self.button_arrow.get_active ()

    def set_active_arrow (self, is_active):
        self.button_arrow.set_active (is_active)
            
    def set_button_image_from_pixbuf (self, pixbuf):
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
            return gtk.ARROW_LEFT
        else:
            return gtk.ARROW_RIGHT
    
    def set_layout_by_orientation (self, orientation):
        """
        @param orientation: should be a gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
        
        This method calls self.show_all()
        """
        if self.box != None:
            self.box.remove (self.button_arrow)
            self.box.remove (self.button_main)
            self.remove (self.box)
        if self.arrow != None:
            self.button_arrow.remove (self.arrow)
        
        if orientation in [gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_DOWN]:
            self.box = gtk.HBox ()
        else:
            self.box = gtk.VBox ()
                
        self.arrow = gtk.Arrow (self.gnomeapplet_dir_to_arrow_dir(orientation), gtk.SHADOW_IN)
        
        self.add (self.box)
        self.button_arrow.add (self.arrow)
        
        self.box.pack_start (self.button_main)
        self.box.pack_end (self.button_arrow, False, False)
                
        self.show_all ()
    
    
class DeskbarApplet (gnomeapplet.Applet, AbstractCuemiacDeskbarIcon):
    
    def __init__(self, applet):
        gnomeapplet.Applet.__init__(self)
        AbstractCuemiacDeskbarIcon.__init__(self)
        
        self.applet = applet
        
        self.handler_size_allocate_id = self.applet.connect ("size-allocate", self.on_allocate)
        self.applet.set_applet_flags (gnomeapplet.EXPAND_MINOR)
        self.applet.set_background_widget(self.applet)
        
        self.tray = CuemiacAppletButton(applet)
        self.tray.connect('toggled-main', self.on_toggled_main)
        self.tray.connect('toggled-arrow', self.on_toggled_arrow)
        self.applet.add(self.tray)
        self.tray.show()
        
        self.__style_applied = False
        self.force_no_focus_applet()
        
        self.setup_menu()
        self._setup_mvc()
        
        self._set_image(self.applet.get_size())
        
        self._setup_history()
        
        self.applet.show_all()

    def force_no_focus_applet(self):
        # Fixes bug #542861: Deskbar applet has a pixel border
        if not self.__style_applied:
            gtk.rc_parse_string ("""
               style \"deskbar-applet-button-style\"
               {
                 GtkWidget::focus-line-width = 0
                 GtkWidget::focus-padding = 0
               }
               widget \"*.deskbar-applet-button\" style \"deskbar-applet-button-style\"
               """)
            self.__style_applied = False
        self.applet.set_name("deskbar-applet-button")

    def _setup_history(self):
        self.hview = CuemiacHistoryView(self._core.get_history())
        self.hview.connect("match-selected", self.__on_history_match_selected)
        self.hview.show()
        
        self.history_popup = CuemiacHistoryPopup (self.tray.button_arrow,
                            self.applet,
                            self.hview)

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
        self.tray.set_button_image_from_pixbuf(pixbuf)
        # If we unblock immediately we get an infinite loop
        glib.timeout_add(100, self.unblock_allocate)
        
    def unblock_allocate(self):
        self.applet.handler_unblock (self.handler_size_allocate_id)
        return False
    
    def on_toggled_main(self, widget):
        self.set_active (not self.get_active(),
                          gtk.get_current_event_time())
    
    def on_toggled_arrow(self, widget):
        self._controller.on_quit()
        if self.history_popup.get_property("visible"):
            self.history_popup.popdown()
        else:
            self.history_popup.popup()
    
    def get_reference_widget(self):
        return self.tray
    
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
        
    def __on_history_match_selected(self, history, text, action):
        self._controller.on_history_match_selected(history, text, action)
        self.tray.set_active_arrow(False)
        