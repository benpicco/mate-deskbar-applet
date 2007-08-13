import deskbar.interfaces.Action
import deskbar.core.gnomedesktop
from deskbar.core.Utils import get_xdg_data_dirs
from os.path import join, exists
from gettext import gettext as _

class OpenDesktopFileAction(deskbar.interfaces.Action):
    
    def __init__(self, name, desktop, desktop_file):
        deskbar.interfaces.Action.__init__(self, name)
        self._desktop = desktop
        self._desktop_file = desktop_file
    
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["_desktop"]
        return state
    
    def __setstate__(self, state):
        self.__dict__ = state
        self._desktop = parse_desktop_filename(self._desktop_file)
    
    def get_icon(self):
        return "gtk-open"
    
    def get_verb(self):
        #translators: First %s is the programs full name, second is the executable name
        #translators: For example: Launch Text Editor (gedit)
        return _("Launch <b>%(name)s</b>")
    
    def activate(self, text=None):
        try:
            self._desktop.launch([])
        except Exception, e:
            #FIXME: Proper dialog here. Also see end of Utils.py
            print 'Warning:Could not launch .desktop file:', e
            
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
        desktop = deskbar.core.gnomedesktop.item_new_from_file(desktop, deskbar.core.gnomedesktop.LOAD_ONLY_IF_EXISTS)
    except Exception, e:
        print 'Couldn\'t read desktop file:%s:%s' % (desktop, e)
        return None
    
    if desktop == None or desktop.get_entry_type() != deskbar.core.gnomedesktop.TYPE_APPLICATION:
        return None
    if desktop.get_boolean(deskbar.core.gnomedesktop.KEY_TERMINAL):
        return None
    if only_if_visible and desktop.get_boolean(deskbar.core.gnomedesktop.KEY_NO_DISPLAY):
        return None
        
    return desktop