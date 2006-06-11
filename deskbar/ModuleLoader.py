import os, sys, pydoc
from os.path import abspath, expanduser, join, basename
import traceback
import gtk, gobject

import deskbar, deskbar.Handler, deskbar.Categories
from deskbar.Watcher import DirWatcher
from deskbar.ModuleContext import ModuleContext

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
		# Fired when the passed module context is loaded, that is the module's __init__ method has been called
		"module-loaded" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		# Fired when load_all has loaded every available modules
		"modules-loaded" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		# Fired when the passed module context has successfully run the initialize() method, and is thus ready to be queried
		"module-initialized" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		# Fired when the passed module context has not run initialize() without errors. The module is no usable anymore
		"module-not-initialized" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		# Fired when the passed module context has run the stop() method successfully. The module is not usable anymore
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
		
		if (dirs):
			self.dirs = [abspath(expanduser(s)) for s in dirs]
			self.build_filelist ()
			self.watcher.add(self.dirs)
		else:
			self.dirs = None
			self.filelist = []
		
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
				print >> sys.stderr, "Error reading directory %s, skipping." % d
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
			print >> sys.stderr, "Error loading the file: %s." % filename
			traceback.print_exc()
			return
		
		try:
			if (mod.HANDLERS): pass
		except AttributeError:
			print >> sys.stderr, "The file %s is not a valid module. Skipping." %filename
			print >> sys.stderr, "A module must have the variable HANDLERS defined as a dictionary."
			traceback.print_exc()
			return
		
		if mod.HANDLERS == None:
			if not hasattr(mod, "ERROR"):
				mod.ERROR = "Unspecified Reason"
				
			print >> sys.stderr, "*** The file %s decided to not load itself: %s" % (filename, mod.ERROR)
			return
		
		for handler, infos in mod.HANDLERS.items():
			if hasattr(getattr(mod, handler), "initialize") and "name" in infos:
				pass				
			else:
				print >> sys.stderr, "Class %s in file %s does not have an initialize(self) method or does not define a 'name' attribute. Skipping." % (handler, filename)
				return
			
			if "requirements" in infos:
				status, msg, callback = infos["requirements"]()
				if status == deskbar.Handler.HANDLER_IS_NOT_APPLICABLE:
					print >> sys.stderr, "***"
					print >> sys.stderr, "*** The file %s (%s) decided to not load itself: %s" % (filename, handler, msg)
					print >> sys.stderr, "***"
					return
		
		return mod
			
	def load (self, filename):
		"""Loads the given file as a module and emits a 'module-loaded' signal
		passing a corresponding ModuleContext as argument.
		"""
		mod = self.import_module (filename)
		if mod is None:
			return
		
		for handler, infos in mod.HANDLERS.items():
			print "Loading module '%s' from file %s." % (infos["name"], filename)
			mod_instance = getattr (mod, handler) ()
			context = ModuleContext (mod_instance.get_icon(), False, mod_instance, filename, handler, infos)
					
			self.emit("module-loaded", context)
		
		return context
	
	def load_all (self):
		"""Tries to load all qualified modules detected by the ModuleLoader.
		Each time a module is loaded it will emit a 'module-loaded' signal
		passing a corresponding module context.
		"""
		if self.dirs is None:
			print >> sys.stderr, "The ModuleLoader at %s has no filelist!" % str(id(self))
			print >> sys.stderr, "It was probably initialized with dirs=None."
			return
			
		for f in self.filelist:
			self.load (f)
		
		self.emit('modules-loaded')
					
	def initialize_module (self, context):
		"""
		Initializes the module in the given context. Emits a 'module-initialized' signal
		when done, passing the (now enabled) contextas argument.
		If module is already initialized, do nothing.
		"""
		if context.enabled:
			return
			
		print "Initializing %s" % context.infos["name"]
		try:
			context.module.initialize ()
			
			# Add necessary categories
			if "categories" in context.infos:
				for catname, catinfo in context.infos["categories"].items():
					deskbar.Categories.CATEGORIES[catname] = catinfo
		except Exception, msg:
			print "Error while initializing %s: %s" % (context.infos["name"],msg)
			traceback.print_exc()
			context.enabled = False
			self.emit("module-not-initialized", context)
			return
		
		context.enabled = True
		self.emit("module-initialized", context)
	
	def stop_module (self, context):
		"""
		Stops the module an sets context.enabled = False. Furthermore the context.module
		instance is also set to None. Emits a 'context-stopped' signal when done passing
		the stopped context as argument.
		"""
		
		print "Stopping %s" % context.infos["name"]
		context.module.stop ()
		
		# Remove the category installed by this module
		if "category" in context.infos:
			catname, catinfo = context.infos["category"]
			del deskbar.Categories.CATEGORIES[catname]
				
		context.enabled = False
		self.emit("module-stopped", context)
			
	def load_all_async (self):
		"""
		Same as load_all() except the loading is done in an idle mainloop call.
		"""
		gobject.idle_add(self.load_all)
		
	def initialize_module_async (self, context):
		"""
		Invokes initialize_module in an idle mainloop call.
		"""
		gobject.idle_add(self.initialize_module, context)
		
	def stop_module_async (self, context):
		"""
		Invokes stop_module in an idle mainloop call.
		"""
		gobject.idle_add(self.stop_module, context)
		
if gtk.pygtk_version < (2,8,0):
	gobject.type_register(ModuleLoader)
