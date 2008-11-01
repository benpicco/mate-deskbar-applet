import glib
import gtk
import gobject
from gettext import gettext as _

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
        self.set_property("rules-hint", True)
        self.set_reorderable(True)
        
        cell_enabled = gtk.CellRendererToggle ()
        cell_enabled.set_property ("activatable", True)
        cell_enabled.connect('toggled', self.emit_row_toggled, model)
        self.column_enabled = gtk.TreeViewColumn ("Enabled", cell_enabled, active=model.ENABLED_COL)

        cell_icon = gtk.CellRendererPixbuf ()
        self.column_icon = gtk.TreeViewColumn ("Icon", cell_icon)
        self.column_icon.set_attributes (cell_icon, pixbuf=model.ICON_COL)
        self.column_icon.set_max_width (36)
        
        cell_description = gtk.CellRendererText ()
        self.column_description = gtk.TreeViewColumn ("Description", cell_description)
        self.column_description.set_cell_data_func(cell_description, self.get_description_data)
        
        self.append_column(self.column_enabled)
        self.append_column(self.column_icon)
        self.append_column(self.column_description)
    
    def get_description_data(self, column, cell, model, iter, data=None):
        mod = model[iter][model.MODULE_CTX_COL]
        name = mod.INFOS["name"]
        version = mod.INFOS["version"]
        description = ""
        if "description" in mod.INFOS:
            description = mod.INFOS["description"]

        description = "<b>%s</b> <small>(<i>%s</i> %s)</small>\n%s" % (name, _("Version:"), version, description)

        if model[iter][model.UPDATEABLE_COL]:
            description += "\n<i><b><small>%s</small></b></i>" % _("Update Available")
            
        cell.set_property ("markup", description)
        
    def get_selected_module (self):
        selection = self.get_selection()
        if selection == None:
            return None
            
        model, iter = selection.get_selected()
        if iter is None:
            return None
        return model[iter][model.MODULE_CTX_COL]
        
    def emit_row_toggled (self, cell, path, model):
        """Callback for the toggle buttons in the ModuleList.ENABLED_COL.
        Emits a 'row-toggled' signal passing the context in the row as argument."""
        self.emit ("row-toggled", model[model.get_iter(path)][model.MODULE_CTX_COL])
        
    def scroll_to_iter(self, iter):
        path = self.get_model().get_path(iter)
        self.get_selection().select_path( path )
        glib.idle_add(self.scroll_to_cell, path )
        self.set_cursor_on_cell( path )

if gtk.pygtk_version < (2,8,0):
    gobject.type_register(ModuleListView)
    
class DisabledModuleListView (gtk.TreeView):
    
    def __init__ (self, model):
        gtk.TreeView.__init__ (self, model)
        
        self.set_property("headers-visible", False)
        self.set_property("rules-hint", True)
        self.set_reorderable(True)
        
        cell_icon = gtk.CellRendererPixbuf ()
        self.column_icon = gtk.TreeViewColumn ("Icon", cell_icon)
        self.column_icon.set_attributes (cell_icon, pixbuf=model.ICON_COL)
        self.column_icon.set_max_width (36)
        
        cell_description = gtk.CellRendererText ()
        self.column_description = gtk.TreeViewColumn ("Description", cell_description)
        self.column_description.set_cell_data_func(cell_description, self.get_description_data)
        
        self.append_column(self.column_icon)
        self.append_column(self.column_description)
    
    def get_description_data(self, column, cell, model, iter, data=None):
        mod = model[iter][model.MODULE_CTX_COL]
        name = mod.INFOS["name"]
        description = ""
        if "description" in mod.INFOS:
            description = mod.INFOS["description"]

        description = "<b>%s</b>\n%s" % (name, description)            
        cell.set_property ("markup", description)
        
    def get_selected_module (self):
        selection = self.get_selection()
        if selection == None:
            return None
            
        model, iter = selection.get_selected()
        if iter is None:
            return None
        return model[iter][model.MODULE_CTX_COL]
    
if gtk.pygtk_version < (2,8,0):
    gobject.type_register(DisabledModuleListView)
    
class WebModuleListView (gtk.TreeView):
    
    def __init__ (self, model):
        gtk.TreeView.__init__ (self, model)
        
        self.set_property("headers-visible", False)
        self.set_property("rules-hint", True)
        self.set_reorderable(True)
                
        cell_description = gtk.CellRendererText ()
        column_description = gtk.TreeViewColumn ("Description", cell_description)
        column_description.set_cell_data_func(cell_description, self.get_description_data)

        self.append_column(column_description)
    
    def get_description_data(self, column, cell, model, iter, data=None):
        mod_name = model[iter][model.MODULE_NAME]
        mod_desc = model[iter][model.MODULE_DESCRIPTION]
        description = "<b>%s</b>\n%s" % (mod_name, mod_desc)
            
        cell.set_property ("markup", description)
        
    def get_selected_module_id (self):
        model, iter = self.get_selection().get_selected()
        if iter is None:
            return None
        return model[iter][model.MODULE_ID]
        
if gtk.pygtk_version < (2,8,0):
    gobject.type_register(WebModuleListView)
