import gtk
import pango
import gobject
import logging
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow

LOGGER = logging.getLogger(__name__)

class CuemiacHistoryView (gtk.TreeView):

    __gsignals__ = {
        "match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT]),
    }
    
    def __init__ (self, historystore):
        gtk.TreeView.__init__ (self, historystore)
        
        self.connect ("row-activated", lambda w,p,c: self.__on_activated())
        self.connect ("button-press-event", lambda w,e: self.__on_activated())
        self.set_property ("headers-visible", False)
        self.set_property ("hover-selection", True)
        
        icon = gtk.CellRendererPixbuf ()
        icon.set_property("xpad", 4)
        icon.set_property("xalign", 0.1)
        
        title = gtk.CellRendererText ()
        title.set_property ("ellipsize", pango.ELLIPSIZE_END)
        title.set_property ("width-chars", 25) #FIXME: Pick width according to screen size
        
        hits = gtk.TreeViewColumn ("Hits")
        hits.pack_start (icon)
        hits.pack_start (title)            
        hits.set_cell_data_func(icon, self.__get_action_icon_for_cell)
        hits.set_cell_data_func(title, self.__get_action_title_for_cell)
        self.append_column (hits)
        
    def __get_action_icon_for_cell (self, celllayout, cell, model, iter, user_data=None):
        
        timestamp, text, action = model[iter]
        if action == None:
            return
        
        cell.set_property ("pixbuf", action.get_pixbuf())
        
    def __get_action_title_for_cell (self, celllayout, cell, model, iter, user_data=None):
        
        timestamp, text, action = model[iter]
        if action == None:
            return
        
        text = action.get_verb () % action.get_escaped_name(text)
        # We only want to display the first line of text
        # E.g. some beagle-live actions display a snippet in the second line 
        text = text.split("\n")[0]
        cell.set_property ("markup", text)

    def __on_activated (self):
        model, iter = self.get_selection().get_selected()
        if iter != None:
            timestamp, text, action = self.get_model()[iter]
            if not action.is_valid():
                LOGGER.warning("Action is not valid anymore. Removing it from history.")
                self.get_model().remove(iter)
                self.__select_default_item()
                return False
            self.emit ("match-selected", text, action)
            
        return False

class CuemiacHistoryPopup (CuemiacAlignedWindow) :
    
    def __init__ (self, widget_to_align_with, applet, history_view):
        """
        @param widget_to_align_with: A widget the popup should align itself to.
        @param applet: A gnomeapplet.Applet instance. However - all that is needed is a .window attribute and a get_orient() method.
        @param history_view: A L{CuemiacHistoryView} instance.
        """
        CuemiacAlignedWindow.__init__ (self, widget_to_align_with, applet, window_type=gtk.WINDOW_POPUP)
        self.applet = applet
        self.window_group = None
        
        self.view = history_view
            
        self.add (self.view)
        self.view.connect('enter-notify-event', self.on_view_enter)
        self.view.connect('motion-notify-event', self.on_view_motion)
        self.view.connect('button-press-event', self.on_view_button_press)
        
    def on_view_button_press (self, widget, event):
        self.popdown()
        return False
    
    def on_view_enter (self, widget, event):
        return self.ignore_enter
            
    def on_view_motion (self, widget, event):
        self.ignore_enter = False
        return False
    
    def popup (self, time=None):
        if not (self.widgetToAlignWith.flags() & gtk.REALIZED):
            return
        if (self.flags()&gtk.MAPPED):
            return
        if not (self.widgetToAlignWith.flags()&gtk.MAPPED):
            return
        if len(self.view.get_model()) <= 0:
            return
        
        self.ignore_enter = True
        
        if not self.window_group :
            target_toplevel = self.widgetToAlignWith.get_toplevel()
            if target_toplevel != None and target_toplevel.group != None:
                target_toplevel.group.add_window (self)
                self.target_group = target_toplevel.group
            elif target_toplevel is not None:
                self.window_group = gtk.WindowGroup ()
                self.window_group.add_window (target_toplevel)
                self.window_group.add_window (self)
            else:
                print "WARNING in CuemiacEntryPopup : No toplevel window for widgetToAlignWith!"
                return
                    
        self.update_position()
        gtk.Window.show_all (self) # We issue warnings on the native methods, so bypass that

        # For grabbing to work we need the view realized
        if not (self.view.flags() & gtk.REALIZED):
            self.view.realize ()

        # Grab pointer
        self.view.grab_add()
        gtk.gdk.pointer_grab(
            self.view.window, True,
            gtk.gdk.BUTTON_PRESS_MASK|
                gtk.gdk.BUTTON_RELEASE_MASK|
                gtk.gdk.POINTER_MOTION_MASK,
            None, None, gtk.get_current_event_time())
            
    def popdown (self):
        if not (self.flags()&gtk.MAPPED):
            return
        
        self.ignore_enter = False

        gtk.Window.hide (self) # Bypass the warning we issue on hide()

        # Ungrab pointer
        gtk.gdk.pointer_ungrab(gtk.get_current_event_time())
        self.view.grab_remove()
    
    def show (self):
        LOGGER.warning("CuemiacHistoryPopup : Use of show() detected. Please use popup() instead.")
    
    def show_all (self):
        LOGGER.warning("WARNING, CuemiacHistoryPopup : Use of show_all() detected. Please use popup() instead.")
    
    def hide (self):
        LOGGER.warning("WARNING, CuemiacHistoryPopup : Use of hide() detected. Please use popdown() instead.")
    
if gtk.pygtk_version < (2,8,0):    
    gobject.type_register (CuemiacHistoryView)
    gobject.type_register (CuemiacHistoryPopup)
    