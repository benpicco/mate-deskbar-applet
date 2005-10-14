from gettext import gettext as _

import gnomevfs
import deskbar.handler
import re

EXPORTED_CLASS = "EmailAddressHandler"
NAME = (_("Email Addresses"), _("Send mails to people in your address book."))

PRIORITY = 250
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
	
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		return [EmailAddressMatch(self, m) for m in REGEX.findall(query)]
