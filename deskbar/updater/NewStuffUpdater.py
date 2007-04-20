from gettext import gettext as _
from deskbar.ModuleLoader import ModuleLoader
from deskbar.ModuleList import ModuleList
from deskbar.ModuleContext import WebModuleContext
from deskbar.ui.ModuleListView import ModuleListView
from deskbar.updater.ProgressbarDialog import ProgressbarDialog
from deskbar.updater.ErrorDialog import ErrorDialog
import deskbar
import gobject
import gtk
import os.path
import dbus
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib


def global_error_handler(e):
	#print 'DBUS ERROR:', e
	ed = ErrorDialog(None, e)
	ed.run()
	ed.destroy()
		
	
class NewStuffUpdater(gobject.GObject):
	__gsignals__ = {
		"ready" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		"connection-failed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}
	NEW_STUFF_SERVICE = 'org.gnome.NewStuffManager'
	NEW_STUFF_IFACE = 'org.gnome.NewStuffManager.NewStuff'
	NEW_STUFF_MANAGER_IFACE = 'org.gnome.NewStuffManager'
	NEW_STUFF_MANAGER_PATH = '/org/gnome/NewStuffManager'

	def __init__(self, parent, module_loader, module_list, web_module_list):
		"""
		Creates NewStuffManager and NewStuff object
		"""
		gobject.GObject.__init__(self)
		self.parent = parent
		self.module_list = module_list
		self.module_loader = module_loader
		self.web_module_list = web_module_list
		self.newstuff = None
		self.check_for_newstuff = True
		self.progressbar_pulse = False
		
		self.bus = dbus.SessionBus()
		proxy_obj_manager = self.bus.get_object(self.NEW_STUFF_SERVICE, self.NEW_STUFF_MANAGER_PATH)
		stuffmanager = dbus.Interface(proxy_obj_manager, self.NEW_STUFF_MANAGER_IFACE)
		stuffmanager.GetNewStuff('deskbarapplet', reply_handler=self.on_newstuff_ready, error_handler=global_error_handler)
			
	def on_newstuff_ready(self, newstuff_infos):
		"""
		Sets up the NewStuff object
		
		Called by L{self.__init__}
		"""
		path = newstuff_infos
		proxy_obj_stuff = self.bus.get_object(self.NEW_STUFF_SERVICE, path)
		self.newstuff = dbus.Interface(proxy_obj_stuff, self.NEW_STUFF_IFACE)
		self.newstuff.connect_to_signal('Updated', self.on_newstuff_updated)
		self.newstuff.connect_to_signal('DownloadStatus', self.on_newstuff_downloadstatus)
		self.newstuff.Refresh(reply_handler=lambda: self.emit('ready'), error_handler=lambda e: self.emit('connection-failed', e))
	
	def check_new(self):
		"""
		Fetches all the available handlers in the repository
		
		Called by L{self.on_newstuff_ready}
		"""
		if self.check_for_newstuff:
			self.check_for_newstuff = False
			self.newstuff.GetAvailableNewStuff(reply_handler=self.on_available_newstuff, error_handler=global_error_handler)
	
	def on_newstuff_downloadstatus(self, action, progress):
		self.progressdialog.set_current_operation(action)
		if progress == -1.0:
			if not self.progressbar_pulse:
				self.progressbar_pulse = True
				self.progressdialog.set_fraction(0.2)
			self.progressdialog.pulse()
		else:
			if self.progressbar_pulse:
				self.progressbar_pulse = False
			self.progressdialog.set_fraction(progress)
	
	def on_available_newstuff(self, newstuff):
		self.web_module_list.clear()
		print 'NewStuff Available:', newstuff
		for id, name, description in newstuff:
			mod = self.module_context_for_id(id)
			if mod != None:
				continue
			
			self.web_module_list.add(
				WebModuleContext(
					id, name, description))
			
	def check_all(self):
		plugins = [(self.id_for_module_context(context), context.version) for context in self.module_list]
		print 'Checking for updates:', plugins
		self.newstuff.GetAvailableUpdates(plugins, reply_handler=self.on_available_updates, error_handler=global_error_handler)
	
	def id_for_module_context(self, context):
		return os.path.basename(context.filename)
		
	def module_context_for_id(self, id):
		for mod in self.module_list:
			if self.id_for_module_context(mod) == id:
				return mod
				
	def on_available_updates(self, plugins):
		all_plugins = [self.id_for_module_context(context) for context in self.module_list]
		
		for id, changelog in plugins:
			print 'Available update:', id, changelog
			mod = self.module_context_for_id(id)
			mod.update_infos = (True, changelog)
			self.module_list.module_changed(mod)
			if id in all_plugins:
				all_plugins.remove(id)
		
		for id in all_plugins:
			mod = self.module_context_for_id(id)
			mod.update_infos = (False, None)
			self.module_list.module_changed(mod)
				
	def update(self, mod_ctx):
		print 'Updating:', self.id_for_module_context(mod_ctx)
		self.progressdialog = ProgressbarDialog(self.parent)
		self.progressdialog.set_text(_('Updating %s') % mod_ctx.infos['name'], _('The update is being downloaded from the internet. Please wait until the update is complete'))		
		self.progressdialog.run_nonblocked()
		self.newstuff.Update(self.id_for_module_context(mod_ctx), reply_handler=lambda: None, error_handler=global_error_handler)
	
	def on_newstuff_updated(self, plugin_id):
		print 'Plugin updated:', plugin_id
		self.progressdialog.destroy()
		mod_ctx = self.module_context_for_id(plugin_id)
		print mod_ctx
		if mod_ctx != None:
			# The plugin is already loaded
			self.module_loader.stop_module(mod_ctx)
			self.module_list.remove_module(mod_ctx)
		
		print 'Loading plugin', os.path.join(deskbar.USER_HANDLERS_DIR[0], plugin_id)
		self.module_loader.build_filelist()
		mod_ctx = self.module_loader.load(os.path.join(deskbar.USER_HANDLERS_DIR[0], plugin_id))
		print 'New Module Loaded:', mod_ctx

		self.check_new()
		
		
	def install(self, mod_ctx):
		print 'Installing:', mod_ctx.id
		self.progressdialog = ProgressbarDialog(self.parent)
		self.progressdialog.set_text(_('Installing %s') % mod_ctx.name, _('The handler is being downloaded from the internet. Please wait until the installation is complete'))
		self.progressdialog.set_current_operation(_('Downloading'))
		self.progressdialog.run_nonblocked()
		
		self.newstuff.Update(mod_ctx.id, reply_handler=lambda: None, error_handler=global_error_handler)
		mod_ctx.installing = True
		self.web_module_list.module_changed(mod_ctx)
		self.check_for_newstuff = True
	
	def close(self):
		# Check if we close the prefs before having a ready signal.
		if self.newstuff != None:
			self.newstuff.Close(reply_handler=lambda: None, error_handler=global_error_handler)
