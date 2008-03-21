from deskbar.core.DeskbarHistory import DeskbarHistory
from deskbar.defs import VERSION
from gettext import gettext as _
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gtk



HANDLERS = ["HistoryHandler"]

class HistoryMatch(deskbar.interfaces.Match):
    
    def __init__(self, name, action):
        deskbar.interfaces.Match.__init__(self, name=name, category="history")
        self._action = action
   
    def get_hash(self):
        return "history_"+str(self._action.get_hash())
    
    def get_icon(self):
        return self._action.get_pixbuf()

class HistoryHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("stock_redo"),
             "name": _("History"),
             "description": _("Recognize previously used searches"),
             "version": VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
    
    def _get_history_order (self):
        col_id, order = DeskbarHistory.get_instance().get_sort_column_id ()
        return order
        
    def query(self, query):
        result = []
        
        # We need to take the position of the applet into consideration
        # this can be identified through the history sorting
        priority = len (DeskbarHistory.get_instance())
        
        inc_priority = None
        if self._get_history_order() == gtk.SORT_DESCENDING :
            inc_priority = lambda x : x - 1
        else:
            inc_priority = lambda x : x + 1
            
        for timestamp, text, action in DeskbarHistory.get_instance():
            if text.startswith(query):
                match_name = action.get_verb() % action.get_escaped_name(text)
                match = HistoryMatch(match_name, action)
                match.add_action(action)
                match.set_priority( self.get_priority() + priority )
                result.append(match)
                priority = inc_priority (priority)
        
        self._emit_query_ready(query, result )
