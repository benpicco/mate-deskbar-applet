import cPickle, os
import gtk, gobject
from deskbar import MAX_HISTORY, HISTORY_FILE, MAX_RESULTS_PER_HANDLER

class DeskbarHistoryIter : 
	"""An iter type to iterate over a DeskbarHistory.
	This object is (typically) not used directly.
	For documentation on iters see: http://docs.python.org/lib/typeiter.html
	"""
	def __init__ (self, owner):
		self.owner = owner
		self.owner_iter = owner.get_iter_first ()
		
	def __iter__ (self):
		return self
		
	def next (self):
		try:
			item = self.owner[self.owner_iter][0]
			self.owner_iter = self.owner.iter_next (self.owner_iter)
		except TypeError:
			raise StopIteration
		return item

class DeskbarHistory (gtk.ListStore) :
	"""
	Iteraating over a DeskbarHistory with a for loop returns (text,match) pairs.
	Keeps an internal pointer to a history index which you can move with up(), down(),
	and reset(). You retrieve the item in question by get_history().
	
	Signals:
		"changed" : emitted when the internal pointer has changed
	"""

	__gsignals__ = {
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
	}
	
	def __init__ (self):
		gtk.ListStore.__init__ (self, gobject.TYPE_PYOBJECT)
		self.count = 0
		self._index = -1
		
	def __iter__ (self):
		return DeskbarHistoryIter (self)				
		
	def load (self, module_list):
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
					self.append ([(text, match)])
					self.count = self.count + 1
		
	def save (self):
		save = []
		for text, match in self:
			hsh = match.get_hash(text)
			save.append((text, str(match.get_handler().__class__), str(match.__class__), match.serialize()))
			
		try:
			cPickle.dump(save, file(HISTORY_FILE, 'w'), cPickle.HIGHEST_PROTOCOL)
			print 'History saved'
		except Exception, msg:
			print 'Error:History.save:%s', msg
		pass
	
	def add (self, text, match):
		idx = 0
		for htext, hmatch in self:
			if (text, match.__class__) == (htext, hmatch.__class__):
				self.remove (self.get_iter_from_string (str(idx)))
				self.count = self.count - 1
			idx = idx + 1

		self.prepend ([(text, match)])
		self.count = self.count + 1
		if self.count > MAX_HISTORY:
			# Remove the last element
			last = self.get_iter_from_string (str(self.count - 1))
			self.remove (last)
			self.count = self.count - 1
		self._index = -1
	
	def up(self):
		if self._index < self.count-1:
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
		if self.count == 0:
			return None
		last = self.get_iter_from_string (str(self.count - 1))
		return self[last][0]
	
	def get_all_history(self):
		return self
		
	def get_history(self):
		if self._index == -1:
			return None
		return self[self.get_iter_from_string (str(self._index))][0]
	
if gtk.pygtk_version < (2,8,0):
	gobject.type_register(DeskbarHistory)
	
shared_history = DeskbarHistory()
def get_deskbar_history():
	return shared_history
