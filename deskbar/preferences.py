from os.path import join
import gtk, gtk.glade, gobject, gconf
import deskbar
from deskbar.module_list import ModuleListView

class PrefsDialog:
	def __init__(self, module_loader, module_list):
		self.module_list = module_list
		self.glade = gtk.glade.XML(join(deskbar.SHARED_DATA_DIR, "prefs-dialog.glade"))

		self.dialog = self.glade.get_widget("preferences")
		try:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(join(deskbar.ART_DATA_DIR, "deskbar-applet-small.png"), gtk.ICON_SIZE_DIALOG, gtk.ICON_SIZE_DIALOG)
			self.dialog.set_icon(pixbuf)
		except gobject.GError, msg:
			print 'Error:PrefsDialog:', msg

		# Retreive current values
		self.width = deskbar.GCONF_CLIENT.get_int(deskbar.GCONF_WIDTH)
		self.expand = deskbar.GCONF_CLIENT.get_bool(deskbar.GCONF_EXPAND)
		
		self.width_spin = self.glade.get_widget("width")
		self.width_spin.connect('value-changed', self.on_spin_width_change)
		self.width_notify_id = deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))

		self.expand_toggle = self.glade.get_widget("expand")
		self.expand_toggle.connect('toggled', self.on_expand_toggle)
		self.expand_notify_id = deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_EXPAND, lambda x, y, z, a: self.on_config_expand(z.value))
			
		container = self.glade.get_widget("handlers")
		self.moduleview = ModuleListView(module_list)
		self.moduleview.connect ("row-toggled", self.on_module_toggled, module_loader)
		container.add(self.moduleview)
				
		self.sync_ui()
		
	def show_run_hide(self):
		self.dialog.show_all()
		self.dialog.run()
		self.dialog.destroy()
		
		# Update the gconf enabled modules settings, and recompute priorities
		enabled_modules = [ctx.handler for ctx in self.module_list if ctx.enabled]
		update_modules_priority(self.module_list, enabled_modules)
		deskbar.GCONF_CLIENT.set_list(deskbar.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING, enabled_modules)
		
		deskbar.GCONF_CLIENT.notify_remove(self.width_notify_id)
		deskbar.GCONF_CLIENT.notify_remove(self.expand_notify_id)
	
	def sync_ui(self):
		self.width_spin.set_sensitive(not self.expand)
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
	
	def on_expand_toggle(self, toggle):
		deskbar.GCONF_CLIENT.set_bool(deskbar.GCONF_EXPAND, toggle.get_property('active'))
		
	def on_spin_width_change(self, spinner):
		deskbar.GCONF_CLIENT.set_int(deskbar.GCONF_WIDTH, int(spinner.get_value()))
	
	def on_module_toggled(self, moduleview, context, loader):
		if (context.enabled):
			loader.stop_module_async (context)
		else:
			loader.initialize_module_async (context)

def show_preferences(loader, model):
	PrefsDialog(loader, model).show_run_hide()

def update_modules_priority(module_list, enabled_modules, callback=None):
	"""
	module_list is a module_loader.ModuleList() with loaded modules
	enabled_modules is a list of exported classnames.
	
	Update the module priority present in both module_list and enabled_modules according
	to the ordering of enabled_modules. Optionally calls callback when != None on each
	module context, in the correct order (from important to less important)
	"""
	# Compute the highest priority
	high_prio = (len(enabled_modules)-1)*100
	
	# Now we enable each gconf-enabled handler, and set it's priority according to gconf ordering
	for i, mod in enumerate(enabled_modules):
		modctx = [modctx for modctx in module_list if modctx.handler == mod]
		if len(modctx) != 1:
			# We have a gconf handler not on disk anymore..
			continue
			
		modctx = modctx[0]
		modctx.module.set_priority(high_prio-i*100)
		
		# Call the optional callback
		if callback != None:
			callback(modctx)
