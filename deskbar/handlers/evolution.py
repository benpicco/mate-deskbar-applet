from gettext import gettext as _
import cgi, re
import gnomevfs
import deskbar, deskbar.indexer, deskbar.handler, deskbar.evolution

def _on_more_information():
	import gtk
	message_dialog = gtk.MessageDialog(buttons=gtk.BUTTONS_CLOSE)
	message_dialog.set_markup(
		"<span size='larger' weight='bold'>%s</span>\n\n%s" % (
		_("Autocompletion Needs to be Enabled"),
		_("We cannot provide e-mail addresses from your address book unless autocompletion is enabled.  To do this, from your mail program's menu, choose Edit → Preferences → Autocompletion.")));
	resp = message_dialog.run()
	if resp == gtk.RESPONSE_CLOSE:
		message_dialog.destroy()

def _check_requirements():
	if deskbar.evolution.num_address_books_with_completion() > 0:
		return (deskbar.handler.HANDLER_IS_HAPPY, None, None)
	else:
		return (deskbar.handler.HANDLER_IS_CONFIGURABLE, _("You need to enable autocomplete in your mail preferences"), _on_more_information)

HANDLERS = {
	"EvolutionHandler" : {
		"name": _("Mail (Address Book)"),
		"description": _("Send mail to your contacts by typing their name or e-mail address"),
		"requirements" : _check_requirements
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
