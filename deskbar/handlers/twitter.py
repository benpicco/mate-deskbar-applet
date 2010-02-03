from deskbar.core.Utils import load_base64_icon
from deskbar.core.Web import GnomeURLopener, Account, AccountDialog, ConcurrentRequestsException
from deskbar.defs import VERSION
from gettext import gettext as _
import deskbar
import deskbar.interfaces.Action
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gtk
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
VERSION = "0.3.1"

MIN_MESSAGE_LEN = 2

# Translators: The escaped characters are the standard UTF-8 bullet        
_FAIL_POST = _(
"""Failed to post update to %(domain)s.
Please make sure that:

 \342\200\242 Your internet connection is working
 \342\200\242 You can connect to <i>http://%(domain)s</i> in
    your web browser
 \342\200\242 Your credentials in the preferences are correct"""
)

class TwitterClientFactory :
    """
    A factory to help instantiating C{TwitterClient}s.
    """
    def __init__ (self,
                  domain="twitter.com",
                  update_url=TWITTER_UPDATE_URL,
                  realm="Twitter API",
                  extra_widget_factory=None):
        self._domain = domain
        self._update_url = update_url
        self._realm = realm
        self._extra_widget_factory = extra_widget_factory
    
    def create_client (self):
        return TwitterClient(domain=self._domain,
                             update_url=self._update_url,
                             realm=self._realm,
                             extra_widget_factory=self._extra_widget_factory)
        
class TwitterClient :
    """
    Client capable of talking to a twitter-like API.
    
    Note on proxies: The URLopener used here will not reflect changes done
                     to the Gnome proxy configuration. Therefore preferably
                     use the TwitterClientFactory and create a new TwitterClient
                     instance each time you need it
    """
    def __init__ (self,
                  domain="twitter.com",
                  update_url=TWITTER_UPDATE_URL,
                  realm="Twitter API",
                  extra_widget_factory=None):
        self._account = Account (domain, realm)
        self._opener = GnomeURLopener (self._account,
                                       extra_widget_factory=extra_widget_factory)
        self._thread = None
        self._update_url = update_url
        self._domain = domain
        
    def update (self, msg):
        try:
            post_payload = urllib.urlencode({"status" : msg, "source" : "deskbar"})
            self._opener.open_async (self._update_url, post_payload, self._on_opener_done)
        except ConcurrentRequestsException :
            LOGGER.warning ("Attempting to post while another post is already running. Ignoring")
            error = gtk.MessageDialog (None,
                                       type=gtk.MESSAGE_WARNING,
                                       buttons=gtk.BUTTONS_OK)
            error.set_markup (_("A post is already awaiting submission; please wait before you post another message"))
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
    
    def __init__(self, msg, client_factory, domain="twitter.com", service="Twitter", pixbuf=None):
        deskbar.interfaces.Action.__init__ (self, msg)
        
        global _twitter_pixbuf
        
        self._msg = msg
        self._client_factory = client_factory
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
            # Create the client on-demand to make sure proxy info is up to date
            client = self._client_factory.create_client()
            client.update (self._msg)
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
        # TRANSLATORS: An example display of the below string:
        #
        #   (125) Post "I can eat glass"
        #
        # The number in the parens indicates how many characters the user 
        # has left of the maximum message size. It should be at the start of
        # the string as to not be hidden by ellipsation.
        #
        return _('<small>(%(remain)s)</small> Post <i>"%(msg)s"</i>')

    def get_tooltip(self, text=None):
        return _("Update your %s account with the message:\n\n\t<i>%s</i>") % (self._service, self._msg)
        
    def get_name(self, text=None):
        return {"name": self._msg, "msg" : self._msg, "remain" : str(140 - len(self._msg))}
    
    def skip_history(self):
        return True

class TwitterMatch(deskbar.interfaces.Match):
    
    def __init__(self, msg, client_factory, domain="twitter.com", service="Twitter", pixbuf=None, **args):
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
                                           
        action = TwitterUpdateAction(self.get_name(), client_factory,
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
    
    def __init__(self,
                 domain="twitter.com",
                 service="Twitter",
                 pixbuf=None,
                 update_url=TWITTER_UPDATE_URL,
                 realm="Twitter API",
                 extra_widget_factory=None):
        global _twitter_pixbuf
        
        deskbar.interfaces.Module.__init__(self)

        self._domain = domain
        self._service = service
        self._realm = realm
        
        if pixbuf : self._pixbuf = pixbuf
        else : self._pixbuf = _twitter_pixbuf
        
        self._client_factory = TwitterClientFactory(domain=self._domain,
                                                    update_url=update_url,
                                                    realm=self._realm,
                                                    extra_widget_factory=self.get_extra_account_dialog_widget)
    
    def query(self, qstring):
        # Convert string to unicode string so we get the correct length
        # See bug #577487
        qstring = unicode(qstring)
        if len (qstring) <= MIN_MESSAGE_LEN and \
           len (qstring) > 140: return None
        
        match = TwitterMatch(qstring, self._client_factory,
                             domain=self._domain,
                             service=self._service,
                             pixbuf=self._pixbuf)
        
        self._emit_query_ready(qstring, [match])
    
    def has_config(self):        
        return True
    
    def show_config(self, parent):
        account = Account (self._domain, self._realm)
        LOGGER.debug ("Showing config")
        login_dialog = AccountDialog(account, dialog_parent=parent)
        
        # Pack optional widget if appropriate
        extra_widget = self.get_extra_account_dialog_widget ()
        if extra_widget != None:
            login_dialog.vbox.pack_start (extra_widget)
        
        login_dialog.show_all()
        login_dialog.run()            
        login_dialog.destroy()
    
    def get_domain (self):
        return self._domain
    
    def get_extra_account_dialog_widget (self):
        """
        This method should return a C{gtk.Widget} or C{None}. If it returns
        a widget that widget will be packed into the L{AccountDialog} spawned
        by the underlying url opener.
        
        The default implementation simply returns C{None}
        """
        return None
    
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
    
    def get_extra_account_dialog_widget (self):
        vbox = gtk.VBox()
        label = gtk.Label()
        label.set_markup (_("Please note that Deskbar Applet does not support authentication via OpenID. You must configure a username and password on the <i>identi.ca</i> website if you haven't already."))
        label.set_line_wrap(True)
        button = gtk.LinkButton ("http://identi.ca", _("Visit identi.ca website"))
        vbox.pack_start (label)
        vbox.pack_start (button)
        return vbox
    
