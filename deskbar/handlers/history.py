from gettext import gettext as _

import gtk

import deskbar.interfaces.Module
import deskbar.interfaces.Match
from deskbar.core.DeskbarHistory import DeskbarHistory
from deskbar.defs import VERSION

HANDLERS = ["HistoryHandler"]

class HistoryMatch(deskbar.interfaces.Match):
    
    def __init__(self, name):
        deskbar.interfaces.Match.__init__(self, name=name, category="history")

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
                match = HistoryMatch(action.get_verb() % action.get_escaped_name(query))
                match.add_action(action)
                match.set_priority( self.get_priority() + priority )
                result.append(match)
                priority = inc_priority (priority)
        
        self._emit_query_ready(query, result )
