import gtk
import gnomeapplet
import gobject
from gettext import gettext as _
import deskbar
from os.path import join
from deskbar.core.CoreImpl import CoreImpl
from deskbar.ui.CuemiacWindowView import CuemiacWindowView
from deskbar.ui.CuemiacAlignedView import CuemiacAlignedView
from deskbar.ui.CuemiacWindowController import CuemiacWindowController
from deskbar.core.GconfStore import GconfStore
        
class DeskbarTray (gtk.EventBox):
    """
    Button consisting of a image.
    
    It automatically arranges itself according to one of 
    gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
    
    Signals:
        toggled-main: The main button has been toggle
    """
    __gsignals__ = {
        "toggled-main" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
    }

    def __init__ (self, applet):
        gtk.EventBox.__init__ (self)
        self.active = False
        self.set_visible_window(False)
        self.set_sensitive(False)
        
        self.applet = applet
        self.applet.set_background_widget(applet)
        self.applet.connect ("change-size", self.on_change_size)
        # popup_dir = gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}
        self.popup_dir = applet.get_orient()
        
        self.image = gtk.Image ()
        self.add(self.image)
        self.connect('button-press-event', self.on_button_press)
        
        self.tooltips = gtk.Tooltips()
        self.tooltips.set_tip(self, _("Show search entry"))
        
        self.__setup_applet_menu()
        self.__setup_mvc()
        
        self.on_change_size(self.applet, self.applet.get_size())
    
    def on_button_press(self, widget, event):
        if event.button == 1: # left mouse button
            self.set_active(not self.active, event.time)
            return True
                
    def get_active(self):
        return self.active
    
    def set_active(self, active, time):
        changed = (self.active != active)
        self.active = active
        
        if changed:
            self.__show_toggle(self, time)
            self.emit ("toggled-main", self)
    
    def __setup_mvc(self):
        self.__core = CoreImpl(deskbar.MODULES_DIRS)
        self.__core.connect("loaded", self.__on_loaded)
        
        self.__controller = CuemiacWindowController(self.__core)

        # Select the view based on user choice. CuemiacWindowView is
        # the new style UI,
        # CuemiacAlignedView is the older UI as seen in the
        # Deskbar gnome-2-18 branch.
        if self.__core.get_ui_name() == deskbar.WINDOW_UI_NAME:
            self.__create_window_ui()
        else:
            # We need to use an AlignedWindow, which needs a Widget (self.image
            # in this case) and the applet (self.applet)
            self.__create_button_ui()

        self.__view.set_sensitive(False)
        
        GconfStore.get_instance().connect("ui-name-changed", self.__on_ui_name_changed)
        
        self.__core.run()
        
    def __create_button_ui(self):
        self.__view = CuemiacAlignedView(self.__controller, self.__core, self.image, self.applet)
        self._active_view = deskbar.BUTTON_UI_NAME
        
    def __create_window_ui(self):
        self.__view = CuemiacWindowView(self.__controller, self.__core)
        self._active_view = deskbar.WINDOW_UI_NAME
        
    def __setup_applet_menu(self):
        self.applet.setup_menu_from_file (
            deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml",
            None, [
            ("About", lambda a,b: self.__controller.on_show_about(a)),
            ("Prefs", lambda a,b: self.__controller.on_show_preferences(a)),
            ("Clear", lambda a,b: self.__controller.on_clear_history(a),),
            ("Help", lambda a,b: self.__controller.on_show_help(a),)
            ])
        
    def __on_loaded(self, sender):
        self.set_sensitive(True)
        self.__view.set_sensitive(True)
          
    def __show_toggle(self, widget, time):
        self.__controller.on_keybinding_activated(widget, time, False)
        
    def __on_ui_name_changed(self, gconfstore, name):
        if name != self._active_view:
            self.__view.destroy()
            if name == deskbar.WINDOW_UI_NAME:
                self.__create_window_ui()
            else:
                self.__create_button_ui()
            self._active_view = name
    
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
        
        if size <= 36:
            image_name += ".png"
            s = -1
        else:
            image_name += ".svg"
            s = size-12
        
        self.set_button_image_from_file (join(deskbar.ART_DATA_DIR, image_name), s)
        
        self.set_size_request( size, size )
            
if gtk.pygtk_version < (2,8,0):            
    gobject.type_register(DeskbarTray)