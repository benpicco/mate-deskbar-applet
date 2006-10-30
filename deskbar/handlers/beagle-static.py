import os
from os.path import exists, join
from glob import glob
from gettext import gettext as _
from deskbar.defs import VERSION
import gobject
import deskbar.Handler, deskbar.Utils, deskbar.Match
from deskbar.Utils import get_xdg_data_dirs, spawn_async

#FIXME: better way to detect beagle ?
def _check_requirements():
	for dir in get_xdg_data_dirs():
		if glob(join(dir, "applications", "*best.desktop")) or glob(join(dir, "applications", "*beagle-search.desktop")):
			return (deskbar.Handler.HANDLER_IS_HAPPY, None, None)
	
	return (deskbar.Handler.HANDLER_IS_NOT_APPLICABLE, "Beagle does not seem to be installed, skipping", None)

HANDLERS = {
	"BeagleHandler" : {
		"name": _("Beagle"),
		"description": _("Search all of your documents (using Beagle)"),
		"requirements": _check_requirements,
		"version": VERSION,
	}
}

class BeagleMatch(deskbar.Match.Match):
	def __init__(self, backend, **args):
		deskbar.Match.Match.__init__(self, backend, **args)
		
	def action(self, text=None):
		if not spawn_async(["beagle-search", self.name]):
			spawn_async(["best", '--no-tray', '--show-window', self.name])
			
	def get_verb(self):
		return _("Search for %s using Beagle") % "<b>%(name)s</b>"
	
	def get_category (self):
		return "actions"
	
				
class BeagleHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, ("system-search", "best"))
				
	def query(self, query):
		return [BeagleMatch(self, name=query)]
