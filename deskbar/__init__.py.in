#!/usr/bin/env python

import gtk, gtk.gdk
import os, sys
from os.path import *

# Allow to use uninstalled deskbar
def _check(path):
	return exists(path) and isdir(path) and isfile(path+"/Makefile.am")

DEFAULT_WIDTH = 150

# Shared data dir is most the time /usr/share/deskbar-applet
name = join(dirname(__file__), '..', 'data')
if _check(name):
	SHARED_DATA_DIR = abspath(name)
else:
	SHARED_DATA_DIR = join("@DATADIR@", "deskbar-applets")
print "Data Dir: %s" % SHARED_DATA_DIR

#Path to images, icons
ART_DATA_DIR = join(SHARED_DATA_DIR, "art")

# HOME_DIR is the user's directory
HOME_DIR = expanduser("~")
# USER_DIR is where we store our infos
USER_DIR = expanduser("~/.gnome2/deskbar-applet")

if not exists(USER_DIR):
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
	# Fixme: use spawn here
	os.system(cmd + " &")

#-------------------------------------------------------------------------------
# Icons

ICON_SIZE = 12

def load_image(name, scale=True):
	name = escape_dots(name)
	
	n = join(ART_DATA_DIR, name)
	if exists(n):
		return load_image_by_filename(n, scale)
	if exists(n + ".png"):
		return load_image_by_filename(n + ".png", scale)
	if exists(n + ".ico"):
		return load_image_by_filename(n + ".ico", scale)
	if exists(n + ".xpm"):
		return load_image_by_filename(n + ".xpm", scale)
	
	n = join(USER_DIR, name)
	if exists(n):
		return load_image_by_filename(n, scale)
	if exists(n + ".png"):
		return load_image_by_filename(n + ".png", scale)
	if exists(n + ".ico"):
		return load_image_by_filename(n + ".ico", scale)
	if exists(n + ".xpm"):
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


GENERIC_IMAGE = load_image_by_filename(join(ART_DATA_DIR, "generic.png"))


DESKBAR_BIG_IMAGE     = load_image("deskbar-applet", False)
DESKBAR_IMAGE         = load_image("deskbar-applet-small")
FILE_IMAGE            = load_image("file")
FOLDER_IMAGE          = load_image("folder")
FOLDER_BOOKMARK_IMAGE = load_image("folder-bookmark")
MAIL_IMAGE            = load_image("mail")
WEB_IMAGE             = load_image("web")
WEB_BOOKMARK_IMAGE    = load_image("web-bookmark")
