import deskbar.interfaces.Action
from gettext import gettext as _
import gtk

class CopyToClipboardAction(deskbar.interfaces.Action):
    """
    Copy given text to clipboard
    """
    
    def __init__(self, name, text):
        deskbar.interfaces.Action.__init__(self, name)
        self._text = text
        
    def get_icon(self):
        return "gtk-copy"
        
    def get_verb(self):
        return _("Copy <b>%(name)s</b> to clipboard")
    
    def activate(self, text=None):
        cb = gtk.clipboard_get()
        cb.set_text(self._text)
        cb.store()