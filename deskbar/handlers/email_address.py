from gettext import gettext as _

import gnomevfs
import deskbar.handler
import re

HANDLERS = {
	"EmailAddressHandler" : {
		"name": _("Mail"),
		"description": _("Send mail by typing a complete e-mail address"),
	}
}

REGEX = re.compile(r'^([\w\-]+\.)*[\w\-]+@([\w\-]+\.)*[\w\-]+$')

class EmailAddressMatch(deskbar.handler.Match):
	def __init__(self, backend, email):
		deskbar.handler.Match.__init__(self, backend, email)
		
		self._email = email
		
	def action(self, text=None):
		gnomevfs.url_show("mailto:"+self._email)
	
	def get_verb(self):
		return _("Send Email to %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self._email
		
	
class EmailAddressHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "stock_mail")
		
	def query(self, query, max=5):
		if REGEX.match(query) != None:
			return [EmailAddressMatch(self, query)]
		else:
			return []
