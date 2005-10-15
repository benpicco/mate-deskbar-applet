import gtk
import gobject
import os
import sys
import pydoc
from os.path import join, basename, normpath, abspath
from os.path import split, expanduser, exists, isfile, dirname
from threading import Thread
import Queue

class ModuleContext:
	"""A generic wrapper for any object stored in a ModuleList.
	settings is unused at the moment.
	"""	
	
	def __init__ (self, icon, enabled, module, settings, filename, name, exported_class):
		"""The icon should be a gtk.gdk.Pixbuf"""
		self.icon = icon
		self.enabled = enabled
		self.module = module
		self.settings = settings
		self.filename = filename
		self.name = name
		self.exported_class = exported_class
		

class ModuleListIter : 
	"""An iter type to iterate over the of *enabled* module contexts in a ModuleList object.
	This object is (typically) not used directly. See the documentation for ModuleList.
			
	For documentation on iters see: http://docs.python.org/lib/typeiter.html
	"""
	def __init__ (self, owner):
		"""Constructor for ModuleListIter.
		owner is the ModuleList which this iterator will iterate over.
		"""
		self.owner = owner
		self.owner_iter = owner.get_iter_first ()
		
	def __iter__ (self):
		return self
		
	def next (self):
		"""Return the next *enabled* module in the ModuleList."""
		try:
			mod = self.owner.get_context_from_iter (self.owner_iter)
			self.owner_iter = self.owner.iter_next (self.owner_iter)
			if not mod.enabled: 
				return self.next()
		except TypeError:
			raise StopIteration
		return mod

class ModuleList (gtk.ListStore):
	"""Mostly generic implementation of a dynamic module handler.
	Use a ModuleListView object to display the contents of a ModuleList. 
	You can iterate over the list with
	
		for modctx in modlist:
			do_something (modctx)
	
	From this perspective the ModuleList stores ModuleContexts (it actually doesnt),
	so to utilize the modules you'll have to acces modctx.module.
	
	Note that the gtk.ListView extends the following classes:
		gobject.GObject, gtk.TreeModel, gtk.TreeDragSource, gtk.TreeDragDest,
		gtk.TreeSortable
	More documentation:
		http://www.pygtk.org/pygtk2reference/class-gtkliststore.html
	Note that
	"""
	
	ICON_COL = 0
	ENABLED_COL = 1
	MODULE_COL = 2
	SETTINGS_COL = 3
	FILENAME_COL = 4
	NAME_COL = 5
	EXP_CLASS_COL = 6
	
	def __init__ (self):
		gtk.ListStore.__init__ (self, 	gtk.gdk.Pixbuf, 
						bool, 
						gobject.TYPE_PYOBJECT, 
						gobject.TYPE_PYOBJECT, 
						gobject.TYPE_STRING, 
						gobject.TYPE_STRING,
						gobject.TYPE_STRING)
		
	def __iter__ (self):
		return ModuleListIter (self)
	
	def add (self, context):
		"""Appends the module context to the list."""
		self.update_row (context, iter)


	def get_iter_from_context (self, modctx):
		"""Returns a gtk.TreeIter pointing to the row containing the filename
		modctx.filename. This should be uniqualy determined by the context.
		
		If the filename is not found return None.
		
		INVARIANT: ModuleContexts are uniquely determined by their .filename
		"""
	
		iter = self.get_iter_first ()
		while (iter is not None):
			if self.get_value (iter, self.FILENAME_COL) == modctx.filename:
				break
			iter = self.iter_next (iter)
		return iter

	def get_context_from_iter (self, iter):
		"""Return a ModuleContext representing the row pointed to by iter."""
		modctx = ModuleContext (	self.get_value (iter, self.ICON_COL), 
						self.get_value (iter, self.ENABLED_COL), 
						self.get_value (iter, self.MODULE_COL), 
						self.get_value (iter, self.SETTINGS_COL), 
						self.get_value (iter, self.FILENAME_COL), 
						self.get_value (iter, self.NAME_COL), 
						self.get_value (iter, self.EXP_CLASS_COL))
		return modctx

	def update_row (self, context, iter=None):
		"""If iter is set this method updates the row pointed to by iter with the 
		values of context. 
		
		If iter is not set it will try to obtain an iter pointing
		to the row containg context.filename. If there's no such row, it will append it.
		"""
		
		if (iter is None):
			iter = self.get_iter_from_context (context)
		if (iter is None):
			iter = self.append ()
		
		self.set_value(iter, self.ICON_COL, context.icon)
		self.set_value(iter, self.ENABLED_COL, context.enabled)
		self.set_value(iter, self.MODULE_COL, context.module)
		self.set_value(iter, self.SETTINGS_COL, context.settings)
		self.set_value(iter, self.FILENAME_COL, context.filename)
		self.set_value(iter, self.NAME_COL, "<b>%s</b>\n%s" % context.name)
		self.set_value(iter, self.EXP_CLASS_COL, context.exported_class)
		
	def update_row_cb (self, sender, context, iter=None):
		"""
		Callback for updating the row containing context.
		If iter is set the row to which it points to will be
		updated with the context.
		"""
		self.update_row (context, iter)
	
	def module_toggled_cb (self, sender, context):
		"""
		Callback to toggle the enabled state of the context.
		"""
		self.set_value(self.get_iter_from_context (context), self.ENABLED_COL, context.enabled)
		
class ModuleListView (gtk.TreeView):
	"""A versatile list widget that displays the contents of a ModuleList.
	model: ModuleList
	columns: List specifying columns to display. See ModuleList for options.
	
	Example:
		model = ModuleList ()
		view = ModuleListView (model, [ModuleList.NAME_COL, ModuleList.ENABLED_COL])
	
	This will construct a list showing the module names and a checkbox on whether or
	not they are enabled.
	"""
	
	__gsignals__ = {
		"row-toggled" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
	}
	
	def __init__ (self, model, columns):
		gtk.TreeView.__init__ (self, model)
		
		if (model.ICON_COL in columns):
			cell_icon = gtk.CellRendererPixbuf ()
			self.column_icon = gtk.TreeViewColumn ("Icon", cell_icon)
			self.column_icon.set_attributes (cell_icon, pixbuf=model.ICON_COL)
			self.column_icon.set_max_width (36)
		
		if (model.ENABLED_COL in columns):
			cell_enabled = gtk.CellRendererToggle ()
			cell_enabled.set_property ("activatable", True)
			cell_enabled.connect('toggled', self.emit_row_toggled, model)
			self.column_enabled = gtk.TreeViewColumn ("Enabled", cell_enabled, active=model.ENABLED_COL)
	
		if (model.NAME_COL in columns):
			cell_module_name = gtk.CellRendererText ()
			self.column_module_name = gtk.TreeViewColumn ("Module", cell_module_name, markup=model.NAME_COL)
		
		if (model.FILENAME_COL in columns):
			cell_filename = gtk.CellRendererText ()
			self.column_filename = gtk.TreeViewColumn ("Filename", cell_filename, markup=model.FILENAME_COL)
		
		for col in columns:
			if col==model.ICON_COL : self.append_column(self.column_icon)
			if col==model.ENABLED_COL : self.append_column(self.column_enabled)
			if col==model.NAME_COL : self.append_column(self.column_module_name)
			if col==model.FILENAME_COL : self.append_column(self.column_filename)
		
		self.set_property("headers-visible", False)
		self.set_reorderable(True)
			
	def emit_row_toggled (self, cell, path, model):
		"""Callback for the toggle buttons in the ModuleList.ENABLED_COL.
		Emits a 'row-toggled' signal passing the context in the row as argument."""
		self.emit ("row-toggled", model.get_context_from_iter (model.get_iter(path)))
		
class ModuleLoader (gobject.GObject):
	"""An auxilary class to ModuleList. Create an instance of ModuleLoader by
	specifying the which directories to search and what extension to accept.
	The load_all() method will load all qualified modules into the ModuleList
	specified in the constructor.
	
	Most methods have a _async variant. These methods emits signals that is handled
	by the *main* thread. This ensures that locking mechanisms are unlikely to be 
	needed.
		
	Hint: If you pass None as the dirs argument the ModuleLoader will not search
	for modules at all. This is useful if you want to reload a single module for
	which you know the path.
	
	Important: Remember to do gtk.gdk.threads_init() or gobject.threads_init() before
	using any of the _async methods or else it WON'T WORK. Caveat emptor!
	"""
	
	__gsignals__ = {
		"module-loaded" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		"module-initialized" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		"module-stopped" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
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
		if (dirs):
			self.dirs = map (lambda s: abspath(expanduser(s)), dirs)
			self.filelist = self.build_filelist ()
		else:
			self.dirs = None
			self.filelist = []
		
		self.task_queue = Queue.Queue(0)
		thread = Thread(None, self.consume_queue)
		# WE don't want the queue thread to prevent us from exiting
		thread.setDaemon(True)
		thread.start()
	
	def consume_queue(self):
		while True:
			task = self.task_queue.get()
			try:
				task ()
			except Exception, msg:
				print 'Error:consume_queue:Got an error while processing item:', msg
				
	def build_filelist (self):
		"""Returns a list containing the filenames of all qualified modules.
		This method is automatically invoked by the constructor.
		"""
		res = []
		for d in self.dirs:
			try:
				tmp = filter (self.is_module, os.listdir (d))
				res = res + map (lambda s: d+"/"+s, tmp)
			except OSError, err:
				print >> sys.stderr, "Error reading directory %s, skipping." % d
				print >> sys.stderr, str(err)
		return res
			
	def is_module (self, filename):
		"""Tests whether the filename has the appropriate extension."""
		return (filename[-len(self.ext):] == self.ext)
				
	def import_module (self, filename):
		"""Tries to import the specified file. Returns the python module on succes.
		Primarily for internal use."""
		try:
			mod = pydoc.importfile (filename)
		except IOError, err:
			print >> sys.stderr, "Error loading the file: %s\nThe file probably doesn't exist." % filename
			print >> sys.stderr, str(err)
			return
		except pydoc.ErrorDuringImport, err:
			print >> sys.stderr, "Unknown error loading the file: %s." % filename
			print >> sys.stderr, str(err)
			return
		
		try:
			if (mod.EXPORTED_CLASS): pass
			if (mod.NAME): pass
		except AttributeError:
			print >> sys.stderr, "The file %s is not a valid module. Skipping." %filename
			print >> sys.stderr, "A module must the string constants EXPORTED_CLASS and NAME."
			return
		
		if mod.EXPORTED_CLASS == None:
			print >> sys.stderr, "***"
			print >> sys.stderr, "*** The file %s decided to not load itself: %s" % (filename, mod.NAME)
			print >> sys.stderr, "***"
			return
		
		if hasattr(getattr(mod, mod.EXPORTED_CLASS), "initialize") or hasattr(getattr(mod, mod.EXPORTED_CLASS), "initialize_safe"):
			pass
		else:
			print >> sys.stderr, "Class %s in file %s does not have an initialize(self) method. Skipping." % (mod.EXPORTED_CLASS, filename)
			return
		
		return mod
	
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
	
	def load (self, filename):
		"""Loads the given file as a module and emits a 'module-loaded' signal
		passing a corresponding ModuleContext as argument. 
		
		Returns the context as added to the list.
		"""
		mod = self.import_module (filename)
		if mod is None:
			return
		
		print "Loading module '%s' from file %s." % (mod.NAME, filename)
		mod_instance = getattr (mod, mod.EXPORTED_CLASS) ()
		context = ModuleContext (mod_instance.get_icon(), False, mod_instance, 
					None, filename, mod.NAME, mod.EXPORTED_CLASS)
					
		gobject.idle_add (self.emit, "module-loaded", context)
		
		return context
							
	def initialize_module (self, context):
		"""
		Initializes the module in the given context. Emits a 'module-initialized' signal
		when done, passing the (now enabled) contextas argument.
		"""
		
		print "Initializing %r" % (context.name,)
		
		# First we check if the module must be called in a thread safe way
		if hasattr(context.module, "initialize_safe"):
			gtk.threads_enter ()
			try:
				context.module.initialize_safe()
			finally:
				gtk.threads_leave ()
		# Else we use the simple non-locked method
		else:
			context.module.initialize ()
		
		context.enabled = True
		gobject.idle_add (self.emit, "module-initialized", context)
	
	def stop_module (self, context):
		"""
		Stops the module an sets context.enabled = False. Furthermore the context.module
		instance is also set to None. Emits a 'context-stopped' signal when done passing
		the stopped context as argument.
		"""
		
		print "Stopping %r" % (context.name,)
		context.module.stop ()
		
		context.enabled = False
		context.module = None
		gobject.idle_add (self.emit, "module-stopped", context)
			
	def load_all_async (self):
		"""
		Same as load_all() except the loading is done in a separate thread.
		"""
		self.task_queue.put(self.load_all)
	
	def load_async (self, filename):
		"""
		Invokes load() in a new thread.
		"""
		self.task_queue.put( lambda: self.load(filename) )
		
	def initialize_module_async (self, context):
		"""
		Invokes initialize_module in a new thread.
		"""
		self.task_queue.put( lambda: self.initialize_module(context) )
		
	def stop_module_async (self, context):
		"""
		Invokes stop_module in a new thread.
		"""
		self.task_queue.put( lambda: self.stop_module(context) )

def toggle_module (sender, context, ml):
	"""Test function"""
	if (context.enabled):
		ml.stop_module_async (context)
	else:
		ml.initialize_module_async (context)

if __name__ == "__main__":

	"""A test suite for the Module* classes. Run from top level dir,
	ie. from deskbar-applet/ run 'python deskbar/module_list.py'."""
	
	gtk.threads_init()
	
	name = join(dirname(__file__), '..')
	print 'Changing PYTHONPATH'
	sys.path.insert(0, abspath(name))
    
	l = ModuleList ()    
	ml = ModuleLoader (["deskbar/handlers"], ".py")
	ml.connect ("module-loaded", l.update_row_cb)
	ml.connect ("module-initialized", l.module_toggled_cb)
	ml.connect ("module-stopped", l.module_toggled_cb)
	
	# Load all or just the directories handler. Uncomment to your liking
	ml.load_all_async ()
	#ml.load_async (abspath(expanduser("deskbar/testmod.py")))


	lw = ModuleListView (l, [ModuleList.FILENAME_COL, ModuleList.NAME_COL, ModuleList.ENABLED_COL])
	lw.connect ("row-toggled", toggle_module, ml)
	
	win = gtk.Window ()
	win.connect ("destroy", gtk.main_quit)
	win.add (lw)
	win.show ()
	lw.show ()
	
	gtk.threads_enter()
	gtk.main ()
	gtk.threads_leave()
