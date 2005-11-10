import os
from os.path import *
import deskbar, deskbar.gnomedesktop
import gtk, gnome.ui

ICON_THEME = gtk.icon_theme_get_default()
factory = gnome.ui.ThumbnailFactory(deskbar.ICON_SIZE)

def get_xdg_data_dirs():
	dirs = os.getenv("XDG_DATA_HOME")
	if dirs == None:
		dirs = expanduser("~/.local/share")
	
	sysdirs = os.getenv("XDG_DATA_DIRS")
	if sysdirs == None:
		sysdirs = "/usr/local/share:/usr/share"
	
	dirs = "%s:%s" % (dirs, sysdirs)
	return [dir for dir in dirs.split(":") if dir.strip() != "" and exists(dir)]

def load_icon_for_file(f):
	icon_name, flags = gnome.ui.icon_lookup(ICON_THEME, factory,
				f, "",
				gnome.ui.ICON_LOOKUP_FLAGS_SHOW_SMALL_IMAGES_AS_THEMSELVES)
		
	return load_icon(icon_name)

def load_icon_for_desktop_icon(icon):
	if icon != None:
		icon = deskbar.gnomedesktop.find_icon(ICON_THEME, icon, deskbar.ICON_SIZE, 0)
		if icon != None:
			return load_icon(icon)
		
# We load the icon file, and if it fails load an empty one
# If the iconfile is a path starting with /, load the file
# else try to load a stock or named icon name
def load_icon(icon, size=deskbar.ICON_SIZE):
	pixbuf = None
	if icon != None and icon != "":
		try:
			our_icon = join(deskbar.ART_DATA_DIR, icon)
			if exists(our_icon):
				pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(our_icon, size, size)
			elif icon.startswith("/"):
				pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon, size, size)
			else:
				pixbuf = ICON_THEME.load_icon(splitext(icon)[0], size, gtk.ICON_LOOKUP_USE_BUILTIN)
		except Exception, msg1:
			try:
				pixbuf = ICON_THEME.load_icon(icon, size, gtk.ICON_LOOKUP_USE_BUILTIN)
			except Exception, msg2:
				print 'Error:load_icon:Icon Load Error:%s (%s)' % (msg1, msg2)
	return pixbuf
	
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
