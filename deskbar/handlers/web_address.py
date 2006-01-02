from gettext import gettext as _
import re, os
import gobject
import gnomevfs
import deskbar.handler

HANDLERS = {
	"WebAddressHandler" : {
		"name": _("Web"),
		"description": _("Open web pages by typing a complete web address"),
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
		if self._url.startswith("http"):
			gnomevfs.url_show(self._url)
		else:
			gobject.spawn_async(["nautilus", self._url], flags=gobject.SPAWN_SEARCH_PATH)
	
	def get_verb(self):
		if not self._has_method:
			return _("Open the web page %s") % "<b>%(name)s</b>"
		else:
			return _("Open the location %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self._url
		
class WebAddressHandler(deskbar.handler.Handler):
	def __init__(self):
		deskbar.handler.Handler.__init__(self, "stock_internet")
	
	def query(self, query, max=5):
		match = AUTH_REGEX.match(query)
		if match != None:
			return [WebAddressMatch(self, query)]
		
		match = HTTP_REGEX.match(query)
		if match != None:
			return [WebAddressMatch(self, query, (match.group('method') != None))]
	
		return []
