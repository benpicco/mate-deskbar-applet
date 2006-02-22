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
	def __init__(self, backend, **args):
		deskbar.Match.Match.__init__(self, backend, **args)
		
	def action(self, text=None):
		gnomevfs.url_show("mailto:"+self.name)
		
	def get_category(self):
		return "people"
	
	def get_verb(self):
		return _("Send Email to %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.name
		
	
class EmailAddressHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "stock_mail")
		
	def query(self, query):
		if REGEX.match(query) != None:
			return [EmailAddressMatch(self, name=query)]
		else:
			return []
