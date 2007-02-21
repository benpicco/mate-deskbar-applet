from gettext import gettext as _

import gtk

import deskbar.Handler
from deskbar.DeskbarHistory import get_deskbar_history
from deskbar.defs import VERSION

HANDLERS = {
	"HistoryHandler" : {
		"name": _("History"),
		"description": _("Recognize previously used searches"),
		"version": VERSION,
	}
}

class HistoryHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "stock_redo")
	
	def _get_history_order (self):
		col_id, order = get_deskbar_history ().get_sort_column_id ()
		return order
		
	def query(self, query):
		result = []
		
		# We need to take the position of the applet into consideration
		# this can be identified through the history sorting
		priority = len (get_deskbar_history())
		inc_priority = None
		if self._get_history_order() == gtk.SORT_DESCENDING :
			inc_priority = lambda x : x - 1
		else:
			inc_priority = lambda x : x + 1
			
		for text, match in get_deskbar_history():
			if text.startswith(query):
				match.get_category = lambda: "history"
								
				# Spare my life for overriding a private variable, but overriding
				# the method doesn't work . ie:
				# match.get_priority = lambda: (self.get_priority(), priority)
				match._priority = priority
				result.append((text, match))
				priority = inc_priority (priority)
		
		return result
