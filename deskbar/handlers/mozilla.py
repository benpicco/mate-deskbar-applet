from ConfigParser import RawConfigParser
from deskbar.core.BrowserMatch import BrowserSmartMatch, BrowserMatch, is_preferred_browser, get_preferred_browser
from deskbar.core.GconfStore import GconfStore
from deskbar.core.Watcher import FileWatcher, DirWatcher
from deskbar.defs import VERSION
from gettext import gettext as _
from os.path import join, expanduser, exists, basename
from xml.dom import minidom
import HTMLParser
import base64
import deskbar
import deskbar.core.Indexer
import deskbar.interfaces.Module
import glob
import gtk
import logging
import os
import re
import subprocess
import urllib
LOGGER = logging.getLogger(__name__)

# Check for presence of set to be compatible with python 2.3
try:
    set
except NameError:
    from sets import Set as set

# Whether we will index firefox or mozilla bookmarks
USING_FIREFOX = False
if is_preferred_browser("firefox") or is_preferred_browser("iceweasel"):
    USING_FIREFOX = True
    
# Minimum and maximum version of Firefox
MIN_FF_VERSION = [2, 0, 0, 0]
MAX_FF_VERSION = [3, 0, 0, 0] # exclusively
MIN_FF_VERSION_STRING = "2.0.0.0"
MAX_FF_VERSION_STRING = "3.0.0.0"
        
# File returned here should be checked for existence
def get_mozilla_home_file(needed_file):    
    default_profile_dir = expanduser("~/.mozilla/default")
    if exists(default_profile_dir):
        for d in os.listdir(default_profile_dir):
            return join(default_profile_dir, d, needed_file)
    
    return ""
    
def get_firefox_home_file(needed_file):
    firefox_dir = expanduser("~/.mozilla/firefox/")
    config = RawConfigParser({"Default" : 0})
    config.read(expanduser(join(firefox_dir, "profiles.ini")))
    path = None

    for section in config.sections():
        if config.has_option(section, "Default") and config.get(section, "Default") == "1":
            path = config.get (section, "Path")
            break
        elif path == None and config.has_option(section, "Path"):
            path = config.get (section, "Path")
        
    if path == None:
        return ""

    if path.startswith("/"):
        return join(path, needed_file)

    return join(firefox_dir, path, needed_file)

def get_firefox_version():
    browser = get_preferred_browser ()
    process = subprocess.Popen(browser + " -version", stdout=subprocess.PIPE, shell=True)
    process.wait()
    info = process.stdout.readline().split(" ")
    pattern = re.compile("([0-9]+?)\.([0-9]+?)(\.([0-9]+))*")
    version = None
    for word in info:
        if pattern.match(word):
            match = pattern.match(word)
            version = word[match.start():match.end()]
    
    if version != None:
        # Convert to integers
        version = [int(i) for i in version.split(".")]
        # List must have 4 elements
        if len(version) < 4:
            while (len(version) < 4):
                version.append(0)
        return version
    else:
        return None

# Whether we offer all of the browser's search engines, or only the primary
# one (since by default Firefox seems to come with at least half a dozen)            
GCONF_SHOW_ONLY_PRIMARY_KEY = GconfStore.GCONF_DIR + "/mozilla/show_only_primary_search"
SHOW_ONLY_PRIMARY = GconfStore.get_instance().get_client().get_bool(GCONF_SHOW_ONLY_PRIMARY_KEY)
if SHOW_ONLY_PRIMARY == None:
    SHOW_ONLY_PRIMARY = False
def _on_gconf_show_only_primary(value):
    global SHOW_ONLY_PRIMARY
    SHOW_ONLY_PRIMARY = value
GconfStore.get_instance().get_client().notify_add(GCONF_SHOW_ONLY_PRIMARY_KEY, lambda x, y, z, a: _on_gconf_show_only_primary(z.value.get_bool()))

# TODO re-load PRIMARY_SEARCH_ENGINE everytime it changes (which should happen
# only rarely).  One (unavoidable) problem may be that firefox doesn't actually
# save the change to disk until you quit firefox.

# Google is the default search engine 
PRIMARY_SEARCH_ENGINE = "Google"
try:
    if USING_FIREFOX:
        prefs_file = file(get_firefox_home_file("prefs.js"))
        for line in prefs_file:
            if line.startswith('user_pref("browser.search.selectedEngine", "'):
                line = line.strip()
                PRIMARY_SEARCH_ENGINE = line[len('user_pref("browser.search.selectedEngine", "'):-len('");')]
                break
        prefs_file.close()
    # TODO - similar functionality for old-school mozilla (not firefox)
except:
    pass

def _on_handler_preferences(dialog):
    def toggled_cb(sender, show_all_radio, show_primary_radio):
        GconfStore.get_instance().get_client().set_bool(GCONF_SHOW_ONLY_PRIMARY_KEY, show_primary_radio.get_active())
        
    def sync_ui(new_show_only_primary, show_all_radio, show_primary_radio):
        show_all_radio.set_active(not new_show_only_primary)
        show_primary_radio.set_active(new_show_only_primary)
    
    builder = gtk.Builder()
    builder.add_from_file(os.path.join(deskbar.SHARED_DATA_DIR, "mozilla-search.ui"))
    dialog = builder.get_object("prefs-dialog")
    show_all_radio = builder.get_object("show_all_radio")
    show_primary_radio = builder.get_object("show_primary_radio")
    
    show_primary_radio.set_active(SHOW_ONLY_PRIMARY)
    show_all_radio.set_active(not SHOW_ONLY_PRIMARY)
    
    show_all_radio.connect ("toggled", toggled_cb, show_all_radio, show_primary_radio)
    show_primary_radio.connect ("toggled", toggled_cb, show_all_radio, show_primary_radio)
    
    notify_id = GconfStore.get_instance().get_client().notify_add(GCONF_SHOW_ONLY_PRIMARY_KEY, lambda x, y, z, a: sync_ui(z.value.get_bool(), show_all_radio, show_primary_radio))
    dialog.set_icon_name("deskbar-applet")
    dialog.show_all()
    dialog.run()
    dialog.destroy()
    GconfStore.get_instance().get_client().notify_remove(notify_id)
    

        
HANDLERS = ["MozillaBookmarksHandler",
    "MozillaSearchHandler",
    "MozillaHistoryHandler"]

class MozillaBookmarksHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("stock_bookmark"),
             "name": _("Web Bookmarks (Mozilla)"),
             "description": _("Open your web bookmarks by name"),
             "version": VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
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
        
    def query(self, query):
        # First, check the smart bookmarks, or "keywords", where
        # "wp Foo" takes you to the wikipedia entry for Foo.
        matches = self.query_smart_bookmarks(query, deskbar.DEFAULT_RESULTS_PER_HANDLER)
        if matches == None:
            # If none of the smart bookmarks matched as a prefix,
            # then we'll just look up all bookmarks.
            matches = self._bookmarks.look_up(query)[:deskbar.DEFAULT_RESULTS_PER_HANDLER]
        self.set_priority_for_matches( matches )
        self._emit_query_ready(query, matches )
    
    def query_smart_bookmarks(self, query, max):
        # if one of the smart bookmarks' shortcuts matches as a prefix,
        # then only return that bookmark
        x = query.find(" ")
        if x != -1:
            prefix = query[:x]
            try:
                b = self._shortcuts_to_smart_bookmarks_map[prefix]
                text = query[x+1:]
                return [BrowserSmartMatch(b.get_name(), b.url, prefix, b, pixbuf=b.get_icon())]
            except KeyError:
                # Probably from the b = ... line.  Getting here
                # means that there is no such shortcut.
                pass
        return None
    
    @staticmethod
    def has_requirements():
        if is_preferred_browser("mozilla"):
            return True
        elif is_preferred_browser("firefox") or is_preferred_browser("iceweasel"):
            if MozillaBookmarksHandler.has_firefox_version():
                return True
            
            MozillaBookmarksHandler.INSTRUCTIONS = \
                _("Firefox version must be at least %s and less than %s") % (MIN_FF_VERSION_STRING, MAX_FF_VERSION_STRING)
            return False
        else:
            MozillaBookmarksHandler.INSTRUCTIONS = _("Mozilla/Firefox is not your preferred browser.")
            return False
        
    @staticmethod
    def has_firefox_version():
        version = get_firefox_version()
        if version != None:
            return (version >= MIN_FF_VERSION and version < MAX_FF_VERSION)
        return False
        

class MozillaSearchHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("web-search.png"),
             "name": _("Web Searches (Mozilla)"),
             "description": _("Search the web via your browser's search settings"),
             "version": VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self._smart_bookmarks = None
    
    def initialize(self):
        smart_dirs = None
        if USING_FIREFOX:
            smart_dirs = [
                get_firefox_home_file("searchplugins"),
                get_firefox_home_file("search"),
                expanduser("~/.mozilla/searchplugins"),
                "/usr/local/lib/firefox/searchplugins",
                "/usr/lib/mozilla-firefox/searchplugins",
                "/usr/local/lib/mozilla-firefox/searchplugins",
                "/usr/lib/iceweasel/searchplugins"] + \
                glob.glob("/usr/lib*/firefox*/searchplugins")
        else:
            smart_dirs = [
                get_mozilla_home_file("search"),
                expanduser("~/.mozilla/searchplugins"),
                "/usr/lib/mozilla/searchplugins",
                "/usr/local/lib/mozilla/searchplugins"]
        
        if not hasattr(self, 'watcher'):
            self.watcher = DirWatcher()
            self.watcher.connect('changed', lambda watcher, f: self._parse_search_engines(smart_dirs))
        
        self.watcher.add(smart_dirs)
        self._parse_search_engines(smart_dirs)
        
    def _parse_search_engines(self, smart_dirs):
        self._smart_bookmarks = MozillaSmartBookmarksDirParser(smart_dirs).get_smart_bookmarks()
        self.set_priority_for_matches(self._smart_bookmarks)

    def stop(self):
        self.watcher.remove_all()
        
    def query(self, query):
        self.set_priority_for_matches (self._smart_bookmarks)
        if SHOW_ONLY_PRIMARY and PRIMARY_SEARCH_ENGINE != None:
            for s in self._smart_bookmarks:
                if s.get_name() == PRIMARY_SEARCH_ENGINE:
                    self._emit_query_ready(query, [s] )
                    return
            self._emit_query_ready(query, self._smart_bookmarks )
        else:
            self._emit_query_ready(query, self._smart_bookmarks )
    
    def has_config(self):
        return True
    
    def show_config(self, parent):
        _on_handler_preferences(parent)
    
    @staticmethod
    def has_requirements():
        if is_preferred_browser("firefox") or is_preferred_browser("iceweasel"):
            if is_preferred_browser("firefox") and not MozillaBookmarksHandler.has_firefox_version():
                
                MozillaSearchHandler.INSTRUCTIONS = \
                    _("Firefox version must be at least %s and less than %s") % (MIN_FF_VERSION_STRING, MAX_FF_VERSION_STRING)
                return False
            
            # Correct firefox version or iceweasel
            MozillaSearchHandler.INSTRUCTIONS = _("You can customize which search engines are offered.")
            return True
        elif is_preferred_browser("mozilla"):
            # TODO - similar functionality for old-school mozilla (not firefox)
            return True
        else:
            MozillaSearchHandler.INSTRUCTIONS = _("Mozilla/Firefox is not your preferred browser.")
            return False
        
class MozillaBookmarksParser(HTMLParser.HTMLParser):
    def __init__(self, handler):
        HTMLParser.HTMLParser.__init__(self)
        
        self.handler = handler
        
        self.chars = ""
        self.href = None
        self.icon_data = None
        self.bookmarks = set()
        self._shortcuts_to_smart_bookmarks_map = {}
        
        self._indexer = deskbar.core.Indexer.Indexer()
        
        try:
            if USING_FIREFOX:
                self.indexed_file = self._index_firefox()
            else:
                self.indexed_file = self._index_mozilla()
            self.close()
        except Exception, e:
            LOGGER.error('Could not index Firefox bookmarks')
            LOGGER.exception(e)
        
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
            LOGGER.error('Retrieving Mozilla Bookmarks')
            LOGGER.exception(msg)
        
    def _index_firefox(self):
        try:
            bookmarks_file = get_firefox_home_file("bookmarks.html")
            if exists(bookmarks_file):
                self.feed(file(bookmarks_file).read())
                return bookmarks_file
        except Exception, msg:
            LOGGER.error('Retrieving Firefox Bookmarks')
            LOGGER.exception(msg)
    
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "a":
            self.chars = ""
            self.href = None
            self.icon_data = None
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
            if self.href == None or self.href.startswith("javascript:"):
                return
            
            pixbuf = None
            if self.icon_data != None:
                loader = gtk.gdk.PixbufLoader()
                try:
                    # data:text/html;base64 should be the Header
                    header, content = self.icon_data.split(",", 2)
                    loader.set_size(deskbar.ICON_HEIGHT, deskbar.ICON_HEIGHT)
                    try:
                        # Python 2.4
                        loader.write(base64.b64decode(urllib.unquote(content)))
                    except AttributeError:
                        # Python 2.3 and earlier
                        loader.write(base64.decodestring(urllib.unquote(content)))
                finally:
                    loader.close()
                    pixbuf = loader.get_pixbuf()
                # Reset icon data for the following icon
                self.icon_data = None
                
            bookmark = BrowserMatch(self.chars, self.href, pixbuf=pixbuf)
            if self.shortcuturl != None:
                bookmark = BrowserSmartMatch(self.chars, self.href, self.shortcuturl, bookmark, pixbuf=pixbuf)
                self._shortcuts_to_smart_bookmarks_map[self.shortcuturl] = bookmark
            else:
                self._indexer.add("%s %s" % (self.chars, self.href), bookmark)

    def handle_data(self, chars):
        self.chars = self.chars + chars

class Firefox2SearchEngineParser :
    def __init__ (self, filename):
        self.filename = filename
        
        self._infos = {
            "name" : "",
            "action" : "",
            "description" : "",
            "url" : ""
        }
        
        self._namespace = None
        
    def get_infos (self):
        return self._infos
    
    def parse (self):
        xml = minidom.parse(self.filename)
        
        self._detect_namespace(xml)
        
        self._parse_name (xml)
        self._parse_description (xml)
        self._parse_action_and_url (xml)
        
        try:
            self._parse_image (xml)
        except Exception, msg:
            LOGGER.error("Parsing icon for %s\n%s", self.filename, msg)
    
    def _detect_namespace (self, xml):
        # Manually added search engines use the "os" namespace
        # for some reason.
        try:
            plugin = xml.getElementsByTagName ("SearchPlugin")[0]
            ns = plugin.getAttribute("xmlns:os")
            if ns == "":
                return
            self._namespace = "os"            
        except:
            pass
            
    def _ns_convert (self, tagname):
        # Convert the tag to the configured xml namespace
        if self._namespace is not None:
            return self._namespace + ":" + tagname
        else:
            return tagname
    
    def _parse_name (self, xml):
        for node in xml.getElementsByTagName (self._ns_convert("ShortName"))[0].childNodes:
            self._infos ["name"] += node.data
    
    def _parse_description (self, xml):
        for node in xml.getElementsByTagName (self._ns_convert("Description"))[0].childNodes:
            self._infos ["description"] += node.data
            
    def _parse_action_and_url (self, xml):
        
        # Some search engines have multiple Url tags
        # - fx. to a suggest-service, so we have to
        # detect the correct one. It will be the one
        # with type text/html.
        url_node = None
        for node in xml.getElementsByTagName (self._ns_convert("Url")):
            if node.getAttribute("type") == "text/html":
                url_node = node
                break 
        
        if url_node is None:
            raise ParseException ("No Url tag of type text/html in %s" % self.filename)
        
        self._infos ["url"] = url_node.getAttribute ("template")
        self._infos ["action"] = self._infos["url"]
        
        # Append search paramters to the action url
        params = ""
        for param in url_node.getElementsByTagName(self._ns_convert("Param")):
            key = param.getAttribute ("name")
            value = param.getAttribute ("value")            
            params += "&%s=%s" % (key,value)
        
        # Cut away leading & in param string
        params = params[1:]
        
        if params != "":
            self._infos["action"] += "?" + params
        
        # Escape the "{searchTerms}" parameter and take care of spelling variations
        self._infos["action"] = self._infos["action"].replace("{searchTerms}", "%s")
        self._infos["action"] = self._infos["action"].replace("{SearchTerms}", "%s")
        
    
    def _parse_image (self, xml):
        # The Image tag contains a base64 encoded image 
        try:
            # Some custom search engines might now contain a favicon
            img_tag = xml.getElementsByTagName(self._ns_convert("Image"))[0]
        except:
            return
        
        loader = gtk.gdk.PixbufLoader()
        loader.set_size(deskbar.ICON_HEIGHT, deskbar.ICON_HEIGHT)
        
        content = ""
        for data in img_tag.childNodes:
            content += data.data
        
        # Strip header data before decoding the base64 image
        header = "data:image/x-icon;base64,"
        content = content[content.index(header) + len(header):]
        
        try:
            # Python 2.4
            loader.write(base64.b64decode(urllib.unquote(content)))
        except AttributeError:
            # Python 2.3 and earlier
            loader.write(base64.decodestring(urllib.unquote(content)))
        
        loader.close()
        pixbuf = loader.get_pixbuf()
        self._infos["pixbuf"] = pixbuf
                
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
        
        img = self._find_icon ()
        if img is not None:
            infos["icon"] = img
        
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
    
    def _find_icon (self):
        try:
            parent_dir = self.f[:self.f.rindex("/")]
            return [img for img in glob.glob(join(parent_dir, '%s.*' % self.f[:-4])) if not img.endswith(".src")][0]
        except Exception, msg:
            LOGGER.warning("Error detecting icon for smart bookmark:%s\n%s", self.f, msg)
            return None
    
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
    def __init__ (self, msg): Exception.__init__(self, msg)
class ParseException(Exception):
    def __init__ (self, msg): Exception.__init__(self, msg)
    
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
    def __init__(self, dirs):
        self._smart_bookmarks = []
        
        # Avoid getting duplicate search engines
        bookmark_names = []
        
        # Full path to detected bookmark file
        found_bookmarks = []
        
        for bookmarks_dir in dirs:
            if not exists(bookmarks_dir):
                continue
            
            # Detect Firefox <= 1.5 search engines  
            for f in glob.glob(join(bookmarks_dir, '*.src')):
                # Check if we already parsed the file
                if not basename(f) in bookmark_names:
                    found_bookmarks.append(f)
                    bookmark_names.append(basename(f))
            
            # Detect Firefox >= 2.0 search engines
            for f in glob.glob(join(bookmarks_dir, '*.xml')):
                # Check if we already parsed the file
                if not basename(f) in bookmark_names:
                    found_bookmarks.append(f)
                    bookmark_names.append(basename(f))
      
        for f in found_bookmarks:
            img = None
            if f.endswith (".xml"):
                # Firefox >= 2.0 format
                parser = Firefox2SearchEngineParser (f)
            else:
                # f ends with ".src" and is in Firefox <= 1.5 format 
                parser = MozillaSmartBookmarksParser(f)
                            
            try:
                parser.parse()
                infos = parser.get_infos()
                
                if infos.has_key("pixbuf"):
                    bookmark = BrowserMatch(infos["name"], infos["url"], pixbuf=infos["pixbuf"])
                    bookmark = BrowserSmartMatch(infos["name"], infos["action"], pixbuf=infos["pixbuf"], bookmark=bookmark)
                elif infos.has_key ("icon"):
                    bookmark = BrowserMatch(infos["name"], infos["url"], icon=infos["icon"])
                    bookmark = BrowserSmartMatch(infos["name"], infos["action"], icon=infos["icon"], bookmark=bookmark)
                else:
                    bookmark = BrowserMatch(infos["name"], infos["url"])
                    bookmark = BrowserSmartMatch(infos["name"], infos["action"], bookmark=bookmark)
                    
                self._smart_bookmarks.append(bookmark)
                
            except Exception, msg:
                LOGGER.error('MozillaSmartBookmarksDirParser:cannot parse smart bookmark: %s\n%s', f, msg)
                    
    
    def get_smart_bookmarks(self):
        """
        Return a list of MozillaSmartMatch instances representing smart bookmarks
        """
        return self._smart_bookmarks

MOZILLA_HISTORY_REGEX = re.compile("\=http[0-9a-zA-Z\-\&\%\=\?\:\/\.]*\)")
class MozillaHistoryHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("epiphany-history.png"),
            "name": _("Web History (Mozilla)"),
            "description": _("Open your web history by name"),
             "version": VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self._history = None
    
    def initialize(self):
        self._indexer = deskbar.core.Indexer.Indexer()
        self._history = self._parse_history()
        for history_url in self._history:
            history_wo_http = history_url[history_url.find('//')+2:]
            if history_wo_http.find('www.') == -1:
                history_wo_www = history_wo_http
            else:
                history_wo_www = history_wo_http[history_wo_http.find('www.')+4:]
            self._indexer.add("%s %s %s" % (history_wo_www, history_wo_http, history_url), BrowserMatch(history_wo_www, history_url, True))
        
    def _parse_history(self):
        if USING_FIREFOX:
            historydat = get_firefox_home_file("history.dat")
        else:
            historydat = get_mozilla_home_file("history.dat")
        try:
            historycontents = file(historydat).read()
            historycontents = re.findall(MOZILLA_HISTORY_REGEX, historycontents)
            historycontents = [x[1:-1] for x in historycontents]
            return historycontents
        except:
            return ""
    
    def query(self, query):
        matches = self._indexer.look_up(query)[:deskbar.DEFAULT_RESULTS_PER_HANDLER]
        self.set_priority_for_matches( matches )
        self._emit_query_ready(query, matches )
        
    @staticmethod
    def has_requirements():
        if is_preferred_browser("mozilla"):
            return True
        elif is_preferred_browser("firefox") or is_preferred_browser("iceweasel"):
            if MozillaBookmarksHandler.has_firefox_version():
                return True
            
            MozillaHistoryHandler.INSTRUCTIONS = \
                _("Firefox version must be at least %s and less than %s") % (MIN_FF_VERSION_STRING, MAX_FF_VERSION_STRING)
            return False
        else:
            MozillaHistoryHandler.INSTRUCTIONS = _("Mozilla/Firefox is not your preferred browser.")
            return False

