from deskbar.core.Utils import get_xdg_data_dirs, spawn_async, load_icon
from deskbar.defs import VERSION
from gettext import gettext as _
from glob import glob
from os.path import join
import deskbar.interfaces.Action
import deskbar.interfaces.Module
import deskbar.interfaces.Match

HANDLERS = ["BeagleHandler"]

class SearchWithBeagleAction(deskbar.interfaces.Action):
    
    def __init__(self, name):
        deskbar.interfaces.Action.__init__(self, name)
    
    def activate(self, text=None):
        if not spawn_async(["beagle-search", self._name]):
            spawn_async(["best", '--no-tray', '--show-window', self._name])
    
    def get_verb(self):
        return _("Search for %s using Beagle") % "<b>%(name)s</b>"
    
    def get_icon(self):
        return "system-search"
        
class BeagleMatch(deskbar.interfaces.Match):
    def __init__(self, **args):
        deskbar.interfaces.Match.__init__(self, icon="system-search", category="actions", **args)
        self.add_action( SearchWithBeagleAction(self.get_name()) )
    
    def get_hash(self):
        return "beagle_static_"+self.get_name()
            
class BeagleHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': load_icon("system-search"),
            "name": _("Beagle"),
            "description": _("Search all of your documents (using Beagle)"),
            'version': VERSION,
            }
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
                
    def query(self, query):
        self._emit_query_ready(query, [BeagleMatch(name=query, priority=self.get_priority())] )
    
    @staticmethod
    def has_requirements():
        #FIXME: better way to detect beagle ?
        for dir in get_xdg_data_dirs():
            if glob(join(dir, "applications", "*best.desktop")) or glob(join(dir, "applications", "*beagle-search.desktop")):
                return True
        BeagleHandler.INSTRUCTIONS = _("Beagle does not seem to be installed.")
        return False
