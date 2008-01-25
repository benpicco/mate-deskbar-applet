import gobject

class Core(gobject.GObject):
    
    __gsignals__ = {
        "query-ready" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        "loaded" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "initialized" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "keybinding-activated" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_ULONG]),
    }
    
    def __init__(self):
        super(Core, self).__init__()
    
    def _emit_query_ready (self, matches):
        """Idle handler to emit a 'query-ready' signal to the main loop."""
        self.emit ("query-ready", matches)
        return False
    
    def _emit_loaded(self):
        self.emit("loaded")
        return False
    
    def _emit_initialized (self):
        self.emit ("initialized")
        return False
    
    def _emit_keybinding_activated(self, time):
        self.emit("keybinding-activated", time)
        return False
    
    def get_modules_dir(self):
        raise NotImplementedError
    
    def get_modules(self):
        raise NotImplementedError
    
    def get_enabled_modules(self):
        raise NotImplementedError
    
    def set_enabled_modules(self, name):
        raise NotImplementedError
    
    def query(self, text):
        raise NotImplementedError
    
    def get_keybinding(self):
        raise NotImplementedError
    
    def get_min_chars(self):
        raise NotImplementedError
    
    def get_type_delay(self):
        raise NotImplementedError
    
    def get_use_selection(self):
        raise NotImplementedError
    
    def get_clear_entry(self):
        raise NotImplementedError
    
    def get_use_http_proxy(self):
        raise NotImplementedError
    
    def get_proxy_host(self):
        raise NotImplementedError
    
    def get_proxy_port(self):
        raise NotImplementedError
    
    def get_collapsed_cat(self):
        raise NotImplementedError
    
    def get_window_width(self):
        raise NotImplementedError
    
    def get_window_height(self):
        raise NotImplementedError
    
    def get_window_x(self):
        raise NotImplementedError
        
    def get_window_y(self):
        raise NotImplementedError
    
    def get_hide_after_action(self):
        raise NotImplementedError
    
    def get_max_history_items(self):
        raise NotImplementedError
    
    def get_ui_name(self):
        raise NotImplementedError
    
    def set_keybinding(self, binding):
        raise NotImplementedError
    
    def set_min_chars(self, number):
        raise NotImplementedError
    
    def set_type_delay(self, seconds):
        raise NotImplementedError
    
    def set_use_selection(self, val):
        raise NotImplementedError
    
    def set_clear_entry(self, val):
        raise NotImplementedError
    
    def set_use_http_proxy(self, val):
        raise NotImplementedError
    
    def set_proxy_host(self, host):
        raise NotImplementedError
    
    def set_proxy_port(self, port):
        raise NotImplementedError
    
    def set_collapsed_cat(self, cat):
        raise NotImplementedError
    
    def set_window_width(self, width):
        raise NotImplementedError
    
    def set_window_height(self, height):
        raise NotImplementedError
   
    def set_window_x(self, x):
        raise NotImplementedError
        
    def set_window_y(self, y):
        raise NotImplementedError
   
    def set_hide_after_action(self, val):
        raise NotImplementedError
    
    def set_max_history_items(self, amount):
        raise NotImplementedError
    
    def set_ui_name(self, name):
        raise NotImplementedError
    
    def get_history(self):
        """
        Returns History object
        
        This one is able to:
            - append
            - prepend
            - clear
        """
        raise NotImplementedError
     
    def get_module_list(self):
        raise NotImplementedError
    
    def get_disabled_module_list(self):
        raise NotImplementedError
    
    def install_module(self, filename):
        raise NotImplementedError
    
    def uninstall_module(self, mod):
        raise NotImplementedError
    
    def stop_module(self, mod, async=True):
        raise NotImplementedError
    
    def initialize_module (self, module, async=True):
        raise NotImplementedError
    
    def stop_queries(self):
        raise NotImplementedError