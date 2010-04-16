# -*- coding: utf-8 -*-
import gobject
import gtk
import gtk.gdk
import struct
from gettext import gettext as _

MAXINT = 2 ** ((8 * struct.calcsize('i')) - 1) - 1

class AccelEntry( gobject.GObject ):

    __gsignals__ = {
        'accel-edited': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                         [gobject.TYPE_STRING, gobject.TYPE_UINT, gobject.TYPE_UINT, gobject.TYPE_UINT]),
    }
    __gproperties__ = {
        'accel_key': ( gobject.TYPE_UINT, "Accelerator key", "Accelerator key", 0, MAXINT, 0, gobject.PARAM_READWRITE ),
        'accel_mods': ( gobject.TYPE_FLAGS, "Accelerator modifiers", "Accelerator modifiers", 0, gobject.PARAM_READWRITE ),
        'keycode': ( gobject.TYPE_UINT, "Accelerator keycode", "Accelerator keycode", 0, MAXINT, 0, gobject.PARAM_READWRITE ),
    }
    
    FORBIDDEN_KEYS = (gtk.keysyms.BackSpace, gtk.keysyms.Begin, gtk.keysyms.Delete, gtk.keysyms.End, gtk.keysyms.Down,
                      gtk.keysyms.Home, gtk.keysyms.Insert, gtk.keysyms.Left, gtk.keysyms.Page_Down, gtk.keysyms.Page_Up,
                      gtk.keysyms.Right, gtk.keysyms.Tab, gtk.keysyms.Up, gtk.keysyms.bar, gtk.keysyms.braceleft,
                      gtk.keysyms.braceright, gtk.keysyms.colon, gtk.keysyms.comma, gtk.keysyms.dollar, gtk.keysyms.equal,
                      gtk.keysyms.exclam, gtk.keysyms.hyphen, gtk.keysyms.period, gtk.keysyms.percent, gtk.keysyms.question,
                      gtk.keysyms.quotedbl, gtk.keysyms.semicolon, gtk.keysyms.slash, gtk.keysyms.space, gtk.keysyms.underscore)

    def __init__(self, accel_name=''):
        self.__old_value = None
        self._attributes = {'accel_key': 0, 'accel_mods': 0, 'keycode': 0}
        gobject.GObject.__init__(self)
        
        self.entry = gtk.Entry()
        self.entry.set_property('editable', False)
        self.entry.connect('button-press-event', self.__on_button_press_event)
        self.entry.connect('key-press-event', self.__on_key_press_event)
        self.entry.connect('focus-out-event', self.__on_focus_out_event)

        self.set_accelerator_name(accel_name)

    def do_get_property(self, pspec):
        if pspec.name in ('accel_key', 'accel_mods', 'keycode'):
            return self._attributes[pspec.name]
    
    def do_set_property(self, pspec, value):
        if pspec.name == 'accel_key':
            self.set_accelerator(int(value), self.get_property('keycode'), self.get_property('accel_mask'))
        elif pspec.name == 'accel_mods':
            self.set_accelerator(self.get_property('accel_key'), self.get_property('keycode'), int(value))
        elif pspec.name == 'keycode':
            self.set_accelerator(self.get_property('accel_key'), int(value), self.get_property('accel_mask'))

    def get_accelerator_name(self):
        return self.entry.get_text()

    def set_accelerator_name(self, value):
        if value == None:
            value = ""
            
        (keyval, mods) = gtk.accelerator_parse(value)
        if gtk.accelerator_valid(keyval, mods):
            self.entry.set_text(value)
        return

    def get_accelerator(self):
        return ( self.get_property('accel_key'), self.get_property('keycode'), self.get_property('accel_mods') )

    def set_accelerator(self, keyval, mods, keycode):
        changed = False
        self.freeze_notify()
        if keyval != self._attributes['accel_key']:
            self._attributes['accel_key'] = keyval
            self.notify('accel_key')
            changed = True
            
        if mods != self._attributes['accel_mods']:
            self._attributes['accel_mods'] = mods
            self.notify('accel_mods')
            changed = True
            
        if keycode != self._attributes['keycode']:
            self._attributes['keycode'] = keycode
            self.notify('keycode')
            changed = True
            
        self.thaw_notify()
        if changed:
            text = self.__convert_keysym_state_to_string (keyval, keycode, mods)
            self.entry.set_text(text)
            
    def __convert_keysym_state_to_string(self, keysym, keycode, mask):        
        name = gtk.accelerator_name(keysym, mask)
        if keysym == 0:
            name = "%s0x%02x" % (name, keycode)
        return name

    def get_widget(self):
        return self.entry

    def __on_button_press_event(self, entry, event):
        self.__old_value = self.entry.get_text()
        entry.set_text( _('New accelerator…') )
        entry.grab_focus()
        return True

    def __on_key_press_event(self, entry, event):
        accel_mods = 0
        edited = False
        
        keymap = gtk.gdk.keymap_get_default()
        translation = keymap.translate_keyboard_state(event.hardware_keycode, event.state, event.group)
        if translation == None:
            consumed_modifiers = 0
        else:
            (keyval, egroup, level, consumed_modifiers) = translation
        
        accel_keyval = gtk.gdk.keyval_to_lower(event.keyval)
        if (accel_keyval == gtk.keysyms.ISO_Left_Tab):
            accel_keyval = gtk.keysyms.Tab
        
        accel_mods = event.state & gtk.accelerator_get_default_mod_mask()
        
        # Filter consumed modifiers        
        accel_mods &= ~consumed_modifiers
        
          # Put shift back if it changed the case of the key, not otherwise.
        if (accel_keyval != event.keyval):
            accel_mods |= gtk.gdk.SHIFT_MASK
            
        if accel_mods == 0:
            if accel_keyval == gtk.keysyms.Escape:
                self.__revert()
                return True
                        
        # Do not make keyboard unusable
        if ( ((accel_mods == 0 or accel_mods == gtk.gdk.SHIFT_MASK) and accel_keyval >= gtk.keysyms.a and accel_keyval <= gtk.keysyms.z) # alphabet
            or (accel_mods == 0 and (
                   (accel_keyval >= 48 and accel_keyval <= 57) # number keys
                or (accel_keyval >= gtk.keysyms.kana_fullstop and accel_keyval <= gtk.keysyms.semivoicedsound)
                   or (accel_keyval >= gtk.keysyms.Arabic_comma and accel_keyval <= gtk.keysyms.Arabic_sukun)
                    or (accel_keyval >= gtk.keysyms.Serbian_dje and accel_keyval <= gtk.keysyms.Cyrillic_HARDSIGN)
                     or (accel_keyval >= gtk.keysyms.Greek_ALPHAaccent and accel_keyval <= gtk.keysyms.Greek_omega)
                      or (accel_keyval >= gtk.keysyms.hebrew_doublelowline and accel_keyval <= gtk.keysyms.hebrew_taf)
                      or (accel_keyval >= gtk.keysyms.Thai_kokai and accel_keyval <= gtk.keysyms.Thai_lekkao)
                      or (accel_keyval >= gtk.keysyms.Hangul and accel_keyval <= gtk.keysyms.Hangul_Special)
                      or (accel_keyval >= gtk.keysyms.Hangul_Kiyeog and accel_keyval <= gtk.keysyms.Hangul_J_YeorinHieuh)
                  ))
            or (accel_mods == 0 and accel_keyval in self.FORBIDDEN_KEYS)
            or (accel_keyval == 0 and accel_mods != 0) ):
            dialog = gtk.MessageDialog (self.entry.get_toplevel(),
                gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
                gtk.MESSAGE_WARNING,
                gtk.BUTTONS_CANCEL,
                _("The shortcut \"%s\" cannot be used because it will prevent correct operation of your keyboard.\nPlease try with a key such as Control, Alt or Shift at the same time.\n")
                % gtk.accelerator_name(accel_keyval, accel_mods)
            )
            dialog.run()
            dialog.destroy()
            self.__revert()
            return True
                        
        if not gtk.accelerator_valid(accel_keyval, accel_mods):
            self.__revert()
            return True
        
        accel_name = self.__convert_keysym_state_to_string(accel_keyval, event.hardware_keycode, accel_mods)
        self.set_accelerator(accel_keyval, accel_mods, event.hardware_keycode)
        self.__old_value = None
        self.emit('accel-edited', accel_name, accel_keyval, accel_mods, event.hardware_keycode)
        return True

    def __on_focus_out_event(self, entry, event):
        if self.__old_value != None:
            self.__revert()
    
    def __revert(self):
        self.set_accelerator_name(self.__old_value)
