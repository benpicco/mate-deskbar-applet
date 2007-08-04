import gobject
"""
Each file will require a list of handlers stored in HANDLERS variable
"""
class Module(gobject.GObject):
    
    __gsignals__ = {
        "query-ready" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT]),
    }
    
    INFOS = {'icon': '', 'name': '', 'description': '', 'version': '1.0.0.0', 'categories': {}}
    INSTRUCTIONS = ""
    
    def __init__(self):
        super(Module, self).__init__()
        self._priority = 0
        self._enabled = False
        self._filename = None
        self._id = ""
    
    def _emit_query_ready (self, query, matches):
        """Idle handler to emit a 'query-ready' signal to the main loop."""
        self.emit ("query-ready", query, matches)
        return False
    
    def is_enabled(self):
        return self._enabled
    
    def set_enabled(self, val):
        self._enabled = val
    
    def get_priority(self):
        return self._priority
    
    def set_priority(self, prio):
        self._priority = prio
        
    def get_filename(self):
        return self._filename
    
    def set_filename(self, filename):
        self._filename = filename
        
    def get_id(self):
        return self._id
        
    def set_id(self, mod_id):
        self._id = mod_id
        
    def set_priority_for_matches(self, matches):
        for m in matches:
            m.set_priority( self.get_priority( ))
    
    def query(self, text):
        raise NotImplementedError
    
    def has_config(self):
        return False
    
    def show_config(self, parent):
        pass
    
    def initialize(self):
        """
        The initialize of the Handler should not block. 
        Heavy duty tasks such as indexing should be done in this method, it 
        will be called with a low priority in the mainloop.
        
        Handler.initialize() is guarantied to be called before the handler
        is queried.
        
        If an exception is thrown in this method, the module will be ignored and will
        not receive any query.
        """
        pass
    
    def stop(self):
        """
        If the handler needs any cleaning up before it is unloaded, do it here.
        
        Handler.stop() is guarantied to be called before the handler is 
        unloaded.
        """
        pass
    
    @staticmethod
    def has_requirements():
        return True
    