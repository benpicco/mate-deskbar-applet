from gettext import gettext as _
import deskbar, deskbar.Indexer, deskbar.Handler, deskbar.Utils
from deskbar.defs import VERSION
import gdmclient
import gtk, gnome, gnome.ui

HANDLERS = {
	"GdmHandler" : {
		"name": _("Computer Actions"),
		"description": _("Logoff, shutdown, restart and switch user actions."),
		"version": VERSION,
	}
}

class GdmMatch(deskbar.Match.Match):
	def __init__(self, backend, name, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		self.logout_reentrance = 0
		
	def get_category(self):
		return "actions"

	def request_logout(self):
		if self.logout_reentrance == 0:
			self.logout_reentrance += 1

			client = gnome.ui.master_client()
			if client:
				client.request_save(gnome.ui.SAVE_GLOBAL,
					True, # Shutdown?
					gnome.ui.INTERACT_ANY,
					True, # Fast?
					True) # Global?

				self.logout_reentrance -= 1
            
class GdmShutdownMatch(GdmMatch):
	def __init__(self, backend, **args):
		GdmMatch.__init__(self, backend, _("Shut Down"), **args)
		
	def action(self, text=None):
		gdmclient.set_logout_action(gdmclient.LOGOUT_ACTION_SHUTDOWN)
		self.request_logout()
		
	def get_verb(self):
		return _("Turn off the computer")

class GdmLogoutMatch(GdmMatch):
	def __init__(self, backend, **args):
		GdmMatch.__init__(self, backend, _("Log Out"), **args)
		
	def action(self, text=None):
		gdmclient.set_logout_action(gdmclient.LOGOUT_ACTION_NONE)
		self.request_logout()
		
	def get_verb(self):
		return _("Log out")
		
class GdmRebootMatch(GdmMatch):
	def __init__(self, backend, **args):
		GdmMatch.__init__(self, backend, _("Restart"), **args)
		
	def action(self, text=None):
		gdmclient.set_logout_action(gdmclient.LOGOUT_ACTION_REBOOT)
		self.request_logout()
		
	def get_verb(self):
		return _("Restart the computer")
		
class GdmSwitchUserMatch(GdmMatch):
	def __init__(self, backend, **args):
		GdmMatch.__init__(self, backend, _("Switch User"), **args)
		
	def action(self, text=None):
		gdmclient.new_login()
		
	def get_verb(self):
		return _("Switch User")
				
class GdmHandler(deskbar.Handler.Handler):
	def __init__(self):
		deskbar.Handler.Handler.__init__(self, gtk.STOCK_EXECUTE)	
		self.indexer = deskbar.Indexer.Indexer()
		
	def initialize(self):
		for klass in (GdmShutdownMatch,GdmSwitchUserMatch,GdmRebootMatch,GdmLogoutMatch):
			match = klass(self)
			self.indexer.add(match.get_verb(), match)
		
	def query(self, query):
		return self.indexer.look_up(query)
