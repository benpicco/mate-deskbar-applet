from gettext import gettext as _

import gnomevfs
import deskbar.Handler
import re

HANDLERS = {
	"EmailAddressHandler" : {
		"name": _("Mail"),
		"description": _("Send mail by typing a complete e-mail address"),
	}
}

REGEX = re.compile(r'^([\w\-]+\.)*[\w\-]+@([\w\-]+\.)*[\w\-]+$')

class EmailAddressMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, icon=None):
		deskbar.Match.Match.__init__(self, backend, name)
		
	def action(self, text=None):
		gnomevfs.url_show("mailto:"+self.name)
		
	def get_category(self):
		return "emails"
	
	def get_verb(self):
		return _("Send Email to %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.name
		
	
class EmailAddressHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "stock_mail")
		
	def query(self, query, max):
		if REGEX.match(query) != None:
			return [EmailAddressMatch(self, query)]
		else:
			return []
