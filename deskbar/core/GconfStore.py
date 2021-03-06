import mateconf
import gobject

class GconfStore(gobject.GObject):
    """
    Handles storing to and retrieving values from MateConf 
    """

    # MateConf directory for deskbar in window mode and shared settings
    MATECONF_DIR = "/apps/deskbar"
    
    # MateConf key to the setting for the minimum number of chars of a query
    MATECONF_MINCHARS = MATECONF_DIR + "/minchars"
    # MateConf key to the setting for time between keystroke in search entry, and actual search
    MATECONF_TYPINGDELAY = MATECONF_DIR + "/typingdelay"
    # MateConf key to the setting whether to use selection clipboard when activating hotkey
    MATECONF_USE_SELECTION = MATECONF_DIR + "/use_selection"
    # MateConf key for global keybinding
    MATECONF_KEYBINDING = MATECONF_DIR + "/keybinding"
    # MateConf key clear the entry after a search result has been selected
    MATECONF_CLEAR_ENTRY = MATECONF_DIR + "/clear_entry"
    
    MATECONF_PROXY_USE_HTTP_PROXY = '/system/http_proxy/use_http_proxy'
    MATECONF_PROXY_HOST_KEY = '/system/http_proxy/host'
    MATECONF_PROXY_PORT_KEY = '/system/http_proxy/port'
    
    # MateConf key for list of enabled handlers, when uninstalled, use a debug key to not conflict
    # with development version
    MATECONF_ENABLED_HANDLERS = MATECONF_DIR + "/enabled_handlers"

    # MateConf key for collapsed categories in the cuemiac view
    MATECONF_COLLAPSED_CAT = MATECONF_DIR + "/collapsed_cat"
    
    MATECONF_WINDOW_WIDTH = MATECONF_DIR + "/window_width"
    MATECONF_WINDOW_HEIGHT = MATECONF_DIR + "/window_height"
    
    MATECONF_WINDOW_X = MATECONF_DIR + "/window_x"      
    MATECONF_WINDOW_Y = MATECONF_DIR + "/window_y"
    
    MATECONF_HIDE_AFTER_ACTION = MATECONF_DIR + "/hide_after_action"
    
    MATECONF_MAX_HISTORY_ITEMS = MATECONF_DIR + "/max_history_items"
    
    MATECONF_UI_NAME = MATECONF_DIR + "/ui_name" 
    
    MATECONF_ENTRY_WIDTH = MATECONF_DIR + "/entry_width"

    MATECONF_DEFAULT_BROWSER = "/desktop/mate/url-handlers/http/command"
    
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
        self._client = mateconf.client_get_default()
        self.__connect_notifications()
        
    def __connect_notifications(self):
        self._client.add_dir(self.MATECONF_DIR, mateconf.CLIENT_PRELOAD_RECURSIVE)
        self._client.notify_add(self.MATECONF_KEYBINDING, self.__emit_signal_string, "keybinding-changed")
        self._client.notify_add(self.MATECONF_MINCHARS, self.__emit_signal_int, "min-chars-changed")
        self._client.notify_add(self.MATECONF_TYPINGDELAY, self.__emit_signal_int, "type-delay-changed")
        self._client.notify_add(self.MATECONF_USE_SELECTION, self.__emit_signal_bool, "use-selection-changed")
        self._client.notify_add(self.MATECONF_CLEAR_ENTRY, self.__emit_signal_bool, "clear-entry-changed")
        self._client.notify_add(self.MATECONF_PROXY_USE_HTTP_PROXY, self.__emit_signal_bool, "use-http-proxy-changed")
        self._client.notify_add(self.MATECONF_PROXY_HOST_KEY, self.__emit_signal_string, "proxy-host-changed")
        self._client.notify_add(self.MATECONF_PROXY_PORT_KEY, self.__emit_signal_int, "proxy-port-changed")
        self._client.notify_add(self.MATECONF_ENABLED_HANDLERS, self.__emit_signal_string_list, "enabled-modules-changed")
        self._client.notify_add(self.MATECONF_COLLAPSED_CAT, self.__emit_signal_string_list, "collapsed-rows-changed")
        self._client.notify_add(self.MATECONF_HIDE_AFTER_ACTION, self.__emit_signal_bool, "hide-after-action-changed")
        self._client.notify_add(self.MATECONF_TYPINGDELAY, self.__emit_signal_int, "max-history-items-changed")
        self._client.notify_add(self.MATECONF_DEFAULT_BROWSER, self.__emit_signal_string, "default-browser-changed")
        self._client.notify_add(self.MATECONF_UI_NAME, self.__emit_signal_string, "ui-name-changed")
        self._client.notify_add(self.MATECONF_ENTRY_WIDTH, self.__emit_signal_int, "entry-width-changed")
        
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
        return self._client.get_string(self.MATECONF_KEYBINDING)
    
    def get_min_chars(self):
        minchars = self._client.get_int(self.MATECONF_MINCHARS)
        if minchars == None:
            minchars = 1
        return minchars
    
    def get_type_delay(self):
        delay = self._client.get_int(self.MATECONF_TYPINGDELAY)
        if delay == None:
            delay = 250
        return delay
    
    def get_use_selection(self):
        select = self._client.get_bool(self.MATECONF_USE_SELECTION)
        if select == None:
            select = True
        return select
    
    def get_clear_entry(self):
        clear = self._client.get_bool(self.MATECONF_CLEAR_ENTRY)
        if clear == None:
            clear = False
        return clear
    
    def get_use_http_proxy(self):
        proxy = self._client.get_bool(self.MATECONF_PROXY_USE_HTTP_PROXY)
        if proxy == None:
            proxy = False
        return proxy
    
    def get_proxy_host(self):
        return self._client.get_string(self.MATECONF_PROXY_HOST_KEY)
    
    def get_proxy_port(self):
        return self._client.get_int(self.MATECONF_PROXY_PORT_KEY)
    
    def get_enabled_modules(self):
        return self._client.get_list(self.MATECONF_ENABLED_HANDLERS, mateconf.VALUE_STRING)
    
    def get_collapsed_cat(self):
        return self._client.get_list(self.MATECONF_COLLAPSED_CAT, mateconf.VALUE_STRING)
    
    def get_window_width(self):
        return self._client.get_int(self.MATECONF_WINDOW_WIDTH)
    
    def get_window_height(self):
        return self._client.get_int(self.MATECONF_WINDOW_HEIGHT)
    
    def get_window_x(self):      
        return self._client.get_int(self.MATECONF_WINDOW_X)      
           
    def get_window_y(self):      
        return self._client.get_int(self.MATECONF_WINDOW_Y)
    
    def get_hide_after_action(self):
        return self._client.get_bool(self.MATECONF_HIDE_AFTER_ACTION)
    
    def get_max_history_items(self):
        return self._client.get_int(self.MATECONF_MAX_HISTORY_ITEMS)
           
    def get_default_browser(self):      
        return self._client.get_string(self.MATECONF_DEFAULT_BROWSER)
        
    def get_ui_name(self):
        return self._client.get_string(self.MATECONF_UI_NAME)
    
    def get_entry_width(self):
        return self._client.get_int(self.MATECONF_ENTRY_WIDTH)

    def set_keybinding(self, binding):
        return self.__set_string_if_writeable(self.MATECONF_KEYBINDING, binding)
    
    def set_min_chars(self, number):
        return self.__set_int_if_writeable(self.MATECONF_MINCHARS, int(number))
    
    def set_type_delay(self, seconds):
        return self.__set_int_if_writeable(self.MATECONF_TYPINGDELAY, int(seconds))
    
    def set_use_selection(self, val):
        return self.__set_bool_if_writeable(self.MATECONF_USE_SELECTION, val)
    
    def set_clear_entry(self, val):
        return self.__set_bool_if_writeable(self.MATECONF_CLEAR_ENTRY)
    
    def set_use_http_proxy(self, val):
        return self.__set_bool_if_writeable(self.MATECONF_PROXY_USE_HTTP_PROXY, val)
    
    def set_proxy_host(self, host):
        return self.__set_string_if_writeable(self.MATECONF_PROXY_HOST_KEY, host)
    
    def set_proxy_port(self, port):
        return self.__set_int_if_writeable(self.MATECONF_PROXY_HOST_KEY, port)
    
    def set_enabled_modules(self, handlers):
        return self.__set_list_if_writeable(self.MATECONF_ENABLED_HANDLERS, mateconf.VALUE_STRING,  handlers)
        
    def set_collapsed_cat(self, cat):
        return self.__set_list_if_writeable(self.MATECONF_COLLAPSED_CAT, mateconf.VALUE_STRING, cat)
     
    def set_window_width(self, width):
        return self.__set_int_if_writeable(self.MATECONF_WINDOW_WIDTH, width)
    
    def set_window_height(self, height):
        return self.__set_int_if_writeable(self.MATECONF_WINDOW_HEIGHT, height)  
    
    def set_window_x(self, x):      
        return self.__set_int_if_writeable(self.MATECONF_WINDOW_X, x)      
           
    def set_window_y(self, y):      
        return self.__set_int_if_writeable(self.MATECONF_WINDOW_Y, y)
        
    def set_hide_after_action(self, val):
        return self.__set_bool_if_writeable(self.MATECONF_HIDE_AFTER_ACTION, val)
        
    def set_max_history_items(self, amount):
        return self.__set_int_if_writeable(self.MATECONF_MAX_HISTORY_ITEMS, int(amount))
        
    def set_ui_name(self, name):
        return self.__set_string_if_writeable(self.MATECONF_UI_NAME, name)

    def set_entry_width(self, width):
        return self.__set_int_if_writeable(self.MATECONF_ENTRY_WIDTH, int(width))

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
