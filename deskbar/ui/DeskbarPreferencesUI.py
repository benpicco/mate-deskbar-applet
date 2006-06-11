from gettext import gettext as _
from os.path import join
import struct
import gtk, gtk.gdk, gtk.glade, gobject, gconf
import deskbar, deskbar.Utils
from deskbar.updater.NewStuffUpdater import NewStuffUpdater
from deskbar.ui.ModuleListView import ModuleListView, WebModuleListView
from deskbar.ModuleList import WebModuleList
from deskbar import CUEMIAC_UI_NAME, ENTRIAC_UI_NAME

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
		(keyval, egroup, level, consumed_modifiers) = keymap.translate_keyboard_state(event.hardware_keycode, event.state, event.group)

		upper = event.keyval
		accel_keyval = gtk.gdk.keyval_to_lower(upper)

		# Put shift back if it changed the case of the key, not otherwise.
		if upper != accel_keyval and (consumed_modifiers & gtk.gdk.SHIFT_MASK):
			consumed_modifiers &= ~(gtk.gdk.SHIFT_MASK)

		# filter consumed/ignored modifiers
		ignored_modifiers = gtk.gdk.MOD2_MASK | gtk.gdk.MOD5_MASK
		accel_mods = event.state & gtk.gdk.MODIFIER_MASK & ~(consumed_modifiers | ignored_modifiers)
		
		if accel_mods == 0 and accel_keyval == gtk.keysyms.Escape:
			self.__cancel()
			return # cancel
		
		if not gtk.accelerator_valid(accel_keyval, accel_mods):
			self.__cancel()
			return # cancel

		accel_name = gtk.accelerator_name(accel_keyval, accel_mods)
		self.set_accelerator(accel_keyval, event.hardware_keycode, accel_mods)
		self.emit('accel-edited', accel_name, accel_keyval, accel_mods, event.hardware_keycode)
		return True

	def __cancel(self):
		self.set_accelerator_name(self.__old_value)
		return
		

class DeskbarPreferencesUI:
	def __init__(self, applet, module_loader, module_list):
		self.module_list = module_list
		self.web_module_list = WebModuleList()
		self.module_loader = module_loader
		self.glade = gtk.glade.XML(join(deskbar.SHARED_DATA_DIR, "prefs-dialog.glade"))
		
		self.newstuff = NewStuffUpdater(module_loader, module_list, self.web_module_list)
		
		self.dialog = self.glade.get_widget("preferences")
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
		
		container = self.glade.get_widget("newhandlers")
		self.webmoduleview = WebModuleListView(self.web_module_list)
		self.webmoduleview.get_selection().connect("changed", self.on_webmodule_selected)
		self.web_module_list.connect('row-changed', lambda list, path, iter: self.on_webmodule_selected(self.webmoduleview.get_selection()))
		
		container.add(self.webmoduleview)
		
		self.install = self.glade.get_widget("install")
		self.check = self.glade.get_widget("check")
		self.update = self.glade.get_widget("update")
		
		self.check.connect('clicked', self.on_check_handlers)
		self.update.connect('clicked', self.on_update_handler)
		self.update.set_sensitive(False)
		self.install.connect('clicked', self.on_install_handler)
		
		self.sync_ui()
		
	def show_run_hide(self):
		self.dialog.show_all()
		self.moduleview.grab_focus()
		self.dialog.connect("response", self.on_dialog_response)
	
	def on_dialog_response(self, dialog, response):	
		self.dialog.destroy()
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
			
	def set_width_settings_sensitive(self, sensitive):
		if sensitive and not self.expand:
			self.width_spin.set_sensitive(True)
			self.glade.get_widget("width_units").set_sensitive(True)
		else:
			self.width_spin.set_sensitive(False)
			self.glade.get_widget("width_units").set_sensitive(False)
			
		self.use_all_width_radio.set_sensitive(sensitive)
		self.fixed_width_radio.set_sensitive(sensitive)
		
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
			
	def on_ui_changed (self, sender, applet):
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

	def on_more_button_clicked(self, button):
		if self.more_button_callback != None:
			self.more_button_callback(self.dialog)
	
	def on_module_selected(self, selection):
		module_context = self.moduleview.get_selected_module_context()
		if module_context != None:
			self.check_requirements(module_context)
			gobject.timeout_add(1000, self.poll_requirements, module_context)
			
		# Check if we can update
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
			
	def on_check_handlers(self, button):
		#Update all handlers
		self.newstuff.check_all()
		
	def on_update_handler(self, button):
		module_context = self.moduleview.get_selected_module_context()
		if module_context != None:
			# Trigger module update
			self.newstuff.update(module_context)
			button.set_sensitive(False)
		
	def on_install_handler(self, button):
		# Install the selected new handler
		module_context = self.webmoduleview.get_selected_module_context()
		if module_context != None:
			self.newstuff.install(module_context)
			button.set_sensitive(False)
			
def show_preferences(applet, loader, model):
	DeskbarPreferencesUI(applet, loader, model).show_run_hide()
