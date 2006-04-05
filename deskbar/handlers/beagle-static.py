import os
from os.path import exists, join
from gettext import gettext as _

import gobject
import deskbar.Handler, deskbar.Utils, deskbar.Match
from deskbar.Utils import get_xdg_data_dirs

#FIXME: better way to detect beagle ?
def _check_requirements():
	for dir in get_xdg_data_dirs():
		if exists(join(dir, "applications", "best.desktop")) or exists(join(dir, "applications", "beagle-search.desktop")):
			return (deskbar.Handler.HANDLER_IS_HAPPY, None, None)
	
	return (deskbar.Handler.HANDLER_IS_NOT_APPLICABLE, "Beagle does not seem to be installed, skipping", None)

HANDLERS = {
	"BeagleHandler" : {
		"name": _("Beagle"),
		"description": _("Search all of your documents (using Beagle)"),
		"requirements": _check_requirements,
	}
}

class BeagleMatch(deskbar.Match.Match):
	def __init__(self, backend, **args):
		deskbar.Match.Match.__init__(self, backend, **args)
		
	def action(self, text=None):
		try:
			gobject.spawn_async(["beagle-search", self.name], flags=gobject.SPAWN_SEARCH_PATH)
		except:
			gobject.spawn_async(["best", '--no-tray', '--show-window', self.name], flags=gobject.SPAWN_SEARCH_PATH)
			
	def get_verb(self):
		return _("Search for %s using Beagle") % "<b>%(name)s</b>"
	
	def get_category (self):
		return "actions"
	
				
class BeagleHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, ("system-search", "best"))
				
	def query(self, query):
		return [BeagleMatch(self, name=query)]
