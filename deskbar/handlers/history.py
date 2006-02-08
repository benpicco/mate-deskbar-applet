from gettext import gettext as _

import deskbar.Handler
from deskbar.DeskbarHistory import get_deskbar_history

HANDLERS = {
	"HistoryHandler" : {
		"name": _("History"),
		"description": _("Recognize previously used searches"),
	}
}

class HistoryHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "stock_redo")
		
	def query(self, query, max):
		result = []
		for text, match in get_deskbar_history():
			if text.startswith(query):
				match.get_category = lambda: "history"
				
				# Beware of the infinite recursion here !
				match_prio = match.get_priority()[1]
				match.get_priority = lambda: (self.get_priority(), match_prio)
				result.append((text, match))
		
		return result
