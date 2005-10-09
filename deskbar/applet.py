import os, time
import deskbar, deskbar.deskbarentry, deskbar.about, deskbar.preferences, deskbar.applet_keybinder
# WARNING: Load gnome.ui before gnomeapplet or we have a nasty warning.
import gnome.ui
import gnomeapplet, gtk, gtk.gdk, gconf

class DeskbarApplet:
	def __init__(self, applet):
		self.applet = applet
						
		self.entry = deskbar.deskbarentry.DeskbarEntry()
		self.entry.get_evbox().connect("button-press-event", lambda box, event: self.applet.emit("button-press-event", event))
		self.entry.get_entry().connect("button-press-event", self.on_entry_button_press)

		self.keybinder = deskbar.applet_keybinder.AppletKeybinder(self)

		# Set and retreive entry width from gconf
		self.config_width = deskbar.GCONF_CLIENT.get_int(deskbar.GCONF_WIDTH)
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))
		self.config_expand = deskbar.GCONF_CLIENT.get_bool(deskbar.GCONF_EXPAND)
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_EXPAND, lambda x, y, z, a: self.on_config_expand(z.value))
				
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.applet.add(self.entry)
		self.applet.connect("button-press-event", self.on_applet_button_press)
		self.applet.connect('destroy', lambda x: self.keybinder.unbind())
		self.applet.setup_menu_from_file (
			None, os.path.join(deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml"),
			None, [("About", self.on_about), ("Prefs", self.on_preferences)])

		self.applet.show_all()
		self.sync_applet_size()
		
		self.entry.get_entry().grab_focus()
		
	def on_about(self, component, verb):
		deskbar.about.show_about()
	
	def on_preferences(self, component, verb):
		deskbar.preferences.show_preferences()

	def on_config_width(self, value=None):
		if value != None and value.type == gconf.VALUE_INT:
			self.config_width = value.get_int()
			self.sync_applet_size()
	
	def on_config_expand(self, value=None):
		if value != None and value.type == gconf.VALUE_BOOL:
			self.config_expand = value.get_bool()
			self.sync_applet_size()
	
	def sync_applet_size(self):
		if self.config_expand:
			self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR | gnomeapplet.EXPAND_MAJOR)
		else:
			self.applet.set_applet_flags(0)
			
			# Set the new size of the entry
			self.applet.set_size_request(self.config_width, -1)
			
	def on_applet_button_press(self, widget, event):
		self.applet.request_focus(long(event.time))
		# Left-Mouse-Button should focus the GtkEntry widget (for Fitt's Law
		# - so that a click on applet border on edge of screen activates the
		# most important widget).
		if event.button == 1:
			self.entry.get_entry().select_region(0, -1)
			self.entry.get_entry().grab_focus()
			return True
		
		return False
		
	def on_entry_button_press(self, widget, event):
		self.applet.request_focus(long(event.time))
		return False

	
