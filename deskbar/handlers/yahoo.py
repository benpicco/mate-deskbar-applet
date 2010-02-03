from deskbar.core.GconfStore import GconfStore
from deskbar.core.Utils import strip_html, get_proxy, get_locale_lang
from deskbar.defs import VERSION
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from xml.sax.saxutils import unescape
import deskbar
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gtk
import logging
import re
import urllib
import xml.sax
import xml.sax.handler

LOGGER = logging.getLogger(__name__)

HANDLERS = ["YahooHandler", "YahooSuggestHandler"]

YAHOO_API_KEY = 'deskbar-applet'
MAX_RESULTS = 15
    
GCONF_YAHOO_LANG = GconfStore.GCONF_DIR+"/yahoo/language"

# Languages supported by Yahoo
# see http://developer.yahoo.com/search/languages.html
LANGUAGES = (
    (_("Arabic"), "ar"),
    (_("Bulgarian"), "bg"),
    (_("Catalan"), "ca"),
    (_("Chinese (Simplified)"), "szh"),
    (_("Chinese (Traditional)"), "tzh"),
    (_("Croatian"), "hr"),
    (_("Czech"), "cs"),
    (_("Danish"), "da"),
    (_("Dutch"), "nl"),
    (_("English"), "en"),
    (_("Estonian"), "et"),
    (_("Finnish"), "fi"),
    (_("French"), "fr"),
    (_("German"), "de"),
    (_("Greek"), "el"),
    (_("Hebrew"), "he"),
    (_("Hungarian"), "hu"),
    (_("Icelandic"), "is"),
    (_("Indonesian"), "id"),
    (_("Italian"), "it"),
    (_("Japanese"), "ja"),
    (_("Korean"), "ko"),
    (_("Latvian"), "lv"),
    (_("Lithuanian"), "lt"),
    (_("Norwegian"), "no"),
    (_("Persian"), "fa"),
    (_("Polish"), "pl"),
    (_("Portuguese"), "pt"),
    (_("Romanian"), "ro"),
    (_("Russian"), "ru"),
    (_("Slovak"), "sk"),
    (_("Serbian"), "sr"),
    (_("Slovenian"), "sl"),
    (_("Spanish"), "es"),
    (_("Swedish"), "sv"),
    (_("Thai"), "th"),
    (_("Turkish"), "tr"),
)
    
class OpenYahooAction(ShowUrlAction):
    
    def __init__(self, name, url):
        ShowUrlAction.__init__(self, name, url)

    def get_verb(self):
        return "%(name)s"

class YahooMatch(deskbar.interfaces.Match):
    
    def __init__(self, url=None, summary=None, **args):
        deskbar.interfaces.Match.__init__ (self, category="web", icon="yahoo.png", **args)
        self.url = url
        self.set_snippet(summary)
        
        self.add_action( OpenYahooAction(self.get_name(), self.url) )
        self.add_action( CopyToClipboardAction( _("URL"), self.url) )
    
    def get_hash(self):
        return self.url

class YahooHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("yahoo.png"),
             'name': _("Yahoo! Search"),
             'description': _("Search Yahoo! as you type"),
             'version': VERSION}
    INSTRUCTIONS = _("You can configure in which language the results should be.")
    
    BASE_URL = "http://search.yahooapis.com/WebSearchService/V1/webSearch?%s"
    DEFAULT_LANG = "en"
    SUPPORTED_FORMATS = set(["html",
                             "msword",
                             "pdf",
                             "ppt",
                             "rss",
                             "txt",
                             "xls"])
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self.server = None
        self._lang = None
        self._format_regex = re.compile("format:(\w+)")
        self._gconf = GconfStore.get_instance().get_client()
        self._gconf.notify_add(GCONF_YAHOO_LANG, self._on_language_changed)
        self._set_lang()
        
    def _on_language_changed(self, client, cnxn_id, entry, data):
        if entry.value == None:
            self._set_lang()
        else:
            self._lang = entry.value.get_string()
            
    def _set_lang(self):
        self._lang = self._gconf.get_string(GCONF_YAHOO_LANG)
        if self._lang == None:
            localelang = self._guess_lang()
            self._gconf.set_string(GCONF_YAHOO_LANG, localelang)
    
    def _guess_lang(self):
        """ Try to guess lang """
        localelang = get_locale_lang()
        if localelang == None:
            localelang = self.DEFAULT_LANG
        else:
            # Take care of exceptions
            if localelang == 'zh_CN':
                localelang = 'szh'
            elif localelang == 'zh_TW':
                localelang = 'tzh'
            else:
                localelang = localelang.split("_")[0]
            
            # Check if the language is supported
            for name, code in LANGUAGES:
                if code == localelang:
                    return localelang
            
            # Set fallback
            localelang = self.DEFAULT_LANG
                    
        return localelang
    
    def _get_parameters_from_query(self, qstring):
        """
        See L{YahooHandler.SUPPORTED_FORMATS} for a list of supported parameters
        """
        params = {'appid': YAHOO_API_KEY,
                'results': MAX_RESULTS,
                'language': self._lang}
        match = self._format_regex.search(qstring)
        if match != None:
            format = match.group(1)
            if format in self.SUPPORTED_FORMATS:
                params['format'] = format
                start, end = match.span()
                # Remove format info from query string
                qstring = qstring.replace(qstring[start:end], '').strip()
            
        params['query'] = qstring
        return params

    def query(self, qstring):
        url = self.BASE_URL % urllib.urlencode(
                self._get_parameters_from_query(qstring))
        
        LOGGER.debug("Retrieving %s", url)
        
        matches = []
        
        try:
            stream = urllib.urlopen(url, proxies=get_proxy())
        except (IOError, EOFError), msg:
            LOGGER.error("Could not open URL %s: %s, %s", url, msg[0], msg[1])
            return
    
        try:
            try:
                handler = WebSearchResultsParser()
                xml.sax.parse(stream, handler)
            except xml.sax.SAXParseException, e:
                LOGGER.exception(e)
                handler = None
        finally:
            stream.close()
    
        if handler == None:
            return
        
        LOGGER.debug('Got yahoo answer for: %s', qstring)
         
        num_results = len(handler.get_results())
        for i, result in enumerate(handler.get_results()):
            result_prio = self.get_priority() + num_results - i
            result_title = strip_html(result["title"])
            result_summary = result["summary"]
            if result_summary != None:
                result_summary = strip_html(result_summary)
            matches.append(YahooMatch(name=result_title, url=result["clickurl"],
                                      summary=result_summary,
                                      priority=result_prio))
            
        matches.append(YahooSearchForMatch(qstring, priority=self.get_priority()))
            
        LOGGER.debug("Returning yahoo answer for: %s", qstring)
        self._emit_query_ready(qstring, matches)
        
    def has_config(self):
        return True
    
    def show_config(self, parent):
        dialog = YahooSearchConfigDialog(parent)
        dialog.run()
        dialog.destroy()
        
class WebSearchResultsParser (xml.sax.handler.ContentHandler):
    """
    @see: http://developer.yahoo.com/search/web/V1/webSearch.html
    """
    
    RESULT_ELEMENT = "Result"
    TITLE_ELMENT = "Title"
    SUMMARY_ELEMENT = "Summary"
    CLICK_URL_ELEMENT = "ClickUrl"
    MIME_TYPE_ELEMENT = "MimeType"
     
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        # Elements we want to store the contents of
        self._elements = set([self.TITLE_ELMENT,
                              self.SUMMARY_ELEMENT,
                              self.CLICK_URL_ELEMENT,
                              self.MIME_TYPE_ELEMENT])
        
    def get_results(self):
        """
        @returns: a dict with keys C{title}, C{summary}, C{clickurl} and C{mimetype}
        """
        return self._results
        
    def startDocument(self):
        self._results = []
        self._reset_result()
        
    def _reset_result(self):
        self.__not_interested = False
        self.__result = {}
        self._reset_contents()
        
    def _reset_contents(self):
        self.__contents = ""
        
    def _add_to_result(self, key):
        value = self.__contents.strip()
        if len(value) == 0:
            self.value = None
        self.__result[key] = unescape(value)
        self._reset_contents()
        
    def startElement(self, name, attrs):
        if name in self._elements:
            self.__not_interested = False
        else:
            self.__not_interested = True
            
    def endElement(self, name):
        if name == self.RESULT_ELEMENT:
            self._results.append(self.__result)
            self._reset_result()
        elif name == self.TITLE_ELMENT:
            self._add_to_result("title")
        elif name == self.SUMMARY_ELEMENT:
            self._add_to_result("summary")
        elif name == self.CLICK_URL_ELEMENT:
            self._add_to_result("clickurl")
        elif name == self.MIME_TYPE_ELEMENT:
            self._add_to_result("mimetype")
        
        self.__mime_type_started = False
            
    def characters(self, content):
        # Only save content for the elements we're interested in
        if not self.__not_interested:
            self.__contents += content

class SearchWithYahooAction(ShowUrlAction):
    """
    Open the Yahoo! search page with results
    for the given query
    """
    
    BASE_URL = "http://search.yahoo.com/search?%s"
    
    def __init__(self, term):
        url = self.BASE_URL % urllib.urlencode({'p': term})
        ShowUrlAction.__init__(self, term, url)

    def get_verb(self):
        return _("Search <b>Yahoo!</b> for <i>%(name)s</i>")

class YahooSearchForMatch(deskbar.interfaces.Match):
    """
    Search Yahoo! for the given query
    """
    
    def __init__(self, term=None, **args):
        deskbar.interfaces.Match.__init__ (self, category="web", icon="yahoo.png", **args)
        self._term = term
        self.add_action( SearchWithYahooAction(self._term) )
    
    def get_hash(self):
        return "yahoo:"+self._term
       
class YahooSuggestHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("yahoo.png"),
             'name': _("Yahoo! Suggestions"),
             'description': _("Provides suggestions for queries related to the submitted query"),
             'version': VERSION}
    
    BASE_URL = "http://search.yahooapis.com/WebSearchService/V1/relatedSuggestion?%s"
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        
    def query(self, qstring):
        url = self.BASE_URL % urllib.urlencode(
                {'appid': YAHOO_API_KEY,
                 'results': MAX_RESULTS,
                 'query': qstring})
        
        LOGGER.debug("Retrieving %s", url)
    
        matches = []
        
        try:
            stream = urllib.urlopen(url, proxies=get_proxy())
        except (IOError, EOFError), msg:
            LOGGER.error("Could not open URL %s: %s, %s", url, msg[0], msg[1])
            return
        
        try:
            try:
                handler = RelatedSuggestionResultsParser()
                xml.sax.parse(stream, handler)
            except xml.sax.SAXParseException, e:
                LOGGER.exception(e)
                handler = None
        finally:
            stream.close()
            
        if handler == None:
            return
            
        num_results = len(handler.get_suggestions())
        for i, suggestion in enumerate(handler.get_suggestions()):
            prio = self.get_priority() + num_results - i
            matches.append( YahooSearchForMatch(term=suggestion, priority=prio) )
            
        self._emit_query_ready(qstring, matches)
        
class RelatedSuggestionResultsParser (xml.sax.handler.ContentHandler):
    """
    @see: http://developer.yahoo.com/search/web/V1/relatedSuggestion.html
    """
    
    RESULT_ELEMENT = "Result"
    
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        
    def get_suggestions(self):
        return self._suggestions
        
    def startDocument(self):
        self._suggestions = []
        self._reset_result()
        
    def _reset_result(self):
        self.__result_started = False
        self.__result = ""
        
    def startElement(self, name, attrs):
        if name == self.RESULT_ELEMENT:
            self.__result_started = True
            
    def endElement(self, name):
        if name == self.RESULT_ELEMENT:
            self._suggestions.append(self.__result)
            self._reset_result()
            
    def characters(self, content):
        if self.__result_started:
            self.__result += content
            
class YahooSearchConfigDialog(gtk.Dialog):
    
    
    def __init__(self, parent):
        gtk.Dialog.__init__(self, title=_("Configure Yahoo!"),
                            parent=parent,
                            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK))
        
        self.vbox2 = gtk.VBox(spacing=6)
        self.vbox2.show()
        self.vbox.pack_start(self.vbox2)
        
        self.label = gtk.Label()
        self.label.set_markup(_("<b>Choose the language the results should be in:</b>"))
        self.label.show()
        self.vbox2.pack_start(self.label, False)
        
        self.liststore = gtk.ListStore(str, str)
        for lang in LANGUAGES:
            self.liststore.append( lang )
                
        self.combobox = gtk.ComboBox(self.liststore)
        self.combobox.connect("changed", self._on_combobox_changed)
        cell = gtk.CellRendererText()
        self.combobox.pack_start(cell)
        self.combobox.add_attribute(cell, 'text', 0)
        self.combobox.show()
        self.vbox2.pack_start(self.combobox, False, False, 0)
        
        lang = GconfStore.get_instance().get_client().get_string(GCONF_YAHOO_LANG)
        if lang != None:
            self._select_lang(lang)
        
    def _select_lang(self, lang):
        iter = self.liststore.get_iter_first()
        lang_iter = None
        while iter != None:
            if self.liststore[iter][1] == lang:
                lang_iter = iter
                break
            iter = self.liststore.iter_next(iter)
                
        if lang_iter != None:
            self.combobox.set_active_iter(lang_iter)
        
    def _on_combobox_changed(self, combobox):
        lang = combobox.get_model()[combobox.get_active_iter()][1]
        GconfStore.get_instance().get_client().set_string(GCONF_YAHOO_LANG, lang)
