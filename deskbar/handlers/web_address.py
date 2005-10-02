from gettext import gettext as _

import gnomevfs
import handler

PRIORITY = 250

class WebAddressMatch(handler.Match):
	def __init__(self, backend, url):
		handler.Match.__init__(self, backend, url)
		
		self._is_web_page = False
		if url.find('://') == -1:
			url = 'http://' + url
		if url.startswith('http'):
			self._is_web_page = True
		self._url = url
		
	def action(self, text=None):
		gnomevfs.url_show(self._url)
	
	def get_verb(self):
		if self._is_web_page:
			return _("Open the web page <b>%(name)s</b>")
		else:
			return _("Open the location <b>%(name)s</b>")
		
		
	
class WebAddressHandler(handler.Handler):
	def __init__(self):
		handler.Handler.__init__(self, "web.png")
	
	def get_priority(self):
		return PRIORITY
		
	def query(self, query, max=5):
		if len(query) == 0:
			return []
		
		if query.find(" ") != -1:
			return []
			
		if query.find(".") != -1 and not query.endswith(".") and not query.startswith(".") and query.find("@") == -1:
			return [WebAddressMatch(self, query)]
		else:
			return []
