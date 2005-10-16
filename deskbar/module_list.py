import gtk
import gobject
import os
import sys
import pydoc
from os.path import join, basename, normpath, abspath
from os.path import split, expanduser, exists, isfile, dirname
import gobject

class ModuleContext:
	"""A generic wrapper for any object stored in a ModuleList.
	"""	
	def __init__ (self, icon, enabled, module, filename, handler, infos):
		"""The icon should be a gtk.gdk.Pixbuf"""
		self.icon = icon
		self.enabled = enabled
		self.module = module
		self.filename = filename
		self.handler = handler
		self.infos = infos

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
		"module-loaded" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		"modules-loaded" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		"module-initialized" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
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
		if (dirs):
			self.dirs = map (lambda s: abspath(expanduser(s)), dirs)
			self.filelist = self.build_filelist ()
		else:
			self.dirs = None
			self.filelist = []
						
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
			if (mod.HANDLERS): pass
		except AttributeError:
			print >> sys.stderr, "The file %s is not a valid module. Skipping." %filename
			print >> sys.stderr, "A module must have the variable HANDLERS defined as a dictionary."
			return
		
		if mod.HANDLERS == None:
			if not hasattr(mod, "ERROR"):
				mod.ERROR = "Unspecified Reason"
				
			print >> sys.stderr, "***"
			print >> sys.stderr, "*** The file %s decided to not load itself: %s" % (filename, mod.ERROR)
			print >> sys.stderr, "***"
			return
		
		for handler, infos in mod.HANDLERS.items():
			if hasattr(getattr(mod, handler), "initialize") and "name" in infos:
				pass				
			else:
				print >> sys.stderr, "Class %s in file %s does not have an initialize(self) method or does not define a 'name' attribute. Skipping." % (handler, filename)
				return
			
			if "requirements" in infos:
				ok, msg = infos["requirements"]()
				if not ok:
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
		"""
		
		print "Initializing %s" % context.infos["name"]
		context.module.initialize ()
		
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
			mod = self.owner[self.owner_iter][self.owner.MODULE_CTX_COL]
			self.owner_iter = self.owner.iter_next (self.owner_iter)
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
	MODULE_CTX_COL = 2
	
	def __init__ (self):
		gtk.ListStore.__init__ (self,
						gtk.gdk.Pixbuf, 
						bool, 
						gobject.TYPE_PYOBJECT)
		
	def __iter__ (self):
		return ModuleListIter (self)
	
	def get_position_from_context (self, attr, value=None):
		"""Returns a tuple (iter, index)
		
		iter is a gtk.TreeIter pointing to the row containing the given module context.
		index is the index of the module in the list.
		
		If the module context is not found return (None, None).
		"""
		i = 0
		iter = self.get_iter_first ()
		while (iter is not None):
			if value == None:
				if self[iter][self.MODULE_CTX_COL] == attr:
					return (iter, i)
			else:
				if getattr(self[iter][self.MODULE_CTX_COL], attr) == value:
					return (iter, i)
			
			iter = self.iter_next (iter)
			i = i+1
		
		return (None, 0)
		
	def reorder_with_priority(self, enabled_modules):
		new_order = []
		for classname in enabled_modules:
			new_order.append(self.get_position_from_context("handler", classname)[1])
		
		for modctx in [modctx for modctx in self if modctx.handler not in enabled_modules]:
			new_order.append(self.get_position_from_context("handler", modctx.handler)[1])
		
		self.reorder(new_order)
		
	def add (self, context, iter=None):
		"""If iter is set this method updates the row pointed to by iter with the 
		values of context. 
		
		If iter is not set it will try to obtain an iter pointing
		to the row containg the context. If there's no such row, it will append it.
		"""
		
		if iter is None:
			res = self.get_position_from_context(context)
		if res is None or res[0] is None:
			iter = self.append ()
		
		self.set_value(iter, self.ICON_COL, context.icon)
		self.set_value(iter, self.ENABLED_COL, context.enabled)
		self.set_value(iter, self.MODULE_CTX_COL, context)
		
	def update_row_cb (self, sender, context, iter=None):
		"""
		Callback for updating the row containing context.
		If iter is set the row to which it points to will be
		updated with the context.
		"""
		self.add(context, iter)
	
	def module_toggled_cb (self, sender, context):
		"""
		Callback to toggle the enabled state of the context.
		"""
		self[self.get_position_from_context(context)[0]][self.ENABLED_COL] = context.enabled
		
class ModuleListView (gtk.TreeView):
	"""A versatile list widget that displays the contents of a ModuleList.
	model: ModuleList
	
	Example:
		model = ModuleList ()
		view = ModuleListView (model)
	
	This will construct a list showing the module icon, a checkbox on whether or
	not they are enabled, and a pango markup-formatted description.
	"""
	
	__gsignals__ = {
		"row-toggled" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
	}
	
	def __init__ (self, model):
		gtk.TreeView.__init__ (self, model)
		
		self.set_property("headers-visible", False)
		self.set_reorderable(True)
		
		cell_icon = gtk.CellRendererPixbuf ()
		self.column_icon = gtk.TreeViewColumn ("Icon", cell_icon)
		self.column_icon.set_attributes (cell_icon, pixbuf=model.ICON_COL)
		self.column_icon.set_max_width (36)
		
		cell_enabled = gtk.CellRendererToggle ()
		cell_enabled.set_property ("activatable", True)
		cell_enabled.connect('toggled', self.emit_row_toggled, model)
		self.column_enabled = gtk.TreeViewColumn ("Enabled", cell_enabled, active=model.ENABLED_COL)

		cell_description = gtk.CellRendererText ()
		self.column_description = gtk.TreeViewColumn ("Description", cell_description)
		self.column_description.set_cell_data_func(cell_description, self.get_description_data)
		
		self.append_column(self.column_icon)
		self.append_column(self.column_enabled)
		self.append_column(self.column_description)
	
	def get_description_data(self, column, cell, model, iter, data=None):
		modctx = model[iter][model.MODULE_CTX_COL]
		name = modctx.infos["name"]
		description = ""
		if "description" in modctx.infos:	
			description = modctx.infos["description"]
			
		cell.set_property ("markup", "<b>%s</b>\n%s" % (name, description))
		
	def emit_row_toggled (self, cell, path, model):
		"""Callback for the toggle buttons in the ModuleList.ENABLED_COL.
		Emits a 'row-toggled' signal passing the context in the row as argument."""
		self.emit ("row-toggled", model[model.get_iter(path)][model.MODULE_CTX_COL])
		
def toggle_module (sender, context, ml):
	"""Test function"""
	if (context.enabled):
		ml.stop_module_async (context)
	else:
		ml.initialize_module_async (context)

if __name__ == "__main__":

	"""A test suite for the Module* classes. Run from top level dir,
	ie. from deskbar-applet/ run 'python deskbar/module_list.py'."""
		
	name = join(dirname(__file__), '..')
	print 'Changing PYTHONPATH'
	sys.path.insert(0, abspath(name))
    
	l = ModuleList ()    
	ml = ModuleLoader (["deskbar/handlers"])
	ml.connect ("module-loaded", l.update_row_cb)
	ml.connect ("module-initialized", l.module_toggled_cb)
	ml.connect ("module-stopped", l.module_toggled_cb)
	
	# Load all or just the directories handler. Uncomment to your liking
	ml.load_all_async ()
	#ml.load_async (abspath(expanduser("deskbar/testmod.py")))


	lw = ModuleListView (l)
	lw.connect ("row-toggled", toggle_module, ml)
	
	win = gtk.Window ()
	win.connect ("destroy", gtk.main_quit)
	win.add (lw)
	win.show ()
	lw.show ()
	
	gtk.main ()
