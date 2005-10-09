from os.path import join
import gtk, gtk.glade, gobject, gconf
import deskbar


class PrefsDialog:
	def __init__(self):
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
		
		self.sync_ui()
	
	def show_run_hide(self):
		self.dialog.show_all()
		self.dialog.run()
		self.dialog.destroy()
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

def show_preferences():
	PrefsDialog().show_run_hide()
