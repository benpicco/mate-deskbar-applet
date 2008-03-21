import deskbar
import deskbar.core.keybinder
import gobject
import gtk
import logging

LOGGER = logging.getLogger(__name__)

class Keybinder(gobject.GObject):
    __gsignals__ = {
        "activated" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_ULONG]),
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        
        self.bound = False
        self.prevbinding = None
    
    def on_keyboard_shortcut(self):
        self.emit('activated', deskbar.core.keybinder.tomboy_keybinder_get_current_event_time())
        
    def bind(self, keybinding):
        if self.bound:
            self.unbind()

        LOGGER.info('Binding Global shortcut %s to focus the deskbar', keybinding)
        try:
            self.bound = deskbar.core.keybinder.tomboy_keybinder_bind(keybinding, self.on_keyboard_shortcut)
            self.prevbinding = keybinding
        except KeyError:
            # binding failed
            self.bound = False
        
        return self.bound
                    
    def unbind(self):
        LOGGER.info('Unbinding Global shortcut %s to focus the deskbar', self.prevbinding)
        try:
            deskbar.core.keybinder.tomboy_keybinder_unbind(self.prevbinding)
            self.bound = False
        except KeyError:
            # if the requested keybinding is not bound, a KeyError will be thrown
            pass

if gtk.pygtk_version < (2,8,0):
    gobject.type_register(Keybinder)