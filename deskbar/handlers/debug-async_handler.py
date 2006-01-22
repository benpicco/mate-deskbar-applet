from deskbar.Handler import *
from deskbar.Match import *
from time import sleep
import gtk

HANDLERS = {
	"AsyncDebugHandler" : {
		"name": "Debug (Async)",
	}
}

# Change these values to for your debugging pleasures
QUERY_TIME = 1
NUM_QUERIES = 6
PARTIAL_RESULTS_TIME = 3

class AsyncDebugMatch (Match):
	def __init__(self, handler, name=None, icon=None):
		Match.__init__ (self, handler, name)
	
	def get_verb(self):
		return "%(name)s - %(text)s"
		
	def action(self, text=None):
		print str(self.__class__) + " : action triggered"
		
	def get_category (self):
		return "debug"

class AsyncDebugHandler (AsyncHandler): 

	def __init__ (self):
		AsyncHandler.__init__ (self, "stock_script")
		
	def query (self, qstring, max):
		
		for i in range (NUM_QUERIES):
			sleep (QUERY_TIME)
			print "Querying: " + (i+1)*"."
			if i == PARTIAL_RESULTS_TIME:
				# emit partial results
				self.emit_query_ready ([AsyncDebugMatch(self, "AsyncDebug:partial results - %s"%qstring)])
				
			# This call will exit this method if there's a new query pending
			# or we have been instructed to stop:
			self.check_query_changed (self.clean_me, [qstring])
		
		# it is also allowed to return matches like this:
		return [AsyncDebugMatch(self, "AsyncDebug:returned results - %s"%qstring)]
				
	def clean_me (self, args):
		print str(self.__class__) + " : Clean up for query: " + str(args)
		
	def stop (self):
		print str(self.__class__) + " : stop() called"

