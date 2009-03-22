import gtk
import gtk.gdk
import gobject
from deskbar.ui.AbstractCuemiacView import AbstractCuemiacView

class CuemiacWindowView(AbstractCuemiacView, gtk.Window):
    """
    This class is responsible for setting up the GUI.
    """
    
    def __init__(self, controller, model):
        AbstractCuemiacView.__init__(self, controller, model)
        gtk.Window.__init__(self)
        self._controller.register_view(self)
        self.__small_window_height = None
        
        self.connect("configure-event", self.__save_window_size)
        self.connect("delete-event", self._controller.on_quit)
        self.connect("destroy-event", self._controller.on_quit)
        self.connect("focus-out-event", self._controller.on_quit) 
        self.connect("key-press-event", self.__on_window_key_press_event)
       
        self.set_title("Deskbar Applet")
        self.set_default_size( self._model.get_window_width(), -1 )
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_role("deskbar-search-window")
        self.set_property("skip-taskbar-hint", True)

        # Reset width to default
        self.get_entry().set_width_chars(-1)

        self.add(self.vbox_main)

        # Search entry
        self.vbox_main.pack_start(self.header, False)
        
        # Results
        self.results_box = gtk.HBox()
        self.results_box.connect("unmap", self.__save_window_height)
        self.results_box.pack_start(self.scrolled_results)
        self.results_box.pack_start(self.actions_box)
        self.vbox_main.pack_start(self.results_box)
   
    def clear_all(self):
        AbstractCuemiacView.clear_all(self)
        width, height = self.get_size()
        
        if self.__small_window_height != None:
            self.resize( width, self.__small_window_height )
        self.results_box.hide()
    
    def get_toplevel(self):
        return self
    
    def receive_focus(self, time):
        self.move( self._model.get_window_x(), self._model.get_window_y() )
        self.entry.grab_focus()
        self.realize()
        self.window.set_user_time(time)
        self.present()
    
    def show_results(self):
        AbstractCuemiacView.show_results(self)
        width, height = self.get_size()
        self.resize( width, self._model.get_window_height() )
   
    def __on_window_key_press_event(self, window, event):
        if event.keyval == gtk.keysyms.Escape:
            self.emit("destroy-event", event)
                
        return False
    
    def __save_window_size(self, window, event):
        """
        Save window width and height of the window when
        results_box is not visible
        """
        self._model.set_window_width( event.width )
        if self.__small_window_height == None:
            self.__small_window_height = event.height
            
    def __save_window_height(self, resultsbox):
        """
        Save window height before results_box disappears
        """
        self._model.set_window_height( self.get_size()[1] )
