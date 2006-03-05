import os
from os.path import join, basename, normpath, abspath, dirname
from os.path import split, expanduser, exists, isfile, isdir

from gettext import gettext as _

import gobject
import gtk, gnome, gnome.ui
import deskbar, deskbar.Indexer
import deskbar.Handler

from threading import Thread

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
		gnome.url_show(self.absname)
		
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
		gnome.url_show(self.absname)
	
	def get_category(self):
		return "places"
	
	def get_verb(self):
		return _("Open folder %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.absname
		
class FileFolderHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, gtk.STOCK_OPEN)
		self.cache = {}
		
	def initialize(self):
		# Disables the file indexing functionnality as it's too slow
		pass
#		def add_files(files):
#			for f in files:
#				self.cache[basename(f).lower()] = f
#			
#		def add_files_dirs(dir, depth=0):
#			if depth >= 4:
#				return
#			
#			files = []
#			for f in os.listdir(dir):
#				if f.startswith("."):
#					continue
#					
#				f = join(dir, f)
#				if isdir(f):
#					add_files_dirs(f, depth+1)
#				
#				files.append(f)
#			
#			gobject.idle_add(add_files, files)
#		
#		Thread (None, add_files_dirs, args=(abspath(expanduser("~")),)).start ()

		
	def query(self, query):
		
		result = []
		result += self.query_filefolder(query, False)
		result += self.query_filefolder(query, True)
		
#		query = query.lower()
#		for key, absname in self.cache.items():
#			if len(result) >= 50:
#				break
#			
#			if not exists(absname):
#				del self.cache[key]
#				continue
#			
#			if key.startswith(query):
#				if isdir(absname):
#					result += [FolderMatch(self, basename(absname), absname)]
#				else:
#					result += [FileMatch(self, basename(absname), absname)]
#				
		return result
	
	def query_filefolder(self, query, is_file):
		completions, prefix, relative = filesystem_possible_completions(query, is_file)
		if is_file:
			return [FileMatch(self, join(prefix, basename(completion)), "file://"+completion) for completion in completions]
		else:
			return [FolderMatch(self, join(prefix, basename(completion)), "file://"+completion) for completion in completions]
			
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
