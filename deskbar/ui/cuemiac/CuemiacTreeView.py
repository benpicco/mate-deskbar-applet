import gtk
import gtk.gdk
import gobject
import pango
import logging

from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory
from deskbar.interfaces import Match

class CellRendererCuemiacCategory (gtk.CellRendererText):
    """
    Special cell renderer for the CuemiacTreeView.
    If the cell to be rendered is a normal Match, it falls back to the normal
    gtk.CellRendererText render method.
    If the cell is a CuemiacCategory it takes the icon column of the view into
    consideration and correctly left justifies the category title.
    
    This renderer also creates a small space between category headers. This is
    to ensure that they don't appear as one solid block when collapsed.
    """
    __gproperties__ = {
                'category-header' : (gobject.TYPE_STRING, 'markup for category title string',
                      'markup for category title string, None if this is not a category header',
                      None, gobject.PARAM_READWRITE),
                      
                 'match-count' : (gobject.TYPE_INT, 'number of hits in the category',
                      'the number of hits for the CuemiacCategory to be rendered',
                      0,1000,0, gobject.PARAM_READWRITE),
                 'has-more-actions' : (gobject.TYPE_BOOLEAN, 'whether the match has more than one action',
                                    'If set to True a symbol will be displayed on the right',
                                    False, gobject.PARAM_READWRITE),
                 'match-markup' : (gobject.TYPE_STRING, 'markup for match description',
                      'markup for match description',
                      "", gobject.PARAM_READWRITE),
        }
    
    def __init__ (self):
        gtk.CellRendererText.__init__ (self)
        self.__category_header = None
        self.__match_count = 0
        self.__has_more_actions = False
        self.__match_markup = ""
        
        # Grab some default theme settings
        # they are probably incorrect, but we reset
        # them on each render anyway.
        style = gtk.Style ()
        self.header_font_desc = style.font_desc
        self.header_font_desc.set_weight (pango.WEIGHT_BOLD)
        self.header_font_desc.set_size (self.header_font_desc.get_size () - pango.SCALE *2)
        self.header_bg = style.base [gtk.STATE_NORMAL]
    
    def set_style (self, widget):
        """
        Apply the style from widget, to this cellrenderer
        """
        self.header_font_desc = widget.style.font_desc
        self.header_font_desc.set_weight (pango.WEIGHT_BOLD)
        self.header_font_desc.set_size (self.header_font_desc.get_size () - pango.SCALE *2)
        self.header_bg = widget.style.base [gtk.STATE_NORMAL]
    
    def do_render (self, window, widget, background_area, cell_area, expose_area, flags):
        if not self.get_property ("category-header"):
            self.render_match (window, widget, background_area, cell_area, expose_area, flags)
        else:
            self.render_category (window, widget, background_area, cell_area, expose_area, flags)
    
    def render_match (self, window, widget, background_area, cell_area, expose_area, flag):
        ctx = window.cairo_create ()
        
        # Set up a pango.Layout
        more_actions_layout = ctx.create_layout ()
        if self.get_property("has-more-actions"):
            more_actions_layout.set_markup ("<b>&gt;</b>")
        else:
            more_actions_layout.set_text("")
        more_actions_layout.set_font_description (self.header_font_desc)
        
        more_actions_layout_width, more_actions_layout_height = more_actions_layout.get_pixel_size()
                
        state = self.renderer_state_to_widget_state(flag)
        
        # Draw the actual text in the remaining area
        cell_area_width = cell_area.width
        cell_area.width -= more_actions_layout_width + 2
        gtk.CellRendererText.do_render (self, window, widget, background_area, cell_area, expose_area, flag)
        
        mod_gc = widget.get_style().text_gc[state]
        window.draw_layout(mod_gc,
                        (cell_area.x + cell_area_width) - more_actions_layout_width - 2,
                        cell_area.y + ( (cell_area.height - more_actions_layout_height) / 2 ) + 1,
                        more_actions_layout)
        
    def render_category (self, window, widget, background_area, cell_area, expose_area, flag):
        """
        Renders the category title from the "category-header" property and displays a rigth aligned
        hit count (read from the "match-count" property).
        """
        # Ensure we have fresh style settings
        self.set_style (widget)
        
        ctx = window.cairo_create ()
        
        # Set up a pango.Layout for the category title
        cat_layout = ctx.create_layout ()
        cat_layout.set_font_description (self.header_font_desc)
        
        cat_layout.set_markup("...")        
        cat_layout_width, cat_layout_height = cat_layout.get_pixel_size()
        ellipsise_size = cat_layout_width
        
        cat_text = self.get_property("category-header")
        cat_layout.set_markup(cat_text)
        cat_layout_width, cat_layout_height = cat_layout.get_pixel_size()
        
        # Set up a pango.Layout for the hit count
        count_layout = ctx.create_layout ()
        count_layout.set_text ("(" + str(self.get_property("match-count")) + ")")
        count_layout.set_font_description (self.header_font_desc)
        
        count_layout_width, count_layout_height = count_layout.get_pixel_size()
        
        max_cat_layout_width = cell_area.width - count_layout_width - 10
        
        if cat_layout_width > max_cat_layout_width:
            ratio = float(max_cat_layout_width - ellipsise_size)/cat_layout_width;
            characters = int( ratio * len(cat_text) )
            while (cat_layout_width > max_cat_layout_width):
                if characters > 0:
                    cat_layout.set_markup( cat_text[0:characters].strip() + "..." )
                    characters -= 1
                    cat_layout_width, cat_layout_height = cat_layout.get_pixel_size()
                else:
                    cat_layout.set_markup(cat_text.strip())
                    break
                
        state = self.renderer_state_to_widget_state(flag)
        main_gc = widget.get_style().text_gc[state]
        
        window.draw_layout(main_gc,
                        18,
                        cell_area.y + ( (cell_area.height - cat_layout_height) / 2) + 1,
                        cat_layout)
        
        mod_gc = widget.get_style().text_gc[state]
        window.draw_layout(mod_gc,
                        (cell_area.x + cell_area.width) - count_layout_width - 2,
                        cell_area.y + ( (cell_area.height - count_layout_height) / 2 ) + 1,
                        count_layout)
    
    def renderer_state_to_widget_state(self, flags):
        state = gtk.STATE_NORMAL
        if (gtk.CELL_RENDERER_SELECTED & flags) == gtk.CELL_RENDERER_SELECTED:
            state = gtk.STATE_SELECTED
        return state
        
    def do_get_property(self, property):
        if property.name == 'category-header':
            return self.__category_header
        elif property.name == 'match-count':
            return self.__match_count
        elif property.name == 'has-more-actions':
            return self.__has_more_actions
        elif property.name == 'match-markup':
            return self.__match_markup
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'category-header':
            self.__category_header = value
        elif property.name == 'match-count':
            self.__match_count = value
        elif property.name == 'has-more-actions':
            self.__has_more_actions = value
        elif property.name == 'match-markup':
            self.__match_markup = value
        else:
            raise AttributeError, 'unknown property %s' % property.name
        
class CuemiacTreeView (gtk.TreeView):
    """
    Shows a DeskbarCategoryModel. Sets the background of the root nodes (category headers)
    to gtk.Style().bg[gtk.STATE_NORMAL].
    """
    
    activation_keys = [gtk.keysyms.Return, gtk.keysyms.Right]
    
    __gsignals__ = {
        "match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
        "do-default-action" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT]),
    }
    
    def __init__ (self, model):
        gtk.TreeView.__init__ (self, model)
        self.set_enable_search (False)
        self.set_property ("headers-visible", False)
        
        self.connect ("row-activated", self.__on_activated) # Used activate result if enter in entry has been pressed 
        self.connect ("button-press-event", self.__on_button_press)        
        self.connect ("key-press-event", self.__on_key_press)
                
        icon = gtk.CellRendererPixbuf ()
        icon.set_property("xpad", 10)
        hit_title = CellRendererCuemiacCategory ()
        hit_title.set_property ("ellipsize", pango.ELLIPSIZE_END)
        
        hits = gtk.TreeViewColumn ("Hits")
        hits.pack_start (icon, expand=False)
        hits.pack_start (hit_title)
        hits.set_cell_data_func(hit_title, self.__get_match_title_for_cell)            
        hits.set_cell_data_func(icon, self.__get_match_icon_for_cell)
        self.append_column (hits)
        
        #self.set_reorderable(True)
        # FIXME: Make it so that categories *only* can be reordered by dragging
        # gtkTreeView does not use normal gtk DnD api.
        # it uses the api from hell
    
    def grab_focus(self):
        self.__select_first_item()
        gtk.TreeView.grab_focus(self)
    
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
        if match.__class__ == CuemiacCategory:
            return True
        else:
            return False

    def __on_button_press (self, treeview, event):
        # We want to activate items on single click
        path_ctx = self.get_path_at_pos (int(event.x), int(event.y))
        if path_ctx is not None:
            path, col, x, y = path_ctx
            model = self.get_model ()
            match = model[model.get_iter(path)][model.MATCHES]
            if match.__class__ != CuemiacCategory:
                if event.state & gtk.gdk.CONTROL_MASK:
                    self.__on_activated(treeview, path, col, event)
                else:
                    self.__on_do_default_action(treeview, path, col, event)
    
#    def __on_config_expanded_cat (self, value):
#        if value != None and value.type == gconf.VALUE_LIST:
#            self.__collapsed_rows = [h.get_string() for h in value.get_list()]
    
    def __get_match_icon_for_cell (self, column, cell, model, iter, data=None):
    
        match = model[iter][model.MATCHES]

        if match.__class__ == CuemiacCategory:
            cell.set_property ("pixbuf", None)
            cell.set_property ("visible", True)
            cell.set_property ("cell-background-gdk", self.style.bg[gtk.STATE_NORMAL])
        else:
            cell.set_property ("cell-background-gdk", self.style.base[gtk.STATE_NORMAL])
            if isinstance(match, Match):
                cell.set_property ("pixbuf", match.get_icon())
                cell.set_property ("visible", True)
            else:
                logging.error("See bug 359251 and report this output: Match object of unexpected type: %r - %r" % (match.__class__, match))
                cell.set_property ("pixbuf", None)
                cell.set_property ("visible", False)
        
    def __get_match_title_for_cell (self, column, cell, model, iter, data=None):
    
        match = model[iter][model.MATCHES]
        
        if match.__class__ == CuemiacCategory:
            # Look up i18n category name
            cell.set_property ("cell-background-gdk", self.style.bg[gtk.STATE_NORMAL])
            cell.set_property ("height", 20)
            cell.set_property ("category-header", match.get_name())
            cell.set_property ("match-count", match.get_count ())
            return
        
        cell.set_property ("category-header", None)
        cell.set_property ("height", -1)
        cell.set_property ("cell-background-gdk", self.style.base[gtk.STATE_NORMAL])
        
        cell.set_property ("has-more-actions", len(match.get_actions()) > 1)
                
        cell.set_property ("markup", model[iter][model.ACTIONS])

    def __on_do_default_action(self, treeview, path, col, event):
        model = self.get_model()
        iter = model.get_iter (path)
        match = model[iter][model.MATCHES]
        qstring = model[iter][model.QUERY]
        
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
            if match.__class__ == CuemiacCategory:
                path = model.get_path (iter)
                if self.row_expanded (path):
                    self.collapse_row (path)
                else:
                    self.expand_row (path, False)
                return True
            else:
                path = model.get_path(iter)
                col = model.ACTIONS
                self.__on_activated(widget, path, col, event)
        elif (event.keyval == gtk.keysyms.Down):
            if match.__class__ == CuemiacCategory:
                return False
            elif model.get_path(iter) == self.__get_bottom_path():
                # We're at the bottom of the list
                self.__select_first_item()
                return True
            else:
                iter_next = model.iter_next(iter)
                if iter_next == None:
                    # We're at the last item of a category
                    # Select the first item of the next category
                    parent = model.iter_parent(iter)
                    num = model.get_path(parent)[0]+1
                    self.__select_path( (num, 0) )
                    return True
        elif (event.keyval == gtk.keysyms.Up):
            if match.__class__ == CuemiacCategory:
                return False
            elif model.get_path(iter) == (0,0):
                # We're at the top of the list 
                self.__select_last_item()
                return True
            elif model.get_path(iter)[1] == 0:
                # We're at the first item of a category
                # Select the last item of the previous category
                parent = model.iter_parent(iter)
                num = model.get_path(parent)[0]-1
                prev_cat = model.get_iter( (num,) )
                child = model.iter_n_children(prev_cat)-1
                
                self.__select_path( (num, child) )
                return True
            
        return False
    
    def __select_first_item(self):
        model = self.get_model()
        path = model.get_path( model.iter_nth_child(model.get_iter_first(), 0))
        self.__select_path(path)
        
    def __select_last_item(self):
        path = self.__get_bottom_path()
        self.__select_path(path)
    
    def __select_path(self, path):
        self.get_selection().select_path( path )
        gobject.idle_add(self.scroll_to_cell, path )
        self.set_cursor_on_cell( path )
        
    def __select_iter(self, iter):
        self.__select_path( self.get_model().get_path(iter) )
    
    def __get_bottom_path(self):
        model = self.get_model()
        last_cat = len(model)-1
        last_cat_iter =  model.iter_nth_child(None, last_cat)
        last_cat_children = model.iter_n_children(last_cat_iter)-1
        return (last_cat, last_cat_children)

if gtk.pygtk_version < (2,8,0):    
    gobject.type_register (CuemiacTreeView)
    gobject.type_register (CellRendererCuemiacCategory)
