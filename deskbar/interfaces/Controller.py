class Controller(object):
    
    def __init__(self, model):
        self._model = model
        self._view = None
        
    def register_view(self, view):
        self._view = view
    
    def on_quit(self, *args):
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
    
    def on_do_default_action(self, treeview, text, match_obj, event):
        raise NotImplementedError
     
    def on_action_selected(self, treeview, text, action, event):
        raise NotImplementedError
     
    def on_clear_history(self, sender):
        raise NotImplementedError
    
    def on_history_match_selected(self, history, text, match):
        raise NotImplementedError