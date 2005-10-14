import cgi, urllib
from gettext import gettext as _
import gnomevfs, gconf
import deskbar, deskbar.handler

PRIORITY = 50

def is_preferred_browser(tests, handler_class, description, failure):
	# We will import only if the user's preferred browser is mozilla
	http_handler = gconf.client_get_default().get_string("/desktop/gnome/url-handlers/http/command").strip().lower()
	if not gconf.client_get_default().get_bool("/desktop/gnome/url-handlers/http/enabled"):
		return (None, "Http Handler Disabled, skipping browser integration", None)
	
	for test in tests:
		if http_handler.find(test) != -1:
			return (handler_class, description, test)
	
	return (None, failure, None)
		
class BrowserMatch(deskbar.handler.Match):
	def __init__(self, backend, name, url, icon=None):
		deskbar.handler.Match.__init__(self, backend, cgi.escape(name), icon)
		self._priority = 10
		self._url = url
		
	def action(self, text=None):
		self._priority = self._priority+1
		gnomevfs.url_show(self._url)
		
	def get_verb(self):
		return _("Open Bookmark <b>%(name)s</b>")

class BrowserSmartMatch(BrowserMatch):
	def __init__(self, bmk, name, url):
		BrowserMatch.__init__(self, bmk.get_handler(), name, url, bmk.get_icon())
		self._priority = 0
		self._bookmark = bmk
		
	def get_bookmark(self):
		return self._bookmark
		
	def action(self, text=""):
		self._priority = self._priority+1
		
		real_url = re.sub("%s", urllib.quote_plus(text), self._url)
		gnomevfs.url_show(real_url)
		
	def get_verb(self):
		return _("Search <b>%(name)s</b> for <i>%(text)s</i>")
		
class BrowserHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "web-bookmark.png")
		self._indexer = None
		self._smart_bookmarks = []
	
	def _parse_bookmarks(self):
		"""
		Returns a tuple (indexer, smart bookmarks list)
		"""
		raise NotImplementedError
		
	def initialize(self):
		self._indexer, self._smart_bookmarks = self._parse_bookmarks()
		
	def get_priority(self):
		return PRIORITY
				
	def query(self, query, max=5):
		bmk = self._indexer.look_up(query)[:max]
		sbmk = self._smart_bookmarks
		
		#Merge the two sources
		result = []
		for b in bmk:
			result.append(b)
		for b in sbmk:
			if not b.get_bookmark() in bmk:
				result.append(b)
		
		return result
		
def get_url_host(url):
	try:
		#Remove http: needed by splithost
		clean = url[url.find(":")+1:]
		
		#Remove the www part so we have more matches
		if clean.startswith("//www."):
			clean = "//"+clean[6:]
			
		return urllib.splithost(clean)[0]
	except Exception, msg:
		print 'Error:get_url_host(%s):%s' % (url, msg)
		return url
