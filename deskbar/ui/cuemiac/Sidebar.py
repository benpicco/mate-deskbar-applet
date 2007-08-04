import gtk
import gobject

class Sidebar(gtk.VBox):

	__gsignals__ = {
		"closed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
	}

	def __init__(self, title=""):
		gtk.VBox.__init__(self)
		hbox = gtk.HBox(False, 0)
		self.pack_start(hbox, False, False, 0)
		
		self.label = gtk.Label()
		self.set_title(title)
		self.label.show()
		hbox.pack_start(self.label, True, True, 0)
		
		close_button = gtk.Button()
		close_button.set_relief(gtk.RELIEF_NONE)
		close_button.connect("clicked", self._close_clicked_cb)

		image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
		close_button.add(image)
		image.show()
		
		hbox.pack_end(close_button, False, False, 0)
		close_button.show()
		
		hbox.show()
		
	def _close_clicked_cb(self, widget):
		self.emit("closed")
		self.hide()
		
	def set_title(self, markup):
		self.label.set_markup(markup)
