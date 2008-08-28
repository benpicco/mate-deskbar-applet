from deskbar.ui.AbstractCuemiacDeskbarIcon import AbstractCuemiacDeskbarIcon
from deskbar.core.Categories import CATEGORIES
from deskbar.core.DeskbarHistory import EmptyHistoryAction
from gettext import gettext as _
from os.path import join
import deskbar
import gtk
import logging

LOGGER = logging.getLogger(__name__)

class DeskbarPopupMenu (gtk.Menu):
    
    class Item (gtk.ImageMenuItem):
        
        def __init__(self, label=None, stock_id=None, pixbuf=None):
            gtk.ImageMenuItem.__init__ (self)
            
            self.box = gtk.HBox (False, 3)
            self.box.show()
            self.add(self.box)
            
            self.image = gtk.Image ()
            if stock_id != None:
                self.set_image_from_stock (stock_id)
            elif isinstance(pixbuf, gtk.gdk.Pixbuf):
                self.set_image_from_pixbuf(pixbuf)
            
            self.image.show()
            self.box.pack_start (self.image, False, False, 0)
            
            self.label = gtk.Label ()
            self.set_markup(label)
            self.label.show()
            
            self.alignment = gtk.Alignment ()
            self.alignment.add (self.label)
            self.alignment.show()
            self.box.pack_start (self.alignment)
            
        def set_image_from_stock(self, stock_id):
            if stock_id != None:
                self.image.set_from_stock (stock_id, gtk.ICON_SIZE_MENU)
            
        def set_image_from_pixbuf(self, pixbuf):
            if pixbuf != None:
                self.image.set_from_pixbuf(pixbuf)
            
        def set_markup(self, text):
            if text != None:
                self.label.set_markup(text)

    def __init__(self, controller, history):
        gtk.Menu.__init__ (self)
        
        menuItem = DeskbarPopupMenu.Item (_("History"),
                                          pixbuf=CATEGORIES["history"]["icon"])
        self.append(menuItem)
        
        self.historymenu = HistoryMenu(controller, history)
        menuItem.set_submenu(self.historymenu)
        
        self.append(gtk.SeparatorMenuItem())
        
        menuItem = DeskbarPopupMenu.Item (_("Clear History"), gtk.STOCK_CLEAR)
        menuItem.connect ("activate", controller.on_clear_history)
        self.append(menuItem)
        
        menuItem = DeskbarPopupMenu.Item (_("Preferences"), gtk.STOCK_PROPERTIES)
        menuItem.connect ("activate", controller.on_show_preferences)
        self.append(menuItem)
        
        menuItem = DeskbarPopupMenu.Item (_("Help"), gtk.STOCK_HELP)
        menuItem.connect ("activate", controller.on_show_help)
        self.append(menuItem)
        
        menuItem = DeskbarPopupMenu.Item (_("About"), gtk.STOCK_ABOUT)
        menuItem.connect ("activate", controller.on_show_about)
        self.append(menuItem)
        
        self.append(gtk.SeparatorMenuItem())
        
        menuItem = DeskbarPopupMenu.Item (_("Quit"), gtk.STOCK_QUIT)
        menuItem.connect ("activate", lambda w: gtk.main_quit())
        self.append(menuItem)
        

class HistoryMenu (gtk.Menu):
    
    def __init__(self, controller, history):
        gtk.Menu.__init__(self)
        self.__controller = controller
        self.__history = history
        self.__is_empty = True
        self.__selected_item = None
        
        self.connect ("key-press-event", self.on_key_press_event)
        
        for row in history:
            text = row[history.COL_TEXT]
            action = row[history.COL_ACTION]
            
            menuItem = DeskbarPopupMenu.Item ()
            menuItem.connect ("select", self.on_item_selected)
            menuItem.connect ("activate",
                              self.__controller.on_history_match_selected,
                              text, action)
                
            if isinstance(action, EmptyHistoryAction):
                # TRANSLATORS: Below "Empty" is an adjective. As in 
                #              the state of being empty
                menuItem.set_markup(_("<i>Empty</i>"))
                menuItem.set_image_from_pixbuf (CATEGORIES["history"]["icon"])
                
                self.__is_empty = True
            else:
                text = action.get_verb () % action.get_escaped_name(text)
                # We only want to display the first line of text
                # E.g. some beagle-live actions display a snippet in the second line 
                text = text.split("\n")[0]
                
                menuItem.set_markup(text)
                menuItem.set_image_from_pixbuf(action.get_pixbuf())
                
                self.__is_empty = False
                
            self.append(menuItem)
    
    def clear(self):
        for w in self:
            self.remove(w)
        self.__selected_item = None
        if not self.__is_empty:
            self.append_empty_action()
    
    def on_key_press_event(self, menu, event):
        if event.keyval == gtk.keysyms.Delete:
            if self.__selected_item != None:
                # This is stupid put we need to get the
                # position of the child somehow
                for i, child in enumerate(self.get_children()):
                    if child == self.__selected_item:
                        break
                self.__history.remove_index_and_save(i)
                self.remove(self.__selected_item)
                self.__selected_item = None
                self.reposition()
            
    def on_item_selected(self, item):
        self.__selected_item = item
        
            
class DeskbarStatusIcon (gtk.StatusIcon, AbstractCuemiacDeskbarIcon):
    
    def __init__(self):
        gtk.StatusIcon.__init__(self)
        AbstractCuemiacDeskbarIcon.__init__(self)
        
        self.set_visible (False)
        self.set_tooltip (_("Show search entry"))
        #self.connect ("notify::orientation", self._on_orientation_changed)
        self.connect ("size-changed", self._on_size_changed)
        self.connect ("activate", self._on_activate)
        self.connect ("popup-menu", self._on_popup_menu)
        
        self._setup_mvc()
        
        self._on_size_changed(self, self.get_size())
    
    def on_loaded(self, sender):
        AbstractCuemiacDeskbarIcon.on_loaded (self, sender)
        self.set_visible (True)
    
    def _on_size_changed (self, status_icon, size):
        pixbuf = self.get_deskbar_icon (size)
        self.set_from_pixbuf (pixbuf)
        
    def _on_activate (self, status_icon):
        AbstractCuemiacDeskbarIcon.set_active (self, not self.active, gtk.get_current_event_time())
        
    def _on_popup_menu (self, status_icon, button, activate_time):
        self.setup_menu()    
        self._menu.show_all()
        self._menu.popup(None, None,
                         gtk.status_icon_position_menu,
                         button, activate_time, self)
    
    def _on_ui_name_changed(self, gconfstore, name):
        if name != deskbar.WINDOW_UI_NAME:
            LOGGER.info ("Only window UI is supported in tray mode")
            
    def _setup_mvc(self):
        self._setup_core()
        self._setup_controller(self._core)
        # Force window UI, because button UI requires applet
        self._setup_view(self._core, deskbar.WINDOW_UI_NAME)
        
        self._core.run()
    
    def create_button_ui(self):
        raise NotImplementedError
    
    def setup_menu(self):
        self._menu = DeskbarPopupMenu (self._controller,
                                       self._core.get_history())
        