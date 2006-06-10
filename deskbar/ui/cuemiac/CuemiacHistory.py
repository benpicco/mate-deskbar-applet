import gtk, pango, gobject, gnomeapplet
import cgi

import deskbar
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow
from deskbar.DeskbarHistory import get_deskbar_history

class CuemiacHistoryView (gtk.TreeView):

	__gsignals__ = {
		"match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}
	
	def __init__ (self):
		gtk.TreeView.__init__ (self, get_deskbar_history())
				
		icon = gtk.CellRendererPixbuf ()
		icon.set_property("xpad", 4)
		icon.set_property("xalign", 0.1)
		title = gtk.CellRendererText ()
		title.set_property ("ellipsize", pango.ELLIPSIZE_END)
		title.set_property ("width-chars", 50) #FIXME: Pick width according to screen size
		hits = gtk.TreeViewColumn ("Hits")
		hits.pack_start (icon)
		hits.pack_start (title)
		hits.set_cell_data_func(title, self.__get_match_title_for_cell)			
		hits.set_cell_data_func(icon, self.__get_match_icon_for_cell)
		self.append_column (hits)
		
		self.connect ("row-activated", lambda w,p,c: self.__on_activated())
		self.connect ("button-press-event", lambda w,e: self.__on_activated())             
        
		self.set_property ("headers-visible", False)
		self.set_property ("hover-selection", True)
		
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

	def __on_activated (self):
		model, iter = self.get_selection().get_selected()
		if iter != None:
			match = model[iter][0]
			self.emit ("match-selected", match)

		return True
		
class CuemiacHistoryPopup (CuemiacAlignedWindow) :

	__gsignals__ = {
		"match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
	}
	
	def __init__ (self, widget_to_align_with, applet, history_view=None):
		"""
		@param widget_to_align_with: A widget the popup should align itself to.
		@param applet: A gnomeapplet.Applet instance. However - all that is needed is a .window attribute and a get_orient() method.
		@param history_view: A L{CuemiacHistoryView} instance. If C{None} or nothing as passed, a new one will be created.
		"""
		CuemiacAlignedWindow.__init__ (self, widget_to_align_with, applet)
		self.applet = applet
		
		if not history_view:
			self.list_view = CuemiacHistoryView ()
		else:
			self.list_view = history_view
			
		self.add (self.list_view)
		
		self.list_view.connect ("match-selected", self.on_match_selected)
	
	def show (self, time=None):
		if len(self.list_view.get_model()) <= 0:
			return
		
		# Adapt the history popup direction to the applet orient
		if self.applet.get_orient() in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
			self.list_view.get_model().set_sort_order(gtk.SORT_DESCENDING)
		else:
			self.list_view.get_model().set_sort_order(gtk.SORT_ASCENDING)
			
		self.update_position ()
		if time == None:
			CuemiacAlignedWindow.show (self)
		else:
			CuemiacAlignedWindow.present_with_time (self, time)
	
	def show_all (self):
		self.update_position ()
		CuemiacAlignedWindow.show_all (self)
	
	def on_match_selected (self, sender, match):
		self.emit ("match-selected", match)
		
if gtk.pygtk_version < (2,8,0):	
	gobject.type_register (CuemiacHistoryView)
	gobject.type_register (CuemiacHistoryPopup)
