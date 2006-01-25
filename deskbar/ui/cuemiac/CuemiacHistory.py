import gtk, pango, gobject
import cgi

import deskbar
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow

class CuemaicHistoryView (gtk.TreeView):

	__gsignals__ = {
		"match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}
	
	def __init__ (self, deskbar_history):
		gtk.TreeView.__init__ (self, deskbar_history)
		
		icon = gtk.CellRendererPixbuf ()
		title = gtk.CellRendererText ()
		title.set_property ("ellipsize", pango.ELLIPSIZE_END)
		title.set_property ("width-chars", 50) #FIXME: Pick width according to screen size
		hits = gtk.TreeViewColumn ("Hits")
		hits.pack_start (icon)
		hits.pack_start (title)
		hits.set_cell_data_func(title, self.__get_match_title_for_cell)			
		hits.set_cell_data_func(icon, self.__get_match_icon_for_cell)
		self.append_column (hits)
		
		self.connect ("button-press-event", self.__on_click)
		self.connect ("key-press-event", self.__on_key_press)
		
		self.set_property ("hover-selection", True)
		self.set_property ("headers-visible", False)
		
	def __get_match_icon_for_cell (self, column, cell, model, iter, data=None):
	
		text, match = model[iter][0]
		cell.set_property ("pixbuf", match.get_icon())

		
	def __get_match_title_for_cell (self, column, cell, model, iter, data=None):
	
		text, match = model[iter][0]

		# Pass unescaped query to the matches
		verbs = {"text" : text}
		verbs.update(match.get_name(text))
		# Escape the query now for display
		verbs["text"] = cgi.escape(verbs["text"])
		
		cell.set_property ("markup", match.get_verb () % verbs)

	def __on_click (self, widget, event):
		model, iter = self.get_selection().get_selected()
		match = model[iter][0]
		self.emit ("match-selected", match)
		print "click"
				
	def __on_key_press (self, widget, event):
		print "press"
		model, iter = self.get_selection().get_selected()
		if iter is None:
			return False
		match = model[iter][0]
		# If this is a category or nest, toggle expansion state
		if event.keyval == 65293: # enter
			self.emit ("match-selected", match)

class CuemiacHistoryPopup (CuemiacAlignedWindow) :

	__gsignals__ = {
		"match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}
	
	def __init__ (self, deskbar_history, widget_to_align_with, alignment):
		CuemiacAlignedWindow.__init__ (self, widget_to_align_with, alignment)
		view = CuemaicHistoryView (deskbar_history)
		self.add (view)
		
		view.connect ("match-selected", self.on_match_selected)
	
	def show (self):
		self.update_position ()
		CuemiacAlignedWindow.show (self)
	
	def show_all (self):
		self.update_position ()
		CuemiacAlignedWindow.show_all (self)
		
	def on_match_selected (self, sender, match):
		print sender, match
		self.hide()
		self.emit ("match-selected", match)
		
if gtk.pygtk_version < (2,8,0):	
	gobject.type_register (CuemiacHistoryView)
	gobject.type_register (CuemiacHistoryPopup)