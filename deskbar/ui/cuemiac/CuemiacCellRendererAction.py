import gtk
import gobject
import pango
from deskbar.ui.cuemiac.CuemiacCellRenderer import CuemiacCellRenderer

class CuemiacCellRendererAction (CuemiacCellRenderer):
    """
    Special cell renderer for the CuemiacTreeView.
    
    If the cell to be rendered is a normal Match that has
    more than one action an arrow is displayed.
    If it's CuemiacCategory the match-count is displayed.
    """
    
    __gproperties__ = {
                 'is-header' : (gobject.TYPE_BOOLEAN, 'whether we render a category header',
                                'Render the header of a category, i.e. display the match-count',
                                False, gobject.PARAM_READWRITE),
                 'match-count' : (gobject.TYPE_INT, 'number of hits in the category',
                                  'the number of hits for the CuemiacCategory to be rendered',
                                  0, 1000, 0, gobject.PARAM_READWRITE),
                 'has-more-actions' : (gobject.TYPE_BOOLEAN, 'whether the match has more than one action',
                                       'If set to True a symbol will be displayed on the right',
                                       False, gobject.PARAM_READWRITE),
        }
    
    def __init__ (self):
        CuemiacCellRenderer.__init__ (self)
        self.__match_count = 0
        self.__has_more_actions = False
        self.__is_header = False
        
    def do_get_property(self, property):
        if property.name == 'match-count':
            return self.__match_count
        elif property.name == 'has-more-actions':
            return self.__has_more_actions
        elif property.name == 'is-header':
            return self.__is_header
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'match-count':
            self.__match_count = value
        elif property.name == 'has-more-actions':
            self.__has_more_actions = value
        elif property.name == 'is-header':
            self.__is_header = value
        else:
            raise AttributeError, 'unknown property %s' % property.name
    
    def do_render (self, window, widget, background_area, cell_area, expose_area, flags):
        self.set_style(widget)
        if self.get_property ("is-header"):
            self.render_category (window, widget, background_area, cell_area, expose_area, flags)
        elif self.get_property ("has-more-actions"):
                self.render_match (window, widget, background_area, cell_area, expose_area, flags)
   
    def do_get_size(self, widget, cell_area):
        """
        Calculate size that is required to display
        """
        (xoffset, yoffset, w, h) = gtk.CellRendererText.do_get_size (self, widget, cell_area)
        
        context = widget.get_pango_context()
        metrics = context.get_metrics(self.header_font_desc, context.get_language())
        char_width = metrics.get_approximate_char_width()
        
        if self.get_property("is-header"):
            num_chars = len(str(self.get_property("match-count"))) + 2
        else:
            num_chars = 1
        
        width = self.get_property("xpad") * 2 + ((char_width/pango.SCALE) * num_chars);
        
        return (xoffset, yoffset, width, h)
   
    def _calculate_arrow_geometry (self, x, y, width, height):
        """
        Stolen from calculate_arrow_geometry at
        http://svn.gnome.org/svn/gtk+/trunk/gtk/gtkstyle.c
        """
        # For right arrows only
        h = height + (height % 2) - 1
        w = (h / 2 + 1)
        
        if w > width:
            w = width
            h = 2 * w - 1
            
        if (width % 2 == 1 or w % 2 == 0):
            w += 1
            
        new_x = x + (width - w) / 2;
        new_y = y + (height - h) / 2;
        return (new_x, new_y, w, h)
        
   
    def _draw_arrow_right(self, window, color, state, area, x, y, width, height):
        (x, y, width, height) = self._calculate_arrow_geometry(x, y, width, height)
        
        cr = window.cairo_create()
        cr.set_source_color (color)
        
        if area:
            cr.rectangle (area)
            cr.clip()
    
        # Draw right arrow
        cr.move_to(x,y)
        cr.line_to(x + width, y + height / 2)
        cr.line_to(x, y + height)

        cr.close_path()
        
        cr.fill()
    
    def render_match (self, window, widget, background_area, cell_area, expose_area, flags):
        """
        Renders an arrow
        """
        state = self.renderer_state_to_widget_state(flags)
        
        if state & gtk.STATE_PRELIGHT:
            color = color = widget.style.dark[state]
        else:
            color = color = widget.style.fg[state]
        
        arrow_width = cell_area.width / 2
        # Set the arrow height to the current font size in pixels
        arrow_height = widget.get_pango_context().get_font_description().get_size() / pango.SCALE
        
        self._draw_arrow_right(window, color, state, cell_area,
                               cell_area.x + cell_area.width / 2,
                               cell_area.y + ((cell_area.height - arrow_height) / 2) + 1,
                               arrow_width,
                               arrow_height)
        
    def render_category (self, window, widget, background_area, cell_area, expose_area, flag):
        """
        Renders the hit count (read from the "match-count" property).
        """
        ctx = window.cairo_create ()
        
        # Set up a pango.Layout for the hit count
        count_layout = ctx.create_layout ()
        count_layout.set_text  ("(" + str(self.get_property("match-count")) + ")")
        count_layout.set_font_description (self.header_font_desc)
        
        count_layout_width, count_layout_height = count_layout.get_pixel_size()
                
        state = self.renderer_state_to_widget_state(flag)
        
        mod_gc = widget.get_style().text_gc[state]
        
        window.draw_layout(mod_gc,
                           cell_area.x + (cell_area.width - count_layout_width) / 2,
                           cell_area.y + ( (cell_area.height - count_layout_height) / 2) + 1,
                           count_layout)
    