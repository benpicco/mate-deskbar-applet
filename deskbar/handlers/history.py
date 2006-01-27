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
				match._history_priority = self.get_priority()
				result.append((text, match))
		
		return result