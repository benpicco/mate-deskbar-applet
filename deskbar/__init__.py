import os
from os.path import join, exists, isdir, isfile, dirname, abspath, expanduser
import logging

LOGGER = logging.getLogger(__name__)

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
    
# Sets SHARED_DATA_DIR to local copy, or the tem location
# Shared data dir is most the time /usr/share/deskbar-applet
if UNINSTALLED_DESKBAR:
    SHARED_DATA_DIR = abspath(join(dirname(__file__), '..', 'data'))
else:
    SHARED_DATA_DIR = join(DATA_DIR, "deskbar-applet")
LOGGER.debug("Data Dir: %s" % SHARED_DATA_DIR)

HANDLERS_DIR = []
if UNINSTALLED_DESKBAR:
    HANDLERS_DIR += [abspath(join(dirname(__file__), 'handlers'))]

HANDLERS_DIR += [join(LIB_DIR, "deskbar-applet", "modules-2.20-compatible")]

USER_DESKBAR_DIR = expanduser("~/.gnome2/deskbar-applet")
if not exists(USER_DESKBAR_DIR):
    try:
        os.makedirs(USER_DESKBAR_DIR, 0744)
    except Exception , msg:
        LOGGER.error('Could not create user handlers dir (%s): %s' % (USER_DESKBAR_DIR, msg))
        
USER_HANDLERS_DIR = expanduser("~/.gnome2/deskbar-applet/modules-2.20-compatible")
if not exists(USER_HANDLERS_DIR):
    try:
        os.makedirs(USER_HANDLERS_DIR, 0744)
    except Exception , msg:
        LOGGER.error('Could not create user handlers dir (%s): %s' % (USER_HANDLERS_DIR, msg))
USER_HANDLERS_DIR = [USER_HANDLERS_DIR]

MODULES_DIRS = USER_HANDLERS_DIR+HANDLERS_DIR
LOGGER.debug("Handlers Dir: %s" % MODULES_DIRS)
# ------------------------------------------------------------------------------

# Set the cwd to the home directory so spawned processes behave correctly
# when presenting save/open dialogs
os.chdir(expanduser("~"))

# Path to images, icons
ART_DATA_DIR = join(SHARED_DATA_DIR, "art")
# Default icon size in the entry
ICON_WIDTH = 28
ICON_HEIGHT = 16

HISTORY_FILE = join(USER_DESKBAR_DIR, "history-2.20-compatible.pickle")

# FIXME: this , here ?
DEFAULT_RESULTS_PER_HANDLER = 6

# Global overrides for command line mode
UI_OVERRIDE = None
