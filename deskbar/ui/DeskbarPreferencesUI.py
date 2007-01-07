from gettext import gettext as _
from os.path import join, isdir
import os
import struct
import gtk, gtk.gdk, gtk.glade, gobject, gconf
import dbus
import deskbar, deskbar.Utils
from deskbar.updater.NewStuffUpdater import NewStuffUpdater
from deskbar.ui.ModuleListView import ModuleListView, WebModuleListView
from deskbar.ModuleList import WebModuleList
from deskbar import CUEMIAC_UI_NAME, ENTRIAC_UI_NAME, WINDOW_UI_NAME
from deskbar.ModuleInstaller import ModuleInstaller

if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib

MAXINT = 2 ** ((8 * struct.calcsize('i')) - 1) - 1

class AccelEntry( gobject.GObject ):

	__gsignals__ = {
		'accel-edited': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
						 [gobject.TYPE_STRING, gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT]),
	}
	__gproperties__ = {
		'message': (gobject.TYPE_STRING, 'Prompt message', 'Message that prompts the user to assign a new accelerator', _('New accelerator...'), gobject.PARAM_READWRITE|gobject.PARAM_CONSTRUCT),
		'accel_key': ( gobject.TYPE_UINT, "Accelerator key", "Accelerator key", 0, MAXINT, 0, gobject.PARAM_READWRITE ),
		'accel_mask': ( gobject.TYPE_FLAGS, "Accelerator modifiers", "Accelerator modifiers", 0, gobject.PARAM_READWRITE ),
		'keycode': ( gobject.TYPE_UINT, "Accelerator keycode", "Accelerator keycode", 0, MAXINT, 0, gobject.PARAM_READWRITE ),
	}

	def __init__(self, accel_name=''):
		self.__old_value = None
		self._attributes = {'accel_key': 0, 'accel_mask': 0, 'keycode': 0}
		gobject.GObject.__init__(self)
		
		self.entry = gtk.Entry()
		self.entry.set_property('editable', False)
		self.entry.connect('button-press-event', self.__on_button_press_event)
		self.entry.connect('key-press-event', self.__on_key_press_event)
		self.entry.connect('focus-out-event', self.__on_focus_out_event)

		self.set_accelerator_name(accel_name)

	def do_get_property(self, pspec):
		if pspec.name in ('message', 'accel_key', 'accel_mask', 'keycode'):
			return self._attributes[pspec.name]
	
	def do_set_property(self, pspec, value):
		if pspec.name == 'message':
			self._attributes['message'] = value
		elif pspec.name == 'accel_key':
			self.set_accelerator(int(value), self.get_property('keycode'), self.get_property('accel_mask'))
		elif pspec.name == 'accel_mask':
			self.set_accelerator(self.get_property('accel_key'), self.get_property('keycode'), int(value))
		elif pspec.name == 'keycode':
			self.set_accelerator(self.get_property('accel_key'), int(value), self.get_property('accel_mask'))

	def get_accelerator_name(self):
		return self.entry.get_text()

	def set_accelerator_name(self, value):
		if value == None:
			value = ""
			
		(keyval, mods) = gtk.accelerator_parse(value)
		if gtk.accelerator_valid(keyval, mods):
			self.entry.set_text(value)
		return

	def get_accelerator(self):
		return ( self.get_property('accel_key'), self.get_property('keycode'), self.get_property('accel_mask') )

	def set_accelerator(self, keyval, keycode, mask):
		changed = False
		self.freeze_notify()
		if keyval != self._attributes['accel_key']:
			self._attributes['accel_key'] = keyval
			self.notify('accel_key')
			changed = True
			
		if mask != self._attributes['accel_mask']:
			self._attributes['accel_mask'] = mask
			self.notify('accel_mask')
			changed = True
			
		if keycode != self._attributes['keycode']:
			self._attributes['keycode'] = keycode
			self.notify('keycode')
			changed = True
			
		self.thaw_notify()
		if changed:
			text = self.__convert_keysym_state_to_string (keyval, keycode, mask)
			self.entry.set_text(text)
			
	def __convert_keysym_state_to_string(self, keysym, keycode, mask):
		if (keysym != 0 and keycode != 0):
			return gtk.accelerator_name(keysym, mask)

	def get_widget(self):
		return self.entry

	def __on_button_press_event(self, entry, event):
		self.__old_value = self.entry.get_text()
		entry.set_text(self.get_property('message'))
		entry.grab_focus()
		return True

	def __on_key_press_event(self, entry, event):
		edited = False
		
		keymap = gtk.gdk.keymap_get_default()
		translation = keymap.translate_keyboard_state(event.hardware_keycode, event.state, event.group)
		if translation == None:
			self.__revert()
			return
			
		(keyval, egroup, level, consumed_modifiers) = translation
		upper = event.keyval
		accel_keyval = gtk.gdk.keyval_to_lower(upper)

		if (accel_keyval >= gtk.keysyms.a and accel_keyval <= gtk.keysyms.z):
			self.__revert()
			return

		# Put shift back if it changed the case of the key, not otherwise.
		if upper != accel_keyval and (consumed_modifiers & gtk.gdk.SHIFT_MASK):
			consumed_modifiers &= ~(gtk.gdk.SHIFT_MASK)

		# filter consumed/ignored modifiers
		ignored_modifiers = gtk.gdk.MOD2_MASK | gtk.gdk.MOD5_MASK
		accel_mods = event.state & gtk.gdk.MODIFIER_MASK & ~(consumed_modifiers | ignored_modifiers)
		
		if accel_mods == 0 and accel_keyval == gtk.keysyms.Escape:
			self.__revert()
			return
		
		if not gtk.accelerator_valid(accel_keyval, accel_mods):
			self.__cancel()
			return

		accel_name = gtk.accelerator_name(accel_keyval, accel_mods)
		self.set_accelerator(accel_keyval, event.hardware_keycode, accel_mods)
		self.__old_value = None
		self.emit('accel-edited', accel_name, accel_keyval, accel_mods, event.hardware_keycode)
		return True

	def __on_focus_out_event(self, entry, event):
		if self.__old_value != None:
			self.__revert()

	def __cancel(self):
		self.set_accelerator_name("")
	
	def __revert(self):
		self.set_accelerator_name(self.__old_value)

class DeskbarPreferencesUI:
	def __init__(self, applet, module_loader, module_list):
		self.module_list = module_list
		self.web_module_list = WebModuleList()
		self.module_loader = module_loader
		self.glade = gtk.glade.XML(join(deskbar.SHARED_DATA_DIR, "prefs-dialog.glade"))
		
		self.dialog = self.glade.get_widget("preferences")
		
		# Since newstuff is optional we have to check if self.newstuff is None each time we use it
		self.newstuff = None
			
		# Retreive current values
		self.width = deskbar.GCONF_CLIENT.get_int(applet.prefs.GCONF_WIDTH)
		self.expand = deskbar.GCONF_CLIENT.get_bool(applet.prefs.GCONF_EXPAND)
		self.keybinding = deskbar.GCONF_CLIENT.get_string(applet.prefs.GCONF_KEYBINDING)
		
		self.width_spin = self.glade.get_widget("width")
		self.width_spin.connect('value-changed', self.on_spin_width_change, applet)
		self.width_notify_id = deskbar.GCONF_CLIENT.notify_add(applet.prefs.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))

		self.use_all_width_radio = self.glade.get_widget("use_all_width_radio")
		self.use_all_width_radio.connect('toggled', self.on_use_all_width_radio_toggle, applet)
		self.expand_notify_id = deskbar.GCONF_CLIENT.notify_add(applet.prefs.GCONF_EXPAND, lambda x, y, z, a: self.on_config_expand(z.value))
		self.fixed_width_radio = self.glade.get_widget("fixed_width_radio")
		
		self.keyboard_shortcut_entry = AccelEntry()
		self.keyboard_shortcut_entry.connect('accel-edited', self.on_keyboard_shortcut_entry_changed, applet)
		self.glade.get_widget("keybinding_entry_container").pack_start(self.keyboard_shortcut_entry.get_widget(), False)
		self.keybinding_notify_id = deskbar.GCONF_CLIENT.notify_add(applet.prefs.GCONF_KEYBINDING, lambda x, y, z, a: self.on_config_keybinding(z.value))
		
		container = self.glade.get_widget("handlers")
		self.moduleview = ModuleListView(module_list)
		self.moduleview.connect ("row-toggled", self.on_module_toggled, module_loader)
		self.moduleview.get_selection().connect("changed", self.on_module_selected)
		self.module_list.connect('row-changed', lambda list, path, iter: self.on_module_selected(self.moduleview.get_selection()))
		container.add(self.moduleview)

		self.default_info = self.glade.get_widget("default_info")
		self.width_units = self.glade.get_widget("width_units")

		self.other_info = gtk.HBox(spacing=6)
		info_image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_BUTTON)
		info_image.set_padding(3, 0)
		self.other_info.pack_start(info_image, expand=False, fill=False)
		self.other_info_label = gtk.Label()
		self.other_info_label.set_alignment(0.0, 0.5)
		self.other_info_label.set_justify(gtk.JUSTIFY_LEFT)
		self.other_info.pack_start(self.other_info_label, expand=True, fill=True)
		
		self.more_button = self.glade.get_widget("more")
		self.more_button.set_sensitive(False)
		self.more_button.connect("clicked", self.on_more_button_clicked)
		self.more_button_callback = None

		self.info_area = self.glade.get_widget("info_area")
		self.old_info_message = None
		
		self.ui_name = deskbar.GCONF_CLIENT.get_string(applet.prefs.GCONF_UI_NAME)
		self.completion_ui_radio = self.glade.get_widget("completion_radio")
		self.cuemiac_ui_radio = self.glade.get_widget("cuemiac_radio")
		self.completion_ui_radio.connect ("toggled", self.on_ui_changed, applet)
		self.cuemiac_ui_radio.connect ("toggled", self.on_ui_changed, applet)
		self.ui_change_id = deskbar.GCONF_CLIENT.notify_add(applet.prefs.GCONF_UI_NAME, lambda x, y, z, a: self.on_config_ui(z.value))
		
		self.use_selection = deskbar.GCONF_CLIENT.get_bool(applet.prefs.GCONF_USE_SELECTION)
		self.use_selection_box = self.glade.get_widget("use_selection")
		self.use_selection_box.connect('toggled', self.on_use_selection_toggled, applet)
		self.use_selection_id = deskbar.GCONF_CLIENT.notify_add(applet.prefs.GCONF_USE_SELECTION, lambda x, y, z, a: self.on_config_use_selection(z.value))
		
		# Setup new-stuff-manager
		self.__enable_newstuffmanager( self.__is_nsm_available() )
  		
		# Setup Drag & Drop
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
		
		self.sync_ui()

	def __invoke_newstuff(self, func):
  		if self.newstuff == None:			
  			self.newstuff = NewStuffUpdater(self.dialog, self.module_loader, self.module_list, self.web_module_list)
  			self.newstuff.connect('ready', self.on_newstuff_ready, getattr(self.newstuff, func))
  			self.newstuff.connect('connection-failed', self.on_connection_failed)			
  		else:
  			getattr(self.newstuff, func)()

	def __is_nsm_available(self):
		bus = dbus.SessionBus()
		proxy = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
		_dbus = dbus.Interface(proxy, 'org.freedesktop.DBus')
		_dbus.ReloadConfig()
		bus_names = _dbus.ListActivatableNames()
		return (NewStuffUpdater.NEW_STUFF_SERVICE in bus_names)

	def __enable_newstuffmanager(self, status):
		if status:
			container = self.glade.get_widget("newhandlers")
  			self.webmoduleview = WebModuleListView(self.web_module_list)
	  		self.webmoduleview.get_selection().connect("changed", self.on_webmodule_selected)
  			self.web_module_list.connect('row-changed', lambda list, path, iter: self.on_webmodule_selected	(self.webmoduleview.get_selection()))
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
  		
  	def on_connection_failed(self, newstuff, error):
  		"""
  		Called if a connection to the repository failed
  		
  		An error message will be displayed in a MessageDialog
  		and C{self.newstuff} is reset
  		
  		@type error: dbus_bindings.DBusException instance
  		"""
  		dialog = gtk.MessageDialog(parent=self.dialog, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)		
  		dialog.set_markup('<span weight="bold" size="larger">%s</span>\n\n%s' % (_("Connection to repository failed"), _("Please check your internet connection")))
  		dialog.run()
  		dialog.destroy()
  		self.newstuff.close()
  		self.newstuff = None
	
	def show_run_hide(self, parent):
		self.dialog.set_screen(parent.get_screen())
		self.dialog.show_all()
		self.moduleview.grab_focus()
		self.dialog.connect("response", self.on_dialog_response)
	
	def on_dialog_response(self, dialog, response):	
		self.dialog.destroy()
		if self.newstuff != None:
			self.newstuff.close()
		
		deskbar.GCONF_CLIENT.notify_remove(self.width_notify_id)
		deskbar.GCONF_CLIENT.notify_remove(self.expand_notify_id)
		deskbar.GCONF_CLIENT.notify_remove(self.keybinding_notify_id)
		deskbar.GCONF_CLIENT.notify_remove(self.ui_change_id)
		
		# Update the gconf enabled modules settings
		enabled_modules = [ctx.handler for ctx in self.module_list if ctx.enabled]
		deskbar.GCONF_CLIENT.set_list(deskbar.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING, enabled_modules)
	
	def sync_ui(self):
		if self.expand:
			self.use_all_width_radio.set_active(True)
		else:
			self.fixed_width_radio.set_active(True)
			
		self.width_spin.set_value(self.width)
		
		if self.keybinding != None:
			self.keyboard_shortcut_entry.set_accelerator_name(self.keybinding)
		else:
			self.keyboard_shortcut_entry.set_accelerator_name("<Alt>F3")
		
		if self.ui_name == ENTRIAC_UI_NAME:
			self.completion_ui_radio.set_active (True)
			self.set_width_settings_sensitive(True)
		elif self.ui_name == CUEMIAC_UI_NAME:
			self.cuemiac_ui_radio.set_active (True)
			self.set_width_settings_sensitive(False)
		elif self.ui_name == WINDOW_UI_NAME:
			self.cuemiac_ui_radio.set_active (True)
			self.set_ui_settings_sensitive(False)
			self.set_width_settings_sensitive(False)
		
		self.use_selection_box.set_active(self.use_selection)
			
	def set_width_settings_sensitive(self, sensitive):
		if sensitive and not self.expand:
			self.width_spin.set_sensitive(True)
			self.width_units.set_sensitive(True)
		else:
			self.width_spin.set_sensitive(False)
			self.width_units.set_sensitive(False)
			
		self.use_all_width_radio.set_sensitive(sensitive)
		self.fixed_width_radio.set_sensitive(sensitive)

	def set_ui_settings_sensitive(self, sensitive):
		self.cuemiac_ui_radio.set_sensitive(sensitive)
		self.completion_ui_radio.set_sensitive(sensitive)

		
	def on_config_width(self, value):
		if value != None and value.type == gconf.VALUE_INT:
			self.width = value.get_int()
			self.sync_ui()
	
	def on_config_expand(self, value):
		if value != None and value.type == gconf.VALUE_BOOL:
			self.expand = value.get_bool()
			self.sync_ui()
		
	def on_config_keybinding(self, value):
		if value != None and value.type == gconf.VALUE_STRING:
			self.keybinding = value.get_string()
			self.sync_ui()
	
	def on_config_ui (self, value):
		if value != None and value.type == gconf.VALUE_STRING:
			self.ui_name = value.get_string ()
			self.sync_ui()
	
	def on_config_use_selection(self, value):
		if value != None and value.type == gconf.VALUE_BOOL:
			self.use_selection = value.get_bool()
			self.sync_ui()
			
	def on_ui_changed (self, sender, applet):
		if self.ui_name == WINDOW_UI_NAME:
			# You cannot change to or from window ui
			return
		if self.completion_ui_radio.get_active ():
			deskbar.GCONF_CLIENT.set_string(applet.prefs.GCONF_UI_NAME, ENTRIAC_UI_NAME)
		elif self.cuemiac_ui_radio.get_active ():
			deskbar.GCONF_CLIENT.set_string(applet.prefs.GCONF_UI_NAME, CUEMIAC_UI_NAME)
			
	def on_use_all_width_radio_toggle(self, toggle, applet):
		deskbar.GCONF_CLIENT.set_bool(applet.prefs.GCONF_EXPAND, toggle.get_property('active'))
		
	def on_spin_width_change(self, spinner, applet):
		deskbar.GCONF_CLIENT.set_int(applet.prefs.GCONF_WIDTH, int(spinner.get_value()))
	
	def on_keyboard_shortcut_entry_changed(self, entry, accel_name, keyval, mods, keycode, applet):		
		if accel_name != "":
				deskbar.GCONF_CLIENT.set_string(applet.prefs.GCONF_KEYBINDING, accel_name)
		return False

	def on_use_selection_toggled(self, toggle, applet):
		deskbar.GCONF_CLIENT.set_bool(applet.prefs.GCONF_USE_SELECTION, toggle.get_active())
		
	def on_more_button_clicked(self, button):
		if self.more_button_callback != None:
			self.more_button_callback(self.dialog)
	
	def on_module_selected(self, selection):
		module_context = self.moduleview.get_selected_module_context()
		if module_context != None:
			self.check_requirements(module_context)
			gobject.timeout_add(1000, self.poll_requirements, module_context)
			
		# Check if we can update
		if self.newstuff != None:
			self.update.set_sensitive(module_context != None and module_context.update_infos[0])				
	
	def on_webmodule_selected(self, selection):
		module_context = self.webmoduleview.get_selected_module_context()
		self.install.set_sensitive(module_context != None and not module_context.installing)
		
	def poll_requirements(self, module_context):
		try:
			if module_context != self.moduleview.get_selected_module_context():
				return False
		except AttributeError:
			return False
		self.check_requirements(module_context)
		return True
	
	def check_requirements(self, module_context):
		if module_context is None:
			return
		if "requirements" in module_context.infos:
			status, message, callback = module_context.infos["requirements"]()
			if status == deskbar.Handler.HANDLER_HAS_REQUIREMENTS:
				self.set_info(message, callback)
				if module_context.enabled:
					self.module_loader.stop_module_async(module_context)
			elif status == deskbar.Handler.HANDLER_IS_CONFIGURABLE:
				self.set_info(message, callback)
			else:
				self.set_info(None, None)
		else:
			self.set_info(None, None)
	
	def set_info(self, message, callback):
		self.more_button_callback = callback
		if message == self.old_info_message:
			return
		self.old_info_message = message
		
		self.info_area.remove(self.info_area.get_children()[0])
		if message == None:
			self.info_area.add(self.default_info)
			self.more_button.set_sensitive(False)
		else:
			self.other_info_label.set_text(message)
			self.info_area.add(self.other_info)
			self.other_info.show_all()
			self.more_button.set_sensitive(self.more_button_callback != None)

	
	def on_module_toggled(self, moduleview, context, loader):
		if (context.enabled):
			loader.stop_module_async (context)
		else:
			loader.initialize_module_async (context)
	
	def on_newstuff_ready(self, newstuff, func):
		func()
		
	def on_check_handlers(self, button):
		#Update all handlers
		self.__invoke_newstuff('check_all')
			
	def on_check_new_extensions(self, button):
		self.__invoke_newstuff('check_new')
		
	def on_update_handler(self, button):
		module_context = self.moduleview.get_selected_module_context()
		if module_context != None:
			# Trigger module update
			if self.newstuff != None:
				self.newstuff.update(module_context)
			button.set_sensitive(False)
		
	def on_install_handler(self, button):
		# Install the selected new handler
		module_context = self.webmoduleview.get_selected_module_context()
		if module_context != None:
			if self.newstuff != None:
				self.newstuff.install(module_context)
			button.set_sensitive(False)
			
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
		module_installer = ModuleInstaller(self.module_loader)
		if module_installer.install(data):
		
			dialog = gtk.MessageDialog(parent=self.dialog,
								   flags=gtk.DIALOG_DESTROY_WITH_PARENT,
								   type=gtk.MESSAGE_INFO,
								   buttons=gtk.BUTTONS_OK,
								   message_format=_("Handler has been installed successfully"))
		else:
			dialog = gtk.MessageDialog(parent=self.dialog,
								   flags=gtk.DIALOG_DESTROY_WITH_PARENT,
								   type=gtk.MESSAGE_ERROR,
								   buttons=gtk.BUTTONS_OK,
								   message_format=_("Handler could not be installed due a problem with the provided file"))
		dialog.connect('response', lambda w, id: dialog.destroy())
		dialog.run()
		
		
		return
			
def show_preferences(applet, loader, model):
	DeskbarPreferencesUI(applet, loader, model).show_run_hide(applet.applet)
