from deskbar.core.Utils import strip_html, get_proxy
from gettext import gettext as _
from deskbar.defs import VERSION
import urllib
import gnomevfs
import deskbar.interfaces.Module, deskbar.interfaces.Match, deskbar
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
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
	
	def get_hash(self, text=None):
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
		
		print 'Query yahoo for:', qstring
		stream = urllib.urlopen(
			YAHOO_URL % 
			urllib.urlencode(
				{'appid': YAHOO_API_KEY,
				'query': qstring,
				'results': 15}), proxies=get_proxy())
		dom = xml.dom.minidom.parse(stream)
		print 'Got yahoo answer for:', qstring
		
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
		print "Returning yahoo answer for:", qstring
		self._emit_query_ready(qstring, matches )
