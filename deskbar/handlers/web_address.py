from gettext import gettext as _
import re, os
import gobject
import gnomevfs
import deskbar.Handler
import deskbar.Match
from deskbar.defs import VERSION

HANDLERS = {
	"WebAddressHandler" : {
		"name": _("Web"),
		"description": _("Open web pages and send emails by typing a complete address"),
		"version": VERSION,
	}
}

AUTH_REGEX = re.compile(r'[a-zA-Z]+://\w+(:\w+)?@([\w\-]+\.)+[\w\-]+(:\d+)?(/.*)?')
HTTP_REGEX = re.compile(r'^(?P<method>[a-zA-Z]+://)?([\w\-]+\.)+[\w\-]+(:\d+)?(/.*)?$')
MAIL_REGEX = re.compile(r'^([\w\-]+\.)*[\w\-]+@([\w\-]+\.)*[\w\-]+$')

class WebAddressMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, has_method=True, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		
		self.has_method = has_method
		if not has_method and not self.name.startswith("http://"):
			self.name = "http://" + name
		
	def action(self, text=None):
		if self.name.startswith("http"):
			gnomevfs.url_show(self.name)
		else:
			gobject.spawn_async(["nautilus", self.name], flags=gobject.SPAWN_SEARCH_PATH)
			
	def get_category(self):
		return "web"
	
	def get_verb(self):
		if not self.has_method:
			return _("Open the web page %s") % "<b>%(name)s</b>"
		else:
			return _("Open the location %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.name

class EmailAddressMatch(deskbar.Match.Match):
	def __init__(self, backend, **args):
		deskbar.Match.Match.__init__(self, backend, icon="stock_mail", **args)
		
	def action(self, text=None):
		gnomevfs.url_show("mailto:"+self.name)
		
	def get_category(self):
		return "people"
	
	def get_verb(self):
		return _("Send Email to %s") % "<b>%(name)s</b>"
	
	def get_hash(self, text=None):
		return self.name
		
class WebAddressHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, "stock_internet")
	
	def query(self, query):
		result = self.query_http(query)
		result += self.query_mail(query)
		return result
		
	def query_http(self, query):
		match = AUTH_REGEX.match(query)
		if match != None:
			return [WebAddressMatch(self, query)]
		
		match = HTTP_REGEX.match(query)
		if match != None:
			return [WebAddressMatch(self, query, (match.group('method') != None))]
	
		return []
		
	def query_mail(self, query):
		if REGEX.match(query) != None:
			return [EmailAddressMatch(self, name=query)]
		else:
			return []
