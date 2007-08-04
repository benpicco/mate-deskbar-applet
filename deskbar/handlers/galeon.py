import xml.sax, traceback
import re, urllib
from os.path import join, expanduser, exists
from gettext import gettext as _
import gtk
import gnomevfs
import sys
import deskbar, deskbar.core.Indexer, deskbar.interfaces.Module
from deskbar.core.Watcher import FileWatcher
from deskbar.core.BrowserMatch import get_url_host, is_preferred_browser
from deskbar.core.BrowserMatch import BrowserSmartMatch, BrowserMatch
from deskbar.defs import VERSION
		
HANDLERS = [
	"GaleonBookmarksHandler",
	"GaleonHistoryHandler" ,
	"GaleonSearchHandler"]

GALEON_HISTORY_FILE = expanduser("~/.galeon/history2.xml")
if not exists(GALEON_HISTORY_FILE):
	GALEON_HISTORY_FILE = expanduser("~/.galeon/history.xml")
GALEON_BOOKMARKS_FILE = expanduser("~/.galeon/bookmarks.xbel")

favicon_cache = None
bookmarks = None
smart_bookmarks = None
quicksearches = None

class GaleonHandler(deskbar.interfaces.Module):
	
	def __init__(self, watched_file, callback):
		deskbar.interfaces.Module.__init__(self)
		self.watched_file = watched_file
		self.watch_callback = callback
		
	def initialize(self):
		global favicon_cache
		
		if not hasattr(self, 'watcher'):
			self.watcher = FileWatcher()
			self.watcher.connect('changed', lambda watcher, f: self.watch_callback())
			
		self.watcher.add(self.watched_file)
		
		if favicon_cache == None:
			favicon_cache = GaleonFaviconCacheParser().get_cache()
	
	def stop(self):
		self.watcher.remove(self.watched_file)
		
	@staticmethod
	def has_requirements():
		#	if deskbar.UNINSTALLED_DESKBAR:
		#		return (deskbar.Handler.HANDLER_IS_HAPPY, None, None)
		
		if is_preferred_browser("galeon"):
			return True
		else:
			GaleonHandler.INSTRUCTIONS = _("Galeon is not your preferred browser.")
			return False
	
class GaleonBookmarksHandler(GaleonHandler):
	
	INFOS = {'icon':  deskbar.core.Utils.load_icon("stock_bookmark"),
			 "name": _("Web Bookmarks"),
			 "description": _("Open your web bookmarks by name"),
			 "version": VERSION}
	
	def __init__(self):
		GaleonHandler.__init__(self, GALEON_BOOKMARKS_FILE, lambda: self._parse_bookmarks(True))
	
	def initialize(self):
		GaleonHandler.initialize(self)
		self._parse_bookmarks()
	
	def _parse_bookmarks(self, force=False):
		global favicon_cache, bookmarks, smart_bookmarks, quicksearches
		if force or bookmarks == None:
			parser = GaleonBookmarksParser(self, favicon_cache)
			bookmarks = parser.get_indexer()
			smart_bookmarks = parser.get_smart_bookmarks()
			quicksearches = parser.get_quicksearches()
	
	def query(self, query):
		global bookmarks
		matches = bookmarks.look_up(query)[:deskbar.DEFAULT_RESULTS_PER_HANDLER]
		self.set_priority_for_matches( matches )
		self._emit_query_ready(query, matches )

class GaleonSearchHandler(GaleonBookmarksHandler):
	
	INFOS = {'icon':  deskbar.core.Utils.load_icon("stock_bookmark"),
			 "name": _("Web Searches"),
			 "description": _("Search the web via your browser's search settings"),
			 "version": VERSION}
	
	def __init__(self):
		GaleonBookmarksHandler.__init__(self)
	
	def query(self, query):
		global smart_bookmarks
		global quicksearches
		query_a = query.split(" ")
		if len(query_a) > 1 and quicksearches.has_key(query_a[0]):
			quicksearches[query_a[0]].set_priority( self.get_priority() )
			self._emit_query_ready(query, (quicksearches[query_a[0]],) )
		else:
			self.set_priority_for_matches( smart_bookmarks )
			self._emit_query_ready(query, smart_bookmarks )
		
class GaleonHistoryHandler(GaleonHandler):
	
	INFOS = {'icon': deskbar.core.Utils.load_icon("epiphany-history.png"),
			 "name": _("Web History"),
			 "description": _("Open your web history by name"),
			 "version": VERSION}
	
	def __init__(self):
		GaleonHandler.__init__(self, GALEON_HISTORY_FILE, self._parse_history)
		self._history = None
		
	def initialize(self):
		GaleonHandler.initialize(self)
		self._parse_history()
		
	def _parse_history(self):
		global favicon_cache
		self._history = GaleonHistoryParser(self, favicon_cache).get_indexer()
			
	def query(self, query):
		matches = self._history.look_up(query)[:deskbar.DEFAULT_RESULTS_PER_HANDLER]
		self.set_priority_for_matches( matches )
		self._emit_query_ready(query, matches )

class GaleonBookmarksParser(xml.sax.ContentHandler):
	def __init__(self, handler, cache):
		xml.sax.ContentHandler.__init__(self)
		
		self.handler = handler
		
		self.chars = ""
		self.title = None
		self.href = None
		self.smarthref = None
		
		self._indexer = deskbar.Indexer.Indexer()
		self._qsindexer = {}
		self._smart_bookmarks = []

		
		self._cache = cache
		self._index_bookmarks()
	
	def get_indexer(self):
		"""
		Returns a completed indexer with the contents of bookmark file
		"""
		return self._indexer
	
	def get_quicksearches(self):
		return self._qsindexer
	
	def get_smart_bookmarks(self):
		"""
		Return a list of GaleonSmartMatch instances representing smart bookmarks
		"""
		return self._smart_bookmarks
		
	def _index_bookmarks(self):
		if exists(GALEON_BOOKMARKS_FILE):
			parser = xml.sax.make_parser()
			parser.setContentHandler(self)
			try:
				parser.parse(GALEON_BOOKMARKS_FILE)
			except Exception, e:
				print "Failed to parse galeon bookmarks, this is a know bug #338762:", e
				traceback.print_exc()
	
	def characters(self, chars):
		self.chars = self.chars + chars
		
	def startElement(self, name, attrs):
		self.chars = ""
		if name == "bookmark":
			self.title = None
			self.href = attrs['href'].encode('latin1')
			self.smarthref = None
			self.nick = None

	def endElement(self, name):
		if name == "title":
			self.title = self.chars.encode('utf8')
		elif name == "smarturl":
			self.smarthref = self.chars.encode('latin1')
			self.smarthref = re.sub('{.*}','',self.smarthref)
		elif name == "nick":
			self.nick = self.chars.encode('latin1')
		elif name == "bookmark":
			if self.href.startswith("javascript:"):
				return
			
			img = None
			host = get_url_host(self.href)
			if host in self._cache:
				img = self._cache[host]

			bookmark = BrowserMatch(self.title, self.href, icon=img)
			self._indexer.add("%s %s" % (self.title, self.href), bookmark)
			if self.nick != None and self.smarthref != None:
				quicksearch = BrowserSmartMatch(self.title, self.smarthref, icon=img, bookmark=bookmark, prefix_to_strip=self.nick)
				self._qsindexer[self.nick] = quicksearch

			if self.smarthref != None:
				bookmark = BrowserSmartMatch(self.title, self.smarthref, icon=img, bookmark=bookmark)
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


class GaleonHistoryParser(xml.sax.ContentHandler):
	def __init__(self, handler, cache):
		xml.sax.ContentHandler.__init__(self)

		self.handler = handler;
		self._cache = cache;

		self._indexer = deskbar.core.Indexer.Indexer()

		self._index_history();

	def get_indexer(self):
		"""
		Returns a completed indexer with the contents of the history file
		"""
		return self._indexer;

	def _index_history(self):
		if exists(GALEON_HISTORY_FILE):
			parser = xml.sax.make_parser()
			parser.setContentHandler(self)
			parser.parse(GALEON_HISTORY_FILE)

	def startElement(self, name, attrs):
		self.chars = ""
		if name == "item":
			url   = attrs['url'].encode('utf8')
			title = attrs['title'].encode('utf8')

			pixbuf = None
			try:
				host = get_url_host(url)
				if host in self._cache:
					pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self._cache[host], deskbar.ICON_HEIGHT, deskbar.ICON_HEIGHT)
			except Exception, msg:
				# Most of the time we have an html page here, it could also be an unrecognized format
				print 'Error:endElement(%s):Title:%s:%s' % (name.encode("utf8"), title, msg)

			item = BrowserMatch(title, url, True, icon=pixbuf)
			self._indexer.add("%s %s" % (title, url), item)

	def characters(self, chars):
		None
	
	def endElement(self, name):
		None
