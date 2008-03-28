import gtk
from gettext import gettext as _

class ErrorDialog( gtk.Dialog ):
    
    def __init__(self, parent, error_short, error_long):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        title = _('Error')
        buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK)
        gtk.Dialog.__init__(self, title, parent, flags, buttons)
        self.connect('response', lambda w, id: self.destroy())
        
        self.set_modal(True)
        self.set_decorated(True)
        self.set_has_separator(False)
        self.set_border_width(6)
        self.set_resizable(False)
        self.vbox.set_spacing(12)
        self.action_area.set_layout(gtk.BUTTONBOX_SPREAD)
        
        self.hbox = gtk.HBox(spacing=6)
        self.vbox.pack_start(self.hbox)
        self.image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
        self.hbox.pack_start(self.image, False, False)
        
        self.text = gtk.Label()
        self.text.set_markup('<span size="larger"><b>%s</b></span>\n\n%s' % (error_short, _("Check the description beneath for further details.")))
        self.text.set_alignment(0.0, 0.0)
        self.text.set_line_wrap(True)
        self.text.set_selectable(True)        
        self.hbox.pack_start(self.text, False)
        
        self.expander = gtk.Expander( _('Details') )
        self.vbox.pack_start(self.expander, False, False)
        
        self.scrolledwin = gtk.ScrolledWindow()
        self.scrolledwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolledwin.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.expander.add(self.scrolledwin)
        
        self.textbuffer = gtk.TextBuffer()
        self.textview = gtk.TextView(self.textbuffer)
        self.textview.set_editable(False)
        self.textbuffer.set_text(str(error_long))
        self.scrolledwin.add(self.textview)
        self.show_all()
