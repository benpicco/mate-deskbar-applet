from time import sleep
from handler import Handler
from handler import Match

HANDLERS = {
	"DebugBlockingInitModule" : {
		"name": "Debug/Blocking Init",
		"description": "Blocking Init Module",
	}
}
INIT_TIME = 0

class DebugBlockingInitMatch(Match):
	def __init__(self, handler, name, icon=None):
		Match.__init__ (self, handler, name)
	
	def get_verb(self):
		return "%(name)s - %(text)s"
		
	def action(self, text=None):
		pass

class DebugBlockingInitModule(Handler):
	def __init__ (self):
		Handler.__init__ (self, None)
		
	def initialize (self):
		print "DebugBlockingInitModule initializing ... This will block for %s seconds." % INIT_TIME
		for i in range(INIT_TIME):
			print (i+1)*"."
			sleep (1)
		
	def query (self, qstring, max):
		if max > 0:
			return [DebugBlockingInitMatch(self, "TestMatch")]
		else:
			return []	
