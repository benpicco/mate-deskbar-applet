import dbus, dbus.glib
from gettext import gettext as _
import deskbar, deskbar.core.Indexer, deskbar.interfaces.Match, deskbar.interfaces.Module, deskbar.core.Utils
from deskbar.defs import VERSION
import deskbar.handlers.gdmclient
import gobject, gtk, gnome.ui
import deskbar.interfaces.Action

HANDLERS = ["GdmHandler"]

( PROMPT_SHUTDOWN,
  PROMPT_LOGOUT,
  PROMPT_REBOOT,
  PROMPT_SUSPEND,
  PROMPT_HIBERNATE
) = range(5)

TIMEOUT = 60

def logout_prompt(prompt_type):
    global TIMEOUT
    if prompt_type == PROMPT_SHUTDOWN:
        message = _("Shut down of this system now?")
        secondary = _("This system will be automatically shut down in %s seconds.")
        button_label = _("Shut Down")
    elif prompt_type == PROMPT_LOGOUT:
        message = _("Log out of this system now?")
        secondary = _("You will be automatically logged out in %s seconds.")
        button_label = _("Log Out")
    elif prompt_type == PROMPT_REBOOT:
        message = _("Restart this system now?")
        secondary = _("This system will be automatically restarted in %s seconds.")
        button_label = _("Restart")
    elif prompt_type == PROMPT_SUSPEND:
        message = _("Suspend this system now?")
        secondary = _("This system will be automatically suspended in %s seconds.")
        button_label = _("Suspend")
    elif prompt_type == PROMPT_HIBERNATE:
        message = _("Hibernate this system now?")
        secondary = _("This system will be automatically hibernated in %s seconds.")
        button_label = _("Hibernate")
   
    TIMEOUT = 60
    prompt = gtk.MessageDialog(flags=gtk.MESSAGE_QUESTION, message_format=message)
    prompt.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    prompt.add_button(button_label, gtk.RESPONSE_OK)
    prompt.set_default_response(gtk.RESPONSE_OK)

    def countdown_func():
        global TIMEOUT
        if TIMEOUT != 0:
            prompt.format_secondary_text(secondary % TIMEOUT)
            TIMEOUT -= 1
            return True
        else:
            prompt.response(gtk.RESPONSE_OK)
            return False
        
    prompt.format_secondary_text(secondary % TIMEOUT)
    TIMEOUT -= 1
    countdown_thread = gobject.timeout_add(1000, countdown_func)

    response = prompt.run()
    if response == gtk.RESPONSE_CANCEL:
        gobject.source_remove(countdown_thread)
    prompt.destroy()

    return response == gtk.RESPONSE_OK

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
            if logout_prompt(PROMPT_SUSPEND):
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
            if logout_prompt(PROMPT_HIBERNATE):
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
            if logout_prompt(PROMPT_SHUTDOWN):
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
        GpmMatch.__init__(self, icon = "gnome-shutdown")
        self.add_action( ShutdownAction() )
    
class LockScreenMatch(deskbar.interfaces.Match):
    def __init__(self, **args):
        deskbar.interfaces.Match.__init__(self, name=_("Lock"), icon = "system-lock-screen", **args)
        self.add_action( LockScreenAction() )

    def get_category(self):
        return "actions"
    
class GdmAction(deskbar.interfaces.Action):
        
    def __init__(self, name):
        deskbar.interfaces.Action.__init__(self, name)
        self.logout_reentrance = 0
    
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
                
class GdmMatch(deskbar.interfaces.Match):
    def __init__(self, **args):
        deskbar.interfaces.Match.__init__(self, category="actions", **args)
    
class GdmShutdownAction(GdmAction):
    
    def __init__(self, name):
        GdmAction.__init__(self, name)
        
    def activate(self, text=None):
        if logout_prompt(PROMPT_SHUTDOWN):
            deskbar.handlers.gdmclient.set_logout_action(deskbar.handlers.gdmclient.LOGOUT_ACTION_SHUTDOWN)
            self.request_logout()
        
    def get_verb(self):
        return _("Turn off the computer")
            
class GdmShutdownMatch(GdmMatch):
    def __init__(self, **args):
        GdmMatch.__init__(self, name=_("Shut Down"), icon = "gnome-shutdown", **args)
        self.add_action( GdmShutdownAction(self.get_name()) )
    
class GdmLogoutAction(GdmAction):
    def __init__(self, name):
        GdmAction.__init__(self, name)
        
    def activate(self, text=None):
        if logout_prompt(PROMPT_LOGOUT):
            deskbar.handlers.gdmclient.set_logout_action(deskbar.handlers.gdmclient.LOGOUT_ACTION_NONE)
            self.request_logout()
        
    def get_verb(self):
        return _("Log Out")
        
class GdmLogoutMatch(GdmMatch):
    def __init__(self, **args):
        GdmMatch.__init__(self, name=_("Log Out"), icon = "system-log-out", **args)
        self.add_action( GdmLogoutAction(self.get_name()) )
    
class GdmRebootAction(GdmAction):
    def __init__(self, name):
        GdmAction.__init__(self, name)
        
    def activate(self, text=None):
        if logout_prompt(PROMPT_REBOOT):
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
