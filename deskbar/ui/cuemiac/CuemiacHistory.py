import gtk, pango, gobject

class CuemiacHistoryView (gtk.TreeView):

    __gsignals__ = {
        "match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT]),
    }
    
    def __init__ (self, historystore):
        gtk.TreeView.__init__ (self, historystore)
                
        icon = gtk.CellRendererPixbuf ()
        icon.set_property("xpad", 4)
        icon.set_property("xalign", 0.1)
        title = gtk.CellRendererText ()
        title.set_property ("ellipsize", pango.ELLIPSIZE_END)
        title.set_property ("width-chars", 25) #FIXME: Pick width according to screen size
        hits = gtk.TreeViewColumn ("Hits")
        hits.pack_start (icon, expand=False)
        hits.pack_start (title)
        hits.set_cell_data_func(title, self.__get_action_title_for_cell)            
        hits.set_cell_data_func(icon, self.__get_action_icon_for_cell)
        self.append_column (hits)
        
        self.connect ("row-activated", lambda w,p,c: self.__on_activated())
        self.connect ("button-press-event", lambda w,e: self.__on_activated())             
        
        self.set_property ("headers-visible", False)
        self.set_property ("hover-selection", True)
        
    def __get_action_icon_for_cell (self, column, cell, model, iter, data=None):
    
        timestamp, text, action = model[iter]
        if action.get_pixbuf() != None:
            cell.set_property ("pixbuf", action.get_pixbuf())
        
    def __get_action_title_for_cell (self, column, cell, model, iter, data=None):
        
        timestamp, text, action = model[iter]
                
        cell.set_property ("markup", action.get_verb () % action.get_escaped_name(text))

    def __on_activated (self):
        model, iter = self.get_selection().get_selected()
        if iter != None:
            timestamp, text, action = model[iter]
            self.emit ("match-selected", text, action)
        return False

if gtk.pygtk_version < (2,8,0):    
    gobject.type_register (CuemiacHistoryView)
