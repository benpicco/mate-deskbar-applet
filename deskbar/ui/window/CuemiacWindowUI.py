from gettext import gettext as _
import gtk
import gobject

from deskbar.ui.DeskbarUI import DeskbarUI
from deskbar.ui.cuemiac.CuemiacUIManager import CuemiacUIManager
from deskbar.ui.cuemiac.CuemiacLayoutProvider import CuemiacLayoutProvider
from deskbar.ui.cuemiac.LingeringSelectionWindow import LingeringSelectionWindow
from deskbar.ui.cuemiac.CuemiacHeader import CuemiacHeader

class CuemiacWindowUI (DeskbarUI, CuemiacLayoutProvider):
    
    __gsignals__ = {
        "show-preferences": ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [] ),
        "show-about": ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [] ),
        "clear-history": ( gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [] ),
    }    
    
    ui = '''<ui>
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
    
    def __init__(self, applet, prefs):
        DeskbarUI.__init__ (self, applet, prefs)
        CuemiacLayoutProvider.__init__ (self)
        
        self.cuemiac = CuemiacUIManager ()
        header = CuemiacHeader (self.cuemiac.get_entry())
        self.vbox = gtk.VBox() 			# Main UI widget
        self.ui_manager = gtk.UIManager() 	# Menubar
        
        actiongroup = gtk.ActionGroup('deskbar-window')
        actiongroup.add_actions([('FileMenuAction', None, _('_File')),
                                  ('QuitAction', gtk.STOCK_QUIT, _('_Quit'), '<Ctrl>Q', None, self.__on_quit_activate),
                                  ('EditMenuAction', None, _('_Edit')),
                                  ('ClearHistoryAction', gtk.STOCK_DELETE, _('_Clear History'), None, None, self.__on_clear_history_activate),
                                  ('PreferencesAction', gtk.STOCK_PREFERENCES, _('_Preferences'), None, None, self.__on_preferences_activate),
                                  ('ViewMenuAction', None, _('_View')),                                  
                                  ('HelpMenuAction', None, _('_Help')),
                                  ('AboutAction', gtk.STOCK_ABOUT, _('_About'), None, None, self.__on_about_activate),
                                  ])
        actiongroup.add_toggle_actions([('HistoryAction', None, _('_History'), '<Ctrl>H', None, self.__on_history_activate),])
        self.ui_manager.insert_action_group(actiongroup, 0)
        self.__accels_connected = False # We use this boolean to check when we should connect the accels - we do this on first receive_focus()
        
        self.ui_manager.add_ui_from_string(self.ui)
        self.menubar = self.ui_manager.get_widget('/menubar')
        self.vbox.pack_start(self.menubar, False)        
        
        self.vbox_main = gtk.VBox(spacing=12)
        self.vbox_main.set_border_width(6)
        self.vbox.pack_start(self.vbox_main)        
        
        # Search entry
        self.vbox_main.pack_start(header, False)        
        self.entry = self.cuemiac.get_entry()
        
        # Results TreeView
        self.scrolled_results = gtk.ScrolledWindow ()
        self.scrolled_results.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_results.set_shadow_type(gtk.SHADOW_IN)
        
        self.cview = self.cuemiac.get_view()
        self.scrolled_results.add(self.cview)
        self.vbox_main.pack_start(self.scrolled_results)
        
        # History TreeView
        self.history_frame = self.__create_frame_with_alignment( _('<b>History</b>') )
        self.vbox_main.pack_start(self.history_frame)
        
        self.scrolled_history = gtk.ScrolledWindow()
        self.scrolled_history.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_history.set_shadow_type(gtk.SHADOW_IN)
        self.history_frame.get_child().add(self.scrolled_history)
        
        self.hview = self.cuemiac.get_history_view()
        self.scrolled_history.add(self.hview)
        
        # Statusbar
        self.statusbar = gtk.Statusbar()
        self.vbox.pack_start(self.statusbar, False)
        
        self.cuemiac.set_layout(self)
        self.cuemiac.forward_deskbar_ui_signals (self)
        self.cuemiac.get_view().connect ("map-event", lambda widget, event: self.__connect_accels()) # Called when the widget is displayed on screen
        LingeringSelectionWindow (self.cuemiac.get_view())
        self.show_all()
    
    def __has_toplevel_window (self):
    	"""
    	Return True if the view is in a gtk.Window.
    	"""
    	# We have to check this frequently because get_view().get_toplevel()
    	# will return the view widget if there's no toplevel window.
    	return (self.get_view().get_toplevel().flags() & gtk.TOPLEVEL)
    
    def __connect_accels (self):
    	"""
    	Connect accelerators to the toplevel window if it is present.
    	"""
    	if self.__accels_connected:
    		# We have already done this
    		return
        accelgroup = self.ui_manager.get_accel_group()
    	if not self.__has_toplevel_window ():
    		print "WARNING, CuemiacWindowUI : Tried to set accels without toplevel window."
    		return

        self.get_view().get_toplevel().add_accel_group(accelgroup)
        self.__accels_connected = True
    
    def __create_frame_with_alignment(self, label_markup):
        label = gtk.Label()
        label.set_markup( label_markup )
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_NONE)
        frame.set_label_widget(label)
        alignment = gtk.Alignment(xscale=1.0, yscale=1.0)
        alignment.set_padding(0, 0, 12, 0)
        frame.add(alignment)
        
        label.show()
        alignment.show()
        
        return frame
    
    def show_all(self):        
        #self.header.show_all()
        #self.results_frame.show_all()
        self.vbox_main.show_all()
        self.history_frame.hide()
        self.menubar.show()
        self.statusbar.show()
        self.vbox.show()
        
    def __on_quit_activate(self, widget):
        self.close_view()
        gtk.main_quit ()
        
    def __on_clear_history_activate(self, widget):
        self.emit('clear-history')
        
    def __on_preferences_activate(self, widget):
        self.emit('show-preferences')
    
    def __on_history_activate(self, widget):
        if widget.get_active():
            self.history_frame.show_all()
        else:
            self.history_frame.hide()
        return
    
    def __on_about_activate(self, widget):
        self.emit('show-about')
        return

    def on_match_selected (self, cuim, match):
    	# Hook called by the cuemiac ui manager
    	self.get_view().get_toplevel().hide ()
    
    def append_matches (self, matches):
        self.cuemiac.append_matches (matches)
        
    def middle_click(self):
        self.cuemiac.get_entry().grab_focus()
    
    def set_sensitive (self, active):
        """
        Called when the UI should be in/active because modules are loading
        """
        self.vbox_main.set_sensitive(active)
        self.history_frame.hide()
        if active:
            self.entry.grab_focus()
        
    def receive_focus(self, time):
    	if not self.__has_toplevel_window ():
    		print "WARNING, CuemiacWindowUI: Focus request without toplevel window."
    		return 
    	if (self.get_view().get_toplevel().flags() & gtk.MAPPED):
    		self.get_view().get_toplevel().hide ()
    	else:
	        self.get_view().get_toplevel().present_with_time(time)
        
    def get_view (self):
        """
        Return the widget to be displayed for this UI.
        """
        return self.vbox
    
    def close_view(self, *args):
        """
        Closes every popup or window owned by the UI, because the ui is going to change
        """
        if self.__has_toplevel_window():
        	self.get_view().get_toplevel().hide()
        self.emit('stop-query')
