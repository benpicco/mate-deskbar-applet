import gtk
import gnomeapplet
import gobject
from gettext import gettext as _
import deskbar
from os.path import join
from deskbar.core.CoreImpl import CoreImpl
from deskbar.ui.CuemiacWindowView import CuemiacWindowView
from deskbar.ui.CuemiacWindowController import CuemiacWindowController

class ToggleEventBox(gtk.EventBox):
    __gsignals__ = {
        "toggled" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_LONG]),
    }
    
    def __init__(self):
        gtk.EventBox.__init__(self)
        self.active = False
        self.set_visible_window(False)
        self.connect('button-press-event', self.on_button_press)
    
    def on_button_press(self, widget, event):
        if event.button == 1:
            self.set_active(not self.active, event.time)
            return True
                
    def get_active(self):
        return self.active
    
    def set_active(self, active, time):
        changed = (self.active != active)
        self.active = active
        
        if changed:
            self.emit("toggled", time)
        
class DeskbarApplet (gtk.HBox):
    """
    Button consisting of two toggle buttons. A "main" with and image, and an "arrow"
    with a gtk.Arrow.
    
    It automatically arranges itself according to one of 
    gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
    
    Signals:
        toggled-main: The main button has been toggled
        toggle-arrow: the arrow button has been toggled
        
    The widget implements an interface like the gtk.ToggleButton, with _main or _arrow
    appended to method names for each button.
    """
    __gsignals__ = {
        "toggled-main" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        "toggled-arrow" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
    }

    def __init__ (self, applet):
        """
        popup_dir: gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}
        set the image in the main button with DeskbarAppletButton.set_button_image_from_file(filename)
        """
        gtk.HBox.__init__ (self)
        self.applet = applet
        self.popup_dir = applet.get_orient()
        
        if self.popup_dir in [gnomeapplet.ORIENT_UP,gnomeapplet.ORIENT_DOWN]:
            self.box = gtk.HBox ()
        else:
            self.box = gtk.VBox ()
            
        #self.button_main = gtk.ToggleButton ()
        #self.button_main.set_relief (gtk.RELIEF_NONE)
        self.button_main = ToggleEventBox()
        self.button_main.set_sensitive(False)
        self.image = gtk.Image ()
        self.button_main.add (self.image)
        self.button_main.connect ("toggled", lambda widget, time: self.emit ("toggled-main", widget))
        self.button_main.connect ("toggled", self.__show_toggle)
                
        self.box.pack_start (self.button_main)
        
        self.add (self.box)
        
        self.tooltips = gtk.Tooltips()
        self.tooltips.set_tip(self.button_main, _("Show search entry"))
        
        self.on_change_size()
        
        self.__setup_mvc()
        self.__setup_applet_menu()
       
    def __setup_mvc(self):
        self.__core = CoreImpl(deskbar.MODULES_DIRS)
        self.__core.connect("initialized", self.__on_init)
        self.__core.run()
        
        self.__controller = CuemiacWindowController(self.__core)
        self.__view = CuemiacWindowView(self.__controller, self.__core)
        self.__view.set_sensitive(False)
        
    def __setup_applet_menu(self):
        self.applet.setup_menu_from_file (
            deskbar.SHARED_DATA_DIR, "Deskbar_Applet.xml",
            None, [
            ("About", lambda a,b: self.__controller.on_show_about(a)),
            ("Prefs", lambda a,b: self.__controller.on_show_preferences(a)),
            ("Clear", lambda a,b: self.__controller.on_clear_history(a),)
            ])
        
    def __on_init(self, sender):
        old_modules = self.__core.get_old_modules()
        if len(old_modules) > 0:
                msg = _("Some potentially old modules that make use of an old Deskbar-Applet API have been found. Remove these files for this warning to disappear.\n")
                for mod in old_modules:
                    msg += "\n"+mod
                dialog = gtk.MessageDialog(parent=None,
                                  flags=0,
                                  type=gtk.MESSAGE_WARNING,
                                  buttons=gtk.BUTTONS_OK,
                                  message_format=msg)
                dialog.connect('response', lambda w, id: dialog.destroy())
                dialog.show_all()
        self.button_main.set_sensitive(True)
        self.__view.set_sensitive(True)
          
    def __show_toggle(self, widget, time):
        if self.__view.get_toplevel().get_property("visible"):
            self.__controller.on_quit()
        else:
            self.__controller.on_keybinding_activated(widget, time, False)
            
    def get_active_main (self):
        return self.button_main.get_active ()
    
    def set_active_main (self, is_active):
        self.button_main.set_active (is_active)
             
    def set_button_image_from_file (self, filename, size):
        # We use an intermediate pixbuf to scale the image
        if self.popup_dir in [gnomeapplet.ORIENT_DOWN, gnomeapplet.ORIENT_UP]:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size (filename, -1, size)
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size (filename, size, -1)
        self.image.set_from_pixbuf (pixbuf)
        
    def on_change_size (self):
        # FIXME: This is ugly, but i don't know how to get it right
        image_name = "deskbar-applet-panel"
        if self.applet.get_orient () in [gnomeapplet.ORIENT_UP, gnomeapplet.ORIENT_DOWN]:
            image_name += "-h"
        else:
            image_name += "-v"
        
        if self.applet.get_size() <= 36:
            image_name += ".png"
            s = -1
        else:
            image_name += ".svg"
            s = self.applet.get_size()-12
        
        self.set_button_image_from_file (join(deskbar.ART_DATA_DIR, image_name), s)
            
if gtk.pygtk_version < (2,8,0):            
    gobject.type_register(DeskbarApplet)
    gobject.type_register(ToggleEventBox)