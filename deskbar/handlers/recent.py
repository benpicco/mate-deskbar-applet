from gettext import gettext as _
import gobject, gtk, gnome

import deskbar
import deskbar.Handler
import deskbar.Match
import deskbar.Utils

from deskbar.defs import VERSION
from deskbar.Watcher import FileWatcher

def _check_requirements():
	if gtk.pygtk_version >= (2,9,0):
		return (deskbar.Handler.HANDLER_IS_HAPPY, None, None)
	return (deskbar.Handler.HANDLER_IS_NOT_APPLICABLE, _("This handler requires a more recent gtk version (2.9.0 or newer)."), None)

HANDLERS = {
	"RecentHandler" : {
		"name": _("Recent Documents"),
		"description": _("Retrieve your recently accessed files and locations"),
		"requirements": _check_requirements,
		"version": VERSION,
	},
}

class RecentMatch(deskbar.Match.Match):
	def __init__(self, backend, recent_infos, **args):
		deskbar.Match.Match.__init__(self, backend, name=recent_infos.get_display_name(), **args)
		self._icon = recent_infos.get_icon(gtk.ICON_SIZE_MENU) # TODO: make use of deskbar.ICON_XXX ?
		
		self.recent_infos = recent_infos
				
	def action(self, text=None):
		deskbar.Utils.url_show_file(self.recent_infos.get_uri())
	
	def is_valid(self, text=None):
		return self.recent_infos.exists()
		
	def get_category(self):
		return "files" 
		
	def get_verb(self):
		return _("Open %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.recent_infos.get_uri()

class RecentHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, gtk.STOCK_FILE)
                self._recent_manager = gtk.recent_manager_get_default()
		
	def query(self, query):
		result = []
		for recent in self._recent_manager.get_items():
			if not recent.get_display_name().lower().startswith(query): continue
			if not recent.exists(): continue
			result.append (RecentMatch (self, recent))
		return result
			


		
