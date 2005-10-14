import os, urllib
from os.path import expanduser, split, exists
from gettext import gettext as _

import gnomevfs
import deskbar.handler

EXPORTED_CLASS = "GtkBookmarkHandler"
NAME = (_("Nautilus Places"), _("Open your nautilus favorite places by name."))

PRIORITY = 150

class GtkBookmarkMatch(deskbar.handler.Match):
	def __init__(self, backend, name, path):
		deskbar.handler.Match.__init__(self, backend, name)
		self._path = path
		
	def action(self, text=None):
		self._priority = self._priority+1
		os.spawnlp(os.P_NOWAIT, "nautilus", "nautilus", self._path)
	
	def get_verb(self):
		return _("Open location <b>%(name)s</b>")
		
	
class GtkBookmarkHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "folder-bookmark.png")
		
		self._locations = {}
		
	def initialize(self):
		self._scan_bookmarks_files()
		
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
		bmk = expanduser("~/.gtk-bookmarks")
		if not exists(bmk):
			return
			
		for line in file(bmk):
			line = line.strip()
			try:
				if gnomevfs.exists(line):
					uri = urllib.unquote(line)
					head, tail = split(uri)	
					self._locations[tail.lower()] = (tail, line)
			except Exception, msg:
				print 'Error:_scan_bookmarks_files:', msg
