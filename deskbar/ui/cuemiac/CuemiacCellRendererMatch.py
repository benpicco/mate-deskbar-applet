import gtk
import gobject
import pango
from deskbar.ui.cuemiac.CuemiacCellRenderer import CuemiacCellRenderer

class CuemiacCellRendererMatch (CuemiacCellRenderer):
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
        }
    
    def __init__ (self):
        CuemiacCellRenderer.__init__ (self)
        self.__category_header = None
        
    def do_get_property(self, property):
        if property.name == 'category-header':
            return self.__category_header
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'category-header':
            self.__category_header = value
        else:
            raise AttributeError, 'unknown property %s' % property.name
        
    def do_render (self, window, widget, background_area, cell_area, expose_area, flags):
        self.set_style(widget)
        if self.get_property ("category-header"):
            self.render_category (window, widget, background_area, cell_area, expose_area, flags)
        else:
            gtk.CellRendererText.do_render (self, window, widget, background_area, cell_area, expose_area, flags)
   
    def render_category (self, window, widget, background_area, cell_area, expose_area, flag):
        """
        Renders the category title from the "category-header" property and displays a rigth aligned
        hit count (read from the "match-count" property).
        """
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
         
        state = self.renderer_state_to_widget_state(flag)
        main_gc = widget.get_style().text_gc[state]
        
        window.draw_layout(main_gc,
                        18,
                        cell_area.y + ( (cell_area.height - cat_layout_height) / 2) + 1,
                        cat_layout)
    