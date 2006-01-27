from os.path import join
import cgi

import gtk, gobject

import deskbar, deskbar.iconentry
from deskbar import MAX_RESULTS_PER_HANDLER
from deskbar.ModuleList import ModuleList
from deskbar.Handler import *
from deskbar.Match import *
from deskbar.ui.EntryHistoryManager import EntryHistoryManager

# The liststore columns
HANDLER_PRIO_COL = 0
MATCH_PRIO_COL = 1
ACTION_COL = 2
ICON_COL = 3
MATCH_COL = 4
TEXT_COL = 5

# The sort function ids
SORT_BY_HANDLER_MATCH_ACTION = 1

#selection directions
MOVE_UP   = -1
MOVE_DOWN = +1

class DeskbarEntry(deskbar.iconentry.IconEntry):
	def __init__(self, ui):
		deskbar.iconentry.IconEntry.__init__(self)
		self.ui = ui
		
		self._completion_model = None
		self._completion_model_invalid = True
		self._selected_match_index = -1
			
		# Connect to underlying entry signals		
		entry = self.get_entry()
		entry.connect("activate", self._on_entry_activate)
		on_entry_changed_id = entry.connect("changed", self._on_entry_changed)
			
		self._history = EntryHistoryManager(self.get_entry(), on_entry_changed_id)
		self._history.connect('history-set', self.on_history_set)
		
		# Connect after the history handler
		entry.connect("key-press-event", self._on_entry_key_press)
		
		# The image showing the matches' icon
		self._image = gtk.Image()
				
		# Create the left icon in an event box
		self._evbox = gtk.EventBox()
		self._evbox.set_property('visible-window', False)
		self._evbox.add(self._image)
		self.pack_widget(self._evbox, True)
		self._evbox.show()
		
		self._default_pixbuf = deskbar.Utils.load_icon("deskbar-applet-small.png")
		self._image.set_property('pixbuf', self._default_pixbuf)

		# Create the listtore, model for the completion popup
		self._completion_model = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_STRING, gtk.gdk.Pixbuf, object, gobject.TYPE_STRING)
		self._completion_model.set_sort_column_id(SORT_BY_HANDLER_MATCH_ACTION, gtk.SORT_DESCENDING)
		self._completion_model.set_sort_func(SORT_BY_HANDLER_MATCH_ACTION, self._on_sort_matches)
		
		# Create the completion model
		completion = gtk.EntryCompletion()
		try:
			# PyGTK >= 2.8
			completion.set_popup_set_width(False)
		except AttributeError:
			pass
			
		try:
			# PyGTK >= 2.4
			completion.set_match_func(lambda x, y, z: True)
			completion.set_model(self._completion_model)
		except AttributeError:
			pass
			
		completion.connect("match-selected", lambda c, mod, it: self._on_completion_selected(mod[it][TEXT_COL], mod[it][MATCH_COL]))
		entry.set_completion(completion)
		
		# Paint  it accordingly		
		renderer = gtk.CellRendererPixbuf()
		completion.pack_start(renderer)
		completion.add_attribute(renderer, "pixbuf", ICON_COL)
		
		renderer = gtk.CellRendererText()
		completion.pack_start(renderer)
		completion.add_attribute(renderer, "markup", ACTION_COL)
		self.show_all()
		
	def get_evbox(self):
		return self._evbox
	
	def get_history(self):
		return self._history
					
	def _on_sort_matches(self, treemodel, iter1, iter2):
		# First compare global handler priority
		diff = treemodel[iter1][HANDLER_PRIO_COL] - treemodel[iter2][HANDLER_PRIO_COL]
		if diff != 0:
			return diff
		
		# We have the same global priority, use relative priority between matches
		diff = treemodel[iter1][MATCH_PRIO_COL] - treemodel[iter2][MATCH_PRIO_COL]
		if diff != 0:
			return diff
		
		# Finally use the Action to sort alphabetically
		a = treemodel[iter1][ACTION_COL]
		b = treemodel[iter2][ACTION_COL]
		if a != None:
			a = a.strip().lower()
		if b != None:
			b = b.strip().lower()
			
		if a < b:
			return 1
		elif a > b:
			return -1
		else:
			return 0
			
	def _on_entry_activate(self, widget):
		# if we have an active history item, use it
		if self._history.current_history != None:
			text, match = self._history.current_history
			self._on_completion_selected (text, match)
		else:	
			# When the user hits enter on the entry, we use the first match to do the action
			iter = self._completion_model.get_iter_first()
			if iter != None:
				self._on_completion_selected (self._completion_model[iter][TEXT_COL], self._completion_model[iter][MATCH_COL])
		
	#Clear the entry in a idle call or we segfault
	def after_match_selection(self):
		self.get_entry().set_text("")
		self._completion_model_invalid = True
		self._completion_model.clear()
		self._update_icon()
		print 'End of match selection sequence'

	def _on_completion_selected(self, text, match):
		self.ui.emit('match-selected', text, match)
						
		gobject.idle_add(self.after_match_selection)
				
	def _on_entry_key_press(self, entry, event):
		if event.keyval == gtk.keysyms.Escape:
			# bind Escape to clear the GtkEntry
			if not entry.get_text().strip() == "":
				# If we cleared some text, tell async handlers to stop.
				self.ui.emit('stop-query')
			entry.set_text("")
			return False
			
		if 	event.state&gtk.gdk.MOD1_MASK != 0:
			# Some Handlers want to know about Alt-keypress
			# combinations, for example.  Here, we notify such
			# Handlers.
			text = entry.get_text().strip()
			if text != "":
				self.ui.emit('stop-query')
				self.ui.emit('keyboard-shortcut', text, event.keyval)
			entry.set_text("")
			
			# Broadcast an escape
			event.state = 0
			event.keyval = gtk.keysyms.Escape
			entry.emit('key-press-event', event)
			return True
			
		return False
		
		def match_move(updown):
			self._selected_match_index = self._selected_match_index  + updown
			if self._selected_match_index == -2:
				# Wrap around
				self._selected_match_index = len(self._completion_model) - 1
			elif self._selected_match_index == len(self._completion_model):
				# End of list
				self._selected_match_index = -1
			self._update_icon()

		if event.keyval == gtk.keysyms.Up:
			match_move(MOVE_UP)

		if event.keyval == gtk.keysyms.Down:
			match_move(MOVE_DOWN)

		return False
					
	def _on_entry_changed(self, widget, matches=None):
		self._selected_match_index = -1
		self._history.history.reset ()

		qstring = widget.get_text().strip()
		if  qstring == "":
			#Reset default icon
			self._completion_model.clear()
			self._update_icon(icon=self._default_pixbuf)
			return
		
		self._completion_model_invalid = True
		self.ui.emit('start-query', qstring, MAX_RESULTS_PER_HANDLER)
	
	def on_history_set(self, historymanager, set):
		if set:
			text, match = self._history.current_history
			self._update_icon(icon=match.get_icon())
		else:
			#self.get_entry().set_text("")
			pass
			
	def _update_icon(self, iter=None, icon=None):
		if self._selected_match_index > -1 and len(self._completion_model) > 0:
			iter = self._selected_match_index

		if iter != None:
			self._image.set_property('pixbuf', self._completion_model[iter][ICON_COL])
		
		if icon != None:
			self._image.set_property('pixbuf', icon)
		
		self._image.set_size_request(deskbar.ICON_SIZE, deskbar.ICON_SIZE)
	
	def append_matches (self, matches):
		print 'Appending matches'
		if self._completion_model_invalid:
			self._completion_model_invalid = False
			self._completion_model.clear()
			
		for text, match in matches:
			handler = match.get_handler()
			if match.get_icon() != None:
				icon = match.get_icon()
			else:
				icon = handler.get_icon()
			
			# Pass unescaped query to the matches
			verbs = {"text" : text}
			verbs.update(match.get_name(text))
			# Escape the query now for display
			verbs["text"] = cgi.escape(verbs["text"])
			
			handler_priority = handler.get_priority()
			if hasattr(match, '_history_priority'):
				handler_priority = match._history_priority
				
			self._completion_model.append([handler_priority, match.get_priority(), match.get_verb() % verbs, icon, match, text])
					
		#Set the entry icon accoring to the first match in the completion list
		self._update_icon(iter=self._completion_model.get_iter_first())
		
