import os, urllib, sys, cgi, ConfigParser
from os.path import join, basename, normpath, abspath, dirname
from os.path import split, expanduser, exists, isfile, isdir
from gettext import gettext as _
import gobject, gtk, gnome, gnome.ui, gnomevfs

import deskbar, deskbar.Indexer
import deskbar.Handler
import deskbar.Match

from deskbar.defs import VERSION
from deskbar.Watcher import FileWatcher
from deskbar.Utils import spawn_async, url_show_file


HANDLERS = {
	"FileFolderHandler" : {
		"name": _("Files, Folders and Places"),
		"description": _("View your files, folders, bookmarks, drives, network places by name"),
		"version": VERSION,
	},
}

NETWORK_URIS = ["http", "ftp", "smb", "sftp"]
AUDIO_URIS = ["cdda"]
MONITOR = gnomevfs.VolumeMonitor()

GTK_BOOKMARKS_FILE = expanduser("~/.gtk-bookmarks")

class FileMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, absname=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		self._icon = deskbar.Utils.load_icon_for_file(absname)
		
		self.absname = absname
				
	def action(self, text=None):
		url_show_file(self.absname)

	def is_valid(self, text=None):
		return exists(self.absname)
		
	def get_category(self):
		return "files"
		
	def get_verb(self):
		return _("Open %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.absname

class FolderMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, absname=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		self._icon = deskbar.Utils.load_icon_for_file(absname)
		
		self.absname = absname
		
	def action(self, text=None):
		url_show_file(self.absname)
	
	def is_valid(self, text=None):
		return exists(self.absname)
		
	def get_category(self):
		return "places"
	
	def get_verb(self):
		return _("Open folder %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.absname

class GtkBookmarkMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, path=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		self.path = path
		
	def action(self, text=None):
		spawn_async(["nautilus", self.path])
	
	def is_valid(self, text=None):
		return exists(self.path)
		
	def get_category(self):
		return "places"
	
	def get_verb(self):
		return _("Open location %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.path

class VolumeMatch (deskbar.Match.Match):
	def __init__(self, backend, name=None, drive=None, icon=None):
		deskbar.Match.Match.__init__(self, backend, name=name, icon=icon)
		self.drive = drive
	
	def action(self, text=None):
		if self.drive == None:
			spawn_async(["nautilus"])
		else:
			spawn_async(["nautilus", self.drive])

	def is_valid(self, text=None):
		return exists(self.drive)
		
	def get_category(self):
		return "places"
	 
	def get_verb(self):
		if self.drive == None:
			uri_scheme = None
		else:
			uri_scheme = gnomevfs.get_uri_scheme(self.drive) 
			
		if uri_scheme in NETWORK_URIS:
			return _("Open network place %s") % "<b>%(name)s</b>"
		elif uri_scheme in AUDIO_URIS:
			return _("Open audio disc %s") % "<b>%(name)s</b>"
		else:
			return _("Open location %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.drive
		
class FileFolderHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, gtk.STOCK_OPEN)
		self._locations = {}
		
	def initialize(self):
		# Gtk Bookmarks --
		if not hasattr(self, 'watcher'):
			self.watcher = FileWatcher()
			self.watcher.connect('changed', lambda watcher, f: self._scan_bookmarks_files())
		
		self.watcher.add(GTK_BOOKMARKS_FILE)
		self._scan_bookmarks_files()

	def stop(self):
		self.watcher.remove(GTK_BOOKMARKS_FILE)
		
	def query(self, query):
		
		result = []
		result += self.query_filefolder(query, False)
		result += self.query_filefolder(query, True)
		
		# Gtk Bookmarks
		query = query.lower()
		for bmk, (name, loc) in self._locations.items():
			if bmk.startswith(query):
				result.append(GtkBookmarkMatch(self, name, loc))
		
		# Volumes		
		# We search both mounted_volumes() and connected_drives.
		# This way an audio cd in the cd drive will show up both
		# on "au" and "cd".
		# Drives returned by mounted_volumes() and connected_drives()
		# does not have the same display_name() strings.
		for drive in MONITOR.get_mounted_volumes() + MONITOR.get_connected_drives():
			if not drive.is_user_visible() : continue
			if not drive.is_mounted () : continue
			if not drive.get_display_name().lower().startswith(query): continue
			
			result.append (VolumeMatch (self, drive.get_display_name(), drive.get_activation_uri(), drive.get_icon()))
		
		
		return result
	
	def query_filefolder(self, query, is_file):
		completions, prefix, relative = filesystem_possible_completions(query, is_file)
		if is_file:
			return [FileMatch(self, join(prefix, basename(completion)), "file://"+completion) for completion in completions]
		else:
			return [FolderMatch(self, join(prefix, basename(completion)), "file://"+completion) for completion in completions]
	
	def _scan_bookmarks_files(self):
		if not exists(GTK_BOOKMARKS_FILE):
			return
			
		for line in file(GTK_BOOKMARKS_FILE):
			line = line.strip()
			try:
				if gnomevfs.exists(line):
					uri = urllib.unquote(line)
					head, tail = split(uri)
					# Sometimes tail=="" when for example using "file:///tmp"
					if tail == "":
						 i = head.rfind("/")
						 tail = head[i+1:]
					self._locations[tail.lower()] = (tail, line)
			except Exception, msg:
				print 'Error:_scan_bookmarks_files:', msg
				
def filesystem_possible_completions(prefix, is_file=False):
	"""
	Given an path prefix, retreive the file/folders in it.
	If files is False return only the folder, else return only the files.
	Return a tuple (list, prefix, relative)
	  list is a list of files whose name starts with prefix
	  prefix is the prefix effectively used, and is always a directory
	  relative is a flag indicating wether the given prefix was given without ~ or /
	"""
	relative = False
	# Path with no leading ~ or / are considered relative to ~
	if not prefix.startswith("~") and not prefix.startswith("/"):
		relative = True
		prefix = join("~/", prefix)
	# Path starting with ~test are considered in ~/test
	if prefix.startswith("~") and not prefix.startswith("~/") and len(prefix) > 1:
		prefix = join("~/", prefix[1:])
	if prefix.endswith("/"):
		prefix = prefix[:-1]
		
	if prefix == "~":
		return ([expanduser(prefix)], dirname(expanduser(prefix)), relative)

	# Now we see if the typed name matches exactly a file/directory, or
	# If we must take the parent directory and match the beginning of each file
	start = None
	path = normpath(abspath(expanduser(prefix)))		

	prefix, start = split(prefix)
	path = normpath(abspath(expanduser(prefix)))	
	if not exists(path):
		# The parent dir wasn't a valid file, exit
		return ([], prefix, relative)
	
	# Now we list all files contained in path. Depending on the parameter we return all
	# files or all directories only. If there was a "start" we also match each name
	# to that prefix so typing ~/cvs/x will match in fact ~/cvs/x*
	
	# First if we have an exact file match, and we requested file matches we return it alone,
	# else, we return the empty file set
	if my_isfile(path):
		print 'Myisfile:', is_file
		if is_file:
			return ([path], dirname(prefix), relative)
		else:
			return ([], prefix, relative)

	return ([f
		for f in map(lambda x: join(path, x), os.listdir(path))
		if my_isfile(f) == is_file and not basename(f).startswith(".") and (start == None or basename(f).startswith(start))
	], prefix, relative)

#FIXME: gross hack to detect .savedSearches from nautilus as folders
def my_isfile(path):
	return isfile(path) and not path.endswith(".savedSearch")
