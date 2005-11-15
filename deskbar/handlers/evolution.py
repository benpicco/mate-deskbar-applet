from gettext import gettext as _
import cgi, re
import gnomevfs
import deskbar, deskbar.indexer, deskbar.handler, deskbar.evolution

HANDLERS = {
	"EvolutionHandler" : {
		"name": _("Mail (Address Book)"),
		"description": _("Send mail to your contacts by typing their name or e-mail address"),
	}
}

NAME_REGEX = re.compile(r"(.*) <.*?>")

class EvolutionMatch(deskbar.handler.Match):
	def __init__(self, backend, name, email, icon):
		deskbar.handler.Match.__init__(self, backend, name, icon)
		self._email = email
		
	def action(self, text=None):
		self._priority = self._priority+1
		gnomevfs.url_show("mailto:"+self._email)
	
	def get_name(self, text=None):
		return {
			"name": cgi.escape(self._name),
			"email": self._email,
		}
		
	def get_verb(self):
		#translators: First %s is the contact full name, second %s is the email address
		return _("Send Email to %s (%s)") % ("<b>%(name)s</b>", "%(email)s")
	
	def get_hash(self, text=None):
		return self._email
		
class EvolutionHandler(deskbar.handler.SignallingHandler):
	def __init__(self):
		deskbar.handler.SignallingHandler.__init__(self, "stock_addressbook")	
	
	def initialize(self):
		deskbar.evolution.set_pixbuf_size(deskbar.ICON_SIZE)
		
	def callback(self, hits, query, n):
		matches = []
		for name, email, pixbuf in hits:
			if name == None or email == None:
				continue
			
			# Strip the <xx@xx.com>	suffix
			match = NAME_REGEX.match(name)
			if match != None:
				name = match.group(1)
			
			matches.append(EvolutionMatch(self, name, email, pixbuf))
			
		self.emit_query_ready(matches, query)
		
	def query(self, query, max=5):
		deskbar.evolution.search_async(self.callback, query, max)
