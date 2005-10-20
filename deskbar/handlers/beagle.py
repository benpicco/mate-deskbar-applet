import os
from os.path import exists
from gettext import gettext as _

import deskbar.handler, deskbar.handler_utils

#FIXME: better way to detect beagle ?
HANDLERS = {
	"BeagleHandler" : {
		"name": _("Beagle"),
		"description": _("Use Beagle to search for documents"),
		# Better Way to detect ?
		"requirements": lambda: (exists("/usr/share/applications/best.desktop"), "Beagle was not detected on your system"),
	}
}

class BeagleMatch(deskbar.handler.Match):
	def __init__(self, backend, name):
		deskbar.handler.Match.__init__(self, backend, name)
		
	def action(self, text=None):
		os.spawnvp(os.P_NOWAIT, "best", ['best', '--no-tray', '--show-window', self._name])
	
	def get_verb(self):
		return _("Search <b>%(name)s</b> with Beagle")
		
				
class BeagleHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "best")
				
	def query(self, query, max=5):
		return [BeagleMatch(self, query)]
