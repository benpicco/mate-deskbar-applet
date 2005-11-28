import os, cgi
from os.path import *
import deskbar, deskbar.gnomedesktop
import gtk, gtk.gdk, gnome.ui

ICON_THEME = gtk.icon_theme_get_default()
factory = gnome.ui.ThumbnailFactory(deskbar.ICON_SIZE)

def more_information_dialog(title, content):
	message_dialog = gtk.MessageDialog(buttons=gtk.BUTTONS_CLOSE)
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
	# an icon that is too tall will make the EntryCompletion look funny
	if pixbuf != None and pixbuf.get_height() > size:
		pixbuf = pixbuf.scale_simple(size, size, gtk.gdk.INTERP_BILINEAR)
	return pixbuf
	
