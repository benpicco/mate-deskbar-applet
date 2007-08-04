import gtk

class View(object):
    
    def __init__(self, controller, model):
        self._controller = controller
        self._model = model
        gtk.window_set_default_icon_name("deskbar-applet")
        
    def clear_results(self):
        raise NotImplemented
    
    def clear_query(self):
        raise NotImplemented
    
    def clear_all(self):
        self.clear_query()
        self.clear_results()
    
    def get_toplevel(self):
        raise NotImplemented
    
    def get_entry(self):
        raise NotImplemented
    
    def show_history(self, value):
        raise NotImplementedError
    
    def is_history_visible(self):
        raise NotImplementedError
    
    def receive_focus(self, time):
        raise NotImplementedError
       
    def display_actions(self, actions, qstring):
        raise NotImplementedError