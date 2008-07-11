import os
import shutil
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
    
# From pyxdg
_home = os.environ.get('HOME', '/')
XDG_DATA_HOME = os.environ.get('XDG_DATA_HOME',
            os.path.join(_home, '.local', 'share'))
XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME',
            os.path.join(_home, '.config'))
    
# Sets SHARED_DATA_DIR to local copy, or the tem location
# Shared data dir is most the time /usr/share/deskbar-applet
if UNINSTALLED_DESKBAR:
    SHARED_DATA_DIR = abspath(join(dirname(__file__), '..', 'data'))
else:
    SHARED_DATA_DIR = join(DATA_DIR, "deskbar-applet")
LOGGER.debug("Data Dir: %s", SHARED_DATA_DIR)

HANDLERS_DIR = []
if UNINSTALLED_DESKBAR:
    HANDLERS_DIR += [abspath(join(dirname(__file__), 'handlers'))]

HANDLERS_DIR += [join(LIB_DIR, "deskbar-applet", "modules-2.20-compatible")]

OLD_USER_DESKBAR_DIR = expanduser("~/.gnome2/deskbar-applet")
USER_CONFIG_DIR = join(XDG_CONFIG_HOME, "deskbar-applet")
        
USER_DATA_DIR = join(XDG_DATA_HOME, "deskbar-applet")
USER_HANDLERS_DIR = join(USER_DATA_DIR, "modules-2.20-compatible")

if not (exists(USER_DATA_DIR) and exists(USER_CONFIG_DIR)):
    error = False
    
    if not exists(USER_CONFIG_DIR):
        try:
            os.makedirs(USER_CONFIG_DIR, 0744)
        except Exception , msg:
            LOGGER.error('Could not create user handlers dir (%s): %s', USER_CONFIG_DIR, msg)
            error = True
    
    if not exists(USER_HANDLERS_DIR):
        try:
            os.makedirs(USER_HANDLERS_DIR, 0744)
        except Exception , msg:
            LOGGER.error('Could not create user handlers dir (%s): %s', USER_HANDLERS_DIR, msg)
            error = True
            
    if not error and exists(OLD_USER_DESKBAR_DIR):
        # Move files from old ~/.gnome2 directory to fd.o compliant dirs
        for root, dirs, files in os.walk(OLD_USER_DESKBAR_DIR):
            if "modules-2.20-compatible" in root:
                destdir = USER_HANDLERS_DIR
            else:
                destdir = USER_CONFIG_DIR
            
            for name in files:
                filepath = join(root, name)
                LOGGER.debug("Copying %s to %s", filepath, destdir)
                shutil.copy (filepath, destdir)
            
USER_HANDLERS_DIR = [USER_HANDLERS_DIR]

MODULES_DIRS = USER_HANDLERS_DIR+HANDLERS_DIR
LOGGER.debug("Handlers Dir: %s", MODULES_DIRS)
# ------------------------------------------------------------------------------

# Set the cwd to the home directory so spawned processes behave correctly
# when presenting save/open dialogs
os.chdir(expanduser("~"))

# Path to images, icons
ART_DATA_DIR = join(SHARED_DATA_DIR, "art")
# Default icon size in the entry
ICON_WIDTH = 28
ICON_HEIGHT = 16

HISTORY_FILE = join(USER_DATA_DIR, "history-2.20-compatible.pickle")

# FIXME: this , here ?
DEFAULT_RESULTS_PER_HANDLER = 6

# Global overrides for command line mode
UI_OVERRIDE = None

WINDOW_UI_NAME = "Window"
BUTTON_UI_NAME = "Button"
