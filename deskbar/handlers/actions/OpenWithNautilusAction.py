from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from gettext import gettext as _
import gio

class OpenWithNautilusAction(OpenWithApplicationAction):
    """
    Open URI with Nautilus
    """
    
    NETWORK_URIS = ["http", "ftp", "smb", "sftp"]
    AUDIO_URIS = ["cdda"]
    
    def __init__(self, name, url):
        """
        @param url: URL including protocol
        (e.g. file://, http://, ftp://)
        """
        OpenWithApplicationAction.__init__(self, name, "nautilus", [url])
        self._url = url
    
    def get_icon(self):
        return "file-manager"
    
    def get_verb(self):
        uri_scheme = gio.File(uri=self._url).get_uri_scheme()
        
        if uri_scheme in self.NETWORK_URIS:
            return _("Open network place %s") % "<b>%(name)s</b>"
        elif uri_scheme in self.AUDIO_URIS:
            return _("Open audio disc %s") % "<b>%(name)s</b>"
        else:
            return _("Open location %s") % "<b>%(name)s</b>"
        
    def get_tooltip(self, text=None):
        return gio.File(uri=self._url).get_parse_name()