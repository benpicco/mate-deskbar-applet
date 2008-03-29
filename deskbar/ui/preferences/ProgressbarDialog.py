import gtk

class ProgressbarDialog( gtk.Dialog ):
    
    def __init__(self, parent):
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        title = ''
        buttons = None
        gtk.Dialog.__init__(self, title, parent, flags, buttons)
        
        self.set_modal(True)
        self.set_decorated(True)
        self.set_has_separator(False)
        self.set_border_width(6)
        self.set_resizable(False)        
        self.set_default_size(440, -1)
        
        # VBox containing text
        self.vbox2 = gtk.VBox(spacing=12)
        self.vbox.pack_start(self.vbox2, True, True, 6)
        
        self.text = gtk.Label()
        self.text.set_alignment(0.0, 0.0)
        self.text.set_line_wrap(True)
        self.vbox2.pack_start(self.text, False, True, 0)
        
        # VBox containing ProgressBar and status
        self.vbox3 = gtk.VBox()
        self.vbox.pack_start(self.vbox3, False, True, 0)
        
        self.progressbar = gtk.ProgressBar()
        self.vbox3.pack_start(self.progressbar, False, True, 0)
        
        self.current_operation = gtk.Label()
        self.current_operation.set_alignment(0.0, self.current_operation.get_alignment()[1])        
        self.vbox3.pack_start(self.current_operation, False, True, 0)
        
        return
    
    def pulse(self):
        """ Processbar pulses """
        self.progressbar.pulse()
        return
    
    def run_nonblocked(self):
        """ Run the dialog in non-blocking way """
        self.connect('response', lambda w,r: None)
        self.show_all()
        return
        
    def set_current_operation(self, text):
        """ Display the currently active operation beneath the progressbar """
        self.current_operation.set_markup('<span style="italic">%s</span>' % text)
        return
    
    def set_text(self, primary_text, secondary_text):
        """
        Set message
        
        @param primary_text: short summary of the message to display
        @param secondary_text: more in-detail information about the message
        """
        self.set_title(primary_text)
        self.text.set_markup('<span size="larger"><b>%s</b></span>\n\n%s' % (primary_text, secondary_text))
        return
    
    def set_fraction(self, value):
        if 0.0 <= value <= 1.0:
            self.progressbar.set_fraction(value)
    
