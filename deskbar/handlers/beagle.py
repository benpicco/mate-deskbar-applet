import os
from os.path import exists, join
from gettext import gettext as _

import gobject
import deskbar.handler, deskbar.handler_utils
from deskbar.handler_utils import get_xdg_data_dirs

#FIXME: better way to detect beagle ?
def _check_requirements():
	for dir in get_xdg_data_dirs():
		if exists(join(dir, "applications", "best.desktop")):
			return (True, None)
	
	return (False, "Beagle does not seem to be installed, skipping")

HANDLERS = {
	"BeagleHandler" : {
		"name": _("Beagle"),
		"description": _("Use Beagle to search for documents"),
		"requirements": _check_requirements,
	}
}

class BeagleMatch(deskbar.handler.Match):
	def __init__(self, backend, name):
		deskbar.handler.Match.__init__(self, backend, name)
		
	def action(self, text=None):
		gobject.spawn_async(["best", '--no-tray', '--show-window', self._name], flags=gobject.SPAWN_SEARCH_PATH)
	
	def get_verb(self):
		return _("Search for %s using Beagle") % "<b>%(name)s</b>"
		
				
class BeagleHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "best")
				
	def query(self, query, max=5):
		return [BeagleMatch(self, query)]
