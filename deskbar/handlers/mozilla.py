import os, re, HTMLParser, base64, glob
from os.path import join, expanduser, exists, basename
from gettext import gettext as _

import gtk
from deskbar.filewatcher import FileWatcher, DirWatcher
import deskbar, deskbar.indexer, deskbar.handler

# Check for presence of set to be compatible with python 2.3
try:
	set
except NameError:
	from sets import Set as set

from deskbar.handlers_browsers import is_preferred_browser
from deskbar.handlers_browsers import BrowserSmartMatch, BrowserMatch

def _on_customize_search_engines():
	pass
	
def _check_requirements():
	if deskbar.UNINSTALLED_DESKBAR:
		return (deskbar.handler.HANDLER_IS_HAPPY, None, None)
	
	#We will need to pass some preference here to select one/all engines
	if is_preferred_browser("firefox") or is_preferred_browser("mozilla"):
		return (deskbar.handler.HANDLER_IS_HAPPY, None, None)
	else:
		return (deskbar.handler.HANDLER_IS_NOT_APPLICABLE, "Mozilla/Firefox is not your preferred browser, not using it.", None)
		
HANDLERS = {
	"MozillaBookmarksHandler" : {
		"name": _("Web Bookmarks"),
		"description": _("Open your web bookmarks by name"),
		"requirements": _check_requirements
	},
	"MozillaSearchHandler" : {
		"name": _("Web Searches"),
		"description": _("Search the web via your browser's search settings"),
		"requirements": _check_requirements
	}
}

# Wether we will index firefox or mozilla bookmarks
USING_FIREFOX = False
if is_preferred_browser("firefox"):
	USING_FIREFOX = True
			
class MozillaBookmarksHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "web-bookmark.png")
		self._bookmarks = None
	
	def initialize(self):
		if not hasattr(self, 'watcher'):
			self.watcher = FileWatcher()
			self.watcher.connect('changed', lambda watcher, f: self._parse_bookmarks())
		
		# We do some gym to get the effectively parsed files
		parsed_file = self._parse_bookmarks()
		if parsed_file != None:
			self.watcher.add(parsed_file)
		
	def _parse_bookmarks(self):
		self._bookmarks, parsed_file, self._shortcuts_to_smart_bookmarks_map = MozillaBookmarksParser(self).get_indexer()
		return parsed_file
	
	def stop(self):
		self.watcher.remove_all()
		
	def query(self, query, max=5):
		# First, check the smart bookmarks, or "keywords", where
		# "wp Foo" takes you to the wikipedia entry for Foo.
		x = self.query_smart_bookmarks(query, max)
		if x != None:
			return x
		else:
			# If none of the smart bookmarks matched as a prefix,
			# then we'll just look up all bookmarks.
			return self._bookmarks.look_up(query)[:max]
	
	def query_smart_bookmarks(self, query, max=5):
		# if one of the smart bookmarks' shortcuts matches as a prefix,
		# then only return that bookmark
		x = query.find(" ")
		if x != -1:
			prefix = query[:x]
			try:
				b = self._shortcuts_to_smart_bookmarks_map[prefix]
				text = query[x+1:]
				return [BrowserSmartMatch(b._bookmark, b._name, b._url, prefix)]
			except KeyError:
				# Probably from the b = ... line.  Getting here
				# means that there is no such shortcut.
				pass
		return None

class MozillaSearchHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "web-bookmark.png")
		self._smart_bookmarks = None
	
	def initialize(self):
		smart_dirs = None
		if USING_FIREFOX:
			smart_dirs = [get_firefox_home_file("searchplugins"), get_firefox_home_file("search"), expanduser("~/.mozilla/searchplugins"), "/usr/lib/mozilla-firefox/searchplugins"]
		else:
			smart_dirs = [get_mozilla_home_file("search"), expanduser("~/.mozilla/searchplugins"), "/usr/lib/mozilla/searchplugins"]
		
		if not hasattr(self, 'watcher'):
			self.watcher = DirWatcher()
			self.watcher.connect('changed', lambda watcher, f: self._parse_search_engines(smart_dirs))
		
		self.watcher.add(smart_dirs)
		self._parse_search_engines(smart_dirs)
		
	def _parse_search_engines(self, smart_dirs):	
		#TODO: if using firefox, show a way to enable only active search engine in a pref dialog.
		self._smart_bookmarks = MozillaSmartBookmarksDirParser(self, smart_dirs).get_smart_bookmarks()

	def stop(self):
		self.watcher.remove_all()
		
	def query(self, query, max=5):
		return self._smart_bookmarks
		
class MozillaBookmarksParser(HTMLParser.HTMLParser):
	def __init__(self, handler):
		HTMLParser.HTMLParser.__init__(self)
		
		self.handler = handler
		
		self.chars = ""
		self.href = None
		self.icon_data = None
		self.bookmarks = set()
		self._shortcuts_to_smart_bookmarks_map = {}
		
		self._indexer = deskbar.indexer.Index()
		
		if USING_FIREFOX:
			self.indexed_file = self._index_firefox()
		else:
			self.indexed_file = self._index_mozilla()
		self.close()
		
	def get_indexer(self):
		"""
		Returns a completed indexer with the contents of bookmark file,
		the name of the indexed file, and a map from shortcuts (or
		prefixes) to smart bookmarks - those bookmarks with %s in the
		URL.
		"""
		return (self._indexer, self.indexed_file, self._shortcuts_to_smart_bookmarks_map)
		
	def _index_mozilla(self):
		try:
			bookmarks_file = get_mozilla_home_file("bookmarks.html")
			if exists(bookmarks_file):
				self.feed(file(bookmarks_file).read())
				return bookmarks_file
		except Exception, msg:
			print 'Error retreiving Mozilla Bookmarks:', msg
		
	def _index_firefox(self):
		try:
			bookmarks_file = get_firefox_home_file("bookmarks.html")
			if exists(bookmarks_file):
				self.feed(file(bookmarks_file).read())
				return bookmarks_file
		except Exception, msg:
			print 'Error retreiving Mozilla Bookmarks:', msg
	
	def handle_starttag(self, tag, attrs):
		tag = tag.lower()
		if tag == "a":
			self.chars = ""
			self.shortcuturl = None
			for tag, value in attrs:
				if tag.lower() == 'href':
					self.href = value
				if tag.lower() == 'icon' and value != "data:" and value.startswith("data:"):
					self.icon_data = value
				if tag.lower() == 'shortcuturl':
					self.shortcuturl = value

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
			if self.shortcuturl != None:
				bookmark = BrowserSmartMatch(bookmark, self.chars, self.href, self.shortcuturl)
				self._shortcuts_to_smart_bookmarks_map[self.shortcuturl] = bookmark
			else:
				self._indexer.add("%s %s" % (self.chars, self.href), bookmark)

	def handle_data(self, chars):
		self.chars = self.chars + chars


						
class MozillaSmartBookmarksParser:
	def __init__(self, f):
		"""
		Init the parse, no exception here
		"""
		self.f = f
		self.infos = {
			"search": {},
			"input": {},
		}
	
	def get_infos(self):
		infos = {}
		
		args = "?"
		for key, arg in self.infos["input"].items():
			args += '%s=%s&' % (key, arg)
		
		if args.endswith("&"):
			args = args[:-1]
		
		infos["name"] = self.infos["search"]["name"]
		infos["description"] = self.infos["search"]["description"]

		# FIXME: If we don't have a real fallback url, doing this will most probably
		# result in some error. Ideally, we should use gnomevfs to extract the
		# simple hostname, for example: https://www.amazon.com/obidos/blah/q=%s&ie=7753829
		# should be trimmed to https://www.amazon.com
		if not "url" in self.infos["search"]:
			infos["url"] = self.infos["search"]["action"]
		else:
			infos["url"] = self.infos["search"]["url"]
			
		infos["action"] = self.infos["search"]["action"] + args
		return infos
		
	def parse(self):
		"""
		"""
		tokenizer = Tokenizer(self.f)
		n = state = None
		
		# We load the two first tokens, whch should be ["<", "search"]
		tokens = [tokenizer.get_next_token(), tokenizer.get_next_token()]
		while tokens[0] != None:
			# Retreive the next state, the number of tokens to read next, and any discarded tokens
			# by the handler, which should be handled on next iteration
			state, n, rest = self._handle_token(state, tokens)
			# If n == None, we finished parsing
			if n == None:
				break
			
			# Read the requested number of tokens, but count the ones that were rejected first
			tokens = rest
			for i in range(n - len(rest)):
				tokens.append(tokenizer.get_next_token())
	
	def _handle_token(self, state, tokens):
		if state == None and (tokens == ["<", "search"] or tokens == ["<", "SEARCH"]):
			return "search", 3, []
		elif state == None:
			raise ParseException("File %s does not begin with <search" % self.f)
		
		# Read key=value pairs and store them in the infos["search"] dict
		if state == "search" and tokens[1] == "=":
			self.infos["search"][tokens[0]] = tokens[2]
			return "search", 3, []
		
		# We reached the end of <Search tag, now in theory come the <input> tags
		if state == "search" or state == "anotherinput" and tokens == [">", "<", "input"]:
			return "input", 6, []
		elif state == "search":
			raise ParseException("Expecting <input after <search section in file %s" % self.f)
		
		# This parses the <input fields, taking each time 6 tokens
		# First triplet is name=value, second triplet is value=val
		# Special case for lone "user" second triplets, and store that in infos["input"] dict
		if state == "input" and tokens[1] == "=":
			if tokens[3] == "user":
				self.infos["input"][tokens[2]] = "%s"
				if tokens[4] != "=":
					return "anotherinput", 3, tokens[4:]
			else:
				self.infos["input"][tokens[2]] = tokens[5]
			return "anotherinput", 3, []
		
		# Here we stop processing, cause we are no longer in <input sections, and what comes after isn't interesting
		return None, None, None

class TokenException(Exception):
	pass
class ParseException(Exception):
	pass
	
class Tokenizer:
	def __init__(self, f):
		"""
		Init the tokenizer on the given file, may throw an exception.
		"""
		self.i = 0
		# Read the file, coud be streamed as well
		self.f = f
		self.data = file(f).read()
		
		self.state = "linestart"
		
	def get_next_token(self):
		"""
		Returns the next token in the file.
		A token is one of:
		< = > name
		
		Returns None when the end of file is reached and beyond
		"""
		while self.i < len(self.data):
			char = self.data[self.i]
			# Skip leading spaces (which are really trailing spaces after a token
			# Newline is important so special case it
			if char.isspace() and not char == "\n":
				self.i += 1
				continue
			
			if self.state == "linestart" and char == "#":
				# Eat all the comment line
				while self.i < len(self.data) and self.data[self.i] != "\n":
					self.i += 1
				self.i += 1 #position on first char after newline
				continue
			
			# At this point, we can only have a token, read it, and return it
			# The method updates the self.i to point to the new char to read next
			next_token = self.read_token()
			# Wait ! We got a newline here, so back to start again..
			if next_token == "\n":
				self.state = "linestart"
				continue
				
			return next_token
	
	def read_token(self):
		"""
		Return the token, self.i must point to the first char in this token.
		self.i is updated to point just after the returned token
		Returned token is one of:
		< = > \n name
		"""
		char = self.data[self.i]
		
		if char == "<" or char == "=" or char == ">" or char == "\n":
			self.i += 1
			return char
		
		elif char == "\"":
			# Here we assume proper quoting
			closing = self.data[self.i+1:].find("\"")
			if closing == -1:
				raise TokenException("Couldn't find a proper closing quote in %s" % self.f)
			
			token = self.data[self.i+1:self.i+1+closing]
			self.i += closing+2 #Next char is just *after* the closing "
			return token
		
		else:
			# Token can just be a string now..
			token = ""
			# We eat all chars until one of "=<>" or whitespace is found
			while self.i < len(self.data) and not self.data[self.i].isspace() and not self.data[self.i] in "=><":
				token += self.data[self.i]
				self.i += 1
				
			return token
			
class MozillaSmartBookmarksDirParser:
	def __init__(self, handler, dirs):
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
				try:
					parser.parse()
					infos = parser.get_infos()
					bookmark = BrowserMatch(handler, infos["name"], infos["url"], pixbuf)
					bookmark = BrowserSmartMatch(bookmark, infos["name"], infos["action"])
					self._smart_bookmarks.append(bookmark)
				except Exception, msg:
					print 'Error:MozillaSmartBookmarksDirParser:cannot parse smrt bookmark:%s:bookmark %s' % (msg, f)
					
	
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
