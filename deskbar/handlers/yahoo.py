from deskbar.core.Utils import strip_html, get_proxy
from deskbar.defs import VERSION
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
import deskbar.interfaces.Module, deskbar.interfaces.Match, deskbar
import logging
import urllib
import xml.dom.minidom

YAHOO_API_KEY = 'deskbar-applet'
YAHOO_URL = 'http://api.search.yahoo.com/WebSearchService/V1/webSearch?%s'
MAX_QUERIES = 10
QUERY_DELAY = 1

HANDLERS = ["YahooHandler"]

class OpenYahooAction(ShowUrlAction):
    
    def __init__(self, name, url):
        ShowUrlAction.__init__(self, name, url)

    def get_verb(self):
        return "%(name)s"

class YahooMatch(deskbar.interfaces.Match):
    def __init__(self, url=None, **args):
        deskbar.interfaces.Match.__init__ (self, category="web", icon="yahoo.png", **args)
        self.url = url
        self.add_action( OpenYahooAction(self.get_name(), self.url) )
        self.add_action( CopyToClipboardAction( _("URL"), self.url) )
    
    def get_hash(self):
        return self.url

class YahooHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("yahoo.png"),
             'name': _("Yahoo! Search"),
             'description': _("Search Yahoo! as you type"),
             'version': VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self.server = None

    def query(self, qstring):
        # Delay before we query so we *don't* make four queries
        # "s", "sp", "spa", "spam".
        
        # TODO: Missing
        #self.check_query_changed (timeout=QUERY_DELAY)
        
        logging.info('Query yahoo for: '+qstring)
        url = YAHOO_URL % urllib.urlencode(
                {'appid': YAHOO_API_KEY,
                'query': qstring,
                'results': 15})
        try:
            stream = urllib.urlopen(url, proxies=get_proxy())
        except IOError, msg:
            logging.error("Could not open URL %s: %s, %s" % (url, msg[0], msg[1]))
            return
        
        dom = xml.dom.minidom.parse(stream)
        logging.info('Got yahoo answer for: '+qstring)
        
        # TODO: Missing
        #self.check_query_changed ()    
        
        # The Yahoo! search might have taken a long time
        # better check if we're still valid
        matches = [
            YahooMatch (
                    name=strip_html(r.getElementsByTagName("Title")[0].firstChild.data.encode('utf8')),
                    url=r.getElementsByTagName("ClickUrl")[0].firstChild.data.encode('utf8'),
                    priority=self.get_priority()
            )
            for r in dom.getElementsByTagName("Result")]
        # TODO: Missing
        #self.check_query_changed ()
        logging.info("Returning yahoo answer for: "+qstring)
        self._emit_query_ready(qstring, matches )
