import gtk
import gtk.gdk
import gobject
import pango
import logging

from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory
from deskbar.ui.cuemiac.CuemiacCellRendererCategory import CuemiacCellRendererCategory
from deskbar.interfaces import Match

LOGGER = logging.getLogger(__name__)
        
class CuemiacTreeView (gtk.TreeView):
    """
    Shows a DeskbarCategoryModel. Sets the background of the root nodes (category headers)
    to gtk.Style().bg[gtk.STATE_NORMAL].
    """
    
    activation_keys = [gtk.keysyms.Return]
    show_actions_keys = [gtk.keysyms.Right]
    
    __gsignals__ = {
        "match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
        "do-default-action" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
        "pressed-up-at-top" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        "pressed-down-at-bottom" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
    }
    
    def __init__ (self, model):
        gtk.TreeView.__init__ (self, model)
        self.set_enable_search (False)
        self.set_property ("headers-visible", False)
        
        self.connect ("key-press-event", self.__on_key_press)
                
        icon = gtk.CellRendererPixbuf ()
        icon.set_property("xpad", 10)
        hit_title = CuemiacCellRendererCategory ()
        hit_title.connect("show-actions-activated", self.__on_show_actions_activated)
        hit_title.connect("do-action-activated", self.__on_do_action_activated)
        hit_title.set_property ("ellipsize", pango.ELLIPSIZE_END)
       
        self._hits_column = gtk.TreeViewColumn ("Hits")
        self._hits_column.pack_start (icon, expand=False)
        self._hits_column.pack_start (hit_title)
        self._hits_column.set_cell_data_func(hit_title, self.__get_match_title_for_cell)            
        self._hits_column.set_cell_data_func(icon, self.__get_match_icon_for_cell)
        self.append_column (self._hits_column)
        
        #self.set_reorderable(True)
        # FIXME: Make it so that categories *only* can be reordered by dragging
        # gtkTreeView does not use normal gtk DnD api.
        # it uses the api from hell

    def is_ready (self):
        """ Returns True if the view is ready for user interaction """
        num_children = self.get_model().iter_n_children (None)
        return self.get_property ("visible") and num_children

    def clear (self):
        self.model.clear ()
    
    def last_visible_path (self):
        """Returns the path to the last visible cell."""
        model = self.get_model ()
        iter = model.get_iter_first ()
        if iter == None:
            return None

        next = model.iter_next (iter)
        
        # Find last category node (they are always visible)
        while next:
            iter = next
            next = model.iter_next (iter)
        
        # If this category is not expanded return
        if not self.row_expanded (model.get_path (iter)):
            return model.get_path (iter)
        
        # Go to last child of category
        num_children = model.iter_n_children (iter)
        iter = model.iter_nth_child (iter, num_children - 1)
        return model.get_path (iter)

    def coord_is_category (self, x, y):
        path_ctx = self.get_path_at_pos(int(x), int(y))
        if path_ctx is None:
            return False
        path, col, x, y = path_ctx
        model = self.get_model()
        match = model[model.get_iter(path)][model.MATCHES]
        if isinstance(match, CuemiacCategory):
            return True
        else:
            return False

    def activate_first_item(self, scroll=True):
        """
        Activate to the first item and scroll to it if C{scroll} is C{True}
        """
        path = self.__find_top_path()
        if path != None:
            if scroll:
                self.__select_path(path)
            self.activate_row( self.get_model().get_iter(path) )

    def activate_row(self, iter):
        """
        Doesn't scroll to the cell. We pretend
        that the row is already selected.
        """
        path = self.get_model().get_path(iter)
        if path != None:
            col = self.get_column(0)
            self.__on_activated(self, path, col)

    def select_first_item(self):
        model = self.get_model()
        path = self.__find_top_path()
        if path != None:
            self.__select_path(path)
        
    def select_last_item(self):
        path = self.__find_bottom_path()
        if path != None:
            self.__select_path(path)

#    def __on_config_expanded_cat (self, value):
#        if value != None and value.type == gconf.VALUE_LIST:
#            self.__collapsed_rows = [h.get_string() for h in value.get_list()]
    
    def __get_match_icon_for_cell (self, column, cell, model, iter, data=None):
    
        match = model[iter][model.MATCHES]

        if isinstance(match, CuemiacCategory):
            cell.set_property ("pixbuf", None)
            cell.set_property ("visible", True)
            cell.set_property ("cell-background-gdk", self.style.bg[gtk.STATE_NORMAL])
        else:
            cell.set_property ("cell-background-gdk", self.style.base[gtk.STATE_NORMAL])
            if isinstance(match, Match):
                cell.set_property ("pixbuf", match.get_icon())
                cell.set_property ("visible", True)
            else:
                LOGGER.error("See bug 359251 or 471672 and report this output: Match object of unexpected type: %r - %r" % (match.__class__, match))
                cell.set_property ("pixbuf", None)
                cell.set_property ("visible", False)
        
    def __get_match_title_for_cell (self, column, cell, model, iter, data=None):
    
        match = model[iter][model.MATCHES]
        
        if isinstance(match, CuemiacCategory):
            # Look up i18n category name
            cell.set_property ("cell-background-gdk", self.style.bg[gtk.STATE_NORMAL])
            cell.set_property ("height", 20)
            cell.set_property ("category-header", match.get_name())
            cell.set_property ("match-count", match.get_count ())
            return
        
        cell.set_property ("category-header", None)
        cell.set_property ("height", -1)
        cell.set_property ("cell-background-gdk", self.style.base[gtk.STATE_NORMAL])
        
        if match == None:
            LOGGER.error("See bug 359251 or 471672 and report this output: Match object of unexpected type: %r - %r" % (match.__class__, match))
            cell.set_property ("has-more-actions", False)
            cell.set_property ("markup", "")
        else:
            cell.set_property ("has-more-actions", len(match.get_actions()) > 1)
            cell.set_property ("markup", model[iter][model.ACTIONS])
        
    def __on_show_actions_activated(self, widget, path):
        col = self.get_model().ACTIONS
        self.__on_activated(self, path, col, None)

    def __on_do_action_activated(self, widget, path):
        model = self.get_model ()
        match = model[model.get_iter(path)][model.MATCHES]
        col = self.get_model().ACTIONS
        if not isinstance(match, CuemiacCategory):
            self.__on_do_default_action(self, path, col, None)
                    
    def __on_do_default_action(self, treeview, path, col, event):
        model = self.get_model()
        iter = model.get_iter (path)
        match = model[iter][model.MATCHES]
        qstring = model[iter][model.QUERY]
        
        # Used by LingeringSelectionWindow
        self.emit("row-activated", path, self._hits_column)
        self.emit("do-default-action", qstring, match, event)

    def __on_activated (self, treeview, path, col, event=None):
        model = self.get_model()
        iter = model.get_iter (path)
        match = model[iter][model.MATCHES]
        qstring = model[iter][model.QUERY]
        
        # Check if this s really a match and not just
        # a category
        if isinstance(match, CuemiacCategory):
            return
        else:
            # So we have a Match, tell the world
            self.emit ("match-selected", qstring, match, event)
        
    def __on_key_press (self, widget, event):
        # FIXME: In the future we should check for ctrl being pressed to create shortcuts
        model, iter = self.get_selection().get_selected()
        if iter is None:
            return False
        match = model[iter][model.MATCHES]
        parent_iter = model.iter_parent(iter)
        
        if event.keyval in self.activation_keys:
            # If this is a category, toggle expansion state
            if isinstance(match, CuemiacCategory):
                path = model.get_path (iter)
                if self.row_expanded (path):
                    self.collapse_row (path)
                else:
                    self.expand_row (path, False)
                return True
            else:
                path = model.get_path(iter)
                col = model.ACTIONS
                self.__on_do_default_action(widget, path, col, event)
        elif event.keyval in self.show_actions_keys:
            if not isinstance(match, CuemiacCategory):
                path = model.get_path(iter)
                col = model.ACTIONS
                self.__on_activated(widget, path, col, event)
        elif (event.keyval == gtk.keysyms.Down):
            if isinstance(match, CuemiacCategory):
                return False
            elif model.get_path(iter) == self.__find_bottom_path():
                # We're at the bottom of the list
                self.emit("pressed-up-at-top")
                return True
            else:
                iter_next = model.iter_next(iter)
                if iter_next == None:
                    # We're at the last item of a category
                    # Select the first item of the next category
                    next_cat = self.__find_next_cat(iter )
                    if next_cat == None:
                        return False
                    else:
                        num = model.get_path(next_cat)[0]
                        self.__select_path( (num, 0) )
                    return True
        elif (event.keyval == gtk.keysyms.Up):
            if isinstance(match, CuemiacCategory):
                return False
            elif model.get_path(iter) == self.__find_top_path():
                # We're at the top of the list 
                self.emit("pressed-down-at-bottom")
                return True
            elif model.get_path(iter)[1] == 0:
                # We're at the first item of a category
                # Select the last item of the previous category
                prev_cat = self.__find_previous_cat( iter )
                if prev_cat == None:
                    return False
                else:
                    num = model.get_path(prev_cat)[0]
                    child = model.iter_n_children(prev_cat)-1
                    self.__select_path( (num, child) )
                    return True
            
        return False
    
    def __find_next_cat(self, iter):
        """
        Find next expanded category
        """
        model = self.get_model()
        next_path = (model.get_path(iter)[0]+1, )
        if next_path[0] >= len(model):
            # All categories are collapsed
            return None
        next_iter = model.get_iter( next_path )
        if self.row_expanded(next_path):
            return next_iter
        else:
            return self.__find_next_cat( next_iter )
    
    def __find_previous_cat(self, iter):
        """
        Find next previous expanded category
        """
        model = self.get_model()
        prev_path = (model.get_path(iter)[0]-1, )
        if prev_path[0] < 0:
            # All categories are collapsed
            return None
        prev_iter = model.get_iter(prev_path)
        if self.row_expanded(prev_path):
            return prev_iter
        else:
            return self.__find_previous_cat( prev_iter )    
    
    def __select_path(self, path):
        self.get_selection().select_path( path )
        gobject.idle_add(self.scroll_to_cell, path )
        self.set_cursor_on_cell( path )
        
    def __select_iter(self, iter):
        self.__select_path( self.get_model().get_path(iter) )
    
    def __find_bottom_path(self):
        """
        Find last item of last expanded category
        """
        model = self.get_model()
        last_cat = len(model)-1
        while (last_cat >= 0) and (not self.row_expanded( (last_cat,) )):
            last_cat -= 1
        if last_cat < 0:
            # All categories are collapsed
            return None
        last_cat_iter =  model.iter_nth_child(None, last_cat)
        last_cat_children = model.iter_n_children(last_cat_iter)-1
        return (last_cat, last_cat_children)
    
    def __find_top_path(self):
        """
        Find first item in first expanded category
        """
        model = self.get_model()
        cat = 0
        while (cat < len(model)) and (not self.row_expanded( (cat,) )):
            cat += 1
        if cat >= len(model):
            # All categories are collapsed
            return None
        return (cat, 0)
