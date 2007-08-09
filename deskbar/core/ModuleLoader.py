import os, pydoc
from os.path import abspath, expanduser, join, basename
import traceback
import gtk, gobject
import logging
import deskbar, deskbar.core.Categories
from deskbar.core.Watcher import DirWatcher

class ModuleLoader (gobject.GObject):
	"""An auxilary class to ModuleList. Create an instance of ModuleLoader by
	specifying the which directories to search and what extension to accept.
	The load_all() method will load all qualified modules into the ModuleList
	specified in the constructor.
	
	Most methods have a _async variant. These methods emits signals that is handled
	by the mainloop.
			
	Hint: If you pass None as the dirs argument the ModuleLoader will not search
	for modules at all. This is useful if you want to reload a single module for
	which you know the path.
	"""
	
	__gsignals__ = {
		# Fired when the passed module module is loaded, that is the module's __init__ method has been called
		"module-loaded" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		# Fired when load_all has loaded every available modules
		"modules-loaded" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		# Fired when the passed module module has successfully run the initialize() method, and is thus ready to be queried
		"module-initialized" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		# Fired when the passed module module has not run initialize() without errors. The module is no usable anymore
		"module-not-initialized" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		# Fired when the passed module module has run the stop() method successfully. The module is not usable anymore
		"module-stopped" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}
	
	def __init__ (self, dirs, extension=".py"):
		"""
		dirs: A list of directories to search. Relative pathnames and paths
			  containing ~ will be expanded. If dirs is None the 
			  ModuleLoader will not search for modules.
		extension: What extension should this ModuleLoader accept (string).
		"""
		gobject.GObject.__init__ (self)
		self.ext = extension
		self.watcher = DirWatcher()
		self.watch_id = self.watcher.connect('changed', self._on_handler_file_changed)
		self.__old_modules = []
		
		if (dirs):
			self.dirs = [abspath(expanduser(s)) for s in dirs]
			self.build_filelist ()
			self.watcher.add(self.dirs)
		else:
			self.dirs = None
			self.filelist = []

	def get_old_modules(self):
		return self.__old_modules

	def _on_handler_file_changed(self, watcher, f):
		if f in self.filelist or not self.is_module(f):
			return
		
		self.load(f)
		self.filelist.append(f)
		
	def build_filelist (self):
		"""Returns a list containing the filenames of all qualified modules.
		This method is automatically invoked by the constructor.
		"""
		res = []
		for d in self.dirs:
			try:
				if not os.path.exists(d):
					continue

				for i in [join(d, m) for m in os.listdir (d) if self.is_module(m)]:
					if basename(i) not in [basename(j) for j in res]:
						res.append(i)
			except OSError, err:
				logging.error("Error reading directory %s, skipping." % d)
				traceback.print_exc()
		
		self.filelist = res
			
	def is_module (self, filename):
		"""Tests whether the filename has the appropriate extension."""
		return (filename[-len(self.ext):] == self.ext)
				
	def import_module (self, filename):
		"""Tries to import the specified file. Returns the python module on succes.
		Primarily for internal use."""
		try:
			mod = pydoc.importfile (filename)
		except Exception:
			logging.error("Error loading the file: %s." % filename)
			error = traceback.format_exc()
			if "No module named deskbar.Handler" in error:
				self.__old_modules.append(filename)
			else:
				print error
			return
		
		try:
			if (mod.HANDLERS): pass
		except AttributeError:
			logging.error("The file %s is not a valid module. Skipping. A module must have the variable HANDLERS defined as a list." % filename)
			#traceback.print_exc()
			return
		
		if mod.HANDLERS == None:
			logging.warning("The file %s doesn't contain a HANDERLS variable" % (filename))
			return
		
		for handler in mod.HANDLERS:
			module = getattr(mod, handler)
			if hasattr(module, "initialize") and hasattr( module, "INFOS"):
				# Check that the given requirements for the handler are met
				if not getattr(module, "has_requirements" )():
					logging.warning("Class %s in file %s has missing requirements. Skipping." % (handler, filename))
					self.emit("module-not-initialized", module)
					return
			else:
				logging.error("Class %s in file %s does not have an initialize(self) method or does not define a 'INFOS' attribute. Skipping." % (handler, filename))
				return
			
		return mod
			
	def load (self, filename):
		"""Loads the given file as a module and emits a 'module-loaded' signal
		passing a corresponding ModuleContext as argument.
		"""
		mod = self.import_module (filename)
		if mod is None:
			return
		
		for handler in mod.HANDLERS:
			logging.info("Loading module '%s' from file %s." % ( getattr(mod, handler).INFOS["name"], filename))
			mod_instance = getattr (mod, handler) ()
			mod_instance.set_filename( filename )
			mod_instance.set_id( os.path.basename(filename) )
					
			self.emit("module-loaded", mod_instance)
	
	def load_all (self):
		"""Tries to load all qualified modules detected by the ModuleLoader.
		Each time a module is loaded it will emit a 'module-loaded' signal
		passing a corresponding module module.
		"""
		if self.dirs is None:
			logging.error("The ModuleLoader at %s has no filelist! It was probably initialized with dirs=None." % str(id(self)))
			return
			
		for f in self.filelist:
			self.load (f)
		
		self.emit('modules-loaded')
					
	def initialize_module (self, module):
		"""
		Initializes the module in the given module. Emits a 'module-initialized' signal
		when done, passing the (now enabled) contextas argument.
		If module is already initialized, do nothing.
		"""
		if module.is_enabled():
			return
			
		logging.info("Initializing %s" % module.INFOS["name"])
		
		try:
			module.initialize ()
			
			# Add necessary categories
			if "categories" in module.INFOS.keys():
				for catname, catinfo in module.INFOS["categories"].items():
					deskbar.core.Categories.CATEGORIES[catname] = catinfo
		except Exception, msg:
			logging.error( "Error while initializing %s: %s" % (module.INFOS["name"],msg))
			traceback.print_exc()
			module.set_enabled(False)
			self.emit("module-not-initialized", module)
			return
		
		module.set_enabled(True)
		self.emit("module-initialized", module)
	
	def stop_module (self, module):
		"""
		Stops the module an sets module.enabled = False. Furthermore the module.module
		instance is also set to None. Emits a 'module-stopped' signal when done passing
		the stopped module as argument.
		"""
		
		logging.info("Stopping %s" % module.INFOS["name"])
		module.stop ()
				
		module.set_enabled(False)
		self.emit("module-stopped", module)
			
	def load_all_async (self):
		"""
		Same as load_all() except the loading is done in an idle mainloop call.
		"""
		gobject.idle_add(self.load_all)
		
	def initialize_module_async (self, module):
		"""
		Invokes initialize_module in an idle mainloop call.
		"""
		gobject.idle_add(self.initialize_module, module)
		
	def stop_module_async (self, module):
		"""
		Invokes stop_module in an idle mainloop call.
		"""
		gobject.idle_add(self.stop_module, module)
		
if gtk.pygtk_version < (2,8,0):
	gobject.type_register(ModuleLoader)
