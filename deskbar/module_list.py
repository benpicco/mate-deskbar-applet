import gtk
import gobject
import os
import sys
import pydoc
from os.path import join, basename, normpath, abspath
from os.path import split, expanduser, exists, isfile, dirname

class ModuleContext:
	"""A generic wrapper for any object stored in a ModuleList.
	settings is unused at the moment.
	"""
	def __init__ (self, icon, enabled, name, module, settings, filename):
		"""The icon should be a gtk.gdk.Pixbuf"""
		self.icon = icon
		self.enabled = enabled
		self.name = name
		self.module = module
		self.settings = settings
		self.filename = filename
		

class ModuleListIter : 
	"""An iter type to iterate over the modules contexts in a ModuleList object.
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
		"""Return the next module in the ModuleList."""
		try:
			mod = ModuleContext (	self.owner.get_value (self.owner_iter, self.owner.ICON_COL), 
						self.owner.get_value (self.owner_iter, self.owner.ENABLED_COL), 
						self.owner.get_value (self.owner_iter, self.owner.NAME_COL), 
						self.owner.get_value (self.owner_iter, self.owner.MODULE_COL), 
						self.owner.get_value (self.owner_iter, self.owner.SETTINGS_COL), 
						self.owner.get_value (self.owner_iter, self.owner.FILENAME_COL))
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
	
	From this perspective the ModuleList stores ModuleContext (it actually doesnt),
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
	NAME_COL = 2
	MODULE_COL = 3
	SETTINGS_COL = 4
	FILENAME_COL = 5
	
	def __init__ (self):
		gtk.ListStore.__init__ (self, 	gtk.gdk.Pixbuf, 
						bool, 
						gobject.TYPE_STRING, 
						gobject.TYPE_PYOBJECT, 
						gobject.TYPE_PYOBJECT, 
						gobject.TYPE_STRING)
		
	def __iter__ (self):
		return ModuleListIter (self)
	
	def add (self, mod_context):
		it = self.append ()
		self.set (it, self.ICON_COL, mod_context.icon)
		self.set (it, self.ENABLED_COL, mod_context.enabled)
		self.set (it, self.NAME_COL, mod_context.name)
		self.set (it, self.MODULE_COL, mod_context.module)
		self.set (it, self.SETTINGS_COL, mod_context.settings)
		self.set (it, self.FILENAME_COL, mod_context.filename)
		
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
	def __init__ (self, model, columns):
		gtk.TreeView.__init__ (self, model)
		
		if (model.ICON_COL in columns):
			cell_icon = gtk.CellRendererPixbuf ()
			self.column_icon = gtk.TreeViewColumn ("", cell_icon)
			self.column_icon.set_attributes (cell_icon, pixbuf=model.ICON_COL)
			self.column_icon.set_max_width (36)
		
		if (model.ENABLED_COL in columns):
			cell_enabled = gtk.CellRendererToggle ()
			cell_enabled.set_property ("activatable", True)
			cell_enabled.connect('toggled', self.toggle_enable, model)
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
				
		self.set_headers_visible(True)
		
	def toggle_enable (self, cell, path, model):
		iter = model.get_iter(path)
		model.set_value(iter, model.ENABLED_COL, not cell.get_active())
		for mod in model:
			print mod.name +" is enabled: " + str(mod.enabled)
			
class ModuleLoader:
	"""An auxilary class to ModuleList. Create an instance of ModuleLoader by
	specifying the which directories to search and what extension to accept.
	The load_all() method will load all qualified modules into the ModuleList
	specified in the constructor.
	"""
	def __init__ (self, modlist, dirs, extension=".py"):
		"""modlist: The ModuleList to store all succesfully loaded modules
		dirs: A list of directories to search. Relative pathnames and paths
			  containing ~ will be expanded.
		extension: What extension should this ModuleLoader accept (string).
		"""
		self.modlist = modlist
		self.dirs = map (lambda s: abspath(expanduser(s)), dirs)
		self.ext = extension
		self.filelist = self.build_filelist ()
		
			
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
		if (filename[-len(self.ext):] == self.ext):
			return True
		return False
			
	def load_all (self):
		"""Tries to load all qualified modules detected by the ModuleLoader.
		All succesfully loaded modules are stored in the ModuleList.
		"""
		for f in self.filelist:
			self.load (f)
	
	def load (self, filename):
		"""Tries to load the specified file as a module and stores it in the ModuleList."""
		try:
			print "Importing %s" % filename
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
			print >> sys.stderr, "The file %s decided to not load itself: %s" % (mod.NAME, filename)
			return
					
		try:
			mod_init = getattr (mod, mod.EXPORTED_CLASS)
		except AttributeError:
			print >> sys.stderr, "Class %s not found in file %s. Skipping." % (mod.EXPORTED_CLASS, filename)
			return
								
		try:
			mod_instance = mod_init()
		except Exception, err:
			print >> sys.stderr, "Error in file: %s" % filename
			print >> sys.stderr, "There was an error initializing the class: %s" % str(mod_init)
			print >> sys.stderr, str(err)
			return

		context = ModuleContext (None, True, mod.NAME, mod_instance, None, filename)
		self.modlist.add(context)
			
if __name__ == "__main__":
	"""A test suite for the Module* classes. Run from top level dir, 
	ie. from deskbar-applet/ run 'python deskbar/module_list.py'."""
	
	name = join(dirname(__file__), '..')
	print 'Changing PYTHONPATH'
	sys.path.insert(0, abspath(name))
    
	l = ModuleList ()    
	ml = ModuleLoader (l, ["deskbar/handlers"], ".py")
	
	# Load all or just the directories handler. Uncomment to your liking
	#ml.load_all ()
	ml.load (abspath(expanduser("deskbar/handlers/directories.py")))

	lw = ModuleListView (l, [ModuleList.FILENAME_COL, ModuleList.NAME_COL, ModuleList.ENABLED_COL])
	win = gtk.Window ()
	win.connect ("destroy", gtk.main_quit)
	win.add (lw)
	win.show ()
	lw.show ()

	gtk.main ()
