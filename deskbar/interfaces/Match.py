from deskbar.core.Categories import CATEGORIES 
import deskbar.core.Utils
import deskbar.interfaces.Action
import gtk.gdk
import logging

LOGGER = logging.getLogger(__name__)

"""
Represents a match returned by handlers
"""

class Match:
    def __init__(self, **args):
        """
        You can pass the named parameter "icon" as a string being an
        absolute path or name of an icon.
        
        Available keyword arguments:
            - name: The query string. This value is mandatory.
            - icon: The name or path of an icon. It's very important
            that you don't try to store something else in it.
            If you don't set a icon a default icon according to the
            match's category is displayed.
            - pixbuf: If you fetch the match's icon on the fly you can
            provide a pixbuf as well and it overrides the value of icon.
            - category: The category the match belongs to.
            - priority: Match's priority. It's recommended that you use your
            module's L{set_priority_for_matches<deskbar.interfaces.Module.Module.set_priority_for_matches>}
            method to assign your matches the priority of your module.
            - snippet: A snippet where the search term appears.
            The snippet will be displayed under the return value of L{deskbar.interfaces.Match.get_verb}
            using the Pango markup size='small' and style='italic'. The snippet can contain Pango markup
            itsself.
        """
        self._name = ""
        self._icon = None
        self._pixbuf = None
        self._category = "default"
        self._priority = 0
        self._actions = []
        self._default_action = None
        self._snippet = None
        self.__actions_hashes = set()
        if "name" in args:
            self._name = args["name"]
        if "icon" in args and args["icon"] != None:
            self.set_icon(args["icon"])
        if "pixbuf" in args and args["pixbuf"] != None:
            if not isinstance(args["pixbuf"], gtk.gdk.Pixbuf):
                raise TypeError, "pixbuf must be a gtk.gdk.Pixbuf"
            self._pixbuf = args["pixbuf"]
        if "category" in args:
            self._category = args["category"]
        if "priority" in args:
            self._priority = args["priority"]
        if "snippet" in args:
            self._snippet = args["snippet"]
                
    def _get_default_icon(self):
        """
        Retrieve pixbuf depending on category
        
        @return: gtk.gdk.Pixbuf
        """
        if CATEGORIES[self.get_category()].has_key("icon"):
            return CATEGORIES[self.get_category()]["icon"]
        else:
            return CATEGORIES["default"]["icon"]
    
    def get_priority(self):
        """
        Get priority of the match
        """
        return self._priority
    
    def set_priority(self, prio):
        """
        Set priority of the match
        
        @type prio: int 
        """
        self._priority = prio
        
    def get_icon(self):
        """
        Returns a pixbuf hat represents this match.
        Returns None if there is no associated icon.
        
        @return: gtk.gdk.Pixbuf
        """
        if self._pixbuf != None:
            # Only for Matches that won't be stored in history
            return self._pixbuf
        elif self._icon != None:
            return deskbar.core.Utils.load_icon(self._icon)
        else:
            return self._get_default_icon()
    
    def set_icon(self, iconname):
        """
        Set the name if the icon
        
        @type iconname: string 
        """
        if not isinstance(iconname, str):
            raise TypeError, "icon must be a string"
        self._icon = iconname
        
    def get_snippet(self):
        """
        Get the snippet where the search term appears
        """
        return self._snippet
        
    def set_snippet(self, snippet):
        """
        Set the snippet where the search term appears
        
        @type snippet: string
        """
        self._snippet = snippet
    
    def get_category(self):
        """
        Returns a string corresponding to a key in the Categories.py file,
        indicating in which category this match should be put in.
        
        Returning None, uses the default category
        
        @return: str
        """
        return self._category
    
    def set_category(self, cat):
        """
        Set category
        
        @type cat: A key from Categories.py
        """
        self._category = cat
        
    def get_actions(self):
        """
        Get category
        """
        return self._actions
    
    def get_default_action(self):
        """
        Get default action
        """
        return self._default_action
    
    def add_action(self, action, is_default=False):
        """
        Add action to match
        
        @type action: L{deskbar.interfaces.action}
        @param is_default: Whether the action should be
        the default action. Will override previously set
        default action.
        @type is_default: bool
        @return: Returns False if the action hasn't been added,
        beacause it's not valid  
        """
        if not isinstance(action, deskbar.interfaces.Action):
            raise TypeError("Expected deskbar.interfaces.Action but got %r" % action)
        
        if not action.is_valid():
            LOGGER.warning("Action %r is not valid, not adding it" % action)
            return False
        
        if not action.get_hash() in self.__actions_hashes:
            self.__actions_hashes.add(action.get_hash())
            self._actions.append(action)
        if is_default:
            self._default_action = action
        return True
    
    def add_all_actions(self, actions):
        """
        Add all actions
        
        @type actions: list of L{deskbar.interfaces.action}
        """
        for action in actions:
            self.add_action(action)

    def remove_action(self, action):
        """
        Remove action from match

        @type action: L{deskbar.interfaces.Action}
        """
        if action.get_hash() in self.__actions_hashes:
            self.__actions_hashes.remove(action.get_hash())
            self._actions.remove(action)
        if self._default_action == action:
            if len(self._actions):
                self._default_action = self._default_action[0]
            else:
                self._default_action = None

    def get_hash(self):
        """
        Returns a hash used to verify if a query has one or more duplicates.
        Matches that have same hash will be selected based on the handler priority.
        text is the entered query string.
        
        By default, if the handler does not override this, it will return the
        id of the class.
        """
        return id(self)
    
    def get_name(self, text=None):
        """
        Returns the name of the item the match represents
        
        By default this is the C{name} parameter you supplied
        when creating the class
        """
        return self._name
    
