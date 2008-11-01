import glib
import gtk
import gtk.gdk
import gobject
import pango

class CuemiacActionsModel(gtk.ListStore):
    
    ICON_COL, LABEL_COL, QUERY_COL, ACTION_COL = range(4)
    
    def __init__(self):
        gtk.ListStore.__init__(self, gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
        self.set_sort_order(gtk.SORT_ASCENDING)
        
    def add_actions(self, actions, qstring):
        for action in actions:
            text = action.get_verb() % action.get_escaped_name(qstring)
            self.append_method(self, [action.get_pixbuf(), text, qstring, action])
  
    def set_sort_order(self, order):
        """
        @param order Either C{gtk.SORT_DESCENDING} or C{gtk.SORT_ASSCENDING}
        """
        if order == gtk.SORT_DESCENDING:
            # Alternatively gtk.TreeStore.prepend for bottom panel layout
            self.append_method = gtk.ListStore.prepend
        else:
            self.append_method = gtk.ListStore.append
    
        
class CuemiacActionsTreeView(gtk.TreeView):
   
    __gsignals__ = { 
        "action-selected": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
        "go-back": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
    }
    
    activation_keys = [gtk.keysyms.Return, gtk.keysyms.Right]
    back_keys = [gtk.keysyms.Left]
   
    def __init__(self, model=None):
        gtk.TreeView.__init__(self, model)
        self.set_property ("headers-visible", False)
        self.set_property ("has-tooltip", True)
        self.set_enable_search (False)
        self.connect("button-press-event", self.__on_button_press_event)
        self.connect("key-press-event", self.__on_key_press_event)
        self.connect("query-tooltip", self.__on_query_tooltip)
        
        cell_icon = gtk.CellRendererPixbuf()
        cell_icon.set_property("xpad", 10)
        cell_text = gtk.CellRendererText()
        cell_text.set_property ("ellipsize", pango.ELLIPSIZE_END)
        self._column = gtk.TreeViewColumn("Actions")
        self._column.pack_start(cell_icon, expand=False)
        self._column.add_attribute(cell_icon, "pixbuf", model.ICON_COL)
        self._column.pack_start(cell_text)
        self._column.add_attribute(cell_text, "markup", model.LABEL_COL)
        self.append_column(self._column)
        
    def __on_button_press_event (self, treeview, event):
        path_ctx = self.get_path_at_pos (int(event.x), int(event.y))
        if path_ctx != None:
            path, col, x, y = path_ctx
            model = self.get_model ()
            action = model[model.get_iter(path)][model.ACTION_COL]
            qstring = model[model.get_iter(path)][model.QUERY_COL]
            
            self.emit("row-activated", path, self._column)
            self.emit ("action-selected", qstring, action, event)
            
    def __on_key_press_event(self, treeview, event):
        model, iter = self.get_selection().get_selected()
        if iter is None:
            return False
        action = model[iter][model.ACTION_COL]

        if event.keyval in self.activation_keys:
            qstring = model[iter][model.QUERY_COL]
            self.emit ("row-activated", model.get_path(iter), self._column)
            self.emit ("action-selected", qstring, action, event)
        elif event.keyval in self.back_keys:
            self.emit ("go-back")
        elif event.keyval == gtk.keysyms.Down and model.get_path(iter) == (len(model)-1,):
            # Select first item
            self.__select_path( (0,) )
            return True
        elif event.keyval == gtk.keysyms.Up and model.get_path(iter) == (0,):
            # Select last item
            self.__select_path( (len(model)-1,) )
            return True
            
        return False
    
    def __select_path(self, path):
        self.get_selection().select_path( path )
        glib.idle_add(self.scroll_to_cell, path )
        self.set_cursor_on_cell( path )
       
    def __on_query_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        path = self.get_path_at_pos(x, y)
        if path == None:
            return False
        
        tree_path = path[0]
        
        model = self.get_model()
        iter = model.get_iter(tree_path)
        action = model[iter][model.ACTION_COL]
        
        qstring = model[iter][model.QUERY_COL]
        markup = action.get_tooltip (qstring)
        # Return False to not show a blank tooltip
        if markup != None and len(markup) != 0:
            tooltip.set_markup (markup)
            self.set_tooltip_row (tooltip, tree_path)
            return True
        
        return False
         
