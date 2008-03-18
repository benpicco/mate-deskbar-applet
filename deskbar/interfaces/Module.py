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
        self._updateable = False
        self._filename = None
        self._id = ""
    
    def _emit_query_ready (self, query, matches):
        """Idle handler to emit a 'query-ready' signal to the main loop."""
        self.emit ("query-ready", query, matches)
        return False
    
    def is_enabled(self):
        """
        Whether the module is enabled
        """
        return self._enabled
    
    def set_enabled(self, val):
        """
        Set handler's enabled state
        """
        self._enabled = val
        
    def is_updateable(self):
        """
        Whether a update for the plugin is available
        """
        return self._updateable
    
    def set_updateable(self, val):
        self._updateable = val
    
    def get_priority(self):
        """
        Get module's priority
        """
        return self._priority
    
    def set_priority(self, prio):
        """
        Set module's priority
        """
        self._priority = prio
        
    def get_filename(self):
        """
        Get the filename of the module
        """
        return self._filename
    
    def set_filename(self, filename):
        """
        Set the filename of the module
        """
        self._filename = filename
        
    def get_id(self):
        """
        Get module's id
        
        Usually, this is the filename
        """
        return self._id
        
    def set_id(self, mod_id):
        """
        Set module's id
        """
        self._id = mod_id
        
    def set_priority_for_matches(self, matches):
        """
        Set the module's priotity for each match
        
        @type matches: list of L{deskbar.interfaces.Match} 
        """
        for m in matches:
            m.set_priority( self.get_priority( ))
    
    def query(self, text):
        """
        Perform the query
        
        @param text: search term 
        """
        raise NotImplementedError
    
    def has_config(self):
        """
        Whether the module has a config dialog
        """
        return False
    
    def show_config(self, parent):
        """
        Should contain code to display configuration dialog
        """
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
        """
        Whether all requirements are met to use this module
        """
        return True
    