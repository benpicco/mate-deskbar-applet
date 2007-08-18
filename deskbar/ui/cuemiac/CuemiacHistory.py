import gtk, pango, gobject
import logging
import deskbar.interfaces.Action

class CuemiacHistoryView (gtk.ComboBox):

    __gsignals__ = {
        "match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT]),
    }
    
    def __init__ (self, historystore):
        gtk.ComboBox.__init__ (self, historystore)
                
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
        if action.get_pixbuf() != None:
            cell.set_property ("pixbuf", action.get_pixbuf())
        
    def __get_action_title_for_cell (self, celllayout, cell, model, iter, user_data=None):
        
        timestamp, text, action = model[iter]
        if action == None:
            return
        cell.set_property ("markup", action.get_verb () % action.get_escaped_name(text))

    def __on_activated (self):
        iter = self.get_active_iter()
        if iter != None:
            timestamp, text, action = self.get_model()[iter]
            if not action.is_valid():
                logging.warning("Action is not valid anymore. Removing it from history.")
                self.get_model().remove(iter)
                self.set_active(0)
                return False
            self.emit ("match-selected", text, action)
            self.handler_block(self.__changed_id)
            self.set_active ( 0 )
            self.handler_unblock(self.__changed_id)
        return False

if gtk.pygtk_version < (2,8,0):    
    gobject.type_register (CuemiacHistoryView)
