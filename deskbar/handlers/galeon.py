import cgi, re, xml.sax, urllib
from os.path import join, expanduser, exists
from gettext import gettext as _
import gtk, gnomevfs, gconf
import deskbar, deskbar.indexer
import deskbar.handler

# We import ourselves only if the user's preferred browser is mozilla
http_handler = gconf.client_get_default().get_string("/desktop/gnome/url-handlers/http/command").strip().lower()
if http_handler.find("galeon") != -1 and gconf.client_get_default().get_bool("/desktop/gnome/url-handlers/http/enabled"):
	EXPORTED_CLASS = "GaleonHandler"
	NAME = _("Galeon Bookmarks and Search Engines")
else:
	EXPORTED_CLASS = None
	NAME = "Galeon is not your preferred browser, not using it."
	
PRIORITY = 50

class GaleonMatch(deskbar.handler.Match):
	def __init__(self, backend, name, url, icon=None):
		deskbar.handler.Match.__init__(self, backend, cgi.escape(name), icon)
		self._priority = 10
		self._url = url
		
	def action(self, text=None):
		self._priority = self._priority+1
		gnomevfs.url_show(self._url)
		
	def get_verb(self):
		return _("Open Bookmark <b>%(name)s</b>")

class GaleonSmartMatch(GaleonMatch):
	def __init__(self, bmk, name, url):
		GaleonMatch.__init__(self, bmk.get_handler(), name, url, bmk.get_icon())
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
		
class GaleonHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "web-bookmark.png")
	
	def initialize(self):
		parser = GaleonBookmarksParser(self)
		self._indexer = parser.get_indexer()
		self._smart_bookmarks = parser.get_smart_bookmarks()
		
	def get_priority(self):
		return PRIORITY
				
	def query(self, query, max=5):
		bmk = self._indexer.look_up(query)[:max]
		sbmk = self._smart_bookmarks #[:max] We want to show all smart bookmarks
		
		#Merge the two sources
		result = []
		for b in bmk:
			result.append(b)
		for b in sbmk:
			if not b.get_bookmark() in bmk:
				result.append(b)
		
		return result
		
class GaleonBookmarksParser(xml.sax.ContentHandler):
	def __init__(self, handler):
		xml.sax.ContentHandler.__init__(self)
		
		self.handler = handler
		
		self.chars = ""
		self.title = None
		self.href = None
		self.smarthref = None
		
		self._indexer = deskbar.indexer.Index()
		self._smart_bookmarks = []
		
		print 'Starting galeon bookmarks indexation'
		self._cache = GaleonFaviconCacheParser().get_cache()
		self._index_bookmarks()
		print '\tDone !'
	
	def get_indexer(self):
		"""
		Returns a completed indexer with the contents of bookmark file
		"""
		return self._indexer
	
	def get_smart_bookmarks(self):
		"""
		Return a list of GaleonSmartMatch instances representing smart bookmarks
		"""
		return self._smart_bookmarks
		
	def _index_bookmarks(self):
		bookmarks_file_name = expanduser("~/.galeon/bookmarks.xbel")
		if exists(bookmarks_file_name):
			parser = xml.sax.make_parser()
			parser.setContentHandler(self)
			parser.parse(bookmarks_file_name)
	
	def characters(self, chars):
		self.chars = self.chars + chars
		
	def startElement(self, name, attrs):
		self.chars = ""
		if name == "bookmark":
			self.title = None
			self.href = attrs['href'].encode('latin1')
			self.smarthref = None

	def endElement(self, name):
		if name == "title":
			self.title = self.chars.encode('utf8')
		elif name == "smarturl":
			self.smarthref = self.chars.encode('latin1')
		elif name == "bookmark":
			if self.href.startswith("javascript:"):
				return
			
			pixbuf = None
			try:
				host = get_url_host(self.href)
				if host in self._cache:
					pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self._cache[host], deskbar.ICON_SIZE, deskbar.ICON_SIZE)
			except Exception, msg:
				# Most of the time we have an html page here, it could also be an unrecognized format
				print 'Error:endElement(%s):Title:%s:%s' % (name.encode("utf8"), self.title, msg)
			
			bookmark = GaleonMatch(self.handler, self.title, self.href, pixbuf)
			self._indexer.add("%s %s" % (self.title, self.href), bookmark)

			if self.smarthref != None:
				bookmark = GaleonSmartMatch(bookmark, self.title, self.smarthref)
				self._smart_bookmarks.append(bookmark)

class GaleonFaviconCacheParser(xml.sax.ContentHandler):
	def __init__(self):
		xml.sax.ContentHandler.__init__(self)
		self.galeon_dir = expanduser("~/.galeon/")
		self.filename = join(self.galeon_dir, "favicon_cache.xml")
		
		self.cache = None
		
		self.chars = ""
		self.url = None
		self.name = None
	
	def get_cache(self):
		"""
		Returns a dictionary of (host, favicon path) entries where
		  host is the hostname, like google.com (without www)
		  favicon path is the on-disk path to the favicon image file.
		"""
		if self.cache != None:
			return self.cache
		
		self.cache = {}
		if exists(self.filename):
			parser = xml.sax.make_parser()
			parser.setContentHandler(self)
			parser.parse(self.filename)
			
		return self.cache
	
	def characters(self, chars):
		self.chars = self.chars + chars
		
	def startElement(self, name, attrs):
		self.chars = ""
		if name == "entry":
			self.url = attrs['url']
			self.name = attrs['favicon']

	def endElement(self, name):
		if name == "entry":
			# Splithost requires //xxxx[:port]/xxxx, so we remove "http:"
			host = get_url_host(self.url)
			self.cache[host] = join(self.galeon_dir, "favicon_cache", self.name.encode('utf8'))

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
