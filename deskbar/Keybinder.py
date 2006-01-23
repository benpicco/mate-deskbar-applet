import gtk, gobject, gconf
import deskbar, deskbar.keybinder

class Keybinder(gobject.GObject):
	__gsignals__ = {
		"activated" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_ULONG]),
		# When the keybinding changes, passes a boolean indicating wether the keybinding is successful
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
	}
	def __init__(self):
		gobject.GObject.__init__(self)
		
		self.bound = False
		
		# Set and retreive global keybinding from gconf
		self.keybinding = deskbar.GCONF_CLIENT.get_string(deskbar.GCONF_KEYBINDING)
		if self.keybinding == None:
			# This is for uninstalled cases, the real default is in the schema
			self.keybinding = "<Alt>F3"
		deskbar.GCONF_CLIENT.notify_add(deskbar.GCONF_KEYBINDING, lambda x, y, z, a: self.on_config_keybinding(z.value))
		self.bind()
		
	def on_config_keybinding(self, value=None):
		if value != None and value.type == gconf.VALUE_STRING:
			self.keybinding = value.get_string()
			self.bind()
	
	def on_keyboard_shortcut(self):
		self.emit('activated', deskbar.keybinder.tomboy_keybinder_get_current_event_time())
		
	def bind(self):
		if self.bound:
			self.unbind()
			
		try:
			print 'Binding Global shortcut %s to focus the deskbar' % self.keybinding
			deskbar.keybinder.tomboy_keybinder_bind(self.keybinding, self.on_keyboard_shortcut)
			self.bound = True
		except KeyError:
			# if the requested keybinding conflicts with an existing one, a KeyError will be thrown
			self.bound = False
		
		self.emit('changed', self.bound)
					
	def unbind(self):
		try:
			deskbar.keybinder.tomboy_keybinder_unbind(self.keybinding)
			self.bound = False
		except KeyError:
			# if the requested keybinding is not bound, a KeyError will be thrown
			pass

if gtk.pygtk_version < (2,8,0):
	gobject.type_register(Keybinder)

keybinder = Keybinder()
def get_deskbar_keybinder():
	return keybinder
