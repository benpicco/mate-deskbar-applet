import gobject, gtk, gnomeapplet

import deskbar
from deskbar.ui.cuemiac.CuemiacAlignedWindow import CuemiacAlignedWindow
from deskbar.ui.cuemiac.CuemiacModel import CuemiacModel
from deskbar.ui.cuemiac.CuemiacTreeView import CuemiacTreeView
from deskbar.ui.cuemiac.CuemiacItems import CuemiacCategory, Nest
from deskbar.ui.cuemiac.CuemiacHistory import CuemiacHistoryView
from deskbar.ui.cuemiac.CuemiacEntry import CuemiacEntry
from deskbar.DeskbarHistory import get_deskbar_history
from deskbar.ui.EntryHistoryManager import EntryHistoryManager

# Make epydoc document signal
__extra_epydoc_fields__ = [('signal', 'Signals')]

class CuemiacUIManager (gobject.GObject) :
	"""
	This class is a member of the cuemiac duo, together with the
	C{CuemiacLayoutProvider}. The purpose of this class i to manage
	and instantiate the three cuemiac widgets consisting of
	
	 - C{CuemiacEntry}
	 - C{CuemiacTreeView} refered to as just "the view"
	 - C{CuemiacHistoryView}
	 
	The C{CuemiacUIManager} handles the underlying C{CuemiacModel},
	C{EntryHistoryManager} and other objects related to these tasks.
	
	B{Basic Usage}
	Write a subclass of C{CuemiacLayoutProvider} and instantiate a
	C{CuemiacUIManager} passing your layout object to the constructor.

	If you are writing a deskbar ui you might as well subclass both 
	C{CuemiacLayoutProvider} and C{DeskbarUI} to keep the code in a single
	file. For deskbar uis there is also the handy L{forward_deskbar_ui_signals}
	method which should spare you a few lines of code.
	
	B{A Note On Focus Handling}
	If you are using a layout in multiple gtk.Windows, and want to hide some
	of them on focus loss, you should look at how it is handled in 
	CuemiacHistory.CuemiacHistoryPopup and CuemiacPopupEntry.
	
	@signal start-query: (C{string})
	@signal stop-query: C{No arguments}
	@signal match-selected: I{tuple} : (C{query_string, match_object})
	@signal history-match-selected: I{tuple} : (C{query_string, match_object})
	@signal keyboard-shortcut: (C{key, keyval})
	@signal focus-out-event: (C{gtk.gdk.Event})
	"""
	
	__gsignals__ = {
		"start-query" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
		"stop-query" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
		"match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		"history-match-selected" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
		"keyboard-shortcut" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_UINT]),
		"focus-out-event" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT])
	}

	
	navigation_keys = [65364, 65362, 43, 45]#, 65293] # Down, Up, +, -, Enter
	
	def __init__(self, layout=None):
		"""
		@param layout: The C{CuemiacLayoutProvider} to use for layout and focus handling.
		"""
		gobject.GObject.__init__ (self)
		
		self.layout = layout
		
		self.default_entry_pixbuf = deskbar.Utils.load_icon("deskbar-applet-small.png", width=-1)
		self.clipboard = gtk.clipboard_get (selection="PRIMARY")

		self.entry = CuemiacEntry (self.default_entry_pixbuf)
		self.history = get_deskbar_history ()
		self.history_view = CuemiacHistoryView ()
		self.model = CuemiacModel ()
		self.cview = CuemiacTreeView (self.model)

		on_entry_changed_id = self.entry.connect ("changed", self._on_entry_changed)
		
		# Connect first the history handler then the regular key handler
		self.history_entry_manager = EntryHistoryManager(self.entry, on_entry_changed_id)
		self.history_entry_manager.connect('history-set', self._on_history_set)
		
		self.entry.connect ("key-press-event", self._on_entry_key_press)
		self.entry.connect_after ("changed", lambda entry : self._update_entry_icon())
		self.entry.connect ("activate", self._on_entry_activate)
		self.entry.connect ("button-press-event", self._on_entry_button_press)
		self.cview.connect ("key-press-event", self._on_cview_key_press)
		self.cview.connect ("match-selected", self._on_match_selected)
		self.cview.connect_after ("cursor-changed", lambda treeview : self._update_entry_icon())
		self.history_view.connect ("match-selected", self._on_match_selected, True)
		
		self._model_invalid = True
		self._orient = gnomeapplet.ORIENT_DOWN

		self.entry.show_all ()
		
	def get_view (self):
		"""
		@return: A reference to a widget displaying the search results.
		    This is intended to be directly embeddable into the application,
		    without further ado.
		    There is no API stability/garuantee as to what kind of widget is returned.
		    
		    FIXME: In the future a CuemiacView interface might be a good idea.
		"""
		return self.cview
		
	def get_entry (self):
		"""
		@return: A reference to the C{CuemiacEntry} widget managed by this class,
		    The CuemiacUIManager will issue a "start-query" signal when a query 
		    should be launched.
		"""
		return self.entry
		
	def get_history_view (self):
		"""
		@return: A C{CuemiacHistoryView} ready to be embedded in a 
		    C{CuemiacAlignedWindow} to create a history popup, or 
		    what ever you want.
		"""
		return self.history_view
	
	def set_layout (self, layout):
		"""
		@param layout: C{CuemiacLayoutProvider} to use for layout
		"""
		self.layout = layout
		
	def forward_deskbar_ui_signals (self, ui):
		"""
		Automatically emit signals on a C{DeskbarUI} when the relevant
		signals are emitted from the ui manager.
		
		If you are writing a C{DeskbarUI} you will not have set up any
		signal emitting yourself. The ui manager will handle this from
		now on.
		@param ui: The C{deskbar.ui.DeskbarUI} to emit the signals on.
		"""
		self.connect ("stop-query", lambda x: ui.emit("stop-query"))
		self.connect ("start-query", lambda x, qstring: ui.emit("start-query", qstring))
		self.connect ("keyboard-shortcut", lambda x, key, keyval: ui.emit("keyboard-shortcut", key, keyval))
		self.connect ("match-selected", lambda x, match: ui.emit("match-selected", match[0], match[1]))
		self.connect ("history-match-selected", lambda x, match: ui.emit ("match-selected", match[0], match[1]))
	
	def set_layout_by_orientation (self, orient):
		"""
		Adjust the various widgets managed to layout with repect to the given
		orientation.
		
		This method will also call C{set_layout_by_orientation} on the
		C{CuemiacLayoutProvider} associated with this ui manager.
		
		@param orient: The orientation to switch to. 
		    Must be one of gnomeapplet.ORIENT_{UP,DOWN,LEFT,RIGHT}.
		"""
		if orient in [gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT, gnomeapplet.ORIENT_DOWN]:
			self.cview.append_method = gtk.TreeStore.append
			self.model.set_sort_order(gtk.SORT_DESCENDING)
			self.history.set_sort_order (gtk.SORT_DESCENDING)
		else:
			# We are at a bottom panel. Put entry on bottom, and prepend matches (instead of append).
			self.cview.append_method = gtk.TreeStore.prepend
			self.model.set_sort_order(gtk.SORT_ASCENDING)
			self.history.set_sort_order (gtk.SORT_ASCENDING)
		
		self._orient = orient
		
		self.layout.set_layout_by_orientation (self, orient)
		
	def append_matches (self, matches):
		"""
		Append the given C{(query_string, match_obj)} tuple or list of tuples
		to the underlying model.
		
		You will typically call this method from C{DeskbarUI.append_matches()}.

		@param matches: A tuple (query_string, match_obj) or a list of such tuples.
		"""
		if self._model_invalid :
			self._model_invalid = False
			self.model.clear()
			
		self.model.append (matches)
		self._update_entry_icon ()
		
		# The UI might have trouble drawing the view
		# correctly when it is put in a gtk.ScrollView
		# issue a resize of the view to help redrawing correctly
		self.cview.queue_resize () # FIXME: Is this really a gtk bug in Ubuntu Dapper?
		
		self.layout.on_matches_added (self)
		
	def unselect_all (self):
		"""
		Convenience method for CuemiacLayoutProviders.
		Unselects everything in the view, history view, and entry,
		and updates the icon to reflect this.
		"""
		self.cview.get_selection().unselect_all()
		self.history_view.get_selection().unselect_all()
		self.entry.select_region (0,0)
		self._update_entry_icon ()

	def _update_entry_icon (self, icon=None):
		
		if icon == None:
			icon = self.default_entry_pixbuf
			if not (self.cview.get_toplevel().flags() & gtk.MAPPED):
				# The view is hidden, just show default icon
				self.entry.set_icon (icon)
				return
				
			path, column = self.cview.get_cursor ()
		
			if path != None:
				item = self.model[self.model.get_iter(path)][self.model.MATCHES]
				if item.__class__ != CuemiacCategory and item.__class__ != Nest:
					text, match = item
					icon=match.get_icon()
				
		self.entry.set_icon (icon)
		
	def _on_match_selected (self, cview, match, is_historic=False):
		if is_historic:
			self.layout.on_history_match_selected (self, match)
			self.emit ("history-match-selected", match)
		else:
			# This is a normal match
			self.layout.on_match_selected (self, match)
			self.emit ("match-selected", match)
			
		self.unselect_all () # This call updates the entry icon
	
	def _on_entry_changed (self, entry):
		self.history.reset()
		qstring = self.entry.get_text().strip()
		self.cview.set_query_string (qstring)
		if qstring == "":
			self.model.clear()
			self.emit ("stop-query")
			self.layout.on_stop (self)
			return
		
		self._model_invalid = True
		self.emit ("start-query", qstring)
	
	def _on_entry_key_press (self, entry, event):
		if event.keyval == gtk.keysyms.Escape:
			# bind Escape to clear the GtkEntry
			self.model.clear ()
			self.entry.set_text ("")
			# Setting the entry text to "" will emit a "stop-query"
			# and also call layout.on_stop()
			return False
		
		if 	event.state&gtk.gdk.MOD1_MASK != 0:
			# Some Handlers want to know about Alt-keypress
			# combinations, for example.  Here, we notify such
			# Handlers.
			text = entry.get_text().strip()
			if text != "":
				self.emit('stop-query')
				self.emit('keyboard-shortcut', text, event.keyval)
			entry.set_text("")
			
			# Broadcast an escape
			event.state = 0
			event.keyval = gtk.keysyms.Escape
			entry.emit('key-press-event', event)
			return True
			
		model, iter = self.cview.get_selection().get_selected ()
		if iter:
			# We have a selection in the view
			if event.keyval in self.navigation_keys:
				return self._on_cview_key_press (self.cview, event)
			
		if event.keyval == 65362: # Up
			if not self.cview.is_ready () : return
			self.layout.on_up_from_entry (self, event)
			return True
			
		if event.keyval == 65364: # Down
			if not self.cview.is_ready () : return
			self.layout.on_down_from_entry (self, event)
			return True

		return False
	
	def _on_history_key_press (self, history, event):
		if event.keyval == gtk.keysyms.Escape:
			self.hide_window (self.history_popup, event.time)
		self._update_entry_icon () # FIXME: Should we really do this?
		# FIXME: Call layout.on_{up,down}_from_history_{top,bottom}
		# This needs an API addition as CuemiacTreeView has (focus_{first,last}_match())
	
	def _on_history_set (self, historymanager, set):
		if set:
			text, match = historymanager.current_history
			self._update_entry_icon (icon=match.get_icon())
		else:
			self.entry.set_text("")
			self._update_entry_icon ()
	
	def _on_entry_activate (self, widget):
		# if we have an active history item, use it
		if self.history_entry_manager.current_history != None:
			text, match = self.history_entry_manager.current_history
			self._on_match_selected(widget, (text, match), True)
			return
			
		path, column = self.cview.get_cursor ()
		iter = None
		if path != None:
			iter = self.model.get_iter (path)
			
		if iter is None:
			if self._orient in [gnomeapplet.ORIENT_DOWN, gnomeapplet.ORIENT_LEFT, gnomeapplet.ORIENT_RIGHT]:
				# No selection, select top element # FIXME do this
				iter = self.model.get_iter_first()
				while iter != None and ((not self.model.iter_has_child(iter)) or (not self.cview.row_expanded(self.model.get_path(iter)))):
					iter = self.model.iter_next(iter)
				if iter != None:
					iter = self.model.iter_children(iter)

			else:
				# We are on a bottom panel - select the bottom element in the list 
				#FIXME: Should we iterate backwards up the list if the hit is a category?
				iter = self.model.get_iter (self.cview.last_visible_path())

		if iter is None:
			return
		# retrieve new path-col pair, since it might have been None to start out
		path = self.model.get_path (iter)
		column = self.cview.get_column (0)
		self.cview.emit ("row-activated", path, column) # This emits a match-selected from the cview
		
	def _view_has_selection (self):
		path, col = self.cview.get_cursor ()
		if path is None:
			return False
		else:
			return True
	
	def _on_cview_key_press (self, cview, event):
		# If this is an ordinary keystroke, or there is no selection in the cview,
		# just let the entry handle it.
		if not event.keyval in self.navigation_keys:# and not self._view_has_selection():
			self.entry.event (event)
			return True
		
		model, iter = cview.get_selection().get_selected ()
		if iter is None:
			# We have no selection
			return False
		path = model.get_path (iter)
		
		if event.keyval == 65362: # Up
			if model.paths_equal (path, model.get_path(model.get_iter_first())):		
				self.layout.on_up_from_view_top (self, event)
			else:
				self.cview.move_cursor_up_down (-1)
			return True
			
		elif event.keyval == 65364: # Down				
			if model.paths_equal (path, cview.last_visible_path()):
				self.layout.on_down_from_view_bottom (self, event)
			else:
				self.cview.move_cursor_up_down (1)
			return True
			
		elif event.keyval == 43: # +
			if model.iter_has_child (iter):
				self.cview.expand_row (path, False)
				return True
				
		elif event.keyval == 45: # -
			if model.iter_has_child (iter):
				self.cview.collapse_row (path)
				return True
				
		return False
				
	def _on_entry_button_press (self, widget, event):
		try:
			# GNOME 2.12
			self.applet.request_focus(long(event.time))
		except AttributeError:
			pass
			
		return False
		
gobject.type_register (CuemiacUIManager)
