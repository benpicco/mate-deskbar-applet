from deskbar.core.Utils import strip_html, get_proxy
from deskbar.defs import VERSION
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from xml.dom import DOMException
from xml.parsers.expat import ExpatError
import deskbar
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import logging
import urllib
import xml.dom.minidom

LOGGER = logging.getLogger(__name__)

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
        LOGGER.info('Query yahoo for: %s', qstring)
        
        url = YAHOO_URL % urllib.urlencode(
                {'appid': YAHOO_API_KEY,
                'query': qstring,
                'results': 15})
        
        matches = []
        try:
            try:
                stream = urllib.urlopen(url, proxies=get_proxy())
                dom = xml.dom.minidom.parse(stream)
            except IOError, msg:
                LOGGER.error("Could not open URL %s: %s, %s", url, msg[0], msg[1])
            except ExpatError, e:
                LOGGER.exception(e)
        finally:
            stream.close()
        
        LOGGER.info('Got yahoo answer for: %s', qstring)
            
        try:
            try:
                for r in dom.getElementsByTagName("Result"):
                    result_title = strip_html(r.getElementsByTagName("Title")[0].firstChild.data.encode('utf8'))
                    result_url = r.getElementsByTagName("ClickUrl")[0].firstChild.data.encode('utf8')
                    matches.append(
                                   YahooMatch (name=result_title, url=result_url, priority=self.get_priority())
                    )
            except DOMExecption, e:
                LOGGER.exception(e)
        finally:
            # Cleanup
            dom.unlink()
            
        LOGGER.info("Returning yahoo answer for: %s", qstring)
        self._emit_query_ready(qstring, matches)
