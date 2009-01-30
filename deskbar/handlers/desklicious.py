from deskbar.core.GconfStore import GconfStore
from deskbar.defs import VERSION
from deskbar.handlers.actions.ShowUrlAction import ShowUrlAction
from gettext import gettext as _
from xml.dom import DOMException
from xml.parsers.expat import ExpatError
import deskbar
import deskbar.core.Utils
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import gconf
import gtk
import logging
import re
import urllib
import xml.dom.minidom

LOGGER = logging.getLogger(__name__)

GCONF_DELICIOUS_USER  = GconfStore.GCONF_DIR+"/desklicious/user"

DEFAULT_QUERY_TAG = 'http://feeds.delicious.com/rss/%s/%s'

HANDLERS = ["DeliciousHandler"]

class DeliciousAction(ShowUrlAction):
    
    def __init__(self, name, url, tags=None):
        """
        @param tags: Is ignored since 2.23.1,
        just there for backwards compatibility 
        """
        ShowUrlAction.__init__(self, name, url)
        
    def get_verb(self):
        return "<b>%(name)s</b>"
        
class DeliciousMatch(deskbar.interfaces.Match):
    def __init__(self, url=None, tags=None, author=None, **args):
        deskbar.interfaces.Match.__init__ (self, icon="delicious.png", **args)
        self.url = url
        self.author = author
        self.set_snippet(' '.join(tags))
        self.add_action( DeliciousAction(self.get_name(), self.url) )

    def get_hash(self):
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
        self._bad_chars_pattern = re.compile("\s")

    def query(self, tag):
        # Remove bad characters from query
        tag = self._bad_chars_pattern.sub(' ', tag)
        
        #The queryyyyYyyYy :)
        LOGGER.info( "Asking del.icio.us tags for %s", tag )
        posts = self._delicious.get_posts_by_tag(tag)

        LOGGER.info('Returning del.icio.us result')
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
        
        posts = []
        #Get the info from del.icio.us and parse
        url = DEFAULT_QUERY_TAG % (urllib.quote_plus(self._user), urllib.quote_plus(tag))
        
        LOGGER.debug("Opening URL %s", url)
        stream = None
        try:
            stream = urllib.urlopen(url, proxies=deskbar.core.Utils.get_proxy())
        except (IOError, EOFError), msg:
            LOGGER.error("Could not open URL %s: %s, %s", url, msg[0], msg[1])
            return []
                
        try:
            dom = xml.dom.minidom.parse(stream)
        except ExpatError, e:
            LOGGER.exception(e)
            return []
        
        if stream != None:
            stream.close()
        
        #And return the results
        try:
            try:
                for item in dom.getElementsByTagName("item"):
                    title_nodes = item.getElementsByTagName("title")
                    url_nodes = item.getElementsByTagName("link")
                    
                    # Check if we have expected content at all
                    if len(title_nodes) == 0 or len(url_nodes) == 0:
                        return []
                    
                    item_title = title_nodes[0].firstChild.nodeValue
                    item_url = url_nodes[0].firstChild.nodeValue
                    
                    # by default we have no tags
                    tags = []
                    subject_nodes = item.getElementsByTagName("dc:subject")
                    if len(subject_nodes) > 0:
                        subject_node = subject_nodes[0]
                        # There might be no tags
                        if (subject_node.hasChildNodes()):
                            tags = subject_node.firstChild.nodeValue.split(" ")
                    
                    creator_nodes = item.getElementsByTagName("dc:creator")
                    if len(creator_nodes) > 0: 
                        creator_node = creator_nodes[0]
                        creator = creator_node.firstChild.nodeValue
                    else:
                        creator = self._user
                    
                    posts.append(
                        DeliciousMatch(
                            name=item_title,
                            url=item_url,
                            tags=tags,
                            author=creator,
                            category="web"))
            except DOMException, e:
                LOGGER.exception(e)
        finally:
            # Cleanup
            dom.unlink()
        
        return posts

