from gettext import gettext as _
from os.path import join
import gtk, gtk.glade, gobject, gconf
import deskbar, deskbar.handler_utils
from deskbar.module_list import ModuleListView

class PrefsDialog:
	def __init__(self, applet, module_loader, module_list):
		self.module_list = module_list
		self.module_loader = module_loader
		self.glade = gtk.glade.XML(join(deskbar.SHARED_DATA_DIR, "prefs-dialog.glade"))

		self.dialog = self.glade.get_widget("preferences")
		
		pixbuf = deskbar.handler_utils.load_icon("deskbar-applet-small.png")
		if pixbuf != None:
			self.dialog.set_icon(pixbuf)

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
		
		self.keyboard_shortcut_entry = self.glade.get_widget("keyboard_shortcut_entry")
		self.keyboard_shortcut_entry.connect('changed', self.on_keyboard_shortcut_entry_changed, applet)
		self.keybinding_notify_id = deskbar.GCONF_CLIENT.notify_add(applet.prefs.GCONF_KEYBINDING, lambda x, y, z, a: self.on_config_keybinding(z.value))
		
		container = self.glade.get_widget("handlers")
		self.moduleview = ModuleListView(module_list)
		self.moduleview.connect ("row-toggled", self.on_module_toggled, module_loader)
		self.moduleview.get_selection().connect("changed", self.on_module_selected)
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
		self.more_button = gtk.Button(_("_More..."))
		self.more_button.connect("clicked", self.on_more_button_clicked)
		self.more_button_callback = None
		self.other_info.pack_start(self.more_button, expand=False, fill=False)

		self.info_area = self.glade.get_widget("info_area")
		self.old_info_message = None
				
		self.sync_ui()
		
	def show_run_hide(self):
		self.dialog.show_all()
		self.moduleview.grab_focus()
		self.dialog.run()
		self.dialog.destroy()
		
		deskbar.GCONF_CLIENT.notify_remove(self.width_notify_id)
		deskbar.GCONF_CLIENT.notify_remove(self.expand_notify_id)
		deskbar.GCONF_CLIENT.notify_remove(self.keybinding_notify_id)
		
		# Update the gconf enabled modules settings
		enabled_modules = [ctx.handler for ctx in self.module_list if ctx.enabled]
		deskbar.GCONF_CLIENT.set_list(deskbar.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING, enabled_modules)
	
	def sync_ui(self):
		if self.expand:
			self.use_all_width_radio.set_active(True)
		else:
			self.fixed_width_radio.set_active(True)
		self.width_spin.set_value(self.width)
		self.keyboard_shortcut_entry.set_text(self.keybinding)
		
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
		
	def on_use_all_width_radio_toggle(self, toggle, applet):
		deskbar.GCONF_CLIENT.set_bool(applet.prefs.GCONF_EXPAND, toggle.get_property('active'))
		
	def on_spin_width_change(self, spinner, applet):
		deskbar.GCONF_CLIENT.set_int(applet.prefs.GCONF_WIDTH, int(spinner.get_value()))
	
	def on_keyboard_shortcut_entry_changed(self, entry, applet):
		deskbar.GCONF_CLIENT.set_string(applet.prefs.GCONF_KEYBINDING, entry.get_text())
	
	def on_more_button_clicked(self, button):
		if self.more_button_callback != None:
			self.more_button_callback()
	
	def on_module_selected(self, selection):
		module_context = self.moduleview.get_selected_module_context()
		if module_context != None:
			self.check_requirements(module_context)
			gobject.timeout_add(1000, self.poll_requirements, module_context)
	
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
			if status == deskbar.handler.HANDLER_HAS_REQUIREMENTS:
				self.set_info(message, callback)
				if module_context.enabled:
					self.module_loader.stop_module_async(module_context)
			elif status == deskbar.handler.HANDLER_IS_CONFIGURABLE:
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
			if self.more_button_callback != None:
				self.more_button.show()
			else:
				self.more_button.hide()
	
	def on_module_toggled(self, moduleview, context, loader):
		if (context.enabled):
			loader.stop_module_async (context)
		else:
			loader.initialize_module_async (context)

def show_preferences(applet, loader, model):
	PrefsDialog(applet, loader, model).show_run_hide()
