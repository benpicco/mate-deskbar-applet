from deskbar.core.Utils import url_show_file
from gettext import gettext as _
from os.path import exists
import deskbar.interfaces.Action
import gnomevfs
import logging

LOGGER = logging.getLogger(__name__) 

class OpenFileAction(deskbar.interfaces.Action):
    """
    Open file with its preferred application
    """
    
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
    
    def _get_unesacped_url_without_protocol(self):
        url = self._url[7:]
        if not self._escape:
            url = gnomevfs.unescape_string_for_display(url)
        return url
    
    def is_valid(self):
        url = self._get_unesacped_url_without_protocol()

        if not exists(url):
            LOGGER.debug("File %s does not exist", url)
            return False
        else:
            try:
                mime_type = gnomevfs.get_mime_type(url)
                returnval = gnomevfs.mime_get_default_application(mime_type) != None
            except RuntimeError, e:
                # get_mime_type throws a RuntimeException when something went wrong
                returnval = False
        if not returnval:
            LOGGER.debug("File %s has no default application", url)
        return returnval
    
    def get_hash(self):
        return self._url
        
    def get_verb(self):
        return _("Open %s") % "<b>%(name)s</b>"
    
    def activate(self, text=None):
        url_show_file(self._url, escape=self._escape)
        
    def get_tooltip(self, text=None):
        return self._get_unesacped_url_without_protocol()
