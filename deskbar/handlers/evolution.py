from gettext import gettext as _
import cgi
import gnomevfs
import deskbar, deskbar.Indexer, deskbar.Handler, deskbar.evolution, deskbar.Utils, deskbar.Match
from deskbar.defs import VERSION

def _check_requirements():
	if deskbar.evolution.num_address_books_with_completion() > 0:
		return (deskbar.Handler.HANDLER_IS_HAPPY, None, None)
	else:
		return (deskbar.Handler.HANDLER_HAS_REQUIREMENTS,
		_("You need to enable autocomplete in your mail preferences"),
		lambda dialog: deskbar.Utils.more_information_dialog(
			dialog,
			_("Autocompletion Needs to be Enabled"),
			_("We cannot provide e-mail addresses from your address book unless autocompletion is enabled.  To do this, from your mail program's menu, choose Edit - Preferences, and then Autocompletion.")
			))

HANDLERS = {
	"EvolutionHandler" : {
		"name": _("Mail (Address Book)"),
		"description": _("Send mail to your contacts by typing their name or e-mail address"),
		"requirements" : _check_requirements,
		"version": VERSION,
	}
}

class EvolutionMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, email=None, pixbuf=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, email=email, **args)
		self._icon = pixbuf
		self.email = email
		
	def action(self, text=None):
		gnomevfs.url_show("mailto:"+self.email)
		
	def get_category(self):
		return "people"
	
	def get_name(self, text=None):
		return {
			"name": cgi.escape(self.name),
			"email": self.email,
		}
		
	def get_verb(self):
		#translators: First %s is the contact full name, second %s is the email address
		return _("Send Email to <b>%(name)s</b> (%(email)s)")
	
	def get_hash(self, text=None):
		return self.email
		
class EvolutionHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "stock_addressbook")	
	
	def initialize(self):
		deskbar.evolution.set_pixbuf_size(deskbar.ICON_HEIGHT)
		
	def query(self, query):
		hits = deskbar.evolution.search_sync(query, deskbar.DEFAULT_RESULTS_PER_HANDLER)
		matches = []
		for name, email, pixbuf in hits:
			if name == None or email == None:
				continue
			
			matches.append(EvolutionMatch(self, name, email, pixbuf))
		return matches
