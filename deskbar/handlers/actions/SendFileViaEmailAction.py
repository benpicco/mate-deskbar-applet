import deskbar.interfaces.Action
from gettext import gettext as _
from os.path import exists
from deskbar.core.GconfStore import GconfStore
from deskbar.core.Utils import spawn_async

class SendFileViaEmailAction (deskbar.interfaces.Action):
    """
    Compose new e-mail in preferred mail client
    and add given file as attachment
    """
    
    def __init__(self, name, file_uri):
        deskbar.interfaces.Action.__init__(self, name)
        if file_uri.startswith("file://"):
            self._uri = file_uri
            self._file = file_uri.replace("file://", "")
        else:
            self._uri = "file://"+file_uri
            self._file = file_uri
            
    def get_hash(self):
        self._file
        
    def is_valid(self):
        return exists(self._file)
    
    def get_icon(self):
        return "stock_mail-compose"
    
    def activate(self, text=None):
        exe = GconfStore.get_instance().get_client().get_string("/desktop/gnome/url-handlers/mailto/command")
        exe = exe.replace(" %s", "") 
        if "thunderbird" in exe:
            cmd = ["--compose", "attachment=%s" % self._uri]
        else:
            # RFC 2368 mailto URI
            cmd = ["mailto:?attach=%s" % self._file]
        
        spawn_async([exe] + cmd)
   
    def get_verb(self):
        # translators: %s is a filename
        return _("Send %s via e-mail") % "<b>%(name)s</b>"