import os, time
import deskbar, deskbar.deskbarentry, deskbar.about, deskbar.preferences
import gnomeapplet, gtk, gtk.gdk, gconf

class DeskbarApplet:
	def __init__(self, applet):
		self.applet = applet
						
		self.entry = deskbar.deskbarentry.DeskbarEntry()
		self.entry.get_evbox().connect("button-press-event", lambda box, event: self.applet.emit("button-press-event", event))
		self.entry.get_entry().connect("button-press-event", self.on_entry_button_press)
		
		# Set and retreive entry width from gconf
		self.config_width = deskbar.GCONF_CLIENT.get_int(deskbar.GCONF_WIDTH)
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_WIDTH, lambda x, y, z, a: self.on_config_width(z.value))
		self.on_config_width()
						
		self.applet.set_flags(gtk.CAN_FOCUS)
		self.applet.add(self.entry)
		self.applet.set_applet_flags(gnomeapplet.EXPAND_MINOR | gnomeapplet.EXPAND_MAJOR)
		self.applet.connect("button-press-event", self.on_applet_button_press)
		self.applet.setup_menu_from_file (
			None, os.path.join(deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml"),
			None, [("About", self.on_about), ("Prefs", self.on_preferences)])

		self.applet.show_all()
		self.applet.request_focus(long(time.time()))
		
	def on_about(self, component, verb):
		deskbar.about.show_about()
	
	def on_preferences(self, component, verb):
		deskbar.preferences.show_preferences()

	# TODO - remove this (unused) method entirely
	def on_config_width(self, value=None):
		if value != None and value.type == gconf.VALUE_INT:
			self.config_width = value.get_int()
		
		# Set the new size of the entry
		# Commented out by Nigel Tao - the less preferences the better.
		#entry = self.entry.get_entry()
		#entry.set_size_request(200, entry.size_request()[1])

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
