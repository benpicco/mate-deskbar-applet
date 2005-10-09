import cgi, re, xml.sax, urllib
from os.path import join, expanduser, exists
from gettext import gettext as _
import gtk, gnomevfs
import deskbar, deskbar.indexer
import deskbar.handler

EXPORTED_CLASS = "EpiphanyHandler"
NAME = _("Epiphany Bookmarks and Search Engines")

PRIORITY = 50

class EpiphanyMatch(deskbar.handler.Match):
	def __init__(self, backend, name, url, icon=None):
		deskbar.handler.Match.__init__(self, backend, cgi.escape(name), icon)
		self._priority = 10
		self._url = url
		
	def action(self, text=None):
		self._priority = self._priority+1
		gnomevfs.url_show(self._url)
		
	def get_verb(self):
		return _("Open Bookmark <b>%(name)s</b>")

class EpiphanySmartMatch(EpiphanyMatch):
	def __init__(self, bmk, name, url):
		EpiphanyMatch.__init__(self, bmk.get_handler(), name, url, bmk.get_icon())
		self._priority = 0
		self._bookmark = bmk
		
	def get_bookmark(self):
		return self._bookmark
		
	def action(self, text=""):
		self._priority = self._priority+1
		
		real_url = re.sub("%s", text, self._url)
		gnomevfs.url_show(real_url)
		
	def get_verb(self):
		return _("Search <b>%(name)s</b> for <i>%(text)s</i>")
		
class EpiphanyHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "web-bookmark.png")
		
		parser = EpiphanyBookmarksParser(self)
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
		
class EpiphanyBookmarksParser(xml.sax.ContentHandler):
	def __init__(self, handler):
		xml.sax.ContentHandler.__init__(self)
		
		self.handler = handler
		
		self.chars = ""
		self.title = None
		self.href = None
		self.smarthref = None
		
		self._indexer = deskbar.indexer.Index()
		self._smart_bookmarks = []
		
		print 'Starting ephy bookmarks indexation'
		self._cache = EpiphanyFaviconCacheParser().get_cache()
		self._index_bookmarks()
		print '\tDone !'
	
	def get_indexer(self):
		"""
		Returns a completed indexer with the contents of bookmark file
		"""
		return self._indexer
	
	def get_smart_bookmarks(self):
		"""
		Return a list of EpiphanySmartMatch instances representing smart bookmarks
		"""
		return self._smart_bookmarks
		
	def _index_bookmarks(self):
		bookmarks_file_name = expanduser("~/.gnome2/epiphany/bookmarks.rdf")
		if exists(bookmarks_file_name):
			parser = xml.sax.make_parser()
			parser.setContentHandler(self)
			parser.parse(bookmarks_file_name)
	
	def characters(self, chars):
		self.chars = self.chars + chars
		
	def startElement(self, name, attrs):
		self.chars = ""
		if name == "item":
			self.title = None
			self.href = None
			self.smarthref = None

	def endElement(self, name):
		if name == "title":
			self.title = self.chars.encode('utf8')
		elif name == "link":
			self.href = self.chars.encode('latin1')
		elif name == "ephy:smartlink":
			self.smarthref = self.chars.encode('latin1')
		elif name == "item":
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
			
			bookmark = EpiphanyMatch(self.handler, self.title, self.href, pixbuf)
			self._indexer.add("%s %s" % (self.title, self.href), bookmark)
					
			if self.smarthref != None:
				bookmark = EpiphanySmartMatch(bookmark, self.title, self.smarthref)
				self._smart_bookmarks.append(bookmark)

class EpiphanyFaviconCacheParser(xml.sax.ContentHandler):
	def __init__(self):
		xml.sax.ContentHandler.__init__(self)
		self.ephy_dir = expanduser("~/.gnome2/epiphany")
		self.filename = join(self.ephy_dir, "ephy-favicon-cache.xml")
		
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
		if name == "property" and attrs['id'] == "2":
			self.url = None
		if name == "property" and attrs['id'] == "3":
			self.name = None

	def endElement(self, name):
		if name == "property":
			if self.url == None:
				self.url = self.chars
			elif self.name == None:
				self.name = self.chars
		elif name == "node":
			# Splithost requires //xxxx[:port]/xxxx, so we remove "http:"
			host = get_url_host(self.url)
			self.cache[host] = join(self.ephy_dir, "favicon_cache", self.name.encode('utf8'))

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
