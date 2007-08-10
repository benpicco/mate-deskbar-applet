from gettext import gettext as _
import gtk

import deskbar
import deskbar.interfaces.Module
import deskbar.interfaces.Match

from deskbar.handlers.actions.OpenFileAction import OpenFileAction
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.SendFileViaEmailAction import SendFileViaEmailAction
from deskbar.defs import VERSION

HANDLERS = ["RecentHandler"]

class OpenRecentAction(OpenFileAction):
    
    def __init__(self, name, url):
        OpenFileAction.__init__(self, name, url, escape=False)

    def skip_history(self):
        return True

class RecentMatch(deskbar.interfaces.Match):
    def __init__(self, recent_infos, **args):
        deskbar.interfaces.Match.__init__(self, pixbuf=recent_infos.get_icon(deskbar.ICON_HEIGHT), name=recent_infos.get_display_name(), **args)        
        self.recent_infos = recent_infos
        self.add_action( OpenRecentAction(self.get_name(), self.recent_infos.get_uri()) )
        self.add_action( CopyToClipboardAction( _("Location"), self.recent_infos.get_uri()) )
        self.add_action( SendFileViaEmailAction(self.get_name(), self.recent_infos.get_uri()) )

    def is_valid(self, text=None):
        return self.recent_infos.exists()

    def get_hash(self, text=None):
        return self.recent_infos.get_uri()
    
class RecentHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon(gtk.STOCK_FILE),
            "name": _("Recent Documents"),
            "description": _("Retrieve your recently accessed files and locations"),
             "version": VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self._recent_manager = gtk.recent_manager_get_default()
        
    def query(self, query):
        result = []
        for recent in self._recent_manager.get_items():
            if not recent.get_display_name().lower().startswith(query): continue
            if not recent.exists(): continue
            result.append (RecentMatch (recent, category="files", priority=self.get_priority()))
        self._emit_query_ready(query, result )
            
    @staticmethod
    def has_requirements():
        if gtk.pygtk_version >= (2,9,0):
            return True
        RecentHandler.INSTRUCTIONS = _("This handler requires a more recent gtk version (2.9.0 or newer).")
        return False