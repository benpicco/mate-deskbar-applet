import os, cgi, re, HTMLParser, base64
from os.path import join, expanduser, exists
from gettext import gettext as _

import gtk, gnomevfs
import deskbar, deskbar.indexer
import deskbar.handler

EXPORTED_CLASS = "MozillaHandler"
NAME = _("Mozilla Bookmarks")

# Check for presence of set to be compatible with python 2.3
try:
	set
except NameError:
	from sets import Set as set

PRIORITY = 50

class MozillaMatch(deskbar.handler.Match):
	def __init__(self, backend, name, url, icon=None):
		deskbar.handler.Match.__init__(self, backend, cgi.escape(name), icon)
		self._priority = 10
		self._url = url
		
	def action(self, text=None):
		self._priority = self._priority+1
		gnomevfs.url_show(self._url)
		
	def get_verb(self):
		return _("Open mozilla bookmark <b>%(name)s</b>")

class MozillaHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "web-bookmark.png")
		
		parser = MozillaBookmarksParser(self)
		self._indexer = parser.get_indexer()
		self._smart_bookmarks = parser.get_smart_bookmarks()
		
	def get_priority(self):
		return PRIORITY
				
	def query(self, query, max=5):
		bmk = self._indexer.look_up(query)[:max]
		sbmk = self._smart_bookmarks[:max]
		
		#Merge the two sources
		result = []
		for b in bmk:
			result.append(b)
		for b in sbmk:
			if not b.get_bookmark() in bmk:
				result.append(b)
		
		return result
		
class MozillaBookmarksParser(HTMLParser.HTMLParser):
	def __init__(self, handler):
		HTMLParser.HTMLParser.__init__(self)
		
		self.handler = handler
		
		self.chars = ""
		self.href = None
		self.icon_data = None
		self.bookmarks = set()
		
		self._indexer = deskbar.indexer.Index()
		self._smart_bookmarks = []
		
		print 'Starting mozilla/ff bookmarks indexation'
		self._index_mozilla()
		self._index_firefox()
		self.close()
		print '\tDone !'
		
	def get_indexer(self):
		"""
		Returns a completed indexer with the contents of bookmark file
		"""
		return self._indexer
	
	def get_smart_bookmarks(self):
		"""
		Return a list of MozillaSmartMatch instances representing smart bookmarks
		"""
		return self._smart_bookmarks
	
	def _index_mozilla(self):
		bookmarks_file = None
		default_profile_dir = expanduser("~/.mozilla/default")
		if exists(default_profile_dir):
			for d in os.listdir(default_profile_dir):
				fn = join(default_profile_dir, d, "bookmarks.html")
				if exists(fn):
					bookmarks_file = fn
					break
		
		if bookmarks_file != None:
			self.feed(file(bookmarks_file).read())
		
	def _index_firefox(self):
		bookmarks_file = None
		try:
			firefox_dir = expanduser("~/.mozilla/firefox/")
			path_pattern = re.compile("^Path=(.*)")
			for line in file(join(firefox_dir, "profiles.ini")):
				match_obj = path_pattern.search(line)
				if match_obj:
					if match_obj.group(1).startswith("/"):
						bookmarks_file = join(match_obj.group(1), "bookmarks.html")
					else:
						bookmarks_file = join(firefox_dir, match_obj.group(1), "bookmarks.html")
					break
		except IOError, msg:
			print 'Error retreiving FF bookmark file:', msg

		if bookmarks_file != None:
			self.feed(file(bookmarks_file).read())
	
	def handle_starttag(self, tag, attrs):
		tag = tag.lower()
		if tag == "a":
			self.chars = ""
			for tag, value in attrs:
				if tag.lower() == 'href':
					self.href = value
				if tag.lower() == 'icon' and value != "data:" and value.startswith("data:"):
					self.icon_data = value

	def handle_endtag(self, tag):
		tag = tag.lower()
		if tag == "a":
			if self.href.startswith("javascript:"):
				return
			
			pixbuf = None
			if self.icon_data != None:
				try:
					# data:text/html;base64 should be the Header
					header, content = self.icon_data.split(",", 2)
					loader = gtk.gdk.PixbufLoader()
					loader.set_size(deskbar.ICON_SIZE, deskbar.ICON_SIZE)
					loader.write(base64.b64decode(content))
					loader.close()
					pixbuf = loader.get_pixbuf()
				except Exception, msg:
					print 'Error:mozilla.py:handle_endtag:', msg
				# Reset icon data for the following icon
				self.icon_data = None
				
			bookmark = MozillaMatch(self.handler, self.chars, self.href, pixbuf)
			self._indexer.add("%s %s" % (self.chars, self.href), bookmark)

	def handle_data(self, chars):
		self.chars = self.chars + chars
