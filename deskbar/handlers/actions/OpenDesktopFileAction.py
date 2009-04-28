from deskbar.core.Utils import get_xdg_data_dirs
from gettext import gettext as _
from os.path import join, exists
import gnomedesktop
import deskbar.interfaces.Action
import logging

LOGGER = logging.getLogger(__name__)

class OpenDesktopFileAction(deskbar.interfaces.Action):
    """
    Retrieve information about an application from
    its .desktop file
    """
    
    def __init__(self, name, desktop, desktop_file, executable):
        """
        @type desktop: L{gnomedesktop.DesktopItem}
        @type desktop_file: path pointing to .desktop file
        @param executeable: Name of the executeable for display 
        """
        deskbar.interfaces.Action.__init__(self, name)
        self._desktop = desktop
        self._desktop_file = desktop_file
        self._prog = executable
    
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["_desktop"]
        return state
    
    def __setstate__(self, state):
        self.__dict__ = state
        self._desktop = parse_desktop_filename(self._desktop_file)
    
    def is_valid(self):
        return exists(self._desktop_file)
    
    def get_icon(self):
        if self._desktop != None:
            return self._desktop.get_string(gnomedesktop.KEY_ICON)
        else:
            return "gtk-open"
    
    def get_name(self, text=None):
        name_dict = {"name": self._name}
        # Be compatible with previous versions
        if hasattr(self, "_prog"):
            name_dict["prog"] = self._prog
        else:
            name_dict["prog"] = ""
        return name_dict
    
    def get_verb(self):
        #translators: First %s is the programs full name, second is the executable name
        #translators: For example: Launch Text Editor (gedit)
        return _("Launch <b>%(name)s</b> (%(prog)s)")
    
    def activate(self, text=None):
        try:
            self._desktop.launch([])
        except Exception, e:
            #FIXME: Proper dialog here. Also see end of Utils.py
            LOGGER.warning('Could not launch .desktop file:')
            LOGGER.exception(e)
            
def parse_desktop_filename(desktop, only_if_visible=True):
    if desktop[0] == "/" and exists(desktop):
        return parse_desktop_file(desktop, only_if_visible)
            
    for dir in get_xdg_data_dirs():
        f = join(dir, "applications", desktop)
        if exists(f):
            return parse_desktop_file(f, only_if_visible)
    
    return None

def parse_desktop_file(desktop, only_if_visible=True):
    try:
        desktop = gnomedesktop.item_new_from_file(desktop, gnomedesktop.LOAD_ONLY_IF_EXISTS)
    except Exception, e:
        LOGGER.warning('Couldn\'t read desktop file %s:', desktop)
        LOGGER.exception(e)
        return None
    
    if desktop == None or desktop.get_entry_type() != gnomedesktop.TYPE_APPLICATION:
        return None
    if desktop.get_boolean(gnomedesktop.KEY_TERMINAL):
        return None
    if only_if_visible and desktop.get_boolean(gnomedesktop.KEY_NO_DISPLAY):
        return None
        
    return desktop