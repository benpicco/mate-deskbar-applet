import os
from os.path import join, basename, normpath, abspath
from os.path import split, expanduser, exists, isfile

from gettext import gettext as _

import gobject
import gtk, gnome.ui
import deskbar, deskbar.indexer
import deskbar.handler

from deskbar.handler_utils import filesystem_possible_completions

HANDLERS = {
	"FileHandler" : {
		"name": _("Files"),
		"description": _("Open files by typing their names."),
	}
}

class FileMatch(deskbar.handler.Match):
	def __init__(self, backend, prefix, absname):
		pixbuf = deskbar.handler_utils.load_icon_for_file(absname)
		name = join(prefix, basename(absname))
		deskbar.handler.Match.__init__(self, backend, name, pixbuf)
		
		self._filename = absname
				
	def action(self, text=None):
		gobject.spawn_async(["gnome-open", self._filename], flags=gobject.SPAWN_SEARCH_PATH)
		
	def get_verb(self):
		return _("Open <b>%(name)s</b>")
	
	def get_hash(self, text=None):
		return self._filename
		
class FileHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "stock_new-text")
		self._relative = True
		
	def get_priority(self):
		if self._relative:
			return self._priority
		else:
			return self._priority+1
		
	def query(self, query, max=5):
		completions, prefix, self._relative = filesystem_possible_completions(query, True)

		result = []
		for completion in completions:
			result.append(FileMatch(self, prefix, completion))
		
		return result[:max]
