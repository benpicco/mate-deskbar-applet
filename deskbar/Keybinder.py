import gtk, gobject, gconf
import deskbar, deskbar.keybinder

class Keybinder(gobject.GObject):
	__gsignals__ = {
		"activated" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		# When the keybinding changes, passes a boolean indicating wether the keybinding is successful
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
	}
	def __init__(self, gconf_key):
		gobject.GObject.__init__(self)

		# Set and retreive global keybinding from gconf
		self.keybinding = deskbar.GCONF_CLIENT.get_string(gconf_key)
		if self.keybinding == None:
			# This is for uninstalled cases, the real default is in the schema
			self.keybinding = "<Alt>F3"
		deskbar.GCONF_CLIENT.notify_add(gconf_key, lambda x, y, z, a: self.on_config_keybinding(z.value))
		self.bind()
	
	def on_config_keybinding(self, value=None):
		if value != None and value.type == gconf.VALUE_STRING:
			v = value.get_string()
			if self.keybinding != v:
				self.unbind()
				self.keybinding = v
				self.bind()
	
	def on_keyboard_shortcut(self):
		self.emit('activated')
		
	def bind(self):
		if self.keybinding != None:
			try:
				print 'Binding Global shortcut %s to focus the deskbar' % self.keybinding
				deskbar.keybinder.tomboy_keybinder_bind(self.keybinding, self.on_keyboard_shortcut, self)
				self.emit('changed', True)
			except KeyError:
				# if the requested keybinding conflicts with an existing one, a KeyError will be thrown
				self.emit('changed', False)
				pass

	def unbind(self):
		if self.keybinding != None:
			try:
				deskbar.keybinder.tomboy_keybinder_unbind(self.keybinding)
			except KeyError:
				# if the requested keybinding is not bound, a KeyError will be thrown
				pass
			
			self.emit('changed', False)

if gtk.pygtk_version < (2,8,0):
	gobject.type_register(Keybinder)
