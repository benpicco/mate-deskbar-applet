import gtk, pango, gobject
import logging

class CuemiacHistoryView (gtk.ComboBox):

    __gsignals__ = {
        "match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT]),
    }
    
    def __init__ (self, historystore):
        gtk.ComboBox.__init__ (self, historystore)
        historystore.connect("cleared", self.__select_default_item)
        
        icon = gtk.CellRendererPixbuf ()
        icon.set_property("xpad", 4)
        icon.set_property("xalign", 0.1)
        
        title = gtk.CellRendererText ()
        title.set_property ("ellipsize", pango.ELLIPSIZE_END)
        title.set_property ("width-chars", 25) #FIXME: Pick width according to screen size
        
        self.pack_start (icon, expand=False)
        self.pack_start (title)
        self.set_cell_data_func(title, self.__get_action_title_for_cell)            
        self.set_cell_data_func(icon, self.__get_action_icon_for_cell)
        
        self.set_active(0)
        
        self.__changed_id = self.connect ("changed", lambda w: self.__on_activated())             
        
    def __get_action_icon_for_cell (self, celllayout, cell, model, iter, user_data=None):
        
        timestamp, text, action = model[iter]
        if action == None:
            return
        
        cell.set_property ("pixbuf", action.get_pixbuf())
        
    def __get_action_title_for_cell (self, celllayout, cell, model, iter, user_data=None):
        
        timestamp, text, action = model[iter]
        if action == None:
            return
        
        text = action.get_verb () % action.get_escaped_name(text)
        # We only want to display the first line of text
        # E.g. some beagle-live actions display a snippet in the second line 
        text = text.split("\n")[0]
        cell.set_property ("markup", text)

    def __on_activated (self):
        iter = self.get_active_iter()
        if iter != None:
            timestamp, text, action = self.get_model()[iter]
            if not action.is_valid():
                logging.warning("Action is not valid anymore. Removing it from history.")
                self.get_model().remove(iter)
                self.__select_default_item()
                return False
            self.emit ("match-selected", text, action)
            self.__select_default_item()
            
        return False

    def __select_default_item(self, model=None):
        self.handler_block(self.__changed_id)
        self.set_active ( 0 )
        self.handler_unblock(self.__changed_id)

if gtk.pygtk_version < (2,8,0):    
    gobject.type_register (CuemiacHistoryView)
