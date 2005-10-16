import os
from os.path import exists
from gettext import gettext as _

import deskbar.handler

#FIXME: better way to detect beagle ?
if exists("/usr/share/applications/best.desktop"):
	EXPORTED_CLASS = "BeagleHandler"
	NAME = (_("Beagle"), _("Use Beagle to search for documents"))
else:
	EXPORTED_CLASS = None
	NAME = "Beagle was not detected on your system"

class BeagleMatch(deskbar.handler.Match):
	def __init__(self, backend, name):
		deskbar.handler.Match.__init__(self, backend, name)
		
	def action(self, text=None):
		os.spawnvp(os.P_NOWAIT, "best", ['best', '--no-tray', '--show-window', self._name])
	
	def get_verb(self):
		return _("Search <b>%(name)s</b> with Beagle")
		
				
class BeagleHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "/usr/share/pixmaps/best.png")
				
	def query(self, query, max=5):
		return [BeagleMatch(self, query)]
