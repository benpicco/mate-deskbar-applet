import deskbar.interfaces.Action
from gettext import gettext as _
from deskbar.core.Utils import url_show_file
from os.path import exists
import gnomevfs

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
    
    def is_valid(self):
        url = self._url[7:]
        if not self._escape:
            url = gnomevfs.unescape_string_for_display(url)
        return exists( url )
    
    def get_hash(self):
        return self._url
        
    def get_verb(self):
        return _("Open %s") % "<b>%(name)s</b>"
    
    def activate(self, text=None):
        url_show_file(self._url, escape=self._escape)