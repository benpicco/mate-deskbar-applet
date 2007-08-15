import deskbar.interfaces.Action
from gettext import gettext as _
from deskbar.core.Utils import url_show_file

class OpenFileAction(deskbar.interfaces.Action):
    
    def __init__(self, name, url, escape=True):
        """
        @param uri: URI pointing to the file.
        (has to start with 'file://')
        @param escape: Whether to escape the URI
        """
        deskbar.interfaces.Action.__init__(self, name)
        self._url = url
        self._escape = escape
    
    def get_icon(self):
        return "gtk-open"
    
    def get_hash(self):
        return self._url
        
    def get_verb(self):
        return _("Open %s") % "<b>%(name)s</b>"
    
    def activate(self, text=None):
        url_show_file(self._url, escape=self._escape)