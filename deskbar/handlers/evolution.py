from gettext import gettext as _
import deskbar, deskbar.core.Indexer, deskbar.interfaces.Module, deskbar.handlers.evolution, deskbar.core.Utils, deskbar.interfaces.Match
from deskbar.defs import VERSION
from deskbar.handlers.actions.SendEmailToAction import SendEmailToAction

HANDLERS = ["EvolutionHandler"]

class EvolutionMatch(deskbar.interfaces.Match):
    def __init__(self, name=None, email=None, pixbuf=None, **args):
        deskbar.interfaces.Match.__init__(self, name=name, email=email, **args)
        self._icon = pixbuf
        self.email = email
        self.add_action( SendEmailToAction(name, email) )
    
    def get_hash(self, text=None):
        return self.email
        
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
        for name, email, pixbuf in hits:
            if name == None or email == None:
                continue
            
            matches.append(EvolutionMatch(name, email, pixbuf, category="people", priority=self.get_priority()))
        self._emit_query_ready(query, matches )
        
    @staticmethod
    def has_requirements():
        if deskbar.handlers.evolution.num_address_books_with_completion() > 0:
            return True
        else:
            EvolutionHandler.INSTRUCTIONS = _("Autocompletion Needs to be Enabled\nWe cannot provide e-mail addresses from your address book unless autocompletion is enabled.  To do this, from your mail program's menu, choose Edit - Preferences, and then Autocompletion.")
            return False
