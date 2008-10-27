import gconf
import gobject

class GconfStore(gobject.GObject):
    """
    Handles storing to and retrieving values from GConf 
    """

    # GConf directory for deskbar in window mode and shared settings
    GCONF_DIR = "/apps/deskbar"
    
    # GConf key to the setting for the minimum number of chars of a query
    GCONF_MINCHARS = GCONF_DIR + "/minchars"
    # GConf key to the setting for time between keystroke in search entry, and actual search
    GCONF_TYPINGDELAY = GCONF_DIR + "/typingdelay"
    # GConf key to the setting whether to use selection clipboard when activating hotkey
    GCONF_USE_SELECTION = GCONF_DIR + "/use_selection"
    # GConf key for global keybinding
    GCONF_KEYBINDING = GCONF_DIR + "/keybinding"
    # GConf key clear the entry after a search result has been selected
    GCONF_CLEAR_ENTRY = GCONF_DIR + "/clear_entry"
    
    GCONF_PROXY_USE_HTTP_PROXY = '/system/http_proxy/use_http_proxy'
    GCONF_PROXY_HOST_KEY = '/system/http_proxy/host'
    GCONF_PROXY_PORT_KEY = '/system/http_proxy/port'
    
    # GConf key for list of enabled handlers, when uninstalled, use a debug key to not conflict
    # with development version
    GCONF_ENABLED_HANDLERS = GCONF_DIR + "/enabled_handlers"

    # GConf key for collapsed categories in the cuemiac view
    GCONF_COLLAPSED_CAT = GCONF_DIR + "/collapsed_cat"
    
    GCONF_WINDOW_WIDTH = GCONF_DIR + "/window_width"
    GCONF_WINDOW_HEIGHT = GCONF_DIR + "/window_height"
    
    GCONF_WINDOW_X = GCONF_DIR + "/window_x"      
    GCONF_WINDOW_Y = GCONF_DIR + "/window_y"
    
    GCONF_HIDE_AFTER_ACTION = GCONF_DIR + "/hide_after_action"
    
    GCONF_MAX_HISTORY_ITEMS = GCONF_DIR + "/max_history_items"
    
    GCONF_UI_NAME = GCONF_DIR + "/ui_name" 
    
    GCONF_ENTRY_WIDTH = GCONF_DIR + "/entry_width"

    GCONF_DEFAULT_BROWSER = "/desktop/gnome/url-handlers/http/command"
    
    __gsignals__ = {
        "keybinding-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "min-chars-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
        "type-delay-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
        "use-selection-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "clear-entry-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "use-http-proxy-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "proxy-host-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "proxy-port-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
        "enabled-modules-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        "collapsed-rows-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        "hide-after-action-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "max-history-items-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
        "default-browser-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "ui-name-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "entry-width-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
    }

    __instance = None
        
    @staticmethod
    def get_instance():
        if not GconfStore.__instance:
            GconfStore.__instance = GconfStore()
        return GconfStore.__instance
        
    def __init__(self):
        """
        *Do not* use the constructor directly. Always use L{get_instance}
        """
        super(GconfStore, self).__init__()
        self._client = gconf.client_get_default()
        self.__connect_notifications()
        
    def __connect_notifications(self):
        self._client.add_dir(self.GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)
        self._client.notify_add(self.GCONF_KEYBINDING, self.__emit_signal_string, "keybinding-changed")
        self._client.notify_add(self.GCONF_MINCHARS, self.__emit_signal_int, "min-chars-changed")
        self._client.notify_add(self.GCONF_TYPINGDELAY, self.__emit_signal_int, "type-delay-changed")
        self._client.notify_add(self.GCONF_USE_SELECTION, self.__emit_signal_bool, "use-selection-changed")
        self._client.notify_add(self.GCONF_CLEAR_ENTRY, self.__emit_signal_bool, "clear-entry-changed")
        self._client.notify_add(self.GCONF_PROXY_USE_HTTP_PROXY, self.__emit_signal_bool, "use-http-proxy-changed")
        self._client.notify_add(self.GCONF_PROXY_HOST_KEY, self.__emit_signal_string, "proxy-host-changed")
        self._client.notify_add(self.GCONF_PROXY_PORT_KEY, self.__emit_signal_int, "proxy-port-changed")
        self._client.notify_add(self.GCONF_ENABLED_HANDLERS, self.__emit_signal_string_list, "enabled-modules-changed")
        self._client.notify_add(self.GCONF_COLLAPSED_CAT, self.__emit_signal_string_list, "collapsed-rows-changed")
        self._client.notify_add(self.GCONF_HIDE_AFTER_ACTION, self.__emit_signal_bool, "hide-after-action-changed")
        self._client.notify_add(self.GCONF_TYPINGDELAY, self.__emit_signal_int, "max-history-items-changed")
        self._client.notify_add(self.GCONF_DEFAULT_BROWSER, self.__emit_signal_string, "default-browser-changed")
        self._client.notify_add(self.GCONF_UI_NAME, self.__emit_signal_string, "ui-name-changed")
        self._client.notify_add(self.GCONF_ENTRY_WIDTH, self.__emit_signal_int, "entry-width-changed")
        
    def __emit_signal_string(self, client, cnxn_id, entry, data):
        if entry.value != None:
            self.emit(data, entry.value.get_string())
    
    def __emit_signal_string_list(self, client, cnxn_id, entry, data):
        if entry.value != None:
            vals = []
            for i in entry.value.get_list():
                if i != None:
                    vals.append(i.get_string())
            self.emit(data, vals)
    
    def __emit_signal_bool(self, client, cnxn_id, entry, data):
        if entry.value != None:
            self.emit(data, entry.value.get_bool())
    
    def __emit_signal_int(self, client, cnxn_id, entry, data):
        if entry.value != None:
            self.emit(data, entry.value.get_int())
    
    def get_client(self):
        return self._client
    
    def get_keybinding(self):
        return self._client.get_string(self.GCONF_KEYBINDING)
    
    def get_min_chars(self):
        minchars = self._client.get_int(self.GCONF_MINCHARS)
        if minchars == None:
            minchars = 1
        return minchars
    
    def get_type_delay(self):
        delay = self._client.get_int(self.GCONF_TYPINGDELAY)
        if delay == None:
            delay = 250
        return delay
    
    def get_use_selection(self):
        select = self._client.get_bool(self.GCONF_USE_SELECTION)
        if select == None:
            select = True
        return select
    
    def get_clear_entry(self):
        clear = self._client.get_bool(self.GCONF_CLEAR_ENTRY)
        if clear == None:
            clear = False
        return clear
    
    def get_use_http_proxy(self):
        proxy = self._client.get_bool(self.GCONF_PROXY_USE_HTTP_PROXY)
        if proxy == None:
            proxy = False
        return proxy
    
    def get_proxy_host(self):
        return self._client.get_string(self.GCONF_PROXY_HOST_KEY)
    
    def get_proxy_port(self):
        return self._client.get_int(self.GCONF_PROXY_PORT_KEY)
    
    def get_enabled_modules(self):
        return self._client.get_list(self.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING)
    
    def get_collapsed_cat(self):
        return self._client.get_list(self.GCONF_COLLAPSED_CAT, gconf.VALUE_STRING)
    
    def get_window_width(self):
        return self._client.get_int(self.GCONF_WINDOW_WIDTH)
    
    def get_window_height(self):
        return self._client.get_int(self.GCONF_WINDOW_HEIGHT)
    
    def get_window_x(self):      
        return self._client.get_int(self.GCONF_WINDOW_X)      
           
    def get_window_y(self):      
        return self._client.get_int(self.GCONF_WINDOW_Y)
    
    def get_hide_after_action(self):
        return self._client.get_bool(self.GCONF_HIDE_AFTER_ACTION)
    
    def get_max_history_items(self):
        return self._client.get_int(self.GCONF_MAX_HISTORY_ITEMS)
           
    def get_default_browser(self):      
        return self._client.get_string(self.GCONF_DEFAULT_BROWSER)
        
    def get_ui_name(self):
        return self._client.get_string(self.GCONF_UI_NAME)
    
    def get_entry_width(self):
        return self._client.get_int(self.GCONF_ENTRY_WIDTH)

    def set_keybinding(self, binding):
        return self.__set_string_if_writeable(self.GCONF_KEYBINDING, binding)
    
    def set_min_chars(self, number):
        return self.__set_int_if_writeable(self.GCONF_MINCHARS, int(number))
    
    def set_type_delay(self, seconds):
        return self.__set_int_if_writeable(self.GCONF_TYPINGDELAY, int(seconds))
    
    def set_use_selection(self, val):
        return self.__set_bool_if_writeable(self.GCONF_USE_SELECTION, val)
    
    def set_clear_entry(self, val):
        return self.__set_bool_if_writeable(self.GCONF_CLEAR_ENTRY)
    
    def set_use_http_proxy(self, val):
        return self.__set_bool_if_writeable(self.GCONF_PROXY_USE_HTTP_PROXY, val)
    
    def set_proxy_host(self, host):
        return self.__set_string_if_writeable(self.GCONF_PROXY_HOST_KEY, host)
    
    def set_proxy_port(self, port):
        return self.__set_int_if_writeable(self.GCONF_PROXY_HOST_KEY, port)
    
    def set_enabled_modules(self, handlers):
        return self.__set_list_if_writeable(self.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING,  handlers)
        
    def set_collapsed_cat(self, cat):
        return self.__set_list_if_writeable(self.GCONF_COLLAPSED_CAT, gconf.VALUE_STRING, cat)
     
    def set_window_width(self, width):
        return self.__set_int_if_writeable(self.GCONF_WINDOW_WIDTH, width)
    
    def set_window_height(self, height):
        return self.__set_int_if_writeable(self.GCONF_WINDOW_HEIGHT, height)  
    
    def set_window_x(self, x):      
        return self.__set_int_if_writeable(self.GCONF_WINDOW_X, x)      
           
    def set_window_y(self, y):      
        return self.__set_int_if_writeable(self.GCONF_WINDOW_Y, y)
        
    def set_hide_after_action(self, val):
        return self.__set_bool_if_writeable(self.GCONF_HIDE_AFTER_ACTION, val)
        
    def set_max_history_items(self, amount):
        return self.__set_int_if_writeable(self.GCONF_MAX_HISTORY_ITEMS, int(amount))
        
    def set_ui_name(self, name):
        return self.__set_string_if_writeable(self.GCONF_UI_NAME, name)

    def set_entry_width(self, width):
        return self.__set_int_if_writeable(self.GCONF_ENTRY_WIDTH, int(width))

    def __set_string_if_writeable(self, key, val):
        if self._client.key_is_writable(key):
            return self._client.set_string(key, val)
        return False

    def __set_int_if_writeable(self, key, val):
        if self._client.key_is_writable(key):
            return self._client.set_int(key, val)
        return False

    def __set_bool_if_writeable(self, key, val):
        if self._client.key_is_writable(key):
            return self._client.set_bool(key, val)
        return False

    def __set_list_if_writeable(self, key, value_type, val):
        if self._client.key_is_writable(key):
            return self._client.set_list(key, value_type, val)
        return False
