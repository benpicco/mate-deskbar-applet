import gtk
import gtk.gdk
import gobject
import pango

class CuemiacActionsModel(gtk.ListStore):
    
    ICON_COL, LABEL_COL, QUERY_COL, ACTION_COL = range(4)
    
    def __init__(self):
        gtk.ListStore.__init__(self, gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
        
    def add_actions(self, actions, qstring):
        for action in actions:
            text = action.get_verb() % action.get_escaped_name(qstring)
            self.append([action.get_pixbuf(), text, qstring, action])
        
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
        self.set_enable_search (False)
        self.connect("button-press-event", self.__on_button_press_event)
        self.connect("key-press-event", self.__on_key_press_event)
        
        cell_icon = gtk.CellRendererPixbuf()
        cell_icon.set_property("xpad", 10)
        cell_text = gtk.CellRendererText()
        cell_text.set_property ("ellipsize", pango.ELLIPSIZE_END)
        col = gtk.TreeViewColumn("Actions")
        col.pack_start(cell_icon, expand=False)
        col.add_attribute(cell_icon, "pixbuf", model.ICON_COL)
        col.pack_start(cell_text)
        col.add_attribute(cell_text, "markup", model.LABEL_COL)
        self.append_column(col)
        
    def __on_button_press_event (self, treeview, event):
        path_ctx = self.get_path_at_pos (int(event.x), int(event.y))
        if path_ctx != None:
            path, col, x, y = path_ctx
            model = self.get_model ()
            action = model[model.get_iter(path)][model.ACTION_COL]
            qstring = model[model.get_iter(path)][model.QUERY_COL]
            
            self.emit ("action-selected", qstring, action, event)
            
    def __on_key_press_event(self, treeview, event):
        model, iter = self.get_selection().get_selected()
        if iter is None:
            return False
        action = model[iter][model.ACTION_COL]

        if event.keyval in self.activation_keys:
            qstring = model[iter][model.QUERY_COL]
            self.emit ("action-selected", qstring, action, event)
        elif event.keyval in self.back_keys:
            self.emit ("go-back")
        return False
		 