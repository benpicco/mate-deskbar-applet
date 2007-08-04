import gobject
import dbus
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib

class NewStuffUpdater(gobject.GObject):
	__gsignals__ = {
		"ready" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		"error" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
		"downloadstatus" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_FLOAT]),
		"updated" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
		"new-modules-available" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		"updates-available" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}
	NEW_STUFF_SERVICE = 'org.gnome.NewStuffManager'
	NEW_STUFF_IFACE = 'org.gnome.NewStuffManager.NewStuff'
	NEW_STUFF_MANAGER_IFACE = 'org.gnome.NewStuffManager'
	NEW_STUFF_MANAGER_PATH = '/org/gnome/NewStuffManager'

	def __init__(self):
		"""
		Creates NewStuffManager and NewStuff object
		"""
		gobject.GObject.__init__(self)
		
		self._installed_modules = []
		
		self._bus = dbus.SessionBus()
		proxy_obj_manager = self._bus.get_object(self.NEW_STUFF_SERVICE, self.NEW_STUFF_MANAGER_PATH)
		stuffmanager = dbus.Interface(proxy_obj_manager, self.NEW_STUFF_MANAGER_IFACE)
		stuffmanager.GetNewStuff('deskbarapplet', reply_handler=self.__on_newstuff_ready, error_handler=self.__emit_error)
		
	def __emit_error(self, msg):
		self.emit("error", msg)

	def __on_newstuff_ready(self, path):
		proxy_obj_stuff = self._bus.get_object(self.NEW_STUFF_SERVICE, path)
		self._newstuff = dbus.Interface(proxy_obj_stuff, self.NEW_STUFF_IFACE)
		self._newstuff.connect_to_signal('Updated', lambda mod_id: self.emit("updated", mod_id))
		self._newstuff.connect_to_signal('DownloadStatus', lambda a,p: self.emit("downloadstatus", a, p))
		
		self._newstuff.Refresh(reply_handler=lambda: self.emit('ready'), error_handler=self.__emit_error)
		
	def __on_available_new_stuff(self, newstuff):
		new_modules = []
		for mod_id, name, description in newstuff:
			if not mod_id in self._installed_modules:				
				new_modules.append(( mod_id, name, description ))
		self.emit("new-modules-available", new_modules)
		self._installed_modules = []
		
	def fetch_new_modules(self, installed_modules):
		"""
		@param installed_modules: a list of module ids
		"""
		self._installed_modules = installed_modules
		self._newstuff.GetAvailableNewStuff(reply_handler=self.__on_available_new_stuff, error_handler=self.__emit_error)
		
	def fetch_updates(self, installed_modules):
		"""
		@param installed_modules: a list tuples containing module id and version
		"""
		self._newstuff.GetAvailableUpdates(installed_modules, reply_handler=lambda p: self.emit("updates-available", p), error_handler=self.__emit_error)
		
	def install_module(self, mod_id):
		self._newstuff.Update(mod_id, reply_handler=lambda: None, error_handler=self.__emit_error)
		
	def close(self):
		self._newstuff.Close(reply_handler=lambda: None, error_handler=self.__emit_error)
	