from handler import AsyncHandler, Match
from deskbar import MODULES_DIRS

import os
from os.path import expanduser, exists, join
from gettext import gettext as _

try:
	from SOAPpy import WSDL
except:
	pass
	
import gtk

GOOGLE_WSDL = expanduser('~/.gnome2/deskbar-applet/GoogleSearch.wsdl')
GOOGLE_API_KEY = expanduser('~/.gnome2/deskbar-applet/Google.key')
HELP_FILE = 'GoogleLiveHelp.txt'
GOOGLE_HELP = exists(join(MODULES_DIRS[0], HELP_FILE)) and join(MODULES_DIRS[0], HELP_FILE) or join(MODULES_DIRS[1], HELP_FILE)
MAX_QUERIES = 10
QUERY_DELAY = 1

def _print_help():
	if exists (GOOGLE_HELP): print "GoogleLive: Read the file %s for further instructions." % GOOGLE_HELP
	else: print "GoogleLive: You need a Google API key and WSDL file. You can obtain these on api.google.com."
		

def _check_requirements():
	try:
		from SOAPpy import WSDL
	except:
		_print_help()
		return (False, "You need SOAPpy python module for google-live to work properly.")
	if not exists (GOOGLE_WSDL):
		_print_help()
		return (False, "WSDL file %s not found. Aborting." % GOOGLE_WSDL)
	if not exists (GOOGLE_API_KEY):
		_print_help()
		return (False, "Google API key file %s not found. Aborting." % GOOGLE_API_KEY)
	else:
		return (True, None)
		
HANDLERS = {
	"GoogleLiveHandler" : {
		"name": _("Live Google search"),
		"description": _("Search the words you type with Google and display the results in the list."),
		"requirements" : _check_requirements
	}
}


class GoogleMatch (Match):
	def __init__(self, handler, name, url, icon=None):
		Match.__init__ (self, handler, "Google: "+name, icon)
		self.__url = url
	
	def get_verb(self):
		return "%(name)s"
		
	def action(self, text=None):
		os.spawnlp(os.P_NOWAIT, "gnome-open", "gnome-open", self.__url)

class GoogleLiveHandler (AsyncHandler):
	"""
	This handler requires the user to have a valid Google account, a Google
	API key and a GoogleSearch.wsdl file. The file locations are specified
	above.
	
	It uses SOAPpy to interact with Googles SOAP inteface.
	"""
	def __init__ (self):
		AsyncHandler.__init__ (self, "google.png")
		self.server = None
		self.api_key = None
		
	def initialize (self):
		self.server = WSDL.Proxy (GOOGLE_WSDL)
		api_key_file = file (GOOGLE_API_KEY)
		self.api_key = api_key_file.readline()
		api_key_file.close ()
		
	
	def query (self, qstring, qmax=5):
		"""Behold the true power of the AsyncHandler!"""
		
		# Just to ensure we don't bork anything
		qmax = min (qmax, 10)
		
		# Delay before we query so we *don't* make four queries
		# "s", "sp", "spa", "spam".
		self.check_query_changed (timeout=QUERY_DELAY)
		
		print "GoogleLive: Querying Google for", qstring
		results = self.server.doGoogleSearch (self.api_key, # personal google api key
						qstring, 	# query
						0, qmax, 	# start/end of result list
						True, 		# filter duplicates?
						"", 		# get results from specific country
						False, 		# safe search (filter adult material)
						"", 		# get results in specific language
						"utf-8", "utf-8") # input/output encodings
					
		# The google search might have taken a long time
		# better check if we're still valid	
		self.check_query_changed ()
		return [
			GoogleMatch (self, r.title.encode("utf-8"), 
					#r.snippet.encode("utf-8"),  # We don't use the description
					r.URL.encode ("utf-8"))
			for r in results.resultElements[:qmax-1]
		]
