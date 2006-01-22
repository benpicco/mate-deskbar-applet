import cPickle, os
import gtk, gobject
from deskbar import MAX_HISTORY, HISTORY_FILE, MAX_RESULTS_PER_HANDLER
	
class DeskbarHistory(gobject.GObject):
	__gsignals__ = {
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
	}
	
	def __init__(self):
		gobject.GObject.__init__ (self)
		self._history = []
		self._index = -1
					
	def load(self, module_list):
		print 'Loading History'
		try:
			saved_history = cPickle.load(file(HISTORY_FILE))
		except Exception, msg:
			return
		
		def strip_class(name):
			i = name.rfind(".")
			if i == -1:
				return None
				
			return name[i+1:]
					
		for text, handler_class_name, match_class_name, serialized in saved_history:
			for modctx in module_list:
				if strip_class(handler_class_name) != modctx.handler:
					continue
				
				match_class = strip_class(match_class_name)
				if match_class == None:
					continue
					
				match = modctx.module.deserialize(match_class, serialized)
				if match != None:
					self.add(text, match)
		
	def save(self):
		save = []
		for text, match in self._history:
			hsh = match.get_hash(text)
			save.append((text, str(match.get_handler().__class__), str(match.__class__), match.serialize()))
			
		try:
			cPickle.dump(save, file(HISTORY_FILE, 'w'), cPickle.HIGHEST_PROTOCOL)
			print 'History saved'
		except Exception, msg:
			print 'Error:History.save:%s', msg
		pass
	
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
	
if gtk.pygtk_version < (2,8,0):
	gobject.type_register(DeskbarHistory)
	
shared_history = DeskbarHistory()
def get_deskbar_history():
	return shared_history
