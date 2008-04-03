from deskbar.core.CoreImpl import CoreImpl
from deskbar.core.GconfStore import GconfStore
from deskbar.ui.CuemiacAlignedView import CuemiacAlignedView
from deskbar.ui.CuemiacWindowController import CuemiacWindowController
from deskbar.ui.CuemiacWindowView import CuemiacWindowView
import deskbar
import gtk
import gobject

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
        self._view = CuemiacAlignedView(self._controller, self._core, self.image, self.applet)
        self._active_view = deskbar.BUTTON_UI_NAME
        
    def create_window_ui(self):
        self._view = CuemiacWindowView(self._controller, self._core)
        self._active_view = deskbar.WINDOW_UI_NAME
            
    def _setup_mvc(self):
        self._core = CoreImpl(deskbar.MODULES_DIRS)
        self._core.connect("loaded", self.on_loaded)
        
        self._controller = CuemiacWindowController(self._core)

        # Select the view based on user choice. CuemiacWindowView is
        # the new style UI,
        # CuemiacAlignedView is the older UI as seen in the
        # Deskbar gnome-2-18 branch.
        if self._core.get_ui_name() == deskbar.WINDOW_UI_NAME:
            self.create_window_ui()
        else:
            # We need to use an AlignedWindow, which needs a Widget (self.image
            # in this case) and the applet (self.applet)
            self.create_button_ui()

        self._view.set_sensitive(False)
        
        GconfStore.get_instance().connect("ui-name-changed", self._on_ui_name_changed)
        
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
       
    def on_loaded(self, sender):
        """
        Called when all modules have been loaded and
        initialized. You should mark you UI
        sensitive here
        """
        self._view.set_sensitive(True)
      
    def setup_menu(self):
        """
        Setup popup menu
        """
        raise NotImplementedError
