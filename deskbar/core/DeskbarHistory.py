from deskbar import HISTORY_FILE
from deskbar.core.Categories import CATEGORIES
from gettext import gettext as _
import cPickle
import deskbar.interfaces.Action
import gobject
import gtk
import logging
import time

LOGGER = logging.getLogger(__name__)

class EmptyHistoryAction (deskbar.interfaces.Action):
    """
    This will be displayed if history is empty
    """
    
    def __init__(self):
        deskbar.interfaces.Action.__init__(self, "")
        
    def get_verb(self):
        return _("<i>Empty history</i>")
    
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
        "cleared" :        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "action-added" :   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [str, gobject.TYPE_PYOBJECT]), 
    }
    __instance = None
    (COL_TIME, COL_TEXT, COL_ACTION) = range(3)
    
    def __init__ (self, max_history_items=25):
        """
        *Do not* use the constructor directly. Always
        use L{get_instance}.
        """
        gtk.ListStore.__init__ (self, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT) # timestamp, query, match
        
        self.set_sort_order (gtk.SORT_DESCENDING)
        self.set_sort_func (self.COL_TIME, self.__sort_actions)
        
        self._index = -1
        self.set_max_history_items(max_history_items)
    
    def set_sort_order(self, order):
        """
        @param order Either C{gtk.SORT_DESCENDING} or C{gtk.SORT_ASCENDING}
        """
        self.set_sort_column_id(self.COL_TIME, order)
        if order == gtk.SORT_DESCENDING:
            # Alternatively gtk.TreeStore.prepend for bottom panel layout
            self.append_method = gtk.ListStore.append
        else:
            self.append_method = gtk.ListStore.prepend
    
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
                
        if self[iter1][self.COL_TIME] > self[iter2][self.COL_TIME] :
            return 1
        else:
            return -1
    
    def clear (self):
        """
        Clear the history
        """
        gtk.ListStore.clear(self)
        self._index = -1
        self.emit("cleared")
        self.append("", "", EmptyHistoryAction())
    
    def load (self):
        """
        Load history
        """
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
        except ImportError:
            # The module is not available anymore
            pass
        except Exception, e:
            # The history file is corrupted
            LOGGER.error("Could not restore history")
            LOGGER.exception(e)
        
        if len(self) == 0:
            self.append(0, "", EmptyHistoryAction())

    def save (self):
        """
        Save history
        """
        save = []
        for timestamp, text, action in self:
            if not isinstance(action, EmptyHistoryAction):
                save.append((timestamp, text, action))
        
        try:
            cPickle.dump(save, file(HISTORY_FILE, 'w'), cPickle.HIGHEST_PROTOCOL)
        except Exception, msg:
            LOGGER.error('History.save:%s', msg)
    
    def append (self, timestamp, text, action):
        """
        *Do not* use this method. Always use L{add}.
        """
        self.emit('action-added', text, action)
        self.append_method (self, (timestamp, text, action))
    
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
        assert text != None and action != None
        
        if not isinstance(action, deskbar.interfaces.Action):
            raise TypeError("Action must be a deskbar.interfaces.Action instance")
        
        if isinstance(action, EmptyHistoryAction):
            return
        if action.skip_history():
            self.reset()
            return
        
        for idx, val in enumerate(self):
            htime, htext, haction = val
            if isinstance(haction, EmptyHistoryAction):
                self.remove_index (idx)
                continue
                
            if (action.get_hash() == haction.get_hash() and action.__class__.__name__ == haction.__class__.__name__):
                self.remove_index (idx)
                break
                
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.append (timestamp, text, action)
        self.__remove_too_many()

        self.reset()
        self.save()
        
    def remove(self, aiter):
        gtk.ListStore.remove(self, aiter)
        if len(self) == 0:
            self.clear()
        
    def remove_index(self, index):
        self.remove (self.get_iter_from_string (str(index)))
    
    def remove_index_and_save(self, index):
        self.remove_index(index)
        self.save()
    
    def remove_and_save(self, aiter):
        self.remove(aiter)
        self.save()
    
    def __remove_too_many(self):
        while len(self) > self.__max_history_items:
            self.remove_index (len(self) - 1)
    
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
