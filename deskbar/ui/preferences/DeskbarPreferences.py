import gtk
import gtk.gdk
import traceback
from gettext import gettext as _
from os.path import join, basename
import deskbar
from deskbar.core.updater.Capuchin import *
from deskbar.core.ModuleList import WebModuleList
from deskbar.ui.preferences.AccelEntry import AccelEntry
from deskbar.ui.preferences.ErrorDialog import ErrorDialog
from deskbar.ui.preferences.ModuleListView import ModuleListView, DisabledModuleListView, WebModuleListView
from deskbar.ui.preferences.ProgressbarDialog import ProgressbarDialog
import dbus
import time
import dbus.glib
    
DESKBAR_CAPUCHIN_REPO = "http://www.gnome.org/~sebp/deskbar/deskbar-applet-2.24.xml"

class InfoBox(gtk.HBox):
    
    def __init__(self, text, stock_icon=gtk.STOCK_DIALOG_INFO):
        gtk.HBox.__init__(self, spacing=6)
        self.info_image = gtk.image_new_from_stock(stock_icon, gtk.ICON_SIZE_BUTTON)
        self.info_image.set_padding(3, 0)
        self.info_image.show()
        self.pack_start(self.info_image, expand=False, fill=False)
        self.label = gtk.Label()
        self.label.set_line_wrap(True)
        self.label.set_alignment(0.0, 0.5)
        self.label.set_justify(gtk.JUSTIFY_LEFT)
        self.label.set_markup(text)
        self.label.set_selectable(True)
        self.label.show()
        self.pack_start(self.label, expand=True, fill=True)

class DeskbarPreferences:
    
    def __init__(self, model):
        self._model = model
        self._model.connect("initialized", self.on_modules_initialized)
        
        self.module_list = self._model.get_module_list()
    
        self.builder = gtk.Builder()
        self.builder.add_from_file(join(deskbar.SHARED_DATA_DIR, "prefs-dialog.ui"))
        
        self.dialog = self.builder.get_object("preferences")
        
        # Since capuchin is optional we have to check if self.capuchin is None each time we use it
        self.__capuchin = None
        self.has_capuchin = False
        self.__capuchin_updated = False
        self.progessdialog = None
        self.__capuchin_installing = False
        
        self.keybinding = self._model.get_keybinding()
        
        self.__setup_active_modules_tab()
        
        self.__setup_general_tab()
        
        # Setup Drag & Drop
        self.__setup_drag_and_drop()
        
        self.__setup_disabled_modules_tab()
        
        # Setup capuchin
        self.__setup_updater()
          
        self.__select_first_tab()
        
        self.sync_ui()

    def __setup_active_modules_tab(self):
        container = self.builder.get_object("handlers")
        self.moduleview = ModuleListView(self.module_list)
        self.moduleview.connect ("row-toggled", self.on_module_toggled)
        self.moduleview.get_selection().connect("changed", self.on_module_selected)
        self.moduleview.get_selection().connect("changed", self.set_buttons)
        self.module_list.connect('row-changed', lambda list, path, iter: self.on_module_selected(self.moduleview.get_selection()))
        self.moduleview.show()
        container.add(self.moduleview)
        
        # Buttons beneath list
        self.more_button = self.builder.get_object("more")
        self.more_button.set_sensitive(False)
        self.more_button.connect("clicked", self.on_more_button_clicked)
        self.more_button_callback = None
        self.reload_button = self.builder.get_object("reload")
        self.reload_button.connect("clicked", self.on_reload_button_clicked)
        self.reload_button.set_tooltip_markup(("Reload all extensions"))

        # Info are at the bottom
        self.info_area = self.builder.get_object("info_area")
        self.old_info_message = None
        info_text = _("<i><small>Drag and drop an extension to change its order.</small></i>")
        self.default_info = InfoBox(info_text, gtk.STOCK_DIALOG_INFO)
        self.default_info.show()
        self.info_area.add(self.default_info)
        
        # Buttons on the right
        self.button_top = self.builder.get_object("button_top")
        self.button_top.connect("clicked", self.on_button_top_clicked)
        self.button_up = self.builder.get_object("button_up")
        self.button_up.connect("clicked", self.on_button_up_clicked)
        self.button_down = self.builder.get_object("button_down")
        self.button_down.connect("clicked", self.on_button_down_clicked)
        self.button_bottom = self.builder.get_object("button_bottom")
        self.button_bottom.connect("clicked", self.on_button_bottom_clicked)

    def __setup_general_tab(self):
        self.keyboard_shortcut_entry = AccelEntry()
        self.keyboard_shortcut_entry.connect('accel-edited', self.on_keyboard_shortcut_entry_changed)
        self.keyboard_shortcut_entry.get_widget().show()
        self.builder.get_object("keybinding_entry_container").pack_start(self.keyboard_shortcut_entry.get_widget(), False)
        
        if self._model.get_ui_name() == deskbar.BUTTON_UI_NAME:
            spinbutton = self.builder.get_object("width")
            spinbutton.set_value(self._model.get_entry_width())
            spinbutton.connect('value-changed', self.on_entry_width_changed)
        else:
            frame = self.builder.get_object("frame_width")
            frame.hide()
        
        self.use_selection = self._model.get_use_selection()
        self.use_selection_box = self.builder.get_object("use_selection")
        self.use_selection_box.connect('toggled', self.on_use_selection_toggled)

        self.sticktopanel_checkbox = self.builder.get_object("sticktopanel_checkbox")
        self.sticktopanel_checkbox.connect("toggled", self.on_ui_changed)
       
    def __setup_drag_and_drop(self):
        big_box = self.builder.get_object("big_box")
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
        self.disabledmoduleview.show()
        
        disabledhandlers = self.builder.get_object("disabledhandlers")
        disabledhandlers.add(self.disabledmoduleview)
        
        self.disabledhandlers_box = self.builder.get_object("disabledhandlers_box")

    def __select_first_tab(self):
        """ Select first tab """
        notebook = self.builder.get_object("notebook1")
        current = notebook.get_current_page()
        if (current != 0):
            for i in range(current):
                notebook.prev_page()

    def __setup_updater(self):
        if is_capuchin_available():
            self.has_capuchin = True
            
            self.web_module_list = WebModuleList()
            
            self.ROW_SEPERATOR_STRING = "<-->"
            self.ALL_EXTENSIONS_TEXT = _("All Extensions")
            
            self.combobox_tags = self.builder.get_object("combobox_tags")
            self.combobox_tags.set_row_separator_func( lambda model, iter: model[iter][0] == self.ROW_SEPERATOR_STRING )  
            
            tag_cell = gtk.CellRendererText ()
            self.combobox_tags.pack_start (tag_cell)
            self.combobox_tags.add_attribute (tag_cell, 'text', 0)
            
            self.tags_list = gtk.ListStore (str)
            self.tags_list.set_sort_column_id (0, gtk.SORT_ASCENDING)
            self.tags_list.set_sort_func (0, self._tags_sort_func)
            
            self.combobox_tags.set_model (self.tags_list)
            self.combobox_tags.connect ("changed", self.on_combobox_tags_changed)
            
            container = self.builder.get_object("newhandlers")
            
            self.webmoduleview = WebModuleListView(self.web_module_list)
            self.webmoduleview.get_selection().connect("changed", self.on_webmodule_selected)
            self.web_module_list.connect('row-changed', lambda list, path, iter: self.on_webmodule_selected    (self.webmoduleview.get_selection()))
            self.webmoduleview.show()
            container.add(self.webmoduleview)
              
            self.install = self.builder.get_object("install")
            self.check_new_extensions = self.builder.get_object("check_new_extensions")
            self.check = self.builder.get_object("check")
            self.update = self.builder.get_object("update")
              
            self.check.connect('clicked', self.on_check_handlers)
            self.update.connect('clicked', self.on_update_handler)
            self.update.set_sensitive(False)
            self.check_new_extensions.connect('clicked', self.on_check_new_extensions)
            self.install.connect('clicked', self.on_install_handler)
            self.install.set_sensitive(False)
        else:
            notebook = self.builder.get_object("notebook1")
            tab = self.builder.get_object("extensions_vbox")
            notebook.remove_page( notebook.page_num(tab) )
            # Remove buttons in handlers tab
            self.builder.get_object("check").destroy()
            self.builder.get_object("update").destroy()
    
    def _get_capuchin_instance(self):
        if self.__capuchin == None:
            manager = AppObjectManager ()
            self.__capuchin = manager.get_app_object (DESKBAR_CAPUCHIN_REPO)
            self.__capuchin.connect ('install-finished', self._on_install_finished)
            self.__capuchin.connect ('status', self._on_status)
            self.__capuchin.update (False)
            
            if self.progessdialog != None:
                self.progessdialog.destroy()
                self.progessdialog = None

        return self.__capuchin
       
    def _show_error_dialog(self, error):
          """
          An error message will be displayed in a MessageDialog
          """
          dialog = ErrorDialog(self.dialog, _("A problem occured"), error)
          dialog.run()
    
    def _show_module_installed_dialog(self):
        dialog = gtk.MessageDialog(parent=self.dialog,
                       flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                       type=gtk.MESSAGE_INFO,
                       buttons=gtk.BUTTONS_OK,
                       message_format=_("Extension has been installed successfully"))
        dialog.set_modal(True)
        dialog.connect ('response', lambda w, r: w.destroy())
        dialog.show_all ()
        
    def _tags_sort_func(self, model, iter1, iter2):
        val1 = model[iter1][0]
        val2 = model[iter2][0]
        if val1 == self.ALL_EXTENSIONS_TEXT:
            # Always at top
            return -1
        elif val2 == self.ALL_EXTENSIONS_TEXT:
            # Always at top
            return 1
        else:
            # Sort alphabetically
            if val1 < val2:
                return -1
            elif val1 > val2:
                return 1
            else:
                return 0
          
    def show_run_hide(self, parent):
        self.dialog.set_screen(parent.get_screen())
        self.dialog.show()
        self.moduleview.grab_focus()
        self.dialog.connect("response", self.on_dialog_response)
    
    def on_dialog_response(self, dialog, response):
        self._model.update_gconf()
        self.dialog.destroy()
        # Check if capuchin service is available and if actually used it
        if self.has_capuchin and self.__capuchin != None:
            self.__capuchin.close()
        
    def sync_ui(self):
        if self.keybinding != None:
            self.keyboard_shortcut_entry.set_accelerator_name(self.keybinding)
        else:
            self.keyboard_shortcut_entry.set_accelerator_name("<Alt>F3")
        
        self.use_selection_box.set_active(self.use_selection)
         
        self.sticktopanel_checkbox.set_active( self._model.get_ui_name() == deskbar.BUTTON_UI_NAME)
   
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

    def on_reload_button_clicked(self, button):
        self.reload_button.set_sensitive(False)
        self._model.reload_all_modules()
    
    def on_module_selected(self, selection):
        """
        Check if update for module is available
        and set button (in)sensitive
        """
        module = self.moduleview.get_selected_module()
         
        if module != None:
            self.check_requirements(module)
           
        # Check if module is not None, because the signal
        # is emitted when the user moves a module, too  
        # Check if we can update
        if self.has_capuchin:
            if module != None:
                self.update.set_sensitive(module.is_updateable())
            else:
                self.update.set_sensitive(False)
    
    def set_buttons(self, selection):
        """
        Set top/up/down/bottom sensitive according
        to the selected module
        """
        model, iter = selection.get_selected()
        if iter == None:
            self.__set_top_buttons_sensitive(False)
            self.__set_buttom_buttons_sensitive(False)
            return
        sensitive = model.is_module_enabled(iter)
        if sensitive:
            path = model.get_path(iter)
            path_first = model.get_path(model.get_iter_first())
            up = not (path == path_first)
            self.__set_top_buttons_sensitive(up)
            iter_next = model.iter_next(iter)
            down = not (iter_next == None or not model.is_module_enabled(iter_next))
            self.__set_buttom_buttons_sensitive(down)
        else:
            self.__set_top_buttons_sensitive(sensitive)
            self.__set_buttom_buttons_sensitive(sensitive)
    
    def __set_top_buttons_sensitive(self, sensitive):
        self.button_top.set_sensitive(sensitive)
        self.button_up.set_sensitive(sensitive)
        
    def __set_buttom_buttons_sensitive(self, sensitive):
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
        self._model.update_gconf()
    
    def on_check_handlers(self, button):
        """
        Check if updates for the installed modules are available
        """
        installed_modules = set()
        for mod in self.module_list:
            installed_modules.add( mod.get_id() )
        
        try:
            repo_plugins = set (self._get_capuchin_instance().get_available_plugins())
            
            # Get modules that are installed locally and are in the repository
            updateable_modules = repo_plugins & installed_modules 
                
            current_modules = []
            for mod in self.module_list:
                if mod.get_id() in updateable_modules:
                    current_modules.append( PluginInfo(mod.get_id(), mod.INFOS["version"]) )
            
            updates = self._get_capuchin_instance().get_available_updates (current_modules)
           
            for modid in updates:
                iter = self.module_list.get_iter_from_module_id (modid)
                self.module_list[iter][self.module_list.MODULE_CTX_COL].set_updateable (True)
                self.module_list.set_module_update_available(iter, True)
        except dbus.exceptions.DBusException, e:
            self._show_error_dialog(e)
            self.__capuchin.close()
            self.__capuchin = None
            
    def on_check_new_extensions(self, button):
        self._get_tags()
        self._get_new_modules()
        
    def on_update_handler(self, button):
        """ Update the selected module """
        module = self.moduleview.get_selected_module()
        if module != None:
            self.__capuchin_installing = False
            self._capuchin_install(module.get_id())
            button.set_sensitive(False)
        
    def on_install_handler(self, button):
        """ Install the selected new handler """
        mod_id = self.webmoduleview.get_selected_module_id()
        self.__capuchin_installing = True
        self._capuchin_install(mod_id)
        button.set_sensitive(False)
        
    def on_combobox_tags_changed (self, combobox):
        iter = combobox.get_active_iter()
        if iter == None:
            return
        
        selected_tag = self.tags_list[iter][0]
        
        if selected_tag == self.ALL_EXTENSIONS_TEXT:
            self.web_module_list.clear ()
            self._get_new_modules()
        else:
            try:
                plugins = self._get_capuchin_instance().get_plugins_with_tag (selected_tag)
                self.web_module_list.clear ()
                for mod_id in plugins:
                    self._add_module_infos_to_web_modules (mod_id)
            except dbus.exceptions.DBusException, e:
                self._show_error_dialog(e)
                self.__capuchin.close()
                self.__capuchin = None
            
    def _capuchin_install(self, mod_id):
        if mod_id != None:
            if self.has_capuchin:
                try:
                    self._get_capuchin_instance().install(mod_id)
                except dbus.exceptions.DBusException, e:
                    self._show_error_dialog(e)
                    self.__capuchin.close()
                    self.__capuchin = None
     
    def _get_tags (self):
        self.tags_list.clear()
        self.tags_list.append ([self.ALL_EXTENSIONS_TEXT])
        self.tags_list.append ([self.ROW_SEPERATOR_STRING])
            
        try:
            for tag in self._get_capuchin_instance().get_tags ():
                self.tags_list.append ( [tag] )
        except dbus.exceptions.DBusException, e:
            self._show_error_dialog(e)
            self.__capuchin.close()
            self.__capuchin = None
            
        self.combobox_tags.set_active (0) # Set to all
    
    def _get_new_modules (self):
        """
        Display a list of modules that aren't installed, yet
        """
        local_modules = set()
        for mod in self.module_list:
            local_modules.add(mod.get_id())
            
        for mod in self._model.get_disabled_module_list():
            local_modules.add(basename(mod.filename))
        
        try:
            repo_modules = set (self._get_capuchin_instance().get_available_plugins())
            
            new_modules = repo_modules - local_modules
            
            for mod_id in new_modules:
                self._add_module_infos_to_web_modules (mod_id)
        except dbus.exceptions.DBusException, e:
            self._show_error_dialog(e)
            self.__capuchin.close()
            self.__capuchin = None
            
    def _add_module_infos_to_web_modules (self, mod_id):
        mod_name, mod_desc = self._get_capuchin_instance().get_plugin_infos (mod_id)
        self.web_module_list.add(mod_id, mod_name, mod_desc)
   
    def on_webmodule_selected(self, selection):
        mod_id = self.webmoduleview.get_selected_module_id()
        self.install.set_sensitive(mod_id != None)
    
    def _on_status(self, appobject, action, plugin_id, progress, speed):
        primary_text = _("Installing extension")
        secondary_text = _("The extension will be downloaded and installed.")
        if action == ACTION_UPDATING_REPO:
            primary_text = _("Retrieving list of extensions")
            secondary_text = _("A list of available extensions is downloaded.")
            action_text = _("Retrieving the extension index")
        elif action == ACTION_DOWNLOADING_PLUGIN:
            action_text = _("Downloading extension")
        elif action == ACTION_EXTRACTING_PLUGIN:
            action_text = _("Extracting archive")
        else:
            return
        
        if self.progessdialog == None:
            # Create new dialog
            self.progessdialog = ProgressbarDialog (self.dialog)
            self.progessdialog.set_text (primary_text, secondary_text)
            self.progessdialog.run_nonblocked ()
        
        self.progessdialog.set_current_operation (action_text)
        self.progessdialog.set_fraction (progress)
    
    def _on_install_finished(self, appobject, plugin_id):
        self.progessdialog.destroy ()
        self.progessdialog = None
        
        # indicates that repository index has been downloaded
        if plugin_id == "INDEX":
            return
        
        # Remove from webmodulelist
        if self.__capuchin_installing:
            # We where installing a new module
            model, iter = self.webmoduleview.get_selection().get_selected()
            self.web_module_list.remove (iter)
            self.__capuchin_installing = False
        else:
            # We updated a already installed module
            model, iter = self.moduleview.get_selection().get_selected()
            self.module_list[iter][self.module_list.MODULE_CTX_COL].set_updateable (False)
            self.module_list.set_module_update_available(iter, False)
        
        self._show_module_installed_dialog()
           
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
            self._show_module_installed_dialog()
        except Exception, e:
            dialog = ErrorDialog(self.dialog,
                                 _("Extension could not be installed due to a problem with the provided file"),
                                 traceback.format_exc() )
            dialog.run()
        
        return
    
    def on_button_top_clicked(self, button):
        model, iter = self.moduleview.get_selection().get_selected()
        if iter != None:
            self.module_list.move_module_to_top(iter)
            self.moduleview.scroll_to_iter(iter)
            self.set_buttons(self.moduleview.get_selection())
            self.moduleview.grab_focus()
    
    def on_button_up_clicked(self, button):
        model, iter = self.moduleview.get_selection().get_selected()
        if iter != None:
            self.module_list.move_module_up(iter)
            self.moduleview.scroll_to_iter(iter)
            self.set_buttons(self.moduleview.get_selection())
            self.moduleview.grab_focus()
    
    def on_button_down_clicked(self, button):
        model, iter = self.moduleview.get_selection().get_selected()
        if iter != None:
            self.module_list.move_module_down(iter)
            self.moduleview.scroll_to_iter(iter)
            self.set_buttons(self.moduleview.get_selection())
            self.moduleview.grab_focus()
    
    def on_button_bottom_clicked(self, button):
        model, iter = self.moduleview.get_selection().get_selected()
        if iter != None:
            self.module_list.move_module_to_bottom(iter)
            self.moduleview.scroll_to_iter(iter)
            self.set_buttons(self.moduleview.get_selection())
            self.moduleview.grab_focus()
        
    def on_ui_changed(self, check):
        frame = self.builder.get_object("frame_width")
        if self.sticktopanel_checkbox.get_active():
            self._model.set_ui_name(deskbar.BUTTON_UI_NAME)
            frame.show()
        else:
            self._model.set_ui_name(deskbar.WINDOW_UI_NAME)
            frame.hide()
            
    def on_modules_initialized(self, model):
        self.reload_button.set_sensitive(True)
        
    def on_entry_width_changed(self, spinbutton):
        self._model.set_entry_width(spinbutton.get_value())
