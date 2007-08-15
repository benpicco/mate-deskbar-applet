import gtk
import gtk.gdk
import gobject
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

class CuemiacWindowView(deskbar.interfaces.View, gtk.Window):
    
    def __init__(self, controller, model):
        deskbar.interfaces.View.__init__(self, controller, model)
        gtk.Window.__init__(self)
        self._controller.register_view(self)
        self.__small_window_height = None
        
        self.connect("delete-event", self._controller.on_quit)
        self.connect("destroy-event", self._controller.on_quit)
        self.connect("key-press-event", self.__on_window_key_press_event)
        
        self.set_title("Deskbar Applet")
        self.set_default_size( self._model.get_window_width(), -1 )
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_property("skip-taskbar-hint", True)

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
        
        header = CuemiacHeader ( self.entry )
        header.show()   
       
        # Search entry
        self.vbox_main.pack_start(header, False)
        
        # History TreeView
        hhbox = gtk.HBox(spacing=6)
        hhbox.show()
        self.vbox_main.pack_start(hhbox, False)
        
        hlabel = gtk.Label()
        # translators: _H is a mnemonic, i.e. pressing Alt+h will focus the widget
        hlabel.set_markup_with_mnemonic("<b>%s:</b>" % _("_History"))
        hlabel.show()
        hhbox.pack_start(hlabel, False)
        
        self.hview = CuemiacHistoryView(self._model.get_history())
        self.hview.connect("match-selected", self._controller.on_history_match_selected)
        self.hview.show()
        hhbox.pack_start(self.hview)
        hlabel.set_mnemonic_widget(self.hview)
        
        empty_button = gtk.Button()
        empty_button.set_image( gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU) )
        empty_button.connect("clicked", self._controller.on_clear_history)
        empty_button.show()
        hhbox.pack_start(empty_button, False)
        
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
        
        self.scrolled_results = gtk.ScrolledWindow ()
        self.scrolled_results.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_results.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled_results.add(self.cview)
        self.scrolled_results.show()
        
        # Actions TreeView
        self.actions_model = CuemiacActionsModel()
        self.aview = CuemiacActionsTreeView(self.actions_model)
        self.aview.connect ("action-selected", self._controller.on_action_selected)
        self.aview.connect ("go-back", self.__on_go_back)
        self.aview.show()
        
        self.scrolled_actions = gtk.ScrolledWindow()
        self.scrolled_actions.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_actions.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled_actions.add(self.aview)
       
        # Results
        self.results_box = gtk.HBox()
        self.results_box.pack_start(self.scrolled_results)
        self.results_box.pack_start(self.scrolled_actions)
        self.vbox_main.pack_start(self.results_box)
    
    def clear_all(self):
        deskbar.interfaces.View.clear_all(self)
        width, height = self.get_size()
        self._model.set_window_width( width )
        self._model.set_window_height( height )
        
        if self.__small_window_height != None:
            self.resize( width, self.__small_window_height )
        self.results_box.hide()
    
    def clear_results(self):
        self.treeview_model.clear()
        
    def clear_actions(self):
        self.actions_model.clear()
        
    def clear_query(self):
        self.entry.set_text("")
        self.update_entry_icon()
    
    def get_toplevel(self):
        return self
    
    def get_entry(self):
        return self.entry
    
    def receive_focus(self, time):
        self.entry.grab_focus()
        self.realize()
        self.window.set_user_time(time)
        self.present()
        self.move( self._model.get_window_x(), self._model.get_window_y() )

    def show_results(self):
        width, height = self.get_size()
        if self.__small_window_height == None:
            self.__small_window_height = height
        self.results_box.show()
        self.scrolled_results.show()
        self.scrolled_actions.hide()
        self.resize( width, self._model.get_window_height() )
    
    def display_actions(self, actions, qstring):
        self.actions_model.clear()
        self.scrolled_results.hide()
        self.scrolled_actions.show()
        self.actions_model.add_actions(actions, qstring)
        self.aview.grab_focus()

    def append_matches (self, sender, matches):
        """
        We suppose that the results belong to the text
        that is currently in the entry
        """
        self.treeview_model.append (matches, self.entry.get_text())
        self.update_entry_icon()
        
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
        
            if path != None:
                match = self.treeview_model[self.treeview_model.get_iter(path)][self.treeview_model.MATCHES]
                if not isinstance(match, CuemiacCategory):
                    icon=match.get_icon()
                
        self.entry.set_icon (icon)
        
    def __on_go_back(self, treeview):
        self.scrolled_actions.hide()
        self.scrolled_results.show()
        self.cview.grab_focus()
        return False
    
    def __on_window_key_press_event(self, window, event):
        if event.keyval == gtk.keysyms.Escape:
            self.clear_all()
            self.clear_query()
            self.emit("destroy-event", event)
                
        return False
    
    def __focus_matches_if_visible(self, mode):
        if (self.results_box.get_property("visible")):
            if mode == "top":
                self.cview.select_first_item()
            elif mode == "bottom":
                self.cview.select_last_item()
            self.cview.grab_focus()
        else:
            self.entry.grab_focus()
        