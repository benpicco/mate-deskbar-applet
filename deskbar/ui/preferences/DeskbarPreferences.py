import gtk
import gtk.gdk
import gtk.glade
import traceback
from gettext import gettext as _
from os.path import join
import deskbar
from deskbar.core.updater.NewStuffUpdater import NewStuffUpdater
from deskbar.core.ModuleList import WebModuleList
from deskbar.ui.preferences.AccelEntry import AccelEntry
from deskbar.ui.preferences.ErrorDialog import ErrorDialog
from deskbar.ui.preferences.ModuleListView import ModuleListView, DisabledModuleListView, WebModuleListView
import dbus
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
    import dbus.glib

class InfoBox(gtk.HBox):
    
    def __init__(self, text, stock_icon=gtk.STOCK_DIALOG_INFO):
        gtk.HBox.__init__(self, spacing=6)
        self.info_image = gtk.image_new_from_stock(stock_icon, gtk.ICON_SIZE_BUTTON)
        self.info_image.set_padding(3, 0)
        self.pack_start(self.info_image, expand=False, fill=False)
        self.label = gtk.Label()
        self.label.set_line_wrap(True)
        self.label.set_alignment(0.0, 0.5)
        self.label.set_justify(gtk.JUSTIFY_LEFT)
        self.label.set_markup(text)
        self.pack_start(self.label, expand=True, fill=True)

class DeskbarPreferences:
    
    def __init__(self, model):
        self._model = model
        
        self.module_list = self._model.get_module_list()
    
        self.glade = gtk.glade.XML(join(deskbar.SHARED_DATA_DIR, "prefs-dialog.glade"))
        
        self.dialog = self.glade.get_widget("preferences")
        
        # Since newstuff is optional we have to check if self.newstuff is None each time we use it
        self.newstuff = None
        
        self.keybinding = self._model.get_keybinding()
        
        self.__setup_active_modules_tab()
        
        self.__setup_general_tab()
        
        # Setup Drag & Drop
        self.__setup_drag_and_drop()
        
        self.__setup_disabled_modules_tab()
        
        # Setup new-stuff-manager
        self.__enable_newstuffmanager( self.__is_nsm_available() )
          
        self.__select_first_tab()
        
        self.sync_ui()

    def __setup_active_modules_tab(self):
        container = self.glade.get_widget("handlers")
        self.moduleview = ModuleListView(self.module_list)
        self.moduleview.connect ("row-toggled", self.on_module_toggled)
        self.moduleview.get_selection().connect("changed", self.on_module_selected)
        self.moduleview.get_selection().connect("changed", self.set_buttons)
        self.module_list.connect('row-changed', lambda list, path, iter: self.on_module_selected(self.moduleview.get_selection()))
        container.add(self.moduleview)
        
        # Buttons beneath list
        self.more_button = self.glade.get_widget("more")
        self.more_button.set_sensitive(False)
        self.more_button.connect("clicked", self.on_more_button_clicked)
        self.more_button_callback = None

        # Info are at the bottom
        self.info_area = self.glade.get_widget("info_area")
        self.old_info_message = None
        info_text = _("<i><small>Drag and drop an extension to change its order.</small></i>")
        self.default_info = InfoBox(info_text, gtk.STOCK_DIALOG_INFO)
        self.info_area.add(self.default_info)
        
        # Buttons on the right
        self.button_top = self.glade.get_widget("button_top")
        self.button_top.connect("clicked", self.on_button_top_clicked)
        self.button_up = self.glade.get_widget("button_up")
        self.button_up.connect("clicked", self.on_button_up_clicked)
        self.button_down = self.glade.get_widget("button_down")
        self.button_down.connect("clicked", self.on_button_down_clicked)
        self.button_bottom = self.glade.get_widget("button_bottom")
        self.button_bottom.connect("clicked", self.on_button_bottom_clicked)

    def __setup_general_tab(self):
        self.keyboard_shortcut_entry = AccelEntry()
        self.keyboard_shortcut_entry.connect('accel-edited', self.on_keyboard_shortcut_entry_changed)
        self.glade.get_widget("keybinding_entry_container").pack_start(self.keyboard_shortcut_entry.get_widget(), False)
        #self.keybinding_notify_id = deskbar.GCONF_CLIENT.notify_add(applet.prefs.GCONF_KEYBINDING, lambda x, y, z, a: self.on_config_keybinding(z.value))
        
        self.use_selection = self._model.get_use_selection()
        self.use_selection_box = self.glade.get_widget("use_selection")
        self.use_selection_box.connect('toggled', self.on_use_selection_toggled)
        #self.use_selection_id = deskbar.GCONF_CLIENT.notify_add(applet.prefs.GCONF_USE_SELECTION, lambda x, y, z, a: self.on_config_use_selection(z.value))

    def __setup_drag_and_drop(self):
        big_box = self.glade.get_widget("big_box")
        self.TARGET_URI_LIST, self.TARGET_NS_URL = range(2)
        DROP_TYPES = [('text/uri-list', 0, self.TARGET_URI_LIST),
                      ('_NETSCAPE_URL', 0, self.TARGET_NS_URL),
                     ]
        big_box.drag_dest_set(gtk.DEST_DEFAULT_ALL, DROP_TYPES,
                              gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_MOVE)
        big_box.connect("drag_data_received",
                              self.on_drag_data_received_data)
        big_box.connect("drag_motion", self.on_drag_motion)
        big_box.connect("drag_leave", self.on_drag_leave)

    def __setup_disabled_modules_tab(self):
        self.disabledmoduleview = DisabledModuleListView( self._model.get_disabled_module_list() )
        self.disabledmoduleview.get_selection().connect("changed", self.on_disabled_module_changed)
        
        disabledhandlers = self.glade.get_widget("disabledhandlers")
        disabledhandlers.add(self.disabledmoduleview)
        
        self.disabledhandlers_box = self.glade.get_widget("disabledhandlers_box")

    def __select_first_tab(self):
         # Select first tab
        notebook = self.glade.get_widget("notebook1")
        current = notebook.get_current_page()
        if (current != 0):
            for i in range(current):
                notebook.prev_page()

    def __is_nsm_available(self):
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        _dbus = dbus.Interface(proxy, 'org.freedesktop.DBus')
        _dbus.ReloadConfig()
        bus_names = _dbus.ListActivatableNames()
        return (NewStuffUpdater.NEW_STUFF_SERVICE in bus_names)

    def __enable_newstuffmanager(self, status):
        if status:
            self.web_module_list = WebModuleList()
            
            container = self.glade.get_widget("newhandlers")
            self.webmoduleview = WebModuleListView(self.web_module_list)
            self.webmoduleview.get_selection().connect("changed", self.on_webmodule_selected)
            self.web_module_list.connect('row-changed', lambda list, path, iter: self.on_webmodule_selected    (self.webmoduleview.get_selection()))
            container.add(self.webmoduleview)
              
            self.install = self.glade.get_widget("install")
            self.check_new_extensions = self.glade.get_widget("check_new_extensions")
            self.check = self.glade.get_widget("check")
            self.update = self.glade.get_widget("update")
              
            self.check.connect('clicked', self.on_check_handlers)
            self.update.connect('clicked', self.on_update_handler)
            self.update.set_sensitive(False)
            self.check_new_extensions.connect('clicked', self.on_check_new_extensions)
            self.install.connect('clicked', self.on_install_handler)
            self.install.set_sensitive(False)
        else:
            notebook = self.glade.get_widget("notebook1")
            tab = self.glade.get_widget("extensions_vbox")
            notebook.remove_page( notebook.page_num(tab) )
            # Remove buttons in handlers tab
            self.glade.get_widget("check").destroy()
            self.glade.get_widget("update").destroy()
    
    def _call_on_newstuffmanager(self, method, *args):
        if self.newstuff == None:
            self.newstuff = NewStuffUpdater()
            self.newstuff.connect('ready', lambda s: getattr(self.newstuff, method)(*args) )
            self.newstuff.connect('error', self.on_newstuff_error)
            self.newstuff.connect('new-modules-available', self.on_new_modules_available)
            self.newstuff.connect('updates-available', self.on_updates_available)
        else:
            getattr(self.newstuff, method)(*args)
   
    def show_run_hide(self, parent):
        self.dialog.set_screen(parent.get_screen())
        self.dialog.show_all()
        self.moduleview.grab_focus()
        self.dialog.connect("response", self.on_dialog_response)
    
    def on_dialog_response(self, dialog, response):
        self.update_gconf()    
        self.dialog.destroy()
        if self.newstuff != None:
            self.newstuff.close()
        
    def sync_ui(self):
        if self.keybinding != None:
            self.keyboard_shortcut_entry.set_accelerator_name(self.keybinding)
        else:
            self.keyboard_shortcut_entry.set_accelerator_name("<Alt>F3")
        
        self.use_selection_box.set_active(self.use_selection)
   
    def on_hide_after_action_toggled(self, toggle):
        self._model.set_hide_after_action(toggle.get_active())
        
    def on_typingdelay_value_changed(self, spinbutton):
        self._model.set_type_delay(spinbutton.get_value())
        
    def on_max_history_items_changed(self, spinbutton):
        self._model.set_max_history_items(spinbutton.get_value())
            
    def on_keyboard_shortcut_entry_changed(self, entry, accel_name, keyval, mods, keycode):        
        if accel_name != "":
            self._model.set_keybinding(accel_name)
        return False

    def on_use_selection_toggled(self, toggle):
        self._model.set_use_selection(toggle.get_active())
        
    def on_more_button_clicked(self, button):
        if self.more_button_callback != None:
            self.more_button_callback(self.dialog)
    
    def on_module_selected(self, selection):
        module_context = self.moduleview.get_selected_module()
        
        if module_context != None:
            self.check_requirements(module_context)
            
        # Check if we can update
        if self.newstuff != None:
            #TODO: Save information whether update is available
            self.update.set_sensitive(module_context != None)                
    
    def set_buttons(self, selection):
        model, iter = selection.get_selected()
        if iter == None:
            return
        sensitive = model.is_module_enabled(iter)
        if sensitive:
            path = model.get_path(iter)
            path_first = model.get_path(model.get_iter_first())
            up = not (path == path_first)
            self.button_top.set_sensitive(up)
            self.button_up.set_sensitive(up)
            iter_next = model.iter_next(iter)
            down = not (iter_next == None or not model.is_module_enabled(iter_next))
            self.button_down.set_sensitive(down)
            self.button_bottom.set_sensitive(down)
        else:
            self.button_top.set_sensitive(sensitive)
            self.button_up.set_sensitive(sensitive)
            self.button_down.set_sensitive(sensitive)
            self.button_bottom.set_sensitive(sensitive)
    
    def on_disabled_module_changed(self, selection):
        module = self.disabledmoduleview.get_selected_module()
        
        if (len(self.disabledhandlers_box.get_children()) > 1):
            self.disabledhandlers_box.remove( self.disabledhandlers_box.get_children()[1] )
        if hasattr(module, "INSTRUCTIONS") and module.INSTRUCTIONS != None and module.INSTRUCTIONS != "":
            self.disabledhandlers_box.pack_end(InfoBox(module.INSTRUCTIONS, gtk.STOCK_DIALOG_ERROR), False, False, 0)
        self.disabledhandlers_box.show_all()
  
    def check_requirements(self, module):
        if module is None:
            return
        
        message = module.INSTRUCTIONS
        if not module.has_requirements():
            self.set_info(gtk.STOCK_DIALOG_ERROR, message, module.show_config)
            if module.is_enabled():
                self._model.stop_module(module)
        elif module.has_config():
            self.set_info(gtk.STOCK_DIALOG_INFO, message, module.show_config)
        else:
            self.set_info(None, None, None)
    
    def set_info(self, stock_icon, message, callback):
        self.more_button_callback = callback
        if message == self.old_info_message:
            return
        self.old_info_message = message
        
        self.info_area.remove(self.info_area.get_children()[0])
        
        if callable(callback):
            other_info = InfoBox(message, stock_icon)
            self.info_area.add( other_info )
            other_info.show_all()
            self.more_button.set_sensitive(self.more_button_callback != None)
        else:
            self.info_area.add(self.default_info)
            self.more_button.set_sensitive(False)
    
    def on_module_toggled(self, moduleview, module):
        if (module.is_enabled()):
            self._model.stop_module (module, False)
        else:
            self._model.initialize_module (module, False)
        self.update_gconf()
       
    def on_newstuff_error(self, newstuff, error):
          """
          Called if a connection to the repository failed
          
          An error message will be displayed in a MessageDialog
          and C{self.newstuff} is reset
          
          @type error: dbus_bindings.DBusException instance
          """
          dialog = ErrorDialog(self.dialog, _("A problem occured"), error)
          dialog.run()
          self.newstuff.close()
          self.newstuff = None
          
    def on_check_handlers(self, button):
        #Update all handlers
        current_modules = []
        for mod in self.module_list:
            current_modules.append((mod.get_id(), mod.INFOS["version"]))
        self._call_on_newstuffmanager("fetch_updates", current_modules)
            
    def on_check_new_extensions(self, button):
        current_modules = []
        for mod in self.module_list:
            current_modules.append(mod.get_id())
        self._call_on_newstuffmanager("fetch_new_modules", current_modules)
        
    def on_new_modules_available(self, newstuff, modules):
        for mod in modules:
            self.web_module_list.add(mod)
        
    def on_updates_available(self, newstuff, modules):
        for modid, desc in modules:
            self.module_list.set_module_update_available(modid)
        
    def on_update_handler(self, button):
        module = self.moduleview.get_selected_module()
        if module != None:
            # Trigger module update
            if self.newstuff != None:
                self.newstuff.install_module(module.get_id())
            button.set_sensitive(False)
        
    def on_install_handler(self, button):
        # Install the selected new handler
        mod_id = self.webmoduleview.get_selected_module_id()
        if mod_id != None:
            if self.newstuff != None:
                self.newstuff.install_module(mod_id)
            button.set_sensitive(False)
     
    def on_webmodule_selected(self, selection):
        mod_id = self.webmoduleview.get_selected_module_id()
        self.install.set_sensitive(mod_id != None)
              
    def on_drag_motion(self, widget, drag_context, x, y, timestamp):
        return False
    
    def on_drag_leave(self, big_box, drag_context, timestamp):
        big_box.queue_draw()
        
    def on_drag_data_received_data(self, widget, context, x, y, selection, info, etime):
        if (not(info == self.TARGET_URI_LIST or info == self.TARGET_NS_URL)):
            return
        if (info == self.TARGET_NS_URL):
            data = selection.data.strip().split("\n")[0]
        else:
            data = selection.data.strip()
        try:
            self._model.install_module(data)
            dialog = gtk.MessageDialog(parent=self.dialog,
                       flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                       type=gtk.MESSAGE_INFO,
                       buttons=gtk.BUTTONS_OK,
                       message_format=_("Handler has been installed successfully"))
            dialog.connect('response', lambda w, id: dialog.destroy())
        except Exception, e:
            dialog = ErrorDialog(self.dialog, _("Handler could not be installed due a problem with the provided file"), traceback.format_exc() )
        
        dialog.run()
        return
    
    def on_button_top_clicked(self, button):
        model, iter = self.moduleview.get_selection().get_selected()
        self.module_list.move_module_to_top(iter)
        self.moduleview.scroll_to_iter(iter)
        self.set_buttons(self.moduleview.get_selection())
        self.moduleview.grab_focus()
    
    def on_button_up_clicked(self, button):
        model, iter = self.moduleview.get_selection().get_selected()
        self.module_list.move_module_up(iter)
        self.moduleview.scroll_to_iter(iter)
        self.set_buttons(self.moduleview.get_selection())
        self.moduleview.grab_focus()
    
    def on_button_down_clicked(self, button):
        model, iter = self.moduleview.get_selection().get_selected()
        self.module_list.move_module_down(iter)
        self.moduleview.scroll_to_iter(iter)
        self.set_buttons(self.moduleview.get_selection())
        self.moduleview.grab_focus()
    
    def on_button_bottom_clicked(self, button):
        model, iter = self.moduleview.get_selection().get_selected()
        self.module_list.move_module_to_bottom(iter)
        self.moduleview.scroll_to_iter(iter)
        self.set_buttons(self.moduleview.get_selection())
        self.moduleview.grab_focus()
        
    def update_gconf(self):
         # Update the gconf enabled modules settings
        enabled_modules = [mod.__class__.__name__ for mod in self.module_list if mod.is_enabled()]
        self._model.set_enabled_modules(enabled_modules)
