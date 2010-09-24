from deskbar.defs import VERSION
from gettext import gettext as _
from gettext import ngettext
import dbus
import dbus.glib
import deskbar
import deskbar.core.Indexer
import deskbar.core.Utils
import deskbar.interfaces.Action
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import glib
import gtk

HANDLERS = ["GdmHandler"]

( PROMPT_SHUTDOWN,
  PROMPT_LOGOUT,
  PROMPT_REBOOT,
  PROMPT_SUSPEND,
  PROMPT_HIBERNATE
) = range(5)

TIMEOUT = 60
SESSION_MANAGER_PATH = '/org/gnome/SessionManager'
SESSION_MANAGER_SERVICE = 'org.gnome.SessionManager'

class LogoutPrompt(gtk.MessageDialog):
    
    def __init__(self, prompt_type, starttime):
        gtk.MessageDialog.__init__(self, flags=gtk.MESSAGE_QUESTION)
        self.connect('response', self.on_response)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.set_default_response(gtk.RESPONSE_OK)   
        self.prompt_type = prompt_type
        self.timeleft = starttime
        self.countdown_thread = None
        
        if prompt_type == PROMPT_SHUTDOWN:
            message = _("Shut down this system now?")
            button_label = _("Shut Down")
        elif prompt_type == PROMPT_LOGOUT:
            message = _("Log out of this system now?")
            button_label = _("Log Out")
        elif prompt_type == PROMPT_REBOOT:
            message = _("Restart this system now?")
            button_label = _("Restart")
        elif prompt_type == PROMPT_SUSPEND:
            message = _("Suspend this system now?")
            button_label = _("Suspend")
        elif prompt_type == PROMPT_HIBERNATE:
            message = _("Hibernate this system now?")
            button_label = _("Hibernate")
    
        self.add_button(button_label, gtk.RESPONSE_OK)
        self.set_markup(message)
        self.format_secondary_text(self.get_secondary(self.timeleft) % self.timeleft)
 
    def get_secondary(self, timeleft):
        if self.prompt_type == PROMPT_SHUTDOWN:
            secondary = ngettext("This system will be automatically shut down in %s second.",
                           "This system will be automatically shut down in %s seconds.",
                           timeleft)
        elif self.prompt_type == PROMPT_LOGOUT:
            secondary = ngettext("You will be automatically logged out in %s second.",
                           "You will be automatically logged out in %s seconds.",
                           timeleft)
        elif self.prompt_type == PROMPT_REBOOT:
            secondary = ngettext("This system will be automatically restarted in %s second.",
                           "This system will be automatically restarted in %s seconds.",
                           timeleft)
        elif self.prompt_type == PROMPT_SUSPEND:
            secondary = ngettext("This system will be automatically suspended in %s second.",
                           "This system will be automatically suspended in %s seconds.",
                           timeleft)
        elif self.prompt_type == PROMPT_HIBERNATE:
            secondary = ngettext("This system will be automatically hibernated in %s second.",
                           "This system will be automatically hibernated in %s seconds.",
                           timeleft)
        return secondary
    
    def countdown_func(self):
        self.timeleft -= 1
        if self.timeleft != 0:
            secondary = self.get_secondary(self.timeleft)
            self.format_secondary_text(secondary % self.timeleft)
            return True
        else:
            self.response(gtk.RESPONSE_OK)
            return False
        
    def run(self):
        self.countdown_thread = glib.timeout_add(1000, self.countdown_func)
        return gtk.MessageDialog.run(self)
    
    def on_response(self, dialog, response):
        if response == gtk.RESPONSE_CANCEL and self.countdown_thread != None:
            glib.source_remove(self.countdown_thread)

class GpmAction(deskbar.interfaces.Action):
    
    def __init__(self):
        deskbar.interfaces.Action.__init__(self, "")
        bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
        obj = bus.get_object('org.freedesktop.PowerManagement', '/org/freedesktop/PowerManagement')
        self._gpm = dbus.Interface (obj, "org.freedesktop.PowerManagement")
        
class SuspendAction(GpmAction):
    
    def __init__(self):
        GpmAction.__init__(self)
    
    def activate(self, text=None):
        prompt = LogoutPrompt(PROMPT_SUSPEND, TIMEOUT)
        response = prompt.run()
        prompt.destroy()
        
        try:
            if response == gtk.RESPONSE_OK:
                self._gpm.Suspend()
        except dbus.exceptions.DBusException:
            # this will trigger a method timeout exception.
            # As a workaround we swallow it silently
            pass

    def get_verb(self):
        return _("Suspend the machine")
    
class HibernateAction(GpmAction):
    
    def __init__(self):
        GpmAction.__init__(self)

    def activate(self, text=None):
        prompt = LogoutPrompt(PROMPT_HIBERNATE, TIMEOUT)
        response = prompt.run()
        prompt.destroy()
        
        try:
            if response == gtk.RESPONSE_OK:
                self._gpm.Hibernate()
        except dbus.exceptions.DBusException:
            # this will trigger a method timeout exception.
            # As a workaround we swallow it silently
            pass

    def get_verb(self):
        return _("Hibernate the machine")
    
class ShutdownAction(GpmAction):
        
    def __init__(self):
        GpmAction.__init__(self)
        
    def activate(self, text=None):
        prompt = LogoutPrompt(PROMPT_SHUTDOWN, TIMEOUT)
        response = prompt.run()
        prompt.destroy()
        
        try:
            if response == gtk.RESPONSE_OK:
                self._gpm.Shutdown()
        except dbus.exceptions.DBusException:
            # this will trigger a method timeout exception.
            # As a workaround we swallow it silently
            pass

    def get_verb(self):
        return _("Shutdown the machine")
    
    
class RebootAction(GpmAction):
        
    def __init__(self):
        GpmAction.__init__(self)
        
    def activate(self, text=None):
        prompt = LogoutPrompt(PROMPT_REBOOT, TIMEOUT)
        response = prompt.run()
        prompt.destroy()
        
        try:
            if response == gtk.RESPONSE_OK:
                self._gpm.Reboot()
        except dbus.exceptions.DBusException:
            # this will trigger a method timeout exception.
            # As a workaround we swallow it silently
            pass

    def get_verb(self):
        return _("Reboot the machine")
     
    
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
        except dbus.exceptions.DBusException:
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
        GpmMatch.__init__(self, icon="gpm-suspend-to-ram.png")
        self.add_action( SuspendAction() )

class HibernateMatch(GpmMatch):
    def __init__(self, **args):
        GpmMatch.__init__(self, icon = "gpm-suspend-to-disk.png")
        self.add_action( HibernateAction() )

class ShutdownMatch(GpmMatch):
    def __init__(self, **args):
        GpmMatch.__init__(self, icon = "gnome-shutdown")
        self.add_action( ShutdownAction() )

class RebootMatch(GpmMatch):
    def __init__(self, **args):
        GpmMatch.__init__(self, icon = "gtk-refresh")
        self.add_action( RebootAction() )
        
class LockScreenMatch(deskbar.interfaces.Match):
    def __init__(self, **args):
        deskbar.interfaces.Match.__init__(self, name=_("Lock"), icon = "system-lock-screen", **args)
        self.add_action( LockScreenAction() )

    def get_category(self):
        return "actions"

class GdmMatch(deskbar.interfaces.Match):
    def __init__(self, **args):
        deskbar.interfaces.Match.__init__(self, category="actions", **args)
    
class GdmShutdownAction(deskbar.interfaces.Action):
    
    def __init__(self, name):
        deskbar.interfaces.Action.__init__(self, name)
        
    def activate(self, text=None):
        prompt = LogoutPrompt(PROMPT_SHUTDOWN, TIMEOUT)
        response = prompt.run()
        prompt.destroy()
        
        if response == gtk.RESPONSE_OK:
            bus = dbus.SessionBus()
            obj = bus.get_object(SESSION_MANAGER_SERVICE, SESSION_MANAGER_PATH)
            sessionManager = dbus.Interface(obj, SESSION_MANAGER_SERVICE)
            sessionManager.RequestShutdown()
        
    def get_verb(self):
        return _("Turn off the computer")
            
class GdmShutdownMatch(GdmMatch):
    def __init__(self, **args):
        GdmMatch.__init__(self, name=_("Shut Down"), icon = "gnome-shutdown", **args)
        self.add_action( GdmShutdownAction(self.get_name()) )
    
class GdmLogoutAction(deskbar.interfaces.Action):
    def __init__(self, name):
        deskbar.interfaces.Action.__init__(self, name)
        
    def activate(self, text=None):
        prompt = LogoutPrompt(PROMPT_LOGOUT, TIMEOUT)
        response = prompt.run()
        prompt.destroy()
        
        if response == gtk.RESPONSE_OK:
            bus = dbus.SessionBus()
            obj = bus.get_object(SESSION_MANAGER_SERVICE, SESSION_MANAGER_PATH)
            sessionManager = dbus.Interface(obj, SESSION_MANAGER_SERVICE)
            sessionManager.Logout(dbus.types.UInt32(0))
        
    def get_verb(self):
        return _("Log Out")
        
class GdmLogoutMatch(GdmMatch):
    def __init__(self, **args):
        GdmMatch.__init__(self, name=_("Log Out"), icon = "system-log-out", **args)
        self.add_action( GdmLogoutAction(self.get_name()) )
    
class GdmRebootAction(deskbar.interfaces.Action):
    def __init__(self, name):
        deskbar.interfaces.Action.__init__(self, name)
        
    def activate(self, text=None):
        prompt = LogoutPrompt(PROMPT_REBOOT, TIMEOUT)
        response = prompt.run()
        prompt.destroy()
        
        if response == gtk.RESPONSE_OK:
            bus = dbus.SessionBus()
            obj = bus.get_object(SESSION_MANAGER_SERVICE, SESSION_MANAGER_PATH)
            sessionManager = dbus.Interface(obj, SESSION_MANAGER_SERVICE)
            sessionManager.RequestReboot()
        
    def get_verb(self):
        return _("Restart the computer")
    
class GdmRebootMatch(GdmMatch):
    def __init__(self, **args):
        GdmMatch.__init__(self, name=_("Restart"), icon = "gtk-refresh", **args)
        self.add_action( GdmRebootAction(self.get_name()) )
    
class GdmSwitchUserAction(deskbar.interfaces.Action):
    def __init__(self, name):
        deskbar.interfaces.Action.__init__(self, name)
        
    def activate(self, text=None):
        glib.spawn_async(["gdmflexiserver", "--startnew"], flags=glib.SPAWN_SEARCH_PATH)
        
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
            obj = bus.get_object('org.freedesktop.PowerManagement', '/org/freedesktop/PowerManagement')
            gpm = dbus.Interface (obj, "org.freedesktop.PowerManagement")
            if gpm.CanSuspend():
                self.indexer.add(_("Suspend"), SuspendMatch())
            if gpm.CanHibernate():
                self.indexer.add(_("Hibernate"), HibernateMatch())
            if gpm.CanShutdown():
                self.indexer.add(_("Shutdown"), ShutdownMatch())
            if gpm.CanReboot():
                self.indexer.add(_("Reboot"), RebootMatch())
        except dbus.DBusException:
            return False
            
    def query(self, query):
        matches = self.indexer.look_up(query)
        self.set_priority_for_matches( matches )
        self._emit_query_ready(query, matches )
