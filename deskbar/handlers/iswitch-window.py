from deskbar.defs import VERSION
from gettext import gettext as _
import deskbar.interfaces.Module
import deskbar.interfaces.Match
import deskbar.interfaces.Action
import deskbar
import gtk
import logging
import wnck

LOGGER = logging.getLogger(__name__)
HANDLERS = ["ISwitchWindowHandler"]

class SwitchToWindowAction(deskbar.interfaces.Action):
    
    def __init__(self, name, window):
        deskbar.interfaces.Action.__init__(self, name)
        self._window = window
    
    def get_verb(self):
        return _("Switch to <b>%(name)s</b>")

    def activate(self, text=None):
        if self._window.is_active():
            return
        
        try:
            time = gtk.get_current_event().time
        except:
            LOGGER.warning("Using bogus timestamp.")
            time = gtk.get_current_event_time()
        
        workspace = self._window.get_workspace()
        if workspace != None and workspace.is_virtual():
            if not self._window.is_in_viewport(workspace):
                pos_x = workspace.get_viewport_x() + self._window.get_geometry()[0]
                pos_y = workspace.get_viewport_y() + self._window.get_geometry()[1]
                self._window.get_screen().move_viewport(pos_x, pos_y)

        if hasattr(self._window.get_workspace(), 'activate') and self._window.get_workspace() != self._window.get_screen().get_active_workspace():
            self._window.get_workspace().activate(time)

        self._window.activate(time)    

    def skip_history(self):
        return True

class ISwitchWindowMatch(deskbar.interfaces.Match):
    def __init__(self, window=None, **args):
        deskbar.interfaces.Match.__init__ (self, category="windows", **args)
        self.add_action( SwitchToWindowAction(self.get_name(), window) )

    def get_hash(self):
        return self.get_name()
    
class ISwitchWindowHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("gnome-panel-window-menu.png"),
             "name": _("Window Switcher"),
             "description": _("Switch to an existing window by name."),
             "version": VERSION,
             "categories" : {
                "windows"    : {    "name": _("Windows"), }
                }
             }
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)

    def query(self, query):
        results = []
        query = query.lower()
        for w in wnck.screen_get_default().get_windows_stacked():
                if w.is_skip_tasklist():
                        continue
                
                for name in (w.get_name().lower(), w.get_application().get_name().lower()):
                        if name.find(query) != -1:
                                results.append( ISwitchWindowMatch(name=name, window=w, pixbuf=w.get_mini_icon(), priority=self.get_priority()) )
                                break

        self._emit_query_ready(query, results )
