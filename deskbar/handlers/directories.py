import os
from os.path import join, basename, normpath, abspath
from os.path import split, expanduser, exists, isfile

from gettext import gettext as _

import gtk, gnome.ui
import deskbar, deskbar.indexer
import deskbar.handler

from deskbar.handler_utils import filesystem_possible_completions

EXPORTED_CLASS = "FolderHandler"
NAME = (_("Folders"),  _("Open folders by their names."))

PRIORITY = 150

class FolderMatch(deskbar.handler.Match):
	def __init__(self, backend, prefix, absname):
		name = join(prefix, basename(absname))
		deskbar.handler.Match.__init__(self, backend, name)
		
		self._filename = absname
		
	def action(self, text=None):
		os.spawnlp(os.P_NOWAIT, "nautilus", "nautilus", self._filename)
	
	def get_verb(self):
		return _("Open folder <b>%(name)s</b>")
				
class FolderHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "folder.png")
		self._relative = True
		
	def get_priority(self):
		if self._relative:
			return PRIORITY/2
		else:
			return PRIORITY
		
	def query(self, query, max=5):
		completions, prefix, self._relative = filesystem_possible_completions(query)

		result = []
		for completion in completions:
			result.append(FolderMatch(self, prefix, completion))
		
		return result[:max]
	
