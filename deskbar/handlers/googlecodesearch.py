from deskbar.core.Utils import strip_html, get_proxy, htmldecode
from deskbar.defs import VERSION
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from os.path import basename
import deskbar
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import logging
import re
import urllib
import xml.sax
import xml.sax.handler

LOGGER = logging.getLogger(__name__)

HANDLERS = ["GoogleCodeSearchModule"]

MAX_RESULTS = 15
BASE_URL = "http://www.google.com/codesearch/feeds/search?%s"
    

class GoogleCodeSearchModule(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("google.png"),
             'name': _("Google Code Search"),
             'description': _("Search public source code for function definitions and sample code"),
             'version': VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        
    def _format_content(self, content, qstring):
        """
        Remove HTML tags and display only the first line
        that contains the search term
        """
        content_lines = strip_html(htmldecode(content)).split("\n")
        pattern = re.escape(qstring)
        new_content = ""
        for content in content_lines:
            if qstring in content:
                new_content += re.sub(pattern,
                              "<span weight='bold'>"+qstring+"</span>",
                              content.strip(),
                              re.IGNORECASE | re.MULTILINE)
                new_content += "\n"
        
        if len(new_content) > 0:
            return new_content.strip().replace("&", "&amp;")
        else:
            return None
        
    def query(self, qstring):
        url = BASE_URL % urllib.urlencode(
                {'q': qstring,
                 'max-results': MAX_RESULTS})
        
        matches = []
        
        try:
            stream = urllib.urlopen(url, proxies=get_proxy())
        except (IOError, EOFError), msg:
            LOGGER.error("Could not open URL %s: %s, %s", url, msg[0], msg[1])
            return
        
        try:
            try:
                handler = GoogleCodeSearchFeedParser()
                xml.sax.parse(stream, handler)
            except xml.sax.SAXParseException, e:
                LOGGER.exception(e)
                handler = None
        finally:
            stream.close()
                
        if handler == None:
            return
            
        results = handler.get_results()
        num_results = len(results)
        for i, result in enumerate(results):
            prio = self.get_priority() + num_results - i
            content = self._format_content(result["content"], qstring)
            matches.append(
                GoogleCodeSearchMatch(result["id"], result["title"], content,
                                      result["package-name"], result["package-uri"],
                                      priority=prio)
            )
            
        matches.append(GoogleCodeSearchForMatch(qstring, priority=self.get_priority()))
        self._emit_query_ready(qstring, matches)
    
class GoogleCodeSearchMatch(deskbar.interfaces.Match):
    
    def __init__(self, id, title, content, pkg_name, pkg_uri, **args):
        deskbar.interfaces.Match.__init__(self, name=title, category="web", icon="google.png", **args)
        self._id = id
        
        self.set_snippet(content)
        # Display only the filename and not the complete path
        self.add_action(OpenGoogleCodeSearchAction(basename(title), id), True)
        if pkg_uri.startswith("http") or pkg_uri.startswith("ftp"):
            self.add_action(GoToPackageLocationAction(basename(pkg_name), pkg_uri))
            self.add_action(CopyToClipboardAction(_("URL"), pkg_uri))
        
    def get_hash(self):
        return self._id
    
class OpenGoogleCodeSearchAction(ShowUrlAction):
    
    def __init__(self, name, url):
        ShowUrlAction.__init__(self, name, url)    
    
    def get_verb(self):
        return _("View <i>%(name)s</i> at <b>Google Code Search</b>")
    
class GoToPackageLocationAction(ShowUrlAction):
    
    def __init__(self, name, url):
        ShowUrlAction.__init__(self, name, url)    
    
    def get_verb(self):
        return _("Open package <i>%(name)s</i>")

    def is_valid(self):
        if self._url.startswith("ftp://"):
            return True
        else:
            return ShowUrlAction.is_valid(self)

class SearchWithGoogleCodeAction(ShowUrlAction):
    """
    Open the Google Codesearch page with results
    for the given query
    """
    
    BASE_URL = "http://www.google.com/codesearch?%s"
    
    def __init__(self, term):
        url = self.BASE_URL % urllib.urlencode({'q': term})
        ShowUrlAction.__init__(self, term, url)

    def get_verb(self):
        return _("Search <b>Google Code Search</b> for <i>%(name)s</i>")

class GoogleCodeSearchForMatch(deskbar.interfaces.Match):
    """
    Search Google Codesearch for the given query
    """
    
    def __init__(self, term=None, **args):
        deskbar.interfaces.Match.__init__ (self, category="web", icon="google.png", **args)
        self._term = term
        self.add_action( SearchWithGoogleCodeAction(self._term) )
    
    def get_hash(self):
        return "googlecodesearch:"+self._term
    
class GoogleCodeSearchFeedParser(xml.sax.handler.ContentHandler):
    """
    The result is an atom feed with additional elements (gcs namespace)
    @see: http://code.google.com/apis/codesearch/reference.html
    """
    
    ENTRY_ELEMENT = "entry"
    ID_ELEMENT = "id"
    TITLE_ELEMENT = "title"
    CONTENT_ELEMENT = "content"
    FILE_ELEMENT = "gcs:file"
    FILE_NAME_ATTR = "name"
    PACKAGE_ELEMENT = "gcs:package"
    PACKAGE_NAME_ATTR = "name"
    PACKAGE_URI_ATTR = "uri"
    
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        # The elements we want to save the text from
        self._elements = set([self.ID_ELEMENT,
                              self.TITLE_ELEMENT,
                              self.CONTENT_ELEMENT,
                              ])
    
    def _reset_entry(self):
        self.__entry = {}
        self.__not_interested = False
        
        self._reset_contents()
        
    def _reset_contents(self):
        self.__contents = ""
        
    def _add_to_entry(self, key):
        value = self.__contents.strip()
        if len(value) == 0:
            value = None
        self.__entry[key] = value
        self._reset_contents()
    
    def get_results(self):
        return self._results
        
    def startDocument(self):
        self._results = []
        self._reset_entry()
        
    def startElement(self, name, attrs):
        # Check if we're interested in contents
        if name in self._elements:
            self.__not_interested = False
        else:
            self.__not_interested = True
            
        if name == self.FILE_ELEMENT:
            if attrs.has_key(self.FILE_NAME_ATTR):
                self.__entry["filename"] = \
                attrs.getValue(self.FILE_NAME_ATTR)
        elif name == self.PACKAGE_ELEMENT:
            if attrs.has_key(self.PACKAGE_NAME_ATTR):
                self.__entry["package-name"] = \
                attrs.getValue(self.PACKAGE_NAME_ATTR)
            if attrs.has_key(self.PACKAGE_URI_ATTR):
                self.__entry["package-uri"] = \
                attrs.getValue(self.PACKAGE_URI_ATTR)
    
    def endElement(self, name):
        if name == self.ENTRY_ELEMENT:
            self._results.append(self.__entry)
            self.__entry = {}
        elif name == self.ID_ELEMENT:
            self._add_to_entry("id")
        elif name == self.TITLE_ELEMENT:
            self._add_to_entry("title")
        elif name == self.CONTENT_ELEMENT:
            self._add_to_entry("content")
        
        self.__not_interested = False
    
    def characters(self, content):
        if not self.__not_interested:
            self.__contents += content

