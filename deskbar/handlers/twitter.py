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
IDENTICA_UPDATE_URL = "http://identi.ca/api/statuses/update.xml"

# Base64 encoded Twitter logo
TWITTER_ICON = \
"""iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAcVJREFUOI2FkztuFEEQhr/q7nnIa2GQVgiDCYCEAzhAHMY3gASJgAtwAXLuQ0AGRiQbOEBeGdsy4PXOTNdPMLOrWVbCJVXUVf+ru42h2pzVZEdmBEQwo07JuKUSgEta5szMjfNOTKLxvIDsrhjCf0ESABJXDl+WHTVw0sE0JB7gtwkYAIBG4mcWCVgCGTA5N22rngTMjBiMFKNtATjwx0Vh0Am+NpmzGPB+FwBDPEzQdFll6kESQAjBZjetfrsozDDEp0U3MmBrmAS8uldvW8jAlaBESGvVYIZJgDAz5tmZuzYB3F3fl5kLd+oRoQbZq/FO4mkZeFKETQADMuLSndqM6yxe3605rBJLaW0gI6YxUo6uNq0sNoK5i12DXy52gjExcSdFGCw5kP55FwH68wI4dXHiYubiW+skA7n3AxK44xoFMA7xcWGUZhxngcHbiwVnueIgBroVO/CyTuN91nKUO72/bHh3fg1xCGmDTCBjPxqfD/bYL/t3sI7TLfBmr+Jot4LO+9SCjTpANH50znGbNzMAiCFYNPh4f4cP0wnPklFJVBL10Lh4UScOq7htYVXZXblrWRA5deGjIQGPolEaVMNX/wuhBOJI5bQAKAAAAABJRU5ErkJggg=="""

IDENTICA_ICON = \
"""iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9gIBRUoA+uuEZoAAACXSURBVDjLY5Q0cfzPQAFgYqAQDLwBLNgEOdjZGJRVpBmMDNQYGBgYGM5duMVw985Thh8/fxE2gIOdjcHVxZRBW1sRLiYtLcpw9ep9ht17TmMYguEFZRVpFM0woK2tyKCsIk04DGDOxgawyVE/Fs5duIVTMTY5DAPu3nnKcPXqfQyFV6/eZ7h75ymGOCO2pExKNDKO5gUGAHZcMhS+r1WkAAAAAElFTkSuQmCC"""

# Singleton ref to the loaded pixbufs
_twitter_pixbuf = load_base64_icon (TWITTER_ICON)
_identica_pixbuf = load_base64_icon (IDENTICA_ICON)

HANDLERS = ["TwitterModule", "IdenticaModule"]
VERSION = "0.3"

MIN_MESSAGE_LEN = 2
        
_FAIL_POST = _(
"""Failed to post update to %(domain)s. Please make sure that:

  - Your internet connection is working
  - You can connect to <i>http://%(domain)s</i> in your web browser
  - Your credentials in the preferences are correct
"""
)
        
class TwitterClient :
    def __init__ (self, domain="twitter.com", update_url=TWITTER_UPDATE_URL, realm="Twitter API"):
        self._account = Account (domain, realm)
        self._opener = GnomeURLopener (self._account)
        self._thread = None
        self._update_url = update_url
        self._domain = domain
        
        self._opener.connect ("done", self._on_opener_done)
        
    def update (self, msg):
        try:
            post_payload = urllib.urlencode({"status" : msg})
            self._opener.open_async (self._update_url, post_payload)
        except ConcurrentRequestsException :
            LOGGER.warning ("Attempting to post while another post is already running. Ignoring")
            error = gtk.MessageDialog (None,
                                       type=gtk.MESSAGE_WARNING,
                                       buttons=gtk.BUTTONS_OK)
            error.set_markup (_("A post is already awaiting submission, please wait before you post another message"))
            error.set_title (_("Error posting to %s" % self._domain))
            error.show_all()
            error.run()
            error.destroy()
            return
            
    def _on_opener_done (self, opener, info):
        LOGGER.debug ("Got reply from %s. Success: %s" % (self._update_url, self._opener.get_success()))
        if not self._opener.get_success() :
            error = gtk.MessageDialog (None,
                                       type=gtk.MESSAGE_WARNING,
                                       buttons=gtk.BUTTONS_OK)
            error.set_markup (_FAIL_POST % {"domain" : self._domain})
            error.set_title (_("Error posting to %s" % self._domain))
            error.show_all()
            error.run()
            error.destroy()

class TwitterUpdateAction(deskbar.interfaces.Action):
    
    def __init__(self, msg, client, domain="twitter.com", service="Twitter", pixbuf=None):
        deskbar.interfaces.Action.__init__ (self, msg)
        
        global _twitter_pixbuf
        
        self._msg = msg
        self._client = client
        self._domain = domain
        self._service = service
        
        if pixbuf : self._pixbuf = pixbuf
        else : self._pixbuf = _twitter_pixbuf
    
    def get_hash(self):
        return "%s:%s" % (self._service,self._msg)
        
    def get_icon(self):
        # We use only pixbufs
        return None
    
    def get_pixbuf(self) :
        return self._pixbuf
    
    def activate(self, text=None):
        LOGGER.info ("Posting: '%s'" % self._msg)
        try:
            self._client.update (self._msg)
        except IOError, e:
            LOGGER.warning ("Failed to post to %s: %s" % (self._domain,e))
            error = gtk.MessageDialog (None,
                                       type=gtk.MESSAGE_WARNING,
                                       buttons=gtk.BUTTONS_OK)
            error.set_markup (_FAIL_POST % {"domain" : self._domain})
            error.set_title (_("Error posting to %s" % self._domain))
            error.show_all()
            error.run()
            error.destroy()
        
    def get_verb(self):
        return _('<small>(%(remain)s)</small> Post <i>"%(msg)s"</i>')

    def get_tooltip(self, text=None):
        return _("Update your %s account with the message:\n\n\t<i>%s</i>") % (self._service_name, self._msg)
        
    def get_name(self, text=None):
        return {"name": self._msg, "msg" : self._msg, "remain" : str(140 - len(self._msg))}
    
    def skip_history(self):
        return True

class TwitterMatch(deskbar.interfaces.Match):
    
    def __init__(self, msg, client, domain="twitter.com", service="Twitter", pixbuf=None, **args):
        global _twitter_pixbuf
        
        self._service = service
        self._domain = domain
        
        if pixbuf : self._pixbuf = pixbuf
        else : self._pixbuf = _twitter_pixbuf
        
        deskbar.interfaces.Match.__init__ (self,
                                           category="web",                                           
                                           name=msg,
                                           pixbuf=self._pixbuf,
                                           **args)
                                           
        action = TwitterUpdateAction(self.get_name(), client,
                                     domain=self._domain,
                                     service=self._service,
                                     pixbuf=self._pixbuf)
        self.add_action(action)
    
    def get_hash(self):
        return "%s:%s" % (self._service,self.get_name())

class TwitterModule(deskbar.interfaces.Module):
    
    INFOS = {'icon': _twitter_pixbuf,
             'name': _("Twitter"),
             'description': _("Post updates to your Twitter account"),
             'version': VERSION}
    
    def __init__(self, domain="twitter.com", service="Twitter", pixbuf=None, update_url=TWITTER_UPDATE_URL, realm="Twitter API"):
        global _twitter_pixbuf
        
        deskbar.interfaces.Module.__init__(self)

        self._domain = domain
        self._service = service
        self._realm = realm
        
        if pixbuf : self._pixbuf = pixbuf
        else : self._pixbuf = _twitter_pixbuf
        
        self._client = TwitterClient(domain=self._domain, update_url=update_url, realm=self._realm)
    
    def query(self, qstring):
        if len (qstring) <= MIN_MESSAGE_LEN and \
           len (qstring) > 140: return None
        
        match = TwitterMatch(qstring, self._client,
                             domain=self._domain,
                             service=self._service,
                             pixbuf=self._pixbuf)
        
        self._emit_query_ready(qstring, [match])
    
    def has_config(self):        
        return True
    
    def show_config(self, parent):
        LOGGER.debug ("Showing config")
        account = Account (self._domain, self._realm)
        
        login_dialog = AccountDialog(account)
        login_dialog.show_all()
        login_dialog.run()            
        login_dialog.destroy()
    
    def get_domain (self):
        return self._domain
    
class IdenticaModule(TwitterModule):
    
    INFOS = {'icon': _identica_pixbuf,
             'name': _("identi.ca"),
             'description': _("Post updates to your identi.ca account"),
             'version': VERSION}
    
    def __init__(self):
        TwitterModule.__init__(self,
                               domain="identi.ca",
                               service="Identica",
                               pixbuf=_identica_pixbuf,
                               update_url=IDENTICA_UPDATE_URL,
                               realm="Laconica API")

