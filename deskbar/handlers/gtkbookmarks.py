import os, urllib
from os.path import expanduser, split, exists
from gettext import gettext as _

import gobject
import gnomevfs
import deskbar.handler
from deskbar.filewatcher import FileWatcher

HANDLERS = {
	"GtkBookmarkHandler" : {
		"name": _("File Manager bookmarks"),
		"description": _("Open your file manager's bookmarks by name."),
	}
}

GTK_BOOKMARKS_FILE = expanduser("~/.gtk-bookmarks")

class GtkBookmarkMatch(deskbar.handler.Match):
	def __init__(self, backend, name, path):
		deskbar.handler.Match.__init__(self, backend, name)
		self._path = path
		
	def action(self, text=None):
		self._priority = self._priority+1
		gobject.spawn_async(["nautilus", self._path], flags=gobject.SPAWN_SEARCH_PATH)
	
	def get_verb(self):
		return _("Open location %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self._path
	
class GtkBookmarkHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "folder-bookmark.png")
		self._locations = {}
		
	def initialize(self):
		if not hasattr(self, 'watcher'):
			self.watcher = FileWatcher()
			self.watcher.connect('changed', lambda watcher, f: self._scan_bookmarks_files())
		
		self.watcher.add(GTK_BOOKMARKS_FILE)
		self._scan_bookmarks_files()
		
	def query(self, query, max=5):
		result = []
		query = query.lower()
		for bmk, (name, loc) in self._locations.items():
			if bmk.startswith(query):
				result.append(GtkBookmarkMatch(self, name, loc))
		
		return result[:max]
	
	def stop(self):
		self.watcher.remove(GTK_BOOKMARKS_FILE)
		
	def _scan_bookmarks_files(self):
		if not exists(GTK_BOOKMARKS_FILE):
			return
			
		for line in file(GTK_BOOKMARKS_FILE):
			line = line.strip()
			try:
				if gnomevfs.exists(line):
					uri = urllib.unquote(line)
					head, tail = split(uri)	
					self._locations[tail.lower()] = (tail, line)
			except Exception, msg:
				print 'Error:_scan_bookmarks_files:', msg
