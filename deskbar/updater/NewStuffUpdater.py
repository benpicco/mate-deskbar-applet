"""
Updater for handlers
====================
	Currently only writes updated handlers to C{deskbar.USER_HANDLERS_DIR[0]}

	Requirements
	------------
		- handler's id == basename of handler's filename
		- handlers' infos must contain an additional version key
		- handlers must be compressed as tar.bz2 or tar.gz (the naming is <filename>.tar.bz2, whereas <filename> is the handler's main python file, e.g. leoorg.py)
		- Respository must be loaded before ModuleLoader loads the handlers (Creating an Updater instance does that for you)
		- Each handler should have its own file (highly recommended)
	
"""
from deskbar.ModuleLoader import ModuleLoader
from deskbar.ModuleList import ModuleList
from deskbar.ModuleContext import WebModuleContext
from deskbar.ui.ModuleListView import ModuleListView
import deskbar
import gobject
import gtk
import os.path
import dbus
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib

# class createXML:
# 	"""
# 	Creates XML file of installed handlers
# 	"""
# 	def __init__(self):
# 		self.root = ElementTree.Element("items")
# 		self.loader = ModuleLoader (deskbar.MODULES_DIRS)
# 		self.loader.connect ("module-loaded", self.on_module_loaded)
# 		self.loader.connect ("modules-loaded", self.on_modules_loaded)
# 		self.loader.load_all()
# 			
# 	def on_module_loaded(self, loader, context):
# 		handler = ElementTree.SubElement(self.root, "item")
# 		id = ElementTree.SubElement(handler, "id")
# 		id.text = context.handler
# 		name = ElementTree.SubElement(handler, "name")
# 		name.text = context.infos['name']
# 		description = ElementTree.SubElement(handler, "description")
# 		description.text = context.infos['description']
# 		author = ElementTree.SubElement(handler, "author")
# 		author.text = 'deskbar-applet'
# 		version = ElementTree.SubElement(handler, "version")
# 		version.text = '1.0.0'
# 		
# 	def on_modules_loaded(self, loader):
# 		tree = ElementTree.ElementTree(self.root)
# 		tree.write('/home/marduk/eclipse/workspace/deskbar-applet/deskbar/updater/updater.xml')
# 			
# 	def get_modules(self):
# 		print self._loaded_modules
# 
# 
# class ModuleList (gtk.ListStore):
#	 
#	 (ENABLED_COL,
#	 ICON_COL,
#	 MODULE_CTX_COL,
#	 CHANGELOG_COL) = range(4)
#	 
#	 def __init__ (self):
#		 gtk.ListStore.__init__ (self,
#								 bool,
#								 gtk.gdk.Pixbuf,
#								 gobject.TYPE_PYOBJECT,
#								 str)
#  
#	 def add (self, context, plugin_id, iter=None):
#		 """If iter is set this method updates the row pointed to by iter with the 
#		 values of context. 
#		 
#		 If iter is not set it will try to obtain an iter pointing
#		 to the row containg the context. If there's no such row, it will append it.
#		 """
#		 iter = self.append ([True, context.icon, context, plugin_id])
#		 return iter
#	 
#	 def get_checked_contexts(self):
#		 checked_items = []
#		 for row in self:
#			 if row[0] == True:
#				 checked_items.append( (row[2], row[3]) )
#		 return checked_items
#	 
# 
# class ModuleListView (gtk.TreeView):
#	 
#	 def __init__ (self, model):
#		 gtk.TreeView.__init__ (self, model)
#		 
#		 self.set_property("headers-visible", False)
#		 self.set_property("rules-hint", True)
#		 
#		 cell_enabled = gtk.CellRendererToggle ()
#		 cell_enabled.set_property ("activatable", True)
#		 cell_enabled.connect('toggled', self.on_row_toggled, model)
#		 self.column_enabled = gtk.TreeViewColumn ("Enabled", cell_enabled, active=model.ENABLED_COL)
# 
#		 cell_icon = gtk.CellRendererPixbuf ()
#		 self.column_icon = gtk.TreeViewColumn ("Icon", cell_icon)
#		 self.column_icon.set_attributes (cell_icon, pixbuf=model.ICON_COL)
#		 self.column_icon.set_max_width (36)
#		 
#		 cell_description = gtk.CellRendererText ()
#		 self.column_description = gtk.TreeViewColumn ("Description", cell_description)
#		 self.column_description.set_cell_data_func(cell_description, self.get_description_data)
#		 
#		 self.append_column(self.column_enabled)
#		 self.append_column(self.column_icon)
#		 self.append_column(self.column_description)
#		 
#	 def get_description_data(self, column, cell, model, iter, data=None):		
#		 context = model[iter][model.MODULE_CTX_COL]
#		 name = context.infos['name']
#		 changelog = model[iter][model.CHANGELOG_COL]
#			 
#		 cell.set_property ("markup", "<b>%s</b>\n<small><i>%s</i></small>" % (name, changelog))
#		 # <small><i>%s</i></small>\n%s
#		 
#	 def on_row_toggled(self, widget, path, model):
#		 model[path][0] = not model[path][0]
# 
# class UpdatableModuleListView(ModuleListView):
# 	def __init__(self, model):
# 		ModuleListView.__init__(self, model)
# 		
# 	def get_description_data(self, column, cell, model, iter, data=None):
# 		modctx = model[iter][model.MODULE_CTX_COL]
# 		name = modctx.infos["name"]
# 		description = ""
# 		if "description" in modctx.infos:	
# 			description = modctx.infos["description"]
# 			
# 		cell.set_property ("markup", "<b>%s</b>\n%s" % (name, description))
# 		
# class Updater( gtk.Dialog ):
# 	
# 	def __init__(self, loader):
# 		"""
# 		@param loader: ModuleLoader instane
# 		"""
# 		gtk.Dialog.__init__(self, title="Handler updater", buttons=(gtk.STOCK_REFRESH, gtk.RESPONSE_OK, gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE) )
# 		self.set_border_width(6)
# 		self.vbox.set_spacing(6)
# 		self.connect('response', self._on_response)
# 		self.connect('delete-event', gtk.main_quit)
# 		self.connect('destroy-event', gtk.main_quit)
# 		
# 		self.contexts = {}
# 		self.loader = loader
# 		
# 		self.label = gtk.Label()
# 		self.label.set_selectable(True)
# 		self.label.set_line_wrap(True)
# 		self.label.set_markup('<span size="x-large" weight="bold">Handler Updater</span>\n\nSee the list underneath for available updates.')
# 		self.label.show()
# 		self.vbox.pack_start(self.label, False)
# 		
# 		self.outdated_modulelist = ModuleList()
# 		self.loader.connect ("module-loaded", self.outdated_modulelist.update_row_cb)
# 		self.loader.connect ("module-initialized", self.outdated_modulelist.module_toggled_cb)
# 		self.loader.connect ("module-stopped", self.outdated_modulelist.module_toggled_cb)
# 		self.outdated_modulelistview = UpdatableModuleListView(self.outdated_modulelist)
# 		#self.outdated_modulelistview.set_size_request(-1, 100)
# 		self.outdated_modulelistview.show()	  
# 		
# 		scroll = gtk.ScrolledWindow()
# 		scroll.add(self.outdated_modulelistview)
# 		scroll.show()
# 		
# 		self.vbox.pack_start(scroll)
# 		
# 		self.bus = dbus.SessionBus()
# 		proxy_obj_manager = self.bus.get_object('org.gnome.NewStuffManager', '/org/gnome/NewStuffManager')
# 		stuffmanager = dbus.Interface(proxy_obj_manager, 'org.gnome.NewStuffManager')
# 		
# 		service, path = stuffmanager.GetNewStuff('deskbarapplet')
# 		
# 		proxy_obj_stuff = self.bus.get_object(service, path)
# 		self.newstuff = dbus.Interface(proxy_obj_stuff, 'org.gnome.NewStuffManager.NewStuff')
# 		#self.newstuff.connect_to_signal('Available', self.available_cb)
# 		#self.newstuff.connect_to_signal('CanUpdate', self.can_update_cb)
# 		self.newstuff.connect_to_signal('Updated', self.updated_cb)
# 		self.newstuff.GetAvailableNewStuff()
# 		return
# 		
# 	def _on_response(self, dialog, response_id):
# 		if response_id == gtk.RESPONSE_OK:
# 			self.do_update()		
# 		elif response_id == gtk.RESPONSE_CLOSE:
# 			self.close()
# 		
# 	def close(self):
# 		self.destroy()
# 		self.newstuff.Close()	
# 		self.bus.close()
# 		
# 	def available_cb(self, stuff):
# 		print "Available:", stuff
# 	
# 	def can_update_cb(self, plugin_id, changelog):
# 		print 'newstuffCanUpdate', plugin_id, changelog
# 		self.outdated_modulelist.add(self.contexts[plugin_id], changelog)
# 		
# 	def updated_cb(self, plugin_id):
# 		"""
# 		Reload handler
# 		"""
# 		filename = os.path.join(deskbar.USER_HANDLERS_DIR[0], plugin_id)
# 		self.loader.load(filename)
# 			
# 	def on_module_loaded(self, loader, context):
# 		"""
# 		Checks if an update for the previously loaded module is available
# 		
# 		If context.infos dict doesn't provide a version key it's set to the default value (1.0.0).
# 		Outdated modules will be added to the ModuleList C{self.outdated_modulelist}
# 		"""
# 		id = os.path.basename(context.filename)
# 		name = context.infos['name']
# 		version = '1.0.0'
# 		if context.infos.has_key('version'):
# 			version = context.infos['version']
# 		self.contexts[id] = context
# 		
# 		self.newstuff.GetAvailableUpdates([(id, version)])
# 		
# 	def do_update(self):
# 		"""
# 		Actually does the update
# 		
# 			- Iterate self.outdated_modulelist
# 			- Stop handler
# 			- Invoke updating handler
# 		"""
# 		for context, plugin_id in self.outdated_modulelist.get_checked_contexts():
# 			handler = context.handler			
# 			plugin_id = os.path.basename(context.filename)
# 			
# 			self.loader.stop_module(context)
# 			
# 			self.newstuff.Update(plugin_id)
# 		self.outdated_modulelist.clear()
# 						
def global_error_handler(e):
	print 'DBUS ERROR:', e
	
class NewStuffUpdater:
	def __init__(self, module_loader, module_list, web_module_list):
		self.module_list = module_list
		self.module_loader = module_loader
		self.web_module_list = web_module_list
		self.newstuff = None
		self.check_for_newstuff = True
		
		self.bus = dbus.SessionBus()
		proxy_obj_manager = self.bus.get_object('org.gnome.NewStuffManager', '/org/gnome/NewStuffManager')
		stuffmanager = dbus.Interface(proxy_obj_manager, 'org.gnome.NewStuffManager')
		stuffmanager.GetNewStuff('deskbarapplet', reply_handler=self.on_newstuff_ready, error_handler=global_error_handler)
			
	def on_newstuff_ready(self, newstuff_infos):
		service, path = newstuff_infos
		proxy_obj_stuff = self.bus.get_object(service, path)
		self.newstuff = dbus.Interface(proxy_obj_stuff, 'org.gnome.NewStuffManager.NewStuff')
		self.newstuff.connect_to_signal('Updated', self.on_newstuff_updated)
		self.newstuff.Refresh(reply_handler=self.check_new, error_handler=global_error_handler)
	
	def check_new(self):
		if self.check_for_newstuff:
			self.check_for_newstuff = False
			self.newstuff.GetAvailableNewStuff(reply_handler=self.on_available_newstuff, error_handler=global_error_handler)
	
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
		self.newstuff.Update(self.id_for_module_context(mod_ctx), reply_handler=lambda: None, error_handler=global_error_handler)
	
	def on_newstuff_updated(self, plugin_id):
		print 'Plugin updated:', plugin_id
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
		print 'Installing:', mod_ctx
		self.newstuff.Update(mod_ctx.id, reply_handler=lambda: None, error_handler=global_error_handler)
		mod_ctx.installing = True
		self.web_module_list.module_changed(mod_ctx)
		self.check_for_newstuff = True
	
	def close(self):
		self.newstuff.Close(reply_handler=lambda: None, error_handler=global_error_handler)
		
# if __name__ == '__main__':
# 	#createXML()
# 	loader = ModuleLoader (deskbar.MODULES_DIRS)
# 	updater = Updater(loader)
# 	loader.connect ("module-loaded", updater.on_module_loaded)
# 	loader.load_all()
# 	updater.run()
# 	gtk.main()
