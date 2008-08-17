import gtk
import gnomeapplet
import gobject
import logging

LOGGER = logging.getLogger(__name__)

class CuemiacAlignedWindow (gtk.Window):
    """
    Borderless window aligning itself to a given widget.
    Use CuemiacWindow.update_position() to align it.
    """
    def __init__(self, widgetToAlignWith, applet, window_type=gtk.WINDOW_TOPLEVEL):
        """
        alignment should be one of
            gnomeapplet.ORIENT_{DOWN,UP,LEFT,RIGHT}
        
        Call CuemiacWindow.update_position () to position the window.
        """
        gtk.Window.__init__(self, window_type)
        self.set_decorated (False)

        # Skip the taskbar, and the pager, stick and stay on top
        self.stick()
        self.set_keep_above(True)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_border_width (1)
                
        self.widgetToAlignWith = widgetToAlignWith
        self.applet = applet

        self.realize_status = None
        self.connect ("realize", lambda win : self.__register_realize ())
        self.connect ("delete-event", self.on_delete_event)
        self.connect ("size-allocate", self.__resize_event)
    
    def on_delete_event(self, window, event):
        # Since all users of this class expect it to remain open and alive
        # We must catch deletion events (for example alt-f4) and just hide the window
        self.hide()
        return True
        
    def __resize_event (self, widget, allocation):
        # Update position, cause the size might have changed for the window
        self.update_position ()
    
    def adjust_popup_size(self):
         w, h = self.widgetToAlignWith.size_request ()
         
         # add border width
         w += 1
         h += 1
         
         self.resize(w, h)
    
    def update_position (self):
        """
        Calculates the position and moves the window to it.
        IMPORATNT: widgetToAlignWith should be realized!
        """
        if self.realize_status == None:
            self.realize_status = False
            self.realize ()
            return
        
        if self.realize_status == False:
            return
        
        if not (self.widgetToAlignWith.flags() & gtk.REALIZED):
            LOGGER.warning("CuemiacAlignedWindow.update_position() widgetToAlignWith is not realized.")
            return
            
        # Get our own dimensions & position
        (wx, wy) = self.window.get_origin ()
        (ax, ay) = self.widgetToAlignWith.window.get_origin ()

        (ww, wh) = self.window.get_size ()
        (aw, ah) = self.widgetToAlignWith.window.get_size ()

        screen = self.get_screen()
        monitor = screen.get_monitor_geometry (screen.get_monitor_at_window (self.applet.window))
        alignment = self.applet.get_orient()
        
        if alignment == gnomeapplet.ORIENT_LEFT:
            x = ax - ww
            y = ay
            
            if (y + wh > monitor.y + monitor.height):
                y = monitor.y + monitor.height - wh
            
            if (y < 0):
                y = 0
            
            if (y + wh > monitor.height / 2):
                gravity = gtk.gdk.GRAVITY_SOUTH_WEST    
            else:
                gravity = gtk.gdk.GRAVITY_NORTH_WEST
                    
        elif alignment == gnomeapplet.ORIENT_RIGHT:
            x = ax + aw
            y = ay
            
            if (y + wh > monitor.y + monitor.height):
                y = monitor.y + monitor.height - wh
            
            if (y < 0):
                y = 0
            
            if (y + wh > monitor.height / 2):
                gravity = gtk.gdk.GRAVITY_SOUTH_EAST
            else:
                gravity = gtk.gdk.GRAVITY_NORTH_EAST

        elif alignment == gnomeapplet.ORIENT_DOWN:
            x = ax
            y = ay + ah
            
            if (x + ww > monitor.x + monitor.width):
                x = monitor.x + monitor.width - ww
            
            if (x < 0):
                x = 0
            
            gravity = gtk.gdk.GRAVITY_NORTH_WEST
        elif alignment == gnomeapplet.ORIENT_UP:
            x = ax
            y = ay - wh
            
            if (x + ww > monitor.x + monitor.width):
                x = monitor.x + monitor.width - ww
            
            if (x < 0):
                x = 0
            
            gravity = gtk.gdk.GRAVITY_SOUTH_WEST
        
        self.move(x, y)
        self.set_gravity(gravity)
    
    def __register_realize (self):
        self.realize_status = True
        self.update_position()
        
gobject.type_register (CuemiacAlignedWindow)
