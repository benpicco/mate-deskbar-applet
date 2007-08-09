import dbus, dbus.glib
from gettext import gettext as _
import deskbar, deskbar.core.Indexer, deskbar.interfaces.Match, deskbar.interfaces.Module, deskbar.core.Utils
from deskbar.defs import VERSION
import deskbar.handlers.gdmclient
import gtk, gnome.ui
import deskbar.interfaces.Action

HANDLERS = ["GdmHandler"]

class GpmAction(deskbar.interfaces.Action):
	
	def __init__(self):
		deskbar.interfaces.Action.__init__(self, "")
		bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		obj = bus.get_object('org.gnome.PowerManager', '/org/gnome/PowerManager')
		self._gpm = dbus.Interface (obj, "org.gnome.PowerManager")
		
class SuspendAction(GpmAction):
	
	def __init__(self):
		GpmAction.__init__(self)
	
	def activate(self, text=None):
		try:
			self._gpm.Suspend()
		except dbus.DBusException:
			# this will trigger a method timeout exception.
			# As a workaround we swallow it silently
			pass

	def get_verb(self):
		return _("Suspend the machine")
	
class HibernateAction(GpmAction):
	
	def __init__(self):
		GpmAction.__init__(self)

	def activate(self, text=None):
		try:
			self._gpm.Hibernate()
		except dbus.DBusException:
			# this will trigger a method timeout exception.
			# As a workaround we swallow it silently
			pass

	def get_verb(self):
		return _("Hibernate the machine")
	
class ShutdownAction(GpmAction):
		
	def __init__(self):
		GpmAction.__init__(self)
		
	def activate(self, text=None):
		try:
			self._gpm.Shutdown()
		except dbus.DBusException:
			# this will trigger a method timeout exception.
			# As a workaround we swallow it silently
			pass

	def get_verb(self):
		return _("Shutdown the machine")
	
class LockScreenAction(deskbar.interfaces.Action):
		
	def __init__(self):
		deskbar.interfaces.Action.__init__(self, "")
		
		bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		obj = bus.get_object('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver')
		# FIXME : This timeouts ?
		self._scrsvr = dbus.Interface (obj, "org.gnome.ScreenSaver")

	def activate(self, text=None):
		try:
			self._scrsvr.Lock()
		except dbus.DBusException:
			# this will trigger a method timeout exception.
			# As a workaround we swallow it silently
			pass

	def get_verb(self):
		return _("Lock the screen")

class GpmMatch(deskbar.interfaces.Match):
	def __init__(self, **args):
		deskbar.interfaces.Match.__init__(self, category="actions", **args)	

class SuspendMatch(GpmMatch):
	def __init__(self, **args):
		GpmMatch.__init__(self, category="actions", icon="gpm-suspend-to-ram.png")
		self.add_action( SuspendAction() )

class HibernateMatch(GpmMatch):
	def __init__(self, **args):
		GpmMatch.__init__(self, icon = "gpm-suspend-to-disk.png")
		self.add_action( HibernateAction() )

class ShutdownMatch(GpmMatch):
	def __init__(self, **args):
		GpmMatch.__init__(self, icon = gtk.STOCK_QUIT)
		self.add_action( ShutdownAction() )
	
class LockScreenMatch(deskbar.interfaces.Match):
	def __init__(self, **args):
		deskbar.interfaces.Match.__init__(self, name=_("Lock"), icon = gtk.STOCK_FULLSCREEN, **args)
		self.add_action( LockScreenAction() )

	def get_category(self):
		return "actions"
	
class GdmAction(deskbar.interfaces.Action):
		
	def __init__(self, name):
		deskbar.interfaces.Action.__init__(self, name)
		self.logout_reentrance = 0
	
	def __request_logout(self):
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
				
class GdmMatch(deskbar.interfaces.Match):
	def __init__(self, **args):
		deskbar.interfaces.Match.__init__(self, category="actions", **args)
	
class GdmShutdownAction(GdmAction):
	
	def __init__(self, name):
		GdmAction.__init__(self, name)
		
	def activate(self, text=None):
		deskbar.handlers.gdmclient.set_logout_action(deskbar.handlers.gdmclient.LOGOUT_ACTION_SHUTDOWN)
		self.request_logout()
		
	def get_verb(self):
		return _("Turn off the computer")
			
class GdmShutdownMatch(GdmMatch):
	def __init__(self, **args):
		GdmMatch.__init__(self, name=_("Shut Down"), **args)
		self.add_action( GdmShutdownAction(self.get_name()) )
	
class GdmLogoutAction(GdmAction):
	def __init__(self, name):
		GdmAction.__init__(self, name)
		
	def activate(self, text=None):
		deskbar.handlers.gdmclient.set_logout_action(deskbar.handlers.gdmclient.LOGOUT_ACTION_NONE)
		self.request_logout()
		
	def get_verb(self):
		return _("Log out")
		
class GdmLogoutMatch(GdmMatch):
	def __init__(self, **args):
		GdmMatch.__init__(self, name=_("Log Out"), **args)
		self.add_action( GdmLogoutAction(self.get_name()) )
	
class GdmRebootAction(GdmAction):
	def __init__(self, name):
		GdmAction.__init__(self, name)
		
	def activate(self, text=None):
		deskbar.handlers.gdmclient.set_logout_action(deskbar.handlers.gdmclient.LOGOUT_ACTION_REBOOT)
		self.request_logout()
		
	def get_verb(self):
		return _("Restart the computer")
	
class GdmRebootMatch(GdmMatch):
	def __init__(self, **args):
		GdmMatch.__init__(self, name=_("Restart"), **args)
		self.add_action( GdmRebootAction(self.get_name()) )
	
class GdmSwitchUserAction(GdmAction):	
	def __init__(self, name):
		GdmAction.__init__(self, name)
		
	def activate(self, text=None):
		deskbar.handlers.gdmclient.new_login()
		
	def get_verb(self):
		return _("Switch User")
					
class GdmSwitchUserMatch(GdmMatch):
	def __init__(self, **args):
		GdmMatch.__init__(self, name=_("Switch User"), **args)
		self.add_action( GdmSwitchUserAction(self.get_name()) )
	
class GdmHandler(deskbar.interfaces.Module):
	
	INFOS = {'icon':  deskbar.core.Utils.load_icon("gpm-suspend-to-ram.png"),
			 "name": _("Computer Actions"),
			 "description": _("Logoff, shutdown, restart, suspend and related actions."),
			 "version": VERSION}
	ACTIONS = ((GdmShutdownMatch, _("Shut Down")),
			(GdmSwitchUserMatch, _("Switch User")),
			(GdmRebootMatch, _("Restart")),
			(GdmLogoutMatch, _("Log Out")))
	def __init__(self):
		deskbar.interfaces.Module.__init__(self)	
		self.indexer = deskbar.core.Indexer.Indexer()
		
	def initialize(self):
		for klass, verb in self.ACTIONS:
			match = klass()
			self.indexer.add(verb, match)
		
		self.init_gpm_matches()
		self.init_screensaver_matches()

	def init_screensaver_matches(self):
		try:
			bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
			obj = bus.get_object('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver')
			scrsvr = dbus.Interface (obj, "org.gnome.ScreenSaver")
			self.indexer.add(_("Lock"), LockScreenMatch())
			return True
		except dbus.DBusException:
			return False

	def init_gpm_matches(self):
		try:
			bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
			obj = bus.get_object('org.gnome.PowerManager', '/org/gnome/PowerManager')
			gpm = dbus.Interface (obj, "org.gnome.PowerManager")
			if gpm.canSuspend():
				self.indexer.add(_("Suspend"), SuspendMatch())
			if gpm.canHibernate():
				self.indexer.add(_("Hibernate"), HibernateMatch())
			if gpm.canShutdown():
				self.indexer.add(_("Shutdown"), ShutdownMatch())
		except dbus.DBusException:
			return False
			
	def query(self, query):
		matches = self.indexer.look_up(query)
		self.set_priority_for_matches( matches )
		self._emit_query_ready(query, matches )
