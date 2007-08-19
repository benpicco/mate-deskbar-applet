from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from gettext import gettext as _
import gnomevfs

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
        uri_scheme = gnomevfs.get_uri_scheme(self._url)
        
        if uri_scheme in self.NETWORK_URIS:
            return _("Open network place %s") % "<b>%(name)s</b>"
        elif uri_scheme in self.AUDIO_URIS:
            return _("Open audio disc %s") % "<b>%(name)s</b>"
        else:
            return _("Open location %s") % "<b>%(name)s</b>"