import cgi
from deskbar.core.Utils import load_icon

class Action:
    
    def __init__(self, name):
        """
        @param name: Name of the object
        the action works with
        
        E.g. if the action opens files, name
        should be the filename of the file
        that will be opened
        """
        self._name = name
    
    def get_escaped_name(self, text=None):
        """
        Escape pango markup of all values
        returned by L{get_name} and add
        search term as C{text} key
        
        @return: dict with escaped pango markup
        """
        # Escape the query now for display
        name_dict = {"text" : cgi.escape(text)}
        for key, value in self.get_name(text).items():
            name_dict[key] = cgi.escape(value)
        return name_dict
    
    def get_hash(self):
        """
        Returns a hash that identifies the action
        
        You have to return a hashable object
        (a string is the best choice)
        """
        return self._name
        
    def get_icon(self):
        """
        Returns the name of the icon displayed
        beside the action
        """
        return None
    
    def get_pixbuf(self):
        """
        Returns pixbuf that L{get_icon}
        points to
        
        @return: gtk.gdk.Pixbuf
        """
        if self.get_icon() != None:
            return load_icon(self.get_icon())
        return None
    
    def activate(self, text=None):
        """
        Tell the match to do the associated action.
        
        This method should not block.
        
        @param text: Additional argument entered in the entry
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
            - Send mail to %(address)s
            - Search <b>%s</b> for %(text)s
            - Execute %(prog)s
        """
        raise NotImplementedError

    def get_tooltip(self, text=None):
        """
        Returns the tooltip markup string associated to this action.

        The passed string is the complete query string.
        
        Examples:
            - URI: http://...
            
        @since: 2.24
        """
        return None
        
    def get_name(self, text=None):
        """
        Returns a dictionary whose entries will be used in the Action
        string returned by L{get_verb}
        
        The passed string is the complete query string.
        
        The resulting action text will be
        C{match.get_verb() % match.get_name(query)}
        
        Don't escape pango markup that's what L{get_escaped_name} does
        """
        return {"name": self._name}
    
    def is_valid(self):
        """
        Tests whether the match is still valid, by default it's True.
        
        For example if a file has moved, the file match is invalid
        """
        return True
    
    def skip_history(self):
        """
        Whether the match should appear or not in the history dropdown
        (and thus be saved as history is saved)
        """
        return False