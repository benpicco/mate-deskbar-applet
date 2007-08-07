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
from deskbar.ui.cuemiac.Sidebar import Sidebar
from deskbar.ui.cuemiac.CuemiacActionsTreeView import CuemiacActionsTreeView, CuemiacActionsModel

class CuemiacWindowView(deskbar.interfaces.View, gtk.Window):
    
    UI = '''<ui>
        <menubar>
            <menu name="FileMenu" action="FileMenuAction">
            <separator />
            <menuitem name="Quit" action="QuitAction" />
            </menu>
            <menu name="EditMenu" action="EditMenuAction">
                <menuitem name="ClearHistory" action="ClearHistoryAction" />
                <separator />
                <menuitem name="Preferences" action="PreferencesAction" />
            </menu>
            <menu name="ViewMenu" action="ViewMenuAction">
                <menuitem name="History" action="HistoryAction" />                
            </menu>
            <menu name="HelpMenu" action="HelpMenuAction">
                <menuitem name="About" action="AboutAction" />
            </menu>
        </menubar>
    </ui>'''
    
    def __init__(self, controller, model):
        deskbar.interfaces.View.__init__(self, controller, model)
        gtk.Window.__init__(self)
        self._controller.register_view(self)
        
        self.connect("delete-event", self._controller.on_quit)
        self.connect("destroy-event", self._controller.on_quit)
        self.set_title("Deskbar Applet")
        self.set_default_size( self._model.get_window_width(), self._model.get_window_height() )
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("configure-event", self._controller.on_window_resized)
        
        #self._model.connect("query-ready", self.append_matches)
        self._model.connect("query-ready", lambda s,m: gobject.idle_add(self.append_matches, s, m))
        
#        self.completion = gtk.EntryCompletion()
#        self.completion.set_model(self._model.get_history())
#        self.completion.set_inline_completion(True)
#        self.completion.set_popup_completion(False)
#        self.completion.set_text_column(1)
        
        self.default_entry_pixbuf = deskbar.core.Utils.load_icon("deskbar-applet-panel-h.png", width=23, height=14)
        self.entry = CuemiacEntry (self.default_entry_pixbuf)
        self.entry.connect("changed", self._controller.on_query_entry_changed)
        self.entry.connect("key-press-event", self._controller.on_query_entry_key_press_event)
        self.entry.connect("activate", self._controller.on_query_entry_activate)
#        self.entry.get_entry().set_completion(self.completion)
        self.entry.show()
        
        header = CuemiacHeader ( self.entry )
        header.show()

        self.vbox = gtk.VBox()
        self.add(self.vbox)
        self.ui_manager = gtk.UIManager() # Menubar
        
        actiongroup = gtk.ActionGroup('deskbar-window')
        actiongroup.add_actions([('FileMenuAction', None, _('_File')),
                                  ('QuitAction', gtk.STOCK_QUIT, _('_Quit'), '<Ctrl>Q', None, self._controller.on_quit),
                                  ('EditMenuAction', None, _('_Edit')),
                                  ('ClearHistoryAction', gtk.STOCK_DELETE, _('_Clear History'), None, None, self._controller.on_clear_history),
                                  ('PreferencesAction', gtk.STOCK_PREFERENCES, _('_Preferences'), None, None, self._controller.on_show_preferences),
                                  ('ViewMenuAction', None, _('_View')),                                  
                                  ('HelpMenuAction', None, _('_Help')),
                                  ('AboutAction', gtk.STOCK_ABOUT, _('_About'), None, None, self._controller.on_show_about),
                                  ])
        actiongroup.add_toggle_actions([('HistoryAction', None, _('_History'), '<Ctrl>H', None, self._controller.on_toggle_history),])
        self.ui_manager.insert_action_group(actiongroup, 0)
        self.__connect_accels()
        
        self.ui_manager.add_ui_from_string(self.UI)
        self.menubar = self.ui_manager.get_widget('/menubar')
        self.menubar.show()
        self.vbox.pack_start(self.menubar, False)        
        
        self.vbox_main = gtk.VBox(spacing=12)
        self.vbox_main.set_border_width(6)
        self.vbox.pack_start(self.vbox_main)
        self.vbox_main.show()
        
        # Search entry
        self.vbox_main.pack_start(header, False)
        
        # History TreeView
        self.scrolled_history = gtk.ScrolledWindow()
        self.scrolled_history.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_history.set_shadow_type(gtk.SHADOW_IN)
        
        self.hview = CuemiacHistoryView(self._model.get_history())
        self.hview.connect("match-selected", self._controller.on_history_match_selected)
        self.hview.show()
        self.scrolled_history.add(self.hview)
        self.scrolled_history.show()
        
        self.sidebar = Sidebar( "<b>%s</b>" % _("History"))
        self.sidebar.connect("closed", lambda w: self.ui_manager.get_action('/menubar/ViewMenu/History').activate())
        self.sidebar.pack_start(self.scrolled_history)
        
        # Results TreeView
        self.treeview_model = CuemiacModel ()
        self.treeview_model.connect("category-added", self._controller.on_category_added)
        
        self.cview = CuemiacTreeView (self.treeview_model)
        #self.cview.connect ("key-press-event", self._on_cview_key_press)
        self.cview.connect ("match-selected", self._controller.on_match_selected)
        self.cview.connect_after ("cursor-changed", self._controller.on_treeview_cursor_changed)
        self.cview.connect ("row-expanded", self._controller.on_category_expanded, self.treeview_model)
        self.cview.connect ("row-collapsed", self._controller.on_category_collapsed, self.treeview_model)
        self.cview.show()
        
        scrolled_results = gtk.ScrolledWindow ()
        scrolled_results.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_results.set_shadow_type(gtk.SHADOW_IN)        
        scrolled_results.add(self.cview)
        scrolled_results.show()
        
        # Actions TreeView
        self.actions_model = CuemiacActionsModel()
        self.aview = CuemiacActionsTreeView(self.actions_model)
        self.aview.connect ("action-selected", self._controller.on_action_selected)
        self.aview.show()
        
        scrolled_actions = gtk.ScrolledWindow()
        scrolled_actions.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_actions.set_shadow_type(gtk.SHADOW_IN)
        scrolled_actions.add(self.aview)
        scrolled_actions.show()
       
        # HPaned
        self.hpaned_right = gtk.HPaned()
        self.hpaned_right.set_position( self._model.get_resultsview_width() )
        self.hpaned_right.connect("notify::position", self._controller.on_resultsview_width_changed)
        self.hpaned_right.pack1(scrolled_results)
        self.hpaned_right.pack2(scrolled_actions)
        self.hpaned_right.show()
        
        self.hpaned_left = gtk.HPaned()
        self.hpaned_left.set_position( self._model.get_sidebar_width() )
        self.hpaned_left.connect("notify::position", self._controller.on_sidebar_width_changed)
        self.vbox_main.pack_start(self.hpaned_left)
        
        self.hpaned_left.pack1(self.sidebar)
        self.hpaned_left.pack2(self.hpaned_right)
        self.hpaned_left.show()
       
        # Statusbar
        self.statusbar = gtk.Statusbar()
        self.statusbar.show()
        self.vbox.pack_end(self.statusbar, False, False, 0)
        self.vbox.show()
        
        if self._model.get_show_history():
            self.ui_manager.get_action('/menubar/ViewMenu/History').activate()
    
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
    
    def show_history(self, value):
        if value:
            self.sidebar.show()
        else:
            self.sidebar.hide()
            
    def is_history_visible(self):
        return self.sidebar.get_property("visible")
    
    def receive_focus(self, time):
        self.entry.grab_focus()
        self.realize()
        self.window.set_user_time(time)
        self.present()

    def display_actions(self, actions, qstring):
        self.actions_model.clear()
        self.actions_model.add_actions(actions, qstring)

    def __connect_accels (self):
        """
        Connect accelerators to the toplevel window if it is present.
        """
        accelgroup = self.ui_manager.get_accel_group()

        self.add_accel_group(accelgroup)
        self.__accels_connected = True
    
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