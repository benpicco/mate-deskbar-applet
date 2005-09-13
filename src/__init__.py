import gnome
import gtk
import gtk.gdk
import os
import os.path


APP_NAME = "deskbar-applet"
VERSION = "0.4"

DEFAULT_WIDTH = 150

# SHARED_DATA_DIR ends in a "/"
SHARED_DATA_DIR = gnome.program_init(APP_NAME, VERSION).get_property(gnome.PARAM_GNOME_DATADIR) + "/deskbar-applet/"
# HOME_DIR does not
HOME_DIR = os.path.expanduser("~")
# USER_DIR ends in a "/"
USER_DIR = os.path.expanduser("~/.deskbar/")


if not os.path.exists(USER_DIR):
	os.makedirs(USER_DIR)


# This should be a string that rarely occurs naturally.
NO_CHECK_CAN_HANDLE = "nO_cHECK_cAN_hANDLE*"


def escape_dots(text):
	return text.replace(".", "_dot_").replace("`", "_backtick_")


def escape_markup(text):
	text = text.replace("&", "&amp;")
	text = text.replace("<", "&lt;")
	text = text.replace(">", "&gt;")
	return text


def ellipsize(text, length = 80):
	if len(text) <= length:
		return text
	else:
		x = (length / 2) - 6
		return text[:x] + " ... " + text[-x:]


def run_command(cmd, arg):
	arg = arg.replace("\"", "\\\"")
	cmd = cmd.replace("%s", arg)
	#print "  >>", cmd
	os.system(cmd + " &")


#-------------------------------------------------------------------------------
# Icons

ICON_SIZE = 12


def load_image(name, scale=True):
	name = escape_dots(name)
	
	n = SHARED_DATA_DIR + name
	if os.path.exists(n):
		return load_image_by_filename(n, scale)
	if os.path.exists(n + ".png"):
		return load_image_by_filename(n + ".png", scale)
	if os.path.exists(n + ".ico"):
		return load_image_by_filename(n + ".ico", scale)
	if os.path.exists(n + ".xpm"):
		return load_image_by_filename(n + ".xpm", scale)
	
	n = USER_DIR + name
	if os.path.exists(n):
		return load_image_by_filename(n, scale)
	if os.path.exists(n + ".png"):
		return load_image_by_filename(n + ".png", scale)
	if os.path.exists(n + ".ico"):
		return load_image_by_filename(n + ".ico", scale)
	if os.path.exists(n + ".xpm"):
		return load_image_by_filename(n + ".xpm", scale)
	
	return GENERIC_IMAGE


def load_image_by_filename(filename, scale=True):
	image = gtk.Image()
	image.set_from_file(filename)
	try:
		if scale:
			scaled = image.get_pixbuf().scale_simple(ICON_SIZE, ICON_SIZE, gtk.gdk.INTERP_BILINEAR)
			image.set_from_pixbuf(scaled)
		return image
	except:
		return GENERIC_IMAGE


GENERIC_IMAGE = load_image_by_filename(SHARED_DATA_DIR + "generic.png")


DESKBAR_BIG_IMAGE     = load_image("deskbar-applet", False)
DESKBAR_IMAGE         = load_image("deskbar-applet-small")
FILE_IMAGE            = load_image("file")
FOLDER_IMAGE          = load_image("folder")
FOLDER_BOOKMARK_IMAGE = load_image("folder-bookmark")
MAIL_IMAGE            = load_image("mail")
WEB_IMAGE             = load_image("web")
WEB_BOOKMARK_IMAGE    = load_image("web-bookmark")
