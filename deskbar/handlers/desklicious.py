from deskbar.core.GconfStore import GconfStore
from deskbar.defs import VERSION
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
import deskbar, deskbar.interfaces.Match, deskbar.interfaces.Module, deskbar.core.Utils
import gconf
import gtk
import logging
import xml.dom.minidom, urllib

GCONF_DELICIOUS_USER  = GconfStore.GCONF_DIR+"/desklicious/user"

DEFAULT_QUERY_TAG = 'http://del.icio.us/rss/%s/%s'
QUERY_DELAY = 1
HANDLERS = ["DeliciousHandler"]

class DeliciousAction(ShowUrlAction):
    
    def __init__(self, name, url, tags):
        ShowUrlAction.__init__(self, name, url)
        self.tags = tags
        
    def get_verb(self):
        return "<b>%(name)s</b>\n<span size='small' foreground='grey'>%(tags)s</span>"
    
    def get_name(self, text=None):
        return {
            "name": self._name,
            "tags": ' '.join(self.tags),
        }
        
class DeliciousMatch(deskbar.interfaces.Match):
    def __init__(self, url=None, tags=None, author=None, **args):
        deskbar.interfaces.Match.__init__ (self, icon="delicious.png", **args)
        self.url = url
        self.author = author
        self.add_action( DeliciousAction(self.get_name(), self.url, tags) )

    def get_hash(self, text=None):
        return self.url
        
class DeliciousHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon': deskbar.core.Utils.load_icon("delicious.png"),
             "name": _("del.icio.us Bookmarks"),
             "description": _("Search your del.icio.us bookmarks by tag name"),
             "version": VERSION,
             }
    
    def __init__(self):
        deskbar.interfaces.Module.__init__ (self)
        self._delicious = DeliciousTagQueryEngine(self)

    def query(self, tag):
        #Hey man, calm down and query once a time :P
        # TODO: Missing
        #self.check_query_changed (timeout=QUERY_DELAY)
        
        # Yes, the google and yahoo search might take a long time
        # and of course deliciuos too !!! ... better check if we're still valid    
        # TODO: Missing
        #self.check_query_changed ()
        
        #The queryyyyYyyYy :)
        logging.info( "Asking del.icio.us tags for %s" % tag )
        posts = self._delicious.get_posts_by_tag(tag)

        # TODO: Missing
        #self.check_query_changed (timeout=QUERY_DELAY)
        logging.info('Returning del.icio.us result')
        self.set_priority_for_matches( posts )
        self._emit_query_ready(tag, posts )
        
    def has_config(self):
        return True
        
    def show_config(self, parent):
        dialog = gtk.Dialog(_("del.icio.us Account"), parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    
        table = gtk.Table(rows=2, columns=2)
        
        table.attach(gtk.Label(_("Enter your del.icio.us username below")), 0, 2, 0, 1)
    
        user_entry = gtk.Entry()
        t = GconfStore.get_instance().get_client().get_string(GCONF_DELICIOUS_USER)
        if t != None:
            user_entry.set_text(t)
        table.attach(gtk.Label(_("Username: ")), 0, 1, 1, 2)
        table.attach(user_entry, 1, 2, 1, 2)
        
        table.show_all()
        dialog.vbox.add(table)
        
        response = dialog.run()
        dialog.destroy()
        
        if response == gtk.RESPONSE_ACCEPT and user_entry.get_text() != "":
            GconfStore.get_instance().get_client().set_string(GCONF_DELICIOUS_USER, user_entry.get_text())

    @staticmethod
    def has_requirements():
        #We need user and password
        if not GconfStore.get_instance().get_client().get_string(GCONF_DELICIOUS_USER):
            DeliciousHandler.INSTRUCTIONS = _("You need to configure your del.icio.us account.")
            # TODO
            #_on_config_account()
            return True
        else:
            DeliciousHandler.INSTRUCTIONS = _("You can modify your del.icio.us account.")
            # TODO
            #_on_config_account()
            return True

class DeliciousTagQueryEngine:    
    def __init__(self, handler):
        """We need use the globals DELICIOUS_USER and DELICIOUS_PASS"""
        self.handler = handler
        
        self._user = GconfStore.get_instance().get_client().get_string(GCONF_DELICIOUS_USER)
            
        GconfStore.get_instance().get_client().notify_add(GCONF_DELICIOUS_USER, lambda x, y, z, a: self.on_username_change(z.value))
        
    def on_username_change(self, value):
        if value != None and value.type == gconf.VALUE_STRING:
            self._user = value.get_string()
            
    def get_posts_by_tag(self, tag):
        if self._user == None:
            return []
        
        #Get the info from del.icio.us and parse
        url = DEFAULT_QUERY_TAG % (urllib.quote_plus(self._user), urllib.quote_plus(tag))
        try:
            stream = urllib.urlopen(url, proxies=deskbar.core.Utils.get_proxy())
        except IOError, msg:
            logging.error("Could not open URL %s: %s, %s" % (url, msg[0], msg[1]))
            return []
        
        dom = xml.dom.minidom.parse(stream)
        stream.close()
        
        #And return the results
        posts=[]
        for item in dom.getElementsByTagName("item"):
            posts.append(
                DeliciousMatch(
                    name=item.getElementsByTagName("title")[0].firstChild.nodeValue,
                    url=item.getElementsByTagName("link")[0].firstChild.nodeValue,
                    tags=item.getElementsByTagName("dc:subject")[0].firstChild.nodeValue.split(" "),
                    author=item.getElementsByTagName("dc:creator")[0].firstChild.nodeValue,
                    category="web"))
        
        return posts

