from deskbar.defs import VERSION
from deskbar.handlers.actions.OpenWithApplicationAction import OpenWithApplicationAction
from deskbar.handlers.actions.SendEmailToAction import SendEmailToAction
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from gettext import gettext as _
import deskbar
import deskbar.core.Indexer
import deskbar.core.Utils
import deskbar.handlers.evolution
import deskbar.interfaces.Match
import deskbar.interfaces.Module

HANDLERS = ["EvolutionHandler"]

class EditEvolutionContactAction(OpenWithApplicationAction):
    
    def __init__(self, name, email, uri):
        OpenWithApplicationAction.__init__(self, name, "evolution", [uri])
        self._email = email
        self._uri = uri
    
    def get_icon(self):
        return "stock_edit"
    
    def get_name(self, text=None):
        return {
            "name": self._name,
            "email": self._email,
        }
    
    def get_verb(self):
        #translators: First %s is the contact full name, second %s is the email address
        return _("Edit contact <b>%(name)s</b> (%(email)s)")

class EvolutionMatch(deskbar.interfaces.Match):
    def __init__(self, name, email, uri, pixbuf=None, **args):
        deskbar.interfaces.Match.__init__(self, name=name, pixbuf=pixbuf, category="people")
        
        self.add_action( SendEmailToAction(name, email), True )
        self.add_action( EditEvolutionContactAction(name, email, uri) )
        self.add_action( CopyToClipboardAction(name, email) )
    
    def get_hash(self):
        return self.get_name()
        
class EvolutionHandler(deskbar.interfaces.Module):
    
    INFOS = {'icon':  deskbar.core.Utils.load_icon("stock_addressbook"),
             "name": _("Mail (Address Book)"),
             "description": _("Send mail to your contacts by typing their name or e-mail address"),
             "version": VERSION,
             }
    
    def __init__(self):
        deskbar.interfaces.Module.__init__(self)    
    
    def initialize(self):
        deskbar.handlers.evolution.set_pixbuf_size(deskbar.ICON_HEIGHT)
        
    def query(self, query):
        hits = deskbar.handlers.evolution.search_sync(query, deskbar.DEFAULT_RESULTS_PER_HANDLER)
        matches = []
        for name, email, pixbuf, uri in hits:
            if name == None or email == None:
                continue            
            matches.append(EvolutionMatch(name, email, uri, pixbuf, priority=self.get_priority()))
        self._emit_query_ready(query, matches )
        
    @staticmethod
    def has_requirements():
        if deskbar.handlers.evolution.num_address_books_with_completion() > 0:
            return True
        else:
            EvolutionHandler.INSTRUCTIONS = _("Autocompletion Needs to be Enabled\nWe cannot provide e-mail addresses from your address book unless autocompletion is enabled.  To do this, from your mail program's menu, choose Edit → Preferences, and then Autocompletion.")
            return False
