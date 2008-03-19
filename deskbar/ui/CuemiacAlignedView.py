import gtk
import gtk.gdk
import gobject
import gnomeapplet
from gettext import gettext as _
import deskbar.interfaces.View
import deskbar.core.Utils
from deskbar.ui.cuemiac.CuemiacEntry import CuemiacEntry
from deskbar.ui.cuemiac.CuemiacHeader import CuemiacHeader
from deskbar.ui.cuemiac.CuemiacModel import CuemiacModel
from deskbar.ui.cuemiac.CuemiacTreeView import CuemiacTreeView
from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory
from deskbar.ui.cuemiac.CuemiacHistory import CuemiacHistoryView
from deskbar.ui.cuemiac.CuemiacActionsTreeView import CuemiacActionsTreeView, CuemiacActionsModel
from deskbar.ui.cuemiac.LingeringSelectionWindow import LingeringSelectionWindow
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow

class CuemiacAlignedView(deskbar.interfaces.View, CuemiacAlignedWindow):
    """
    This class is responsible for setting up the GUI.
    It displays the older version of deskbar's GUI, where the
    results window is aligned to the gnome panel.
    """
    
    def __init__(self, controller, model, widget, applet):
        deskbar.interfaces.View.__init__(self, controller, model)
        CuemiacAlignedWindow.__init__(self, widget, applet)
        self._controller.register_view(self)
        self._do_clear = True
        self.applet = applet
        
        self.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_MENU)
        self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR)
        self.applet.set_flags(gtk.CAN_FOCUS)
        
        self._screen_height = self.get_screen().get_height ()
        self._screen_width = self.get_screen().get_width ()
        self._max_window_height = int (0.8 * self._screen_height)
        self._max_window_width = int (0.6 * self._screen_width)
        
        self.connect("delete-event", self._controller.on_quit)
        self.connect("destroy-event", self._controller.on_quit)
        self.connect("key-press-event", self.__on_window_key_press_event)
       
        self.set_title("Deskbar Applet")
        self.set_default_size( self._model.get_window_width(), -1 )

        self.set_role("deskbar-search-window")

        self._model.connect("query-ready", lambda s,m: gobject.idle_add(self.append_matches, s, m))
        
        # VBox 
        self.vbox_main = gtk.VBox(spacing=12)
        self.vbox_main.set_border_width(6)
        self.add(self.vbox_main)
        self.vbox_main.show()
        
#        self.completion = gtk.EntryCompletion()
#        self.completion.set_model(self._model.get_history())
#        self.completion.set_inline_completion(True)
#        self.completion.set_popup_completion(False)
#        self.completion.set_text_column(1)
        
         # Search entry
        self.default_entry_pixbuf = deskbar.core.Utils.load_icon("deskbar-applet-panel-h.png", width=23, height=14)
        self.entry = CuemiacEntry (self.default_entry_pixbuf)
        self.entry.connect("changed", self._controller.on_query_entry_changed)
        # Connect this before "go-next/previous" to parse history
        self.entry.connect("key-press-event", self._controller.on_query_entry_key_press_event)
        self.entry.connect("activate", self._controller.on_query_entry_activate)
        self.entry.connect("go-next", lambda e: self.__focus_matches_if_visible("top"))
        self.entry.connect("go-previous", lambda e: self.__focus_matches_if_visible("bottom"))
#        self.entry.get_entry().set_completion(self.completion)
        self.entry.show()
        
        self.header = CuemiacHeader ( self.entry )
        self.header.show()
        
        # History TreeView
        self.history_box = gtk.HBox(spacing=6)
        self.history_box.show()
        
        hlabel = gtk.Label()
        # translators: _H is a mnemonic, i.e. pressing Alt+h will focus the widget
        hlabel.set_markup_with_mnemonic("<b>%s:</b>" % _("_History"))
        hlabel.show()
        self.history_box.pack_start(hlabel, False)
        
        self.hview = CuemiacHistoryView(self._model.get_history())
        self.hview.connect("match-selected", self._controller.on_history_match_selected)
        self.hview.show()
        self.history_box.pack_start(self.hview)
        hlabel.set_mnemonic_widget(self.hview)
        
        empty_button = gtk.Button()
        empty_button.set_image( gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU) )
        empty_button.connect("clicked", self._controller.on_clear_history)
        empty_button.show()
        self.history_box.pack_start(empty_button, False)
        
        # Results TreeView
        self.treeview_model = CuemiacModel ()
        self.treeview_model.connect("category-added", self._controller.on_category_added)
        
        self.cview = CuemiacTreeView (self.treeview_model)
        #self.cview.connect ("key-press-event", self._on_cview_key_press)
        self.cview.connect ("match-selected", self._controller.on_match_selected)
        self.cview.connect ("do-default-action", self._controller.on_do_default_action)
        self.cview.connect ("pressed-up-at-top", lambda s: self.entry.grab_focus())
        self.cview.connect ("pressed-down-at-bottom", lambda s: self.entry.grab_focus())
        self.cview.connect_after ("cursor-changed", self._controller.on_treeview_cursor_changed)
        self.cview.connect ("row-expanded", self._controller.on_category_expanded, self.treeview_model)
        self.cview.connect ("row-collapsed", self._controller.on_category_collapsed, self.treeview_model)
        self.cview.show()
        
        LingeringSelectionWindow (self.cview)
        
        self.scrolled_results = gtk.ScrolledWindow ()
        self.scrolled_results.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_results.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled_results.add(self.cview)
        self.scrolled_results.show()
        
        # Actions TreeView
        self.actions_box = gtk.VBox(spacing=3)
        
        self.actions_model = CuemiacActionsModel()
        self.aview = CuemiacActionsTreeView(self.actions_model)
        self.aview.connect ("action-selected", self._controller.on_action_selected)
        self.aview.connect ("go-back", self.__on_go_back)
        self.aview.show()
        
        LingeringSelectionWindow (self.aview)
        
        self.scrolled_actions = gtk.ScrolledWindow()
        self.scrolled_actions.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_actions.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled_actions.add(self.aview)
        self.scrolled_actions.show()
        self.actions_box.pack_start(self.scrolled_actions)
        
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_START)
        buttonbox.show()
        self.actions_box.pack_start(buttonbox, False)
        
        back_button = gtk.Button(_("Back to Matches"))
        back_button.set_image( gtk.image_new_from_stock(gtk.STOCK_GO_BACK, gtk.ICON_SIZE_MENU) )
        back_button.set_relief(gtk.RELIEF_NONE)
        back_button.connect("clicked", self.__on_go_back)
        back_button.show()
        buttonbox.pack_start(back_button, False, False, 0)
       
        # Results
        self.results_box = gtk.HBox()
        self.results_box.pack_start(self.scrolled_results)
        self.results_box.pack_start(self.actions_box)
        
        self.__set_layout_by_orientation(self.applet.get_orient())
        self.resize( *self.size_request() )
   
    def clear_all(self):
        deskbar.interfaces.View.clear_all(self)
        self.applet.set_state(gtk.STATE_NORMAL)
        self.results_box.hide()
        self.__adjust_popup_size()
    
    def clear_results(self):
        self.treeview_model.clear()
        
    def clear_actions(self):
        self.actions_model.clear()
        
    def clear_query(self):
        self.entry.set_text("")
        self.entry.set_icon( self.default_entry_pixbuf )
    
    def get_toplevel(self):
        return self
    
    def get_entry(self):
        return self.entry
    
    def set_clear(self):
        """
        Set a flag to clear the list of matches and actions
        as soon as the first result arrives
        """
        self._do_clear = True
    
    def receive_focus(self, time):
        self.applet.set_state(gtk.STATE_SELECTED)
        self.update_position()
        self.show()
        self.present_with_time(time)
        self.entry.grab_focus()
        
    def mark_history_empty(self, val):
        if val:
            self.hview.set_sensitive (False)
        else:
            self.hview.set_sensitive (True)
        
    def __show_matches(self):
        self.scrolled_results.show()
        self.actions_box.hide()
        
    def __show_actions(self):
        self.scrolled_results.hide()
        self.actions_box.show()
    
    def show_results(self):
        self.results_box.show()
        self.__show_matches()
    
    def display_actions(self, actions, qstring):
        self.actions_model.clear()
        self.__show_actions()
        self.actions_model.add_actions(actions, qstring)
        self.aview.grab_focus()

    def append_matches (self, sender, matches):
        """
        We suppose that the results belong to the text
        that is currently in the entry
        """
        if self._do_clear:
            self._do_clear = False
            self.clear_results()
            self.clear_actions()
            # Display default icon in entry
            self.update_entry_icon()
        self.treeview_model.append (matches, self.entry.get_text())
        self.__adjust_popup_size ()
        
    def set_sensitive (self, active):
        """
        Called when the UI should be in/active because modules are loading
        """
        self.vbox_main.set_sensitive(active)
        if active:
            self.entry.grab_focus()
   
    def update_entry_icon (self, icon=None):
        if icon == None:
            icon = self.default_entry_pixbuf
            if not (self.cview.get_toplevel().flags() & gtk.MAPPED):
                # The view is hidden, just show default icon
                self.entry.set_icon (icon)
                return
                
            path, column = self.cview.get_cursor ()
        
            if path != None and self.entry.get_text() != "":
                match = self.treeview_model[self.treeview_model.get_iter(path)][self.treeview_model.MATCHES]
                if not isinstance(match, CuemiacCategory):
                    icon = match.get_icon()
                
        self.entry.set_icon (icon)
        
    def __on_go_back(self, widget):
        self.__show_matches()
        self.cview.grab_focus()
        return False
    
    def __on_window_key_press_event(self, window, event):
        if event.keyval == gtk.keysyms.Escape:
            self.emit("destroy-event", event)
                
        return False
    
    def __focus_matches_if_visible(self, mode):
        if (self.results_box.get_property("visible")):
            if mode == "top":
                self.cview.select_first_item()
            elif mode == "bottom":
                self.cview.select_last_item()
            self.cview.grab_focus()
            return True
        else:
            return False
        
    def __adjust_popup_size (self):
        """adjust window size to the size of the children"""
        # FIXME: Should we handle width intelligently also?
        w, h = self.cview.size_request ()
        h = h + self.header.allocation.height + 2 # To ensure we don't always show scrollbars
        h = min (h, self._max_window_height)
        w = min (w, self._max_window_width)
        if w > 0 and h > 0:
            self.resize (w, h)
    
    def __set_layout_by_orientation (self, orient):
        """
        Adjust the various widgets managed to layout with repect to the given
        orientation.
        
        @param orient: The orientation to switch to. 
                    Must be one of C{gnomeapplet.ORIENT_UP}, C{gnomeapplet.ORIENT_DOWN},
                    C{gnomeapplet.ORIENT_LEFT}, C{gnomeapplet.ORIENT_RIGHT}.
        """
        if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
            self.treeview_model.set_sort_order (gtk.SORT_ASCENDING)
            self.actions_model.set_sort_order (gtk.SORT_ASCENDING)
            self._model.get_history().set_sort_order (gtk.SORT_DESCENDING)
            self.vbox_main.pack_start(self.header, False)
            self.vbox_main.pack_start(self.history_box, False)
            self.vbox_main.pack_start(self.results_box)
        else:
            # We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
            self.treeview_model.set_sort_order (gtk.SORT_DESCENDING)
            self.actions_model.set_sort_order (gtk.SORT_DESCENDING)
            self._model.get_history().set_sort_order (gtk.SORT_ASCENDING)
            self.vbox_main.pack_start(self.results_box)
            self.vbox_main.pack_start(self.history_box, False)
            self.vbox_main.pack_start(self.header, False)
