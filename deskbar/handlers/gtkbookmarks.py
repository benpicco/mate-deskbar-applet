import os, urllib
from os.path import expanduser, split, exists
from gettext import gettext as _

import gobject
import gnomevfs
import deskbar.Handler
from deskbar.Watcher import FileWatcher

HANDLERS = {
	"GtkBookmarkHandler" : {
		"name": _("Files and Folders Bookmarks"),
		"description": _("Open your files and folders bookmarks by name"),
	}
}

GTK_BOOKMARKS_FILE = expanduser("~/.gtk-bookmarks")

class GtkBookmarkMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, path=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		self.path = path
		
	def action(self, text=None):
		gobject.spawn_async(["nautilus", self.path], flags=gobject.SPAWN_SEARCH_PATH)
		
	def get_category(self):
		return "places"
	
	def get_verb(self):
		return _("Open location %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.path
	
class GtkBookmarkHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "folder-bookmark.png")
		self._locations = {}
		
	def initialize(self):
		if not hasattr(self, 'watcher'):
			self.watcher = FileWatcher()
			self.watcher.connect('changed', lambda watcher, f: self._scan_bookmarks_files())
		
		self.watcher.add(GTK_BOOKMARKS_FILE)
		self._scan_bookmarks_files()
		
	def query(self, query):
		result = []
		query = query.lower()
		for bmk, (name, loc) in self._locations.items():
			if bmk.startswith(query):
				result.append(GtkBookmarkMatch(self, name, loc))
		
		return result
	
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
