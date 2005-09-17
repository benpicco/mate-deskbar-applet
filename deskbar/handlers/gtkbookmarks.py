import os, urllib
from os.path import expanduser, split
from gettext import gettext as _

import gnomevfs
import handler

PRIORITY = 150

class GtkBookmarkMatch(handler.Match):
	def __init__(self, backend, name, path):
		handler.Match.__init__(self, backend, name)
		self._path = path
		
	def action(self, text=None):
		self._priority = self._priority+1
		os.spawnlp(os.P_NOWAIT, "nautilus", "nautilus", self._path)
	
	def get_verb(self):
		return _("Open location <b>%(name)s</b>")
		
	
class GtkBookmarkHandler(handler.Handler):
	def __init__(self):
		handler.Handler.__init__(self, "folder-bookmark.png")
		
		print 'Starting .gtkbookmarks file indexation'
		self._locations = {}
		self._scan_bookmarks_files()
		print '\tDone !'
		
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		result = []
		query = query.lower()
		for bmk, (name, loc) in self._locations.items():
			if bmk.startswith(query):
				result.append(GtkBookmarkMatch(self, name, loc))
		
		return result[:max]
		
	def _scan_bookmarks_files(self):
		for line in file(expanduser("~/.gtk-bookmarks")):
			line = line.strip()
			if gnomevfs.exists(line):
				uri = urllib.unquote(line)
				head, tail = split(uri)	
				self._locations[tail.lower()] = (tail, line)
