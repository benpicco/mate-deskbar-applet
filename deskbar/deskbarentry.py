from os.path import join
import cgi

import gtk, gobject

import deskbar, deskbar.iconentry
from deskbar.module_list import ModuleList
from deskbar.handler import *
from deskbar.history import get_deskbar_history

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
	def __init__(self, applet, module_list, loader):
		deskbar.iconentry.IconEntry.__init__(self)
		
		# Set up the Handlers
		self._handlers = module_list
		
		self._completion_model = None
		self._selected_match_index = -1
		self._history = get_deskbar_history()
		self._history.add_module_loader(loader)
		self._history.connect('changed', self._on_history_move)
		
		# Connect to underlying entry signals		
		entry = self.get_entry()
		entry.connect("activate", self._on_entry_activate)
		self._on_entry_changed_id = entry.connect("changed", self._on_entry_changed)
		entry.connect("key-press-event", self._on_entry_key_press, applet.applet)
		entry.connect("destroy", self._stop_async_handlers)
		entry.connect("destroy", self._save_history)
		
		# The image showing the matches' icon
		self._image = gtk.Image()
				
		# Create the left icon in an event box
		self._evbox = gtk.EventBox()
		self._evbox.set_property('visible-window', False)
		self._evbox.add(self._image)
		self.pack_widget(self._evbox, True)
		self._evbox.show()
		
		self._default_pixbuf = deskbar.handler_utils.load_icon("deskbar-applet-small.png")
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
			completion.set_property("text-column", ACTION_COL)
		except AttributeError:
			pass
			
		try:
			# PyGTK >= 2.4
			completion.set_match_func(lambda x, y, z: True)
			completion.set_model(self._completion_model)
		except AttributeError:
			pass
			
		completion.connect("match-selected", self._on_completion_selected)
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
			
	def _on_completion_selected(self, completion, model, iterator):
		match = model[iterator][MATCH_COL]
		text = model[iterator][TEXT_COL]
		
		# Do the action, match will be either a regular selected manually match
		# Or the match stored in the model by history navigation
		match.action(text)
		
		# Add the item to history
		self._history.add(text, match)
		self._history.reset()
						
		#Clear the entry in a idle call or we segfault
		gobject.idle_add(lambda: self.get_entry().set_text(""))
		
		# Tell the async handlers to stop
		self._stop_async_handlers()

	def _on_entry_activate(self, widget):
		# When the user hits enter on the entry, we use the first match to do the action
		iter = self._completion_model.get_iter_first()
		if iter != None:
			self._on_completion_selected (widget, self._completion_model, iter)
	
	def _on_entry_key_press(self, entry, event, applet):
		# For key UP to browse in history, we have either to be already in history mode, or have an empty text entry to trigger hist. mode
		up_history_condition = self._history.get_history() != None or (self._history.get_history() == None and entry.get_text() == "")
		# For key DOWN to browse history, we have to be already in history mode. Down cannot trigger history mode in that orient.
		down_history_condition = self._history.get_history() != None
					
		if event.keyval == gtk.keysyms.Up and up_history_condition:
			# Browse back history
			self._history.up()
			return True
				
		if event.keyval == gtk.keysyms.Down and down_history_condition:
			# Browse back history
			self._history.down()			
			return True
		
		# If the checks above fail and we come here, let's see if it's right to swallow up/down stroke
		# to avoid the entry losing focus.
		if (event.keyval == gtk.keysyms.Down or event.keyval == gtk.keysyms.Up) and entry.get_text() == "":
			return True
			
		if event.keyval == gtk.keysyms.Escape:
			# bind Escape to clear the GtkEntry
			if not entry.get_text().strip() == "":
				# If we cleared some text, tell async handlers to stop.
				self._stop_async_handlers()
			entry.set_text("")
			return False

		if event.state != 0 and event.state != gtk.gdk.SHIFT_MASK:
			# Some Handlers want to know about Ctrl-keypress
			# combinations, for example.  Here, we notify such
			# Handlers.
			for modctx in self._handlers:
				if not modctx.enabled:
					continue
				try:
					if modctx.module.on_entry_key_press(entry, event, applet):
						if not entry.get_text().strip() == "":
							# If we cleared some text, tell async handlers to stop.
							self._stop_async_handlers()
						entry.set_text("")
						return True
				except AttributeError:
					# The handler most likely does not have
					# an on_entry_key_press method.
					pass
		
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
	
	def _on_history_move(self, history):
		item = self._history.get_history()
		entry = self.get_entry()
		if item != None:
			self.get_entry().handler_block(self._on_entry_changed_id)
			text, match = item
			entry.set_text(text)
			entry.select_region(0, -1)
			# Update the icon entry, without erasing history position
			self._on_entry_changed(self.get_entry(), [match])
			self.get_entry().handler_unblock(self._on_entry_changed_id)
		else:
			# Here we delete the text cause we got out of history mode
			entry.set_text("")
				
	def _on_entry_changed(self, widget, matches=None):
		self._completion_model.clear()
		self._completion_model._hashes = {}
		self._selected_match_index = -1
		
		if matches == None:
			# We have a regular changed event, fill the new model, reset history
			self._history.reset()

		qstring = widget.get_text().strip()
		if  qstring == "":
			#Reset default icon
			self._update_icon(icon=self._default_pixbuf)
			return
			
		# Fill the model with new matches
		result = []
		if matches == None:
			for modctx in self._handlers:
				if not modctx.enabled:
					continue
				if modctx.module.is_async():
					modctx.module.query_async(qstring, MAX_RESULTS_PER_HANDLER)
				else:
					matches = modctx.module.query(qstring, MAX_RESULTS_PER_HANDLER)
					for match in matches:
						result.append(match)
					
			self._append_matches (result)
			# Special case history items:
			self._append_matches([(text, match) for text, match in self._history.get_all_history() if text.startswith(qstring)], override_query=True, override_priority=True)
		else:
			# We are called from history, do not display history items
			self._append_matches (matches)
		
	def _append_matches (self, matches, async=False, override_query=False, override_priority=False):
		"""
		Appends the list of Match objects to the list of query matches
		"""
		# By default, take the entry content as query string, unless override_query is specified
		t = self.get_entry().get_text().strip()
		
		for match in matches:
			# If override_query, then the passed match is in fact a (text, match)
			if override_query:
				t, match = match
				
			handler = match.get_handler()
			if match.get_icon() != None:
				icon = match.get_icon()
			else:
				icon = handler.get_icon()
			
			# Pass unescaped query to the matches
			verbs = {"text" : t}
			verbs.update(match.get_name(t))
			# Escape the query now for display
			verbs["text"] = cgi.escape(verbs["text"])
			
			hsh = match.get_hash(t)
			
			# Let's take the correct priority for the handler, by default use the order defined in the prefs
			# If we have priority_override, then we are probably adding previous history item, so we must make it very high prio
			handler_priority = handler.get_priority()
			if override_priority:
				handler_priority = 100000

			if (hsh != None and not hsh in self._completion_model._hashes) or hsh == None or async:
				self._completion_model._hashes[hsh] = True
				self._completion_model.append([handler_priority, match.get_priority(), match.get_verb() % verbs, icon, match, t])
					
		#Set the entry icon accoring to the first match in the completion list
		self._update_icon(iter=self._completion_model.get_iter_first())
	
	def _update_icon(self, iter=None, icon=None):
		if self._selected_match_index > -1 and len(self._completion_model) > 0:
			iter = self._selected_match_index

		if iter != None:
			self._image.set_property('pixbuf', self._completion_model[iter][ICON_COL])
		
		if icon != None:
			self._image.set_property('pixbuf', icon)
		
		self._image.set_size_request(deskbar.ICON_SIZE, deskbar.ICON_SIZE)
	
	def _stop_async_handlers (self, sender=None):
		for modctx in self._handlers:
			if modctx.module.is_async():
				modctx.module.stop_query()
	
	def _save_history(self, sender):
		self._history.save()
		
	def _connect_if_async (self, sender, context):
		if context.module.is_async():
			context.module.connect('query-ready', lambda sender, matches: self._append_matches(matches, True))

