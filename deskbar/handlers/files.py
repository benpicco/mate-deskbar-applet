import os
from os.path import join, basename, normpath, abspath, dirname
from os.path import split, expanduser, exists, isfile

from gettext import gettext as _

import gobject
import gtk, gnome.ui
import deskbar, deskbar.Indexer
import deskbar.Handler

HANDLERS = {
	"FileFolderHandler" : {
		"name": _("Files and Folders"),
		"description": _("Open your files and folders by name"),
	},
}

class FileMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, absname=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		self._icon = deskbar.Utils.load_icon_for_file(absname)
		
		self.absname = absname
				
	def action(self, text=None):
		gobject.spawn_async(["gnome-open", self.absname], flags=gobject.SPAWN_SEARCH_PATH)
		
	def get_category(self):
		return "files"
		
	def get_verb(self):
		return _("Open %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.absname

class FolderMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, absname=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		
		self.absname = absname
		
	def action(self, text=None):
		gobject.spawn_async(["nautilus", self.absname], flags=gobject.SPAWN_SEARCH_PATH)
	
	def get_category(self):
		return "Files"
	
	def get_verb(self):
		return _("Open folder %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.absname
		
class FileFolderHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "stock_my-documents")
				
	def query(self, query, max):
		result = []
		result += self.query_filefolder(query, False)[:max]
		result += self.query_filefolder(query, True)[:max]
		return result
	
	def query_filefolder(self, query, is_file):
		completions, prefix, relative = filesystem_possible_completions(query, is_file)
		if is_file:
			return [FileMatch(self, join(prefix, basename(completion)), completion) for completion in completions]
		else:
			return [FolderMatch(self, join(prefix, basename(completion)), completion) for completion in completions]
			
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
	if prefix.startswith("~") and not prefix.startswith("~/"):
		prefix = join("~/", prefix[1:])
	if prefix.endswith("/"):
		prefix = prefix[:-1]
		
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
	if isfile(path):
		if is_file:
			return ([path], dirname(prefix), relative)
		else:
			return ([], prefix, relative)
			
	return ([f
		for f in map(lambda x: join(path, x), os.listdir(path))
		if isfile(f) == is_file and not basename(f).startswith(".") and (start == None or basename(f).startswith(start))
	], prefix, relative)

