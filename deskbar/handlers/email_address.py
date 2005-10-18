from gettext import gettext as _

import gnomevfs
import deskbar.handler
import re

HANDLERS = {
	"EmailAddressHandler" : {
		"name": _("Email Addresses"),
		"description": _("Send mails by typing an email address."),
	}
}

REGEX = re.compile(r'[\w\-][\w\-\.]*@[\w\-][\w\-\.]*[\w]')

class EmailAddressMatch(deskbar.handler.Match):
	def __init__(self, backend, email):
		deskbar.handler.Match.__init__(self, backend, email)
		
		self._email = email
		
	def action(self, text=None):
		gnomevfs.url_show("mailto:"+self._email)
	
	def get_verb(self):
		return _("Send Email to <b>%(name)s</b>")
		
		
	
class EmailAddressHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "mail.png")
		
	def query(self, query, max=5):
		return [EmailAddressMatch(self, m) for m in REGEX.findall(query)]
