import os
from os.path import *

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
