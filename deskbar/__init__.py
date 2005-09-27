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
# ------------------------------------------------------------------------------

# SEt the cwd to the home directory so spawned processes behave correctly
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
# GConf key to the entr width setting
GCONF_WIDTH = GCONF_DIR + "/width"
# Preload gconf directories
GCONF_CLIENT.add_dir(deskbar.GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)
