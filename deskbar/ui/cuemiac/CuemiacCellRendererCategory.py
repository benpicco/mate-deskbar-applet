import gtk
import gobject
import pango

class CuemiacCellRendererCategory (gtk.CellRendererText):
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
        }
    __gsignals__ = {
        # This signal will be emited when '>' on the right is clicked
        "show-actions-activated": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        # This signal will be emited then an area that's not the '>' from above is clicked
        "do-action-activated": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
    }
    
    def __init__ (self):
        gtk.CellRendererText.__init__ (self)
        self.__category_header = None
        self.__match_count = 0
        self.__has_more_actions = False
        self.__match_markup = ""
        self.__button_x = 0
        self.__button_y = 0
        self.__button_width = 0
        self.__button_height = 0
        self.__relative_header_size = -0.2 # Make header 20% smaller than normal fonts
        
        self.set_property("mode", gtk.CELL_RENDERER_MODE_ACTIVATABLE)
        
        # Grab some default theme settings
        # they are probably incorrect, but we reset
        # them on each render anyway.
        style = gtk.Style ()
        self.header_font_desc = style.font_desc
        self.header_font_desc.set_weight (pango.WEIGHT_BOLD)        
        self.header_font_desc.set_size (self.header_font_desc.get_size () + int(self.header_font_desc.get_size ()*self.__relative_header_size))
        self.header_bg = style.base [gtk.STATE_NORMAL]
    
    def set_style (self, widget):
        """
        Apply the style from widget, to this cellrenderer
        """
        self.header_font_desc = widget.style.font_desc
        self.header_font_desc.set_weight (pango.WEIGHT_BOLD)
        self.header_font_desc.set_size (self.header_font_desc.get_size () + int(self.header_font_desc.get_size ()*self.__relative_header_size))
        self.header_bg = widget.style.base [gtk.STATE_NORMAL]
    
    def do_render (self, window, widget, background_area, cell_area, expose_area, flags):
        if not self.get_property ("category-header"):
            self.render_match (window, widget, background_area, cell_area, expose_area, flags)
        else:
            self.render_category (window, widget, background_area, cell_area, expose_area, flags)
   
    def render_match (self, window, widget, background_area, cell_area, expose_area, flags):
        ctx = window.cairo_create ()
        
        # Set up a pango.Layout
        more_actions_layout = ctx.create_layout ()
        if self.get_property("has-more-actions"):
            more_actions_layout.set_markup ("<b>&gt;</b>")
        
        more_actions_layout.set_font_description (self.header_font_desc)
        
        more_actions_layout_width, more_actions_layout_height = more_actions_layout.get_pixel_size()
                
        state = self.renderer_state_to_widget_state(flags)
        
        self.__button_width = more_actions_layout_width + 2
        self.__button_height = cell_area.height 
        
        # Draw the actual text in the remaining area
        cell_area_width = cell_area.width
        cell_area.width -= self.__button_width
        gtk.CellRendererText.do_render (self, window, widget, background_area, cell_area, expose_area, flags)
        
        mod_gc = widget.get_style().text_gc[state]
        
        self.__button_x = (cell_area.x + cell_area_width) - more_actions_layout_width - 2
        self.__button_y = cell_area.y + ( (cell_area.height - more_actions_layout_height) / 2 ) + 1
        
        window.draw_layout(mod_gc,
                        self.__button_x,
                        self.__button_y,
                        more_actions_layout)
        
        if self.get_property("has-more-actions"):
            # Add some additional area around the '>' to activate it
            self.__button_x -= 3
            self.__button_y = cell_area.y
            self.__button_width += 3
        else:
            self.__button_height = 0
            self.__button_width = 0
            self.__button_x = 0
            self.__button_y = 0
        
        #window.draw_rectangle(mod_gc, False, self.__button_x, self.__button_y,
        #            self.__button_width, self.__button_height          
        #            )
        
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
    
    def do_activate(self, event, widget, path_string, background_area, cell_area, flags):
        if not isinstance(widget, gtk.TreeView):
            # Not a treeview
            return False
        
        if event == None or event.type != gtk.gdk.BUTTON_PRESS:
            # Event type not GDK_BUTTON_PRESS
            return True
        
        ex = event.x
        ey = event.y
        bx = self.__button_x
        # Otherwise, we get problems when the cell
        # is at the top of the visible part of the treeview
        by = cell_area.y 
        bw = self.__button_width
        bh = self.__button_height
        
        path = tuple([int(i) for i in path_string.split(':')])
        if (ex < bx or ex > (bx+bw) or ey < by or ey > (by+bh)):
            # Click wasn't on the icon
            self.emit("do-action-activated", path)
            return True
        else:
            self.emit("show-actions-activated", path)
            return False
        
    def do_get_property(self, property):
        if property.name == 'category-header':
            return self.__category_header
        elif property.name == 'match-count':
            return self.__match_count
        elif property.name == 'has-more-actions':
            return self.__has_more_actions
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'category-header':
            self.__category_header = value
        elif property.name == 'match-count':
            self.__match_count = value
        elif property.name == 'has-more-actions':
            self.__has_more_actions = value
        else:
            raise AttributeError, 'unknown property %s' % property.name
    