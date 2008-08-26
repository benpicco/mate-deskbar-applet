from deskbar.core.CoreImpl import CoreImpl
from deskbar.core.GconfStore import GconfStore
from deskbar.core.Utils import load_icon_from_icon_theme
from deskbar.ui.CuemiacAlignedView import CuemiacAlignedView
from deskbar.ui.CuemiacWindowController import CuemiacWindowController
from deskbar.ui.CuemiacWindowView import CuemiacWindowView
import deskbar
import gtk
import gobject

ICON_NAME = "deskbar-applet"

class AbstractCuemiacDeskbarIcon (object):
    
    def __init__(self):
        self.active = False
          
    def get_active(self):
        return self.active
    
    def set_active(self, active, time):
        changed = (self.active != active)
        self.active = active
        
        if changed:
            self._show_toggle(self, time)
      
    def create_button_ui(self):
        self._view = CuemiacAlignedView(self._controller, self._core,
                                        self.get_reference_widget(), self.get_applet())
        self._active_view = deskbar.BUTTON_UI_NAME
        
    def create_window_ui(self):
        self._view = CuemiacWindowView(self._controller, self._core)
        self._active_view = deskbar.WINDOW_UI_NAME
            
    def _setup_core (self):
        self._core = CoreImpl(deskbar.MODULES_DIRS)
        self._core.connect("loaded", self.on_loaded)
        
    def _setup_controller (self, core):
        self._controller = CuemiacWindowController(core)
        
    def _setup_view (self, core, window_type):
        # Select the view based on user choice. CuemiacWindowView is
        # the new style UI,
        # CuemiacAlignedView is the older UI as seen in the
        # Deskbar gnome-2-18 branch.
        if window_type == deskbar.WINDOW_UI_NAME:
            self.create_window_ui()
        else:
            # We need to use an AlignedWindow, which needs a Widget (self.image
            # in this case) and the applet (self.applet)
            self.create_button_ui()

        self._view.set_sensitive(False)
        
        # we want to update active when the window is closed
        self._view.get_toplevel().connect("notify::visible", self.__on_toplevel_visible_notify)
        
        GconfStore.get_instance().connect("ui-name-changed", self._on_ui_name_changed)
            
    def _setup_mvc(self):
        self._setup_core()
        self._setup_controller(self._core)
        self._setup_view(self._core, self._core.get_ui_name())
        
        self._core.run()
        
    def _show_toggle(self, widget, time):
        self._controller.on_keybinding_activated(widget, time, False)
        
    def _on_ui_name_changed(self, gconfstore, name):
        if name != self._active_view:
            self._view.destroy()
            if name == deskbar.WINDOW_UI_NAME:
                self.create_window_ui()
            else:
                self.create_button_ui()
            self._active_view = name
        
    def _has_svg_support (self):
        for format in gtk.gdk.pixbuf_get_formats():
            if format["name"] == "svg":
                return True
        return False
    
    def __on_toplevel_visible_notify(self, widget, param):
        self.active = widget.get_property("visible")
        
    def get_deskbar_icon(self, size):
        if size < 24:
            size = 16
        elif size < 32:
            size = 22
        elif size < 48:
            size = 32
        elif size >= 48:
            if not self._has_svg_support():
                size = 48
        
        return load_icon_from_icon_theme (ICON_NAME, size)
        
    def on_loaded(self, sender):
        """
        Called when all modules have been loaded and
        initialized. You should mark the UI
        sensitive here
        """
        self._view.set_sensitive(True)
      
    def setup_menu(self):
        """
        Setup popup menu
        """
        raise NotImplementedError
    
    def get_reference_widget(self):
        """
        Required by CuemiacAlignedView
        """
        raise NotImplementedError
    
    def get_applet(self):
        """
        Required by CuemiacAlignedView
        """
        raise NotImplementedError
