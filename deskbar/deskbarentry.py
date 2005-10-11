from os.path import join
import cgi

import deskbar
import deskbar.iconentry

import gtk, gobject

from deskbar.module_list import ModuleList
from deskbar.module_list import ModuleLoader
module_dirs = [deskbar.HANDLERS_DIR, "~/.gnome2/deskbar-applet"]


# The liststore columns
HANDLER_PRIO_COL = 0
MATCH_PRIO_COL = 1
ACTION_COL = 2
ICON_COL = 3
MATCH_COL = 4

# The sort function ids
SORT_BY_HANDLER_MATCH_ACTION = 1

MAX_RESULTS_PER_HANDLER = 6

#Maximum number of history items
MAX_HISTORY = 25

#selection directions
MOVE_UP   = -1
MOVE_DOWN = +1

class DeskbarEntry(deskbar.iconentry.IconEntry):
	def __init__(self):
		deskbar.iconentry.IconEntry.__init__(self)
		
		# Set up the Handlers
		self._handlers = ModuleList ()
		self._load_handlers()
		
		self._completion_model = None
		self._selected_match_index = -1
		self._history = History()
		
		# Connect to underlying entry signals		
		entry = self.get_entry()
		entry.connect("activate", self._on_entry_activate)
		self._on_entry_changed_id = entry.connect("changed", self._on_entry_changed)
		entry.connect("key-press-event", self._on_entry_key_press)
		
		# The image showing the matches' icon
		self._image = gtk.Image()
				
		# Create the left icon in an event box
		self._evbox = gtk.EventBox()
		self._evbox.set_property('visible-window', False)
		self._evbox.add(self._image)
		self.pack_widget(self._evbox, True)
		
		self._default_pixbuf = None
		try:
			self._default_pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(join(deskbar.ART_DATA_DIR, "deskbar-applet-small.png"), deskbar.ICON_SIZE, deskbar.ICON_SIZE)
		except gobject.GError, msg:
			print 'Error:DeskbarEntry.__init__:', msg
		
		self._image.set_property('pixbuf', self._default_pixbuf)

		# Create the listtore, model for the completion popup
		self._completion_model = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_STRING, gtk.gdk.Pixbuf, object)
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
		
		# Pain it accordingly		
		renderer = gtk.CellRendererPixbuf()
		completion.pack_start(renderer)
		completion.add_attribute(renderer, "pixbuf", ICON_COL)
		
		renderer = gtk.CellRendererText()
		completion.pack_start(renderer)
		completion.add_attribute(renderer, "markup", ACTION_COL)
	
	def get_evbox(self):
		return self._evbox
	
	def get_history(self):
		return self._history
		
	def _load_handlers(self):
		loader = ModuleLoader (self._handlers, module_dirs, ".py")
		loader.load_all ()
		return 
			
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
		if a < b:
			return 1
		elif a > b:
			return -1
		else:
			return 0
			
	def _on_completion_selected(self, completion, model, iterator):
		match = model[iterator][MATCH_COL]
		text = self.get_entry().get_text().strip()
		
		# Do the action, match will be either a regular selected manually match
		# Or the match stored in the model by history navigation
		match.action(text)
		
		# Add the item to history
		if self._history.last() != (text, match):
			self._history.add((text, match))
		self._history.reset()
						
		#Clear the entry in a idle call or we segfault
		gobject.idle_add(lambda: self.get_entry().set_text(""))

	def _on_entry_activate(self, widget):
		# When the user hits enter on the entry, we use the first match to do the action
		iter = self._completion_model.get_iter_first()
		if iter != None:
			self._on_completion_selected (widget, self._completion_model, iter)

	def _on_entry_key_press(self, entry, event):
		if event.keyval == gtk.keysyms.Page_Up:
			# Browse back history
			self._history.up()
			item = self._history.get_history()
			if item != None:
				self.get_entry().handler_block(self._on_entry_changed_id)
				text, match = item
				entry.set_text(text)
				entry.select_region(0, -1)
				# Update the icon entry, without erasing history position
				self._on_entry_changed(self.get_entry(), [match])
				self.get_entry().handler_unblock(self._on_entry_changed_id)
			else:
				entry.set_text("")

			return True
			
		if event.keyval == gtk.keysyms.Page_Down:
			# Browse back history
			self._history.down()
			item = self._history.get_history()
			if item != None:
				self.get_entry().handler_block(self._on_entry_changed_id)
				text, match = item
				entry.set_text(text)
				entry.select_region(0, -1)
				# Update the icon entry, without erasing history position
				self._on_entry_changed(self.get_entry(), [match])
				self.get_entry().handler_unblock(self._on_entry_changed_id)
			else:
				entry.set_text("")
								
			return True
			
		if event.keyval == gtk.keysyms.Escape:
			# bind Escape to clear the GtkEntry
			entry.set_text("")
		
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
		self._completion_model.clear()
		self._selected_match_index = -1
		
		if matches == None:
			# We have a regular changed event, fill the new model, reset history
			self._history.reset()

		t = widget.get_text().strip()
		if t == "":
			#Reset default icon
			self._update_icon(icon=self._default_pixbuf)
			return
			
		# Fill the model with new matches
		result = []
		if matches == None:
			for modctx in self._handlers:
				matches = modctx.module.query(t, MAX_RESULTS_PER_HANDLER)
				for match in matches:
					result.append(match)
		else:
			result = matches
				
		for res in result:
			handler = res.get_handler()
			if res.get_icon() != None:
				icon = res.get_icon()
			else:
				icon = handler.get_icon()
			
			# Pass unescaped query to the matches
			verbs = {"text" : t}
			verbs.update(res.get_name(t))
			# Escape the query now for display
			verbs["text"] = cgi.escape(verbs["text"])
			
			self._completion_model.append([handler.get_priority(), res.get_priority(), res.get_verb() % verbs, icon, res])
		
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
			
class History:
	def __init__(self):
		self._history = []
		self._index = -1
		
	def add(self, history):
		self._history.insert(0, history)
		self._history[:MAX_HISTORY]
		self._index = -1
	
	def up(self):
		if self._index < len(self._history)-1:
			self._index = self._index + 1
	
	def down(self):
		if self._index > -1:
			self._index = self._index - 1
	
	def reset(self):
		self._index = -1
	
	def last(self):
		if len(self._history) == 0:
			return None
		return self._history[0]
	
	def get_all_history(self):
		return self._history
		
	def get_history(self):
		if self._index == -1:
			return None
		
		return self._history[self._index]
