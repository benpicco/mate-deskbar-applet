import dbus, dbus.glib
from gettext import gettext as _
import deskbar, deskbar.Indexer, deskbar.Handler, deskbar.Utils
from deskbar.defs import VERSION
import gdmclient
import gtk, gnome, gnome.ui

HANDLERS = {
	"GdmHandler" : {
		"name": _("Computer Actions"),
		"description": _("Logoff, shutdown, restart, suspend and related actions."),
		"version": VERSION,
	}
}

class GpmMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		obj = bus.get_object('org.gnome.PowerManager', '/org/gnome/PowerManager')
		self._gpm = dbus.Interface (obj, "org.gnome.PowerManager")

	def get_category(self):
		return "actions"


class SuspendMatch(GpmMatch):
	def __init__(self, backend, name=None, **args):
		GpmMatch.__init__(self, backend, name)
		self._icon = deskbar.Utils.load_icon("gpm-suspend-to-ram.png")

	def action(self, text=None):
		try:
			self._gpm.Suspend()
		except dbus.DBusException:
			# this will trigger a method timeout exception.
			# As a workaround we swallow it silently
			pass

	def get_category(self):
		return "actions"

	def get_verb(self):
		return _("Suspend the machine")

class HibernateMatch(GpmMatch):
	def __init__(self, backend, name=None, **args):
		GpmMatch.__init__(self, backend, name)
		self._icon = deskbar.Utils.load_icon("gpm-suspend-to-disk.png")

	def action(self, text=None):
		try:
			self._gpm.Hibernate()
		except dbus.DBusException:
			# this will trigger a method timeout exception.
			# As a workaround we swallow it silently
			pass

	def get_verb(self):
		return _("Hibernate the machine")

class ShutdownMatch(GpmMatch):
	def __init__(self, backend, name=None, **args):
		GpmMatch.__init__(self, backend, name)
		self._icon = deskbar.Utils.load_icon(gtk.STOCK_QUIT) 

	def action(self, text=None):
		try:
			self._gpm.Shutdown()
		except dbus.DBusException:
			# this will trigger a method timeout exception.
			# As a workaround we swallow it silently
			pass

	def get_verb(self):
		return _("Shutdown the machine")

class LockScreenMatch(deskbar.Match.Match):
	def __init__(self, backend, name=None, **args):
		deskbar.Match.Match.__init__(self, backend, name=name, **args)
		self._icon = deskbar.Utils.load_icon(gtk.STOCK_FULLSCREEN)
		
		bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		obj = bus.get_object('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver')
		# FIXME : This timeouts ?
		self._scrsvr = dbus.Interface (obj, "org.gnome.ScreenSaver")

	def action(self, text=None):
		try:
			self._scrsvr.Lock()
		except dbus.DBusException:
			# this will trigger a method timeout exception.
			# As a workaround we swallow it silently
			pass

	def get_category(self):
		return "actions"

	def get_verb(self):
		return _("Lock the screen")

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
		deskbar.Handler.Handler.__init__(self, "gpm-suspend-to-ram.png")	
		self.indexer = deskbar.Indexer.Indexer()
		
	def initialize(self):
		for klass in (GdmShutdownMatch,GdmSwitchUserMatch,GdmRebootMatch,GdmLogoutMatch):
			match = klass(self)
			self.indexer.add(match.get_verb(), match)
		
		self.init_gpm_matches()
		self.init_screensaver_matches()

	def init_screensaver_matches(self):
		try:
			bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
			obj = bus.get_object('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver')
			scrsvr = dbus.Interface (obj, "org.gnome.ScreenSaver")
			self.indexer.add(_("Lock"), LockScreenMatch(self))
			return True
		except dbus.dbus_bindings.DBusException:
			return False

	def init_gpm_matches(self):
		try:
			bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
			obj = bus.get_object('org.gnome.PowerManager', '/org/gnome/PowerManager')
			gpm = dbus.Interface (obj, "org.gnome.PowerManager")
			if gpm.canSuspend():
				self.indexer.add(_("Suspend"), SuspendMatch(self))
			if gpm.canHibernate():
				self.indexer.add(_("Hibernate"), HibernateMatch(self))
			if gpm.canShutdown():
				self.indexer.add(_("Shutdown"), ShutdownMatch(self))
		except dbus.dbus_bindings.DBusException:
			return False
			
	def query(self, query):
		return self.indexer.look_up(query)
