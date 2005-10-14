import os
from os.path import join, basename, normpath, abspath
from os.path import split, expanduser, exists, isfile

from gettext import gettext as _

import gtk, gnome.ui
import deskbar, deskbar.indexer
import deskbar.handler

from deskbar.handler_utils import filesystem_possible_completions

EXPORTED_CLASS = "FileHandler"
NAME = (_("Files"), _("Open files by typing their names."))

PRIORITY = 150

factory = gnome.ui.ThumbnailFactory(gnome.ui.THUMBNAIL_SIZE_NORMAL)
icon_theme = gtk.icon_theme_get_default()

class FileMatch(deskbar.handler.Match):
	def __init__(self, backend, prefix, absname):
		icon_name, flags = gnome.ui.icon_lookup(icon_theme, factory,
				absname, "",
				gnome.ui.ICON_LOOKUP_FLAGS_SHOW_SMALL_IMAGES_AS_THEMSELVES)
		
		pixbuf = icon_theme.load_icon(icon_name, deskbar.ICON_SIZE, gtk.ICON_LOOKUP_USE_BUILTIN)
		name = join(prefix, basename(absname))
		deskbar.handler.Match.__init__(self, backend, name, pixbuf)
		
		self._filename = absname
				
	def action(self, text=None):
		os.spawnlp(os.P_NOWAIT, "gnome-open", "gnome-open", self._filename)
		
	def get_verb(self):
		return _("Open <b>%(name)s</b>")
				
class FileHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "file.png")
		self._relative = True
		
	def get_priority(self):
		if self._relative:
			return PRIORITY/2+1
		else:
			return PRIORITY+1
		
	def query(self, query, max=5):
		completions, prefix, self._relative = filesystem_possible_completions(query, True)

		result = []
		for completion in completions:
			result.append(FileMatch(self, prefix, completion))
		
		return result[:max]
