import gtk

from deskbar.core.Categories import CATEGORIES
import gettext

class CuemiacCategory :
    """
    A class representing a root node in the cuemiac model/view.
    """
    def __init__ (self, id, parent):
        """
        name: i18n'ed name for the category
        parent: CuemiacTreeStore in which this category belongs
        """
        self.__category_row_ref = None
        self.__parent = parent
        
        try:
            # Prevent xgettext from extracting "name" key
            id_cat_name = CATEGORIES[id]["name"]
            self.__name = gettext.gettext(id_cat_name)
            self.__id = id
        except:
            default_cat_name = CATEGORIES["default"]["name"]
            self.__name = gettext.gettext(default_cat_name)
            self.__id = "default"

            
        self.__priority = 0
        self.__count = 0

    def get_category_row_path (self):
        if self.__category_row_ref is None:
            return None
        return self.__category_row_ref.get_path ()
        
    def set_category_iter (self, iter):
        self.__category_row_ref = gtk.TreeRowReference (self.__parent, self.__parent.get_path(iter))
        
    def get_category_iter (self):
        """Returns a gtk.TreeIter pointing at the category"""
        if self.__category_row_ref is None:
            return None
        return self.__parent.get_iter (self.__category_row_ref.get_path())
            
    def get_name (self):
        return self.__name
        
    def get_id (self):
        """id used to store expansion state"""
        return self.__id
    
    def inc_count (self):
        """increase total number of hits in this category"""
        self.__count = self.__count + 1
    
    def get_count (self):
        """return the total number of hits in this category"""
        return self.__count
        
    def get_priority(self):
        return self.__priority
    
    def set_priority(self, match):
        p = match.get_priority()
        if p > self.__priority:
            self.__priority = p
