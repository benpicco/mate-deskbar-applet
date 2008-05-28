from deskbar.core.GconfStore import GconfStore
from deskbar.core.Utils import load_icon
from deskbar.defs import VERSION
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gtk
import locale
import logging
import urllib

LOGGER = logging.getLogger(__name__)
    
HANDLERS = ["WikipediaSuggestHandler"]
    
WIKIPEDIA_SUGGEST_URL = "http://www.wikipedia.de/suggest.php"
WIKIPEDIA_ARTICLE_URL = "http://www.wikipedia.de/go"
GCONF_KEY = GconfStore.GCONF_DIR + "/wikipedia-suggest/lang"

# From http://meta.wikimedia.org/wiki/List_of_Wikipedias
LANGUAGES = (
(_("English"), "en"),
(_("German"), "de"),
(_("French"), "fr"),
(_("Polish"), "pl"),
(_("Japanese"), "jp"),
(_("Italian"), "it"),
(_("Dutch"), "nl"),
(_("Portuguese"), "pt"),
(_("Spanish"), "es"),
(_("Russian"), "ru"),
(_("Swedish"), "sv"),
(_("Chinese"), "zh"),
(_("Norwegian"), "no"),
(_("Finnish"), "fi"),
(_("Catalan"), "ca"),
(_("Ukrainian"), "uk"),
(_("Romanian"), "ro"),
(_("Turkish"), "tr"),
)

class WikipediaSuggestAction(ShowUrlAction):
    def __init__(self, title, lang):
        ShowUrlAction.__init__(self, title,
                               WIKIPEDIA_ARTICLE_URL + '?' + urllib.urlencode({'l': lang, 'q': title}))
        
    def get_verb(self):
        return _("Open article <i>%(name)s</i> in <b>Wikipedia</b>")

class WikipediaSuggestMatch(deskbar.interfaces.Match):
    def __init__(self, title, lang, **args):
        deskbar.interfaces.Match.__init__ (self, name=title, category="web", icon="wikipedia.png", **args)
        self._title = title
        self._lang = lang
        self.add_action( WikipediaSuggestAction(title, lang) ) 
        
    def get_hash(self, text=None):
        return self._title + self._lang
        
class WikipediaSuggestHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': load_icon("wikipedia.png"),
             'name': _("Wikipedia Suggest"),
             'description': _("As you type, Wikipedia will offer suggestions."),
             'version': VERSION}
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)
        self._gconf = GconfStore.get_instance().get_client()
        self._gconf.notify_add(GCONF_KEY, lambda x, y, z, a: self.set_lang(z.value.get_string()))
        self._lang = self._gconf.get_string(GCONF_KEY)
        # Try to guess language from current locale
        if self._lang == None:
            lang = "en"
            # we get (de_DE, UTF-8) and want only de
            localelang = locale.getlocale()[0]
            if localelang != None:
                localelang = localelang.split("_")[0]
            for l in LANGUAGES:
                if l[1] == localelang:
                    lang = localelang
                    break
            self._gconf.set_string(GCONF_KEY, lang)
        
    def set_lang(self, lang):
        self._lang = lang
        
    def query(self, qstring):        
        args = {'lang': self._lang, 'search': qstring}
        url = WIKIPEDIA_SUGGEST_URL + '?' + urllib.urlencode(args)
        
        try:
            result = urllib.urlopen(url)
        except IOError, msg:
            # Print error for debugging purposes and end querying
            LOGGER.error("Could not open URL %s: %s, %s" % (url, msg[0], msg[1]))
            return

        matches = []
        for line in result:
            title, lang = line.strip().split("\t")
            matches.append( WikipediaSuggestMatch(title, lang) )
        self._emit_query_ready( qstring, matches )
        
    def has_config(self):
        return True
        
    def show_config(self, parent):
        dialog = ConfigDialog (parent)
        if dialog.run() == gtk.RESPONSE_ACCEPT:
            self._gconf.set_string(GCONF_KEY, dialog.get_lang())
        dialog.destroy()
        
class ConfigDialog (gtk.Dialog):
    
    def __init__(self, parent):
        dialog = gtk.Dialog.__init__(self, _("Wikipedia Suggest settings"), parent,
                        gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        vbox = gtk.VBox(spacing=6)
        self.vbox.pack_start(vbox)
        
        label = gtk.Label( _("Choose the language you want to use or enter the code of your language manually"))
        label.set_line_wrap(True)
        vbox.pack_start(label)
        
        hbox = gtk.HBox(spacing=6)
        vbox.pack_start(hbox)
        
        langstore = gtk.ListStore (str, str)
        for l in LANGUAGES:
            langstore.append(l)
        combobox = gtk.ComboBox(langstore)
        combobox.connect("changed", self._on_combobox_changed)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell)
        combobox.add_attribute(cell, 'text', 0)
        combobox.show()
        hbox.pack_start(combobox)
        
        self.entry = gtk.Entry()
        self.entry.set_width_chars(2)
        hbox.pack_start(self.entry, False, False, 0)
        vbox.show_all()
        
        self._gconf = GconfStore.get_instance().get_client()
        self._gconf.notify_add(GCONF_KEY, lambda x, y, z, a: self.set_lang(z.value.get_string()))
        self.set_lang (self._gconf.get_string(GCONF_KEY))
        
    def set_lang(self, lang):
        self.entry.set_text (lang)
        
    def get_lang(self):
        return self.entry.get_text()
        
    def _on_combobox_changed(self, combobox):
        lang = combobox.get_model()[combobox.get_active_iter()][1]
        self.entry.set_text (lang)
        