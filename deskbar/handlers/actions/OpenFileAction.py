from deskbar.core.Utils import url_show_file
from gettext import gettext as _
import deskbar.interfaces.Action
import gio
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
    
    def _get_unescaped_url_without_protocol(self):
        return gio.File(uri=self._url).get_path()
    
    def is_valid(self):
        gfile = gio.File (uri=self._url)

        if not gfile.query_exists():
            LOGGER.debug("File %s does not exist", gfile.get_uri ())
            return False
        else:
            try: 
                fileinfo = gfile.query_info("standard::content-type")
                returnval = gio.app_info_get_default_for_type(
                                fileinfo.get_content_type(), True) != None
            except Exception, e:
                # get_mime_type throws a RuntimeException when something went wrong
                returnval = False
        if not returnval:
            LOGGER.debug("File %s has no default application", gfile.get_uri ())
        return returnval
    
    def get_hash(self):
        return self._url
        
    def get_verb(self):
        return _("Open %s") % "<b>%(name)s</b>"
    
    def activate(self, text=None):
        url_show_file(self._url, escape=self._escape)
        
    def get_tooltip(self, text=None):
        return self._get_unescaped_url_without_protocol()
