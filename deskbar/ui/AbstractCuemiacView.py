import gtk
import gtk.gdk
import glib
from gettext import gettext as _
import deskbar.core.Utils
import deskbar.interfaces.View
from deskbar.ui.cuemiac.CuemiacEntry import CuemiacEntry
from deskbar.ui.cuemiac.CuemiacHeader import CuemiacHeader
from deskbar.ui.cuemiac.CuemiacModel import CuemiacModel
from deskbar.ui.cuemiac.CuemiacTreeView import CuemiacTreeView
from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory
from deskbar.ui.cuemiac.CuemiacActionsTreeView import CuemiacActionsTreeView, CuemiacActionsModel
from deskbar.ui.cuemiac.LingeringSelectionWindow import LingeringSelectionWindow

class AbstractCuemiacView (deskbar.interfaces.View):
    """
    An abstract base class for all cuemiac derived UIs
    
    It creates and packs all necessary widget and connects
    the signals correctly. L{self.vbox_main} contains the actual
    UI.
    
    You still have to implement methods from L{deskbar.interfaces.View}:
        * get_toplevel
        * receive_focus
    """
    
    VBOX_MAIN_SPACING = 12
    VBOX_MAIN_BORDER_WIDTH = 6
    
    def __init__(self, controller, model):
        deskbar.interfaces.View.__init__(self, controller, model)
        self._do_clear = True
        
        self._model.connect("query-ready", lambda s,m: glib.idle_add(self.append_matches, s, m))
        
        # VBox 
        self._create_vbox_main()
        self.vbox_main.show()
        
        self._create_header()
        self.header.show()
        
        # Results TreeView
        self._create_results_treeview()
        self.cview.show()
        self.scrolled_results.show()
        
        # Actions TreeView
        self._create_actions_view()
        self.aview.show()
        self.scrolled_actions.show()
        
    def _create_vbox_main(self):
        """
        Sets self.vbox_main
        """
        self.vbox_main = gtk.VBox(spacing=self.VBOX_MAIN_SPACING)
        self.vbox_main.set_border_width(self.VBOX_MAIN_BORDER_WIDTH)
        
    def _create_cuemiac_entry(self):
        """
        Sets self.entry
        """
        # Search entry
        self.default_entry_pixbuf = deskbar.core.Utils.load_icon("deskbar-applet-panel-h.png", width=23, height=14)
        self.entry = CuemiacEntry (self.default_entry_pixbuf)
        self.entry.connect("changed", self._controller.on_query_entry_changed)
        # Connect this before "go-next/previous" to parse history
        self.entry.connect("key-press-event", self._controller.on_query_entry_key_press_event)
        self.entry.connect("activate", self._controller.on_query_entry_activate)
        self.entry.connect("go-next", lambda e: self._focus_matches_if_visible("top"))
        self.entry.connect("go-previous", lambda e: self._focus_matches_if_visible("bottom"))
        
    def _create_header(self):
        """
        Sets self.entry and self.header
        """
#        self.completion = gtk.EntryCompletion()
#        self.completion.set_model(self._model.get_history())
#        self.completion.set_inline_completion(True)
#        self.completion.set_popup_completion(False)
#        self.completion.set_text_column(1)
        
        self._create_cuemiac_entry()
#        self.entry.get_entry().set_completion(self.completion)
        self.entry.show()
        
        self.header = CuemiacHeader ( self.entry )
    
    def _create_results_treeview(self):
        """
        Sets:
            * self.treeview_model
            * self.cview
            * self.scrolled_results
        """
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
        
        LingeringSelectionWindow (self.cview)
        
        self.scrolled_results = gtk.ScrolledWindow ()
        self.scrolled_results.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_results.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled_results.add(self.cview)
        
    def _create_actions_view(self):
        """
        Sets:
            * self.actions_box
            * self.actions_model
            * self.aview
            * self.scrolled_actions
        """
        self.actions_box = gtk.VBox(spacing=3)
        
        self.actions_model = CuemiacActionsModel()
        self.aview = CuemiacActionsTreeView(self.actions_model)
        self.aview.connect ("action-selected", self._controller.on_action_selected)
        self.aview.connect ("go-back", self._on_go_back)
        
        LingeringSelectionWindow (self.aview)
        
        self.scrolled_actions = gtk.ScrolledWindow()
        self.scrolled_actions.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_actions.set_shadow_type(gtk.SHADOW_IN)
        self.scrolled_actions.add(self.aview)
        self.actions_box.pack_start(self.scrolled_actions)
        
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_START)
        buttonbox.show()
        self.actions_box.pack_start(buttonbox, False)
        
        back_button = gtk.Button(_("Back to Matches"))
        back_button.set_image( gtk.image_new_from_stock(gtk.STOCK_GO_BACK, gtk.ICON_SIZE_MENU) )
        back_button.set_relief(gtk.RELIEF_NONE)
        back_button.connect("clicked", self._on_go_back)
        back_button.show()
        buttonbox.pack_start(back_button, False, False, 0)
    
    def _focus_matches_if_visible(self, mode):
        if (self.results_box.get_property("visible")):
            if mode == "top":
                self.cview.select_first_item()
            elif mode == "bottom":
                self.cview.select_last_item()
            self.cview.grab_focus()
            return True
        else:
            return False
         
    def _on_go_back(self, widget):
        self._show_matches()
        self.cview.grab_focus()
        return False
        
    def _show_matches(self):
        self.scrolled_results.show()
        self.actions_box.hide()
        
    def _show_actions(self):
        self.scrolled_results.hide()
        self.actions_box.show()
    
    def clear_results(self):
        self.treeview_model.clear()
        
    def clear_actions(self):
        self.actions_model.clear()
        
    def clear_query(self):
        self.entry.set_text("")
        self.entry.set_icon( self.default_entry_pixbuf )
    
    def get_entry(self):
        return self.entry
    
    def set_clear(self):
        """
        Set a flag to clear the list of matches and actions
        as soon as the first result arrives
        """
        self._do_clear = True
        
    def mark_history_empty(self, val):
        pass
    
    def show_results(self):
        self.results_box.show()
        self._show_matches()
    
    def display_actions(self, actions, qstring):
        self.actions_model.clear()
        self._show_actions()
        self.actions_model.add_actions(actions, qstring)
        first_iter = self.actions_model.get_iter_first()
        self.aview.get_selection().select_iter(first_iter)
    
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
    
