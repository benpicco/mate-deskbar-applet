import cgi
from deskbar.core.Utils import load_icon

class Action:
    
    def __init__(self, name):
        self._name = name
    
    def get_escaped_name(self, text=None):
        # Escape the query now for display
        name_dict = {"text" : cgi.escape(text)}
        for key, value in self.get_name(text).items():
            name_dict[key] = cgi.escape(value)
        return name_dict
    
    def get_hash(self):
        return self._name
        
    def get_icon(self):
        return None
    
    def get_pixbuf(self):
        if self.get_icon() != None:
            return load_icon(self.get_icon())
        return None
    
    def activate(self, text=None):
        """
        Tell the match to do the associated action.
        This method should not block.
        The optional text is the additional argument entered in the entry
        """
        raise NotImplementedError
        
    def get_verb(self):
        """
        Returns the action string associated to this handler.
        
        The string must contain one or more "%(name)s" that will
        be replaced by the match get_name().
        
        The %(text)s will be replaced by the typed text.
        By default the %(name)s will be replaced by the self._name
        
        The string can also contain pango markup.
        
        Examples:
         Send mail to %(address)s
         Search <b>%s</b> for %(text)s
         Execute %(prog)s
        """
        raise NotImplementedError
        
    def get_name(self, text=None):
        """
        Returns a dictionary whose entries will be used in the Action
        string returned by get_verb.
        
        The passed string is the complete query string.
        
        The resulting action text will be
        match.get_verb() % match.get_name(query)
        
        Remember to escape pango markup if needed.
        """
        return {"name": self._name}
    
    def is_valid(self):
        """
        Tests wether the match is still valid, by default it's True.
        For example if a file has moved, the file match is invalid
        """
        return True
    
    def skip_history(self):
        """
        Wether the match should appear or not in the history dropdown (and thus be saved as history is saved)
        """
        return False