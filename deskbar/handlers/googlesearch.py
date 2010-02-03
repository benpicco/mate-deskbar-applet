from deskbar.core.GconfStore import GconfStore
from deskbar.core.Utils import strip_html, get_proxy, get_locale_lang, htmldecode
from deskbar.defs import VERSION
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
import deskbar
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import logging
import urllib
import gtk

try:
    import json
except:
    try:
        import simplejson as json
    except:
        pass
    
LOGGER = logging.getLogger(__name__)
    
HANDLERS = ["GoogleHandler"]
GCONF_GOOGLE_LANG = GconfStore.GCONF_DIR+"/google/language"

# Languages supported by Google
# see: http://www.google.com/coop/docs/cse/resultsxml.html#languageCollections
LANGUAGES = (
    (_("Arabic"), "lang_ar"),
    (_("Bulgarian"), "lang_bg"),
    (_("Catalan"), "lang_ca"),
    (_("Chinese (Simplified)"), "lang_zh-CN"),
    (_("Chinese (Traditional)"), "lang_zh-TW"),
    (_("Croatian"), "lang_hr"),
    (_("Czech"), "lang_cs"),
    (_("Danish"), "lang_da"),
    (_("Dutch"), "lang_nl"),
    (_("English"), "lang_en"),
    (_("Estonian"), "lang_et"),
    (_("Finnish"), "lang_fi"),
    (_("French"), "lang_fr"),
    (_("German"), "lang_de"),
    (_("Greek"), "lang_el"),
    (_("Hebrew"), "lang_iw"),
    (_("Hungarian"), "lang_hu"),
    (_("Icelandic"), "lang_is"),
    (_("Indonesian"), "lang_id"),
    (_("Italian"), "lang_it"),
    (_("Japanese"), "lang_ja"),
    (_("Korean"), "lang_ko"),
    (_("Latvian"), "lang_lv"),
    (_("Lithuanian"), "lang_lt"),
    (_("Norwegian"), "lang_no"),
    (_("Polish"), "lang_pl"),
    (_("Portuguese"), "lang_pt"),
    (_("Romanian"), "lang_ro"),
    (_("Russian"), "lang_ru"),
    (_("Serbian"), "lang_sr"),
    (_("Slovak"), "lang_sk"),
    (_("Slovenian"), "lang_sl"),
    (_("Spanish"), "lang_es"),
    (_("Swedish"), "lang_sv"),
    (_("Turkish"), "lang_tr")
)


class GoogleHandler(deskbar.interfaces.Module):
    """
    
       Class that handle searchs through google.
       
       @see: http://code.google.com/apis/ajaxsearch/documentation/reference.html
           
    """
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("google.png"),
             'name': _("Google Search"),
             'description': _("Search terms through Google Search engine."),
             'version': VERSION}
    
    INSTRUCTIONS = _("You can configure in which language the results should be.")         
    
    BASE_URL = "http://ajax.googleapis.com/ajax/services/search/web?%s"
    DEFAULT_LANG = "lang_en"
    PROTOCOL_VERSION = "1.0"
    RESULT_SIZE = "large"
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self.server = None
        self._lang = None
        self._gconf = GconfStore.get_instance().get_client()
        self._gconf.notify_add(GCONF_GOOGLE_LANG, self._on_language_changed)
        self._set_lang()
    
    def _on_language_changed(self, client, cnxn_id, entry, data):
        if entry.value == None:
            self._set_lang()
        else:
            self._lang = entry.value.get_string()
            
    def _set_lang(self):
        self._lang = self._gconf.get_string(GCONF_GOOGLE_LANG)
        if self._lang == None:
            localelang = self._guess_lang()
            self._gconf.set_string(GCONF_GOOGLE_LANG, localelang)
    
    def _guess_lang(self):
        """ 
        
            Try to guess lang based on the system default language 
       
        """
        
        localelang = get_locale_lang()
        if localelang == None:
            localelang = self.DEFAULT_LANG
        else:
            # Take care of exceptions
            if localelang == 'zh_CN':
                localelang = 'lang_zh-CN'
            elif localelang == 'zh_TW':
                localelang = 'lang_zh-TW'
            else:
                localelang = 'lang_' + localelang.split("_")[0]
            
            # Check if the language is supported
            for name, code in LANGUAGES:
                if code == localelang:
                    return localelang
            
            # Set fallback
            localelang = self.DEFAULT_LANG
       
        return localelang
    
    def query(self, qstring):        
        params = {'v': self.PROTOCOL_VERSION, 
                'rsz': self.RESULT_SIZE, 
                'lr': self._lang,
                'q': qstring}
        
        url = self.BASE_URL % urllib.urlencode(params)
        
        LOGGER.debug("Retrieving %s", url)
        
        matches = []
        results = []
        
        try:
            stream = urllib.urlopen(url, proxies=get_proxy())
        except (IOError, EOFError), msg:
            LOGGER.error("Could not open URL %s: %s, %s", url, msg[0], msg[1])
            return
            
        LOGGER.debug('Got Google answer for: %s', qstring)

        jsondata = json.loads(stream.read())
        results = jsondata['responseData']['results']
        stream.close()
        
        LOGGER.debug("Returning Google answer for: %s", qstring)
        
        if not 'Error' in results:
            num_results = len(results)
            for i, result in enumerate(results):
                print result
                prio = self.get_priority() + num_results - i
                matches.append(GoogleMatch(result, priority=prio))
            
        matches.append(GoogleSearchForMatch(qstring, priority=self.get_priority()))    
        self._emit_query_ready(qstring, matches)

    def has_config(self):
        return True
    
    def show_config(self, parent):
        dialog = GoogleConfigDialog(parent)
        dialog.run()
        dialog.destroy()
        
    @staticmethod
    def has_requirements():
        """
        Check that required libraries are available for this module to work
        """

        try:
            import json
        except:
            try:
                import simplejson as json
            except:
                 GoogleHandler.INSTRUCTIONS = _("Python module json or simplejson are not available")
                 return False
        return True


class OpenGoogleAction(ShowUrlAction):
    
    def __init__(self, name, url):
        ShowUrlAction.__init__(self, name, url)

    def get_verb(self):
        return "%(name)s"

class GoogleMatch(deskbar.interfaces.Match):
    def __init__(self, result=None, **args):
        deskbar.interfaces.Match.__init__(self, category="web", icon="google.png", **args)
        self._name = htmldecode(result['titleNoFormatting'])
        self.url = result['url']
        self.set_snippet(htmldecode(result['content']))
        
        self.add_action( OpenGoogleAction(self.get_name(), self.url) )
        self.add_action( CopyToClipboardAction( _("URL"), self.url) )
        
    def get_hash(self):
        return self.url
        

class SearchWithGoogleAction(ShowUrlAction):
    """
    Open the Google search page with results
    for the given query
    """
    
    BASE_URL = "http://www.google.com/search?%s"
    
    def __init__(self, term):
        url = self.BASE_URL % urllib.urlencode({'q': term})
        ShowUrlAction.__init__(self, term, url)

    def get_verb(self):
        return _("Search <b>Google</b> for <i>%(name)s</i>")

class GoogleSearchForMatch(deskbar.interfaces.Match):
    """
    Search Google for the given query
    """
    
    def __init__(self, term=None, **args):
        deskbar.interfaces.Match.__init__ (self, category="web", icon="google.png", **args)
        self._term = term
        self.add_action( SearchWithGoogleAction(self._term) )
    
    def get_hash(self):
        return "google:"+self._term

class GoogleConfigDialog(gtk.Dialog):
    """
    
        Create the language configuration dialog for Google Search handler.
    
    """
    
    def __init__(self, parent):
        gtk.Dialog.__init__(self, title=_("Configure Google"),
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
        
        lang = GconfStore.get_instance().get_client().get_string(GCONF_GOOGLE_LANG)
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
        GconfStore.get_instance().get_client().set_string(GCONF_GOOGLE_LANG, lang)


