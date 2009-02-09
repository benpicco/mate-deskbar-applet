import deskbar.interfaces.Action
from gettext import gettext as _
from deskbar.core.Utils import url_show, uri_has_default_handler
import cgi

class ShowUrlAction(deskbar.interfaces.Action):
    """
    Open an arbitrary URL
    """
    
    def __init__(self, name, url):
        deskbar.interfaces.Action.__init__(self, name)
        self._url = url
    
    def get_icon(self):
        if self._url.startswith("http") or self._url.startswith("ftp"):
            return "stock_internet"
        else:
            return "gtk-open"
        
    def get_hash(self):
        return self._url
        
    def get_verb(self):
        return _("Open %s") % "<b>%(name)s</b>" 
    
    def activate(self, text=None):
        url_show(self._url)
        
    def get_tooltip(self, text=None):
        return cgi.escape(self._url)
    
    def is_valid(self):
        return uri_has_default_handler(self._url)