import deskbar.Handler, deskbar.Match, deskbar
from deskbar.Utils import strip_html
import os, cgi
import gobject
import gnomevfs
from os.path import expanduser, exists, join
from gettext import gettext as _
from deskbar.defs import VERSION

try:
	from SOAPpy import WSDL
except:
	pass
	
GOOGLE_WSDL = expanduser('~/.gnome2/deskbar-applet/GoogleSearch.wsdl')
GOOGLE_API_KEY = expanduser('~/.gnome2/deskbar-applet/Google.key')
MAX_QUERIES = 10
QUERY_DELAY = 1

HELP_TEXT = _("""You need a Google account to use Google Live.  To get one, go to http://api.google.com/

When you have created your account, you should receive a Google API key by mail.  Place this key in the file

~/.gnome2/deskbar-applet/Google.key

If you do not receive an API key (or you have lost it) in your account verification mail, then go to www.google.com/accounts and log in.  Go to api.google.com, click "Create Account" and enter your e-mail address and password.  Your API key will be re-sent.

Now download the developers' kit and extract the GoogleSearch.wsdl file from it.  Copy this file to

~/.gnome2/deskbar-applet/GoogleSearch.wsdl""")

def _on_more_information(dialog):
	deskbar.Utils.more_information_dialog(dialog, _("Setting Up Google Live"), HELP_TEXT)

def _check_requirements():
	try:
		from SOAPpy import WSDL
	except:
		return (deskbar.Handler.HANDLER_IS_NOT_APPLICABLE, _("You need to install the SOAPpy python module."), None)
	if not exists (GOOGLE_WSDL):
		return (deskbar.Handler.HANDLER_HAS_REQUIREMENTS, _("You need the Google WSDL file."), _on_more_information)
	if not exists (GOOGLE_API_KEY):
		return (deskbar.Handler.HANDLER_HAS_REQUIREMENTS, _("You need a Google API key."), _on_more_information)
	else:
		return (deskbar.Handler.HANDLER_IS_HAPPY, None, None)
		
HANDLERS = {
	"GoogleLiveHandler" : {
		"name": _("Google Search"),
		"description": _("Search Google as you type"),
		"requirements" : _check_requirements,
		"version": VERSION,
	}
}


class GoogleMatch (deskbar.Match.Match):
	def __init__(self, handler, name, url, **args):
		deskbar.Match.Match.__init__ (self, handler, name=name, **args)
		self.url = url
	
	def get_verb(self):
		return "%(name)s"
		
	def action(self, text=None):
		gnomevfs.url_show(self.url)
		
	def get_category(self):
		return "web"
	
	def get_hash(self, text=None):
		return self.url

class GoogleLiveHandler (deskbar.Handler.AsyncHandler):
	"""
	This handler requires the user to have a valid Google account, a Google
	API key and a GoogleSearch.wsdl file. The file locations are specified
	above.
	
	It uses SOAPpy to interact with Googles SOAP inteface.
	"""
	def __init__ (self):
		deskbar.Handler.AsyncHandler.__init__ (self, "google.png")
		self.server = None
		self.api_key = None
		
	def initialize (self):                        
		self.server = WSDL.Proxy (GOOGLE_WSDL)
		
		try:
			proxy = os.environ['http_proxy']
			if proxy.startswith('http://'):
				proxy = proxy[len('http://'):]
			if proxy.endswith('/'):
				proxy = proxy[:len(proxy)-1]
				
			self.server.soapproxy.http_proxy = proxy
			print "Using http_proxy '%s' for google live" % proxy
		except KeyError:
			pass
			
		api_key_file = file (GOOGLE_API_KEY)
		self.api_key = api_key_file.readline()
		api_key_file.close ()
			
	def query (self, qstring):
		"""Behold the true power of the AsyncHandler!"""
		
		# Just to ensure we don't bork anything
		qmax = min (deskbar.DEFAULT_RESULTS_PER_HANDLER, MAX_QUERIES)
		
		# Delay before we query so we *don't* make four queries
		# "s", "sp", "spa", "spam".
		self.check_query_changed (timeout=QUERY_DELAY)
		
		#print "GoogleLive: Querying Google for", qstring
		print 'Query google for:', qstring
		results = self.server.doGoogleSearch (self.api_key, # personal google api key
						qstring, 	# query
						0, qmax, 	# start/end of result list
						True, 		# filter duplicates?
						"", 		# get results from specific country
						False, 		# safe search (filter adult material)
						"", 		# get results in specific language
						"utf-8", "utf-8") # input/output encodings
		print 'Got google answer for:', qstring
		
		# The google search might have taken a long time
		# better check if we're still valid	
		self.check_query_changed ()
		matches = [
			GoogleMatch (self, cgi.escape(strip_html(r.title.encode("utf-8"))), 
					#r.snippet.encode("utf-8"),  # We don't use the description
					r.URL.encode ("utf-8"))
			for r in results.resultElements[:qmax-1]
			]
		self.check_query_changed ()
		print "Returning google answer for:", qstring
		return matches
