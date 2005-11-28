import deskbar.handler, deskbar.handler_utils

def _on_more():
	print "More..."

def _check_requirements():
	import os.path
	if os.path.exists(os.path.expanduser("~/foo")):
		print "DebugRequirementsModule: Requirements met"
		return (deskbar.handler.HANDLER_IS_HAPPY, None, None)
	else:
		print "DebugRequirementsModule: Requirements not met"
		return (deskbar.handler.HANDLER_HAS_REQUIREMENTS,
			'You need to create a file called "~/foo"',
			lambda: deskbar.handler_utils.more_information_dialog(
			"Debug Requirements Title",
			"Debug Requirements Content"
			))

HANDLERS = {
	"DebugRequirementsModule" : {
		"name": "Debug (Requirements)",
		"requirements": _check_requirements,
	}
}

class DebugRequirementsMatch(deskbar.handler.Match):
	def __init__(self, handler, name, icon=None):
		deskbar.handler.Match.__init__ (self, handler, name)
	
	def get_verb(self):
		return "%(name)s - %(text)s"
		
	def action(self, text=None):
		pass

class DebugRequirementsModule(deskbar.handler.Handler):
	def __init__ (self):
		deskbar.handler.Handler.__init__ (self, "stock_script")
		
	def query (self, qstring, max):
		if max > 0:
			return [DebugRequirementsMatch(self, "TestMatch")]
		else:
			return []	
