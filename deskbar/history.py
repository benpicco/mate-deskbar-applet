import cPickle, os
import gobject
from deskbar import MAX_HISTORY, HISTORY_FILE
import deskbar.handler
from deskbar.handler import *
	
class DeskbarHistory(gobject.GObject):
	__gsignals__ = {
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
	}
	
	def __init__(self):
		gobject.GObject.__init__ (self)
		self._history = []
				
		try:
			self.saved_history = cPickle.load(file(HISTORY_FILE))
		except Exception, msg:
			self.saved_history = []
			print 'Warning while loading history:', msg			
			
		self._index = -1
	
	def add_module_loader(self, loader):
		loader.connect ("module-initialized", self.on_module_initialized)
		loader.connect ("module-initialized", self.connect_if_async)
		
	def on_module_initialized(self, loader, modctx, matches=None):
		to_delete = []
		for i, saved in enumerate(self.saved_history):
			text, hsh, handler_class = saved
			
			# Checks wether it's the good handler
			j = handler_class.rfind(".")
			if j == -1 or handler_class[j+1:] != modctx.handler:
				continue
			
			if modctx.module.is_async() and matches == None:
				modctx.module.query_async(text, MAX_RESULTS_PER_HANDLER)
			elif matches == None:
				matches = modctx.module.query(text, MAX_RESULTS_PER_HANDLER)

			if matches != None:
				for match in matches:
					self.add_saved_to_history(match, i, text, hsh)
				to_delete.append(saved)
		
		for delete in to_delete:
			self.saved_history.remove(delete)
				
	def connect_if_async (self, sender, context):
		if context.module.is_async():
			context.module.connect('query-ready', lambda sender, matches: self.on_module_initialized(sender, context, matches))
	
	def add_saved_to_history(self, match, i, text, hsh):
		if match.get_hash(text) == hsh:
			self._history.insert(i, (text, match))
		
	def add(self, text, match):
		for htext, hmatch in self._history:
			if (text, match.__class__) == (htext, hmatch.__class__):
				self._history.remove((htext, hmatch))

		self._history.insert(0, (text, match))
		self._history = self._history[:MAX_HISTORY]
		self._index = -1
	
	def up(self):
		if self._index < len(self._history)-1:
			self._index = self._index + 1
			self.emit('changed')
	
	def down(self):
		if self._index > -1:
			self._index = self._index - 1
			self.emit('changed')
	
	def reset(self):
		if self._index != -1:
			self._index = -1
			self.emit('changed')
	
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
	
	def save(self):
		save = []
		for text, match in self._history:
			hsh = match.get_hash(text)
			if hsh != None:
				save.append((text, hsh, str(match.get_handler().__class__) ))
				
		try:
			cPickle.dump(save, file(HISTORY_FILE, 'w'), cPickle.HIGHEST_PROTOCOL)
			pass
		except Exception, msg:
			print 'Error:History.save:%s', msg
		pass

shared_history = DeskbarHistory()
def get_deskbar_history():
	return shared_history
