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

HANDLERS_DIR = []
if UNINSTALLED_DESKBAR:
	HANDLERS_DIR += [abspath(join(dirname(__file__), 'handlers'))]

HANDLERS_DIR += [join(LIB_DIR, "deskbar-applet", "handlers")]

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
USER_HANDLERS_DIR = [USER_HANDLERS_DIR]

MODULES_DIRS = USER_HANDLERS_DIR+HANDLERS_DIR
print "Handlers Dir: %s" % MODULES_DIRS
# ------------------------------------------------------------------------------

# Set the cwd to the home directory so spawned processes behave correctly
# when presenting save/open dialogs
os.chdir(expanduser("~"))

# Path to images, icons
ART_DATA_DIR = join(SHARED_DATA_DIR, "art")
# Default icon size in the entry
ICON_WIDTH = 28
ICON_HEIGHT = 16

#Maximum number of history items
MAX_HISTORY = 25
HISTORY_FILE = join(USER_DESKBAR_DIR, "history.pickle")

# FIXME: this , here ?
DEFAULT_RESULTS_PER_HANDLER = 6

#Gconf client
GCONF_CLIENT = gconf.client_get_default()

# GConf directory for deskbar in window mode and shared settings
GCONF_DIR = "/apps/deskbar"

# GConf key to the per applet entry width setting
GCONF_WIDTH =  GCONF_DIR + "/width"
# GConf key to the per applet entry expand setting
GCONF_EXPAND = GCONF_DIR + "/expand"

# GConf key to the setting for the minimum number of chars of a query
GCONF_MINCHARS = GCONF_DIR + "/minchars"
# GConf key to the setting for time between keystroke in search entry, and actual search
GCONF_TYPINGDELAY = GCONF_DIR + "/typingdelay"
# GConf key to the setting whether to use selection clipboard when activating hotkey
GCONF_USE_SELECTION = GCONF_DIR + "/use_selection"
# GConf key for global keybinding
GCONF_KEYBINDING = GCONF_DIR + "/keybinding"
# GConf key clear the entry after a search result has been selected
GCONF_CLEAR_ENTRY = GCONF_DIR + "/clear_entry"

# GConf key for UI name
GCONF_UI_NAME = GCONF_DIR + "/ui_name"

ENTRIAC_UI_NAME = "Entriac"
CUEMIAC_UI_NAME = "Cuemiac"
WINDOW_UI_NAME = "Window"

# GConf key for list of enabled handlers, when uninstalled, use a debug key to not conflict
# with development version
if UNINSTALLED_DESKBAR:
	GCONF_ENABLED_HANDLERS = GCONF_DIR + "/enabled_handlers_debug"
else:
	GCONF_ENABLED_HANDLERS = GCONF_DIR + "/enabled_handlers"

# GConf key for collapsed categories in the cuemiac view
GCONF_COLLAPSED_CAT = GCONF_DIR + "/collapsed_cat"

# Preload gconf directories
GCONF_CLIENT.add_dir(GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)

# Global overrides for command line mode
UI_OVERRIDE = None
