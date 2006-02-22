from deskbar.Utils import strip_html
from gettext import gettext as _

import urllib, cgi
import gnomevfs
import deskbar.Handler, deskbar
import xml.dom.minidom

YAHOO_API_KEY = 'deskbar-applet'
YAHOO_URL = 'http://api.search.yahoo.com/WebSearchService/V1/webSearch?%s'
MAX_QUERIES = 10
QUERY_DELAY = 1

HANDLERS = {
	"YahooHandler" : {
    	"name": _("Yahoo! Search"),
    	"description": _("Search Yahoo! as you type"),
	}
}

class YahooMatch(deskbar.Match.Match):
	def __init__(self, handler, name, url, **args):
		deskbar.Match.Match.__init__ (self, handler, name=name, **args)
		self.url = url

	def get_verb(self):
		return "%(name)s"

	def action(self, text=None):
		gnomevfs.url_show(self.url)

	def get_category(self):
		return "web"

	def get_hash(self, text=None):
		return self.url

class YahooHandler(deskbar.Handler.AsyncHandler):
	def __init__(self):
		deskbar.Handler.AsyncHandler.__init__(self, "yahoo.png")
		self.server = None

	def query(self, qstring, qmax):
		# Just to ensure we don't bork anything
		qmax = min (deskbar.DEFAULT_RESULTS_PER_HANDLER, MAX_QUERIES)

		# Delay before we query so we *don't* make four queries
		# "s", "sp", "spa", "spam".
		self.check_query_changed (timeout=QUERY_DELAY)
		
		print 'Query yahoo for:', qstring
		stream = urllib.urlopen(
			YAHOO_URL % 
			urllib.urlencode(
				{'appid': YAHOO_API_KEY,
				'query': qstring,
				'results': qmax}))
		dom = xml.dom.minidom.parse(stream)
		print 'Got yahoo answer for:', qstring
		
		self.check_query_changed ()	
		# The Yahoo! search might have taken a long time
		# better check if we're still valid
		matches = [
			YahooMatch (self, 
					cgi.escape(strip_html(r.getElementsByTagName("Title")[0].firstChild.data.encode('utf8'))),
					r.getElementsByTagName("ClickUrl")[0].firstChild.data.encode('utf8')
			)
			for r in dom.getElementsByTagName("Result")[:qmax-1]
			]
		self.check_query_changed ()
		print "Returning yahoo answer for:", qstring
		return matches
