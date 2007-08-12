import gconf
import gobject

class GconfStore(gobject.GObject):

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
    
    GCONF_SHOW_HISTORY = GCONF_DIR + "/show_history"
    
    GCONF_WINDOW_WIDTH = GCONF_DIR + "/window_width"
    GCONF_WINDOW_HEIGHT = GCONF_DIR + "/window_height"
    
    GCONF_RESULTSVIEW_WIDTH = GCONF_DIR + "/resultsview_width"
    
    GCONF_HIDE_AFTER_ACTION = GCONF_DIR + "/hide_after_action"
    
    GCONF_MAX_HISTORY_ITEMS = GCONF_DIR + "/max_history_items"

    __gsignals__ = {
        "keybinding-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "min-chars-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
        "type-delay-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
        "use-selection-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "clear-entry-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "use-http-proxy-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "proxy-host-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "proxy-port-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        "enabled-modules-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        "collapsed-rows-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        "show-history-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "hide-after-action-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN]),
        "max-history-items-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
    }

    __instance = None
        
    @staticmethod
    def get_instance():
        if not GconfStore.__instance:
            GconfStore.__instance = GconfStore()
        return GconfStore.__instance
        
    def __init__(self):
        super(GconfStore, self).__init__()
        self._client = gconf.client_get_default()
        self.__connect_notifications()
        
    def __connect_notifications(self):
        self._client.add_dir(self.GCONF_DIR, gconf.CLIENT_PRELOAD_RECURSIVE)
        self._client.notify_add(self.GCONF_KEYBINDING, lambda x, y, z, a: self.emit("keybinding-changed", z.value.get_string()))
        self._client.notify_add(self.GCONF_MINCHARS, lambda x, y, z, a: self.emit("min-chars-changed", z.value.get_int()))
        self._client.notify_add(self.GCONF_TYPINGDELAY, lambda x, y, z, a: self.emit("type-delay-changed", z.value.get_int()))
        self._client.notify_add(self.GCONF_USE_SELECTION, lambda x, y, z, a: self.emit("use-selection-changed", z.value.get_bool()))
        self._client.notify_add(self.GCONF_CLEAR_ENTRY, lambda x, y, z, a: self.emit("clear-entry-changed", z.value.get_bool()))
        self._client.notify_add(self.GCONF_PROXY_USE_HTTP_PROXY, lambda x, y, z, a: self.emit("use-http-proxy-changed", z.value.get_bool()))
        self._client.notify_add(self.GCONF_PROXY_HOST_KEY, lambda x, y, z, a: self.emit("proxy-host-changed", z.value.get_string()))
        self._client.notify_add(self.GCONF_PROXY_PORT_KEY, lambda x, y, z, a: self.emit("proxy-port-changed", z.value.get_string()))
        self._client.notify_add(self.GCONF_ENABLED_HANDLERS, lambda x, y, z, a: self.emit("enabled-modules-changed", [i.get_string() for i in z.value.get_list()]))
        self._client.notify_add(self.GCONF_COLLAPSED_CAT, lambda x, y, z, a: self.emit("collapsed-rows-changed", [i.get_string() for i in z.value.get_list()]))
        self._client.notify_add(self.GCONF_SHOW_HISTORY, lambda x, y, z, a: self.emit("show-history-changed", z.value.get_bool()))
        self._client.notify_add(self.GCONF_HIDE_AFTER_ACTION, lambda x, y, z, a: self.emit("hide-after-action-changed", z.value.get_bool()))
        self._client.notify_add(self.GCONF_TYPINGDELAY, lambda x, y, z, a: self.emit("max-history-items-changed", z.value.get_int()))
    
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
    
    def get_show_history(self):
        return self._client.get_bool(self.GCONF_SHOW_HISTORY)
    
    def get_window_width(self):
        return self._client.get_int(self.GCONF_WINDOW_WIDTH)
    
    def get_window_height(self):
        return self._client.get_int(self.GCONF_WINDOW_HEIGHT)
    
    def get_resultsview_width(self):
        return self._client.get_int(self.GCONF_RESULTSVIEW_WIDTH)
    
    def get_hide_after_action(self):
        return self._client.get_bool(self.GCONF_HIDE_AFTER_ACTION)
    
    def get_max_history_items(self):
        return self._client.get_int(self.GCONF_MAX_HISTORY_ITEMS)
           
    def set_keybinding(self, binding):
        self._client.set_string(self.GCONF_KEYBINDING, binding)
    
    def set_min_chars(self, number):
        self._client.set_int(self.GCONF_MINCHARS, int(number))
    
    def set_type_delay(self, seconds):
        self._client.set_int(self.GCONF_TYPINGDELAY, int(seconds))
    
    def set_use_selection(self, val):
        self._client.set_bool(self.GCONF_USE_SELECTION, val)
    
    def set_clear_entry(self, val):
        self._client.set_bool(self.GCONF_CLEAR_ENTRY)
    
    def set_use_http_proxy(self, val):
        self._client.set_bool(self.GCONF_PROXY_USE_HTTP_PROXY, val)
    
    def set_proxy_host(self, host):
        self._client.set_string(self.GCONF_PROXY_HOST_KEY, host)
    
    def set_proxy_port(self, port):
        self._client.set_int(self.GCONF_PROXY_HOST_KEY, port)
    
    def set_enabled_modules(self, handlers):
        self._client.set_list(self.GCONF_ENABLED_HANDLERS, gconf.VALUE_STRING,  handlers)
        
    def set_collapsed_cat(self, cat):
        self._client.set_list(self.GCONF_COLLAPSED_CAT, gconf.VALUE_STRING, cat)
        
    def set_show_history(self, val):
        self._client.set_bool(self.GCONF_SHOW_HISTORY, val)
    
    def set_window_width(self, width):
        self._client.set_int(self.GCONF_WINDOW_WIDTH, width)
    
    def set_window_height(self, height):
        self._client.set_int(self.GCONF_WINDOW_HEIGHT, height)  
     
    def set_resultsview_width(self, width):
        self._client.set_int(self.GCONF_RESULTSVIEW_WIDTH, width)
        
    def set_hide_after_action(self, val):
        self._client.set_bool(self.GCONF_HIDE_AFTER_ACTION, val)
        
    def set_max_history_items(self, amount):
        self._client.set_int(self.GCONF_MAX_HISTORY_ITEMS, int(amount))