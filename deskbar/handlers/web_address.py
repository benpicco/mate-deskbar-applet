from gettext import gettext as _
import re, os
import gnomevfs
import deskbar.handler

HANDLERS = {
	"WebAddressHandler" : {
		"name": _("Web Addresses"),
		"description": _("Open webpages by typing an address."),
	}
}

AUTH_REGEX = re.compile(r'[a-zA-Z]+://\w+(:\w+)?@([\w\-]+\.)+[\w\-]+(:\d+)?(/.*)?')
HTTP_REGEX = re.compile(r'^(?P<method>[a-zA-Z]+://)?([\w\-]+\.)+[\w\-]+(:\d+)?(/.*)?$')

class WebAddressMatch(deskbar.handler.Match):
	def __init__(self, backend, url, has_method=True):
		deskbar.handler.Match.__init__(self, backend, url)
		
		self._has_method = has_method
		self._url = url
		if not has_method:
			self._url = "http://" + url
		
	def action(self, text=None):
		self._priority = self._priority+1
		if self._url.startswith("http"):
			gnomevfs.url_show(self._url)
		else:
			os.spawnlp(os.P_NOWAIT, "nautilus", "nautilus", self._url)
	
	def get_verb(self):
		if not self._has_method:
			return _("Open the web page <b>%(name)s</b>")
		else:
			return _("Open the location <b>%(name)s</b>")
		
class WebAddressHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "stock_internet")
	
	def query(self, query, max=5):
		match = AUTH_REGEX.match(query)
		if match != None:
			return [WebAddressMatch(self, query)]
		
		match = HTTP_REGEX.match(query)
		if match != None:
			return [WebAddressMatch(self, query, (match.group('method') != ""))]
	
		return []
