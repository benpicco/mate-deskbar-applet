import gtk

class View(object):
    
    def __init__(self, controller, model):
        self._controller = controller
        self._model = model
        gtk.window_set_default_icon_name("deskbar-applet")
        
    def clear_results(self):
        raise NotImplementedError
        
    def clear_actions(self):
        raise NotImplementedError
    
    def clear_query(self):
        raise NotImplementedError
    
    def clear_all(self):
        self.clear_query()
        self.clear_results()
        self.clear_actions()
    
    def show_results(self):
        raise NotImplementedError
    
    def get_toplevel(self):
        raise NotImplementedError
    
    def get_entry(self):
        raise NotImplementedError
    
    def receive_focus(self, time):
        raise NotImplementedError
       
    def display_actions(self, actions, qstring):
        raise NotImplementedError
    
    def mark_history_empty(self, val):
        raise NotImplementedError