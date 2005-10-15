import os, re, HTMLParser, base64, glob
from os.path import join, expanduser, exists, basename
from gettext import gettext as _

import gtk
import deskbar, deskbar.indexer

# Check for presence of set to be compatible with python 2.3
try:
	set
except NameError:
	from sets import Set as set

from deskbar.handlers_browsers import is_preferred_browser
from deskbar.handlers_browsers import BrowserHandler, BrowserSmartMatch, BrowserMatch

EXPORTED_CLASS, NAME, matched = is_preferred_browser(["firefox", "mozilla"],
							"MozillaHandler",
							(_("Mozilla/Firefox"), _("Index your bookmarks and search engines")),
							"Mozilla/Firefox is not your preferred browser, not using it.")
							
# Wether we will index firefox or mozilla bookmarks
USING_FIREFOX = False
if matched == "firefox":
	USING_FIREFOX = True
			
SEARCH_FIELD = re.compile(r'\s*(\w+)\s*=\s*"(.*)"\s*')
INPUT_VALUE = re.compile(r'<input\s+name="(.*?)"\s+value="(.*?)"\s*.*>', re.IGNORECASE)
INPUT_USER = re.compile(r'<input\s+name="(.*?)"\s+user.*>', re.IGNORECASE)

class MozillaHandler(BrowserHandler):
	def __init__(self):
		BrowserHandler.__init__(self)
		self._history = deskbar.indexer.Index()
	
	def _parse_bookmarks(self):
		indexed = MozillaBookmarksParser(self)
		
		smart_dirs = None
		if USING_FIREFOX:
			smart_dirs = [get_firefox_home_file("search"), "/usr/lib/mozilla-firefox/searchplugins"]
		else:
			smart_dirs = [get_mozilla_home_file("search"), "/usr/lib/mozilla/searchplugins"]
			
		parser = MozillaSmartBookmarksDirParser(self, indexed, smart_dirs)
		
		return (indexed.get_indexer(), parser.get_smart_bookmarks())

	def _parse_history(self):
		# Dummy function
		return self._history;

class MozillaBookmarksParser(HTMLParser.HTMLParser):
	def __init__(self, handler):
		HTMLParser.HTMLParser.__init__(self)
		
		self.handler = handler
		
		self.chars = ""
		self.href = None
		self.icon_data = None
		self.bookmarks = set()
		
		self._indexer = deskbar.indexer.Index()
		
		if USING_FIREFOX:
			self._index_firefox()
		else:
			self._index_mozilla()
		self.close()
		
	def get_indexer(self):
		"""
		Returns a completed indexer with the contents of bookmark file
		"""
		return self._indexer
		
	def _index_mozilla(self):
		try:
			bookmarks_file = get_mozilla_home_file("bookmarks.html")
			if exists(bookmarks_file):
				self.feed(file(bookmarks_file).read())
		except Exception, msg:
			print 'Error retreiving Mozilla Bookmarks:', msg
		
	def _index_firefox(self):
		try:
			bookmarks_file = get_firefox_home_file("bookmarks.html")
			if exists(bookmarks_file):
				self.feed(file(bookmarks_file).read())
		except Exception, msg:
			print 'Error retreiving Mozilla Bookmarks:', msg
	
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
					try:
						# Python 2.4
						loader.write(base64.b64decode(content))
					except AttributeError:
						# Python 2.3 and earlier
						loader.write(base64.decodestring(content))
					loader.close()
					pixbuf = loader.get_pixbuf()
				except Exception, msg:
					print 'Error:mozilla.py:handle_endtag:', msg
				# Reset icon data for the following icon
				self.icon_data = None
				
			bookmark = BrowserMatch(self.handler, self.chars, self.href, pixbuf)
			self._indexer.add("%s %s" % (self.chars, self.href), bookmark)

	def handle_data(self, chars):
		self.chars = self.chars + chars

class MozillaSmartBookmarksParser:	
	def __init__(self, f):
		self.name = None
		self.description = None
		self.action = None
		self.args = "?"
		self.url = None
		
		self._parse_file(f)
	
	def _parse_file(self, source):
		lines = file(source).readlines()
	
		state = "start"
		for line in lines:
			low = line.strip().lower()
			# Skip comments and empty lines
			if low.startswith("#") or low == "":
				continue
			
			if state == "start":
				if low.startswith("<search"):
					state = "search"
					continue
			elif state == "search":		
				if low.endswith(">"):
					state = "input"
					continue
				self._parse_search(line)				
			elif state == "input":
				if not low.startswith("<input "):
					state = "end"
					continue
				self._parse_input(line)
			else:
				break
				
		if self.args.endswith("&"):
			self.args = self.args[:-1]
		
		# FIXME: If we don't have a real fallback url, doing this will most probably
		# result in some error. Ideally, we should use gnomevfs to extract the
		# simple hostname, for example: https://www.amazon.com/obidos/blah/q=%s&ie=7753829
		# should be trimmed to https://www.amazon.com
		if self.url == None:
			self.url = self.action
			
		self.action = self.action + self.args
	
	def _parse_search(self, line):
		match = SEARCH_FIELD.match(line)
		if match != None:
			key, val = match.group(1).lower(), match.group(2)
			if key == "name":
				self.name = val
			elif key == "description":
				self.description = val
			elif key == "action":
				self.action = val
			elif key == "searchform":
				self.url = val
		else:
			print 'Error:_parse_search:No way to extract a <SEARCH field:',line
			
	def _parse_input(self, line):
		match = INPUT_VALUE.match(line)
		if match != None:
			self.args = '%s%s=%s&' % (self.args, match.group(1), match.group(2))
			return
		
		match = INPUT_USER.match(line)
		if match != None:
			self.args = '%s%s=%%s&' % (self.args, match.group(1))
			return
		
		print 'Error:_parse_input:Cannot extract <input> tag:',line

class MozillaSmartBookmarksDirParser:
	def __init__(self, handler, indexer, dirs):
		self._smart_bookmarks = []
		
		# Avoid getting duplicate search engines
		foundbookmarks = []
		
		for bookmarks_dir in dirs:
			if not exists(bookmarks_dir):
				continue
				
			for f in glob.glob(join(bookmarks_dir, '*.src')):
				# Check if we already parsed the file
				bmname = basename(f)
				if bmname in foundbookmarks:
					continue
				else:
					foundbookmarks.append(bmname)
					
				pixbuf = None
				try:
					img = [img for img in glob.glob(join(bookmarks_dir, '%s.*' % f[:-4])) if not img.endswith(".src")][0]
					pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(img, deskbar.ICON_SIZE, deskbar.ICON_SIZE)
				except Exception, msg:
					print 'Error:MozillaSmartBookmarksDirParser:Cannot load image:%s' % msg
				
				parser = MozillaSmartBookmarksParser(f)
				bookmark = BrowserMatch(handler, parser.name, parser.url, pixbuf)
				indexer.add("%s %s %s" % (parser.name, parser.url, parser.description), bookmark)

				bookmark = BrowserSmartMatch(bookmark, parser.name, parser.action)
				self._smart_bookmarks.append(bookmark)
	
	def get_smart_bookmarks(self):
		"""
		Return a list of MozillaSmartMatch instances representing smart bookmarks
		"""
		return self._smart_bookmarks
		
#File returned here need to be checked for existence
def get_mozilla_home_file(needed_file):	
	default_profile_dir = expanduser("~/.mozilla/default")
	if exists(default_profile_dir):
		for d in os.listdir(default_profile_dir):
			return join(default_profile_dir, d, needed_file)
	
	return ""
	
def get_firefox_home_file(needed_file):
	firefox_dir = expanduser("~/.mozilla/firefox/")
	path_pattern = re.compile("^Path=(.*)")
	for line in file(join(firefox_dir, "profiles.ini")):
		match_obj = path_pattern.search(line)
		if match_obj:
			if match_obj.group(1).startswith("/"):
				return join(match_obj.group(1), needed_file)
			else:
				return join(firefox_dir, match_obj.group(1), needed_file)
				
	return ""
