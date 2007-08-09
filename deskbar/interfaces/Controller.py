class Controller(object):
    
    def __init__(self, model):
        self._model = model
        self._view = None
        
    def register_view(self, view):
        self._view = view
    
    def on_quit(self, sender):
        raise NotImplementedError

    def on_keybinding_activated(self, core, time):
        raise NotImplementedError

    def on_show_about(self, sender):
        raise NotImplementedError
        
    def on_toggle_history(self, sender):
        raise NotImplementedError
        
    def on_show_preferences(self, sender):
        raise NotImplementedError
        
    def on_query_entry_changed(self, entry):
        raise NotImplementedError
    
    def on_query_entry_key_press_event(self, entry, event):
        raise NotImplementedError
    
    def on_query_entry_activate(self, entry):
        raise NotImplementedError
        
    def on_treeview_cursor_changed(self, treeview):
        raise NotImplementedError
        
    def on_match_selected(self, treeview, text, match_obj, event):
        raise NotImplementedError
     
    def on_action_selected(self, treeview, text, action, event):
        raise NotImplementedError
     
    def on_clear_history(self, sender):
        raise NotImplementedError
    
    def on_history_match_selected(self, history, text, match):
        raise NotImplementedError
    
    def on_window_resized(self, window, event):
        raise NotImplementedError
       
    def on_sidebar_width_changed(self, sidebar, value):
        raise NotImplementedError
    
    def on_resultsview_width_changed(self, results_hpaned, value):
        raise NotImplementedError
    
    def update_entry_icon (self, icon=None):
        raise NotImplementedError