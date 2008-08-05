from deskbar.core.GconfStore import GconfStore
from deskbar.core.Utils import strip_html, get_proxy, load_base64_icon
from deskbar.core.Web import GnomeURLopener, Account, AccountDialog, ConcurrentRequestsException
from deskbar.defs import VERSION
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from xml.sax.saxutils import unescape
import deskbar
import deskbar.interfaces.Action
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gtk
import gobject
import logging
import urllib

LOGGER = logging.getLogger (__name__)

TWITTER_UPDATE_URL = "http://twitter.com/statuses/update.xml"

# Base64 encoded Twitter logo
TWITTER_ICON = \
"""iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAcVJREFUOI2FkztuFEEQhr/q7nnIa2GQVgiDCYCEAzhAHMY3gASJgAtwAXLuQ0AGRiQbOEBeGdsy4PXOTNdPMLOrWVbCJVXUVf+ru42h2pzVZEdmBEQwo07JuKUSgEta5szMjfNOTKLxvIDsrhjCf0ESABJXDl+WHTVw0sE0JB7gtwkYAIBG4mcWCVgCGTA5N22rngTMjBiMFKNtATjwx0Vh0Am+NpmzGPB+FwBDPEzQdFll6kESQAjBZjetfrsozDDEp0U3MmBrmAS8uldvW8jAlaBESGvVYIZJgDAz5tmZuzYB3F3fl5kLd+oRoQbZq/FO4mkZeFKETQADMuLSndqM6yxe3605rBJLaW0gI6YxUo6uNq0sNoK5i12DXy52gjExcSdFGCw5kP55FwH68wI4dXHiYubiW+skA7n3AxK44xoFMA7xcWGUZhxngcHbiwVnueIgBroVO/CyTuN91nKUO72/bHh3fg1xCGmDTCBjPxqfD/bYL/t3sI7TLfBmr+Jot4LO+9SCjTpANH50znGbNzMAiCFYNPh4f4cP0wnPklFJVBL10Lh4UScOq7htYVXZXblrWRA5deGjIQGPolEaVMNX/wuhBOJI5bQAKAAAAABJRU5ErkJggg=="""

# Singleton ref to the loaded pixbuf
_twitter_pixbuf = load_base64_icon (TWITTER_ICON)

HANDLERS = ["TwitterModule"]
VERSION = "0.2"

MIN_MESSAGE_LEN = 2
        
class TwitterClient :
    def __init__ (self):
        self._account = Account ("twitter.com", "Twitter API")
        self._opener = GnomeURLopener (self._account)
        self._thread = None
        
        self._opener.connect ("done", self._on_opener_done)
        
    def update (self, msg):
        try:
            post_payload = urllib.urlencode({"status" : msg})
            self._opener.open_async (TWITTER_UPDATE_URL, post_payload)
        except ConcurrentRequestsException :
            LOGGER.warning ("Attempting to post while another post is already running. Ignoring")
            error = gtk.MessageDialog (None,
                                       type=gtk.MESSAGE_WARNING,
                                       buttons=gtk.BUTTONS_OK)
            error.set_markup (_("A post is already awaiting submission, please wait before you post another message"))
            error.set_title (_("Error posting to twitter.com"))
            error.show_all()
            error.run()
            error.destroy()
            return
            
    def _on_opener_done (self, opener, info):
        LOGGER.debug ("Got reply from Twitter")
        #for s in info.readlines() : print s

_FAIL_POST = _(
"""Failed to post update to twitter.com. Please make sure that:

  - Your internet connection is working
  - You can connect to <i>http://twitter.com</i> in your web browser
"""
)

class TwitterUpdateAction(deskbar.interfaces.Action):
    
    def __init__(self, msg, client):
        deskbar.interfaces.Action.__init__ (self, msg)
        self._msg = msg
        self._client = client
    
    def get_hash(self):
        return "twitter:"+self._msg
        
    def get_icon(self):
        # We use only pixbufs
        return None
    
    def get_pixbuf(self) :
        global _twitter_pixbuf
        return _twitter_pixbuf
    
    def activate(self, text=None):
        LOGGER.info ("Posting: '%s'" % self._msg)
        try:
            self._client.update (self._msg)
        except IOError, e:
            LOGGER.warning ("Failed to post to twitter.com: %s" % e)
            error = gtk.MessageDialog (None,
                                       type=gtk.MESSAGE_WARNING,
                                       buttons=gtk.BUTTONS_OK)
            error.set_markup (_FAIL_POST)
            error.set_title (_("Error posting to twitter.com"))
            error.show_all()
            error.run()
            error.destroy()
        
    def get_verb(self):
        return _('Post <i>"%(msg)s"</i>')

    def get_tooltip(self, text=None):
        return _("Update your Twitter account with the message:\n\n\t<i>%s</i>") % self._msg
        
    def get_name(self, text=None):
        return {"name": self._msg, "msg" : self._msg}
    
    def skip_history(self):
        return True

class TwitterMatch(deskbar.interfaces.Match):
    
    def __init__(self, msg, client, **args):
        global _twitter_pixbuf
        
        deskbar.interfaces.Match.__init__ (self, category="web", pixbuf=_twitter_pixbuf, name=msg, **args)
        self.add_action( TwitterUpdateAction(self.get_name(), client) )
    
    def get_hash(self):
        return "twitter:"+self.get_name()

class TwitterModule(deskbar.interfaces.Module):
    
    INFOS = {'icon': _twitter_pixbuf,
             'name': _("Twitter"),
             'description': _("Post updates to your Twitter account"),
             'version': VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self._client = TwitterClient()
    
    def query(self, qstring):
        if len (qstring) <= MIN_MESSAGE_LEN and \
           len (qstring) > 140: return None
        
        self._emit_query_ready(qstring, [TwitterMatch(qstring, self._client)])
    
    def has_config(self):        
        return True
    
    def show_config(self, parent):
        LOGGER.debug ("Showing config")
        account = Account ("twitter.com", "Twitter API")
        
        login_dialog = AccountDialog(account)
        login_dialog.show_all()
        login_dialog.run()            
        login_dialog.destroy()
   
