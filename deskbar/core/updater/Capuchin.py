import gobject
import dbus
import dbus.glib
import logging

LOGGER = logging.getLogger(__name__)

CAPUCHIN_DBUS_SERVICE = "org.gnome.Capuchin"
APP_OBJECT_MANAGER_DBUS_INTERFACE = "org.gnome.Capuchin"
APP_OBJECT_MANAGER_DBUS_PATH = "/org/gnome/Capuchin/AppObjectManager"
APP_OBJECT_DBUS_INTERFACE = "org.gnome.Capuchin.AppObject"

(ACTION_UPDATING_REPO,
ACTION_DOWNLOADING_PLUGIN,
ACTION_EXTRACTING_PLUGIN) = range (3)

def is_capuchin_available():
    try:
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        _dbus = dbus.Interface(proxy, 'org.freedesktop.DBus')
        _dbus.ReloadConfig()
        bus_names = _dbus.ListActivatableNames()
        return (CAPUCHIN_DBUS_SERVICE in bus_names)
    except (dbus.DBusException, dbus.exceptions.DBusException), e:
        LOGGER.error("D-Bus Error")
        LOGGER.exception(e)
        return False

class AppObjectManager:
    
    def __init__(self):
        bus = dbus.SessionBus()
        # Get proxy object
        proxy_obj_manager = bus.get_object(CAPUCHIN_DBUS_SERVICE, APP_OBJECT_MANAGER_DBUS_PATH)
        # Apply the correct interace to the proxy object
        self.manager = dbus.Interface(proxy_obj_manager, APP_OBJECT_MANAGER_DBUS_INTERFACE)
        
    def get_app_object(self, url):
        """
        @return: New L{AppObject} instance for the given URL
        """
        object_path = self.manager.GetAppObject (url)
        return AppObject(object_path)
        
class AppObject (gobject.GObject):
    
    __gsignals__ = {
        "install-finished": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [str]),
        "status": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [int, str, float, int]),
                    }
    
    def __init__(self, object_path):
        gobject.GObject.__init__(self)
        
        bus = dbus.SessionBus()
        proxy_obj = bus.get_object(CAPUCHIN_DBUS_SERVICE, object_path)
        self.appobject = dbus.Interface(proxy_obj, APP_OBJECT_DBUS_INTERFACE)
        
        self.appobject.connect_to_signal('InstallFinished', self.__on_install_finished)
        self.appobject.connect_to_signal('Status', self.__on_status)
        
    def __on_install_finished(self, plugin_id):
        self.emit ("install-finished", plugin_id)
    
    def __on_status(self, action, plugin_id, progress, speed):
        """
        @param action: One of C{ACTION_UPDATING_REPO},
        C{ACTION_DOWNLOADING_PLUGIN}, C{ACTION_EXTRACTING_PLUGIN}
        """
        self.emit ("status", action, plugin_id, progress, speed)
    
    def __on_update_finished(self):
        self.emit ("update-finished")
    
    def __check_plugin_id(self, plugin_id):
        if plugin_id == None:
            raise ValueError ("plugin_id must not be None")
        
    def update (self, force_update):
        """
        @type force_update: bool
        """
        self.appobject.Update (force_update)
    
    def install (self, plugin_id):
        self.__check_plugin_id (plugin_id)
        self.appobject.Install (plugin_id)
    
    def get_application_name (self):
        return self.appobject.GetApplicationName ()
    
    def get_available_plugins (self):
        return self.appobject.GetAvailablePlugins ()
    
    def get_available_updates (self, plugins):
        """
        @type plugins: List of PuginInfo objects
        """
        plugins_list = []
        
        for p in plugins:
            plugins_list.append( (p.get_id(), p.get_version()) )
        
        return self.appobject.GetAvailableUpdates (plugins_list)
    
    def get_plugins_with_tag (self, tag):
        return self.appobject.GetPluginsWithTag (tag)
    
    def get_plugin_name (self, plugin_id):
        self.__check_plugin_id (plugin_id)
        return self.appobject.GetPluginName (plugin_id)
    
    def get_plugin_description (self, plugin_id):
        self.__check_plugin_id (plugin_id)
        return self.appobject.GetPluginDescription (plugin_id)
    
    def get_plugin_changes (self, plugin_id, version):
        self.__check_plugin_id (plugin_id)
        return self.appobject.GetPluginChanges (plugin_id, version)
    
    def get_plugin_tags (self, plugin_id):
        self.__check_plugin_id (plugin_id)
        return self.appobject.GetPluginTags (plugin_id)
    
    def get_plugin_author (self, plugin_id):
        """
        @return: PluginAuthor object
        """
        self.__check_plugin_id (plugin_id)
        author_list = self.appobject.GetPluginAuthor (plugin_id)
        return PluginAuthor (author_list[0], author_list[1])
    
    def get_plugin_version (self, plugin_id):
        self.__check_plugin_id (plugin_id)
        return self.appobject.GetPluginVersion (plugin_id)
    
    def get_tags (self):
        return self.appobject.GetTags ()
    
    def close (self):
        self.appobject.Close ()
        
    def get_plugin_infos (self, plugin_id):
        mod_name = self.get_plugin_name (plugin_id)
        mod_desc = self.get_plugin_description (plugin_id)
        return (mod_name, mod_desc)
    
class PluginInfo:
    
    def __init__(self, plugin_id, version):
        self.__id = plugin_id
        self.__version = version
        
    def get_version(self):
        return self.__version
    
    def get_id(self):
        return self.__id
    
    def set_version(self, val):
        self.__version = val
        
    def set_id(self, val):
        self.__id = val
        
class PluginAuthor:
    
    def __init__(self, name, email):
        self.__name = name
        self.__email = email
        
    def get_name(self):
        return name
    
    def get_email(self):
        return email
    
    def set_name(self, val):
        self.__name = val
        
    def set_email(self, val):
        self.__email = val
        