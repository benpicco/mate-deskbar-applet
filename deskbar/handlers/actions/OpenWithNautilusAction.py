from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from gettext import gettext as _
from os.path import exists

class OpenWithNautilusAction(OpenWithApplicationAction):
    
    NETWORK_URIS = ["http", "ftp", "smb", "sftp"]
    AUDIO_URIS = ["cdda"]
    
    def __init__(self, name, url):
        OpenWithApplicationAction.__init__(self, name, "nautilus", [url])
        self._url = url
    
    def get_icon(self):
        return "file-manager"
      
    def is_valid(self):
    	return exists(self._url)
        
    def get_verb(self):
        uri_scheme = gnomevfs.get_uri_scheme(self._url)
        
        if uri_scheme in NETWORK_URIS:
            return _("Open network place %s") % "<b>%(name)s</b>"
        elif uri_scheme in AUDIO_URIS:
            return _("Open audio disc %s") % "<b>%(name)s</b>"
        else:
            return _("Open location %s") % "<b>%(name)s</b>"