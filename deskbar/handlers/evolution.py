from gettext import gettext as _
import cgi
import gnomevfs
import deskbar, deskbar.indexer, deskbar.handler, deskbar.evolution, deskbar.handler_utils

def _check_requirements():
	if deskbar.evolution.num_address_books_with_completion() > 0:
		return (deskbar.handler.HANDLER_IS_HAPPY, None, None)
	else:
		return (deskbar.handler.HANDLER_HAS_REQUIREMENTS,
		_("You need to enable autocomplete in your mail preferences"),
		lambda: deskbar.handler_utils.more_information_dialog(
			_("Autocompletion Needs to be Enabled"),
			_("We cannot provide e-mail addresses from your address book unless autocompletion is enabled.  To do this, from your mail program's menu, choose Edit - Preferences, and then Autocompletion.")
			))

HANDLERS = {
	"EvolutionHandler" : {
		"name": _("Mail (Address Book)"),
		"description": _("Send mail to your contacts by typing their name or e-mail address"),
		"requirements" : _check_requirements
	}
}

class EvolutionMatch(deskbar.handler.Match):
	def __init__(self, backend, name, email, icon):
		deskbar.handler.Match.__init__(self, backend, name, icon)
		self._email = email
		
	def action(self, text=None):
		gnomevfs.url_show("mailto:"+self._email)
	
	def get_name(self, text=None):
		return {
			"name": cgi.escape(self._name),
			"email": self._email,
		}
		
	def get_verb(self):
		#translators: First %s is the contact full name, second %s is the email address
		return _("Send Email to <b>%(name)s</b> (%(email)s)")
	
	def get_hash(self, text=None):
		return self._email
		
class EvolutionHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "stock_addressbook")	
	
	def initialize(self):
		deskbar.evolution.set_pixbuf_size(deskbar.ICON_SIZE)
		
	def query(self, query, max=5):
		hits = deskbar.evolution.search_sync(query, max)
		matches = []
		for name, email, pixbuf in hits:
			if name == None or email == None:
				continue
			
			matches.append(EvolutionMatch(self, name, email, pixbuf))
		return matches
