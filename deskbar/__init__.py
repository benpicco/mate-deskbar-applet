import os, sys
from os.path import join, exists, isdir, isfile, dirname, abspath, expanduser

import gtk, gtk.gdk, gconf

# Autotools set the actual data_dir in defs.py
from defs import *

try:
	# Allows to load uninstalled .la libs
	import ltihooks
except ImportError:
	pass

# Allow to use uninstalled deskbar ---------------------------------------------
UNINSTALLED_DESKBAR = False
def _check(path):
	return exists(path) and isdir(path) and isfile(path+"/AUTHORS")
	
name = join(dirname(__file__), '..')
if _check(name):
	UNINSTALLED_DESKBAR = True
	
# Sets SHARED_DATA_DIR to local copy, or the system location
# Shared data dir is most the time /usr/share/deskbar-applet
if UNINSTALLED_DESKBAR:
	SHARED_DATA_DIR = abspath(join(dirname(__file__), '..', 'data'))
else:
	SHARED_DATA_DIR = join(DATA_DIR, "deskbar-applet")
print "Data Dir: %s" % SHARED_DATA_DIR

if UNINSTALLED_DESKBAR:
	HANDLERS_DIR = abspath(join(dirname(__file__), 'handlers'))
else:
	HANDLERS_DIR = join(LIB_DIR, "deskbar-applet", "handlers")
print "Handlers Dir: %s" % HANDLERS_DIR

USER_DESKBAR_DIR = expanduser("~/.gnome2/deskbar-applet")
if not exists(USER_DESKBAR_DIR):
	try:
		os.makedirs(USER_DESKBAR_DIR, 0744)
	except Exception , msg:
		print 'Error:could not create user handlers dir (%s): %s' % (USER_DESKBAR_DIR, msg)
		
USER_HANDLERS_DIR = expanduser("~/.gnome2/deskbar-applet/handlers")
if not exists(USER_HANDLERS_DIR):
	try:
		os.makedirs(USER_HANDLERS_DIR, 0744)
	except Exception , msg:
		print 'Error:could not create user handlers dir (%s): %s' % (USER_HANDLERS_DIR, msg)

MODULES_DIRS = [HANDLERS_DIR, USER_HANDLERS_DIR]
# ------------------------------------------------------------------------------

# Set the cwd to the home directory so spawned processes behave correctly
# when presenting save/open dialogs
os.chdir(expanduser("~"))

# Path to images, icons
ART_DATA_DIR = join(SHARED_DATA_DIR, "art")
# Default icon size in the entry
ICON_SIZE = 16

#Maximum number of history items
MAX_HISTORY = 25
HISTORY_FILE = join(USER_DESKBAR_DIR, "history.pickle")

# FIXME: this , here ?
MAX_RESULTS_PER_HANDLER = 6

#Gconf client
GCONF_CLIENT = gconf.client_get_default()

# GConf directory for deskbar in window mode and shared settings
GCONF_DIR = "/apps/deskbar"

# GConf key to the per applet entry width setting
GCONF_WIDTH =  GCONF_DIR + "/width"
# GConf key to the per applet entry expand setting
GCONF_EXPAND = GCONF_DIR + "/expand"

# GConf key for global keybinding
GCONF_KEYBINDING = GCONF_DIR + "/keybinding"

# GConf key for list of enabled handlers, when uninstalled, use a debug key to not conflict
# with development version
if UNINSTALLED_DESKBAR:
	GCONF_ENABLED_HANDLERS = GCONF_DIR + "/enabled_handlers_debug"
else:
	GCONF_ENABLED_HANDLERS = GCONF_DIR + "/enabled_handlers"
	
# Preload gconf directories
GCONF_CLIENT.add_dir(GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)
