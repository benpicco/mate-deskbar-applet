import os, sys
from os.path import join, exists, isdir, isfile, dirname, abspath, expanduser

import gtk, gtk.gdk, gconf

# Autotools set the actual data_dir in defs.py
from deskbar.defs import *

try:
	# Allows to load uninstalled .la libs
	import deskbar.ltihooks
except ImportError:
	pass

# Allow to use uninstalled deskbar ---------------------------------------------
# Sets SHARED_DATA_DIR to local copy, or the system location
def _check(path):
	return exists(path) and isdir(path) and isfile(path+"/Makefile.am")

# Shared data dir is most the time /usr/share/deskbar-applet
name = join(dirname(__file__), '..', 'data')
if _check(name):
	SHARED_DATA_DIR = abspath(name)
else:
	SHARED_DATA_DIR = join(DATA_DIR, "deskbar-applet")
print "Data Dir: %s" % SHARED_DATA_DIR

name = join(dirname(__file__), 'handlers')
if _check(name):
	HANDLERS_DIR = abspath(name)
else:
	HANDLERS_DIR = join(LIB_DIR, "deskbar-applet", "handlers")
print "Handlers Dir: %s" % HANDLERS_DIR

MODULES_DIRS = [HANDLERS_DIR, expanduser("~/.gnome2/deskbar-applet/handlers")]
# ------------------------------------------------------------------------------

# Set the cwd to the home directory so spawned processes behave correctly
# when presenting save/open dialogs
os.chdir(expanduser("~"))

# Path to images, icons
ART_DATA_DIR = join(SHARED_DATA_DIR, "art")
# Default icon size in the entry
ICON_SIZE = 16

#Gconf client
GCONF_CLIENT = gconf.client_get_default()
# GConf directory for deskbar
GCONF_DIR = "/apps/deskbar"
# GConf key to the entry width setting
GCONF_WIDTH = GCONF_DIR + "/width"
# GConf key to the entry expand setting
GCONF_EXPAND = GCONF_DIR + "/expand"
# GConf key for global keybinding
GCONF_KEYBINDING = GCONF_DIR + "/keybinding"
# GConf key for list of enabled handlers
GCONF_ENABLED_HANDLERS = GCONF_DIR + "/enabled_handlers"
# Preload gconf directories
GCONF_CLIENT.add_dir(deskbar.GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)
