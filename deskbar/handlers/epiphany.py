import xml.sax
from os.path import join, expanduser, exists
from gettext import gettext as _
import gtk
import deskbar, deskbar.indexer, deskbar.handler
from deskbar.filewatcher import FileWatcher
from deskbar.handlers_browsers import get_url_host, is_preferred_browser, on_customize_search_shortcuts, on_entry_key_press, load_shortcuts
from deskbar.handlers_browsers import BrowserSmartMatch, BrowserMatch

def _check_requirements():
	if deskbar.UNINSTALLED_DESKBAR:
		return (deskbar.handler.HANDLER_IS_HAPPY, None, None)
		
	if is_preferred_browser("epiphany"):
		return (deskbar.handler.HANDLER_IS_HAPPY, None, None)
	else:
		return (deskbar.handler.HANDLER_IS_NOT_APPLICABLE, "Epiphany is not your preferred browser, not using it.", None)
	
def _check_requirements_search():
	callback = lambda: on_customize_search_shortcuts(smart_bookmarks, shortcuts_to_smart_bookmarks_map)
	
	if deskbar.UNINSTALLED_DESKBAR:
		return (deskbar.handler.HANDLER_IS_CONFIGURABLE, "You can set shortcuts for your searches.", callback)
		
	if is_preferred_browser("epiphany"):
		return (deskbar.handler.HANDLER_IS_CONFIGURABLE, "You can set shortcuts for your searches.", callback)
	else:
		return (deskbar.handler.HANDLER_IS_NOT_APPLICABLE, "Epiphany is not your preferred browser, not using it.", None)
	
HANDLERS = {
	"EpiphanyBookmarksHandler": {
		"name": _("Web Bookmarks"),
		"description": _("Open your web bookmarks by name"),
		"requirements": _check_requirements
	},
	"EpiphanyHistoryHandler": {
		"name": _("Web History"),
		"description": _("Open your web history by name"),
		"requirements": _check_requirements
	},
	"EpiphanySearchHandler": {
		"name": _("Web Searches"),
		"description": _("Search the web via your browser's search settings"),
		"requirements": _check_requirements_search
	},
}

EPHY_BOOKMARKS_FILE = expanduser("~/.gnome2/epiphany/bookmarks.rdf")
EPHY_HISTORY_FILE   = expanduser("~/.gnome2/epiphany/ephy-history.xml")

favicon_cache = None
bookmarks = None
smart_bookmarks = None
shortcuts_to_smart_bookmarks_map = {}

class EpiphanyHandler(deskbar.handler.Handler):
	def __init__(self, watched_file, callback):
		deskbar.handler.Handler.__init__(self, "web-browser.png")
		self.watched_file = watched_file
		self.watch_callback = callback
		
	def initialize(self):
		global favicon_cache
		if not hasattr(self, 'watcher'):
			self.watcher = FileWatcher()
			self.watcher.connect('changed', lambda watcher, f: self.watch_callback())
			
		self.watcher.add(self.watched_file)
		
		if favicon_cache == None:
			favicon_cache = EpiphanyFaviconCacheParser().get_cache()
	
	def stop(self):
		self.watcher.remove(self.watched_file)
		
class EpiphanyBookmarksHandler(EpiphanyHandler):
	def __init__(self):
		EpiphanyHandler.__init__(self, EPHY_BOOKMARKS_FILE, lambda: self._parse_bookmarks(True))
				
	def initialize(self):
		EpiphanyHandler.initialize(self)
		self._parse_bookmarks()
		
	def _parse_bookmarks(self, force=False):
		global favicon_cache, bookmarks, smart_bookmarks
		if force or bookmarks == None:
			parser = EpiphanyBookmarksParser(self, favicon_cache)
			bookmarks = parser.get_indexer()
			smart_bookmarks = parser.get_smart_bookmarks()
			load_shortcuts(smart_bookmarks, shortcuts_to_smart_bookmarks_map)
		
	def query(self, query, max=5):
		global bookmarks
		return bookmarks.look_up(query)[:max]

class EpiphanySearchHandler(EpiphanyBookmarksHandler):
	def __init__(self):
		EpiphanyBookmarksHandler.__init__(self)
	
	def on_entry_key_press(self, entry, event, applet):
		return on_entry_key_press(entry, event, applet, shortcuts_to_smart_bookmarks_map)
	
	def query(self, query, max=5):
		# if one of the smart bookmarks' shortcuts matches as a prefix,
		# then only return that bookmark
		x = query.find(" ")
		if x != -1:
			prefix = query[:x]
			try:
				b = shortcuts_to_smart_bookmarks_map[prefix]
				text = query[x+1:]
				return [BrowserSmartMatch(b._bookmark, b._name, b._url, prefix)]
			except KeyError:
				# Probably from the b = ... line.  Getting here
				# means that there is no such shortcut.
				pass
		
		return smart_bookmarks
		
class EpiphanyHistoryHandler(EpiphanyHandler):
	def __init__(self):
		EpiphanyHandler.__init__(self, EPHY_HISTORY_FILE, self._parse_history)
		self._history = None
		
	def initialize(self):
		EpiphanyHandler.initialize(self)
		self._parse_history()
		
	def _parse_history(self):
		global favicon_cache
		self._history = EpiphanyHistoryParser(self, favicon_cache).get_indexer()
			
	def query(self, query, max=5):
		return self._history.look_up(query)[:max]
		
class EpiphanyBookmarksParser(xml.sax.ContentHandler):
	def __init__(self, handler, cache):
		xml.sax.ContentHandler.__init__(self)
		
		self.handler = handler
		
		self.chars = ""
		self.title = None
		self.href = None
		self.smarthref = None
		
		self._indexer = deskbar.indexer.Index()
		self._smart_bookmarks = []
		self._cache = cache;
		
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
		if exists(EPHY_BOOKMARKS_FILE):
			parser = xml.sax.make_parser()
			parser.setContentHandler(self)
			parser.parse(EPHY_BOOKMARKS_FILE)
	
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
			if self.smarthref != None:
				bookmark = BrowserSmartMatch(bookmark, self.title, self.smarthref)
				self._smart_bookmarks.append(bookmark)
			else:
				self._indexer.add("%s %s" % (self.title, self.href), bookmark)

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



class EpiphanyHistoryParser(xml.sax.ContentHandler):
	def __init__(self, handler, cache):
		xml.sax.ContentHandler.__init__(self)

		self.handler = handler;
		self._cache = cache;
		
		self.url = None
		self.title = None
		self.icon = None
		self._id = None;
	
		self._indexer = deskbar.indexer.Index()

		self._index_history();

	def get_indexer(self):
		"""
		Returns a completed indexer with the contents of the history file
		"""
		return self._indexer;

	def _index_history(self):
		if exists(EPHY_HISTORY_FILE):
			parser = xml.sax.make_parser()
			parser.setContentHandler(self)
			parser.parse(EPHY_HISTORY_FILE)

	
	def characters(self, chars):
		self.chars = self.chars + chars
		
	def startElement(self, name, attrs):
		self.chars = ""
		if name == "property":
			self._id = attrs['id']

		if name == "node":
			self.title = None
			self.url = None
			self.icon = None

	def endElement(self, name):
		if name == "property":
			if self._id == "2":
				self.title = self.chars.encode('utf8')
			elif self._id == "3":
				self.url = self.chars.encode('utf8')
			elif self._id == "9":
				self.icon = self.chars.encode('utf8')
		elif name == "node":
			pixbuf = None
			try:
				if self.icon in self._cache:
					pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self._cache[self.icon], deskbar.ICON_SIZE, deskbar.ICON_SIZE)
			except Exception, msg:
				# Most of the time we have an html page here, it could also be an unrecognized format
				print 'Error:endElement(%s):Title:%s:%s' % (name.encode("utf8"), self.title, msg)

			item = BrowserMatch(self.handler, self.title, self.url, pixbuf, True)
			self._indexer.add("%s %s" % (self.title, self.url), item)
