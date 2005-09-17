from os.path import join
import gtk, gtk.glade, gobject, gconf
import deskbar


class PrefsDialog:
	def __init__(self):
		self.glade = gtk.glade.XML(join(deskbar.SHARED_DATA_DIR, "prefs-dialog.glade"))

		self.dialog = self.glade.get_widget("preferences")
		try:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(join(deskbar.ART_DATA_DIR, "deskbar-applet-small.png"), -1, 16)
			self.dialog.set_icon(pixbuf)
		except gobject.GError, msg:
			print 'Error:PrefsDialog:', msg
		
		self.width_spin = self.glade.get_widget("width")
		self.width_spin.set_value(deskbar.GCONF_CLIENT.get_int(deskbar.GCONF_WIDTH))
		self.width_spin.connect('value-changed', self.on_spin_width_change)
		self.width_notify_id = deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))
	
	def show_run_hide(self):
		self.dialog.show_all()
		self.dialog.run()
		self.dialog.destroy()
		deskbar.GCONF_CLIENT.notify_remove(self.width_notify_id)
	
	def on_config_width(self, value):
		if value != None and value.type == gconf.VALUE_INT:
			self.width_spin.set_value(value.get_int())
			
	def on_spin_width_change(self, spinner):
		deskbar.GCONF_CLIENT.set_int(deskbar.GCONF_WIDTH, spinner.get_value())

def show_preferences():
	PrefsDialog().show_run_hide()
