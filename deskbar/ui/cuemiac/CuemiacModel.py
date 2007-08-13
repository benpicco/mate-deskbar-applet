import gtk
import gtk.gdk
import gobject
import deskbar
import deskbar.interfaces.Match
from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory
            
# The sort function ids
SORT_BY_CATEGORY = 1

class CuemiacModel (gtk.TreeStore):
    """
    A tree model to store hits sorted by categories. CuemiacCategory's are root nodes,
    with each child representing a hit.
    Schematically this looks like:
    
    CuemiacCategory->
        -> deskbar.handler.Match
        -> deskbar.handler.Match
        ...
        -> deskbar.handler.Match
    CuemiacCategory->
        ...
    ...
    
    Signal arguments:
        "category-added" : CuemiacCategory, gtk.TreePath
    """
    # Column name
    QUERY, MATCHES, ACTIONS = range(3)
    
    __gsignals__ = {
        "category-added" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
    }
    
    def __init__ (self):
        gtk.TreeStore.__init__ (self, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)
        self.__categories = {}
        self.__match_hashes = {}
        self.append_method = gtk.TreeStore.append # Alternatively gtk.TreeStore.prepend for bottom panel layout
        self.set_sort_func(SORT_BY_CATEGORY, self.__on_sort_categories)
        self.set_sort_order(gtk.SORT_DESCENDING)
    
    def set_sort_order(self, order):
        self.set_sort_column_id(SORT_BY_CATEGORY, order)
    
    def __compare(self, item1, item2):
        if (item1 > item2):
            return 1
        elif (item1 < item2):
            return -1
        else:
            return 0

    def __on_sort_categories(self, treemodel, iter1, iter2):
        match_obj1 = treemodel[iter1][self.MATCHES]
        match_obj2 = treemodel[iter2][self.MATCHES]
        
        if match_obj1 == None or match_obj2 == None:
            return 0
        
        if isinstance(match_obj1, CuemiacCategory):
            return self.__compare( match_obj1.get_priority(), match_obj2.get_priority() )
        
        if match_obj1.get_priority() == match_obj2.get_priority():
            # Sort alphabetically
            a = treemodel[iter1][self.ACTIONS]
            b = treemodel[iter2][self.ACTIONS]
            if a != None and b != None:
                return self.__compare( a.strip().lower(), b.strip().lower() )
        
        return self.__compare( match_obj1.get_priority(), match_obj2.get_priority() )
    
    def __add_to_hash_iter_map(self, hash, iter):
        """
        Maps a hash to the iter pointing to match with given hash
        """
        self.__match_hashes[hash] = iter
    
    def __add_actions_to_match(self, actions, hash):
        """
        Add actions to match with given hash
        """
        match_iter = self.__match_hashes[hash]
        match_obj = self[match_iter][self.MATCHES]
        if self[match_iter][self.ACTIONS] != match_obj.get_name():
            self.set_value(match_iter, self.ACTIONS, match_obj.get_name())
        match_obj.add_all_actions(actions)
    
    def __append_match(self, match_obj, query_string):
        if not self.__match_hashes.has_key(match_obj.get_hash()): 
            iter = self.__append ( query_string, match_obj )
            self.__add_to_hash_iter_map(match_obj.get_hash(), iter)
        else:
            self.__add_actions_to_match(match_obj.get_actions(), match_obj.get_hash())
    
    def append (self, match_obj, query_string):
        """
        Automagically append a match or list of matches 
        to correct category(s), or create a new one(s) if needed.
        """
        #gtk.gdk.threads_enter()
        if isinstance(match_obj, list):
            for hit in match_obj:
                self.__append_match(hit, query_string)
        elif isinstance(match_obj, deskbar.interfaces.Match):
            self.__append_match(match_obj, query_string)
        else:
            raise RuntimeError("Unknown Match type: "+match_obj.__class__.__name__)
        #gtk.gdk.threads_leave()
        
    def __append (self, qstring, match_obj):
        if self.__categories.has_key (match_obj.get_category()):
            iter = self.__append_to_category (qstring, match_obj)
        else:
            iter = self.__create_category_with_match (qstring, match_obj)
        return iter
            
    def __create_category_with_match (self, qstring, match_obj):
        """
        Assumes that the category for the match does not exist.
        """
        #FIXME: Check validity of category name and use  proper i18n
        # Set up a new category
        
        cat = CuemiacCategory (match_obj.get_category(), self)
        cat.set_priority(match_obj)    
        
        iter = self.append_method (self, None, ["", cat, ""])
        cat.set_category_iter (iter)
        self.__categories [match_obj.get_category()] = cat

        # Append the match to the category    
        iter = self.__append_match_to_iter (iter, qstring, match_obj)
        cat.inc_count ()
        self.emit ("category-added", cat, cat.get_category_row_path ())
        
        return iter
    
    def __append_to_category (self, qstring, match_obj):
        cat = self.__categories [match_obj.get_category ()]
        cat.set_priority(match_obj)
        row_iter = None
        
        cat.inc_count ()
        iter = self.__append_match_to_iter (cat.get_category_iter(), qstring, match_obj)
                
        # Update the row count in the view:
        self.row_changed (cat.get_category_row_path(), cat.get_category_iter())
        return iter        

    def __append_match_to_iter (self, iter, qstring, match_obj):
        if len(match_obj.get_actions()) == 1:
            action = match_obj.get_actions()[0]
            label = action.get_verb() % action.get_escaped_name(qstring)
        else:
            label = match_obj.get_name(qstring)
        iter = self.append_method (self, iter, [qstring, match_obj, label])
        return iter
    
    def clear (self):
        """Clears this model of data."""
        gtk.TreeStore.clear (self)
        self.__categories = {}
        self.__match_hashes.clear()
        
    def paths_equal (self, path1, path2):
        """Returns true if the two paths point to the same cell."""
        if path1 == None or path2 == None:
            return False
            
        return ( self.get_string_from_iter (self.get_iter(path1)) == self.get_string_from_iter (self.get_iter(path2)) )

        


if gtk.pygtk_version < (2,8,0):    
    gobject.type_register (CuemiacModel)
