import deskbar.Handler, deskbar.Utils

def _on_more(dialog):
	print "More..."

def _check_requirements():
	import os.path
	if os.path.exists(os.path.expanduser("~/foo")):
		print "DebugRequirementsModule: Requirements met"
		return (deskbar.Handler.HANDLER_IS_HAPPY, None, None)
	else:
		print "DebugRequirementsModule: Requirements not met"
		return (deskbar.Handler.HANDLER_HAS_REQUIREMENTS,
			'You need to create a file called "~/foo"',
			lambda: deskbar.Utils.more_information_dialog(
			"Debug Requirements Title",
			"Debug Requirements Content"
			))

HANDLERS = {
	"DebugRequirementsModule" : {
		"name": "Debug (Requirements)",
		"requirements": _check_requirements,
	}
}

class DebugRequirementsMatch(deskbar.Match.Match):
	def __init__(self, handler, **args):
		deskbar.Match.Match.__init__ (self, handler, **args)
	
	def get_verb(self):
		return "%(name)s - %(text)s"
		
	def action(self, text=None):
		pass
		
	def get_category (self):
		return "debug"

class DebugRequirementsModule(deskbar.Handler.Handler):
	def __init__ (self):
		deskbar.Handler.Handler.__init__ (self, "stock_script")
		
	def query (self, qstring):
		return [DebugRequirementsMatch(self, name="TestMatch")]
