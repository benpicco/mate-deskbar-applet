import xml.sax
from os.path import join, expanduser, exists
from gettext import gettext as _
import gtk
import deskbar, deskbar.indexer

from deskbar.handlers_browsers import get_url_host, is_preferred_browser
from deskbar.handlers_browsers import BrowserHandler, BrowserSmartMatch, BrowserMatch

EXPORTED_CLASS, NAME, matched = is_preferred_browser(["epiphany"],
							"EpiphanyHandler",
							(_("Epiphany"), _("Index your bookmarks and search engines")),
							"Epiphany is not your preferred browser, not using it.")
	
class EpiphanyHandler(BrowserHandler):
	def __init__(self):
		BrowserHandler.__init__(self)
	
	def _parse_bookmarks(self):
		parser = EpiphanyBookmarksParser(self)
		return (parser.get_indexer(), parser.get_smart_bookmarks())

		
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
		
		self._cache = EpiphanyFaviconCacheParser().get_cache()
		self._index_bookmarks()
	
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

			bookmark = BrowserMatch(self.handler, self.title, self.href, pixbuf)
			self._indexer.add("%s %s" % (self.title, self.href), bookmark)

			if self.smarthref != None:
				bookmark = BrowserSmartMatch(bookmark, self.title, self.smarthref)
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

