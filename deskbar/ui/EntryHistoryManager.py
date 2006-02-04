import gtk, gobject
from deskbar.DeskbarHistory import get_deskbar_history

class EntryHistoryManager(gobject.GObject):

	__gsignals__ = {
		"history-set" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_BOOLEAN])
	}
	
	def __init__(self, entry, changed_id):
		gobject.GObject.__init__ (self)
		
		self.entry = entry
		self.history = get_deskbar_history()
		self.changed_id = changed_id
		
		self.current_history = None
		
		self.entry.connect("key-press-event", self._on_entry_key_press)
		self.history.connect('changed', self._on_history_move)
	
	def _on_entry_key_press(self, entry, event):
		# For key UP to browse in history, we have either to be already in history mode, or have an empty text entry to trigger hist. mode
		up_history_condition = self.history.get_history() != None or (self.history.get_history() == None and self.entry.get_text() == "")
		# For key DOWN to browse history, we have to be already in history mode. Down cannot trigger history mode in that orient.
		down_history_condition = self.history.get_history() != None
		print 'Hist:', self.history.get_history()
		if event.keyval == gtk.keysyms.Up and up_history_condition:
			# Browse back history
			self.history.up()
			print 'Hup'
			return True
				
		if event.keyval == gtk.keysyms.Down and down_history_condition:
			# Browse back history
			self.history.down()
			print 'HDown'		
			return True
		
		# If the checks above fail and we come here, let's see if it's right to swallow up/down stroke
		# to avoid the entry losing focus.
		if (event.keyval == gtk.keysyms.Down or event.keyval == gtk.keysyms.Up) and entry.get_text() == "":
			print 'Swalliw'
			return True
		print 'nothing'
		return False
			
	def _on_history_move(self, history):
		item = self.history.get_history()
		entry = self.entry
		
		self.current_history = item
		if item != None:
			entry.handler_block(self.changed_id)
			text, match = item
			entry.set_text(text)
			entry.select_region(0, -1)
			# Update the icon entry, without erasing history position
			
			self.emit('history-set', True)
			entry.handler_unblock(self.changed_id)
		else:
			# Here we delete the text cause we got out of history mode
			self.emit('history-set', False)

if gtk.pygtk_version < (2,8,0):
	gobject.type_register(EntryHistoryManager)
