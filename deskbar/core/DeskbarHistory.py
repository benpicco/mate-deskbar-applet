import cPickle
import gtk, gobject
import time
import logging
import deskbar.interfaces.Action
from deskbar import HISTORY_FILE
from gettext import gettext as _
from deskbar.core.Categories import CATEGORIES

class ChooseFromHistoryAction (deskbar.interfaces.Action):
    """
    This will be displayed always at the top of the history
    and is just there to display "Choose action"
    """
    
    def __init__(self):
        deskbar.interfaces.Action.__init__(self, "")
        
    def get_verb(self):
        return _("<i>Choose action</i>")
    
    def activate(self, text=None):
        pass
    
    def get_pixbuf(self):
        return CATEGORIES["history"]["icon"]
    
    def skip_history(self):
        return True
        
class DeskbarHistory (gtk.ListStore) :
    """
    Iterating over a DeskbarHistory with a for loop returns 
    C{(timestamp, text, action)} tuples.
    
    Keeps an internal pointer to a history index which you can move
    with L{up}, L{down} and L{reset}. You retrieve the item in question
    by L{get_current}.
    """
    
    __gsignals__ = {
        "cleared" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
    }
    __instance = None
    (COL_TIME, COL_TEXT, COL_ACTION) = range(3)
    
    def __init__ (self, max_history_items=25):
        """
        *Do not* use the constructor directly. Always
        use L{get_instance}.
        """
        gtk.ListStore.__init__ (self, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT) # timestamp, query, match
        
        self.set_sort_column_id (self.COL_TIME, gtk.SORT_DESCENDING)
        self.set_sort_func (self.COL_TIME, self.__sort_actions)
        
        self._index = -1
        self.set_max_history_items(max_history_items)
        
        self.append(0, "", ChooseFromHistoryAction())
    
    @staticmethod
    def get_instance(max_history_items=25):
        """
        @return: DeskbarHistory instance
        """
        if not DeskbarHistory.__instance:
            DeskbarHistory.__instance = DeskbarHistory(max_history_items)
        return DeskbarHistory.__instance
    
    def set_max_history_items(self, num):
        """
        Set the maximum number if items that will be
        stored
        """
        self.__max_history_items = num
        self.__remove_too_many()
    
    def __sort_actions (self, model, iter1, iter2):
        """
        @type model: DeskbarHistory
        @type iter1: gtk.TreeIter
        @type iter2: gtk.TreeIter
        """
        action1 = model[iter1][self.COL_ACTION]
        action2 = model[iter2][self.COL_ACTION]
        
        if isinstance(action1, ChooseFromHistoryAction):
            return 1
        elif isinstance(action2, ChooseFromHistoryAction):
            return -1
        else:        
            if self[iter1][self.COL_TIME] > self[iter2][self.COL_TIME] :
                return 1
            else:
                return -1
    
    def clear (self):
        """
        Clear the history
        """
        gtk.ListStore.clear(self)
        self.append("", "", ChooseFromHistoryAction())
        self._index = -1
        self.emit("cleared")
    
    def load (self):
        """
        Load history
        """
        new_history = []
        try:
            saved_history = cPickle.load(file(HISTORY_FILE))
            
            for i, data in enumerate(saved_history):
                if i == self.__max_history_items-1:
                    break
                timestamp, text, action = data
                if action.is_valid():
                    self.append(timestamp, text, action)
            
        except IOError:
            # There's probably no history file
            pass

    def save (self):
        """
        Save history
        """
        save = []
        for timestamp, text, action in self:
            if action.__class__ != ChooseFromHistoryAction:
                save.append((timestamp, text, action))
        
        try:
            cPickle.dump(save, file(HISTORY_FILE, 'w'), cPickle.HIGHEST_PROTOCOL)
        except Exception, msg:
            logging.error('History.save:%s', msg)
        pass
    
    def append (self, timestamp, text, action):
        """
        *Do not* use this method. Always use L{add}.
        """
        gtk.ListStore.append (self, (timestamp, text, action))
    
    def prepend (self, timestamp, text, action):
        """
        Prepending is not supported
        """
        raise NotImplementedError("DeskbarHistory does not support prepending of matches, use append() instead.")
    
    def add (self, text, action):
        """
        Add action to history
        
        @param text: search term
        @type action: L{deskbar.interfaces.Action.Action}
        """
        if action.__class__ == ChooseFromHistoryAction:
            return
        if action.skip_history():
            self.reset()
            return
        
        for idx, val in enumerate(self):
            htime, htext, haction = val
            if (action.get_hash() == haction.get_hash() and action.__class__.__name__ == haction.__class__.__name__):
                self.remove (self.get_iter_from_string (str(idx)))
                break
                
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.append (timestamp, text, action)
        self.__remove_too_many()

        self.reset()
        self.save()
    
    def __remove_too_many(self):
        while len(self) > self.__max_history_items:
            last = self.get_iter_from_string (str(len(self) - 1))
            self.remove (last)
    
    def up(self):
        """
        Set index one up
        """
        if self._index < len(self)-1:
            self._index = self._index + 1
            return self.get_current()
    
    def down(self):
        """
        Set index one down
        """
        if self._index > -1:
            self._index = self._index - 1
            return self.get_current()
    
    def reset(self):
        """
        Reset index
        """
        if self._index != -1:
            self._index = -1
            return self.get_current()
    
    def last(self):
        """
        Get last action
        """
        if len(self) == 0:
            return None
        last = self.get_iter_from_string (str(len(self) - 1))
        return self[last][self.COL_ACTION]
    
    def get_all(self):
        """
        Get all actions
        """
        return self
        
    def get_current(self):
        """
        Get action where the current index points to
        """
        if self._index == -1:
            return None
        col_id, direction = self.get_sort_column_id()
        index = self._index
        if direction == gtk.SORT_ASCENDING:
            index = len(self)-1-index

        row = self[self.get_iter_from_string (str(index))]
        return (row[self.COL_TEXT], row[self.COL_ACTION])
    
if gtk.pygtk_version < (2,8,0):
    gobject.type_register(DeskbarHistory)
