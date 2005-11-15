from gettext import gettext as _

import gnomevfs
import deskbar, deskbar.indexer
import deskbar.handler

# FIXME: Waiting for python bindings of galago.
HANDLERS = {
	"GalagoHandler" : {
		"name": "Instant Messaging (IM) Buddies",
		"description": "Send messages to your buddies by typing their name",
		"requirements": lambda: (False, "Waiting for python bindings of galago. Should allow to send IM by typing name."),
	}
}

class GalagoMatch(deskbar.handler.Match):
	def __init__(self, backend, name, email):
		deskbar.handler.Match.__init__(self, backend, name)
		
		self._email = email
		
	def action(self, text=None):
		self._priority = self._priority+1
		gnomevfs.url_show("mailto:"+self._email)
	
	def get_verb(self):
		return _("Send Email to %s") % "<b>%(name)s</b>"
		
class GalagoHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "mail.png")	
		self._indexer = deskbar.indexer.Index()
	
	def initialize(self):
		# FIXME: Dummy entries		
		#self._indexer.add("William Gates III <billg@microsoft.com>", GalagoMatch(self, "William Gates III", "billg@microsoft.com"))
		#self._indexer.add("Steve Ballmer <steve@microsoft.com>", GalagoMatch(self, "Steve Ballmer", "steve@microsoft.com"))
		#self._indexer.add("Bill Joy <bjoy@sun.com>", GalagoMatch(self, "Bill Joy", "bjoy@sun.com"))
		pass
		
	def query(self, query, max=5):
		return self._indexer.look_up(query)[:5]
