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
		pixbuf = deskbar.handler_utils.load_icon("deskbar-applet-small.png", 16)
		if pixbuf != None:
			self.dialog.set_icon(pixbuf)

		# Retreive current values
		self.width = deskbar.GCONF_CLIENT.get_int(applet.gconf.GCONF_WIDTH)
		self.expand = deskbar.GCONF_CLIENT.get_bool(applet.gconf.GCONF_EXPAND)
		
		self.width_spin = self.glade.get_widget("width")
		self.width_spin.connect('value-changed', self.on_spin_width_change, applet)
		self.width_notify_id = deskbar.GCONF_CLIENT.notify_add(applet.gconf.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))

		self.width_label = self.glade.get_widget("width_label")
		self.width_units = self.glade.get_widget("width_units")

		self.expand_toggle = self.glade.get_widget("expand")
		self.expand_toggle.connect('toggled', self.on_expand_toggle, applet)
		self.expand_notify_id = deskbar.GCONF_CLIENT.notify_add(applet.gconf.GCONF_EXPAND, lambda x, y, z, a: self.on_config_expand(z.value))
		
		container = self.glade.get_widget("handlers")
		self.moduleview = ModuleListView(module_list)
		self.moduleview.connect ("row-toggled", self.on_module_toggled, module_loader)
		container.add(self.moduleview)
				
		self.sync_ui()
		
	def show_run_hide(self):
		self.dialog.show_all()
		self.dialog.run()
		self.dialog.destroy()
		
		deskbar.GCONF_CLIENT.notify_remove(self.width_notify_id)
		deskbar.GCONF_CLIENT.notify_remove(self.expand_notify_id)
		
		# Update the gconf enabled modules settings
		enabled_modules = [ctx.handler for ctx in self.module_list if ctx.enabled]
		deskbar.GCONF_CLIENT.set_list(deskbar.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING, enabled_modules)
	
	def sync_ui(self):
		self.width_spin.set_sensitive(not self.expand)
		self.width_label.set_sensitive(not self.expand)
		self.width_units.set_sensitive(not self.expand)
		self.width_spin.set_value(self.width)
		self.expand_toggle.set_property('active', self.expand)
		
	def on_config_width(self, value):
		if value != None and value.type == gconf.VALUE_INT:
			self.width = value.get_int()
			self.sync_ui()
	
	def on_config_expand(self, value):
		if value != None and value.type == gconf.VALUE_BOOL:
			self.expand = value.get_bool()
			self.sync_ui()
		
	def on_expand_toggle(self, toggle, applet):
		deskbar.GCONF_CLIENT.set_bool(applet.gconf.GCONF_EXPAND, toggle.get_property('active'))
		
	def on_spin_width_change(self, spinner, applet):
		deskbar.GCONF_CLIENT.set_int(applet.gconf.GCONF_WIDTH, int(spinner.get_value()))
	
	def on_module_toggled(self, moduleview, context, loader):
		if (context.enabled):
			loader.stop_module_async (context)
		else:
			loader.initialize_module_async (context)

def show_preferences(applet, loader, model):
	PrefsDialog(applet, loader, model).show_run_hide()
