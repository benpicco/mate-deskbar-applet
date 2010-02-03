import gtk
import gtk.gdk
import glib
import gnomeapplet
from deskbar.core.GconfStore import GconfStore
from deskbar.ui.AbstractCuemiacView import AbstractCuemiacView
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow

class CuemiacAlignedView(AbstractCuemiacView, CuemiacAlignedWindow):
    """
    This class is responsible for setting up the GUI.
    It displays the older version of deskbar's GUI, where the
    results window is aligned to the gnome panel.
    """
    
    VBOX_MAIN_SPACING = 12
    VBOX_MAIN_BORDER_WIDTH = 6
    
    def __init__(self, controller, model, widget, applet):
        AbstractCuemiacView.__init__(self, controller, model)
        CuemiacAlignedWindow.__init__(self, widget, applet)
        self._controller.register_view(self)
        self.applet = applet
        
        GconfStore.get_instance().connect("entry-width-changed",
                                          lambda s, w: self._change_entry_width(w))
        
        self.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_MENU)
        self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
        self.applet.set_flags(gtk.CAN_FOCUS)
        self.applet.connect("change-orient", self._on_change_orient)
        
        self._screen_height = self.get_screen().get_height ()
        self._screen_width = self.get_screen().get_width ()
        self._max_window_height = int (0.8 * self._screen_height)
        self._max_window_width = int (0.6 * self._screen_width)
        
        self.connect("delete-event", self._controller.on_quit)
        self.connect("destroy-event", self._controller.on_quit)
        self.connect("focus-out-event", self._controller.on_quit)
        self.connect("key-press-event", self.__on_window_key_press_event)
       
        self.set_title("Deskbar Applet")
        self.set_default_size( self._model.get_window_width(), -1 )

        self.set_role("deskbar-search-window")
        
        entry_width = self._model.get_entry_width()
        # Account for previous default entry width of 20
        if entry_width == 20:
            entry_width = 40
            self._model.set_entry_width(entry_width)
        self._change_entry_width(entry_width)
        
        # VBox
        self.add(self.vbox_main)
        
        # Results
        self.results_box = gtk.HBox()
        self.results_box.pack_start(self.scrolled_results)
        self.results_box.pack_start(self.actions_box)
        
        self.__set_layout_by_orientation(self.applet.get_orient())
        self.resize( *self.size_request() )
   
    def clear_all(self):
        AbstractCuemiacView.clear_all(self)
        self.applet.set_state(gtk.STATE_NORMAL)
        self.results_box.hide()
        self.__adjust_popup_size()
    
    def get_toplevel(self):
        return self
   
    def receive_focus(self, time):
        self.applet.set_state(gtk.STATE_SELECTED)
        self.update_position()
        w, h = self.size_request()
        self.resize(w, h)
        self.show()
        self.present_with_time(time)
        self.entry.grab_focus()
    
    def append_matches (self, sender, matches):
        AbstractCuemiacView.append_matches(self, sender, matches)
        # Wait a little bit to resize, otherwise we get a size that's too small
        glib.timeout_add(200, self.__adjust_popup_size)
    
    def __on_window_key_press_event(self, window, event):
        if event.keyval == gtk.keysyms.Escape:
            self.emit("destroy-event", event)
                
        return False
     
    def __adjust_popup_size (self):
        """adjust window size to the size of the children"""
        # FIXME: Should we handle width intelligently also?
        w, h = self.cview.size_request ()
        # To ensure we don't always show scrollbars
        h += self.header.allocation.height
        # Spacing between header and results_box
        h += self.VBOX_MAIN_SPACING
        # Border at the top and the bottom
        h += 2*self.VBOX_MAIN_BORDER_WIDTH
        # Some additional space
        h += 5 
        h = min (h, self._max_window_height)
        w = min (w, self._max_window_width)
        if w > 0 and h > 0:
            self.resize (w, h)
        return False
    
    def __set_layout_by_orientation (self, orient):
        """
        Adjust the various widgets managed to layout with repect to the given
        orientation.
        
        @param orient: The orientation to switch to. 
                    Must be one of C{gnomeapplet.ORIENT_UP}, C{gnomeapplet.ORIENT_DOWN},
                    C{gnomeapplet.ORIENT_LEFT}, C{gnomeapplet.ORIENT_RIGHT}.
        """
        if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
            self.vbox_main.pack_start(self.header, False)
            self.vbox_main.pack_start(self.results_box)
        else:
            # We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
            self.vbox_main.pack_start(self.results_box)
            self.vbox_main.pack_start(self.header, False)
            
        self._on_change_orient(self.applet, orient)
        
    def __set_sort_order_by_orientation(self, orient):
        if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
            self.treeview_model.set_sort_order (gtk.SORT_ASCENDING)
            self.actions_model.set_sort_order (gtk.SORT_ASCENDING)
            self._model.get_history().set_sort_order (gtk.SORT_DESCENDING)
        else:
            self.treeview_model.set_sort_order (gtk.SORT_DESCENDING)
            self.actions_model.set_sort_order (gtk.SORT_DESCENDING)
            self._model.get_history().set_sort_order (gtk.SORT_ASCENDING)

    def _on_change_orient(self, applet, orient):
        self.__set_sort_order_by_orientation(orient)
        if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
            self.vbox_main.reorder_child(self.header, 0)
            self.vbox_main.reorder_child(self.results_box, 2)
        else:
            self.vbox_main.reorder_child(self.results_box, 0)
            self.vbox_main.reorder_child(self.header, 2)
       
    def _change_entry_width(self, entry_width):
        if entry_width < 10:
            entry_width = 10
        self.get_entry().set_width_chars(entry_width)

