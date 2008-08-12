import gtk
import gobject
import logging
import deskbar.interfaces.Module

LOGGER = logging.getLogger(__name__)

class ModuleList (gtk.ListStore):
    """
    Stores a list of available enabled or disabaled modules
    
    Note that the gtk.ListStore extends the following classes:
        gobject.GObject, gtk.TreeModel, gtk.TreeDragSource, gtk.TreeDragDest,
        gtk.TreeSortable
    More documentation:
        http://www.pygtk.org/pygtk2reference/class-gtkliststore.html
    Note that
    """
    
    ENABLED_COL, ICON_COL, MODULE_CTX_COL, ACTIVATABLE_COL, UPDATEABLE_COL = range(5)
    
    def __init__ (self):
        gtk.ListStore.__init__ (self,
                                bool,
                                gtk.gdk.Pixbuf,
                                gobject.TYPE_PYOBJECT,
                                bool,
                                bool)
        self._mod_to_name = {}
        self._bottom_enabled_path = None
        
    def __iter__ (self):
        return ModuleListIter (self)
    
    def _is_module(self, module):
        if not isinstance(module, deskbar.interfaces.Module):
            raise TypeError("Expected deskbar.interfaces.Module but got %r" % module)
        
    def increase_bottom_enabled_path(self):
        self._bottom_enabled_path = (self._bottom_enabled_path[0]+1,)
        
    def decrease_bottom_enabled_path(self):
        self._bottom_enabled_path = (self._bottom_enabled_path[0]-1,)
    
    def get_module_instance_from_name(self, modulename):
        if self._mod_to_name.has_key(modulename):
            return self._mod_to_name[modulename]
        else:
            return None
    
    def get_position_from_context (self, module):
        """
        Returns a tuple C{(iter, index)}
        
        iter is a gtk.TreeIter pointing to the row containing the given
        module module.
        index is the index of the module in the list.
        
        If the module is not found return (None, None).
        
        @param module: The module to get the position for
        @type module: Either a L{deskbar.interfaces.Module.Module} instance or the name of a module
        """
        i = 0
        iter = self.get_iter_first ()
        while (iter is not None):
            if isinstance(module, str):
                # Search for module's name
                if self[iter][self.MODULE_CTX_COL].__class__.__name__ == module:
                    return (iter, i)
            elif isinstance(module, deskbar.interfaces.Module):
                if self[iter][self.MODULE_CTX_COL] == module:
                    return (iter, i)
            else:
                raise TypeError("Expected string or deskbar.interfaces.Module but got %r" % module)
                
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
            new_order.append(self.get_position_from_context(classname)[1])
        
        self._bottom_enabled_path = (len(new_order)-1,)
        
        disabled_modules = [mod for mod in self if mod.__class__.__name__ not in enabled_modules]
        disabled_modules.sort(lambda x, y: cmp (x.INFOS["name"], y.INFOS["name"]))
        for dm_name in disabled_modules:
            new_order.append(self.get_position_from_context(dm_name)[1])
        
        self.reorder(new_order)
        
    def add (self, module, iter=None):
        """
        If iter is set this method updates the row pointed to by iter with the 
        values of module. 
        
        If iter is not set it will try to obtain an iter pointing
        to the row containg the module. If there's no such row, it will append it.
        """
        self._is_module(module)
        
        for mod in self:
            if mod.__class__.__name__ == module.__class__.__name__:
                # We don't want a duplicate module
                LOGGER.warning("You tried to add a module twice. Not adding %r from %s", mod, mod.get_filename())
                return
                
        if iter is None:
            res, index = self.get_position_from_context(module)
        if res is None or res[0] is None:
            iter = self.append ()
        
        self.set_value(iter, self.ICON_COL, module.INFOS['icon'])
        self.set_value(iter, self.ENABLED_COL, module.is_enabled())
        self.set_value(iter, self.MODULE_CTX_COL, module)
        self.set_value(iter, self.ACTIVATABLE_COL, True)
        self.set_value(iter, self.UPDATEABLE_COL, False)
        
        self._mod_to_name[module.__class__.__name__] = module
    
    def remove_module(self, module):
        self._is_module(module)
        
        iter, index = self.get_position_from_context(module)
        if iter != None:
            LOGGER.debug('Removing from modulelist: %s', module.INFOS['name'])
            self.remove(iter)
        
    def module_changed(self, module):
        self._is_module(module)
        
        iter, index = self.get_position_from_context(module)
        if iter != None:
            self.emit('row-changed', self.get_path(iter), iter)
        
    def update_row_cb (self, sender, module, iter=None):
        """
        Callback for updating the row containing module.
        If iter is set the row to which it points to will be
        updated with the module.
        """
        self.add(module, iter)
    
    def module_toggled_cb (self, sender, module):
        """
        Callback to toggle the enabled state of the module.
        """ 
        iter, index = self.get_position_from_context(module)
        if iter != None:
            # Only if the module is in the list
            self[iter][self.ENABLED_COL] = module.is_enabled()
        
    def is_module_enabled(self, iter):
        return self[iter][self.ENABLED_COL]
    
    def move_module_to_top(self, iter):
        self.move_before(iter, self.get_iter_first())
        
    def move_module_up(self, iter):
        path = self.get_path(iter)
        path_prev = (path[0]-1,)
        iter_prev = self.get_iter(path_prev)
        self.swap(iter, iter_prev)
        
    def move_module_down(self, iter):
        iter_next = self.iter_next(iter)
        self.swap(iter, iter_next)
        
    def move_module_to_bottom(self, iter):
        self.move_after(iter, self.get_iter(self._bottom_enabled_path))
        
    def get_iter_from_module_id(self, modid):
        iter = self.get_iter_first ()
        while (iter is not None):
            if self[iter][self.MODULE_CTX_COL].get_id() == modid:
                return iter
            iter = self.iter_next(iter)
        return None
            
    def set_module_update_available(self, iter, val):
        if iter != None:
            self.set_value(iter, self.UPDATEABLE_COL, val)

gobject.type_register(ModuleList)

class DisabledModuleList (gtk.ListStore):
    
    ICON_COL, MODULE_CTX_COL, ACTIVATABLE_COL = range(3)
    
    def __init__ (self):
        gtk.ListStore.__init__ (self,
                                gtk.gdk.Pixbuf,
                                gobject.TYPE_PYOBJECT,
                                bool)
        
    def __iter__ (self):
        return ModuleListIter (self)
        
    def add (self, sender, module):
        iter = self.append ()
        
        self.set_value(iter, self.ICON_COL, module.INFOS['icon'])
        self.set_value(iter, self.MODULE_CTX_COL, module)
        self.set_value(iter, self.ACTIVATABLE_COL, False)
    
    def get_position_from_context (self, module):
        """
        Returns a tuple C{(iter, index)}
        
        iter is a gtk.TreeIter pointing to the row containing the given
        module module.
        index is the index of the module in the list.
        
        If the module is not found return (None, None).
        
        @param module: The module to get the position for
        @type module: Either a L{deskbar.interfaces.Module.Module} instance or the name of a module
        
        Note: This class stores the classes of disabled modules. It doesn't store actual module instances.
        """
        i = 0
        iter = self.get_iter_first ()
        while (iter is not None):
            if isinstance(module, str):
                # Search for module's name
                if self[iter][self.MODULE_CTX_COL].__name__ == module:
                    return (iter, i)
            else:
                if self[iter][self.MODULE_CTX_COL] == module:
                    return (iter, i)
                
            iter = self.iter_next (iter)
            i = i+1
        
        return (None, 0)
    
    def remove_module(self, module):
        iter, index = self.get_position_from_context(module)
        if iter != None:
            LOGGER.debug('Removing from disabledModulelist: %s', str(module))
            self.remove(iter)

gobject.type_register(DisabledModuleList)

class WebModuleList (gtk.ListStore):
    
    (MODULE_ID,
     MODULE_NAME,
     MODULE_DESCRIPTION) = range (3)
    
    def __init__ (self):
        gtk.ListStore.__init__ (self, str, str, str)
        self.set_sort_column_id (self.MODULE_NAME, gtk.SORT_ASCENDING)
        
    def __contains__ (self, mod_id):
        for mod in self:
            if mod_id == mod[0]:
                return True
        return False
    
    def get_position_from_context (self, module_id, value=None):
        """
        @param module_id: A module id
        @type module_id: str
        @return: a tuple (iter, index) or (None, 0) if the module is not found
        
        iter is a C{gtk.TreeIter} pointing to the row containing the given module module.
        index is the index of the module in the list.
        """
        i = 0
        iter = self.get_iter_first ()
        while (iter is not None):
            if value == None:
                if self[iter][self.MODULE_ID] == module_id:
                    return (iter, i)
            else:
                if getattr(self[iter][self.MODULE_ID], module_id) == value:
                    return (iter, i)
            
            iter = self.iter_next (iter)
            i = i+1
        
        return (None, 0)
                
    def add (self, mod_id, mod_name, mod_desc, iter=None):
        """
        If iter is set this method updates the row pointed to by iter with the 
        values of module. 
        
        If iter is not set it will try to obtain an iter pointing
        to the row containg the module. If there's no such row, it will append it.
        """
        for mod in self:
            if mod_id == mod[0]:
                # We don't want a duplicate module
                return
    
        if iter is None:
            iter = self.append ()
        
        self.set_value(iter, self.MODULE_ID, mod_id)
        self.set_value(iter, self.MODULE_NAME, mod_name)
        self.set_value(iter, self.MODULE_DESCRIPTION, mod_desc)
    
    def module_changed(self, module):
        iter, index = self.get_position_from_context(module)
        if iter != None:
            self.emit('row-changed', self.get_path(iter), iter)
   
gobject.type_register(WebModuleList)

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
