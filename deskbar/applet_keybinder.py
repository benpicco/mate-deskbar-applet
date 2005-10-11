import gconf
import deskbar, deskbar.keybinder

def on_global_keybinding(applet):
	# We want to grab focus here
	print 'Focusing the deskbar-applet entry'
	applet.applet.request_focus(deskbar.keybinder.tomboy_keybinder_get_current_event_time())
	applet.entry.get_entry().grab_focus()

class AppletKeybinder:
	def __init__(self, applet):
		self.applet = applet

		# Set and retreive global keybinding from gconf
		self.keybinding = deskbar.GCONF_CLIENT.get_string(deskbar.GCONF_KEYBINDING)
		if self.keybinding == None:
			# This is for uninstalled cases, the real default is in the schema
			self.keybinding = "<Alt>F3"
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_KEYBINDING, lambda x, y, z, a: self.on_config_keybinding(z.value))
		self.bind()
	
	def on_config_keybinding(self, value=None):
		if value != None and value.type == gconf.VALUE_STRING:
			self.unbind()
			self.keybinding = value.get_string()
			self.bind()
			
	def bind(self):
		if self.keybinding != None:
			try:
				print 'Binding Global shortcut %s to focus the deskbar' % self.keybinding
				deskbar.keybinder.tomboy_keybinder_bind(self.keybinding, on_global_keybinding, self.applet)
			except KeyError:
				# if the requested keybinding conflicts with an existing one, a KeyError will be thrown
				pass

	def unbind(self):
		if self.keybinding != None:
			try:
				deskbar.keybinder.tomboy_keybinder_unbind(self.keybinding)
			except KeyError:
				# if the requested keybinding is not bound, a KeyError will be thrown
				pass
