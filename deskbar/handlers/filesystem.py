import os
from os.path import join, basename, normpath, abspath
from os.path import split, expanduser, exists, isfile

from gettext import gettext as _

import gtk, gnome.ui
import deskbar, deskbar.indexer
import handler

PRIORITY = 150

factory = gnome.ui.ThumbnailFactory(gnome.ui.THUMBNAIL_SIZE_NORMAL)
icon_theme = gtk.icon_theme_get_default()

class FileMatch(handler.Match):
	def __init__(self, backend, prefix, absname):
		icon_name, flags = gnome.ui.icon_lookup(icon_theme, factory,
				absname, "",
				gnome.ui.ICON_LOOKUP_FLAGS_SHOW_SMALL_IMAGES_AS_THEMSELVES)
		
		pixbuf = icon_theme.load_icon(icon_name, deskbar.ICON_SIZE, gtk.ICON_LOOKUP_USE_BUILTIN)
		name = join(prefix, basename(absname))
		handler.Match.__init__(self, backend, name, pixbuf)
		
		self._filename = absname
				
	def action(self, text=None):
		os.spawnlp(os.P_NOWAIT, "gnome-open", "gnome-open", self._filename)
		
	def get_verb(self):
		return _("Open <b>%(name)s</b>")
		
class FolderMatch(handler.Match):
	def __init__(self, backend, prefix, absname):
		name = join(prefix, basename(absname))
		handler.Match.__init__(self, backend, name)
		
		self._filename = absname
		
	def action(self, text=None):
		os.spawnlp(os.P_NOWAIT, "nautilus", "nautilus", self._filename)
	
	def get_verb(self):
		return _("Open folder <b>%(name)s</b>")
				
class FileHandler(handler.Handler):
	def __init__(self):
		handler.Handler.__init__(self, "file.png")
		self._relative = True
		
	def get_priority(self):
		if self._relative:
			print PRIORITY/2+1
			return PRIORITY/2+1
		else:
			return PRIORITY+1
		
	def query(self, query, max=5):
		completions, prefix, self._relative = possible_completions(query, True)

		result = []
		for completion in completions:
			result.append(FileMatch(self, prefix, completion))
		
		return result[:max]
			
class FolderHandler(handler.Handler):
	def __init__(self):
		handler.Handler.__init__(self, "folder.png")
		self._relative = True
		
	def get_priority(self):
		if self._relative:
			return PRIORITY/2
		else:
			return PRIORITY
		
	def query(self, query, max=5):
		completions, prefix, self._relative = possible_completions(query)

		result = []
		for completion in completions:
			result.append(FolderMatch(self, prefix, completion))
		
		return result[:max]
	
def possible_completions(prefix, is_file=False):
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
	if prefix.startswith("~") and not prefix.startswith("~/"):
		prefix = join("~/", prefix[1:])
	
	# Now we see if the typed name matches exactly a file/directory, or
	# If we must take the parent directory and match the beginning of each file
	start = None
	path = normpath(abspath(expanduser(prefix)))		
	if not exists(path):
		# We are in ~/cvs/x for example, we strop the x and remember it in "start"
		prefix, start = split(prefix)
		path = normpath(abspath(expanduser(prefix)))	
		if not exists(path):
			# The parent dir wasn't a valid file, exit
			return ([], prefix, relative)
	
	# Now we list all files contained in path. Depending on the parameter we return all
	# files or all directories only. If there was a "start" we also match each name
	# to that prefix so typing ~/cvs/x will match in fact ~/cvs/x*
	return ([f
		for f in map(lambda x: join(path, x), os.listdir(path))
		if isfile(f) == is_file and not basename(f).startswith(".") and (start == None or basename(f).startswith(start))
	], prefix, relative)
