import gtk, gobject

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
	
	ENABLED_COL = 0
	ICON_COL = 1
	MODULE_CTX_COL = 2
	
	def __init__ (self):
		gtk.ListStore.__init__ (self,
		                        bool,
		                        gtk.gdk.Pixbuf,
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
		# Modules are sorted:
		# First enabled, then disabled modules.
		#   Enabled modules are sorted by their drag 'n' drop precedence.
		#   Disabled modules are sorted alphabetically by (i18n'd) name,
		#   (not the name of the Handler python class).
		new_order = []
		for classname in enabled_modules:
			new_order.append(self.get_position_from_context("handler", classname)[1])
		
		disabled_modules = [modctx for modctx in self if modctx.handler not in enabled_modules]
		disabled_modules.sort(lambda x, y: cmp (x.infos["name"], y.infos["name"]))
		for dm in disabled_modules:
			new_order.append(self.get_position_from_context("handler", dm.handler)[1])
		
		self.reorder(new_order)
		
	def add (self, context, iter=None):
		"""If iter is set this method updates the row pointed to by iter with the 
		values of context. 
		
		If iter is not set it will try to obtain an iter pointing
		to the row containg the context. If there's no such row, it will append it.
		"""
		for modctx in self:
			if modctx.handler == context.handler:
				# We don't want a duplicate module
				return
				
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

gobject.type_register(ModuleList)

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
