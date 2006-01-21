from deskbar.Handler import *
from deskbar.Match import *
from time import sleep
import gobject

HANDLERS = {
	"SignallingDebugHandler" : {
		"name": "Debug (Signalling)",
	}
}

SIGNAL_DELAY = 1000 # 1 sec.

class SignallingDebugMatch (Match):
	def __init__(self, handler, name, icon=None):
		Match.__init__ (self, handler, name)
		
	def get_verb(self):
		return "%(name)s - %(text)s"
		
	def action(self, text=None):
		print str(self.__class__) + " : action triggered"
		
	def get_category (self):
		return "debug"


class SignallingDebugHandler(SignallingHandler):
	def __init__(self):
		SignallingHandler.__init__(self, "stock_script")
		
	def query(self, qstring, max):
		# gobject.timeout_add represents an async lib call
		self.sig = gobject.timeout_add(SIGNAL_DELAY, lambda : self.__callback(qstring))

	def __callback(self, qstring):
		match = SignallingDebugMatch(self, "SignallingDebug:"+qstring)
		self.emit_query_ready([match], qstring)
		
		# Keep sending the results, see if filter works ok
		return True
		
	def stop_query(self):
		if hasattr(self, "sig"):
			gobject.source_remove(self.sig)
