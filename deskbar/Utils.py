import os, cgi, re
from os.path import *
import deskbar, deskbar.gnomedesktop
import gtk, gtk.gdk, gnome.ui, gobject
from htmlentitydefs import name2codepoint

ICON_THEME = gtk.icon_theme_get_default()
factory = gnome.ui.ThumbnailFactory(deskbar.ICON_HEIGHT)

# This pattern matches a character entity reference (a decimal numeric
# references, a hexadecimal numeric reference, or a named reference).
charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')

def htmldecode(text):
	"""Decode HTML entities in the given text."""
	if type(text) is unicode:
		uchr = unichr
	else:
		uchr = lambda value: value > 255 and unichr(value) or chr(value)
	
	def entitydecode(match, uchr=uchr):
		entity = match.group(1)
		if entity.startswith('#x'):
			return uchr(int(entity[2:], 16))
		elif entity.startswith('#'):
			return uchr(int(entity[1:]))
		elif entity in name2codepoint:
			return uchr(name2codepoint[entity])
		else:
			return match.group(0)
	
	return charrefpat.sub(entitydecode, text)

def strip_html(string):
	return re.sub(r"<.*?>|</.*?>","",string)
	
def more_information_dialog(parent, title, content):
	message_dialog = gtk.MessageDialog(parent=parent, buttons=gtk.BUTTONS_CLOSE)
	message_dialog.set_markup("<span size='larger' weight='bold'>%s</span>\n\n%s" % (cgi.escape(title), cgi.escape(content)))
	resp = message_dialog.run()
	if resp == gtk.RESPONSE_CLOSE:
		message_dialog.destroy()
		
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
		icon = deskbar.gnomedesktop.find_icon(ICON_THEME, icon, deskbar.ICON_HEIGHT, 0)
		if icon != None:
			return load_icon(icon)
		
# We load the icon file, and if it fails load an empty one
# If the iconfile is a path starting with /, load the file
# else try to load a stock or named icon name
def load_icon(icon, width=deskbar.ICON_HEIGHT, height=deskbar.ICON_HEIGHT):
	pixbuf = None
	if icon != None and icon != "":
		try:
			our_icon = join(deskbar.ART_DATA_DIR, icon)
			if exists(our_icon):
				pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(our_icon, width, height)
			elif icon.startswith("/"):
				pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon, width, height)
			else:
				pixbuf = ICON_THEME.load_icon(splitext(icon)[0], width, gtk.ICON_LOOKUP_USE_BUILTIN)
		except Exception, msg1:
			try:
				pixbuf = ICON_THEME.load_icon(icon, width, gtk.ICON_LOOKUP_USE_BUILTIN)
			except Exception, msg2:
				print 'Error:load_icon:Icon Load Error:%s (or %s)' % (msg1, msg2)
				
	# an icon that is too tall will make the EntryCompletion look funny
	if pixbuf != None and pixbuf.get_height() > height:
		pixbuf = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
	return pixbuf

PATH = [path for path in os.getenv("PATH").split(os.path.pathsep) if path.strip() != "" and exists(path) and isdir(path)]
def is_program_in_path(program):
	for path in PATH:
		prog_path = join(path, program)
		if exists(prog_path) and isfile(prog_path) and os.access(prog_path, os.F_OK | os.R_OK | os.X_OK):
			return True

def spawn_async(args):
	try:
		gobject.spawn_async(args, flags=gobject.SPAWN_SEARCH_PATH)
		return True
	except Exception, e:
		# FIXME: Proper dialog support here..
		print 'Warning:Unable to execute process:', e
		return False
